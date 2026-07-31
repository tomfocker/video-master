#!/usr/bin/env python3
"""Create Eagle-backed asset candidate pools, then intake only confirmed picks.

The planner is deliberately a query orchestrator, not a second asset database:
Eagle performs text retrieval and remains the source of truth.  The output only
contains compact discovery metadata, and the confirm route batch-validates
approved IDs before it writes a project manifest.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eagle_asset_intake import MANIFEST_RELATIVE, VALID_ROLES, item_record, merge_assets, new_manifest, read_manifest
from eagle_mcp_client import DEFAULT_EAGLE_MCP_URL, EagleMcpClient, EagleMcpError


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_PROFILE = SKILL_DIR / "references" / "eagle-icon-library-profile.json"
SCHEMA_VERSION = 1
DEFAULT_POOL_LIMIT = 32
DEFAULT_SHOT_LIMIT = 6
MAX_LIMIT = 100


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def write_json(path: Path, value: object) -> Path:
    output = path.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def string_list(value: object, *, field: str, required: bool = False) -> list[str]:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array of strings")
    values = [str(item).strip() for item in value if isinstance(item, str) and item.strip()]
    if len(values) != len(value):
        raise ValueError(f"{field} must contain non-empty strings only")
    if required and not values:
        raise ValueError(f"{field} must not be empty")
    return list(dict.fromkeys(values))


def positive_limit(value: object, *, field: str, default: int) -> int:
    if value is None:
        return default
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_LIMIT:
        raise ValueError(f"{field} must be an integer from 1 to {MAX_LIMIT}")
    return value


def discovery_record(item: dict[str, Any]) -> dict[str, Any]:
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        raise ValueError("Eagle returned a candidate without an id")
    record: dict[str, Any] = {
        "id": item_id,
        "name": str(item.get("name") or item_id),
        "ext": str(item.get("ext") or "").lower().lstrip("."),
        "tags": sorted({str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()})
        if isinstance(item.get("tags"), list)
        else [],
        "folders": sorted({str(folder).strip() for folder in item.get("folders", []) if str(folder).strip()})
        if isinstance(item.get("folders"), list)
        else [],
    }
    for field in ("width", "height"):
        if isinstance(item.get(field), (int, float)) and item[field] > 0:
            record[field] = int(item[field])
    return record


def profile_category_map(profile: dict[str, Any]) -> dict[str, str]:
    categories = profile.get("categories")
    if not isinstance(categories, list):
        raise ValueError("icon library profile requires a categories array")
    result: dict[str, str] = {}
    for category in categories:
        if not isinstance(category, dict):
            continue
        name = str(category.get("name") or "").strip()
        folder_id = str(category.get("id") or "").strip()
        if name and folder_id:
            result[name] = folder_id
    if not result:
        raise ValueError("icon library profile contains no usable categories")
    return result


def resolve_folder_ids(pool: dict[str, Any], category_map: dict[str, str]) -> list[str]:
    folder_ids = string_list(pool.get("folder_ids"), field=f"pools.{pool.get('id', '?')}.folder_ids")
    categories = string_list(pool.get("categories"), field=f"pools.{pool.get('id', '?')}.categories")
    missing = [name for name in categories if name not in category_map]
    if missing:
        raise ValueError(f"pool {pool.get('id', '?')} names unknown icon categories: {', '.join(missing)}")
    return list(dict.fromkeys([*folder_ids, *(category_map[name] for name in categories)]))


def phrase(term: str) -> str:
    cleaned = term.replace('"', " ").strip()
    if not cleaned:
        raise ValueError("search terms may not be empty")
    return f'"{cleaned}"' if re.search(r"\s", cleaned) else cleaned


def build_or_query(terms: list[str]) -> str:
    if not terms:
        raise ValueError("a candidate pool requires at least one search term")
    return " OR ".join(phrase(term) for term in terms)


def constrained(items: list[dict[str, Any]], *, folder_ids: list[str], extensions: list[str]) -> list[dict[str, Any]]:
    wanted_folders = set(folder_ids)
    wanted_extensions = {extension.lower().lstrip(".") for extension in extensions}
    result: list[dict[str, Any]] = []
    for item in items:
        record = discovery_record(item)
        if wanted_folders and not wanted_folders.intersection(record["folders"]):
            continue
        if wanted_extensions and record["ext"] not in wanted_extensions:
            continue
        result.append(record)
    return result


def relevance(record: dict[str, Any], terms: list[str]) -> tuple[int, list[str]]:
    haystack_name = str(record.get("name") or "").casefold()
    haystack_tags = " ".join(str(tag) for tag in record.get("tags", [])).casefold()
    matched: list[str] = []
    score = 0
    for term in terms:
        needle = term.casefold()
        if needle and needle in haystack_name:
            score += 10
            matched.append(term)
        elif needle and needle in haystack_tags:
            score += 4
            matched.append(term)
    return score, matched


def ranked(records: list[dict[str, Any]], *, terms: list[str], limit: int) -> list[dict[str, Any]]:
    scored: list[tuple[int, list[str], dict[str, Any]]] = []
    for record in records:
        score, matched = relevance(record, terms)
        scored.append((score, matched, record))
    scored.sort(key=lambda item: (-item[0], str(item[2]["name"]).casefold(), str(item[2]["id"])))
    return [record for _, _, record in scored[:limit]]


def plan_candidate_pool(request: dict[str, Any], client: EagleMcpClient, *, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    if request.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"candidate-pool request requires schema_version={SCHEMA_VERSION}")
    raw_pools = request.get("pools")
    raw_shots = request.get("shots")
    if not isinstance(raw_pools, list) or not raw_pools:
        raise ValueError("candidate-pool request requires a non-empty pools array")
    if not isinstance(raw_shots, list) or not raw_shots:
        raise ValueError("candidate-pool request requires a non-empty shots array")
    category_map = profile_category_map(profile) if profile is not None else {}
    pools: dict[str, dict[str, Any]] = {}
    # Keep the complete constrained result only for this in-memory planning run.
    # A pool's display limit must never hide a strong candidate from a later
    # shot-specific ranking.
    pool_records: dict[str, list[dict[str, Any]]] = {}
    for raw_pool in raw_pools:
        if not isinstance(raw_pool, dict):
            raise ValueError("each pool must be an object")
        pool_id = str(raw_pool.get("id") or "").strip()
        if not pool_id or pool_id in pools:
            raise ValueError("each pool requires a unique non-empty id")
        terms = string_list(raw_pool.get("terms"), field=f"pools.{pool_id}.terms", required=True)
        extensions = string_list(raw_pool.get("extensions"), field=f"pools.{pool_id}.extensions")
        folder_ids = resolve_folder_ids(raw_pool, category_map)
        query = build_or_query(terms)
        queried = client.query_items(query, full_details=False)
        constrained_records = constrained(queried, folder_ids=folder_ids, extensions=extensions)
        limit = positive_limit(raw_pool.get("limit"), field=f"pools.{pool_id}.limit", default=DEFAULT_POOL_LIMIT)
        pool_records[pool_id] = constrained_records
        pools[pool_id] = {
            "id": pool_id,
            "query": query,
            "terms": terms,
            "folder_ids": folder_ids,
            "extensions": [extension.lower().lstrip(".") for extension in extensions],
            "query_hit_count": len(queried),
            "constrained_hit_count": len(constrained_records),
            "candidates": ranked(constrained_records, terms=terms, limit=limit),
        }

    shots: list[dict[str, Any]] = []
    known_shot_ids: set[str] = set()
    for raw_shot in raw_shots:
        if not isinstance(raw_shot, dict):
            raise ValueError("each shot must be an object")
        shot_id = str(raw_shot.get("id") or "").strip()
        if not shot_id or shot_id in known_shot_ids:
            raise ValueError("each shot requires a unique non-empty id")
        known_shot_ids.add(shot_id)
        pool_ids = string_list(raw_shot.get("pool_ids"), field=f"shots.{shot_id}.pool_ids", required=True)
        missing_pools = [pool_id for pool_id in pool_ids if pool_id not in pools]
        if missing_pools:
            raise ValueError(f"shot {shot_id} references unknown pools: {', '.join(missing_pools)}")
        terms = string_list(raw_shot.get("terms"), field=f"shots.{shot_id}.terms")
        if not terms:
            terms = list(dict.fromkeys(term for pool_id in pool_ids for term in pools[pool_id]["terms"]))
        candidates_by_id: dict[str, dict[str, Any]] = {}
        candidate_pools: dict[str, list[str]] = {}
        for pool_id in pool_ids:
            for candidate in pool_records[pool_id]:
                candidate_id = str(candidate["id"])
                candidates_by_id[candidate_id] = candidate
                candidate_pools.setdefault(candidate_id, []).append(pool_id)
        ranked_candidates: list[dict[str, Any]] = []
        for candidate in candidates_by_id.values():
            score, matched_terms = relevance(candidate, terms)
            ranked_candidates.append(
                {
                    **candidate,
                    "score": score,
                    "matched_terms": matched_terms,
                    "pool_ids": candidate_pools[str(candidate["id"])],
                }
            )
        ranked_candidates.sort(key=lambda candidate: (-int(candidate["score"]), str(candidate["name"]).casefold(), str(candidate["id"])))
        shot: dict[str, Any] = {
            "id": shot_id,
            "pool_ids": pool_ids,
            "terms": terms,
            "candidate_count": len(ranked_candidates),
            "candidates": ranked_candidates[:positive_limit(raw_shot.get("limit"), field=f"shots.{shot_id}.limit", default=DEFAULT_SHOT_LIMIT)],
        }
        if isinstance(raw_shot.get("intent"), str) and raw_shot["intent"].strip():
            shot["intent"] = raw_shot["intent"].strip()
        shots.append(shot)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "official-eagle-mcp",
        "read_only_source": True,
        "generated_at": utc_now(),
        "workflow": "batch-candidate-pool",
        "pools": list(pools.values()),
        "shots": shots,
        "summary": {
            "pool_count": len(pools),
            "shot_count": len(shots),
            "candidate_count": sum(len(shot["candidates"]) for shot in shots),
            "note": "Candidates are not approved assets. Confirm IDs before project intake.",
        },
    }


def allowed_candidate_pairs(pool: dict[str, Any]) -> set[tuple[str, str]]:
    allowed: set[tuple[str, str]] = set()
    for shot in pool.get("shots", []):
        if not isinstance(shot, dict):
            continue
        shot_id = str(shot.get("id") or "")
        for candidate in shot.get("candidates", []):
            if isinstance(candidate, dict) and str(candidate.get("id") or ""):
                allowed.add((shot_id, str(candidate["id"])))
    return allowed


def confirmed_selection_records(selection: dict[str, Any], pool: dict[str, Any]) -> list[dict[str, str]]:
    if selection.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"selection requires schema_version={SCHEMA_VERSION}")
    raw_selections = selection.get("selections")
    if not isinstance(raw_selections, list) or not raw_selections:
        raise ValueError("selection requires a non-empty selections array")
    allowed = allowed_candidate_pairs(pool)
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in raw_selections:
        if not isinstance(raw, dict):
            raise ValueError("each selection must be an object")
        shot_id = str(raw.get("shot_id") or "").strip()
        item_id = str(raw.get("item_id") or "").strip()
        role = str(raw.get("role") or "visual_asset").strip()
        if (shot_id, item_id) not in allowed:
            raise ValueError(f"selection {shot_id}/{item_id} is not a candidate returned for that shot")
        if role not in VALID_ROLES:
            raise ValueError(f"selection {shot_id}/{item_id} has unsupported role: {role}")
        usage = str(raw.get("usage") or "").strip()
        key = (shot_id, item_id, role)
        if key not in seen:
            result.append({"shot_id": shot_id, "item_id": item_id, "role": role, "usage": usage})
            seen.add(key)
    return result


def merge_shot_assignments(manifest: dict[str, Any], selections: list[dict[str, str]]) -> None:
    current = manifest.get("shot_asset_assignments", [])
    existing = [item for item in current if isinstance(item, dict)] if isinstance(current, list) else []
    keys = {(str(item.get("shot_id") or ""), str(item.get("item_id") or ""), str(item.get("role") or "")) for item in existing}
    for selection in selections:
        key = (selection["shot_id"], selection["item_id"], selection["role"])
        if key not in keys:
            entry = {key: value for key, value in selection.items() if value}
            existing.append(entry)
            keys.add(key)
    manifest["shot_asset_assignments"] = sorted(
        existing,
        key=lambda item: (str(item.get("shot_id") or ""), str(item.get("item_id") or ""), str(item.get("role") or "")),
    )


def apply_confirmed_selection(
    pool: dict[str, Any], selection: dict[str, Any], client: EagleMcpClient, *, project: Path, copy_files: bool = False
) -> tuple[Path, list[dict[str, Any]]]:
    selections = confirmed_selection_records(selection, pool)
    item_ids = list(dict.fromkeys(selection["item_id"] for selection in selections))
    returned = client.items_by_id(item_ids)
    by_id = {str(item.get("id") or ""): item for item in returned if isinstance(item, dict)}
    missing = [item_id for item_id in item_ids if item_id not in by_id]
    if missing:
        raise ValueError(f"Eagle could not batch-validate selected IDs: {', '.join(missing)}")
    roles_by_id: dict[str, set[str]] = {}
    for selection_item in selections:
        roles_by_id.setdefault(selection_item["item_id"], set()).add(selection_item["role"])
    records: list[dict[str, Any]] = []
    for item_id in item_ids:
        for role in sorted(roles_by_id[item_id]):
            records.append(item_record(by_id[item_id], role, mcp_url=client.base_url))
    project = project.resolve()
    manifest_path = project / MANIFEST_RELATIVE
    manifest = read_manifest(manifest_path, client.base_url) if manifest_path.is_file() else new_manifest(client.base_url)
    merged = merge_assets(manifest, records, project=project, copy_files=copy_files)
    merge_shot_assignments(manifest, selections)
    manifest["candidate_pool_confirmation"] = {"source": "official-eagle-mcp", "confirmed_at": utc_now()}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path, merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    plan_parser = subcommands.add_parser("plan", help="Search Eagle once per thematic pool and group candidates by shot")
    plan_parser.add_argument("request", type=Path)
    plan_parser.add_argument("--output", type=Path, required=True)
    plan_parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    plan_parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    confirm_parser = subcommands.add_parser("confirm", help="Batch-validate approved IDs and write only them to a project manifest")
    confirm_parser.add_argument("candidate_pool", type=Path)
    confirm_parser.add_argument("selection", type=Path)
    confirm_parser.add_argument("--project", type=Path, required=True)
    confirm_parser.add_argument("--copy", action="store_true")
    confirm_parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            request = read_json_object(args.request, label="candidate-pool request")
            needs_profile = any(isinstance(pool, dict) and pool.get("categories") for pool in request.get("pools", []))
            profile = read_json_object(args.profile, label="icon library profile") if needs_profile else None
            result = plan_candidate_pool(request, EagleMcpClient(args.mcp_url), profile=profile)
            output = write_json(args.output, result)
            print(output)
            print(json.dumps(result["summary"], ensure_ascii=False))
        else:
            pool = read_json_object(args.candidate_pool, label="candidate-pool result")
            if pool.get("source") != "official-eagle-mcp" or pool.get("workflow") != "batch-candidate-pool":
                raise ValueError("candidate-pool result must come from the official Eagle batch-candidate-pool route")
            selection = read_json_object(args.selection, label="confirmed selection")
            manifest_path, merged = apply_confirmed_selection(
                pool, selection, EagleMcpClient(args.mcp_url), project=args.project, copy_files=args.copy
            )
            print(manifest_path)
            for asset in merged:
                print(f"{asset['id']}\t{asset['kind']}\t{asset['name']}")
    except (EagleMcpError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
