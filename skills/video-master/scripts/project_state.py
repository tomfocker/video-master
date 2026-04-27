#!/usr/bin/env python3
"""Build a WebUI-friendly state summary from canonical video-master files."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import (
    HANDOFF,
    IMAGE_PROMPTS,
    METADATA_DIR,
    PREVIEW_MANIFEST,
    TITLE_PACKAGING_MANIFEST,
    VIDEO_PROMPTS,
    WORKBOOK,
    handoff_path,
    image_prompt_path,
    overview_png_path,
    preview_manifest_path,
    preview_mp4_path,
    storyboard_frame_dir,
    storyboard_frame_path,
    title_packaging_dir,
    title_packaging_manifest_path,
    video_prompt_path,
    workbook_path,
)


PROJECT_STATE = METADATA_DIR / "project_state.json"
WORKFLOW_EVENTS = METADATA_DIR / "workflow_events.jsonl"
CODEX_SHOT_REQUESTS = METADATA_DIR / "codex_shot_requests.json"


class ProjectStateError(ValueError):
    """Raised when a project state cannot be built."""


def rel(project: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project.resolve()))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def normalize_section(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def parse_markdown_sections(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current = "root"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = normalize_section(line[3:])
            sections.setdefault(current, {})
            continue
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            sections.setdefault(current, {})[key.strip()] = value.strip()
    return sections


def split_prompt_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line[3:].split()[0].strip()
            blocks.setdefault(current, [raw_line])
        elif current:
            blocks[current].append(raw_line)
    return {key: "\n".join(lines).strip() for key, lines in blocks.items()}


def compact_text(value: str, limit: int = 500) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def preview_text(path: Path, limit: int = 220) -> str:
    text = read_text(path)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        return compact_text(line, limit)
    return compact_text(text, limit)


def normalize_shot_id(value: Any) -> str:
    match = re.search(r"\bS?(\d{1,3})\b", str(value or ""), flags=re.IGNORECASE)
    if not match:
        return ""
    return f"S{int(match.group(1)):02d}"


def extract_numbered_lines_by_shot(text: str, prefix: str) -> dict[str, str]:
    pattern = re.compile(rf"\b{re.escape(prefix)}(\d{{1,3}})\b[^\n:：]*[:：]\s*(.+)", re.IGNORECASE)
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        match = pattern.search(line)
        if match:
            result[f"S{int(match.group(1)):02d}"] = compact_text(match.group(2), 260)
    return result


def build_shot_copywriting(project: Path) -> dict[str, dict[str, str]]:
    voiceover_by_shot = extract_numbered_lines_by_shot(read_text(project / "audio" / "voiceover_script.md"), "VO")
    sfx_by_shot = extract_numbered_lines_by_shot(read_text(project / "audio" / "music_sfx_cue_sheet.md"), "S")
    shot_ids = set(voiceover_by_shot) | set(sfx_by_shot)
    return {
        shot_id: {
            "voiceover": voiceover_by_shot.get(shot_id, ""),
            "sfx": sfx_by_shot.get(shot_id, ""),
        }
        for shot_id in sorted(shot_ids)
    }


def packaging_item_summary(item: dict[str, Any]) -> str:
    for key in ("text", "copy", "title", "label", "description", "prompt"):
        value = item.get(key)
        if value:
            return compact_text(str(value), 180)
    return compact_text(json.dumps(item, ensure_ascii=False), 180)


def infer_packaging_shot(item: dict[str, Any], first_shot: str, last_shot: str) -> str:
    explicit = normalize_shot_id(item.get("shot_id") or item.get("target_shot_id") or item.get("target"))
    if explicit:
        return explicit
    kind = " ".join(str(item.get(key, "")) for key in ("type", "role", "name", "id")).lower()
    if any(token in kind for token in ("end", "cta", "logo", "brand", "落版", "片尾")):
        return last_shot
    return first_shot


def build_shot_packaging(project: Path, shots: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    shot_ids = [str(shot.get("shot_id") or f"S{index:02d}") for index, shot in enumerate(shots, start=1) if isinstance(shot, dict)]
    if not shot_ids:
        return {}
    first_shot = shot_ids[0]
    last_shot = shot_ids[-1]
    manifest = read_json(title_packaging_manifest_path(project), {})
    items = manifest.get("items") if isinstance(manifest, dict) else None
    if isinstance(items, list) and items:
        bindings: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            shot_id = infer_packaging_shot(item, first_shot, last_shot)
            binding = bindings.setdefault(
                shot_id,
                {"status": "已绑定包装", "role": "包装元素", "items": [], "summary": ""},
            )
            binding["items"].append(packaging_item_summary(item))
        for binding in bindings.values():
            binding["summary"] = compact_text("；".join(binding["items"]), 220)
        return bindings

    status = "待生成包装" if manifest else "未启用包装"
    bindings = {
        first_shot: {
            "status": status,
            "role": "片头标题/主视觉钩子",
            "summary": "片头标题、主视觉钩子或首屏品牌露出绑定在本镜头。",
        }
    }
    bindings[last_shot] = {
        "status": status,
        "role": "品牌落版/CTA",
        "summary": "品牌口号、产品信息、CTA 或片尾落版绑定在本镜头。",
    }
    return bindings


def path_info(project: Path, path: Path) -> dict[str, Any]:
    return {
        "path": rel(project, path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def node_status(paths: list[Path], *, optional: bool = False) -> str:
    existing = [path for path in paths if path.exists()]
    if not paths or (optional and not existing):
        return "skipped"
    if len(existing) == len(paths):
        return "complete"
    if existing:
        return "partial"
    return "missing"


def make_node(project: Path, node_id: str, label: str, paths: list[Path], *, optional: bool = False) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "status": node_status(paths, optional=optional),
        "files": [path_info(project, path) for path in paths],
    }


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "enabled", "confirmed", "required"}


def character_lock_required(character_design: dict[str, str]) -> bool:
    status = character_design.get("character_lock_status", "").strip().lower()
    return (
        truthy(character_design.get("character_lock_enabled"))
        or bool(character_design.get("fixed_characters", "").strip())
        or status in {"confirmed", "assumed", "required", "pending"}
    )


def character_lock_node(project: Path, character_design: dict[str, str]) -> dict[str, Any]:
    paths = [
        project / "characters" / "character_bible.md",
        project / "characters" / "character_manifest.json",
        project / "characters",
    ]
    return make_node(
        project,
        "character_lock",
        "Character Design Lock",
        paths[:2],
        optional=not character_lock_required(character_design),
    ) | {"files": [path_info(project, path) for path in paths]}


def prompt_paths(project: Path) -> dict[str, Path]:
    return {
        "storyboard_image_prompts": project / "prompts" / "storyboard_image_prompts.md",
        "working_video_prompts": project / "prompts" / "video_prompts.md",
        "final_video_prompts": video_prompt_path(project),
        "final_image_prompts": image_prompt_path(project),
    }


def build_flow_nodes(project: Path, sections: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    paths = prompt_paths(project)
    title_plan = project / "packaging" / "title_packaging_plan.json"
    title_manifest = title_packaging_manifest_path(project)
    frame_dir = storyboard_frame_dir(project)
    frame_files = list(frame_dir.glob("*.png")) if frame_dir.is_dir() else []
    visual_style_locked = bool(sections.get("visual_style", {}).get("visual_style_preset_id"))
    character_design = sections.get("character_design", {})

    nodes = [
        make_node(project, "input_readiness", "Input Readiness", [project / "strategy" / "input_readiness.md"]),
        make_node(project, "video_mode", "Video Mode", [project / "strategy" / "video_mode.md"]),
        make_node(project, "production_lock", "Production Lock", [project / "brief" / "creative_brief.md", project / "brief" / "spec_lock.md"]),
        {
            "id": "visual_style",
            "label": "Visual Style Lock",
            "status": "complete" if visual_style_locked else "missing",
            "files": [path_info(project, project / "brief" / "spec_lock.md")],
        },
        character_lock_node(project, character_design),
        make_node(project, "strategy", "Creative Strategy", [project / "strategy" / "creative_strategy.md", project / "strategy" / "rhythm_map.md"]),
        make_node(project, "script_audio", "Script And Audio", [project / "script" / "script.md", project / "audio" / "voiceover_script.md", project / "audio" / "music_sfx_cue_sheet.md"]),
        make_node(project, "storyboard_plan", "Shot List", [project / "storyboard" / "shot_list.md", project / "storyboard" / "shot_list.json"]),
        {
            "id": "storyboard_images",
            "label": "Storyboard Images",
            "status": "complete" if frame_files and (project / "storyboard" / "storyboard_manifest.md").exists() else ("partial" if frame_files else "missing"),
            "files": [path_info(project, project / "storyboard" / "storyboard_manifest.md"), path_info(project, frame_dir)],
            "frame_count": len(frame_files),
        },
        make_node(project, "video_prompts", "Video Prompts", [paths["working_video_prompts"], paths["final_video_prompts"]]),
        make_node(project, "title_packaging", "Title Packaging", [title_plan, title_manifest, title_packaging_dir(project)], optional=True),
        make_node(project, "deliverables", "Deliverables", [handoff_path(project), overview_png_path(project), preview_mp4_path(project), workbook_path(project), paths["final_image_prompts"]]),
    ]
    return nodes


def build_shots(project: Path) -> list[dict[str, Any]]:
    shots = read_json(project / "storyboard" / "shot_list.json", [])
    if not isinstance(shots, list):
        shots = []
    prompts = split_prompt_blocks(read_text(project / "prompts" / "video_prompts.md"))
    image_prompts = split_prompt_blocks(read_text(project / "prompts" / "storyboard_image_prompts.md"))
    copywriting = build_shot_copywriting(project)
    packaging = build_shot_packaging(project, shots)

    result = []
    for index, raw_shot in enumerate(shots, start=1):
        if not isinstance(raw_shot, dict):
            continue
        shot_id = str(raw_shot.get("shot_id") or f"S{index:02d}")
        frame = storyboard_frame_path(project, shot_id)
        result.append(
            {
                "shot_id": shot_id,
                "index": index,
                "start": raw_shot.get("start", ""),
                "end": raw_shot.get("end", ""),
                "duration_seconds": raw_shot.get("duration_seconds"),
                "beat": raw_shot.get("beat", ""),
                "purpose": raw_shot.get("purpose", raw_shot.get("narrative_purpose", "")),
                "visual_action": raw_shot.get("visual_action", raw_shot.get("subject/action", "")),
                "framing": raw_shot.get("framing", ""),
                "camera": raw_shot.get("camera_movement", raw_shot.get("camera", "")),
                "movement": raw_shot.get("movement", ""),
                "lighting": raw_shot.get("lighting", ""),
                "sfx": raw_shot.get("sfx", ""),
                "image_prompt_seed": raw_shot.get("image_prompt_seed", ""),
                "video_prompt_seed": raw_shot.get("video_prompt_seed", ""),
                "frame": path_info(project, frame),
                "video_prompt": compact_text(prompts.get(shot_id, "")),
                "image_prompt": compact_text(image_prompts.get(shot_id, "")),
                "copywriting": copywriting.get(shot_id, {}),
                "packaging": packaging.get(shot_id, {}),
            }
        )
    return result


def build_deliverables(project: Path) -> dict[str, Any]:
    paths = prompt_paths(project)
    title_manifest = title_packaging_manifest_path(project)
    preview_manifest = preview_manifest_path(project)
    return {
        "handoff": path_info(project, handoff_path(project)),
        "storyboard_overview": path_info(project, overview_png_path(project)),
        "preview_video": path_info(project, preview_mp4_path(project)),
        "workbook": path_info(project, workbook_path(project)),
        "final_video_prompts": path_info(project, paths["final_video_prompts"]),
        "final_image_prompts": path_info(project, paths["final_image_prompts"]),
        "preview_manifest": read_json(preview_manifest, {}),
        "title_packaging_manifest": read_json(title_manifest, {}),
    }


def build_copywriting(project: Path) -> dict[str, Any]:
    script = project / "script" / "script.md"
    voiceover = project / "audio" / "voiceover_script.md"
    captions = project / "audio" / "captions.srt"
    localized_captions = project / "audio" / "captions_zh.srt"
    music_sfx = project / "audio" / "music_sfx_cue_sheet.md"
    audio_prompt = project / "audio" / "audio_generation_prompt.md"
    files = {
        "script": path_info(project, script),
        "voiceover": path_info(project, voiceover),
        "captions": path_info(project, captions),
        "localized_captions": path_info(project, localized_captions),
        "music_sfx": path_info(project, music_sfx),
        "audio_prompt": path_info(project, audio_prompt),
    }
    return {
        "status": node_status([script, voiceover, captions, music_sfx], optional=True),
        "files": files,
        "voiceover_preview": preview_text(voiceover),
        "caption_preview": preview_text(localized_captions) or preview_text(captions),
        "music_sfx_preview": preview_text(music_sfx),
    }


def number_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def build_shot_requests(project: Path) -> list[dict[str, Any]]:
    raw_requests = read_json(project / CODEX_SHOT_REQUESTS, [])
    if not isinstance(raw_requests, list):
        return []
    result = []
    for index, raw in enumerate(raw_requests, start=1):
        if not isinstance(raw, dict):
            continue
        idea = compact_text(str(raw.get("idea") or "").strip(), 500)
        if not idea:
            continue
        x = number_or_default(raw.get("x"), 520 + index * 24)
        y = number_or_default(raw.get("y"), 160 + index * 24)
        result.append(
            {
                "request_id": str(raw.get("request_id") or f"idea_{index:03d}"),
                "status": str(raw.get("status") or "pending"),
                "idea": idea,
                "x": int(x) if x.is_integer() else x,
                "y": int(y) if y.is_integer() else y,
                "insert_after_shot_id": str(raw.get("insert_after_shot_id") or ""),
                "created_at": str(raw.get("created_at") or ""),
            }
        )
    return result


def build_project_state(project: Path) -> dict[str, Any]:
    project = project.resolve()
    if not project.exists():
        raise ProjectStateError(f"project path does not exist: {project}")
    spec_lock = project / "brief" / "spec_lock.md"
    sections = parse_markdown_sections(read_text(spec_lock))
    workflow = sections.get("workflow", {})
    production = sections.get("production_mode", {})
    visual_style = sections.get("visual_style", {})
    character_design = sections.get("character_design", {})
    format_section = sections.get("format", {})
    title_packaging = sections.get("title_packaging", {})

    state = {
        "schema_version": 1,
        "project": {
            "name": project.name,
            "path": str(project),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "workflow": {
            "workflow_mode": workflow.get("workflow_mode", "guided"),
            "confirmation_policy": workflow.get("confirmation_policy", "confirm_each_phase"),
            "assumption_policy": workflow.get("assumption_policy", "require_user_confirmation"),
            "assumption_log": workflow.get("assumption_log", rel(project, project / WORKFLOW_EVENTS)),
        },
        "format": format_section,
        "production_mode": production,
        "visual_style": visual_style,
        "character_design": character_design,
        "title_packaging": title_packaging,
        "copywriting": build_copywriting(project),
        "shot_requests": build_shot_requests(project),
        "flow_nodes": build_flow_nodes(project, sections),
        "shots": build_shots(project),
        "prompts": {key: path_info(project, path) for key, path in prompt_paths(project).items()},
        "deliverables": build_deliverables(project),
        "metadata": {
            "project_state": rel(project, project / PROJECT_STATE),
            "workflow_events": rel(project, project / WORKFLOW_EVENTS),
        },
    }
    return state


def write_project_state(project: Path, state: dict[str, Any]) -> Path:
    path = project / PROJECT_STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build WebUI-friendly video-master project state JSON.")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument("--write", action="store_true", help="Write qa/metadata/project_state.json")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON to stdout")
    args = parser.parse_args(argv)

    try:
        state = build_project_state(args.project)
    except ProjectStateError as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.write:
        output = write_project_state(args.project.resolve(), state)
        print(f"OK: wrote {output}")
    else:
        print(json.dumps(state, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
