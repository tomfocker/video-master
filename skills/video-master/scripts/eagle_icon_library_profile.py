#!/usr/bin/env python3
"""Refresh a compact, read-only category profile for a large Eagle icon library."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eagle_mcp_client import DEFAULT_EAGLE_MCP_URL, EagleMcpClient, EagleMcpError


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_OUTPUT = SKILL_DIR / "references" / "eagle-icon-library-profile.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def flatten_folders(nodes: object) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    if not isinstance(nodes, list):
        return flattened
    for node in nodes:
        if not isinstance(node, dict):
            continue
        flattened.append(node)
        flattened.extend(flatten_folders(node.get("children")))
    return flattened


def coerce_count(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, dict):
        for key in ("count", "total", "totalCount"):
            if isinstance(value.get(key), (int, float)):
                return int(value[key])
        for key in ("data", "result"):
            nested = value.get(key)
            if nested is not None:
                return coerce_count(nested)
    raise ValueError("Eagle item_count did not return a numeric count")


def build_profile(folder_tree: object, client: EagleMcpClient, *, root_name: str, extension: str) -> dict[str, Any]:
    roots = [node for node in folder_tree if isinstance(node, dict) and str(node.get("name") or "") == root_name]
    if len(roots) != 1:
        raise ValueError(f"expected exactly one Eagle root folder named {root_name!r}, found {len(roots)}")
    root = roots[0]
    categories: list[dict[str, Any]] = []
    for child in root.get("children", []):
        if not isinstance(child, dict):
            continue
        folder_id = str(child.get("id") or "").strip()
        name = str(child.get("name") or "").strip()
        if not folder_id or not name:
            continue
        count = coerce_count(client.call_tool("item_count", {"folders": [folder_id], "ext": extension}))
        categories.append({"id": folder_id, "name": name, "item_count": count})
    categories.sort(key=lambda category: str(category["name"]).casefold())
    return {
        "schema_version": 1,
        "source": "official-eagle-mcp",
        "read_only_source": True,
        "generated_at": utc_now(),
        "scope": "compact-icon-category-profile",
        "root": {"id": str(root.get("id") or ""), "name": root_name},
        "filter": {"extension": extension.lower().lstrip(".")},
        "summary": {
            "category_count": len(categories),
            "item_count": sum(int(category["item_count"]) for category in categories),
            "note": "Category map only; individual icon records remain exclusively in Eagle.",
        },
        "categories": categories,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--root-name", default="original")
    parser.add_argument("--extension", default="png")
    parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        client = EagleMcpClient(args.mcp_url)
        tree = client.call_tool("folder_get", {"getAllHierarchy": True, "fullDetails": True})
        if not isinstance(tree, list):
            raise ValueError("Eagle folder_get did not return a folder list")
        profile = build_profile(tree, client, root_name=args.root_name, extension=args.extension)
    except (EagleMcpError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if args.dry_run:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        return 0
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(json.dumps(profile["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
