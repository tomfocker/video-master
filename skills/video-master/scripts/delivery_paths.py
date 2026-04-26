#!/usr/bin/env python3
"""Shared output paths for video-master project packages."""

from __future__ import annotations

from pathlib import Path


FINAL_ROOT = Path("最终交付")
LEGACY_ROOT = Path("deliverables")
METADATA_DIR = Path("qa") / "metadata"

FINAL_STORYBOARD_DIR = FINAL_ROOT / "01_分镜图"
FINAL_PROMPTS_DIR = FINAL_ROOT / "02_提示词"
FINAL_AUDIO_DIR = FINAL_ROOT / "03_口播与字幕"
FINAL_OVERVIEW_DIR = FINAL_ROOT / "04_分镜总览"
FINAL_PREVIEW_DIR = FINAL_ROOT / "05_预览视频"
FINAL_WORKBOOK_DIR = FINAL_ROOT / "06_制作总表"

HANDOFF = FINAL_ROOT / "00_使用说明.md"
VIDEO_PROMPTS = FINAL_PROMPTS_DIR / "视频生成提示词.md"
IMAGE_PROMPTS = FINAL_PROMPTS_DIR / "图片生成提示词.md"
VOICEOVER_SCRIPT = FINAL_AUDIO_DIR / "口播稿.md"
VOICEOVER_TEXT = FINAL_AUDIO_DIR / "口播文本.txt"
VOICEOVER_AUDIO = FINAL_AUDIO_DIR / "口播音频.mp3"
CAPTIONS_ZH = FINAL_AUDIO_DIR / "中文字幕.srt"
CAPTIONS_EN = FINAL_AUDIO_DIR / "英文字幕.srt"
OVERVIEW_PNG = FINAL_OVERVIEW_DIR / "分镜总览图.png"
PREVIEW_MP4 = FINAL_PREVIEW_DIR / "分镜预览.mp4"
WORKBOOK = FINAL_WORKBOOK_DIR / "制作总表.xlsx"
PREVIEW_MANIFEST = METADATA_DIR / "preview_manifest.json"
TTS_MANIFEST = METADATA_DIR / "tts_manifest.json"
OVERVIEW_HTML = METADATA_DIR / "storyboard_overview.html"


def first_existing(project: Path, relative_paths: list[Path]) -> Path:
    for relative in relative_paths:
        path = project / relative
        if path.exists():
            return path
    return project / relative_paths[0]


def storyboard_frame_dir(project: Path) -> Path:
    return first_existing(project, [FINAL_STORYBOARD_DIR, LEGACY_ROOT / "final_storyboard"])


def storyboard_frame_path(project: Path, shot_id: str) -> Path:
    candidates = [
        FINAL_STORYBOARD_DIR / f"{shot_id}.png",
        LEGACY_ROOT / "final_storyboard" / f"{shot_id}.png",
        Path("storyboard") / "frames" / f"{shot_id}.png",
    ]
    return first_existing(project, candidates)


def read_voiceover_audio_path(project: Path) -> Path:
    return first_existing(project, [VOICEOVER_AUDIO, LEGACY_ROOT / "final_audio" / "voiceover.mp3"])


def video_prompt_path(project: Path) -> Path:
    return first_existing(project, [VIDEO_PROMPTS, LEGACY_ROOT / "final_prompts" / "copy_ready_video_prompts.md"])


def image_prompt_path(project: Path) -> Path:
    return first_existing(project, [IMAGE_PROMPTS, LEGACY_ROOT / "final_prompts" / "copy_ready_image_prompts.md"])


def handoff_path(project: Path) -> Path:
    return first_existing(project, [HANDOFF, LEGACY_ROOT / "production_handoff.md"])


def overview_png_path(project: Path) -> Path:
    return first_existing(project, [OVERVIEW_PNG, LEGACY_ROOT / "storyboard_overview.png"])


def preview_mp4_path(project: Path) -> Path:
    return first_existing(project, [PREVIEW_MP4, LEGACY_ROOT / "storyboard_animatic.mp4"])


def preview_manifest_path(project: Path) -> Path:
    return first_existing(project, [PREVIEW_MANIFEST, LEGACY_ROOT / "preview_manifest.json"])


def workbook_path(project: Path) -> Path:
    return first_existing(project, [WORKBOOK, LEGACY_ROOT / "production_workbook.xlsx"])


def voiceover_script_path(project: Path) -> Path:
    return first_existing(project, [VOICEOVER_SCRIPT, LEGACY_ROOT / "final_audio" / "voiceover_script.md"])


def final_audio_dir(project: Path) -> Path:
    return first_existing(project, [FINAL_AUDIO_DIR, LEGACY_ROOT / "final_audio"])
