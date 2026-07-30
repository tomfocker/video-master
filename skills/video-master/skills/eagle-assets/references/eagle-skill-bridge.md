# Official Eagle Skill Bridge

Use this module to make Eagle a predictable source for Video Master projects. The official Eagle Skill is bundled with Eagle's **Eagle MCP** plugin; the Skill supplies on-demand instructions and a CLI, while the plugin supplies the local MCP server. They are complementary, not alternatives.

## Setup And Recovery

The normal prerequisite is Eagle 4.0 Build 12 or newer with the **Eagle MCP** plugin installed and enabled. Its local endpoint is `http://127.0.0.1:41596/mcp`.

1. Run `scripts/eagle_mcp_status.py --json` from Video Master.
2. If the endpoint is unavailable, open Eagle → **插件** → **插件中心**, install **Eagle MCP**, then enable it. It starts the local server.
3. If the endpoint works but the official Codex Skill is absent, run `scripts/eagle_mcp_status.py --install-official-skill`. It copies the official bundle provided by the installed plugin into `$CODEX_HOME/skills/eagle-skill` (`~/.codex/skills/eagle-skill` by default).
4. Start a new Codex turn after installation so its Skill metadata can be loaded.

The installer intentionally does not download a third-party package. It uses the exact bundle shipped by the locally installed Eagle MCP plugin. Re-run it with `--overwrite` after updating that plugin if a refresh is needed.

## Operating Modes

| Scope | Default capability | Approval needed |
| --- | --- | --- |
| Video asset discovery | Read-only search, selection, metadata inspection | No additional approval |
| Video project intake | Write the project's provenance manifest and optional project-local copy | Confirm the selected item and intended role |
| Eagle library management | Tags, folders, comments, ratings, imports, moves, trash, bulk edits | Explicit request plus approve-after-preview |

Do not modify Eagle's internal `.library` files directly. A file in Eagle is not proof that it has reuse rights; retain the project's rights decision and attribution separately.

## Write-Consent SOP

When the user actually asks to change Eagle, use the official `eagle` Skill and work in three phases:

1. **Analyze:** scope a folder, IDs, tags, count, or time range; use read-only calls to form a proposed change list.
2. **Preview:** present target items, exact fields to change, estimated count, and any uncertain classification. Start with a small batch.
3. **Execute:** make the smallest confirmed write. Report the result and any failures; do not silently broaden scope.

Never translate/merge tags, reorganize folders, import output files, or remove items merely because they would make a video project tidier.

## Privacy

Eagle MCP runs locally. With a cloud model, file names, tags, search queries, annotations, and returned metadata can still be included in model context. Avoid broad processing of sensitive libraries; constrain searches to a folder, a small result count, or an explicit selection. Do not write private paths or source URLs into the shared Eagle catalog; use the project-local provenance manifest only after confirmation.
