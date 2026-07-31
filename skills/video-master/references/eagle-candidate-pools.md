# Experimental Eagle Batch Candidate Pools

This helper is intentionally **not** the current default. Agents should first query Eagle MCP directly per concrete shot, using the compact category profile only as orientation. Keep this script available as an evidence-driven optimisation: revisit it only when real projects repeatedly make agents do the same “merge keywords → filter folders/types → deduplicate → map candidates back to shots” work.

When that repetition is established, this route can solve the orchestration layer without copying a large Eagle library into the skill:

1. Extract visual intents and exact bilingual keywords from all shots.
2. Group related terms into a few thematic pools.
3. Query Eagle once per pool with `OR`; apply folder/category and extension constraints locally to the live results.
4. Score and trim the result per shot into small candidate lists.
5. Review/confirm the final IDs. One `item_get(ids: [...])` call validates them together, then only those assets are written to the project manifest.

Eagle is the source of truth. The candidate-pool result is disposable discovery output; it is not an approval and must never be copied into `sources/eagle_assets_manifest.json`. Do not turn the compact category profile into a full local asset index.

## Compact icon library profile

`eagle-icon-library-profile.json` holds category names, Eagle folder IDs, and counts only. Refresh it after a folder reorganization or material import—not during every video request:

```bash
python3 ${SKILL_DIR}/scripts/eagle_icon_library_profile.py
```

It deliberately has no per-icon records, thumbnails, paths, or generated descriptions.

## Request contract

Save a request JSON such as:

```json
{
  "schema_version": 1,
  "pools": [
    {
      "id": "space-tech",
      "terms": ["卫星", "火箭", "轨道"],
      "categories": ["科学技术", "交通工具"],
      "extensions": ["png"],
      "limit": 24
    },
    {
      "id": "health-data",
      "terms": ["医生", "显微镜", "心脏"],
      "categories": ["医疗健康", "科学技术"],
      "extensions": ["png"]
    }
  ],
  "shots": [
    {
      "id": "S01",
      "intent": "卫星发出数据链路，建立宏观科技感",
      "pool_ids": ["space-tech"],
      "terms": ["卫星", "轨道"],
      "limit": 5
    },
    {
      "id": "S02",
      "intent": "显微镜与医生共同解释科学证据",
      "pool_ids": ["health-data"],
      "terms": ["显微镜", "医生"],
      "limit": 5
    }
  ]
}
```

Rules:

- `terms` are literal search terms; the tool safely builds a single `OR` query for each pool.
- `categories` resolve through the compact profile. Use `folder_ids` when a project needs an explicit folder outside that profile.
- `extensions` is optional. `limit` is 1–100; defaults are 32 displayed candidates per pool and 6 candidates per shot. Shot ranking always considers the full constrained live pool before either list is trimmed, so one generic pool cannot crowd out a better match for a later shot.
- A candidate result includes only ID, name, extension, tags, folders, dimensions, match score, and originating pool—never file paths or thumbnails.

Run the planning phase read-only:

```bash
python3 ${SKILL_DIR}/scripts/eagle_candidate_pool.py plan request.json --output candidate_pool.json
```

## Confirmation and project intake

After an explicit review, create a small selection file. An ID can only be confirmed for the shot where it was actually returned as a candidate.

```json
{
  "schema_version": 1,
  "selections": [
    {
      "shot_id": "S01",
      "item_id": "<EAGLE_ITEM_ID>",
      "role": "visual_asset",
      "usage": "hero satellite icon"
    }
  ]
}
```

Then validate and intake in one batch:

```bash
python3 ${SKILL_DIR}/scripts/eagle_candidate_pool.py confirm candidate_pool.json selection.json --project <project_path>
```

`confirm` reads Eagle but never edits it. It batch-fetches the selected IDs, verifies each original file exists, and writes only confirmed records plus `shot_asset_assignments` to `sources/eagle_assets_manifest.json`. Pass `--copy` only when the project needs portable source copies.
