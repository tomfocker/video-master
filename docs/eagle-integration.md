# Eagle Integration Exploration

Date: 2026-05-09

This note explores how Eagle can work with `video-master` as a local media asset source, reference-style library, audio/SFX catalog, and optional deliverables archive.

## Current Local Findings

- Eagle is running locally on port `41595`.
- The app reports version `4.0.0` on macOS.
- The V1 API endpoints under `/api/...` respond successfully.
- The V2 endpoints under `/api/v2/...` returned `method not allowed` in this local probe, so the first implementation should support V1 and treat V2 as an optional upgrade path.
- Recent Eagle libraries include:
  - `/Volumes/剪辑盘/音乐音效库.library`
  - `/Volumes/剪辑盘/视频素材库.library`
  - `/Volumes/剪辑盘/灵感提示库.library`
- Local library sizes and approximate item directory counts:
  - `音乐音效库.library`: about 77 GB, about 21,234 item directories
  - `视频素材库.library`: about 952 MB, about 44 item directories
  - `灵感提示库.library`: about 18 MB, about 8 item directories
- Eagle item folders use this practical disk layout:

```text
<library>.library/images/<item_id>.info/
  metadata.json
  <original media file>
  <thumbnail>.png
```

- A real audio item was located at:

```text
/Volumes/剪辑盘/音乐音效库.library/images/LZYJTJQVVS48T.info/
  WHSH_SYNTH WHOOSH-Too Hot To Handle_B00M_BRUTE FORCE.wav
```

- During this exploration, the Eagle asset library was manually adjusted in the Eagle app. One probe showed `library/info` and `item/list` pointing at different practical library contexts; treat this as volatile live-app state rather than proof of an Eagle API bug. The integration must verify the intended library path before importing or exporting, and should not silently assume the currently visible Eagle UI library is the API list target.

## Why This Fits Video Master

`video-master` already has strong slots for existing materials:

- `sources/` for user-provided assets.
- `references/reference_style_manifest.md` for classifying reference assets.
- `references/style_analysis.md`, `color_style.md`, and `editing_style.md` for extracting transferable visual rules.
- `audio/music_sfx_cue_sheet.md` for per-shot SFX and whole-film music direction.
- `最终交付/` for storyboard images, prompts, subtitles, previews, workbooks, and title packaging.

Eagle can become the asset browser and archive around those slots.

## Integration Opportunities

### 1. Import Eagle Assets Into A Video Project

Goal: let the user choose Eagle items and pull them into a `video-master` project as source assets.

Recommended behavior:

- Query Eagle libraries, folders, and items.
- Let the user filter by folder, extension, keyword, tag, rating, or recent items.
- Copy small image/reference assets into the project `sources/` directory.
- For large audio/video files, default to recording the original Eagle path in a manifest instead of copying, then offer a copy option when the project needs to be portable.
- Write `sources/eagle_assets_manifest.json` with:
  - Eagle library path
  - item ID
  - item name
  - extension
  - original file path
  - thumbnail path
  - source URL
  - tags/folders
  - role: `reference_style`, `reference_subject`, `music`, `sfx`, `stock_video`, `do-not-copy`

This maps directly into Step 1 and Step 3.5 of the skill.

### 2. Use Eagle As A Reference Style Library

Goal: turn saved screenshots, stills, posters, video clips, and packaging references into safe style rules.

Recommended behavior:

- User selects Eagle items as style references.
- `video-master` copies or records them under `references/reference_keyframes/`.
- The workflow classifies each as `reference_style`, not as content to copy.
- Generated analysis feeds:
  - palette and contrast
  - lighting and material
  - camera/framing language
  - packaging/typography mood
  - editing rhythm for video references

This is especially valuable for the existing `reference-derived` visual style lock.

### 3. Use Eagle As A Music And SFX Picker

Goal: make `audio/music_sfx_cue_sheet.md` less abstract by linking real audio candidates.

Recommended behavior:

- Search Eagle audio libraries by folder names such as `音乐`, `音效`, `转场`, `whoosh`, `impact`, `riser`, `片头`.
- For each shot, suggest 2-5 candidate SFX assets and write their Eagle IDs/paths into an audio candidate manifest.
- Keep background music as whole-film planning, not per-shot generated music.
- For animatic previews, optionally use the selected local audio path if the user confirms rights and wants a preview mix.

This fits the current audio policy without forcing generated music into video-model prompts.

