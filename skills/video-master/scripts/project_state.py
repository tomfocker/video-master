#!/usr/bin/env python3
"""Build a WebUI-friendly state summary from canonical video-master files."""

from __future__ import annotations

import argparse
import json
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
                "camera": raw_shot.get("camera_movement", raw_shot.get("camera", "")),
                "frame": path_info(project, frame),
                "video_prompt": compact_text(prompts.get(shot_id, "")),
                "image_prompt": compact_text(image_prompts.get(shot_id, "")),
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
