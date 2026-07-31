#!/usr/bin/env python3
"""Validate the deliberately small artifact set of an AI-animation preview."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


PREVIEW_SPEC = Path("animation/preview_spec.json")
PLAN_PATH = Path("animation/ai_animation_plan.json")
MANIFEST_PATH = Path("qa/metadata/ai_animation_manifest.json")


def load_object(project: Path, relative: Path, errors: list[str]) -> dict:
    path = project / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {relative.as_posix()}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {relative.as_posix()}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{relative.as_posix()} must be a JSON object")
        return {}
    return value


def existing_file(project: Path, relative: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        errors.append(f"{label} is missing")
        return None
    path = (project / relative).resolve()
    if not path.is_relative_to(project) or not path.is_file() or path.stat().st_size == 0:
        errors.append(f"{label} is unavailable: {relative}")
        return None
    return path


def video_probe(path: Path, errors: list[str]) -> float | None:
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
        "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        errors.append(f"cannot inspect rendered output with ffprobe: {exc}")
        return None
    if result.returncode != 0:
        errors.append(f"ffprobe failed for {path.name}: {result.stderr.strip() or 'unknown error'}")
        return None
    try:
        payload = json.loads(result.stdout)
        duration = float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"ffprobe returned no usable duration for {path.name}: {exc}")
        return None
    streams = payload.get("streams") if isinstance(payload, dict) else []
    if not isinstance(streams, list) or not any(item.get("codec_type") == "video" for item in streams if isinstance(item, dict)):
        errors.append(f"rendered output has no video stream: {path.name}")
    return duration


def validate_alignment(project: Path, manifest: dict, errors: list[str]) -> None:
    if manifest.get("timing_policy") != "service-returned-start-seconds":
        return
    relative = manifest.get("alignment_source", "audio/voice_alignment.json")
    path = existing_file(project, relative, "alignment source", errors)
    if path is None:
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid alignment JSON: {exc}")
        return
    alignment = payload.get("alignment") if isinstance(payload, dict) else None
    tokens = alignment.get("tokens") if isinstance(alignment, dict) else None
    if not isinstance(tokens, list) or not tokens:
        errors.append("service-returned alignment requires a non-empty alignment.tokens list")
        return
    previous_start = -1.0
    for index, token in enumerate(tokens, start=1):
        if not isinstance(token, dict):
            errors.append(f"alignment token {index} must be an object")
            continue
        start, end = token.get("start_seconds"), token.get("end_seconds")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < previous_start or end < start:
            errors.append(f"alignment token {index} has invalid ordered boundaries")
        elif str(token.get("text") or "").strip() == "":
            errors.append(f"alignment token {index} has empty text")
        previous_start = float(start) if isinstance(start, (int, float)) else previous_start


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a minimal AI-animation preview.")
    parser.add_argument("project", type=Path, help="Preview project directory")
    args = parser.parse_args()
    project = args.project.resolve()
    errors: list[str] = []
    if not project.is_dir():
        print(f"ERROR: project directory does not exist: {project}")
        return 2

    spec = load_object(project, PREVIEW_SPEC, errors)
    if spec.get("workflow_profile") != "ai-animation-preview":
        errors.append("preview_spec workflow_profile must be ai-animation-preview")
    plan = load_object(project, PLAN_PATH, errors)
    if plan.get("enabled") is not True or plan.get("engine") != "hyperframes":
        errors.append("AI animation plan must enable the hyperframes engine")
    if plan.get("execution_mode") not in {"hyperframes", "hybrid"}:
        errors.append("AI animation plan execution_mode must be hyperframes or hybrid")
    compositions = plan.get("compositions")
    durations: dict[str, float] = {}
    if not isinstance(compositions, list) or not compositions:
        errors.append("AI animation plan requires a non-empty compositions list")
    else:
        for index, composition in enumerate(compositions, start=1):
            if not isinstance(composition, dict):
                errors.append(f"plan composition {index} must be an object")
                continue
            composition_id = str(composition.get("id") or "")
            source = existing_file(project, composition.get("source"), f"plan composition {index} source", errors)
            duration = composition.get("duration_seconds")
            if not composition_id:
                errors.append(f"plan composition {index} id is missing")
            if not isinstance(duration, (int, float)) or duration <= 0:
                errors.append(f"plan composition {index} duration_seconds must be positive")
            elif source is not None:
                durations[composition_id] = float(duration)

    manifest = load_object(project, MANIFEST_PATH, errors)
    if manifest.get("ai_animation") is not True or manifest.get("engine") != "hyperframes":
        errors.append("AI animation manifest must identify HyperFrames")
    rendered = manifest.get("compositions")
    if not isinstance(rendered, list) or not rendered:
        errors.append("AI animation manifest requires rendered compositions")
    else:
        for index, composition in enumerate(rendered, start=1):
            if not isinstance(composition, dict):
                errors.append(f"manifest composition {index} must be an object")
                continue
            composition_id = str(composition.get("id") or "")
            existing_file(project, composition.get("source"), f"manifest composition {index} source", errors)
            output = existing_file(project, composition.get("output"), f"manifest composition {index} output", errors)
            if output is None:
                continue
            measured = video_probe(output, errors)
            declared = durations.get(composition_id, composition.get("duration_seconds"))
            if measured is not None and isinstance(declared, (int, float)) and abs(measured - float(declared)) > 0.5:
                errors.append(f"{output.name} duration {measured:.3f}s does not match declared {float(declared):.3f}s")

    validate_alignment(project, manifest, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: AI-animation preview {project.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
