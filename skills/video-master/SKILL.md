---
name: video-master
description: Use when a user wants to turn a video idea, campaign brief, existing assets, story, product concept, or rough requirement into a video production package with creative strategy, script/copy/audio, shot list/storyboard, native image-generated frames, model-specific prompts, or deterministic AI animation assembled from reusable HyperFrames typography and motion modules. Triggers include video-master, 视频脚本, 分镜, storyboard, 短视频, 广告片, TVC, 产品宣传片, AI视频提示词, AI动画, 概念动画, 科普动画, HyperFrames, or video prompt.
---

# Video Master

Turn a video requirement into a traceable production package. Work as the main producer: lock requirements, route specialist work, maintain canonical project files, validate outputs, and package user-facing deliverables.

## Operating Rules

- Match the user's language unless requested otherwise.
- Default to `video_projects/<project_slug>_<YYYYMMDD_HHMM>/` under the current workspace.
- Follow the pipeline gates. Do not create later-phase deliverables before their required inputs exist.
- Treat `brief/spec_lock.md` as the execution contract. Re-read it before generating frames, prompts, animation, or final files.
- Use the schemas and project tree in `references/output-contract.md`; do not invent parallel canonical formats.
- Use native image generation when the user requests storyboard frames, keyframes, visual boards, or designed title assets. Follow the dedicated `imagegen` skill when available.
- Default to assuming native image generation is available; do not mark it unavailable from a missing CLI key, environment variable, or tool listing. Only record image generation as unavailable after an actual native image-generation attempt fails. If it fails, preserve complete prompts, mark affected assets `Needs-Generation`, and record the reason in `qa/metadata/workflow_events.jsonl`.
- Never claim an asset exists without verifying its path.
- Keep exact copy, VO, subtitles, packaging text, and deterministic overlays outside generated-video prompt bodies unless the user explicitly authorizes model-rendered text.
- Default `subtitle_rendering_policy` to `post-production-only`, `burned_subtitles_allowed` to `false`, and per-clip generated background music to disabled.
- Reference-style analysis may describe existing captions, but final image/video prompts must not ask models to reproduce burned subtitles or subtitle styling.
- Request natural synchronous sound and room tone when model audio is relevant; add focused SFX cues without suppressing other natural sound.
- Do not include a `负面提示词` section in final video prompts. Express constraints positively under generation requirements.
- Do not reproduce protected characters, unlicensed likenesses, brand marks, source plots, watermarks, or creator-specific style. Distill references into transferable palette, light, framing, material, camera, rhythm, and packaging rules.
- Keep `title_packaging` and deterministic `ai_animation` as sidecar execution branches. They must not silently rewrite script, storyboard, or model prompts.

## Dependencies

The core Skill is instruction-driven. Install repository dependencies only when local rendering, TTS, workbook export, stronger validation, or WebUI operation is needed:

```bash
python3 -m pip install -r requirements.txt
```

## Specialist Skill Routing

Video Master remains self-contained. Use the following sibling Skills as optional specialist executors when they are installed or present; otherwise continue with Video Master's internal references.

- Use `$seedance-storyboard-director` during shot planning and final Seedance 2.0 prompt authoring. Pass the locked brief, rhythm, continuity anchors, reference-frame roles, audio policy, and requested deliverable paths. Video Master remains responsible for `spec_lock.md`, canonical files, QA, and packaging.
- Use `$midjourney-storyboard-prompts` when the chosen still-image workflow is Midjourney, especially for character anchors, scene anchors, `--cref`, and storyboard keyframes. Feed approved prompts or generated assets back into Video Master's manifest and continuity checks.
- Specialist output is a stage result, not a second project contract. Resolve conflicts in favor of the user's explicit direction and `brief/spec_lock.md`.

## Pipeline

### 0. Choose Workflow Mode

At project creation or a major restart, select:

