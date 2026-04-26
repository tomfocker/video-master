#!/usr/bin/env python3
"""Render more polished alpha-channel motion-packaging demo overlays."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "video_projects" / "packaging_effect_demos_v2"
FINAL = PROJECT / Path("\u6700\u7ec8\u4ea4\u4ed8") / "07_title_packaging"
PREVIEW = PROJECT / "qa" / "metadata" / "effect_previews"
FRAMES = PROJECT / "packaging" / "motion_frames"

WIDTH = 1280
HEIGHT = 720
SCALE = 2
SWIDTH = WIDTH * SCALE
SHEIGHT = HEIGHT * SCALE
FPS = 30
FRAME_COUNT = 96

FONT_SERIF = "C:/Windows/Fonts/NotoSerifSC-VF.ttf"
FONT_SANS = "C:/Windows/Fonts/NotoSansSC-VF.ttf"
FONT_YAHEI_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_DENG_BOLD = "C:/Windows/Fonts/Dengb.ttf"
FONT_HEI = "C:/Windows/Fonts/simhei.ttf"

TITLE = "\u73af\u7403\u65c5\u884c\u65e5\u8bb0"
DISTANCE = "\u7d2f\u8ba1\u91cc\u7a0b"


def sc(value: float) -> int:
    return int(round(value * SCALE))


def pt(point: tuple[float, float]) -> tuple[int, int]:
    return sc(point[0]), sc(point[1])


def new_rgba() -> Image.Image:
    return Image.new("RGBA", (SWIDTH, SHEIGHT), (0, 0, 0, 0))


def font(path: str, size: int) -> ImageFont.ImageFont:
    for candidate in (path, FONT_YAHEI_BOLD, FONT_SANS, FONT_HEI):
        try:
            return ImageFont.truetype(candidate, size=sc(size))
        except OSError:
            continue
    return ImageFont.load_default()


def ease_out_cubic(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def ease_in_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def overshoot(value: float) -> float:
    value = max(0.0, min(1.0, value))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (value - 1) ** 3 + c1 * (value - 1) ** 2


def downsample(image: Image.Image) -> Image.Image:
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def draw_text_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_obj: ImageFont.ImageFont,
    y: int,
    fill: tuple[int, int, int, int],
    stroke_fill: tuple[int, int, int, int] | None = None,
    stroke_width: int = 0,
) -> tuple[int, int, int, int]:
    box = draw.textbbox((0, 0), text, font=font_obj, stroke_width=sc(stroke_width))
    text_width = box[2] - box[0]
    text_height = box[3] - box[1]
    x = (SWIDTH - text_width) // 2
    draw.text(
        (x, sc(y)),
        text,
        font=font_obj,
        fill=fill,
        stroke_width=sc(stroke_width),
        stroke_fill=stroke_fill,
    )
    return x, sc(y), text_width, text_height


def checker_background(size: tuple[int, int] = (640, 360)) -> Image.Image:
    image = Image.new("RGB", size, (24, 26, 34))
    draw = ImageDraw.Draw(image)
    step = 28
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2 == 0:
                draw.rectangle([x, y, x + step - 1, y + step - 1], fill=(37, 40, 50))
    return image.convert("RGBA")


def article_background(size: tuple[int, int] = (640, 360)) -> Image.Image:
    image = Image.new("RGBA", size, (248, 249, 250, 255))
    draw = ImageDraw.Draw(image)
    heading = font(FONT_SANS, 19)
    body = font(FONT_SANS, 14)
    draw.text((42, 46), "\u8fd9\u4e00\u884c\u6587\u5b57\u9700\u8981\u88ab\u5f3a\u8c03\uff0c\u4f46\u6807\u6ce8\u7d20\u6750\u672c\u8eab\u662f\u900f\u660e\u7684\u3002", font=heading, fill=(33, 37, 43, 255))
    draw.text((42, 92), "\u6b63\u5f0f\u4ea4\u4ed8\u7684 MOV \u53ea\u5305\u542b\u7ea2\u7ebf\u3001\u7bad\u5934\u3001\u8109\u51b2\u5708\uff0c\u80cc\u666f\u4e0d\u4f1a\u88ab\u5e26\u8d70\u3002", font=body, fill=(92, 99, 112, 255))
    draw.text((42, 136), "\u8fd9\u6837\u624d\u80fd\u5728\u526a\u8f91\u8f6f\u4ef6\u91cc\u76f4\u63a5\u53e0\u5230\u753b\u9762\u4e0a\u3002", font=body, fill=(92, 99, 112, 255))
    return image


def preview_frame(frame: Image.Image, background_kind: str) -> Image.Image:
    background = article_background() if background_kind == "article" else checker_background()
    small = frame.resize(background.size, Image.Resampling.LANCZOS)
    background.alpha_composite(small)
    return background.convert("P", palette=Image.Palette.ADAPTIVE, colors=160)


def alpha_blur(image: Image.Image, radius: float) -> Image.Image:
    blurred = image.copy()
    blurred.putalpha(image.getchannel("A").filter(ImageFilter.GaussianBlur(sc(radius))))
    return blurred


def paste_with_alpha(target: Image.Image, source: Image.Image, alpha_multiplier: float = 1.0) -> None:
    if alpha_multiplier < 0.999:
        source = source.copy()
        alpha = source.getchannel("A").point(lambda value: int(value * alpha_multiplier))
        source.putalpha(alpha)
    target.alpha_composite(source)


def encode_alpha_mov(frame_dir: Path, output: Path) -> None:
    ffmpeg = shutil.which("ffmpeg") or "D:/ffmpeg-n7.1-latest-win64-gpl-7.1/bin/ffmpeg.exe"
    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frame_dir / "%04d.png"),
        "-c:v",
        "prores_ks",
        "-profile:v",
        "4",
        "-pix_fmt",
        "yuva444p10le",
        "-alpha_bits",
        "16",
        str(output),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def save_outputs(name: str, frames: list[Image.Image], background_kind: str = "checker") -> dict[str, str]:
    frame_dir = FRAMES / name
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"{index:04d}.png")

    final_png = FINAL / f"{name}.png"
    alpha_mov = FINAL / f"{name}.mov"
    preview_gif = PREVIEW / f"{name}_preview.gif"
    final_preview = PREVIEW / f"{name}_final_preview.png"

    frames[-1].save(final_png)
    encode_alpha_mov(frame_dir, alpha_mov)

    preview_frames = [preview_frame(frame, background_kind) for frame in frames[::2]]
    preview_frames[0].save(
        preview_gif,
        save_all=True,
        append_images=preview_frames[1:],
        duration=1000 // (FPS // 2),
        loop=0,
        disposal=2,
    )

    still = checker_background()
    still.alpha_composite(frames[-1].resize(still.size, Image.Resampling.LANCZOS))
    still.save(final_preview)

    return {
        "id": name,
        "png": str(final_png),
        "mov": str(alpha_mov),
        "preview_gif": str(preview_gif),
        "final_preview": str(final_preview),
    }


def title_design_layer() -> Image.Image:
    layer = new_rgba()
    glow = new_rgba()
    glow_draw = ImageDraw.Draw(glow)
    main = font(FONT_SERIF, 116)
    subtitle = font(FONT_DENG_BOLD, 25)
    serif_small = font(FONT_SERIF, 19)

    draw_text_center(glow_draw, TITLE, main, 244, (255, 255, 255, 130), stroke_fill=(255, 214, 108, 55), stroke_width=4)
    layer.alpha_composite(alpha_blur(glow, 7))

    draw = ImageDraw.Draw(layer)
    x, y, width, _ = draw_text_center(
        draw,
        TITLE,
        main,
        244,
        (255, 255, 255, 255),
        stroke_fill=(73, 62, 50, 90),
        stroke_width=1,
    )

    sub = "GLOBAL TRAVEL JOURNAL"
    sub_box = draw.textbbox((0, 0), sub, font=subtitle)
    sub_width = sub_box[2] - sub_box[0]
    draw.text(((SWIDTH - sub_width) // 2, sc(433)), sub, font=subtitle, fill=(242, 230, 198, 235))

    swash = []
    for index in range(260):
        t = index / 259
        xx = 244 + 790 * t
        yy = 417 + math.sin(t * math.tau * 1.15) * 18 - t * 13
        swash.append(pt((xx, yy)))
    draw.line(swash, fill=(232, 184, 58, 240), width=sc(5), joint="curve")
    draw.line([pt((x / SCALE + 32, 377)), pt(((x + width) / SCALE - 40, 377))], fill=(255, 255, 255, 38), width=sc(1))

    seal_x, seal_y = 1005, 353
    draw.ellipse([sc(seal_x), sc(seal_y), sc(seal_x + 48), sc(seal_y + 48)], outline=(221, 31, 53, 238), width=sc(3))
    draw.text(pt((seal_x + 15, seal_y + 7)), "\u65c5", font=serif_small, fill=(221, 31, 53, 240))
    draw.text(pt((seal_x + 15, seal_y + 25)), "\u8bb0", font=serif_small, fill=(221, 31, 53, 240))
    return layer


def rough_reveal_mask(progress: float, frame_index: int) -> Image.Image:
    mask = Image.new("L", (SWIDTH, SHEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    edge = -120 + (WIDTH + 260) * progress
    polygon = [(0, 0), pt((edge, 0))]
    for yy in range(-60, HEIGHT + 80, 22):
        wobble = math.sin(yy * 0.041 + frame_index * 0.15) * 26 + math.sin(yy * 0.013) * 16
        polygon.append(pt((edge + wobble, yy)))
    polygon.extend([pt((0, HEIGHT)), (0, 0)])
    draw.polygon(polygon, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(sc(4)))


def premium_title_frames() -> list[Image.Image]:
    design = title_design_layer()
    frames = []
    for index in range(FRAME_COUNT):
        progress = ease_out_cubic(index / (FRAME_COUNT - 1))
        mask = rough_reveal_mask(progress, index)
        frame = new_rgba()
        reveal = design.copy()
        reveal.putalpha(Image.composite(design.getchannel("A"), Image.new("L", (SWIDTH, SHEIGHT), 0), mask))
        paste_with_alpha(frame, reveal)

        if 0.08 < progress < 0.96:
            draw = ImageDraw.Draw(frame)
            edge = -120 + (WIDTH + 260) * progress
            brush_x = edge + math.sin(index * 0.38) * 9
            brush_y = 334 + math.sin(index * 0.22) * 20
            draw.ellipse([sc(brush_x - 20), sc(brush_y - 9), sc(brush_x + 34), sc(brush_y + 13)], fill=(255, 255, 255, 138))
            draw.line([pt((brush_x - 70, brush_y + 46)), pt((brush_x + 9, brush_y + 13))], fill=(237, 188, 63, 150), width=sc(5))

        if 0.58 < progress < 0.9:
            sweep = new_rgba()
            sweep_draw = ImageDraw.Draw(sweep)
            sweep_progress = (progress - 0.58) / 0.32
            x = 260 + 780 * sweep_progress
            sweep_draw.line([pt((x - 42, 216)), pt((x + 54, 482))], fill=(255, 247, 185, 110), width=sc(12))
            sweep = sweep.filter(ImageFilter.GaussianBlur(sc(8)))
            paste_with_alpha(frame, sweep)

        frames.append(downsample(frame))
    return frames


def bezier(
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


def route_points() -> list[tuple[float, float]]:
    first = [bezier((140, 512), (287, 208), (515, 226), (637, 389), index / 150) for index in range(151)]
    second = [bezier((637, 389), (740, 550), (954, 524), (1132, 238), index / 150) for index in range(1, 151)]
    return first + second


def route_frames() -> list[Image.Image]:
    points = route_points()
    title_font = font(FONT_DENG_BOLD, 30)
    label_font = font(FONT_DENG_BOLD, 20)
    labels = [(140, 512, "PARIS", 0.09), (637, 389, "CAPE TOWN", 0.47), (1132, 238, "KYOTO", 0.86)]
    frames = []
    for index in range(FRAME_COUNT):
        progress = ease_in_out(index / (FRAME_COUNT - 1))
        frame = new_rgba()
        draw = ImageDraw.Draw(frame)

        for x in range(118, 1180, 118):
            draw.line([pt((x, 155)), pt((x, 555))], fill=(255, 255, 255, 18), width=sc(1))
        for y in range(190, 560, 72):
            draw.line([pt((108, y)), pt((1174, y))], fill=(255, 255, 255, 17), width=sc(1))
        draw.text(pt((110, 104)), "ROUTE / DAY 01 - DAY 18", font=title_font, fill=(255, 255, 255, 215))

        end = max(2, int(len(points) * progress))
        visible = [pt(point) for point in points[:end]]
        if len(visible) > 1:
            glow = new_rgba()
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.line(visible, fill=(61, 226, 244, 116), width=sc(23), joint="curve")
            paste_with_alpha(frame, glow.filter(ImageFilter.GaussianBlur(sc(3))))
            draw.line(visible, fill=(14, 28, 34, 190), width=sc(12), joint="curve")
            draw.line(visible, fill=(241, 190, 55, 255), width=sc(8), joint="curve")
            draw.line(visible, fill=(255, 255, 255, 235), width=sc(3), joint="curve")

        for x, y, label, threshold in labels:
            if progress > threshold:
                pin_progress = overshoot(min(1.0, (progress - threshold) / 0.16))
                radius = 6 + 6 * pin_progress
                draw.ellipse([sc(x - radius), sc(y - radius), sc(x + radius), sc(y + radius)], fill=(255, 65, 90, 245))
                draw.ellipse([sc(x - 4), sc(y - 4), sc(x + 4), sc(y + 4)], fill=(255, 255, 255, 245))
                draw.rounded_rectangle([sc(x - 44), sc(y + 18), sc(x + 57), sc(y + 48)], radius=sc(9), fill=(8, 15, 21, 180), outline=(255, 255, 255, 50), width=sc(1))
                draw.text(pt((x - 32, y + 23)), label, font=label_font, fill=(255, 255, 255, 225))

        tip_x, tip_y = points[end - 1]
        prev_x, prev_y = points[max(0, end - 8)]
        angle = math.atan2(tip_y - prev_y, tip_x - prev_x)

        def rotate(local_x: float, local_y: float) -> tuple[int, int]:
            return pt(
                (
                    tip_x + local_x * math.cos(angle) - local_y * math.sin(angle),
                    tip_y + local_x * math.sin(angle) + local_y * math.cos(angle),
                )
            )

        plane = [rotate(22, 0), rotate(-17, -11), rotate(-6, 0), rotate(-17, 11)]
        draw.polygon(plane, fill=(255, 255, 255, 245))
        draw.line([plane[0], plane[2], plane[3]], fill=(0, 0, 0, 88), width=sc(1))
        frames.append(downsample(frame))
    return frames


def rolling_digit_layer(text: str, progress: float) -> Image.Image:
    layer = new_rgba()
    draw = ImageDraw.Draw(layer)
    big = font(FONT_DENG_BOLD, 101)
    comma_font = font(FONT_DENG_BOLD, 46)
    x = sc(302)
    y = sc(336)
    digit_box_w = sc(62)
    digit_box_h = sc(116)
    digit_index = 0

    final_digits = [char for char in text if char.isdigit()]
    for char in text:
        if char == ",":
            comma_box = draw.textbbox((0, 0), ",", font=comma_font)
            comma_top = y + sc(72) - (comma_box[3] - comma_box[1])
            draw.text((x + sc(4), comma_top - comma_box[1]), ",", font=comma_font, fill=(255, 255, 255, 205))
            x += sc(26)
            continue

        target = int(final_digits[digit_index])
        roll = progress * (digit_index + 4.5)
        current = int((target * progress + roll * 10) % 10)
        next_digit = (current + 1) % 10
        frac = roll % 1
        if progress > 0.985:
            current = target
            next_digit = target
            frac = 0

        cell = Image.new("RGBA", (digit_box_w, digit_box_h), (0, 0, 0, 0))
        cell_draw = ImageDraw.Draw(cell)
        cell_draw.text((0, int(-frac * digit_box_h) - sc(10)), str(current), font=big, fill=(255, 255, 255, 255))
        cell_draw.text((0, int((1 - frac) * digit_box_h) - sc(10)), str(next_digit), font=big, fill=(255, 255, 255, 190))
        layer.alpha_composite(cell, (x, y))
        x += digit_box_w
        digit_index += 1
    return layer


def data_counter_frames() -> list[Image.Image]:
    label_font = font(FONT_SANS, 30)
    small_font = font(FONT_DENG_BOLD, 22)
    unit_font = font(FONT_DENG_BOLD, 42)
    frames = []
    for index in range(FRAME_COUNT):
        raw = index / (FRAME_COUNT - 1)
        progress = ease_out_cubic(raw)
        frame = new_rgba()
        draw = ImageDraw.Draw(frame)

        panel_alpha = int(230 * ease_out_cubic(min(1, raw / 0.24)))
        panel = [sc(235), sc(178), sc(1047), sc(534)]
        draw.rounded_rectangle(panel, radius=sc(22), fill=(8, 15, 25, panel_alpha), outline=(114, 231, 214, 165), width=sc(2))
        draw.rounded_rectangle([sc(235), sc(178), sc(1047), sc(190)], radius=sc(6), fill=(242, 193, 55, 230))

        sweep_x = 235 + 820 * ((raw * 1.15) % 1.0)
        sweep = new_rgba()
        sweep_draw = ImageDraw.Draw(sweep)
        sweep_draw.polygon([pt((sweep_x - 40, 178)), pt((sweep_x + 38, 178)), pt((sweep_x - 12, 534)), pt((sweep_x - 90, 534))], fill=(255, 255, 255, 30))
        paste_with_alpha(frame, sweep)

        draw.text(pt((296, 226)), DISTANCE, font=label_font, fill=(242, 248, 255, 235))
        draw.text(pt((298, 270)), "TOTAL DISTANCE", font=small_font, fill=(132, 223, 221, 225))

        target = 128640
        current = int(target * progress)
        number_text = f"{current:06,d}" if current < target else "128,640"
        number_layer = rolling_digit_layer(number_text, raw)
        paste_with_alpha(frame, number_layer)
        draw.text(pt((802, 383)), "KM", font=unit_font, fill=(243, 194, 57, 255))

        bar_x, bar_y, bar_width = 300, 480, 640
        draw.rounded_rectangle([sc(bar_x), sc(bar_y), sc(bar_x + bar_width), sc(bar_y + 11)], radius=sc(6), fill=(255, 255, 255, 42))
        draw.rounded_rectangle([sc(bar_x), sc(bar_y), sc(bar_x + bar_width * progress), sc(bar_y + 11)], radius=sc(6), fill=(112, 232, 217, 235))

        cards = [(770, 245, "6 \u5927\u6d32"), (770, 308, "32 \u57ce\u5e02"), (770, 371, "4 \u6d77\u6d0b")]
        for card_index, (x, y, text) in enumerate(cards):
            alpha = int(255 * ease_out_cubic(max(0.0, min(1.0, (raw - 0.22 - card_index * 0.12) / 0.18))))
            draw.rounded_rectangle([sc(x), sc(y), sc(x + 178), sc(y + 45)], radius=sc(12), fill=(255, 255, 255, min(46, alpha // 5)), outline=(255, 255, 255, min(118, alpha // 2)), width=sc(1))
            draw.text(pt((x + 18, y + 9)), text, font=small_font, fill=(255, 255, 255, alpha))
        frames.append(downsample(frame))
    return frames


def annotation_path(progress: float) -> list[tuple[float, float]]:
    points = []
    for index in range(180):
        t = index / 179
        x = 285 + 430 * t
        y = 334 + math.sin(t * math.pi * 2.3) * 2.1 + math.sin(t * math.pi * 7) * 0.7
        points.append((x, y))
    for index in range(92):
        t = index / 91
        x = 715 + 186 * t
        y = 334 - 66 * ease_in_out(t) + math.sin(t * math.pi * 3) * 1.4
        points.append((x, y))
    return points[: max(2, int(len(points) * progress))]


def annotation_frames() -> list[Image.Image]:
    frames = []
    for index in range(FRAME_COUNT):
        raw = index / (FRAME_COUNT - 1)
        progress = ease_in_out(raw)
        frame = new_rgba()
        draw = ImageDraw.Draw(frame)
        visible = [pt(point) for point in annotation_path(min(1, progress / 0.78))]
        if len(visible) > 1:
            draw.line([(x + sc(2), y + sc(2)) for x, y in visible], fill=(130, 0, 18, 92), width=sc(11), joint="curve")
            draw.line(visible, fill=(255, 0, 32, 255), width=sc(8), joint="curve")
            draw.line(visible[::5], fill=(255, 75, 96, 130), width=sc(3), joint="curve")

        if progress > 0.67:
            arrow_progress = min(1.0, (progress - 0.67) / 0.16)
            scale = overshoot(arrow_progress)
            tip = pt((901, 268))
            left = pt((901 - 36 * scale, 268 + 8 * scale))
            right = pt((901 - 18 * scale, 268 + 33 * scale))
            draw.polygon([tip, left, right], fill=(255, 0, 32, 255))

        if progress > 0.76:
            pulse = min(1.0, (progress - 0.76) / 0.24)
            radius = 10 + 62 * pulse
            alpha = int(165 * (1 - pulse))
            draw.ellipse([sc(820 - radius), sc(244 - radius), sc(820 + radius), sc(244 + radius)], outline=(255, 0, 32, alpha), width=sc(4))
        frames.append(downsample(frame))
    return frames


def render_all() -> dict[str, object]:
    for path in (FINAL, PREVIEW, FRAMES):
        path.mkdir(parents=True, exist_ok=True)

    items = [
        save_outputs("v2_premium_title_brush_reveal", premium_title_frames()),
        save_outputs("v2_route_light_trail", route_frames()),
        save_outputs("v2_odometer_data_callout", data_counter_frames()),
        save_outputs("v2_marker_annotation_arrow", annotation_frames(), background_kind="article"),
    ]
    manifest = {
        "project": "packaging_effect_demos_v2",
        "canvas": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "duration_frames": FRAME_COUNT},
        "rendering": {
            "supersampling": SCALE,
            "alpha_delivery": "ProRes 4444",
            "preview": "GIF files are composited over checker/article backgrounds only for viewing.",
        },
        "items": items,
    }
    metadata_dir = PROJECT / "qa" / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "packaging_effect_demo_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    print(json.dumps(render_all(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
