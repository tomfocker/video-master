#!/usr/bin/env python3
"""Load and validate lightweight visual style presets for video-master."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PRESET_PATH = SKILL_DIR / "references" / "visual_style_presets.json"

REQUIRED_PRESET_FIELDS = [
    "id",
    "display_name",
    "status",
    "short_description",
    "best_for",
    "not_for",
    "medium",
    "realism_level",
    "art_direction",
    "color_palette",
    "lighting",
    "texture",
    "camera_language",
    "storyboard_prompt_rules",
    "video_prompt_rules",
    "avoid",
]

VALID_STATUSES = {"official", "draft"}


class VisualStylePresetError(ValueError):
    """Raised when the visual style preset library is invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VisualStylePresetError(f"missing visual style preset file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualStylePresetError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise VisualStylePresetError("visual style preset file must contain a JSON object")
    return data


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VisualStylePresetError(f"{field} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise VisualStylePresetError(f"{field} must be a non-empty list")
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise VisualStylePresetError(f"{field} entries must be non-empty strings")
        result.append(item.strip())
    return result


def _validate_preset_id(value: Any) -> str:
    preset_id = _require_string(value, "id")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(char not in allowed for char in preset_id):
        raise VisualStylePresetError(f"unsafe visual style preset id: {preset_id}")
    return preset_id


def validate_preset(raw: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_PRESET_FIELDS if field not in raw]
    if missing:
        raise VisualStylePresetError(f"missing preset fields: {', '.join(missing)}")

    preset = dict(raw)
    preset["id"] = _validate_preset_id(raw["id"])
    preset["display_name"] = _require_string(raw["display_name"], "display_name")
    preset["status"] = _require_string(raw["status"], "status")
    if preset["status"] not in VALID_STATUSES:
        raise VisualStylePresetError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    for field in [
        "short_description",
        "medium",
        "realism_level",
        "art_direction",
        "color_palette",
        "lighting",
        "texture",
        "camera_language",
    ]:
        preset[field] = _require_string(raw[field], field)

    for field in ["best_for", "not_for", "storyboard_prompt_rules", "video_prompt_rules", "avoid"]:
        preset[field] = _require_string_list(raw[field], field)

    return preset


def load_presets(path: Path | None = None) -> dict[str, dict[str, Any]]:
    data = _read_json(path or DEFAULT_PRESET_PATH)
    if not isinstance(data.get("presets"), list) or not data["presets"]:
        raise VisualStylePresetError("visual style preset file requires a non-empty presets list")

    presets: dict[str, dict[str, Any]] = {}
    for raw in data["presets"]:
        if not isinstance(raw, dict):
            raise VisualStylePresetError("each visual style preset must be an object")
        preset = validate_preset(raw)
        preset_id = preset["id"]
        if preset_id in presets:
            raise VisualStylePresetError(f"duplicate visual style preset id: {preset_id}")
        presets[preset_id] = preset
    return presets


def get_preset(preset_id: str, path: Path | None = None) -> dict[str, Any]:
    presets = load_presets(path)
    clean_id = _validate_preset_id(preset_id)
    try:
        return presets[clean_id]
    except KeyError as exc:
        raise VisualStylePresetError(f"unknown visual style preset: {preset_id}") from exc


def build_spec_lock_visual_style(preset: dict[str, Any], lock: str = "confirmed") -> str:
    storyboard_rules = " ".join(preset["storyboard_prompt_rules"])
    video_rules = " ".join(preset["video_prompt_rules"])
    return "\n".join(
        [
            "## visual_style",
            f"- visual_style_lock: {lock}",
            f"- visual_style_preset_id: {preset['id']}",
            f"- visual_style_preset_name: {preset['display_name']}",
            f"- medium: {preset['medium']}",
            f"- realism_level: {preset['realism_level']}",
            f"- art_direction: {preset['art_direction']}",
            f"- color_palette: {preset['color_palette']}",
            f"- lighting: {preset['lighting']}",
            f"- texture: {preset['texture']}",
            f"- camera_language: {preset['camera_language']}",
            f"- storyboard_prompt_rules: {storyboard_rules}",
            f"- video_prompt_rules: {video_rules}",
            "- visual_style_overrides:",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect video-master visual style presets.")
    parser.add_argument("--preset-file", type=Path, default=None, help="Path to visual_style_presets.json")
    parser.add_argument("--list", action="store_true", help="List preset IDs and display names")
    parser.add_argument("--get", metavar="PRESET_ID", help="Print one preset as JSON")
    parser.add_argument("--spec-lock", metavar="PRESET_ID", help="Print spec_lock visual_style markdown for one preset")
    args = parser.parse_args(argv)

    try:
        if args.get:
            print(json.dumps(get_preset(args.get, args.preset_file), ensure_ascii=False, indent=2))
            return 0
        if args.spec_lock:
            print(build_spec_lock_visual_style(get_preset(args.spec_lock, args.preset_file)))
            return 0
        presets = load_presets(args.preset_file)
    except VisualStylePresetError as exc:
        print(f"ERROR: {exc}")
        return 1

    for preset in presets.values():
        print(f"{preset['id']}: {preset['display_name']} - {preset['short_description']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
