# Eagle Assets for HyperFrames

Use the official Eagle MCP plugin only to discover and read assets for a video project. Keep Eagle as the source library: this workflow never changes tags, folders, ratings, comments, or library files.

For recurring production, refresh and search the local catalog described in `eagle-catalog.md` before doing a live Eagle search. The catalog narrows candidates; live Eagle confirmation and project intake remain mandatory.

## Preconditions

- Eagle is running and its official **Eagle MCP** plugin is enabled on `http://127.0.0.1:41596/mcp`.
- Use the official Eagle Skill to search for candidates or select assets manually in Eagle.
- For every write to the video project, the user has confirmed the selected Eagle items and their intended use.

## Intake

Select items in Eagle, then register the selection in the project:

```bash
python3 ${SKILL_DIR}/scripts/eagle_asset_intake.py <project_path> --selected --role visual_asset
```

The command calls only the official local MCP server and writes `sources/eagle_assets_manifest.json`. By default it records the original Eagle path without copying anything. Use `--copy` only when the project must carry a portable project-level copy:

```bash
python3 ${SKILL_DIR}/scripts/eagle_asset_intake.py <project_path> --item-id <EAGLE_ITEM_ID> --role background_music --copy
```

Valid roles are `visual_asset`, `reference_style`, `video_clip`, `background_music`, and `sound_effect`.

## HyperFrames Media Stage

For an approved image or video, create a project-local full-frame HyperFrames stage:

```bash
python3 ${SKILL_DIR}/scripts/ai_animation/init_eagle_media_stage.py <project_path> --asset-id <EAGLE_ITEM_ID> --title "标题" --caption "素材说明"
python3 ${SKILL_DIR}/scripts/ai_animation/render_motion_template.py <project_path> --composition-id eagle-media-<item-id-lowercase> --format mp4
```

The stage copies the approved source into its own composition directory so HyperFrames can render a stable relative file. It then records the composition and source relationship in both `animation/ai_animation_plan.json` and the Eagle asset manifest. This modifies the video project only, never the Eagle library.

Image stages are the default reliable path. Video stages use a local muted looping `<video>` element; run a full render and inspect it before delivery because browser-video capture depends on the local HyperFrames runtime.

## Composer Timeline and Whole-film Audio

When the project already has an AI Animation Composer plan, attach the confirmed Eagle image or video to the actual final timeline. This only changes the project plan; it does not change the Eagle library:

```bash
python3 ${SKILL_DIR}/scripts/ai_animation/init_eagle_media_stage.py <project_path> --asset-id <EAGLE_ITEM_ID> --append-to-composer --insert-after <existing-composition-id>
python3 ${SKILL_DIR}/scripts/ai_animation/render_composer.py <project_path>
```

`--append-to-composer` adds the stage at the end by default. `--insert-after` places it immediately after an existing Composer composition and reflows the later timestamps. Compose the explainer first, then add the Eagle stage; generating a new Composer plan later replaces the old plan.

For approved Eagle BGM, register it with the `background_music` role, then Composer and animatic previews can use it from the project manifest:

```bash
python3 ${SKILL_DIR}/scripts/eagle_asset_intake.py <project_path> --selected --role background_music --copy
python3 ${SKILL_DIR}/scripts/ai_animation/render_composer.py <project_path> --eagle-background-music-id <EAGLE_BGM_ID>
python3 ${SKILL_DIR}/scripts/make_animatic.py <project_path> --eagle-background-music-id <EAGLE_BGM_ID>
```

The project-manifest route is preferred. It reads no Eagle data during rendering and records the selected item ID and local/original source in the output manifest. Composer uses the first approved `background_music` manifest item when no explicit project BGM file is present; use `--eagle-background-music-id` whenever multiple tracks are registered.

## Working Rules

1. Search or select first; do not ask an agent to reorganize Eagle as part of video production.
2. Present selected asset IDs, names, paths, and intended roles before intake when the user has not already explicitly confirmed them.
3. Keep exact source attribution in `sources/eagle_assets_manifest.json`.
4. Treat linked original files as non-portable. Use `--copy` or the media-stage initializer when the project needs an independent local copy.
5. Preserve rights constraints: a file being in Eagle does not by itself grant permission to reuse it in a generated or delivered video.
