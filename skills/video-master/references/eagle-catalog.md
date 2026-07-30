# Eagle Catalog-first Discovery

Use a refreshed local catalog for candidate recall, then confirm the final item in live Eagle before intake. This is faster and more consistent than beginning every project with an unbounded library search, but it must not replace the live library as the source of truth.

## Refresh

Refresh after a significant import/cleanup, or on a sensible recurring cadence for an active library. Do not refresh during every video request.

```bash
python3 ${SKILL_DIR}/scripts/eagle_library_index.py
```

The generated `references/eagle-library-catalog.json` contains only safe discovery metadata: Eagle ID, name, media kind, extension, tags, folder IDs, and dimensions. It intentionally excludes original paths, thumbnails, source URLs, annotations, voice references, and other private source details. The refresh reads Eagle through its official MCP server and never changes Eagle.

## Curation

The generated file preserves `curation_by_id` entries for assets still in the library. An AI or reviewer can add concise fields such as `description`, `mood`, `energy`, `tempo_bpm`, `vocal`, `usage_notes`, `rights_status`, and `review_status` keyed by Eagle ID. Keep curation separate from Eagle tags unless the user explicitly asks to write tags back into Eagle.

A catalog only helps semantic retrieval when its names, tags, or curation describe the assets. Hash-like filenames and empty tags are still poor search inputs; prioritize curation for frequently reused BGM, SFX, logos, products, locations, and reference imagery.

## Project use

1. Search the catalog for likely candidates using the locked brief, mood, media type, and rights requirements.
2. Verify the candidate against live Eagle and present the item plus intended role for confirmation.
3. Use `eagle_asset_intake.py` to create the project-local manifest and, only when needed, a portable copy.
4. Record exact project provenance in `sources/eagle_assets_manifest.json`; never use the catalog alone as proof of a file's current availability or reuse rights.
