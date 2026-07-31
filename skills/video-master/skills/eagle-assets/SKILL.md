---
name: eagle-assets
description: Internal Video Master module for Eagle asset discovery, readiness checks, project-local intake, and safe use of Eagle images, video, music, or SFX. Use whenever a video task mentions Eagle, an Eagle library, selected Eagle assets, Eagle BGM, or Eagle catalog search.
---

# Eagle Assets

Prepare Eagle before using it as a video source. Treat its official `eagle` Skill as the library-management authority and keep video production read-only unless the user explicitly requests a library edit.

## Start With A Preflight

Run once per live Eagle session:

```bash
python3 ${SKILL_DIR}/scripts/eagle_mcp_status.py --json
```

If status is `ready`, use the official Eagle Skill for search or a user selection in Eagle. If it is `mcp_ready_skill_missing`, install the plugin-bundled official Skill once:

```bash
python3 ${SKILL_DIR}/scripts/eagle_mcp_status.py --install-official-skill
```

If status is `mcp_unavailable`, do not ask the user to diagnose it. Give the exact recovery path from `references/eagle-skill-bridge.md`, then continue with non-Eagle input when possible. Do not call legacy Eagle APIs or assume port 41595 is equivalent to the official MCP endpoint.

## Route Work Safely

1. For discovery, selection, app/version checks, and general Eagle library tasks, use the globally installed official `eagle` Skill after preflight.
2. For an active video project, read `../../references/eagle-assets.md` and keep all default operations read-only: search/inspect/select in Eagle, then write only the project's `sources/eagle_assets_manifest.json`. For large icon sets, query Eagle MCP directly; use the compact category profile only as orientation. `../../references/eagle-candidate-pools.md` is an experimental helper, not a default route. Do not generate a second full icon index.
3. Show candidate IDs, names, and intended project roles before intake unless the user has already confirmed the selection.
4. Use `eagle_asset_intake.py` for confirmed assets. Use a project copy only when portability or rendering requires it.
5. Treat tags, folders, comments, ratings, imports, moves, and deletion in Eagle as a separate library-management task. Read `references/eagle-skill-bridge.md` and require an explicit approve-after-preview step before any write.

## Read The Needed Reference

- Setup, privacy, and write-consent SOP: `references/eagle-skill-bridge.md`
- Project intake and HyperFrames stages: `../../references/eagle-assets.md`
- Curated BGM recall and curation: `../../references/eagle-catalog.md`
- Compact icon overview and experimental candidate pools: `../../references/eagle-icon-library-profile.json` and `../../references/eagle-candidate-pools.md`