- `autopilot`: make reversible assumptions, log them, and ask only about blockers, rights, unsupported claims, missing core assets, or irreversible choices.
- `guided`: confirm major creative and production decisions phase by phase.

Record `workflow_mode`, `confirmation_policy`, and `assumption_policy` in `brief/spec_lock.md`. Default to `autopilot` for “直接做/快速推进” and `guided` for brainstorming or comparison requests.

### 1. Classify Inputs And Routes

Classify the input as `idea-only`, `asset-assisted`, or `material-locked`. Write `strategy/input_readiness.md` with available assets, missing assets, invention boundaries, preserved wording, and source paths.

Classify each supplied reference as:

- `reference_style`: extract safe transferable visual and rhythm rules.
- `reference_subject`: preserve an authorized subject, product, person, or object.
- `do-not-copy`: record protected elements that must not be replicated.

Select the style route:

- `original`
- `use_style_template`
- `create_style_template_from_reference`

When using a template, record `template_id`, `allow_draft_template`, and `template_user_overrides`. User direction and supplied assets override template defaults. Official templates do not have light/medium/high strengths.

The user ideas override template defaults. Do not use a draft style template for a final project unless the user explicitly opts in with `allow_draft_template: true`.

Select a visual-style route: `preset`, `custom`, or `reference-derived`. Select `scene_director_pattern` when a repeatable scene grammar applies.

For AI-built explainers, concept motion, exact animated text, charts, diagrams, UI motion, spatial-camera work, or HyperFrames, read `references/ai-animation.md` and select `animation_execution_mode: generative-video | hyperframes | hybrid`.

### 2. Confirm Video Mode

Read `references/video-modes.md` and confirm a mode such as:

- `fast-paced-tvc`
- `product-promo-short`
- `narrative-short`
- `animation`
- `tutorial-explainer`
- `brand-film`
- `ecommerce-conversion-short`

When a repeatable scene grammar fits, also read `references/scene-director-patterns.md`. Write `strategy/video_mode.md` and do not proceed to scriptwriting until the mode is confirmed or explicitly assumed under `autopilot`.

### 3. Lock Production

Read `references/output-contract.md` and write:

- `brief/creative_brief.md`
- `brief/spec_lock.md`

Lock at minimum:

- objective, audience, platform, duration, aspect ratio, resolution, frame rate, and output language;
- workflow/input/video/style routes, template and scene-pattern choices;
- target image/video models and prompt dialect;
- `copy_language`, `voiceover_language`, caption/localization languages, `subtitle_rendering_policy`, `burned_subtitles_allowed`, generated-text, music, sync-sound, and SFX policies;
- story premise, message hierarchy, CTA, claims, safety, and rights constraints;
- character/product continuity, reference roles, style confirmation gate, and visual preset fields;
- storyboard coverage, image-generation expectations, preview profile, and final packaging requirements;
- optional title-packaging types and `title_packaging_enabled`;
- optional AI-animation mode, engine, selected registered modules, and `ai_animation_enabled`.

Use `references/platform-and-model-profiles.md` for model/platform constraints. Seedance 2.0 is the default target video model: use `target_model: seedance-2.0` and `prompt_dialect: seedance-2.0` unless the user explicitly names another video model. Confirm prompt language separately from copy, VO, and caption languages.

### 3.5. Analyze Reference Style

When `reference_style` assets exist, create:

- `references/reference_style_manifest.json`
- `references/style_analysis.md`
- `references/reference_keyframes/`

Separate measurable observations from director interpretation and safe transfer rules. Never treat reference ownership as permission to copy subjects, branding, dialogue, watermarks, or exact shots.

### Step 3.6: Visual Style Preset Lock And Character Lock

Read `references/visual-style-presets.md` and select a card from `references/visual_style_presets.json`, or write a custom/reference-derived equivalent with the same locked fields. Lock `visual_style_preset_id` before `prompts/storyboard_image_prompts.md` is written.

