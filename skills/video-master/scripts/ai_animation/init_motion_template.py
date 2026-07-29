#!/usr/bin/env python3
"""Add a registered HyperFrames motion template to a video-master project."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[2]
LIBRARY_DIR = SKILL_DIR / "ai_animation" / "motion_templates"
CATALOG_PATH = LIBRARY_DIR / "catalog.json"
TEMPLATES_DIR = LIBRARY_DIR / "templates"


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_catalog() -> dict[str, dict[str, Any]]:
    catalog = read_object(CATALOG_PATH)
    templates = catalog.get("templates")
    if not isinstance(templates, list):
        raise ValueError("motion template catalog requires a templates list")
    return {
        str(item["id"]): item
        for item in templates
        if isinstance(item, dict) and item.get("id")
    }


def safe_id(value: str, label: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError(f"{label} must use lowercase hyphen-case: {value}")
    return value


def project_relative(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def upsert_by_id(items: list[object], new_item: dict[str, Any], field: str = "id") -> list[object]:
    return [item for item in items if not isinstance(item, dict) or item.get(field) != new_item[field]] + [new_item]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--composition-id")
    parser.add_argument("--variables", type=Path, help="JSON object merged over the bundled default preset")
    parser.add_argument("--execution-mode", choices=["hyperframes", "hybrid"], default="hybrid")
    parser.add_argument("--export-mode", choices=["transparent", "mp4"], default="transparent")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    try:
        template_id = safe_id(args.template_id, "--template-id")
        composition_id = safe_id(args.composition_id or template_id, "--composition-id")
        catalog = load_catalog()
        if template_id not in catalog:
            parser.error(f"unknown motion template: {template_id}")
        entry = catalog[template_id]
        source_dir = TEMPLATES_DIR / template_id
        variables = read_object(source_dir / "presets" / "default.json")
        if args.variables:
            variables.update(read_object(args.variables.resolve()))
        variables["exportMode"] = args.export_mode
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    project = args.project.resolve()
    animation_dir = project / "animation"
    destination = animation_dir / "compositions" / composition_id
    plan_path = animation_dir / "ai_animation_plan.json"
    if destination.exists() and not args.force:
        parser.error(f"composition already exists: {destination}; pass --force to replace it")

    destination.mkdir(parents=True, exist_ok=True)
    for name in ["index.html", "design.md", "meta.json", "package.json"]:
        shutil.copy2(source_dir / name, destination / name)
    (destination / "presets").mkdir(parents=True, exist_ok=True)
    preset_path = destination / "presets" / "project.json"
    preset_path.write_text(json.dumps(variables, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(LIBRARY_DIR / "UPSTREAM_NOTICE.md", destination / "UPSTREAM_NOTICE.md")
    shutil.copy2(LIBRARY_DIR / "source.json", destination / "source.json")

    if plan_path.is_file():
        try:
            plan = read_object(plan_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            parser.error(f"cannot extend existing AI animation plan: {exc}")
    else:
        plan = {
            "schema_version": 1,
            "enabled": True,
            "engine": "hyperframes",
            "execution_mode": args.execution_mode,
            "modules": [],
            "compositions": [],
        }

    plan["enabled"] = True
    plan["engine"] = "hyperframes"
    plan["execution_mode"] = args.execution_mode
    modules = plan.get("modules") if isinstance(plan.get("modules"), list) else []
    if "motion-templates" not in modules:
        modules.append("motion-templates")
    plan["modules"] = modules

    motion = plan.get("motion_templates") if isinstance(plan.get("motion_templates"), dict) else {}
    selected = motion.get("templates") if isinstance(motion.get("templates"), list) else []
    selected_item = {
        "composition_id": composition_id,
        "template_id": template_id,
        "variables_file": project_relative(project, preset_path),
        "export_mode": args.export_mode,
        "source": {
            "source_id": "nutllwhy-hyperframes-motion-library",
            "commit": "01c393f9f26b5b0d8432fa02682ceb36f6cc3e0f",
        },
    }
    motion["templates"] = upsert_by_id(selected, selected_item, "composition_id")
    plan["motion_templates"] = motion

    compositions = plan.get("compositions") if isinstance(plan.get("compositions"), list) else []
    composition = {
        "id": composition_id,
        "source": project_relative(project, destination / "index.html"),
        "variables_file": project_relative(project, preset_path),
        "duration_seconds": entry["duration"],
        "aspect_ratio": "16:9",
        "formats": entry.get("formats", ["mp4"]),
    }
    plan["compositions"] = upsert_by_id(compositions, composition)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (animation_dir / "renders").mkdir(parents=True, exist_ok=True)
    (project / "最终交付" / "08_ai_animation").mkdir(parents=True, exist_ok=True)

    print(plan_path)
    print(destination / "index.html")
    print(preset_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
