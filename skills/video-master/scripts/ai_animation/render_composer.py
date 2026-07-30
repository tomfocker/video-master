#!/usr/bin/env python3
"""Batch-render and assemble an AI Animation Composer timeline."""

from __future__ import annotations

import argparse
import json
import re
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


def project_path(project: Path, value: object, label: str) -> Path:
    path = (project / str(value or "")).resolve()
    if not value or not path.is_relative_to(project):
        raise ValueError(f"invalid {label}: {value}")
    return path


def run(command: list[str], *, cwd: Path, dry_run: bool) -> None:
    if dry_run:
        print(json.dumps({"cwd": str(cwd), "command": command}, ensure_ascii=False))
        return
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed with exit code {result.returncode}: {' '.join(command)}")


def find_voiceover(project: Path, explicit: Path | None) -> Path | None:
    if explicit:
        return explicit.resolve()
    for relative in ["audio/voiceover.wav", "audio/voiceover.mp3", "audio/voiceover.m4a"]:
        candidate = project / relative
        if candidate.is_file():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--quality", default="draft")
    parser.add_argument("--voiceover", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    project = args.project.resolve()
    try:
        plan = read_object(project / "animation" / "ai_animation_plan.json")
        if plan.get("composer") != "ai-animation-composer-v1":
            raise ValueError("plan was not created by ai-animation-composer-v1")
        compositions = plan.get("compositions")
        timeline = plan.get("timeline")
        if not isinstance(compositions, list) or not compositions or not isinstance(timeline, list):
            raise ValueError("composer plan requires compositions and timeline")
        by_id = {str(item.get("id")): item for item in compositions if isinstance(item, dict)}
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise ValueError("ffmpeg is required to assemble the timeline")
        npx = npx_prefix()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    render_dir = project / "animation" / "renders"
    normalized_dir = render_dir / "normalized"
    render_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, Any]] = []
    total_duration = 0.0

    try:
        for order, beat in enumerate(timeline, start=1):
            if not isinstance(beat, dict):
                raise ValueError(f"timeline item {order} must be an object")
            composition_id = str(beat.get("composition_id", ""))
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", composition_id) or composition_id not in by_id:
                raise ValueError(f"unknown composition in timeline: {composition_id}")
            composition = by_id[composition_id]
            source = project_path(project, composition.get("source"), "composition source")
            variables = read_object(project_path(project, composition.get("variables_file"), "variables file"))
            variables["exportMode"] = "mp4"
            native = render_dir / f"{order:02d}-{composition_id}-native.mp4"
            normalized = normalized_dir / f"{order:02d}-{composition_id}.mp4"
            render_command = npx + [
                "--yes", f"hyperframes@{HYPERFRAMES_VERSION}", "render", "--quality", args.quality,
                "--format", "mp4", "--strict-variables", "--variables",
                json.dumps(variables, ensure_ascii=False, separators=(",", ":")), "--output", str(native),
            ]
            run(render_command, cwd=source.parent, dry_run=args.dry_run)
            native_duration = float(composition.get("duration_seconds", 0))
            target_duration = float(beat.get("duration_seconds", 0))
            if native_duration <= 0 or target_duration <= 0:
                raise ValueError(f"invalid duration for {composition_id}")
            speed = target_duration / native_duration
            normalize_command = [
                ffmpeg, "-hide_banner", "-loglevel", "warning", "-y", "-i", str(native),
                "-vf", f"setpts={speed:.9f}*PTS,scale=1920:1080:flags=lanczos,fps=30,format=yuv420p",
                "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-movflags", "+faststart", str(normalized),
            ]
            run(normalize_command, cwd=project, dry_run=args.dry_run)
            rendered.append({
                "id": composition_id,
                "template_id": composition.get("template_id"),
                "source": composition.get("source"),
                "native_render": native.relative_to(project).as_posix(),
                "normalized_render": normalized.relative_to(project).as_posix(),
                "target_duration_seconds": target_duration,
            })
            total_duration += target_duration

        concat_file = normalized_dir / "concat.txt"
        concat_lines = []
        for index, item in enumerate(rendered, start=1):
            filename = f"{index:02d}-{item['id']}.mp4"
            concat_lines.append(f"file '{(normalized_dir / filename).as_posix()}'\n")
        concat_text = "".join(concat_lines)
        if not args.dry_run:
            concat_file.write_text(concat_text, encoding="utf-8")
        silent = render_dir / "composer-silent.mp4"
        run([ffmpeg, "-hide_banner", "-loglevel", "warning", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(silent)], cwd=project, dry_run=args.dry_run)

        slug = re.sub(r"[^a-z0-9]+", "-", project.name.lower()).strip("-") or "explainer"
        output = args.output.resolve() if args.output else project / "最终交付" / "08_ai_animation" / f"{slug}-ai-animation.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        voiceover = find_voiceover(project, args.voiceover)
        if voiceover:
            run([
                ffmpeg, "-hide_banner", "-loglevel", "warning", "-y", "-i", str(silent), "-i", str(voiceover),
                "-filter:a", f"apad=pad_dur={total_duration:.3f}", "-t", f"{total_duration:.3f}",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
            ], cwd=project, dry_run=args.dry_run)
        elif not args.dry_run:
            shutil.copy2(silent, output)

        subtitle_source = project / "audio" / "captions.srt"
        subtitle_output = project / "最终交付" / "03_口播与字幕" / "中文字幕.srt"
        subtitle_output.parent.mkdir(parents=True, exist_ok=True)
        if subtitle_source.is_file() and not args.dry_run:
            shutil.copy2(subtitle_source, subtitle_output)
        manifest = {
            "schema_version": 1,
            "ai_animation": True,
            "engine": "hyperframes",
            "composer": "ai-animation-composer-v1",
            "motion_standard": plan.get("motion_standard"),
            "plan": "animation/ai_animation_plan.json",
            "total_duration_seconds": total_duration,
            "voiceover": voiceover.relative_to(project).as_posix() if voiceover and voiceover.is_relative_to(project) else (str(voiceover) if voiceover else None),
            "subtitle_policy": "post-production-only",
            "subtitle": subtitle_output.relative_to(project).as_posix() if subtitle_source.is_file() else None,
            "final_output": output.relative_to(project).as_posix() if output.is_relative_to(project) else str(output),
            "compositions": [{**item, "output": item["normalized_render"]} for item in rendered],
        }
        manifest_path = project / "qa" / "metadata" / "ai_animation_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        if not args.dry_run:
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output)
        print(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
