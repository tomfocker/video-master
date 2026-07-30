#!/usr/bin/env python3
"""Bring confirmed Eagle selections into a video project without changing Eagle."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eagle_mcp_client import DEFAULT_EAGLE_MCP_URL, EagleMcpClient, EagleMcpError


MANIFEST_RELATIVE = Path("sources") / "eagle_assets_manifest.json"
VALID_ROLES = {"visual_asset", "reference_style", "video_clip", "background_music", "sound_effect"}
IMAGE_EXTENSIONS = {"avif", "bmp", "gif", "jpeg", "jpg", "png", "svg", "tif", "tiff", "webp"}
VIDEO_EXTENSIONS = {"avi", "m4v", "mkv", "mov", "mp4", "mpeg", "mpg", "webm"}
AUDIO_EXTENSIONS = {"aac", "aif", "aiff", "flac", "m4a", "mp3", "ogg", "opus", "wav"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_extension(ext: str) -> str:
    value = ext.lower().lstrip(".")
    if value in IMAGE_EXTENSIONS:
        return "image"
    if value in VIDEO_EXTENSIONS:
        return "video"
    if value in AUDIO_EXTENSIONS:
        return "audio"
    return "other"


def item_path(item: dict[str, Any], keys: tuple[str, ...]) -> Path | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value).expanduser()
    return None


def item_record(item: dict[str, Any], role: str, *, mcp_url: str) -> dict[str, Any]:
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        raise ValueError("Eagle item is missing id")
    original = item_path(item, ("filePath", "file_path", "sourcePath", "source_path", "path"))
    if original is None:
        raise ValueError(f"Eagle item {item_id} does not include its original file path; request full item details")
    original = original.resolve()
    if not original.is_file():
        raise FileNotFoundError(f"Eagle source file is unavailable: {original}")
    ext = str(item.get("ext") or original.suffix.lstrip(".")).lower().lstrip(".")
    thumbnail = item_path(item, ("thumbnailPath", "thumbnail_path"))
    return {
        "id": item_id,
        "name": str(item.get("name") or original.stem),
        "ext": ext,
        "kind": classify_extension(ext),
        "roles": [role],
        "original_path": str(original),
        "thumbnail_path": str(thumbnail.resolve()) if thumbnail and thumbnail.is_file() else None,
        "mcp_url": mcp_url,
        "read_only_source": True,
        "imported_at": utc_now(),
    }


def new_manifest(mcp_url: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source": "official-eagle-mcp",
        "mcp_url": mcp_url,
        "read_only_source": True,
        "assets": [],
    }


def read_manifest(path: Path, mcp_url: str) -> dict[str, Any]:
    if not path.is_file():
        return new_manifest(mcp_url)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("assets"), list):
        raise ValueError(f"invalid Eagle asset manifest: {path}")
    return value


def safe_filename(item_id: str, name: str, ext: str) -> str:
    stem = re.sub(r"[^\w.-]+", "-", name, flags=re.UNICODE).strip(".-") or "asset"
    suffix = f".{ext.lstrip('.')}" if ext else ""
    return f"{item_id}_{stem}{suffix}"


def copy_into_project(project: Path, asset: dict[str, Any]) -> str:
    destination_dir = project / "sources" / "eagle"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / safe_filename(asset["id"], asset["name"], asset["ext"])
    shutil.copy2(Path(asset["original_path"]), destination)
    return destination.relative_to(project).as_posix()


def merge_assets(manifest: dict[str, Any], incoming: list[dict[str, Any]], *, project: Path, copy_files: bool) -> list[dict[str, Any]]:
    existing = {
        str(asset.get("id")): asset
        for asset in manifest.get("assets", [])
        if isinstance(asset, dict) and asset.get("id")
    }
    merged: list[dict[str, Any]] = []
    for asset in incoming:
        prior = existing.get(asset["id"])
        if prior:
            roles = set(str(role) for role in prior.get("roles", []) if role)
            roles.update(asset["roles"])
            asset["roles"] = sorted(roles)
            for field in ("project_path", "hyperframes_stages"):
                if field in prior:
                    asset[field] = prior[field]
        if copy_files:
            asset["project_path"] = copy_into_project(project, asset)
            asset["materialization"] = "copied"
        else:
            asset["materialization"] = "copied" if asset.get("project_path") else "linked"
        existing[asset["id"]] = asset
        merged.append(asset)
    manifest["assets"] = [existing[key] for key in sorted(existing)]
    manifest["updated_at"] = utc_now()
    return merged


def unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        item_id = str(item.get("id") or "")
        if item_id and item_id not in seen:
            result.append(item)
            seen.add(item_id)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--selected", action="store_true", help="Read the items currently selected in Eagle")
    parser.add_argument("--item-id", action="append", default=[], help="Read one Eagle item by ID; may be repeated")
    parser.add_argument("--query", help="Read items returned by Eagle's text query")
    parser.add_argument("--role", choices=sorted(VALID_ROLES), default="visual_asset")
    parser.add_argument("--copy", action="store_true", help="Copy approved source files into sources/eagle; default is a linked manifest only")
    parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    args = parser.parse_args(argv)
    if not (args.selected or args.item_id or args.query):
        parser.error("choose --selected, --item-id, or --query")

    try:
        client = EagleMcpClient(args.mcp_url)
        items: list[dict[str, Any]] = []
        if args.selected:
            items.extend(client.selected_items())
        if args.item_id:
            items.extend(client.items_by_id(args.item_id))
        if args.query:
            items.extend(client.query_items(args.query))
        items = unique_items(items)
        if not items:
            raise ValueError("Eagle did not return any matching items")
        records = [item_record(item, args.role, mcp_url=args.mcp_url) for item in items]
        project = args.project.resolve()
        manifest_path = project / MANIFEST_RELATIVE
        manifest = read_manifest(manifest_path, args.mcp_url)
        merged = merge_assets(manifest, records, project=project, copy_files=args.copy)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (EagleMcpError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print(manifest_path)
    for asset in merged:
        print(f"{asset['id']}\t{asset['kind']}\t{asset['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
