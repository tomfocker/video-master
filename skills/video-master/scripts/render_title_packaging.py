#!/usr/bin/env python3
"""Render transparent title-packaging PNGs and optional alpha-channel MOVs.

The creative workflow can still use native image generation for look exploration.
This script is the deterministic finishing pass for exact text, clean alpha, and
editor-ready ProRes 4444 overlays.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import FINAL_TITLE_PACKAGING_DIR, TITLE_PACKAGING_MANIFEST, title_packaging_manifest_path


DEFAULT_PLAN = Path("packaging") / "title_packaging_plan.json"
WORKING_PNG_DIR = Path("packaging") / "title_cards"
WORKING_MOV_DIR = Path("packaging") / "alpha_mov"
VALID_ASSET_TYPES = {
    "title_card",
    "chapter_card",
    "lower_third",
    "name_tag",
    "counter",
    "data_callout",
    "cta_card",
    "end_card",
}

ADVANCED_MOTION_TEMPLATES = {
    "brush_reveal",
    "mask_wipe",
    "glow_sweep",
    "route_draw",
    "route_light_trail",
    "number_roll",
    "odometer",
    "marker_annotation",
    "annotation_arrow",
}

SCALABLE_ITEM_KEYS = {
    "font_size",
    "subtitle_font_size",
    "margin_x",
    "margin_y",
    "gap",
    "accent_height",
    "accent_width",
}


FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/msyhbd.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
]


class PackagingError(ValueError):
    """Raised when the title packaging plan cannot be rendered."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise PackagingError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PackagingError("title packaging plan must be a JSON object")
    return data


def safe_id(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return slug or "title_asset"


def parse_color(value: str | None, default: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    if not value:
        return default
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) == 6:
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4)) + (255,)
    if len(value) == 8:
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4, 6))
    raise PackagingError(f"invalid color value: {value}")


def canvas_size(plan: dict[str, Any]) -> tuple[int, int]:
    canvas = plan.get("canvas") or {}
    if isinstance(canvas, dict) and canvas.get("width") and canvas.get("height"):
        return int(canvas["width"]), int(canvas["height"])

    ratio = str(plan.get("aspect_ratio", "16:9")).strip()
    if ratio == "9:16":
        return 1080, 1920
    if ratio == "1:1":
        return 1080, 1080
    return 1920, 1080


