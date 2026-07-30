#!/usr/bin/env python3
"""Render a project-local registered motion or spatial template with saved variables."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


HYPERFRAMES_VERSION = "0.6.115"


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def project_path(project: Path, value: object, label: str) -> Path:
    if not value:
        raise ValueError(f"missing {label}")
    path = (project / str(value)).resolve()
    if not path.is_relative_to(project):
        raise ValueError(f"{label} escapes the project: {value}")
    return path


def find_by_id(items: object, item_id: str, label: str) -> dict[str, Any]:
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("id") == item_id:
                return item
    raise ValueError(f"unknown {label}: {item_id}")


def npx_prefix() -> list[str]:
    node = shutil.which("node")
    if node:
        npx_cli = Path(node).resolve().parent / "node_modules" / "npm" / "bin" / "npx-cli.js"
        if npx_cli.is_file():
            return [node, str(npx_cli)]
    npx = shutil.which("npx")
    if npx:
        return [npx]
    raise ValueError("npx is required to render HyperFrames compositions")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--composition-id", required=True)
    parser.add_argument("--format", choices=["mp4", "webm", "mov"], default="mp4")
    parser.add_argument("--quality", default="draft")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    try:
        plan = read_object(project / "animation" / "ai_animation_plan.json")
        composition = find_by_id(plan.get("compositions"), args.composition_id, "composition")
        motion = plan.get("motion_templates")
        selected = motion.get("templates") if isinstance(motion, dict) else None
        template = None
        if isinstance(selected, list):
            template = next(
                (
                    item
                    for item in selected
                    if isinstance(item, dict) and item.get("composition_id") == args.composition_id
                ),
                None,
            )
        if not isinstance(template, dict):
            spatial = plan.get("spatial_camera")
            spatial_selected = spatial.get("templates") if isinstance(spatial, dict) else None
            if isinstance(spatial_selected, list):
                template = next(
                    (
                        item
                        for item in spatial_selected
                        if isinstance(item, dict) and item.get("composition_id") == args.composition_id
                    ),
                    None,
                )
        if not isinstance(template, dict):
            raise ValueError(f"composition is not a registered motion or spatial template: {args.composition_id}")
        source = project_path(project, composition.get("source"), "composition source")
        variables_path = project_path(project, template.get("variables_file"), "variables file")
        variables = read_object(variables_path)
        formats = composition.get("formats") if isinstance(composition.get("formats"), list) else ["mp4"]
        if args.format not in formats:
            raise ValueError(f"format {args.format} is not registered for {args.composition_id}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    variables["exportMode"] = "mp4" if args.format == "mp4" else "transparent"
    render_dir = project / "animation" / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    output = args.output
    if output is None:
        output = render_dir / f"{args.composition_id}.{args.format}"
    elif not output.is_absolute():
        output = (project / output).resolve()
    else:
        output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    render_format = "webm" if args.format == "mov" else args.format
    preview = render_dir / f"{args.composition_id}-mov-preview.webm" if args.format == "mov" else output
    try:
        command = npx_prefix() + [
            "--yes",
            f"hyperframes@{HYPERFRAMES_VERSION}",
            "render",
            "--quality",
            args.quality,
            "--format",
            render_format,
            "--strict-variables",
            "--variables",
            json.dumps(variables, ensure_ascii=False, separators=(",", ":")),
            "--output",
            str(preview),
        ]
    except ValueError as exc:
        parser.error(str(exc))
    if args.dry_run:
        print(json.dumps({"cwd": str(source.parent), "command": command, "output": str(output)}, ensure_ascii=False, indent=2))
        return 0
    result = subprocess.run(command, cwd=source.parent, check=False)
    if result.returncode != 0:
        return result.returncode

    if args.format == "mov":
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            parser.error("ffmpeg is required to convert transparent WebM to ProRes 4444 MOV")
        conversion = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "warning",
                "-y",
                "-c:v",
                "libvpx-vp9",
                "-i",
                str(preview),
                "-an",
                "-c:v",
                "prores_ks",
                "-profile:v",
                "4",
                "-pix_fmt",
                "yuva444p10le",
                "-vendor",
                "apl0",
                "-movflags",
                "+faststart",
                str(output),
            ],
            cwd=source.parent,
            check=False,
        )
        if conversion.returncode != 0:
            return conversion.returncode

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
