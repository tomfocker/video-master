#!/usr/bin/env python3
"""Render a self-contained paper-cut collage proof of concept.

This is a deterministic packaging test, not a production template renderer.
It creates a reusable background plate and independent RGBA element assets,
then composites them into a six-second MP4/GIF preview. It deliberately keeps
all typography out of the generated animation so exact text can remain a
post-production layer.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH = 960
HEIGHT = 540
FPS = 24
DURATION_SECONDS = 6
FRAME_COUNT = FPS * DURATION_SECONDS


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease_out(value: float) -> float:
    value = clamp(value)
    return 1 - (1 - value) ** 3


def ease_in_out(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def lerp(start: float, end: float, progress: float) -> float:
    return start + (end - start) * progress


def paste(canvas: Image.Image, layer: Image.Image, x: float, y: float, scale: float = 1.0, alpha: float = 1.0) -> None:
    if scale != 1.0:
        layer = layer.resize(
            (max(1, round(layer.width * scale)), max(1, round(layer.height * scale))),
            Image.Resampling.LANCZOS,
        )
    if alpha < 0.999:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point(lambda value: round(value * alpha)))
    canvas.alpha_composite(layer, (round(x), round(y)))


def rounded_card(size: tuple[int, int], fill: tuple[int, int, int, int], radius: int = 18) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((10, 12, size[0] - 4, size[1] - 2), radius=radius, fill=(32, 37, 48, 75))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 2, size[0] - 10, size[1] - 12), radius=radius, fill=(255, 255, 250, 255))
    draw.rounded_rectangle((12, 10, size[0] - 18, size[1] - 20), radius=max(6, radius - 8), fill=fill)
    return image


def create_background() -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), (243, 238, 224, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, HEIGHT, 6):
        tone = 228 + (y * 17) % 18
        draw.line((0, y, WIDTH, y), fill=(tone, tone - 4, tone - 12, 26), width=1)
    for index in range(70):
        x = (index * 137) % WIDTH
        y = (index * 71) % HEIGHT
        draw.line((x, y, x + 24, y + 2), fill=(111, 95, 73, 18), width=1)
    draw.ellipse((-180, 350, 230, 760), fill=(68, 155, 137, 255))
    draw.ellipse((760, -180, 1160, 220), fill=(240, 157, 78, 235))
    draw.rounded_rectangle((54, 44, 906, 490), radius=34, outline=(53, 63, 68, 26), width=3)
    return image


def create_character() -> Image.Image:
    image = Image.new("RGBA", (240, 330), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((35, 30, 205, 202), fill=(255, 255, 250, 255))
    draw.polygon(((66, 86), (82, 18), (119, 67)), fill=(255, 255, 250, 255))
    draw.polygon(((157, 67), (194, 18), (207, 90)), fill=(255, 255, 250, 255))
    draw.ellipse((29, 181, 211, 315), fill=(255, 255, 250, 255))
    draw.ellipse((47, 38, 194, 188), fill=(87, 171, 205, 255))
    draw.polygon(((73, 83), (86, 35), (113, 71)), fill=(87, 171, 205, 255))
    draw.polygon(((153, 71), (182, 35), (192, 85)), fill=(87, 171, 205, 255))
    draw.ellipse((75, 95, 86, 110), fill=(32, 48, 59, 255))
    draw.ellipse((151, 95, 162, 110), fill=(32, 48, 59, 255))
    draw.arc((101, 112, 139, 147), 15, 165, fill=(32, 48, 59, 255), width=4)
    draw.ellipse((46, 188, 194, 302), fill=(251, 203, 83, 255))
    draw.rectangle((89, 185, 151, 298), fill=(252, 231, 165, 255))
    draw.ellipse((94, 221, 146, 273), fill=(238, 112, 88, 255))
    return image


def create_prop() -> Image.Image:
    image = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 12, 126, 122), fill=(255, 255, 250, 255))
    draw.polygon(((92, 104), (151, 145), (137, 158), (76, 113)), fill=(255, 255, 250, 255))
    draw.ellipse((26, 22, 116, 112), fill=(238, 146, 75, 255), outline=(44, 56, 62, 255), width=5)
    draw.ellipse((47, 43, 96, 92), fill=(100, 195, 211, 255), outline=(255, 255, 250, 170), width=4)
    draw.polygon(((90, 108), (145, 146), (135, 155), (78, 115)), fill=(74, 91, 103, 255))
    return image


def create_scene_window() -> Image.Image:
    card = rounded_card((340, 240), (130, 198, 204, 255), radius=22)
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((28, 28, 304, 198), radius=15, fill=(124, 197, 222, 255))
    draw.ellipse((175, 43, 225, 93), fill=(250, 218, 107, 255))
    draw.polygon(((28, 174), (92, 106), (141, 174), (202, 91), (304, 174)), fill=(78, 156, 130, 255))
    draw.polygon(((28, 198), (110, 143), (192, 198), (256, 126), (304, 194), (304, 198)), fill=(55, 122, 105, 255))
    draw.ellipse((79, 132, 111, 182), fill=(52, 105, 78, 255))
    draw.ellipse((238, 126, 270, 184), fill=(52, 105, 78, 255))
    return card


def create_badge(color: tuple[int, int, int, int]) -> Image.Image:
    image = rounded_card((104, 80), color, radius=18)
    draw = ImageDraw.Draw(image)
    draw.ellipse((41, 28, 61, 48), fill=(255, 255, 250, 220))
    return image


def create_spark() -> Image.Image:
    image = Image.new("RGBA", (74, 74), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    points = []
    for index in range(16):
        angle = math.pi * 2 * index / 16
        radius = 30 if index % 2 == 0 else 12
        points.append((37 + math.cos(angle) * radius, 37 + math.sin(angle) * radius))
    draw.polygon(points, fill=(244, 130, 84, 255), outline=(255, 255, 250, 240))
    return image


def load_chinese_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Use Windows' bundled CJK fonts so title cards remain precise and editable."""
    font_name = "msyhbd.ttc" if bold else "msyh.ttc"
    for directory in (Path("C:/Windows/Fonts"), Path("C:/Windows/Fonts")):
        candidate = directory / font_name
        if candidate.is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def draw_text_packaging(canvas: Image.Image, time: float) -> None:
    """Add a deterministic text-safe title card rather than asking an image model to render copy."""
    progress = ease_out((time - 0.18) / 0.48)
    if progress <= 0:
        return
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    y = round(lerp(38, 62, progress))
    alpha = round(255 * progress)
    draw.rounded_rectangle((62, y, 402, y + 91), radius=20, fill=(255, 254, 246, round(235 * progress)), outline=(47, 91, 91, alpha), width=3)
    draw.text((86, y + 14), "科学小问题", font=load_chinese_font(42, bold=True), fill=(36, 65, 71, alpha))
    draw.text((89, y + 61), "从观察开始", font=load_chinese_font(19), fill=(68, 109, 103, alpha))
    canvas.alpha_composite(layer)


