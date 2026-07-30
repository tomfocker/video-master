#!/usr/bin/env python3
"""Refresh a safe, read-only Eagle inventory for Video Master asset discovery."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from eagle_asset_intake import classify_extension
from eagle_mcp_client import DEFAULT_EAGLE_MCP_URL, EagleMcpClient, EagleMcpError, coerce_item_list


SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_OUTPUT = SKILL_DIR / "references" / "eagle-library-catalog.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def catalog_record(item: dict[str, Any]) -> dict[str, Any] | None:
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        return None
    ext = str(item.get("ext") or "").lower().lstrip(".")
    record: dict[str, Any] = {
        "id": item_id,
        "name": str(item.get("name") or "").strip() or item_id,
        "kind": classify_extension(ext),
        "ext": ext,
        "tags": text_list(item.get("tags")),
        "folders": text_list(item.get("folders")),
    }
    for field in ("width", "height"):
        value = item.get(field)
        if isinstance(value, (int, float)) and value > 0:
            record[field] = int(value)
    return record


def fetch_all_items(client: EagleMcpClient, *, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        batch = coerce_item_list(
            client.call_tool("item_get", {"fullDetails": False, "limit": limit, "offset": offset})
        )
        items.extend(batch)
        if len(batch) < limit:
            break
        offset += len(batch)
    return items


def build_catalog(items: list[dict[str, Any]], *, include_other: bool, mcp_url: str) -> dict[str, Any]:
    assets = [record for item in items if (record := catalog_record(item)) is not None]
    if not include_other:
        assets = [asset for asset in assets if asset["kind"] in {"image", "video", "audio"}]
    assets.sort(key=lambda asset: (asset["kind"], asset["name"].casefold(), asset["id"]))
    counts: dict[str, int] = {}
    for asset in assets:
        kind = str(asset["kind"])
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "schema_version": 1,
        "source": "official-eagle-mcp",
        "mcp_url": mcp_url,
        "read_only_source": True,
        "generated_at": utc_now(),
        "privacy": "No original paths, thumbnails, URLs, annotations, or voice references are stored.",
        "catalog_scope": "video-relevant" if not include_other else "all-items",
        "summary": {"asset_count": len(assets), "kind_counts": counts},
        "assets": assets,
    }


def read_existing_curation(path: Path, asset_ids: set[str]) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    raw = value.get("curation_by_id") if isinstance(value, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(item_id): record
        for item_id, record in raw.items()
        if str(item_id) in asset_ids and isinstance(record, dict)
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    parser.add_argument("--limit", type=int, default=1000, help="MCP page size, 1..1000")
    parser.add_argument("--include-other", action="store_true", help="Include non-image/video/audio records")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be within 1..1000")
    try:
        catalog = build_catalog(
            fetch_all_items(EagleMcpClient(args.mcp_url), limit=args.limit),
            include_other=args.include_other,
            mcp_url=args.mcp_url,
        )
    except EagleMcpError as exc:
        print(f"ERROR: {exc}")
        return 1
    output = args.output.resolve()
    catalog["curation_by_id"] = read_existing_curation(
        output,
        {str(asset["id"]) for asset in catalog["assets"]},
    )
    if args.dry_run:
        print(json.dumps(catalog["summary"], ensure_ascii=False))
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(json.dumps(catalog["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
