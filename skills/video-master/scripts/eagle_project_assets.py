#!/usr/bin/env python3
"""Resolve already-approved Eagle project assets without calling Eagle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EAGLE_ASSET_MANIFEST = Path("sources") / "eagle_assets_manifest.json"


def resolve_eagle_audio_asset(
    project: Path,
    *,
    role: str = "background_music",
    item_id: str | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Resolve one approved audio asset from a project manifest.

    The manifest is the complete contract at render time. This helper never
    contacts Eagle and therefore cannot modify the source library.
    """

    manifest_path = project / EAGLE_ASSET_MANIFEST
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid Eagle asset manifest: {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("source") != "official-eagle-mcp":
        raise ValueError("Eagle asset manifest must identify official-eagle-mcp as its source")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Eagle asset manifest requires an assets list")
    candidates = [
        asset
        for asset in assets
        if isinstance(asset, dict)
        and role in asset.get("roles", [])
        and str(asset.get("kind") or "").lower() == "audio"
    ]
    if item_id:
        candidates = [asset for asset in candidates if str(asset.get("id") or "") == item_id]
        if not candidates:
            raise ValueError(f"approved Eagle {role} was not found in the project manifest: {item_id}")
    if not candidates:
        return None
    asset = candidates[0]
    copied_relative = asset.get("project_path")
    if isinstance(copied_relative, str) and copied_relative:
        source = (project / copied_relative).resolve()
        if not source.is_relative_to(project) or not source.is_file():
            raise ValueError(f"approved Eagle project copy is unavailable: {copied_relative}")
    else:
        original = asset.get("original_path")
        source = Path(str(original or "")).expanduser().resolve()
        if not original or not source.is_file():
            raise ValueError(f"approved Eagle source is unavailable: {original or '<missing>'}")
    return source, {
        "type": "eagle_manifest",
        "manifest": EAGLE_ASSET_MANIFEST.as_posix(),
        "item_id": str(asset.get("id") or ""),
        "name": str(asset.get("name") or ""),
        "role": role,
        "materialization": str(asset.get("materialization") or "linked"),
        "path": str(source),
    }