When recurring characters exist, create and confirm `characters/character_bible.md` and stable character IDs before batch storyboard generation. For formal image workflows, enforce `style_confirmation_gate`:

1. Create/confirm the character anchor when needed.
2. Generate only the first storyboard frame, S01.
3. Set `style_gate_status: pending`.
4. Wait for approval; do not batch-generate remaining storyboard frames.

Record `skipped` with a reason only for an explicit simulation/test or user-approved bypass.

### 4. Write Strategy And Rhythm

Write:

- `strategy/creative_strategy.md`
- `strategy/rhythm_map.md`

Use non-uniform shot timing appropriate to the confirmed mode. If a style template is selected, read its `template.md`, `director_notes.md`, `rhythm_rules.json`, and `editing_craft.md`; explain how the complete method is adapted to the current subject and user overrides.

### 5. Centralize Script, Copy, And Audio

Read `references/audio-and-copy.md` and write:

- `script/script.md`
- `audio/voiceover_script.md`
- `audio/tts_lines.json`
- `audio/captions.srt`
- localized SRT files when required
- `audio/music_sfx_cue_sheet.md`
- `audio/audio_generation_prompt.md`

Keep spoken copy centralized so TTS, captions, previews, and final delivery stay consistent. For Chinese-facing delivery, include Chinese subtitles even when the VO is English. Map natural sound and at least one useful SFX cue to every shot; reserve background music for whole-film post-production unless explicitly requested otherwise.

### 6. Plan Shots

Write `storyboard/shot_list.md` and `storyboard/shot_list.json`. Use a compact overview plus per-shot blocks containing timing, beat, action, framing, camera, movement, light/material, audio/copy references, continuity, transition, reference-frame roles, and image/video prompt seeds.

Read `references/scene-director-patterns.md` when a pattern is selected. If `$seedance-storyboard-director` is available and Seedance is targeted, use it here with the production lock as input.

For code-rendered shots, assign registered module/asset IDs instead of describing reusable effects only in prose.

### 7. Create Storyboard Prompts And Frames

Read `references/storyboard-and-video-prompts.md`, the locked visual-style card, character bible, reference-style analysis, and active template prompt rules.

Write `prompts/storyboard_image_prompts.md` before image generation. For recurring spaces or 15-second segments, create `SEGxx_SCENE` wide scene anchors before A-D/action frames. Keep each still to one decisive state.

When Midjourney is selected and `$midjourney-storyboard-prompts` is available, use it to create character/scene anchors and frame prompts. Otherwise follow Video Master's internal prompt patterns.

Generate only the coverage requested or required by the shot plan. Inspect character, product, palette, lighting, and composition continuity before updating `storyboard/storyboard_manifest.md`. Store working frames in `storyboard/frames/` and approved frames in `最终交付/01_分镜图/`.

### 8. Author Video Prompts

Write:

- `prompts/video_prompts.md`
- `最终交付/02_提示词/视频生成提示词.md`
- `最终交付/02_提示词/图片生成提示词.md`

Read `references/storyboard-and-video-prompts.md`, `references/platform-and-model-profiles.md`, and the selected template/pattern material. For Seedance 2.0 or 15-second web generation, also read `references/seedance2-practical-playbook.md` or use `$seedance-storyboard-director` when available.

Keep review prompts detailed and final copy-ready prompts compact. Seedance prompts must carry model, duration, aspect ratio, and references in the heading; lock scene and visual style; use rhythm-driven whole-second time slices; integrate action, camera, performance, material/environment motion, synchronous sound, and SFX; and consolidate stability, audio, and text policy under generation requirements. Do not add standalone `目标模型`, `时长`, `画幅`, or `参考图` lines.

Do not paste external VO lines, subtitle paths, packaging paths, or post-production commentary into model-facing prompt bodies.

### 8.4. Execute Optional AI Animation

