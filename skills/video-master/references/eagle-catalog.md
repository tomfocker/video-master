# Curated Eagle BGM Catalog

`eagle-library-catalog.json` is intentionally a tiny, human-curated catalog of reusable BGM—not a mirror of the Eagle library. It currently holds the five approved-to-describe music tracks and their editorial notes. Eagle remains the source of truth.

## Refresh an explicit BGM set

The command refreshes only the five IDs already curated in the catalog. To add a track, explicitly pass it by ID or select it in Eagle. It never enumerates all library items.

```bash
python3 ${SKILL_DIR}/scripts/eagle_library_index.py
python3 ${SKILL_DIR}/scripts/eagle_library_index.py --item-id <EAGLE_BGM_ID>
python3 ${SKILL_DIR}/scripts/eagle_library_index.py --selected
```

The file stores only safe discovery metadata: Eagle ID, name, media kind, extension, tags, folder IDs, dimensions, and editorial curation. It intentionally excludes original paths, thumbnails, source URLs, annotations, voice references, and other private source details.

## What does not belong here

Do not put the 8,880-icon library—or any other high-cardinality visual set—into this JSON. A full copy has an ongoing update cost, duplicates Eagle's exact-search index, and increases every agent's context/load cost without making selection more reliable. At the current stage, query Eagle MCP directly for icons; the batch candidate-pool helper is deliberately experimental and should only evolve after repeated real-project friction is observed.

## Project use

1. Search the curated BGM descriptions for likely tracks using mood, energy, and rights requirements.
2. Verify the candidate against live Eagle and present the item plus intended role for confirmation.
3. Use `eagle_asset_intake.py` to create the project-local manifest and, only when needed, a portable copy.
4. Record exact project provenance in `sources/eagle_assets_manifest.json`; never use the catalog alone as proof of current availability or reuse rights.
