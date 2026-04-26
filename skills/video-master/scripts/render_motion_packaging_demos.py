#!/usr/bin/env python3
"""Render demo motion-packaging overlays with real alpha-channel animation."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "video_projects" / "packaging_effect_demos"
FINAL = PROJECT / "最终交付" / "07_title_packaging"
PREVIEW = PROJECT / "qa" / "metadata" / "effect_previews"
FRAMES = PROJECT / "packaging" / "motion_frames"

WIDTH = 1280
HEIGHT = 720
FPS = 30
FRAME_COUNT = 72

FONT_KAI = "C:/Windows/Fonts/simkai.ttf"
FONT_HEI = "C:/Windows/Fonts/simhei.ttf"
FONT_DENG_BOLD = "C:/Windows/Fonts/Dengb.ttf"


def get_font(path: str, size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size=size)
    except OSError:
        return ImageFont.load_default()


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def smooth(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, stroke_width: int = 0) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    return right - left, bottom - top


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    y: int,
    fill: tuple[int, int, int, int],
    stroke_fill: tuple[int, int, int, int] | None = None,
    stroke_width: int = 0,
) -> tuple[int, int, int, int]:
    text_width, text_height = text_size(draw, text, font, stroke_width)
    x = (WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
    return x, y, text_width, text_height


def checker_background(size: tuple[int, int] = (640, 360)) -> Image.Image:
    image = Image.new("RGB", size, (26, 28, 36))
    draw = ImageDraw.Draw(image)
    step = 32
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2 == 0:
                draw.rectangle([x, y, x + step - 1, y + step - 1], fill=(36, 38, 48))
    return image.convert("RGBA")


def screenshot_background(size: tuple[int, int] = (640, 360)) -> Image.Image:
    image = Image.new("RGBA", size, (246, 247, 249, 255))
    draw = ImageDraw.Draw(image)
    font = get_font(FONT_HEI, 21)
    small = get_font(FONT_HEI, 16)
    draw.text((42, 44), "现在包装能力支持真实动效：笔刷书写、路线绘制、数字滚动、遮罩擦入、光扫等。", font=font, fill=(36, 39, 48, 255))
    draw.text((42, 92), "正式流程会询问是否需要大标题、章节、人名条、关键数据等包装图片。", font=font, fill=(36, 39, 48, 255))
    draw.text((42, 146), "这里演示的是红线与箭头标注层，成片交付时背景保持透明。", font=small, fill=(110, 116, 128, 255))
    return image


def compose_preview(frame: Image.Image, background_kind: str) -> Image.Image:
    background = screenshot_background() if background_kind == "screenshot" else checker_background()
    small = frame.resize(background.size, Image.Resampling.LANCZOS)
    background.alpha_composite(small)
    return background.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)


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

    preview_frames = [compose_preview(frame, background_kind) for frame in frames[::2]]
    preview_frames[0].save(
        preview_gif,
        save_all=True,
        append_images=preview_frames[1:],
        duration=66,
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


def brush_reveal_frames() -> list[Image.Image]:
    title_font = get_font(FONT_KAI, 126)
    subtitle_font = get_font(FONT_DENG_BOLD, 24)
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x, y, text_width, text_height = draw_centered(
        draw,
        "环球旅行日记",
        title_font,
        250,
        (255, 255, 255, 255),
        stroke_fill=(255, 255, 255, 72),
        stroke_width=1,
    )

    alpha = layer.getchannel("A")
    alpha_draw = ImageDraw.Draw(alpha)
    for index in range(140):
        px = x + (index * 73) % max(1, text_width)
        py = y + 12 + (index * 37) % max(1, text_height)
        if index % 3 == 0:
            alpha_draw.line([(px, py), (px + 28 + index % 31, py + (index % 9) - 4)], fill=92, width=2)
    layer.putalpha(alpha)

    swash_points = []
    for index in range(180):
        progress = index / 179
        px = int(270 + 760 * progress)
        py = int(438 + math.sin(progress * math.pi * 2.2) * 20 - 34 * progress)
        swash_points.append((px, py))
    draw.line(swash_points, fill=(234, 183, 57, 230), width=5, joint="curve")

    subtitle = "AROUND THE WORLD JOURNEY"
    subtitle_width, _ = text_size(draw, subtitle, subtitle_font)
    draw.text(((WIDTH - subtitle_width) // 2, 432), subtitle, font=subtitle_font, fill=(255, 255, 255, 220))
    draw.ellipse([1015, 352, 1060, 401], outline=(218, 28, 48, 230), width=3)
    seal_font = get_font(FONT_HEI, 17)
    draw.text((1025, 360), "旅", font=seal_font, fill=(218, 28, 48, 240))
    draw.text((1025, 378), "记", font=seal_font, fill=(218, 28, 48, 240))

    frames = []
    for index in range(FRAME_COUNT):
        progress = ease(index / (FRAME_COUNT - 1))
        edge = int((WIDTH + 180) * progress) - 120
        mask = Image.new("L", (WIDTH, HEIGHT), 0)
        mask_draw = ImageDraw.Draw(mask)
        polygon = [(0, 0), (edge, 0)]
        for yy in range(0, HEIGHT + 40, 40):
            wave = int(math.sin(yy * 0.047 + index * 0.22) * 24)
            polygon.append((edge + wave, yy))
        polygon += [(0, HEIGHT), (0, 0)]
        mask_draw.polygon(polygon, fill=255)

        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        reveal = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        reveal.alpha_composite(layer)
        reveal.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (WIDTH, HEIGHT), 0), mask))
        frame.alpha_composite(reveal)

        if 0.05 < progress < 0.98:
            frame_draw = ImageDraw.Draw(frame)
            brush_x = edge + int(math.sin(index * 0.6) * 10)
            brush_y = 316 + int(math.sin(index * 0.23) * 18)
            for radius, alpha_value in [(34, 88), (18, 146), (8, 220)]:
                frame_draw.ellipse(
                    [brush_x - radius, brush_y - radius // 2, brush_x + radius, brush_y + radius // 2],
                    fill=(255, 255, 255, alpha_value),
                )
            frame_draw.line([(brush_x - 74, brush_y + 60), (brush_x + 18, brush_y + 18)], fill=(234, 183, 57, 170), width=5)
        frames.append(frame)
    return frames


def bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    a = (1 - t) ** 3
    b = 3 * (1 - t) ** 2 * t
    c = 3 * (1 - t) * t**2
    d = t**3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def route_draw_frames() -> list[Image.Image]:
    route = [bezier((180, 495), (340, 190), (575, 210), (660, 395), index / 120) for index in range(121)]
    route += [bezier((660, 395), (760, 620), (950, 545), (1110, 250), index / 120) for index in range(1, 121)]
    labels = [(180, 495, "PARIS"), (660, 395, "CAPE TOWN"), (1110, 250, "KYOTO")]
    label_font = get_font(FONT_DENG_BOLD, 24)
    title_font = get_font(FONT_DENG_BOLD, 34)
    frames = []
    for index in range(FRAME_COUNT):
        progress = smooth(index / (FRAME_COUNT - 1))
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        for x in range(120, 1180, 120):
            draw.line([(x, 165), (x, 565)], fill=(255, 255, 255, 26), width=1)
        for y in range(190, 560, 80):
            draw.line([(110, y), (1170, y)], fill=(255, 255, 255, 22), width=1)

        end = max(2, int(len(route) * progress))
        drawn = [(int(x), int(y)) for x, y in route[:end]]
        if len(drawn) > 1:
            draw.line(drawn, fill=(34, 209, 238, 72), width=20, joint="curve")
            draw.line(drawn, fill=(245, 196, 66, 240), width=8, joint="curve")
            draw.line(drawn, fill=(255, 255, 255, 230), width=3, joint="curve")

        for label_index, (label_x, label_y, label) in enumerate(labels):
            if progress > (label_index * 0.32 + 0.08):
                draw.ellipse([label_x - 9, label_y - 9, label_x + 9, label_y + 9], fill=(255, 67, 89, 255))
                draw.ellipse([label_x - 4, label_y - 4, label_x + 4, label_y + 4], fill=(255, 255, 255, 255))
                draw.text((label_x - 34, label_y + 18), label, font=label_font, fill=(255, 255, 255, 210))

        tip_x, tip_y = drawn[-1]
        if len(drawn) > 4:
            previous_x, previous_y = drawn[-5]
            angle = math.atan2(tip_y - previous_y, tip_x - previous_x)
        else:
            angle = 0.0

        def rotate(point: tuple[float, float]) -> tuple[float, float]:
            px, py = point
            return (
                tip_x + px * math.cos(angle) - py * math.sin(angle),
                tip_y + px * math.sin(angle) + py * math.cos(angle),
            )

        plane = [rotate((20, 0)), rotate((-16, -11)), rotate((-6, 0)), rotate((-16, 11))]
        draw.polygon(plane, fill=(255, 255, 255, 235))
        draw.line([plane[0], plane[2], plane[3]], fill=(0, 0, 0, 80), width=1)
        draw.text((128, 112), "ROUTE DRAWING", font=title_font, fill=(255, 255, 255, 210))
        frames.append(frame)
    return frames


def number_roll_frames() -> list[Image.Image]:
    label_font = get_font(FONT_HEI, 34)
    big_font = get_font(FONT_DENG_BOLD, 105)
    unit_font = get_font(FONT_DENG_BOLD, 44)
    small_font = get_font(FONT_HEI, 24)
    frames = []
    for index in range(FRAME_COUNT):
        progress = ease(index / (FRAME_COUNT - 1))
        number = int(128640 * progress)
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        panel = [250, 190, 1030, 522]
        draw.rounded_rectangle(panel, radius=26, fill=(13, 22, 34, 214), outline=(105, 225, 205, 180), width=2)
        draw.rectangle([250, 190, 1030, 198], fill=(245, 196, 66, 220))
        draw.text((304, 236), "累计里程", font=label_font, fill=(240, 247, 255, 230))
        draw.text((304, 282), "TOTAL DISTANCE", font=small_font, fill=(137, 211, 222, 210))
        number_text = f"{number:,}"
        number_width, _ = text_size(draw, number_text, big_font)
        draw.text((304, 340), number_text, font=big_font, fill=(255, 255, 255, 255))
        draw.text((326 + number_width, 384), "KM", font=unit_font, fill=(245, 196, 66, 255))

        bar_x, bar_y, bar_width = 304, 478, 620
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + 10], radius=5, fill=(255, 255, 255, 42))
        draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_width * progress), bar_y + 10], radius=5, fill=(105, 225, 205, 220))
        for tick in range(9):
            tick_x = bar_x + tick * bar_width // 8
            tick_height = 16 if tick % 2 == 0 else 10
            draw.line([(tick_x, bar_y + 22), (tick_x, bar_y + 22 + tick_height)], fill=(255, 255, 255, 80), width=2)

        for value_index, (text_x, text_y, value) in enumerate([(760, 245, "6 大洲"), (760, 306, "32 城市"), (760, 367, "4 海洋")]):
            alpha = int(255 * ease(max(0.0, min(1.0, (progress - value_index * 0.18) / 0.35))))
            draw.rounded_rectangle(
                [text_x, text_y, 948, text_y + 42],
                radius=12,
                fill=(255, 255, 255, min(40, alpha // 4)),
                outline=(255, 255, 255, min(90, alpha // 2)),
                width=1,
            )
            draw.text((text_x + 18, text_y + 7), value, font=small_font, fill=(255, 255, 255, alpha))
        frames.append(frame)
    return frames


def annotation_arrow_frames() -> list[Image.Image]:
    frames = []
    red = (255, 0, 28, 255)
    for index in range(FRAME_COUNT):
        progress = smooth(index / (FRAME_COUNT - 1))
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        underline_progress = min(1.0, progress / 0.48)
        x1, y1 = 285, 333
        x2, y2 = 710, 337
        draw.line(
            [(x1, y1), (x1 + (x2 - x1) * underline_progress, y1 + (y2 - y1) * underline_progress)],
            fill=red,
            width=9,
        )

        if progress > 0.36:
            arrow_progress = min(1.0, (progress - 0.36) / 0.52)
            sx, sy = 700, 336
            ex, ey = 885, 270
            current_x = sx + (ex - sx) * arrow_progress
            current_y = sy + (ey - sy) * arrow_progress
            draw.line([(sx, sy), (current_x, current_y)], fill=red, width=9)
            if arrow_progress > 0.82:
                angle = math.atan2(ey - sy, ex - sx)
                tip = (ex, ey)
                for offset in [angle + 2.55, angle - 2.55]:
                    draw.line(
                        [tip, (tip[0] - 35 * math.cos(offset), tip[1] - 35 * math.sin(offset))],
                        fill=red,
                        width=9,
                    )

        if progress > 0.65:
            pulse = (progress - 0.65) / 0.35
            alpha = int(180 * (1 - pulse))
            draw.ellipse([804 - 42 * pulse, 242 - 42 * pulse, 804 + 42 * pulse, 242 + 42 * pulse], outline=(255, 0, 28, alpha), width=5)
        frames.append(frame)
    return frames


def render_all() -> dict[str, object]:
    for path in (FINAL, PREVIEW, FRAMES):
        path.mkdir(parents=True, exist_ok=True)

    items = [
        save_outputs("brush_reveal_title", brush_reveal_frames()),
        save_outputs("route_draw_travel", route_draw_frames()),
        save_outputs("number_roll_distance", number_roll_frames()),
        save_outputs("red_annotation_arrow", annotation_arrow_frames(), background_kind="screenshot"),
    ]
    manifest = {
        "project": "packaging_effect_demos",
        "canvas": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "duration_frames": FRAME_COUNT},
        "note": "Each .mov is encoded as ProRes 4444 with alpha. GIF files are previews composited over a background.",
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