Gate: `ai_animation_enabled` and mode is `hyperframes` or `hybrid`.

Read `references/ai-animation.md`, `references/ai-animation-motion-grammar.md`, `ai_animation/registry.json`, and the relevant catalog. For a multi-scene concept or science explainer, also read `references/ai-animation-composer.md`, create a structured beat brief, run `scripts/ai_animation/compose_explainer.py`, and assemble it with `scripts/ai_animation/render_composer.py`. Use `scripts/ai_animation/init_project.py` for isolated typography compositions and `scripts/ai_animation/init_motion_template.py` for isolated registered charts, comparisons, explainers, evidence cards, process diagrams, and transparent overlays. Write `animation/ai_animation_plan.json`, author finite deterministic compositions under `animation/compositions/`, and render work files under `animation/renders/`.

Copy approved outputs to `最终交付/08_ai_animation/` and write `qa/metadata/ai_animation_manifest.json`. Validate the library with `scripts/ai_animation/validate_library.py`; lint/check every composition before final render. Never claim an unregistered or only-planned module is available.

### 8.5. Execute Optional Title Packaging

Gate: the user requests `main_title`, `chapter_card`, lower thirds, `data_callout`, CTA/end cards, or animated overlays. This is an optional sidecar branch and does not modify video prompts.

Read the title-packaging sections in `references/storyboard-and-video-prompts.md` and `references/output-contract.md`. Write the separate packaging plan, prompts, assets, and manifest under `packaging/`, then copy approved files to `最终交付/07_title_packaging/`.

Default title packaging output is static transparent PNG. Render alpha MOV only for meaningful requested animation, not simple fades or offsets. Use `scripts/render_title_packaging.py` for exact text, verified transparency, and supported ProRes 4444 motion templates.

### 9. Package And Preview

Create the user-facing package defined in `references/output-contract.md`, including:

- `最终交付/00_使用说明.md`
- approved storyboard frames and image/video prompts
- `最终交付/03_口播与字幕/` copy, VO, and localized subtitles
- optional `07_title_packaging/` and `08_ai_animation/`
- any requested model/platform-specific files

Use the deterministic tools only when their deliverables are requested:

```bash
python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project_path>
python3 ${SKILL_DIR}/scripts/make_storyboard_overview.py <project_path>
python3 ${SKILL_DIR}/scripts/export_production_workbook.py <project_path>
python3 ${SKILL_DIR}/scripts/make_animatic.py <project_path>
python3 ${SKILL_DIR}/scripts/project_state.py <project_path> --write
python3 ${SKILL_DIR}/scripts/serve_webui.py --host 127.0.0.1 --port 8765
```

Keep work-in-progress files outside `最终交付/`. Treat `qa/metadata/project_state.json` as a read-only UI snapshot, never the canonical source.

### 10. Validate

Read `references/quality-check.md`. When project files exist, run:

```bash
python3 ${SKILL_DIR}/scripts/validate_video_project.py <project_path>
```

Fix failures before finishing. Report the project folder, user-facing delivery folder, generated image count/status, animation/title sidecar status, validator result, and remaining manual actions.

## Resource Router

- Project tree and schemas: `references/output-contract.md`
- Video modes and rhythm: `references/video-modes.md`
- Scene-level director grammars: `references/scene-director-patterns.md`
- Storyboard and video prompt patterns: `references/storyboard-and-video-prompts.md`
- Seedance 2.0 practical rules: `references/seedance2-practical-playbook.md`
- Platform/model constraints: `references/platform-and-model-profiles.md`
- Audio, TTS, captions, and copy: `references/audio-and-copy.md`
- Visual preset selection: `references/visual-style-presets.md` and `references/visual_style_presets.json`
- HyperFrames and reusable code animation: `references/ai-animation.md`
- Final checks: `references/quality-check.md`
- Director templates: `style_templates/<template_id>/`
- Registered animation assets: `ai_animation/registry.json`
