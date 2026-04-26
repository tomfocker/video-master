#!/usr/bin/env python3
"""Validate a video-master project package.

This checker is intentionally conservative. It verifies the files and metadata
that are easy to drift during agent-generated production packages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pysubs2
from pydantic import BaseModel, ValidationError, field_validator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import (
    FINAL_STORYBOARD_DIR,
    HANDOFF,
    IMAGE_PROMPTS,
    LEGACY_ROOT,
    OVERVIEW_PNG,
    PREVIEW_MANIFEST,
    PREVIEW_MP4,
    TITLE_PACKAGING_MANIFEST,
    VIDEO_PROMPTS,
    VOICEOVER_SCRIPT,
    WORKBOOK,
    final_audio_dir,
    first_existing,
    preview_manifest_path,
    preview_mp4_path,
    title_packaging_dir,
    title_packaging_manifest_path,
    video_prompt_path,
)
from style_templates import TemplateError, load_template


BASE_REQUIRED = [
    ("brief/creative_brief.md", [Path("brief/creative_brief.md")]),
    ("brief/spec_lock.md", [Path("brief/spec_lock.md")]),
    ("strategy/input_readiness.md", [Path("strategy/input_readiness.md")]),
    ("strategy/video_mode.md", [Path("strategy/video_mode.md")]),
    ("strategy/creative_strategy.md", [Path("strategy/creative_strategy.md")]),
    ("strategy/rhythm_map.md", [Path("strategy/rhythm_map.md")]),
    ("script/script.md", [Path("script/script.md")]),
    ("storyboard/shot_list.md", [Path("storyboard/shot_list.md")]),
    ("storyboard/shot_list.json", [Path("storyboard/shot_list.json")]),
    ("storyboard/storyboard_manifest.md", [Path("storyboard/storyboard_manifest.md")]),
    ("prompts/storyboard_image_prompts.md", [Path("prompts/storyboard_image_prompts.md")]),
    ("prompts/video_prompts.md", [Path("prompts/video_prompts.md")]),
    ("audio/voiceover_script.md", [Path("audio/voiceover_script.md")]),
    ("audio/tts_lines.json", [Path("audio/tts_lines.json")]),
    ("audio/captions.srt", [Path("audio/captions.srt")]),
    ("audio/music_sfx_cue_sheet.md", [Path("audio/music_sfx_cue_sheet.md")]),
    ("audio/audio_generation_prompt.md", [Path("audio/audio_generation_prompt.md")]),
    ("最终交付/00_使用说明.md", [HANDOFF, LEGACY_ROOT / "production_handoff.md"]),
    ("最终交付/02_提示词/视频生成提示词.md", [VIDEO_PROMPTS, LEGACY_ROOT / "final_prompts" / "copy_ready_video_prompts.md"]),
    ("最终交付/02_提示词/图片生成提示词.md", [IMAGE_PROMPTS, LEGACY_ROOT / "final_prompts" / "copy_ready_image_prompts.md"]),
    ("最终交付/03_口播与字幕/口播稿.md", [VOICEOVER_SCRIPT, LEGACY_ROOT / "final_audio" / "voiceover_script.md"]),
    ("最终交付/06_制作总表/制作总表.xlsx", [WORKBOOK, LEGACY_ROOT / "production_workbook.xlsx"]),
    ("qa/metadata/preview_manifest.json", [PREVIEW_MANIFEST, LEGACY_ROOT / "preview_manifest.json"]),
]

AD_MODES = {"fast-paced-tvc", "product-promo-short", "ecommerce-conversion-short"}
COPY_POLICY_FIELDS = [
    "copy_language",
    "voiceover_language",
    "caption_language",
    "subtitle_rendering_policy",
    "burned_subtitles_allowed",
]
MIXED_SUBTITLE_FIELDS = [
    "声音/字幕",
    "Audio/Subtitles",
    "Audio/subtitles",
    "Voiceover/subtitles",
    "Voiceover/Subtitles",
]
NO_SUBTITLE_TERMS = [
    "do not generate subtitles",
    "不要字幕",
    "不要内嵌字幕",
    "不要烧录字幕",
    "不要生成字幕",
    "模型生成画面不添加字幕",
    "字幕使用srt后期添加",
    "no subtitles",
    "no captions",
]
NEGATIVE_PROMPT_FIELDS = [
    "负面提示词",
    "Negative prompt",
    "negative prompt",
]
NO_BACKGROUND_MUSIC_TERMS = [
    "不要生成背景音乐",
    "不生成背景音乐",
    "不要背景音乐",
    "no background music",
    "do not generate background music",
    "no music",
]
SFX_TERMS = [
    "SFX",
    "sfx",
    "音效",
    "声音设计",
]
EXTERNAL_VOICEOVER_TERMS = [
    "外部画外音",
    "外部配音",
    "画外音",
    "后期添加",
    "external voiceover",
    "voiceover added in post",
    "post-production voiceover",
]
TITLE_PACKAGING_VIDEO_PROMPT_MARKERS = [
    "title_packaging",
    "alpha_mov",
    "07_title_packaging",
    "标题包装",
    "透明mov",
    "透明通道mov",
]
HIGH_MOTION_TERMS = [
    "高速",
    "快切",
    "赛车",
    "竞速",
    "运动",
    "action",
    "racing",
    "high-speed",
    "rapid-cut",
]
IMPACT_CAMERA_TERMS = [
    "震动",
    "抖动",
    "晃动",
    "手持",
    "车载",
    "冲击",
    "甩镜",
    "pov",
    "handheld",
    "shake",
    "shaky",
    "vibration",
    "impact",
    "whip",
]

class Shot(BaseModel):
    shot_id: str
    duration_seconds: float

    @field_validator("shot_id")
    @classmethod
    def valid_shot_id(cls, value: str) -> str:
        if not re.fullmatch(r"S\d{2,}", value.strip()):
            raise ValueError("shot_id must look like S01")
        return value.strip()

    @field_validator("duration_seconds")
    @classmethod
    def positive_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("duration_seconds must be positive")
        return value


class TTSLine(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must be non-empty")
        return value


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_spec_lock(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        values[key.strip()] = value.strip()
    return values


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", text))


def validate_required_files(project: Path, errors: list[str]) -> None:
    for label, candidates in BASE_REQUIRED:
        if not any((project / candidate).is_file() for candidate in candidates):
            errors.append(f"missing required file: {label}")


def validate_shot_list(project: Path, spec: dict[str, str], errors: list[str]) -> list[dict]:
    shot_path = project / "storyboard" / "shot_list.json"
    if not shot_path.is_file():
        return []
    try:
        shots = json.loads(read_text(shot_path))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in storyboard/shot_list.json: {exc}")
        return []
    if not isinstance(shots, list) or not shots:
        errors.append("storyboard/shot_list.json must be a non-empty list")
        return []

    durations = []
    seen_ids = set()
    for index, shot in enumerate(shots, start=1):
        if not isinstance(shot, dict):
            errors.append(f"shot {index} must be an object")
            continue
        try:
            parsed_shot = Shot.model_validate(shot)
        except ValidationError as exc:
            errors.append(f"shot {index} schema error: {exc.errors()[0]['msg']}")
            continue
        shot_id = parsed_shot.shot_id
        if shot_id in seen_ids:
            errors.append(f"duplicate shot_id: {shot_id}")
        seen_ids.add(shot_id)
        durations.append(parsed_shot.duration_seconds)
        frame = project / "storyboard" / "frames" / f"{shot_id}.png"
        if not frame.is_file() or frame.stat().st_size == 0:
            errors.append(f"missing generated frame for {shot_id}: storyboard/frames/{shot_id}.png")
        deliverable_frame = first_existing(
            project,
            [FINAL_STORYBOARD_DIR / f"{shot_id}.png", LEGACY_ROOT / "final_storyboard" / f"{shot_id}.png"],
        )
        if not deliverable_frame.is_file() or deliverable_frame.stat().st_size == 0:
            errors.append(f"missing deliverable frame for {shot_id}: 最终交付/01_分镜图/{shot_id}.png")

    target = spec.get("target_duration_seconds")
    if target:
        try:
            expected = float(target)
        except ValueError:
            errors.append(f"target_duration_seconds is not numeric: {target}")
        else:
            total = sum(durations)
            if abs(total - expected) > 0.5:
                errors.append(f"shot durations total {total:g}s, expected {expected:g}s")

    video_mode = spec.get("video_mode", "")
    if video_mode in AD_MODES and len(set(durations)) == 1 and len(durations) >= 4:
        errors.append("shot durations are too uniform for an advertising mode")

    validate_director_rhythm(shots, durations, spec, errors)
    return shots


def has_rapid_cut_cluster(durations: list[float], max_duration: float = 2.0, cluster_size: int = 3) -> bool:
    current = 0
    for duration in durations:
        if duration <= max_duration:
            current += 1
            if current >= cluster_size:
                return True
        else:
            current = 0
    return False


def validate_director_rhythm(
    shots: list[dict],
    durations: list[float],
    spec: dict[str, str],
    errors: list[str],
) -> None:
    spec_text = " ".join(str(value) for value in spec.values()).lower()
    high_motion = any(term.lower() in spec_text for term in HIGH_MOTION_TERMS)
    if not high_motion:
        return

    if not has_rapid_cut_cluster(durations):
        errors.append("high-motion pacing requires at least one rapid-cut cluster of 3 shots at 2s or less")

    shot_text_parts = []
    for shot in shots:
        for key in [
            "movement",
            "camera",
            "camera_prompt",
            "visual_action",
            "action",
            "video_prompt_seed",
            "notes",
        ]:
            if key in shot:
                shot_text_parts.append(str(shot[key]))
    shot_text = " ".join(shot_text_parts).lower()
    if not any(term.lower() in shot_text for term in IMPACT_CAMERA_TERMS):
        errors.append("high-motion pacing requires impact camera language such as handheld, shake, POV, whip, or vehicle vibration")


def validate_audio(project: Path, errors: list[str]) -> None:
    tts_path = project / "audio" / "tts_lines.json"
    if not tts_path.is_file():
        return
    try:
        data = json.loads(read_text(tts_path))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in audio/tts_lines.json: {exc}")
        return
    if not isinstance(data, list) or not data:
        errors.append("audio/tts_lines.json must be a non-empty list")
        return
    for index, row in enumerate(data, start=1):
        try:
            TTSLine.model_validate(row)
        except ValidationError as exc:
            errors.append(f"audio/tts_lines.json row {index} schema error: {exc.errors()[0]['msg']}")
    captions = project / "audio" / "captions.srt"
    if captions.is_file():
        try:
            subs = pysubs2.load(str(captions))
        except Exception as exc:
            errors.append(f"invalid SRT in audio/captions.srt: {exc}")
        else:
            if not subs:
                errors.append("audio/captions.srt must contain at least one caption")


def validate_srt_file(path: Path, label: str, errors: list[str]) -> None:
    try:
        subs = pysubs2.load(str(path))
    except Exception as exc:
        errors.append(f"invalid SRT in {label}: {exc}")
        return
    if not subs:
        errors.append(f"{label} must contain at least one caption")


def validate_final_subtitles(project: Path, spec: dict[str, str], errors: list[str]) -> None:
    final_audio = final_audio_dir(project)
    final_srt_files = sorted(final_audio.glob("*.srt")) if final_audio.is_dir() else []
    if not final_srt_files:
        errors.append("missing final subtitle deliverable: 最终交付/03_口播与字幕/*.srt")
        return

    for path in final_srt_files:
        validate_srt_file(path, path.relative_to(project).as_posix(), errors)

    file_names = " ".join(path.name.lower() for path in final_srt_files)
    has_english_srt = "en" in file_names or "英文" in file_names
    has_chinese_srt = "zh" in file_names or "cn" in file_names or "中文" in file_names
    voiceover_language = spec.get("voiceover_language", "").lower()
    caption_language = spec.get("caption_language", "").lower()
    localized_caption_languages = spec.get("localized_caption_languages", "").lower()

    if ("en" in voiceover_language or "en" in caption_language) and not has_english_srt:
        errors.append("missing English final subtitle file: 最终交付/03_口播与字幕/英文字幕.srt")
    if "zh" in localized_caption_languages and not has_chinese_srt:
        errors.append("missing Chinese final subtitle file: 最终交付/03_口播与字幕/中文字幕.srt")


def validate_prompt_language(project: Path, spec: dict[str, str], errors: list[str]) -> None:
    prompt_language = spec.get("prompt_language", "")
    prompt_text_path = project / "prompts" / "video_prompts.md"
    deliverable_prompt_path = video_prompt_path(project)
    texts = []
    for path in [prompt_text_path, deliverable_prompt_path]:
        if path.is_file():
            texts.append(read_text(path))
    prompt_text = "\n".join(texts)
    if prompt_language.lower().startswith("zh") and not has_cjk(prompt_text):
        errors.append("Chinese prompt language requested but video prompts contain no Chinese text")


def parse_boolish_false(value: str) -> bool:
    return value.strip().lower() in {"false", "no", "0", "否", "不", "不允许"}


def parse_boolish_true(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "on", "enabled", "是", "开启", "啟用"}


def validate_copy_and_subtitle_policy(project: Path, spec: dict[str, str], errors: list[str]) -> None:
    for field in COPY_POLICY_FIELDS:
        if not spec.get(field):
            errors.append(f"spec_lock missing audio policy field: {field}")

    subtitle_policy = spec.get("subtitle_rendering_policy", "").strip().lower()
    burned_subtitles_allowed = spec.get("burned_subtitles_allowed", "")
    burned_disabled = parse_boolish_false(burned_subtitles_allowed) or "post-production" in subtitle_policy
    if not burned_disabled:
        return

    prompt_paths = [
        project / "prompts" / "video_prompts.md",
        video_prompt_path(project),
    ]
    prompt_text = "\n".join(read_text(path) for path in prompt_paths if path.is_file())
    if any(label in prompt_text for label in MIXED_SUBTITLE_FIELDS):
        errors.append(
            "final video prompts mixes voiceover and subtitle instructions; "
            "use separate voiceover/audio and on-screen text policy fields"
        )
    if prompt_text and not any(term.lower() in prompt_text.lower() for term in NO_SUBTITLE_TERMS):
        errors.append(
            "subtitle policy disables burned subtitles but final video prompts do not say "
            "do not generate subtitles"
        )


def split_final_prompt_blocks(prompt_text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^##\s+(S\d{2,}\b[^\n]*)", prompt_text))
    if not matches:
        return []
    blocks = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(prompt_text)
        blocks.append((match.group(1).strip(), prompt_text[start:end]))
    return blocks


def load_tts_text_lines(project: Path) -> list[str]:
    tts_path = project / "audio" / "tts_lines.json"
    if not tts_path.is_file():
        return []
    try:
        data = json.loads(read_text(tts_path))
    except json.JSONDecodeError:
        return []
    lines = []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("voiceover") or item.get("dialogue") or "").strip()
        if len(text) >= 12:
            lines.append(text)
    return lines


def validate_final_video_prompt_audio_contract(project: Path, errors: list[str]) -> None:
    prompt_path = video_prompt_path(project)
    if not prompt_path.is_file():
        return
    prompt_text = read_text(prompt_path)
    prompt_text_lower = prompt_text.lower()

    if any(field in prompt_text for field in NEGATIVE_PROMPT_FIELDS):
        errors.append("final video prompts must not use negative prompt fields; use positive generation requirements instead")

    blocks = split_final_prompt_blocks(prompt_text)
    for label, block in blocks:
        block_lower = block.lower()
        if not any(term.lower() in block_lower for term in NO_BACKGROUND_MUSIC_TERMS):
            errors.append(f"{label} missing no-background-music instruction")
        if not any(term.lower() in block for term in SFX_TERMS):
            errors.append(f"{label} missing SFX sound design")

    external_voiceover = any(term.lower() in prompt_text_lower for term in EXTERNAL_VOICEOVER_TERMS)
    if not external_voiceover:
        return
    for line in load_tts_text_lines(project):
        if line in prompt_text:
            errors.append("external voiceover video prompts must not repeat transcript text; keep VO copy in audio files/SRT")
            break


def validate_style_template(project: Path, spec: dict[str, str], errors: list[str]) -> None:
    template_id = spec.get("template_id", "").strip()
    style_route = spec.get("style_route", "").strip()
    template_strength = spec.get("template_strength", "").strip()
    if template_strength:
        errors.append("template_strength is no longer supported; template rules apply as a whole and explicit user ideas override them")

    if not template_id:
        if style_route == "use_style_template":
            errors.append("template_id is required when style_route is use_style_template")
        return

    try:
        template = load_template(template_id)
    except TemplateError as exc:
        errors.append(str(exc))
        return

    allow_draft = spec.get("allow_draft_template", "false").strip().lower() == "true"
    if template["status"] == "draft" and not allow_draft:
        errors.append(f"draft template requires allow_draft_template: true: {template_id}")

    rhythm_map = project / "strategy" / "rhythm_map.md"
    rhythm_text = read_text(rhythm_map) if rhythm_map.is_file() else ""
    if template_id not in rhythm_text:
        errors.append("rhythm_map must name selected template")

    prompt_validation = template.get("prompt_validation")
    if not prompt_validation:
        return

    required_terms = prompt_validation.get("required_terms", [])
    minimum_matches = prompt_validation.get("minimum_matches", 0)
    final_prompt = video_prompt_path(project)
    prompt_text = read_text(final_prompt) if final_prompt.is_file() else ""
    prompt_text_lower = prompt_text.lower()
    matches = [term for term in required_terms if term.strip().lower() in prompt_text_lower]
    if len(matches) < minimum_matches:
        errors.append(
            f"{template_id} prompts must carry the template visual language "
            f"({len(matches)}/{minimum_matches} required terms matched)"
        )


def validate_storyboard_overview(project: Path, errors: list[str]) -> None:
    overview_candidates = [
        project / OVERVIEW_PNG,
        project / LEGACY_ROOT / "storyboard_overview.png",
        project / LEGACY_ROOT / "storyboard_overview.html",
    ]
    if not any(path.is_file() for path in overview_candidates):
        errors.append("missing storyboard overview: 最终交付/04_分镜总览/分镜总览图.png")


def validate_preview_manifest(project: Path, errors: list[str]) -> None:
    manifest_path = preview_manifest_path(project)
    if not manifest_path.is_file():
        return
    try:
        manifest = json.loads(read_text(manifest_path))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in qa/metadata/preview_manifest.json: {exc}")
        return
    if not isinstance(manifest, dict):
        errors.append("qa/metadata/preview_manifest.json must be an object")
        return
    for field in ["title", "preview_profile", "shot_count", "skipped", "output"]:
        if field not in manifest:
            errors.append(f"preview manifest missing field: {field}")

    if manifest.get("skipped") is True:
        if manifest.get("preview_profile") != "off":
            errors.append("preview manifest skipped=true requires preview_profile=off")
        return

    animatic_path = preview_mp4_path(project)
    if not animatic_path.is_file():
        errors.append("missing required file: 最终交付/05_预览视频/分镜预览.mp4")

    for field in [
        "title",
        "preview_profile",
        "shot_count",
        "skipped",
        "output",
        "title_card",
        "end_card",
        "shot_overlays",
        "burned_captions",
        "ken_burns_motion",
        "motion_style",
        "voiceover_audio",
    ]:
        if field not in manifest:
            errors.append(f"preview manifest missing field: {field}")


def validate_title_packaging(project: Path, spec: dict[str, str], errors: list[str]) -> None:
    plan_path = project / "packaging" / "title_packaging_plan.json"
    manifest_path = title_packaging_manifest_path(project)
    enabled = parse_boolish_true(spec.get("title_packaging_enabled", ""))
    if not enabled and not plan_path.exists() and not manifest_path.exists():
        return

    prompt_path = video_prompt_path(project)
    prompt_text = read_text(prompt_path) if prompt_path.is_file() else ""
    prompt_text_lower = prompt_text.lower()
    if any(marker.lower() in prompt_text_lower for marker in TITLE_PACKAGING_VIDEO_PROMPT_MARKERS):
        errors.append("title packaging must stay out of copy-ready video prompts")

    if not plan_path.is_file():
        errors.append("missing title packaging plan: packaging/title_packaging_plan.json")
    if not manifest_path.is_file():
        errors.append(f"missing title packaging manifest: {TITLE_PACKAGING_MANIFEST.as_posix()}")
        return

    try:
        manifest = json.loads(read_text(manifest_path))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {TITLE_PACKAGING_MANIFEST.as_posix()}: {exc}")
        return
    if not isinstance(manifest, dict):
        errors.append(f"{TITLE_PACKAGING_MANIFEST.as_posix()} must be an object")
        return
    if manifest.get("title_packaging") is not True:
        errors.append("title packaging manifest must set title_packaging=true")

    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        errors.append("title packaging manifest requires a non-empty items list")
        return

    final_dir = title_packaging_dir(project)
    if not final_dir.is_dir():
        errors.append("missing title packaging final directory: 鏈€缁堜氦浠?/07_title_packaging")

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"title packaging manifest item {index} must be an object")
            continue
        png = item.get("transparent_png")
        if not png:
            errors.append(f"title packaging manifest item {index} missing transparent_png")
        else:
            png_path = project / str(png)
            if not png_path.is_file() or png_path.stat().st_size == 0:
                errors.append(f"missing title packaging transparent PNG: {png}")
        mov = item.get("alpha_mov")
        if mov:
            mov_path = project / str(mov)
            if not mov_path.is_file() or mov_path.stat().st_size == 0:
                errors.append(f"missing title packaging alpha MOV: {mov}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a video-master project package.")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    errors: list[str] = []
    if not project.is_dir():
        print(f"ERROR: project directory does not exist: {project}")
        return 2

    validate_required_files(project, errors)
    spec_path = project / "brief" / "spec_lock.md"
    spec = parse_spec_lock(read_text(spec_path)) if spec_path.is_file() else {}
    validate_shot_list(project, spec, errors)
    validate_audio(project, errors)
    validate_final_subtitles(project, spec, errors)
    validate_prompt_language(project, spec, errors)
    validate_copy_and_subtitle_policy(project, spec, errors)
    validate_final_video_prompt_audio_contract(project, errors)
    validate_style_template(project, spec, errors)
    validate_storyboard_overview(project, errors)
    validate_preview_manifest(project, errors)
    validate_title_packaging(project, spec, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
