#!/usr/bin/env python3
"""Refresh Video Master's explicit, curated Eagle BGM catalog.

This deliberately does *not* enumerate the whole Eagle library.  Icons and
other high-cardinality asset sets stay in Eagle and are discovered through the
batch candidate-pool route instead.
"""

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
from eagle_mcp_client import DEFAULT_EAGLE_MCP_URL, EagleMcpClient, EagleMcpError


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


def build_catalog(items: list[dict[str, Any]], *, mcp_url: str) -> dict[str, Any]:
    """Build the small, hand-curated BGM catalog from explicit Eagle items."""

    assets = [record for item in items if (record := catalog_record(item)) is not None and record["kind"] == "audio"]
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
        "catalog_scope": "curated-bgm",
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


def read_existing_asset_ids(path: Path) -> list[str]:
    """Return the existing curated IDs without copying their metadata forward."""

    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    assets = value.get("assets") if isinstance(value, dict) else None
    if not isinstance(assets, list):
        return []
    return [str(asset.get("id")) for asset in assets if isinstance(asset, dict) and str(asset.get("id") or "").strip()]


def unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        item_id = str(item.get("id") or "").strip()
        if item_id and item_id not in seen:
            result.append(item)
            seen.add(item_id)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    parser.add_argument("--item-id", action="append", default=[], help="Explicit BGM ID to add or refresh; may be repeated")
    parser.add_argument("--selected", action="store_true", help="Refresh the BGM items currently selected in Eagle")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        client = EagleMcpClient(args.mcp_url)
        items: list[dict[str, Any]] = []
        existing_ids = read_existing_asset_ids(output)
        if existing_ids:
            items.extend(client.items_by_id(existing_ids))
        if args.item_id:
            items.extend(client.items_by_id(args.item_id))
        if args.selected:
            items.extend(client.selected_items())
        if not items:
            raise ValueError(
                "no curated BGM IDs are available; pass --item-id <EAGLE_ID> or select approved BGM in Eagle"
            )
        catalog = build_catalog(unique_items(items), mcp_url=args.mcp_url)
        if not catalog["assets"]:
            raise ValueError("the explicit Eagle selection contained no audio items for the BGM catalog")
    except EagleMcpError as exc:
        print(f"ERROR: {exc}")
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
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
