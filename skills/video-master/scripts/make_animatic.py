#!/usr/bin/env python3
"""Create a packaged storyboard animatic preview video."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import PREVIEW_MANIFEST, PREVIEW_MP4, read_voiceover_audio_path, storyboard_frame_path


FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

PREVIEW_PROFILES = {
    "draft": {"fps": 12, "fallback_size": (720, 1280), "long_edge": 1280},
    "smooth": {"fps": 15, "fallback_size": (1080, 1920), "long_edge": 1920},
}


def parse_size(value: str) -> tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        parsed = int(width), int(height)
    except Exception as exc:
        raise argparse.ArgumentTypeError("size must look like 1080x1920") from exc
    if parsed[0] <= 0 or parsed[1] <= 0:
        raise argparse.ArgumentTypeError("size values must be positive")
    return parsed


def load_shots(project: Path) -> list[dict]:
    path = project / "storyboard" / "shot_list.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing shot list: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("storyboard/shot_list.json must be a non-empty list")
    return data


def parse_spec_lock(project: Path) -> dict[str, str]:
    path = project / "brief" / "spec_lock.md"
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        values[key.strip()] = value.strip()
    return values


def parse_aspect_ratio(value: str) -> float | None:
    cleaned = value.strip().lower().replace("：", ":")
    if not cleaned:
        return None
    for separator in [":", "/", "x", "×"]:
        if separator in cleaned:
            left, right = cleaned.split(separator, 1)
            try:
                width = float(left.strip())
                height = float(right.strip())
            except ValueError:
                return None
            if width > 0 and height > 0:
                return width / height
            return None
    try:
        ratio = float(cleaned)
    except ValueError:
        return None
    return ratio if ratio > 0 else None


def even_dimension(value: float) -> int:
    rounded = max(2, int(round(value)))
    return rounded if rounded % 2 == 0 else rounded - 1


def infer_size_from_aspect_ratio(aspect_ratio: str, long_edge: int) -> tuple[int, int] | None:
    ratio = parse_aspect_ratio(aspect_ratio)
    if ratio is None:
        return None
    if ratio >= 1:
        return even_dimension(long_edge), even_dimension(long_edge / ratio)
    return even_dimension(long_edge * ratio), even_dimension(long_edge)


def default_preview_size(project: Path, profile: dict) -> tuple[int, int]:
    spec = parse_spec_lock(project)
    inferred = infer_size_from_aspect_ratio(str(spec.get("aspect_ratio", "")), int(profile["long_edge"]))
    if inferred:
        return inferred
    return tuple(profile["fallback_size"])


def infer_title(project: Path) -> str:
    brief = project / "brief" / "creative_brief.md"
    if brief.is_file():
        for line in brief.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip().lstrip("#").strip()
            if cleaned:
                return cleaned[:48]
    return project.name.replace("_", " ").replace("-", " ").strip() or "Video Master Preview"


def frame_path(project: Path, shot_id: str) -> Path:
    path = storyboard_frame_path(project, shot_id)
    if path.is_file():
        return path
    raise FileNotFoundError(f"missing frame for {shot_id}")


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def ease_in_out(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return 0.5 - 0.5 * math.cos(math.pi * progress)


def calculate_crop(
    source_size: tuple[int, int],
    output_size: tuple[int, int],
    progress: float,
    enable_motion: bool,
    motion_style: str,
) -> dict[str, float | int]:
    source_width, source_height = source_size
    output_width, output_height = output_size
    base_scale = max(output_width / source_width, output_height / source_height)
    eased = ease_in_out(progress)
    active_style = motion_style if enable_motion else "none"
    zoom_amount = 0.0
    if active_style == "center-zoom":
        zoom_amount = 0.025 * eased
    elif active_style == "pan-zoom":
        zoom_amount = 0.035 * eased

    scale = base_scale * (1.0 + zoom_amount)
    resized_width = max(output_width, round(source_width * scale))
    resized_height = max(output_height, round(source_height * scale))
    max_x = max(0, resized_width - output_width)
    max_y = max(0, resized_height - output_height)

    if active_style == "pan-zoom":
        left = round(max_x * (0.48 + 0.04 * eased))
        top = round(max_y * (0.48 + 0.04 * eased))
    else:
        left = round(max_x / 2)
        top = round(max_y / 2)

    return {
        "scale": scale,
        "resized_width": resized_width,
        "resized_height": resized_height,
        "left": left,
        "top": top,
    }


def cover_frame(path: Path, size: tuple[int, int], progress: float, enable_motion: bool, motion_style: str) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        crop = calculate_crop(image.size, size, progress, enable_motion, motion_style)
        resized = image.resize(
            (int(crop["resized_width"]), int(crop["resized_height"])),
            Image.Resampling.LANCZOS,
        )
        left = int(crop["left"])
        top = int(crop["top"])
        return resized.crop((left, top, left + size[0], top + size[1]))


def draw_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str | tuple[int, ...]) -> None:
    try:
        draw.rounded_rectangle(box, radius=14, fill=fill)
    except AttributeError:
        draw.rectangle(box, fill=fill)


def add_text_overlay(image: Image.Image, shot: dict, duration: float) -> Image.Image:
    canvas = image.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    margin = max(18, round(width * 0.035))
    font = load_font(max(18, round(width * 0.035)))
    small = load_font(max(15, round(width * 0.027)))
    shot_id = str(shot.get("shot_id", "")).strip() or "SHOT"
    beat = str(shot.get("beat", "")).strip()
    title = f"{shot_id}  {duration:g}s"
    if beat:
        title = f"{title}  {beat}"
    action = str(shot.get("visual_action", "") or shot.get("visual", "") or "").strip()
    lines = [title]
    if action:
        lines.append(action[:34])
    text_heights = []
    max_text_width = 0
    for line, line_font in zip(lines, [font, small]):
        bbox = draw.textbbox((0, 0), line, font=line_font)
        text_heights.append(bbox[3] - bbox[1])
        max_text_width = max(max_text_width, bbox[2] - bbox[0])
    box_height = sum(text_heights) + margin
    box_width = min(width - margin * 2, max_text_width + margin * 2)
    draw_box(draw, (margin, margin, margin + box_width, margin + box_height), (0, 0, 0, 150))
    y = margin + round(margin * 0.38)
    draw.text((margin + round(margin * 0.55), y), lines[0], fill=(255, 255, 255, 245), font=font)
    if len(lines) > 1:
        y += text_heights[0] + round(margin * 0.2)
        draw.text((margin + round(margin * 0.55), y), lines[1], fill=(230, 236, 240, 230), font=small)
    return canvas.convert("RGB")


def parse_timecode(value: str) -> float:
    value = value.strip().replace(",", ".")
    parts = value.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return float(value)


def load_captions(project: Path) -> list[dict]:
    srt_path = project / "audio" / "captions.srt"
    if srt_path.is_file():
        blocks = [block.strip() for block in srt_path.read_text(encoding="utf-8").split("\n\n") if block.strip()]
        captions = []
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if len(lines) >= 2 and "-->" in lines[1]:
                time_line = lines[1]
                text_lines = lines[2:]
            elif lines and "-->" in lines[0]:
                time_line = lines[0]
                text_lines = lines[1:]
            else:
                continue
            start, end = [part.strip() for part in time_line.split("-->", 1)]
            text = " ".join(text_lines).strip()
            if text:
                captions.append({"start": parse_timecode(start), "end": parse_timecode(end), "text": text})
        return captions

    tts_path = project / "audio" / "tts_lines.json"
    if tts_path.is_file():
        data = json.loads(tts_path.read_text(encoding="utf-8"))
        captions = []
        for item in data if isinstance(data, list) else []:
            text = str(item.get("text") or item.get("voiceover") or item.get("dialogue") or "").strip()
            if not text:
                continue
            start = item.get("start_seconds", item.get("start", 0))
            end = item.get("end_seconds", item.get("end", 0))
            try:
                captions.append({"start": parse_timecode(str(start)), "end": parse_timecode(str(end)), "text": text})
            except (TypeError, ValueError):
                continue
        return captions

    return []


def caption_at(captions: list[dict], seconds: float) -> str:
    for caption in captions:
        if float(caption["start"]) <= seconds < float(caption["end"]):
            return str(caption["text"])
    return ""


def add_caption(image: Image.Image, text: str) -> Image.Image:
    if not text:
        return image
    canvas = image.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    margin = max(18, round(width * 0.04))
    font = load_font(max(20, round(width * 0.038)))
    max_chars = max(10, round(width / max(18, font.size if hasattr(font, "size") else 24) * 1.8))
    lines = []
    remaining = text
    while remaining:
        lines.append(remaining[:max_chars])
        remaining = remaining[max_chars:]
    lines = lines[:2]
    line_boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_height = max((box[3] - box[1] for box in line_boxes), default=24)
    band_height = line_height * len(lines) + margin
    top = height - band_height - margin
    draw_box(draw, (margin, top, width - margin, height - margin), (0, 0, 0, 165))
    y = top + round(margin * 0.35)
    for line, box in zip(lines, line_boxes):
        text_width = box[2] - box[0]
        draw.text(((width - text_width) // 2, y), line, fill=(255, 255, 255, 250), font=font)
        y += line_height
    return canvas.convert("RGB")


def create_card(size: tuple[int, int], title: str, kicker: str, subtitle: str) -> np.ndarray:
    width, height = size
    image = Image.new("RGB", size, "#111417")
    draw = ImageDraw.Draw(image)
    title_font = load_font(max(28, round(width * 0.075)))
    kicker_font = load_font(max(16, round(width * 0.032)))
    subtitle_font = load_font(max(18, round(width * 0.038)))
    accent = "#e8d8b8"
    draw.rectangle((0, 0, width, height), fill="#111417")
    draw.rectangle((0, 0, width, round(height * 0.012)), fill=accent)
    draw.rectangle((round(width * 0.08), round(height * 0.18), round(width * 0.10), round(height * 0.35)), fill=accent)
    y = round(height * 0.24)
    x = round(width * 0.14)
    draw.text((x, y), kicker, fill="#d7dde2", font=kicker_font)
    y += round(height * 0.055)
    max_title_width = round(width * 0.76)
    title_lines = wrap_text(draw, title, title_font, max_title_width, max_lines=3)
    for line in title_lines:
        draw.text((x, y), line, fill="#ffffff", font=title_font)
        bbox = draw.textbbox((0, 0), line, font=title_font)
        y += bbox[3] - bbox[1] + round(height * 0.012)
    y += round(height * 0.025)
    for line in wrap_text(draw, subtitle, subtitle_font, max_title_width, max_lines=2):
        draw.text((x, y), line, fill="#b9c1c8", font=subtitle_font)
        bbox = draw.textbbox((0, 0), line, font=subtitle_font)
        y += bbox[3] - bbox[1] + round(height * 0.012)
    return np.asarray(image)


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = f"{current}{char}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and bbox[2] - bbox[0] > max_width:
            lines.append(current)
            current = char
            if len(lines) >= max_lines:
                break
        else:
            current = candidate
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines or [text[:18]]


def append_card(writer: imageio.Writer, frame: np.ndarray, seconds: float, fps: int) -> int:
    repeat = max(1, round(seconds * fps))
    for _ in range(repeat):
        writer.append_data(frame)
    return repeat


def append_shot_frames(
    writer: imageio.Writer,
    project: Path,
    shot: dict,
    size: tuple[int, int],
    fps: int,
    captions: list[dict],
    current_time: float,
    enable_overlays: bool,
    enable_captions: bool,
    enable_motion: bool,
    motion_style: str,
) -> tuple[int, float]:
    shot_id = str(shot.get("shot_id", "")).strip()
    duration = float(shot.get("duration_seconds", 1))
    repeat = max(1, round(duration * fps))
    path = frame_path(project, shot_id)
    for frame_index in range(repeat):
        progress = frame_index / max(1, repeat - 1)
        local_time = frame_index / fps
        image = cover_frame(path, size, progress, enable_motion, motion_style)
        if enable_overlays:
            image = add_text_overlay(image, shot, duration)
        if enable_captions:
            image = add_caption(image, caption_at(captions, current_time + local_time))
        writer.append_data(np.asarray(image))
    return repeat, duration


def mux_voiceover(video_path: Path, audio_path: Path, output_path: Path, duration_seconds: float) -> None:
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
    except ImportError as exc:
        raise RuntimeError("imageio-ffmpeg is required to mux voiceover audio") from exc

    command = [
        get_ffmpeg_exe(),
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-t",
        f"{duration_seconds:.3f}",
        str(output_path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffmpeg failed while muxing voiceover audio")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an MP4 animatic from storyboard frames.")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument(
        "--preview-profile",
        choices=["draft", "smooth", "off"],
        default="draft",
        help="Preview render profile. Use off to skip MP4 generation.",
    )
    parser.add_argument("--fps", type=int, help="Override frames per second for the preview")
    parser.add_argument("--size", type=parse_size, help="Override output size, e.g. 1080x1920")
    parser.add_argument("--title", help="Preview title shown on the opening card")
    parser.add_argument("--title-card-seconds", type=float, default=1.5, help="Opening card duration")
    parser.add_argument("--end-card-seconds", type=float, default=1.5, help="Ending card duration")
    parser.add_argument("--voiceover-audio", type=Path, help="Optional TTS/VO audio file to mux into the preview")
    parser.add_argument("--no-title-card", action="store_true", help="Disable the opening card")
    parser.add_argument("--no-end-card", action="store_true", help="Disable the ending card")
    parser.add_argument("--no-shot-overlays", action="store_true", help="Disable shot ID/beat overlays")
    parser.add_argument("--no-burn-captions", action="store_true", help="Disable subtitle burn-in")
    parser.add_argument("--no-ken-burns", action="store_true", help="Disable subtle pan/zoom motion")
    parser.add_argument(
        "--motion-style",
        choices=["center-zoom", "pan-zoom", "none"],
        default="none",
        help="Motion style for still frames. Default none keeps storyboard frames stable.",
    )
    parser.add_argument("-o", "--output", type=Path, help="Output MP4 path")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not project.is_dir():
        print(f"ERROR: project directory does not exist: {project}")
        return 2

    profile = PREVIEW_PROFILES.get(args.preview_profile, PREVIEW_PROFILES["draft"])
    fps = args.fps if args.fps is not None else profile["fps"]
    size = args.size if args.size is not None else default_preview_size(project, profile)
    if fps <= 0:
        print("ERROR: fps must be positive")
        return 2
    if args.title_card_seconds < 0 or args.end_card_seconds < 0:
        print("ERROR: card durations cannot be negative")
        return 2

    voiceover_audio = args.voiceover_audio
    if voiceover_audio is None:
        candidate = read_voiceover_audio_path(project)
        if candidate.is_file():
            voiceover_audio = candidate
    if voiceover_audio is not None:
        voiceover_audio = voiceover_audio.resolve()
        if not voiceover_audio.is_file():
            print(f"ERROR: voiceover audio does not exist: {voiceover_audio}")
            return 2

    shots = load_shots(project)
    title = args.title or infer_title(project)
    output = args.output or project / PREVIEW_MP4
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = project / PREVIEW_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    if args.preview_profile == "off":
        manifest = {
            "title": title,
            "preview_profile": "off",
            "output": False,
            "fps": 0,
            "size": "",
            "shot_count": len(shots),
            "frame_count": 0,
            "duration_seconds": 0,
            "skipped": True,
            "title_card": False,
            "end_card": False,
            "shot_overlays": False,
            "burned_captions": False,
            "ken_burns_motion": False,
            "motion_style": "none",
            "voiceover_audio": False,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Animatic skipped by preview profile: {manifest_path}")
        return 0

    captions = load_captions(project)
    video_only_output = output
    if voiceover_audio is not None:
        video_only_output = output.with_name(f"{output.stem}.video-only.tmp{output.suffix}")

    title_card_enabled = not args.no_title_card and args.title_card_seconds > 0
    end_card_enabled = not args.no_end_card and args.end_card_seconds > 0
    captions_enabled = not args.no_burn_captions and bool(captions)
    overlays_enabled = not args.no_shot_overlays
    motion_style = "none" if args.no_ken_burns else args.motion_style
    motion_enabled = motion_style != "none"
    total_frames = 0
    timeline_seconds = 0.0
    project_seconds = 0.0

    try:
        with imageio.get_writer(video_only_output, fps=fps, codec="libx264", macro_block_size=1) as writer:
            if title_card_enabled:
                frame = create_card(size, title, "VIDEO MASTER", "分镜动态预览")
                total_frames += append_card(writer, frame, args.title_card_seconds, fps)
                timeline_seconds += args.title_card_seconds
            for shot in shots:
                frames_written, duration = append_shot_frames(
                    writer,
                    project,
                    shot,
                    size,
                    fps,
                    captions,
                    project_seconds,
                    overlays_enabled,
                    captions_enabled,
                    motion_enabled,
                    motion_style,
                )
                total_frames += frames_written
                timeline_seconds += duration
                project_seconds += duration
            if end_card_enabled:
                frame = create_card(size, "包装参考", "PREVIEW PACKAGE", "分镜图 / 字幕 / 配音轨 / 视频提示词")
                total_frames += append_card(writer, frame, args.end_card_seconds, fps)
                timeline_seconds += args.end_card_seconds
        if voiceover_audio is not None:
            mux_voiceover(video_only_output, voiceover_audio, output, total_frames / fps)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        if voiceover_audio is not None and video_only_output != output and video_only_output.exists():
            video_only_output.unlink()

    manifest = {
        "title": title,
        "preview_profile": args.preview_profile,
        "output": str(output.resolve()),
        "fps": fps,
        "size": f"{size[0]}x{size[1]}",
        "shot_count": len(shots),
        "frame_count": total_frames,
        "duration_seconds": round(total_frames / fps, 3),
        "skipped": False,
        "title_card": title_card_enabled,
        "end_card": end_card_enabled,
        "shot_overlays": overlays_enabled,
        "burned_captions": captions_enabled,
        "ken_burns_motion": motion_enabled,
        "motion_style": motion_style,
        "voiceover_audio": str(voiceover_audio) if voiceover_audio is not None else False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Animatic: {output}")
    print(f"Preview manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
