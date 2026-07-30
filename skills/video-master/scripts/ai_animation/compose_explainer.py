#!/usr/bin/env python3
"""Compose a deterministic explainer timeline from a structured beat brief."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[2]
MOTION_DIR = SKILL_DIR / "ai_animation" / "motion_templates"
SPATIAL_DIR = SKILL_DIR / "ai_animation" / "spatial_camera"
UPSTREAM_COMMIT = "01c393f9f26b5b0d8432fa02682ceb36f6cc3e0f"
DEFAULT_MOTION_STANDARD = {
    "max_static_interval_seconds": 2.0,
    "transition_continuity": "spatial-or-semantic-linked",
    "camera_movement": "point-to-point",
    "depth_of_field": "near-sharp-far-soft",
    "flat_slide_forbidden": True,
    "element_jump_forbidden": True,
    "ambient_float": "subtle-only",
}

ROUTES = {
    "hook": ["number-impact", "key-point-marker"],
    "definition": ["concept-spotlight"],
    "spatial": ["spatial-camera"],
    "concept-map": ["spatial-camera"],
    "mechanism-map": ["spatial-camera"],
    "cause": ["cause-chain"],
    "reasoning": ["cause-chain"],
    "misconception": ["myth-fact-swap"],
    "process": ["three-step-flow"],
    "recap": ["checklist-pop"],
    "action": ["checklist-pop"],
    "checklist": ["checklist-pop"],
    "trend": ["line-chart-draw", "turning-point-line"],
    "data": ["bar-chart-grow", "big-number-card"],
    "comparison": ["horizontal-bar-compare", "stat-duel"],
}


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def safe_id(value: object, label: str) -> str:
    text = str(value or "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
        raise ValueError(f"{label} must use lowercase hyphen-case: {text or '<missing>'}")
    return text


def seconds_to_srt(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def load_catalog(path: Path) -> dict[str, dict[str, Any]]:
    items = read_object(path).get("templates")
    if not isinstance(items, list):
        raise ValueError(f"catalog requires templates: {path}")
    return {str(item["id"]): item for item in items if isinstance(item, dict) and item.get("id")}


def copy_template(source: Path, destination: Path, *, force: bool) -> None:
    if destination.exists():
        if not force:
            raise ValueError(f"composition already exists: {destination}; pass --force to replace it")
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def auto_variables(template_id: str, beat: dict[str, Any], palette: dict[str, Any]) -> dict[str, Any]:
    copy = beat.get("on_screen_copy", "")
    lines = [str(item).strip() for item in copy] if isinstance(copy, list) else [part.strip() for part in str(copy).split("|")]
    lines = [line for line in lines if line]
    first = lines[0] if lines else str(beat.get("voiceover", ""))[:28]
    rest = lines[1:]
    values: dict[str, Any] = {}
    if template_id == "number-impact":
        values = {"hero": "?", "label": "核心问题", "value": 100, "unit": "%", "caption": first}
    elif template_id == "concept-spotlight":
        values = {"label": "核心概念", "term": first, "definition": rest[0] if rest else str(beat.get("voiceover", "")), "note": rest[1] if len(rest) > 1 else "概念解释"}
    elif template_id == "cause-chain":
        values = {"title": first, "cause": rest[0] if rest else "输入信息有限", "mechanism": rest[1] if len(rest) > 1 else "按概率继续生成", "result": rest[2] if len(rest) > 2 else "错误也可能很流畅"}
    elif template_id == "myth-fact-swap":
        values = {"mythLabel": "常见误区", "myth": first, "factLabel": "更准确的说法", "fact": rest[0] if rest else str(beat.get("voiceover", "")), "caption": rest[1] if len(rest) > 1 else "纠正认知"}
    elif template_id == "checklist-pop":
        values = {"title": first, "item1": rest[0] if rest else "要求给出来源", "item2": rest[1] if len(rest) > 1 else "交叉验证关键事实", "item3": rest[2] if len(rest) > 2 else "不确定时明确说不知道"}
    color_keys = {"accent", "foreground"}
    if template_id == "spatial-camera":
        color_keys.add("secondary")
    values.update({key: value for key, value in palette.items() if key in color_keys})
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        brief = read_object(args.brief.resolve())
        if brief.get("schema_version") != 1:
            raise ValueError("beat brief schema_version must be 1")
        aspect_ratio = str(brief.get("aspect_ratio", "16:9"))
        if aspect_ratio != "16:9":
            raise ValueError("Composer v1 currently supports aspect_ratio 16:9")
        beats = brief.get("beats")
        if not isinstance(beats, list) or not beats:
            raise ValueError("beat brief requires a non-empty beats list")
        palette = brief.get("palette") if isinstance(brief.get("palette"), dict) else {}
        motion_standard = dict(DEFAULT_MOTION_STANDARD)
        if isinstance(brief.get("motion_standard"), dict):
            motion_standard.update(brief["motion_standard"])
        cadence = float(motion_standard.get("max_static_interval_seconds", 0))
        if cadence <= 0 or cadence > 2:
            raise ValueError("motion_standard.max_static_interval_seconds must be within 0..2")
        for field in ["flat_slide_forbidden", "element_jump_forbidden"]:
            if motion_standard.get(field) is not True:
                raise ValueError(f"motion_standard.{field} must be true")
        if motion_standard.get("camera_movement") != "point-to-point":
            raise ValueError("motion_standard.camera_movement must be point-to-point")
        if motion_standard.get("depth_of_field") != "near-sharp-far-soft":
            raise ValueError("motion_standard.depth_of_field must be near-sharp-far-soft")
        if motion_standard.get("transition_continuity") != "spatial-or-semantic-linked":
            raise ValueError("motion_standard.transition_continuity must be spatial-or-semantic-linked")
        if motion_standard.get("ambient_float") != "subtle-only":
            raise ValueError("motion_standard.ambient_float must be subtle-only")
        forbidden = {str(item) for item in brief.get("forbidden_templates", [])}
        motion_catalog = load_catalog(MOTION_DIR / "catalog.json")
        spatial_catalog = load_catalog(SPATIAL_DIR / "catalog.json")
        catalog = {**motion_catalog, **spatial_catalog}
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    project = args.project.resolve()
    animation = project / "animation"
    compositions_dir = animation / "compositions"
    animation.mkdir(parents=True, exist_ok=True)
    compositions_dir.mkdir(parents=True, exist_ok=True)
    timeline: list[dict[str, Any]] = []
    compositions: list[dict[str, Any]] = []
    selected_motion: list[dict[str, Any]] = []
    selected_spatial: list[dict[str, Any]] = []
    tts_lines: list[dict[str, Any]] = []
    srt_chunks: list[str] = []
    voiceover_lines: list[str] = []
    cursor = 0.0
    seen_ids: set[str] = set()

    try:
        for index, raw in enumerate(beats, start=1):
            if not isinstance(raw, dict):
                raise ValueError(f"beat {index} must be an object")
            beat_id = safe_id(raw.get("id"), f"beat {index} id")
            if beat_id in seen_ids:
                raise ValueError(f"duplicate beat id: {beat_id}")
            seen_ids.add(beat_id)
            intent = str(raw.get("intent", ""))
            if intent not in ROUTES:
                raise ValueError(f"beat {beat_id} has unsupported intent: {intent}")
            duration = float(raw.get("duration_seconds", 0))
            if duration <= 0:
                raise ValueError(f"beat {beat_id} duration_seconds must be positive")
            voiceover = str(raw.get("voiceover", "")).strip()
            if not voiceover:
                raise ValueError(f"beat {beat_id} voiceover is required")
            preferred = str(raw.get("preferred_template", "")).strip()
            candidates = ([preferred] if preferred else []) + ROUTES[intent]
            template_id = next((item for item in candidates if item in catalog and item not in forbidden), "")
            if not template_id:
                raise ValueError(f"beat {beat_id} has no allowed registered template")

            entry = catalog[template_id]
            is_spatial = template_id in spatial_catalog
            library = SPATIAL_DIR if is_spatial else MOTION_DIR
            source_dir = library / str(entry["path"])
            destination = compositions_dir / beat_id
            copy_template(source_dir, destination, force=args.force)
            variables = read_object(source_dir / "presets" / "default.json")
            variables.update(auto_variables(template_id, raw, palette))
            if isinstance(raw.get("variables"), dict):
                variables.update(raw["variables"])
            variables["exportMode"] = "mp4"
            preset = destination / "presets" / "project.json"
            preset.write_text(json.dumps(variables, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if not is_spatial:
                shutil.copy2(MOTION_DIR / "UPSTREAM_NOTICE.md", destination / "UPSTREAM_NOTICE.md")
                shutil.copy2(MOTION_DIR / "source.json", destination / "source.json")

            start = cursor
            end = start + duration
            source_rel = (destination / "index.html").relative_to(project).as_posix()
            preset_rel = preset.relative_to(project).as_posix()
            composition = {
                "id": beat_id,
                "source": source_rel,
                "variables_file": preset_rel,
                "duration_seconds": float(entry["duration"]),
                "target_duration_seconds": duration,
                "aspect_ratio": aspect_ratio,
                "formats": entry.get("formats", ["mp4"]),
                "module": "spatial-camera" if is_spatial else "motion-templates",
                "template_id": template_id,
            }
            compositions.append(composition)
            timeline.append({"beat_id": beat_id, "composition_id": beat_id, "intent": intent, "template_id": template_id, "start_seconds": start, "end_seconds": end, "duration_seconds": duration})
            selected = {"composition_id": beat_id, "template_id": template_id, "variables_file": preset_rel, "export_mode": "mp4"}
            if is_spatial:
                selected["source"] = {"source_id": "video-master-original"}
                selected_spatial.append(selected)
            else:
                selected["source"] = {"source_id": "nutllwhy-hyperframes-motion-library", "commit": UPSTREAM_COMMIT}
                selected_motion.append(selected)
            tts_lines.append({"id": beat_id, "start_seconds": start, "end_seconds": end, "text": voiceover, "pause_after_ms": 120})
            voiceover_lines.append(f"{index}. [{start:.1f}–{end:.1f}s] {voiceover}")
            srt_chunks.append(f"{index}\n{seconds_to_srt(start)} --> {seconds_to_srt(end)}\n{voiceover}\n")
            cursor = end
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    modules = []
    if selected_motion:
        modules.append("motion-templates")
    if selected_spatial:
        modules.append("spatial-camera")
    plan: dict[str, Any] = {
        "schema_version": 2,
        "enabled": True,
        "engine": "hyperframes",
        "execution_mode": "hyperframes",
        "composer": "ai-animation-composer-v1",
        "title": str(brief.get("title", "AI Animation Explainer")),
        "aspect_ratio": aspect_ratio,
        "total_duration_seconds": cursor,
        "motion_standard": motion_standard,
        "modules": modules,
        "timeline": timeline,
        "compositions": compositions,
    }
    if selected_motion:
        plan["motion_templates"] = {"templates": selected_motion}
    if selected_spatial:
        plan["spatial_camera"] = {"templates": selected_spatial}
    plan_path = animation / "ai_animation_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": 1, "composer": "ai-animation-composer-v1", "input": str(args.brief.resolve()), "plan": plan_path.relative_to(project).as_posix(), "selection_policy": "deterministic-intent-route", "motion_standard": motion_standard, "timeline": timeline}
    (animation / "composer_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audio = project / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    (audio / "tts_lines.json").write_text(json.dumps(tts_lines, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (audio / "voiceover_script.md").write_text("# 配音稿\n\n" + "\n\n".join(voiceover_lines) + "\n", encoding="utf-8")
    (audio / "captions.srt").write_text("\n".join(srt_chunks), encoding="utf-8")
    (animation / "renders").mkdir(parents=True, exist_ok=True)
    (project / "qa" / "metadata").mkdir(parents=True, exist_ok=True)
    (project / "最终交付" / "08_ai_animation").mkdir(parents=True, exist_ok=True)
    (project / "最终交付" / "03_口播与字幕").mkdir(parents=True, exist_ok=True)
    print(plan_path)
    print(animation / "composer_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
