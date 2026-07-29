#!/usr/bin/env python3
"""Validate the reusable AI-animation registry and typography runtime."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2]
MODULE_DIR = SKILL_DIR / "ai_animation"
REGISTRY = MODULE_DIR / "registry.json"
CATALOG = MODULE_DIR / "typography" / "catalog.json"
RUNTIME = MODULE_DIR / "typography" / "runtime" / "text-effects-runtime.js"
CATALOG_JS = MODULE_DIR / "typography" / "runtime" / "text-effects-catalog.js"
STYLES = MODULE_DIR / "typography" / "runtime" / "text-effects.css"
SHOWCASE = MODULE_DIR / "typography" / "examples" / "hyperframes-showcase.html"
NOTICE = MODULE_DIR / "typography" / "THIRD_PARTY_NOTICES.md"
LICENSE = MODULE_DIR / "typography" / "licenses" / "sakura-animate-text-MIT.txt"


def read_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path.relative_to(SKILL_DIR)}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path.relative_to(SKILL_DIR)}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected object: {path.relative_to(SKILL_DIR)}")
        return {}
    return value


def validate_effect(effect: object, index: int, seen_ids: set[str], seen_sources: set[str], errors: list[str]) -> None:
    label = f"effect[{index}]"
    if not isinstance(effect, dict):
        errors.append(f"{label} must be an object")
        return
    required = {
        "id",
        "source_id",
        "display_name_zh",
        "category",
        "split",
        "duration_ms",
        "stagger_ms",
        "easing",
        "energy",
        "tone",
        "recommended_for",
        "avoid_for",
        "cjk_safe",
        "frames",
    }
    missing = sorted(required - effect.keys())
    if missing:
        errors.append(f"{label} missing fields: {', '.join(missing)}")
        return
    effect_id = str(effect["id"])
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", effect_id):
        errors.append(f"{label} has invalid id: {effect_id}")
    if effect_id in seen_ids:
        errors.append(f"duplicate effect id: {effect_id}")
    seen_ids.add(effect_id)
    source_id = str(effect["source_id"])
    if source_id in seen_sources:
        errors.append(f"duplicate source_id: {source_id}")
    seen_sources.add(source_id)
    if effect["category"] not in {"entrance", "exit", "loop", "swap"}:
        errors.append(f"{effect_id}: invalid category")
    if effect["split"] not in {"whole", "characters", "words", "lines"}:
        errors.append(f"{effect_id}: invalid split")
    if effect["energy"] not in {"low", "medium", "high"}:
        errors.append(f"{effect_id}: invalid energy")
    if not isinstance(effect["duration_ms"], (int, float)) or effect["duration_ms"] <= 0:
        errors.append(f"{effect_id}: duration_ms must be positive")
    if not isinstance(effect["stagger_ms"], (int, float)) or effect["stagger_ms"] < 0:
        errors.append(f"{effect_id}: stagger_ms must be non-negative")
    if effect["cjk_safe"] is not True:
        errors.append(f"{effect_id}: curated typography effects must set cjk_safe=true")
    frames = effect["frames"]
    if not isinstance(frames, list) or len(frames) < 2:
        errors.append(f"{effect_id}: frames must contain at least two keyframes")
        return
    offsets = [frame.get("offset") for frame in frames if isinstance(frame, dict)]
    if len(offsets) != len(frames) or offsets[0] != 0 or offsets[-1] != 1:
        errors.append(f"{effect_id}: frame offsets must start at 0 and end at 1")
    elif offsets != sorted(offsets) or any(not isinstance(value, (int, float)) or value < 0 or value > 1 for value in offsets):
        errors.append(f"{effect_id}: frame offsets must be ordered within 0..1")


def main() -> int:
    errors: list[str] = []
    registry = read_json(REGISTRY, errors)
    catalog = read_json(CATALOG, errors)
    for path in [RUNTIME, CATALOG_JS, STYLES, SHOWCASE, NOTICE, LICENSE]:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty file: {path.relative_to(SKILL_DIR)}")

    if registry.get("module_id") != "ai-animation":
        errors.append("registry module_id must be ai-animation")
    modules = registry.get("modules")
    if not isinstance(modules, list) or not any(isinstance(item, dict) and item.get("id") == "typography" for item in modules):
        errors.append("registry must declare the typography module")

    source = catalog.get("source")
    if not isinstance(source, dict) or source.get("license") != "MIT" or not source.get("commit"):
        errors.append("catalog source must pin an MIT-licensed commit")
    effects = catalog.get("effects")
    if not isinstance(effects, list) or not effects:
        errors.append("catalog must contain effects")
        effects = []
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    for index, effect in enumerate(effects):
        validate_effect(effect, index, seen_ids, seen_sources, errors)

    policy = catalog.get("selection_policy", {})
    policy_ids: set[str] = set()
    if isinstance(policy, dict):
        for key, value in policy.items():
            if key.startswith("default_for_") or key == "high_energy_only":
                if isinstance(value, list):
                    policy_ids.update(str(item) for item in value)
    unknown_policy_ids = sorted(policy_ids - seen_ids)
    if unknown_policy_ids:
        errors.append(f"selection policy references unknown effects: {', '.join(unknown_policy_ids)}")

    if CATALOG_JS.is_file() and catalog:
        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from build_assets import render_catalog_js

        if CATALOG_JS.read_text(encoding="utf-8") != render_catalog_js(catalog):
            errors.append("generated text-effects-catalog.js is stale")

    if RUNTIME.is_file():
        runtime_text = RUNTIME.read_text(encoding="utf-8")
        if "Infinity" in runtime_text or "iterations: loop" in runtime_text:
            errors.append("runtime must not create infinite render-time animations")
        for marker in ["animation.pause()", "animation.currentTime", "fill: \"both\""]:
            if marker not in runtime_text:
                errors.append(f"runtime missing deterministic WAAPI marker: {marker}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {len(effects)} curated typography effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
