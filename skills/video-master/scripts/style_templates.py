#!/usr/bin/env python3
"""Load and validate video-master style template packages."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_ROOT = SKILL_DIR / "style_templates"

REQUIRED_PACKAGE_FILES = [
    "template.md",
    "template.json",
    "rhythm_rules.json",
    "prompt_rules.md",
    "reference_notes.md",
    "director_notes.md",
    "shot_motifs.json",
    "editing_craft.md",
    "example_shot_list.md",
]

REQUIRED_TEMPLATE_FIELDS = [
    "id",
    "display_name",
    "status",
    "version",
    "updated_at",
    "tags",
    "best_for",
    "not_for",
    "supported_video_modes",
    "supported_aspect_ratios",
    "duration_range_seconds",
    "user_override_policy",
    "visual_rules",
    "rhythm_rules",
    "camera_rules",
    "sound_rules",
    "storyboard_prompt_rules",
    "video_prompt_rules",
    "safety_boundaries",
    "required_files",
]

VALID_STATUSES = {"draft", "official"}
REQUIRED_PACKAGE_FILE_SET = set(REQUIRED_PACKAGE_FILES)


class TemplateError(ValueError):
    """Raised when a style template package is missing or invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TemplateError(f"missing template package file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise TemplateError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TemplateError(f"{path} must contain a JSON object")
    return data


def _as_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise TemplateError(f"{field} must be a non-empty list")
    return value


def _default_template_root() -> Path:
    env_root = os.environ.get("VIDEO_MASTER_STYLE_TEMPLATE_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    return DEFAULT_TEMPLATE_ROOT


def _validate_template_id(template_id: str) -> str:
    if not isinstance(template_id, str):
        raise TemplateError("template_id must be a string")
    clean_id = template_id.strip()
    path = Path(clean_id)
    if (
        not clean_id
        or clean_id in {".", ".."}
        or path.is_absolute()
        or "/" in clean_id
        or "\\" in clean_id
    ):
        raise TemplateError(f"unsafe template_id: {template_id}")
    return clean_id


def _resolve_package_dir(template_root: Path, template_id: str) -> tuple[Path, Path]:
    root = template_root.resolve()
    package_dir = (root / template_id).resolve()
    try:
        package_dir.relative_to(root)
    except ValueError as exc:
        raise TemplateError(f"unsafe template_id: {template_id}") from exc
    return root, package_dir


def _validate_required_files(value: Any, package_dir: Path) -> list[str]:
    required_files = _as_list(value, "required_files")
    filenames = []
    for item in required_files:
        if not isinstance(item, str):
            raise TemplateError("required_files entries must be string basenames")
        filename = item.strip()
        path = Path(filename)
        if (
            not filename
            or filename in {".", ".."}
            or path.is_absolute()
            or "/" in filename
            or "\\" in filename
        ):
            raise TemplateError("required_files entries must be string basenames")
        if filename not in REQUIRED_PACKAGE_FILE_SET:
            raise TemplateError(f"unknown required_files entry: {filename}")
        if not (package_dir / filename).is_file():
            raise TemplateError(f"missing template package file: {filename}")
        filenames.append(filename)

    missing = [filename for filename in REQUIRED_PACKAGE_FILES if filename not in filenames]
    if missing:
        raise TemplateError(f"required_files must include {', '.join(missing)}")
    return filenames


def _validate_prompt_validation(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise TemplateError("prompt_validation must be an object")

    required_terms = value.get("required_terms")
    if not isinstance(required_terms, list) or not required_terms:
        raise TemplateError("prompt_validation.required_terms must be a non-empty list")
    if not all(isinstance(term, str) and term.strip() for term in required_terms):
        raise TemplateError("prompt_validation.required_terms entries must be non-empty strings")

    minimum_matches = value.get("minimum_matches")
    if not isinstance(minimum_matches, int) or minimum_matches <= 0:
        raise TemplateError("prompt_validation.minimum_matches must be a positive integer")
    if minimum_matches > len(required_terms):
        raise TemplateError("prompt_validation.minimum_matches cannot exceed required_terms length")


def validate_template_metadata(data: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    if "strengths" in data:
        raise TemplateError("strengths metadata is no longer supported; templates apply as complete director archives")

    missing = [field for field in REQUIRED_TEMPLATE_FIELDS if field not in data]
    if missing:
        raise TemplateError(f"missing required metadata: {', '.join(missing)}")

    template_id = str(data["id"]).strip()
    if not template_id:
        raise TemplateError("id must be non-empty")
    if template_id != package_dir.name:
        raise TemplateError(
            f"template id {template_id!r} must match folder name {package_dir.name!r}"
        )

    status = str(data["status"]).strip()
    if status not in VALID_STATUSES:
        raise TemplateError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    for field in [
        "tags",
        "best_for",
        "not_for",
        "supported_video_modes",
        "supported_aspect_ratios",
        "user_override_policy",
        "visual_rules",
        "rhythm_rules",
        "camera_rules",
        "sound_rules",
        "storyboard_prompt_rules",
        "video_prompt_rules",
        "safety_boundaries",
    ]:
        _as_list(data[field], field)

    duration_range = data["duration_range_seconds"]
    if (
        not isinstance(duration_range, dict)
        or not isinstance(duration_range.get("min"), (int, float))
        or not isinstance(duration_range.get("max"), (int, float))
        or duration_range["min"] <= 0
        or duration_range["max"] < duration_range["min"]
    ):
        raise TemplateError("duration_range_seconds must include numeric min and max")

    _validate_required_files(data["required_files"], package_dir)
    _validate_prompt_validation(data.get("prompt_validation"))

    return data


def load_template(template_id: str, template_root: Path | None = None) -> dict[str, Any]:
    clean_id = _validate_template_id(template_id)
    root, package_dir = _resolve_package_dir(template_root or _default_template_root(), clean_id)
    if not package_dir.is_dir():
        raise TemplateError(f"template not found: {clean_id}")

    data = _read_json(package_dir / "template.json")
    validated = validate_template_metadata(data, package_dir)
    validated = dict(validated)
    validated["package_dir"] = str(package_dir)
    return validated


def list_templates(template_root: Path | None = None) -> list[dict[str, Any]]:
    root = template_root or _default_template_root()
    if not root.is_dir():
        return []

    templates: list[dict[str, Any]] = []
    for package_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        template = load_template(package_dir.name, template_root=root)
        templates.append(
            {
                "id": template["id"],
                "display_name": template["display_name"],
                "status": template["status"],
                "version": template["version"],
                "tags": template["tags"],
            }
        )
    return templates