def make_walking_character(character: Image.Image, time: float, active: bool) -> Image.Image:
    """Create a paper-puppet walk cycle from a single transparent full-body cutout."""
    if not active:
        return character
    character = character.convert("RGBA")
    width, height = character.size
    leg_top = round(height * 0.55)
    body = character.copy()
    ImageDraw.Draw(body).rectangle((0, leg_top, width, height), fill=(0, 0, 0, 0))

    left_box = (round(width * 0.18), leg_top - 4, round(width * 0.51), height)
    right_box = (round(width * 0.48), leg_top - 4, round(width * 0.82), height)
    phase = max(0.0, min(1.0, (time - 0.62) / 1.22))
    strength = math.sin(phase * math.pi)
    cycle = math.sin(time * math.pi * 5.4) * strength
    result = Image.new("RGBA", character.size, (0, 0, 0, 0))
    for box, direction in ((left_box, 1), (right_box, -1)):
        leg = character.crop(box)
        angle = direction * cycle * 8
        rotated = leg.rotate(angle, resample=Image.Resampling.BICUBIC, center=(leg.width // 2, 3))
        result.alpha_composite(rotated, (box[0], box[1] + round(abs(cycle) * 2)))
    bob = round(abs(cycle) * -4)
    result.alpha_composite(body, (0, bob))
    return result


def fit_to_canvas(image: Image.Image) -> Image.Image:
    """Resize and center-crop an image to the demo canvas without distortion."""
    scale = max(WIDTH / image.width, HEIGHT / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGBA")


def fit_cutout(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """Trim transparent padding and fit a supplied cutout into a demo layer."""
    image = image.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise ValueError("External cutout has no visible pixels")
    trimmed = image.crop(bounds)
    target_width, target_height = target_size
    scale = min((target_width - 12) / trimmed.width, (target_height - 12) / trimmed.height)
    resized = trimmed.resize(
        (max(1, round(trimmed.width * scale)), max(1, round(trimmed.height * scale))),
        Image.Resampling.LANCZOS,
    )
    layer = Image.new("RGBA", target_size, (0, 0, 0, 0))
    layer.alpha_composite(resized, ((target_width - resized.width) // 2, (target_height - resized.height) // 2))
    return layer


def create_assets(
    asset_dir: Path,
    external_background: Path | None = None,
    external_character: Path | None = None,
) -> dict[str, Path]:
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets = {
        "background": fit_to_canvas(Image.open(external_background)) if external_background else create_background(),
        "character": fit_cutout(Image.open(external_character), (240, 330)) if external_character else create_character(),
        "prop": create_prop(),
        "scene_window": create_scene_window(),
        "badge_teal": create_badge((79, 171, 156, 255)),
        "badge_orange": create_badge((238, 146, 75, 255)),
        "spark": create_spark(),
    }
    paths: dict[str, Path] = {}
    for name, image in assets.items():
        path = asset_dir / f"{name}.png"
        image.save(path)
        paths[name] = path
    return paths


def frame_at(index: int, assets: dict[str, Image.Image], walking_character: bool = False) -> Image.Image:
    time = index / FPS
    canvas = assets["background"].copy()
    draw_text_packaging(canvas, time)

    char_progress = ease_out((time - 0.7) / 0.85)
    char_x = lerp(-250, 120, char_progress)
    char_y = 165 + math.sin(clamp((time - 1.55) / 2.8) * math.pi) * 5
    paste(canvas, make_walking_character(assets["character"], time, walking_character), char_x, char_y, 0.92)

    prop_progress = ease_out((time - 1.35) / 0.55)
    prop_scale = 0.75 + 0.28 * math.sin(clamp((time - 1.35) / 0.75) * math.pi)
    paste(canvas, assets["prop"], lerp(510, 395, prop_progress), 122, prop_scale, prop_progress)

    window_progress = ease_in_out((time - 2.1) / 1.05)
    window_scale = lerp(0.18, 1.0, window_progress)
    window_x = lerp(790, 524, window_progress)
    window_y = lerp(105, 126, window_progress)
    paste(canvas, assets["scene_window"], window_x, window_y, window_scale, window_progress)

    for badge_index, badge_name in enumerate(("badge_teal", "badge_orange")):
        badge_progress = ease_out((time - 3.45 - badge_index * 0.32) / 0.42)
        x = 518 + badge_index * 118
        y = lerp(560, 380, badge_progress)
        paste(canvas, assets[badge_name], x, y, 0.88, badge_progress)

    spark_progress = clamp((time - 4.35) / 0.55)
    if spark_progress > 0:
        for spark_index in range(3):
            angle = -0.45 + spark_index * 0.56
            radius = 22 + 82 * spark_progress
            x = 470 + math.cos(angle) * radius
            y = 285 + math.sin(angle) * radius
            paste(canvas, assets["spark"], x, y, 0.28 + spark_progress * 0.34, 1 - spark_progress * 0.25)

    final_progress = ease_in_out((time - 4.85) / 0.9)
    if final_progress > 0:
        veil = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 250, round(50 * final_progress)))
        canvas.alpha_composite(veil)
    return canvas


def render(
    output_root: Path,
    external_background: Path | None = None,
    external_character: Path | None = None,
) -> dict[str, str | int]:
    if output_root.exists():
        raise FileExistsError(f"Refusing to overwrite existing proof directory: {output_root}")

    asset_dir = output_root / "assets" / "layers"
    preview_dir = output_root / "最终交付" / "05_预览视频"
    metadata_dir = output_root / "qa" / "metadata"
    preview_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    for label, source in (("background", external_background), ("character", external_character)):
        if source and not source.is_file():
            raise FileNotFoundError(f"External {label} not found: {source}")
    asset_paths = create_assets(asset_dir, external_background, external_character)
    assets = {name: Image.open(path).convert("RGBA") for name, path in asset_paths.items()}

    mp4_path = preview_dir / "paper_cut_collage_poc.mp4"
    gif_path = preview_dir / "paper_cut_collage_poc.gif"
    contact_path = preview_dir / "paper_cut_collage_contact_sheet.png"
    frames: list[Image.Image] = []

    # Keep the renderer portable: Pillow writes lossless temporary frames and
    # the locally available ffmpeg encodes the final H.264 preview.
    with tempfile.TemporaryDirectory(prefix="paper_cut_frames_", dir=metadata_dir) as frame_dir_name:
        frame_dir = Path(frame_dir_name)
        for index in range(FRAME_COUNT):
            frame = frame_at(index, assets, walking_character=external_character is not None)
            frames.append(frame)
            frame.convert("RGB").save(frame_dir / f"frame_{index:04d}.png")
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-framerate", str(FPS),
                "-i", str(frame_dir / "frame_%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mp4_path),
            ],
            check=True,
        )

    gif_frames = [frame.resize((640, 360), Image.Resampling.LANCZOS).convert("P", palette=Image.Palette.ADAPTIVE) for frame in frames[::2]]
    gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=round(2000 / FPS), loop=0, disposal=2)

    contact = Image.new("RGB", (960, 540), (34, 38, 45))
    for slot, frame_index in enumerate((0, 36, 78, 126)):
        frame = frames[frame_index].convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)
        contact.paste(frame, ((slot % 2) * 480, (slot // 2) * 270))
    contact.save(contact_path)

    manifest = {
        "kind": "paper_cut_collage_poc",
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "canvas": {"width": WIDTH, "height": HEIGHT},
        "method": "Pillow independent RGBA layers composited into MP4 and GIF; no Remotion required for this proof.",
        "external_background_source": str(external_background.resolve()) if external_background else None,
        "external_character_source": str(external_character.resolve()) if external_character else None,
        "assets": {name: str(path) for name, path in asset_paths.items()},
        "outputs": {"mp4": str(mp4_path), "gif": str(gif_path), "contact_sheet": str(contact_path)},
        "test_beats": [
            "background plate holds stable",
            "character cutout enters",
            "prop enters as an independent layer",
            "scene window expands",
            "badges and effect elements assemble",
            "final composition leaves a text-safe area"
        ]
    }
    manifest_path = metadata_dir / "paper_cut_collage_poc_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"mp4": str(mp4_path), "gif": str(gif_path), "contact_sheet": str(contact_path), "manifest": str(manifest_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a paper-cut collage packaging proof of concept.")
    parser.add_argument("--out", type=Path, required=True, help="New output project directory; must not already exist.")
    parser.add_argument(
        "--external-background",
        type=Path,
        help="Optional generated image to use as the background plate; it is copied into the self-contained layer set.",
    )
    parser.add_argument(
        "--external-character",
        type=Path,
        help="Optional RGBA cutout to use as the character layer; it is trimmed and copied into the self-contained layer set.",
    )
    args = parser.parse_args()
    print(json.dumps(
        render(
            args.out.resolve(),
            args.external_background.resolve() if args.external_background else None,
            args.external_character.resolve() if args.external_character else None,
        ),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