def load_font(size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [Path(font_path)] if font_path else []
    candidates.extend(FONT_CANDIDATES)
    for candidate in candidates:
        if candidate and candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_box(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    if not text:
        return 0, 0
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def eased(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) * (1 - value)


def ease_in_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def overshoot(value: float) -> float:
    value = max(0.0, min(1.0, value))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (value - 1) ** 3 + c1 * (value - 1) ** 2


def motion_template(item: dict[str, Any]) -> str:
    value = str(item.get("motion_template") or item.get("animation") or "fade-up")
    return value.strip().lower().replace("-", "_")


def scale_item(item: dict[str, Any], scale: int) -> dict[str, Any]:
    scaled = dict(item)
    for key in SCALABLE_ITEM_KEYS:
        if key in scaled:
            scaled[key] = int(float(scaled[key]) * scale)
    return scaled


def animated_state(item: dict[str, Any], progress: float) -> tuple[int, int, int]:
    animation = str(item.get("animation", "fade-up"))
    alpha = 255
    y_offset = 0
    if animation in {"fade", "fade-up"}:
        alpha = int(255 * eased(min(progress / 0.35, 1.0)))
    if animation == "fade-up":
        y_offset = int((1 - eased(min(progress / 0.45, 1.0))) * 34)
    return 0, y_offset, alpha


def counter_text(item: dict[str, Any], progress: float) -> str:
    start = float(item.get("start_value", 0))
    end = float(item.get("end_value", 100))
    decimals = int(item.get("decimals", 0))
    value = start + (end - start) * eased(progress)
    number = f"{value:,.{decimals}f}"
    return f"{item.get('prefix', '')}{number}{item.get('suffix', '')}"


def resolve_text(item: dict[str, Any], progress: float = 1.0) -> str:
    if item.get("type") == "counter":
        return counter_text(item, progress)
    return str(item.get("text", "")).strip()


def draw_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    shadow: bool,
) -> None:
    if shadow:
        sx, sy = xy[0] + 4, xy[1] + 5
        draw.text((sx, sy), text, font=font, fill=(0, 0, 0, max(40, fill[3] // 2)))
    draw.text(xy, text, font=font, fill=fill)


def position_block(
    item: dict[str, Any],
    canvas: tuple[int, int],
    block_size: tuple[int, int],
    y_offset: int,
) -> tuple[int, int]:
    width, height = canvas
    block_w, block_h = block_size
    position = str(item.get("position", "center")).strip()
    margin_x = int(item.get("margin_x", width * 0.08))
    margin_y = int(item.get("margin_y", height * 0.09))

    if position == "lower_third":
        return margin_x, int(height * 0.68) + y_offset
    if position == "top_left":
        return margin_x, margin_y + y_offset
    if position == "bottom_right":
        return width - margin_x - block_w, height - margin_y - block_h + y_offset
    return (width - block_w) // 2, (height - block_h) // 2 + y_offset


def render_frame(
    item: dict[str, Any],
    canvas: tuple[int, int],
    progress: float = 1.0,
    font_path: str | None = None,
) -> Image.Image:
    asset_type = str(item.get("type", "title_card"))
    if asset_type not in VALID_ASSET_TYPES:
        raise PackagingError(f"unsupported title packaging item type: {asset_type}")

    image = Image.new("RGBA", canvas, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    width, height = canvas
    _, y_offset, alpha = animated_state(item, progress)

    text = resolve_text(item, progress)
    subtitle = str(item.get("subtitle", "")).strip()
    font_size = int(item.get("font_size", max(34, width * 0.075)))
    subtitle_size = int(item.get("subtitle_font_size", max(20, width * 0.026)))
    font = load_font(font_size, font_path or item.get("font_path"))
    subtitle_font = load_font(subtitle_size, font_path or item.get("font_path"))
    fill = parse_color(item.get("color"), (255, 255, 255, alpha))
    fill = fill[:3] + (min(fill[3], alpha),)
    accent = parse_color(item.get("accent_color"), (214, 180, 106, alpha))
    accent = accent[:3] + (min(accent[3], alpha),)

    text_w, text_h = text_box(draw, text, font)
    subtitle_w, subtitle_h = text_box(draw, subtitle, subtitle_font)
    gap = int(item.get("gap", max(12, height * 0.016)))
    accent_h = int(item.get("accent_height", max(4, height * 0.006)))
    block_w = max(text_w, subtitle_w, int(width * 0.24))
    block_h = text_h + (gap + subtitle_h if subtitle else 0) + gap + accent_h
    x, y = position_block(item, canvas, (block_w, block_h), y_offset)
    align = str(item.get("align", "center"))
    shadow = bool(item.get("shadow", True))

    text_x = x if align == "left" else x + (block_w - text_w) // 2
    draw_with_shadow(draw, (text_x, y), text, font, fill, shadow)
    next_y = y + text_h + gap

    if subtitle:
        subtitle_x = x if align == "left" else x + (block_w - subtitle_w) // 2
        draw_with_shadow(draw, (subtitle_x, next_y), subtitle, subtitle_font, fill, shadow)
        next_y += subtitle_h + gap

    accent_width = int(item.get("accent_width", block_w))
    if item.get("accent", True):
        if align == "left":
            accent_x = x
        else:
            accent_x = x + (block_w - accent_width) // 2
        draw.rounded_rectangle(
            [accent_x, next_y, accent_x + accent_width, next_y + accent_h],
            radius=max(1, accent_h // 2),
            fill=accent,
        )

    return image


def write_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def resolve_project_path(project: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return project / path


def load_design_asset(project: Path, item: dict[str, Any], canvas: tuple[int, int]) -> Image.Image | None:
    source = item.get("design_asset") or item.get("source_png") or item.get("transparent_png")
    source_path = resolve_project_path(project, str(source)) if source else None
    if not source_path:
        return None
    if not source_path.is_file():
        raise PackagingError(f"missing title packaging design asset: {source_path}")

    with Image.open(source_path) as opened:
        asset = opened.convert("RGBA")
    width, height = canvas
    fit = str(item.get("design_fit", "contain")).strip().lower()
    if fit == "native" and asset.size == canvas:
        return asset

    scale = min(width / asset.width, height / asset.height)
    if fit == "cover":
        scale = max(width / asset.width, height / asset.height)
    if item.get("design_scale"):
        scale *= float(item["design_scale"])
    new_size = (max(1, int(asset.width * scale)), max(1, int(asset.height * scale)))
    resampling = Image.Resampling.LANCZOS
    asset = asset.resize(new_size, resampling)

    output = Image.new("RGBA", canvas, (0, 0, 0, 0))
    x = int(item.get("design_x", (width - asset.width) / 2))
    y = int(item.get("design_y", (height - asset.height) / 2))
    output.alpha_composite(asset, (x, y))
    return output


def render_static_asset(
    project: Path,
    item: dict[str, Any],
    canvas: tuple[int, int],
    font_path: str | None = None,
) -> Image.Image:
    design = load_design_asset(project, item, canvas)
    if design is not None:
        return design
    return render_frame(item, canvas, 1.0, font_path)


def downsample_if_needed(image: Image.Image, canvas: tuple[int, int]) -> Image.Image:
    if image.size == canvas:
        return image
    return image.resize(canvas, Image.Resampling.LANCZOS)


def composite_alpha(source: Image.Image, alpha: Image.Image) -> Image.Image:
    output = source.copy()
    output.putalpha(Image.composite(source.getchannel("A"), Image.new("L", source.size, 0), alpha))
    return output


def parse_point(value: Any, canvas: tuple[int, int], scale: int = 1) -> tuple[int, int]:
    width, height = canvas
    if isinstance(value, dict):
        x = float(value.get("x", 0))
        y = float(value.get("y", 0))
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        x = float(value[0])
        y = float(value[1])
    else:
        raise PackagingError(f"invalid point value: {value!r}")
    if 0 <= x <= 1 and 0 <= y <= 1:
        x *= width
        y *= height
    return int(x * scale), int(y * scale)


def parse_points(values: Any, canvas: tuple[int, int], scale: int = 1) -> list[tuple[int, int]]:
    if not values:
        return []
    if not isinstance(values, list):
        raise PackagingError("motion path points must be a list")
    return [parse_point(value, canvas, scale) for value in values]


def ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if found:
            return found
    raise PackagingError("ffmpeg is required for alpha MOV rendering; install imageio[ffmpeg] or ffmpeg")


def bezier_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    value: float,
) -> tuple[float, float]:
    a = (1 - value) ** 3
    b = 3 * (1 - value) ** 2 * value
    c = 3 * (1 - value) * value**2
    d = value**3
    return (
        a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
        a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
    )


def default_route_points(canvas: tuple[int, int], scale: int) -> list[tuple[int, int]]:
    width, height = canvas
    first = [
        bezier_point(
            (width * 0.11, height * 0.71),
            (width * 0.23, height * 0.28),
            (width * 0.41, height * 0.31),
            (width * 0.50, height * 0.54),
            index / 150,
        )
        for index in range(151)
    ]
    second = [
        bezier_point(
            (width * 0.50, height * 0.54),
            (width * 0.58, height * 0.76),
            (width * 0.75, height * 0.73),
            (width * 0.89, height * 0.33),
            index / 150,
        )
        for index in range(1, 151)
    ]
    return [(int(x * scale), int(y * scale)) for x, y in first + second]


def advanced_base_layer(
    project: Path,
    item: dict[str, Any],
    canvas: tuple[int, int],
    font_path: str | None,
    scale: int,
) -> Image.Image:
    high_canvas = (canvas[0] * scale, canvas[1] * scale)
    high_item = scale_item(item, scale)
    return render_static_asset(project, high_item, high_canvas, font_path)


def rough_reveal_mask(size: tuple[int, int], progress: float, frame_index: int, scale: int) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    edge = int((-120 + (width / scale + 260) * progress) * scale)
    polygon = [(0, 0), (edge, 0)]
    for yy in range(-60 * scale, height + 80 * scale, 22 * scale):
        wobble = math.sin((yy / scale) * 0.041 + frame_index * 0.15) * 26
        wobble += math.sin((yy / scale) * 0.013) * 16
        polygon.append((edge + int(wobble * scale), yy))
    polygon.extend([(0, height), (0, 0)])
    draw.polygon(polygon, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(max(1, 4 * scale)))


def wipe_mask(size: tuple[int, int], progress: float, scale: int) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    edge = int((width + 180 * scale) * progress) - 90 * scale
    draw.rectangle([0, 0, edge, height], fill=255)
    return mask.filter(ImageFilter.GaussianBlur(max(1, 10 * scale)))


def draw_glow_sweep(frame: Image.Image, progress: float, scale: int) -> None:
    width, height = frame.size
    sweep = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(sweep)
    x = int(width * (-0.15 + progress * 1.3))
    draw.line(
        [(x - 40 * scale, int(height * 0.20)), (x + 70 * scale, int(height * 0.78))],
        fill=(255, 248, 188, 112),
        width=max(1, 12 * scale),
    )
    frame.alpha_composite(sweep.filter(ImageFilter.GaussianBlur(max(1, 7 * scale))))


def brush_reveal_motion_frame(
    base: Image.Image,
    progress: float,
    frame_index: int,
    scale: int,
    template: str,
) -> Image.Image:
    progress = ease_in_out(progress) if template == "mask_wipe" else eased(progress)
    mask = wipe_mask(base.size, progress, scale) if template == "mask_wipe" else rough_reveal_mask(base.size, progress, frame_index, scale)
    frame = composite_alpha(base, mask)
    if template in {"brush_reveal", "glow_sweep"} and 0.55 < progress < 0.93:
        draw_glow_sweep(frame, (progress - 0.55) / 0.38, scale)
    if template == "brush_reveal" and 0.06 < progress < 0.96:
        draw = ImageDraw.Draw(frame)
        width, height = frame.size
        brush_x = int((-80 + (width / scale + 210) * progress + math.sin(frame_index * 0.38) * 9) * scale)
        brush_y = int((height / scale * 0.47 + math.sin(frame_index * 0.22) * 18) * scale)
        draw.ellipse(
            [brush_x - 20 * scale, brush_y - 9 * scale, brush_x + 34 * scale, brush_y + 13 * scale],
            fill=(255, 255, 255, 128),
        )
        draw.line(
            [(brush_x - 70 * scale, brush_y + 46 * scale), (brush_x + 9 * scale, brush_y + 13 * scale)],
            fill=(237, 188, 63, 150),
            width=max(1, 5 * scale),
        )
    return frame


def route_motion_frame(
    item: dict[str, Any],
    canvas: tuple[int, int],
    progress: float,
    scale: int,
    font_path: str | None,
) -> Image.Image:
    high_canvas = (canvas[0] * scale, canvas[1] * scale)
    frame = Image.new("RGBA", high_canvas, (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    width, height = canvas

    if item.get("grid", True):
        for x in range(int(width * 0.09), int(width * 0.92), max(1, int(width * 0.09))):
            draw.line([(x * scale, int(height * 0.21) * scale), (x * scale, int(height * 0.77) * scale)], fill=(255, 255, 255, 18), width=max(1, scale))
        for y in range(int(height * 0.26), int(height * 0.78), max(1, int(height * 0.10))):
            draw.line([(int(width * 0.08) * scale, y * scale), (int(width * 0.92) * scale, y * scale)], fill=(255, 255, 255, 17), width=max(1, scale))

    title = str(item.get("label") or item.get("text") or "ROUTE").strip()
    if title:
        title_font = load_font(max(16, int(item.get("label_font_size", width * 0.024))) * scale, font_path or item.get("font_path"))
        draw.text((int(width * 0.085) * scale, int(height * 0.145) * scale), title, font=title_font, fill=(255, 255, 255, 215))

    points = parse_points(item.get("route_points"), canvas, scale) or default_route_points(canvas, scale)
    progress = ease_in_out(progress)
    end = max(2, int(len(points) * progress))
    visible = points[:end]
    if len(visible) > 1:
        glow = Image.new("RGBA", high_canvas, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.line(visible, fill=(61, 226, 244, 116), width=max(1, 23 * scale), joint="curve")
        frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(1, 3 * scale))))
        draw.line(visible, fill=(14, 28, 34, 190), width=max(1, 12 * scale), joint="curve")
        draw.line(visible, fill=parse_color(item.get("accent_color"), (241, 190, 55, 255)), width=max(1, 8 * scale), joint="curve")
        draw.line(visible, fill=(255, 255, 255, 235), width=max(1, 3 * scale), joint="curve")

    label_font = load_font(max(14, int(item.get("city_font_size", width * 0.016))) * scale, font_path or item.get("font_path"))
    labels = item.get("labels") or []
    if isinstance(labels, list):
        for index, raw_label in enumerate(labels):
            if not isinstance(raw_label, dict):
                continue
            threshold = float(raw_label.get("threshold", (index + 1) / (len(labels) + 1)))
            if progress <= threshold:
                continue
            x, y = parse_point(raw_label, canvas, scale)
            pin_progress = overshoot(min(1.0, (progress - threshold) / 0.16))
            radius = int((6 + 6 * pin_progress) * scale)
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(255, 65, 90, 245))
            draw.ellipse([x - 4 * scale, y - 4 * scale, x + 4 * scale, y + 4 * scale], fill=(255, 255, 255, 245))
            text = str(raw_label.get("text", "")).strip()
            if text:
                box = draw.textbbox((0, 0), text, font=label_font)
                box_w = box[2] - box[0]
                box_h = box[3] - box[1]
                padding_x = 10 * scale
                padding_y = 6 * scale
                label_box = [
                    x - box_w // 2 - padding_x,
                    y + 18 * scale,
                    x + box_w // 2 + padding_x,
                    y + 18 * scale + box_h + padding_y * 2,
                ]
                draw.rounded_rectangle(label_box, radius=8 * scale, fill=(8, 15, 21, 180), outline=(255, 255, 255, 50), width=max(1, scale))
                draw.text((label_box[0] + padding_x, label_box[1] + padding_y - box[1]), text, font=label_font, fill=(255, 255, 255, 225))

    if item.get("route_tip", True) and visible:
        tip_x, tip_y = visible[-1]
        prev_x, prev_y = visible[max(0, len(visible) - 8)]
        angle = math.atan2(tip_y - prev_y, tip_x - prev_x)

        def rotate(local_x: float, local_y: float) -> tuple[int, int]:
            return (
                int(tip_x + local_x * scale * math.cos(angle) - local_y * scale * math.sin(angle)),
                int(tip_y + local_x * scale * math.sin(angle) + local_y * scale * math.cos(angle)),
            )

        plane = [rotate(22, 0), rotate(-17, -11), rotate(-6, 0), rotate(-17, 11)]
        draw.polygon(plane, fill=(255, 255, 255, 245))
        draw.line([plane[0], plane[2], plane[3]], fill=(0, 0, 0, 88), width=max(1, scale))
    return frame


def formatted_counter_value(item: dict[str, Any], progress: float) -> str:
    start = float(item.get("start_value", 0))
    end = float(item.get("end_value", 100))
    decimals = int(item.get("decimals", 0))
    value = start + (end - start) * eased(progress)
    number = f"{value:,.{decimals}f}"
    return f"{item.get('prefix', '')}{number}{item.get('suffix', '')}"


def formatted_counter_number(item: dict[str, Any], progress: float) -> str:
    start = float(item.get("start_value", 0))
    end = float(item.get("end_value", 100))
    decimals = int(item.get("decimals", 0))
    value = start + (end - start) * eased(progress)
    return f"{value:,.{decimals}f}"


def data_counter_motion_frame(
    item: dict[str, Any],
    canvas: tuple[int, int],
    progress: float,
    scale: int,
    font_path: str | None,
) -> Image.Image:
    high_canvas = (canvas[0] * scale, canvas[1] * scale)
    width, height = canvas
    frame = Image.new("RGBA", high_canvas, (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    progress = eased(progress)

    panel_w = int(item.get("panel_width", width * 0.62))
    panel_h = int(item.get("panel_height", height * 0.34))
    x = int(item.get("x", (width - panel_w) / 2))
    y = int(item.get("y", height * 0.30))
    panel = [x * scale, y * scale, (x + panel_w) * scale, (y + panel_h) * scale]
    draw.rounded_rectangle(panel, radius=18 * scale, fill=(8, 15, 25, 220), outline=(114, 231, 214, 165), width=max(1, 2 * scale))
    draw.rounded_rectangle(
        [x * scale, y * scale, (x + panel_w) * scale, (y + max(7, int(panel_h * 0.035))) * scale],
        radius=5 * scale,
        fill=parse_color(item.get("accent_color"), (242, 193, 55, 230)),
    )

    label = str(item.get("label") or item.get("text") or "DATA").strip()
    subtitle = str(item.get("subtitle") or item.get("metric_label") or "").strip()
    label_font = load_font(max(18, int(item.get("label_font_size", width * 0.024))) * scale, font_path or item.get("font_path"))
    small_font = load_font(max(13, int(item.get("subtitle_font_size", width * 0.017))) * scale, font_path or item.get("font_path"))
    number_size = max(38, int(item.get("number_font_size", width * 0.064)))
    unit_size = max(20, int(item.get("unit_font_size", width * 0.032)))

    left = (x + int(panel_w * 0.08)) * scale
    top = (y + int(panel_h * 0.18)) * scale
    draw.text((left, top), label, font=label_font, fill=(242, 248, 255, 235))
    if subtitle:
        draw.text((left, top + int(panel_h * 0.14) * scale), subtitle, font=small_font, fill=(132, 223, 221, 225))

    number_text = f"{item.get('prefix', '')}{formatted_counter_number(item, progress)}"
    unit_text = str(item.get("unit") or item.get("suffix") or "").strip()
    stat_x = x + int(panel_w * 0.68)
    available_number_width = max(180, (stat_x - x - int(panel_w * 0.10))) * scale
    number_font = load_font(number_size * scale, font_path or item.get("font_path"))
    unit_font = load_font(unit_size * scale, font_path or item.get("font_path"))
    number_box = draw.textbbox((0, 0), number_text, font=number_font)
    unit_box = draw.textbbox((0, 0), unit_text, font=unit_font) if unit_text else (0, 0, 0, 0)
    total_width = (number_box[2] - number_box[0]) + (unit_box[2] - unit_box[0]) + (14 * scale if unit_text else 0)
    if total_width > available_number_width:
        shrink = max(0.68, available_number_width / total_width)
        number_font = load_font(max(24, int(number_size * shrink)) * scale, font_path or item.get("font_path"))
        unit_font = load_font(max(15, int(unit_size * shrink)) * scale, font_path or item.get("font_path"))
        number_box = draw.textbbox((0, 0), number_text, font=number_font)
        unit_box = draw.textbbox((0, 0), unit_text, font=unit_font) if unit_text else (0, 0, 0, 0)

    number_y = (y + int(panel_h * 0.46)) * scale
    draw.text((left, number_y), number_text, font=number_font, fill=(255, 255, 255, 255))
    if unit_text:
        unit_x = left + (number_box[2] - number_box[0]) + 14 * scale
        unit_y = number_y + max(0, (number_box[3] - number_box[1]) - (unit_box[3] - unit_box[1]) - 12 * scale)
        draw.text((unit_x, unit_y), unit_text, font=unit_font, fill=parse_color(item.get("accent_color"), (242, 193, 55, 255)))

    bar_x = left
    bar_y = (y + int(panel_h * 0.82)) * scale
    bar_w = int(panel_w * 0.78) * scale
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 9 * scale], radius=5 * scale, fill=(255, 255, 255, 42))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 9 * scale], radius=5 * scale, fill=(112, 232, 217, 235))

    stats = item.get("stats") or []
    if isinstance(stats, list):
        stat_y = y + int(panel_h * 0.22)
        for index, stat in enumerate(stats[:4]):
            text = str(stat.get("text") if isinstance(stat, dict) else stat)
            alpha = int(255 * eased(max(0.0, min(1.0, (progress - 0.22 - index * 0.12) / 0.18))))
            yy = stat_y + index * int(panel_h * 0.18)
            draw.rounded_rectangle(
                [stat_x * scale, yy * scale, (stat_x + int(panel_w * 0.24)) * scale, (yy + int(panel_h * 0.13)) * scale],
                radius=10 * scale,
                fill=(40, 48, 58, min(210, max(80, alpha))),
                outline=(255, 255, 255, min(118, alpha // 2)),
                width=max(1, scale),
            )
            draw.text(((stat_x + 14) * scale, (yy + 6) * scale), text, font=small_font, fill=(255, 255, 255, alpha))
    return frame


def annotation_motion_points(item: dict[str, Any], canvas: tuple[int, int], scale: int) -> list[tuple[int, int]]:
    explicit = parse_points(item.get("path_points"), canvas, scale)
    if explicit:
        return explicit
    width, height = canvas
    points = []
    for index in range(180):
        value = index / 179
        x = width * 0.22 + width * 0.34 * value
        y = height * 0.46 + math.sin(value * math.pi * 2.3) * 2.1 + math.sin(value * math.pi * 7) * 0.7
        points.append((int(x * scale), int(y * scale)))
    for index in range(92):
        value = index / 91
        x = width * 0.56 + width * 0.15 * value
        y = height * 0.46 - height * 0.09 * ease_in_out(value) + math.sin(value * math.pi * 3) * 1.4
        points.append((int(x * scale), int(y * scale)))
    return points


def annotation_motion_frame(
    item: dict[str, Any],
    canvas: tuple[int, int],
    progress: float,
    scale: int,
) -> Image.Image:
    high_canvas = (canvas[0] * scale, canvas[1] * scale)
    frame = Image.new("RGBA", high_canvas, (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    progress = ease_in_out(progress)
    points = annotation_motion_points(item, canvas, scale)
    end = max(2, int(len(points) * min(1.0, progress / 0.78)))
    visible = points[:end]
    color = parse_color(item.get("stroke_color"), (255, 0, 32, 255))
    if len(visible) > 1:
        draw.line([(x + 2 * scale, y + 2 * scale) for x, y in visible], fill=(130, 0, 18, 92), width=max(1, 11 * scale), joint="curve")
        draw.line(visible, fill=color, width=max(1, int(item.get("stroke_width", 8)) * scale), joint="curve")
        draw.line(visible[::5], fill=color[:3] + (130,), width=max(1, 3 * scale), joint="curve")

    if progress > 0.67:
        arrow_progress = min(1.0, (progress - 0.67) / 0.16)
        scale_bounce = overshoot(arrow_progress)
        tip = parse_point(item.get("arrow_tip") or [0.704, 0.372], canvas, scale)
        left = (int(tip[0] - 36 * scale * scale_bounce), int(tip[1] + 8 * scale * scale_bounce))
        right = (int(tip[0] - 18 * scale * scale_bounce), int(tip[1] + 33 * scale * scale_bounce))
        draw.polygon([tip, left, right], fill=color)

    if progress > 0.76 and item.get("pulse", True):
        pulse = min(1.0, (progress - 0.76) / 0.24)
        center = parse_point(item.get("pulse_center") or [0.64, 0.34], canvas, scale)
        radius = int((10 + 62 * pulse) * scale)
        alpha = int(165 * (1 - pulse))
        draw.ellipse(
            [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
            outline=color[:3] + (alpha,),
            width=max(1, 4 * scale),
        )
    return frame


def render_motion_frame(
    project: Path,
    item: dict[str, Any],
    canvas: tuple[int, int],
    progress: float,
    frame_index: int,
    font_path: str | None,
    base: Image.Image | None,
    scale: int,
) -> Image.Image:
    template = motion_template(item)
    if template in {"brush_reveal", "mask_wipe", "glow_sweep"}:
        if base is None:
            raise PackagingError("internal error: missing motion base layer")
        if template == "glow_sweep":
            frame = base.copy()
            draw_glow_sweep(frame, progress, scale)
        else:
            frame = brush_reveal_motion_frame(base, progress, frame_index, scale, template)
        return downsample_if_needed(frame, canvas)
    if template in {"route_draw", "route_light_trail"}:
        return downsample_if_needed(route_motion_frame(item, canvas, progress, scale, font_path), canvas)
    if template in {"number_roll", "odometer"}:
        return downsample_if_needed(data_counter_motion_frame(item, canvas, progress, scale, font_path), canvas)
    if template in {"marker_annotation", "annotation_arrow"}:
        return downsample_if_needed(annotation_motion_frame(item, canvas, progress, scale), canvas)
    return render_frame(item, canvas, progress, font_path)


def render_motion_final_still(
    project: Path,
    item: dict[str, Any],
    canvas: tuple[int, int],
    font_path: str | None,
) -> Image.Image:
    template = motion_template(item)
    scale = int(item.get("motion_supersample", 2 if template in ADVANCED_MOTION_TEMPLATES else 1))
    scale = max(1, min(scale, 4))
    base = None
    if template in {"brush_reveal", "mask_wipe", "glow_sweep"}:
        base = advanced_base_layer(project, item, canvas, font_path, scale)
    return render_motion_frame(project, item, canvas, 1.0, 999, font_path, base, scale)


def render_mov(
    item: dict[str, Any],
    canvas: tuple[int, int],
    output: Path,
    fps: int,
    duration: float,
    font_path: str | None = None,
    project: Path | None = None,
) -> None:
    frame_count = max(1, int(math.ceil(fps * duration)))
    output.parent.mkdir(parents=True, exist_ok=True)
    template = motion_template(item)
    scale = int(item.get("motion_supersample", 2 if template in ADVANCED_MOTION_TEMPLATES else 1))
    scale = max(1, min(scale, 4))
    base = None
    if template in {"brush_reveal", "mask_wipe", "glow_sweep"}:
        if project is None:
            raise PackagingError("project path is required for motion template rendering")
        base = advanced_base_layer(project, item, canvas, font_path, scale)

    with tempfile.TemporaryDirectory() as tmp:
        frame_dir = Path(tmp)
        for index in range(frame_count):
            progress = 1.0 if frame_count == 1 else index / (frame_count - 1)
            frame = render_motion_frame(project or Path.cwd(), item, canvas, progress, index, font_path, base, scale)
            frame.save(frame_dir / f"frame_{index:04d}.png", format="PNG")

        cmd = [
            ffmpeg_executable(),
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frame_dir / "frame_%04d.png"),
            "-c:v",
            "prores_ks",
            "-profile:v",
            "4",
            "-pix_fmt",
            "yuva444p10le",
            "-vendor",
            "apl0",
            str(output),
        ]
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise PackagingError(f"ffmpeg failed while rendering {output}: {result.stderr.strip()}")


def render_project(
    project: Path,
    plan_path: Path | None = None,
    *,
    skip_alpha_mov: bool = False,
    force_alpha_mov: bool = False,
) -> dict[str, Any]:
    project = project.resolve()
    plan_path = plan_path or project / DEFAULT_PLAN
    if not plan_path.is_absolute():
        plan_path = project / plan_path
    if not plan_path.is_file():
        raise PackagingError(f"missing title packaging plan: {plan_path}")

    plan = read_json(plan_path)
    items = plan.get("items")
    if not isinstance(items, list) or not items:
        raise PackagingError("title packaging plan requires a non-empty items list")

    canvas = canvas_size(plan)
    fps = int(plan.get("fps", 24))
    duration = float(plan.get("duration_seconds", 2.0))
    generate_mov = (force_alpha_mov or bool(plan.get("generate_alpha_mov", False))) and not skip_alpha_mov
    font_path = plan.get("font_path")

    working_png_dir = project / WORKING_PNG_DIR
    working_mov_dir = project / WORKING_MOV_DIR
    final_dir = project / FINAL_TITLE_PACKAGING_DIR
    final_dir.mkdir(parents=True, exist_ok=True)

    rendered_items = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            raise PackagingError("each title packaging item must be an object")
        item = dict(raw_item)
        item_id = safe_id(str(item.get("id") or item.get("text") or item.get("type") or "title_asset"))
        item["id"] = item_id
        item_duration = float(item.get("duration_seconds", duration))
        png = working_png_dir / f"{item_id}.png"
        final_png = final_dir / f"{item_id}.png"
        template = motion_template(item)
        should_render_mov = generate_mov and item.get("alpha_mov", True)
        if should_render_mov and template in ADVANCED_MOTION_TEMPLATES:
            static_asset = render_motion_final_still(project, item, canvas, font_path)
        else:
            static_asset = render_static_asset(project, item, canvas, font_path)
        write_png(static_asset, png)
        write_png(static_asset, final_png)

        mov_output = None
        if should_render_mov:
            mov = working_mov_dir / f"{item_id}.mov"
            final_mov = final_dir / f"{item_id}.mov"
            render_mov(item, canvas, mov, fps, item_duration, font_path, project)
            shutil.copyfile(mov, final_mov)
            mov_output = str(final_mov.relative_to(project))

        rendered_items.append(
            {
                "id": item_id,
                "type": item.get("type", "title_card"),
                "motion_template": template if mov_output else None,
                "text": resolve_text(item, 1.0),
                "transparent_png": str(final_png.relative_to(project)),
                "alpha_mov": mov_output,
                "duration_seconds": item_duration,
            }
        )

    manifest = {
        "title_packaging": True,
        "plan": str(plan_path.relative_to(project)),
        "canvas": f"{canvas[0]}x{canvas[1]}",
        "fps": fps,
        "alpha_mov_codec": "prores_ks/prores_4444" if generate_mov else None,
        "alpha_mov_default": False,
        "items": rendered_items,
    }
    manifest_path = title_packaging_manifest_path(project)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render title packaging assets with transparent alpha.")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument("--plan", type=Path, default=None, help="Path to title_packaging_plan.json")
    parser.add_argument("--alpha-mov", action="store_true", help="Also render ProRes 4444 alpha MOV overlays")
    parser.add_argument("--skip-alpha-mov", action="store_true", help="Render transparent PNGs only")
    args = parser.parse_args(argv)

    try:
        manifest = render_project(
            args.project,
            args.plan,
            skip_alpha_mov=args.skip_alpha_mov,
            force_alpha_mov=args.alpha_mov,
        )
    except PackagingError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"OK: rendered {len(manifest['items'])} title packaging asset(s)")
    print(f"Manifest: {args.project / TITLE_PACKAGING_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