### 4. Export Video Master Deliverables Back To Eagle

Goal: after a project is generated, archive useful outputs in Eagle.

Export candidates:

- storyboard frames from `最终交付/01_分镜图/`
- storyboard overview PNG from `最终交付/04_分镜总览/`
- animatic preview MP4 from `最终交付/05_预览视频/`
- title packaging PNG/MOV from `最终交付/07_title_packaging/`
- selected prompt or script files only if Eagle handles them well in the current library

Recommended tags:

- `video-master`
- project slug
- shot IDs such as `S01`
- `storyboard`
- `title-packaging`
- target model, for example `seedance-2.0`

Use Eagle add-from-path endpoints only after user confirmation because this writes into the Eagle library.

### 5. Round-Trip Metadata

Goal: keep Eagle and `video-master` connected without directly editing Eagle's internal files.

Recommended behavior:

- Store Eagle IDs in project manifests.
- Store source URL and notes from Eagle in project files.
- Optionally write back tags/annotations to Eagle only when the user asks.
- Never modify Eagle `metadata.json` files directly.

This lets the project remember where each asset came from while avoiding hidden library damage.

### 6. WebUI Panel

Goal: make Eagle feel like a native asset drawer inside the existing local WebUI.

Possible WebUI panels:

- Eagle connection status
- library selector
- folder tree
- search/filter
- selected asset tray
- "Import as reference style"
- "Import as subject/product asset"
- "Import as SFX/music candidate"
- "Export deliverables to Eagle"

This would sit beside the existing project browser and storyboard controls.

## Proposed Implementation Shape

Keep the installable skill self-contained under `skills/video-master/`.

Suggested new files:

```text
skills/video-master/scripts/eagle_client.py
skills/video-master/scripts/eagle_import.py
skills/video-master/scripts/eagle_export.py
skills/video-master/references/eagle-integration.md
tests/test_eagle_client.py
tests/test_eagle_import.py
tests/test_eagle_export.py
```

`eagle_client.py`:

- local HTTP client for `http://localhost:41595`
- V1-first endpoints:
  - `/api/application/info`
  - `/api/library/info`
  - `/api/library/history`
  - `/api/folder/list`
  - `/api/item/list`
  - `/api/item/addFromPath`
  - `/api/item/addFromPaths`
  - `/api/item/update` only behind explicit opt-in
- no token storage for localhost
- optional token argument for LAN use, never written into repo files

`eagle_import.py`:

- list libraries and folders
- search items
- resolve item original file path from `library_path/images/<item_id>.info/`
- classify imported assets by role
- write `sources/eagle_assets_manifest.json`

`eagle_export.py`:

- discover user-facing deliverables from `最终交付/`
- optionally create or use a target Eagle folder
- import files using Eagle's add-from-path API
- tag imported items with project metadata

## Safety And Product Rules

- Default mode must be read-only.
- Any action that writes to Eagle, switches libraries, updates tags, or imports files must require explicit confirmation.
- Do not log or commit the Eagle API token.
- Do not rely on V2 until the local app confirms it works.
- Do not directly edit files inside `.library/images/*/metadata.json`.
- For commercial projects, selected music/SFX/video stock assets need rights confirmation before final use.
- Large media should be referenced by path by default; copying should be a deliberate portable-package option.

## Recommended First Milestone

Build a read-only Eagle bridge:

1. Detect Eagle status.
2. List recent libraries.
3. Inspect one chosen library path.
4. List folders and search items.
5. Resolve original file paths.
6. Generate `sources/eagle_assets_manifest.json` for a project.
7. Feed selected `reference_style` assets into the existing reference-style analysis step.

This gives immediate value without changing Eagle data or the current skill pipeline.

Status:

- Implemented a read-only `scripts/eagle_client.py` helper for resolving Eagle item IDs to original media files.
- `scripts/make_animatic.py` can now use `--eagle-background-music-id <item_id>` and optional `--eagle-library-path <path>` to mix an Eagle audio item into `分镜预览.mp4`.
- The preview manifest records `background_music_source.type: eagle` with the Eagle item ID, name, original file path, library path, and thumbnail path when available.

## Later Milestones

- Add SFX/music candidate browsing and ranking for `audio/music_sfx_cue_sheet.md`.
- Add deliverables export back to Eagle.
- Add WebUI asset drawer.
- Add optional Eagle annotation/tag write-back.
- Add V2 API support when the local Eagle build responds successfully.
