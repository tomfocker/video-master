---
name: video-master
description: Use when a user wants to turn a video idea, campaign brief, existing assets, story, product concept, or rough requirement into a video pre-production package with intake routing, video-mode confirmation, creative strategy, script/copy/audio extraction, shot list/storyboard, native image-generated storyboard frames, and Chinese or model-specific video generation prompts. Triggers include video-master, 视频脚本, 分镜, storyboard, 短视频, 广告片, TVC, 产品宣传片, AI视频提示词, or video prompt.
---

# Video Master

Video Master turns a user's requirement or source assets into an AI video production package. It behaves like a director's pre-production workflow: identify what the user already has, confirm the video mode, lock production constraints, design rhythm, then create scripts, storyboard frames, audio copy, and copy-ready prompts.

## Dependencies

The skill can run with no extra Python packages, but the repository supports recommended dependencies for richer local tooling. When the user allows setup before production work, install dependencies from the project root:

```bash
python3 -m pip install -r requirements.txt
```

Recommended dependencies enable:

- PNG storyboard contact sheets with Pillow.
- Production workbook export with openpyxl.
- Packaged MP4 storyboard animatic previews with imageio/ffmpeg and numpy. The default `draft` profile uses 12fps and follows the project's aspect ratio, with optional `smooth` and `off` profiles.
- Optional TTS voiceover generation with edge-tts.
- Stronger JSON/subtitle validation with pydantic and pysubs2.

## Global Rules

- Match the user's language unless they explicitly request another language.
- Default output location: create `video_projects/<project_slug>_<YYYYMMDD_HHMM>/` under the current workspace unless the user names a destination.
- Follow the serial pipeline. Do not write later-phase deliverables before the current phase's gate is satisfied.
- Treat `brief/spec_lock.md` as the execution contract. Re-read it before writing each shot prompt, generating each storyboard frame, or assembling final deliverables.
- Use native image generation for storyboard frames when the user asks for images, 分镜图, storyboard frames, keyframes, or visual boards. Do not substitute SVG boxes or text-only placeholders.
- Treat fixed characters as a continuity lock before storyboard generation. When a project includes recurring people, hosts, founders, interviewees, actors, or mascots, create/confirm character design anchors first and reference them from storyboard image prompts and video prompts.
- Treat title packaging as an optional sidecar branch only. It must never change the normal storyboard, script, audio, or video-prompt generation flow.
- When the user asks for commercial title cards, lower thirds, number animations, alpha overlays, or packaging text, create separate title-packaging deliverables; do not add packaging notes, title-packaging file paths, or alpha-MOV instructions to copy-ready video prompts.
- During the Production Lock, explicitly ask whether the user needs title-packaging images: main title, chapter/section cards, lower thirds/name tags, key data/counter callouts, CTA/end cards, or none. Default to `title_packaging_enabled: false` only when the user does not need packaging or asks to keep the package lean.
- For title packaging, use native image generation for designed packaging images and chroma-key/transparent PNG look development when available. Use `scripts/render_title_packaging.py` for exact text, verified transparent PNGs, and optional ProRes 4444 alpha MOV overlays.
- Default title packaging output is static transparent PNG. Do not generate MOV just for a simple fade, scale, or position shift; create MOV only when the user explicitly asks for animated overlay delivery and provides a meaningful animation need.
- If a dedicated `imagegen` skill/tool is available, follow it for image generation and project-bound save-path handling.
- If native image generation is unavailable, create the complete image prompt set, mark each affected frame `Needs-Generation`, and continue with the remaining package.
- Do not claim a storyboard image file exists until its path has been verified.
- Use Seedance 2.0 as the default target video model/profile for video generation prompts. Record `target_model: seedance-2.0` and `prompt_dialect: seedance-2.0` unless the user explicitly names another video model.
- Prefer Chinese final prompts when the target workflow is Chinese or domestic video models are named. Keep optional English camera/style tags only when useful.
- Confirm or explicitly assume `copy_language`, `voiceover_language`, `caption_language`, `localized_caption_languages`, and `subtitle_rendering_policy` before writing script, TTS, captions, or final video prompts. Prompt language controls the model prompt; copy language controls the spoken/readable words.
- Default `subtitle_rendering_policy` to `post-production-only` and `burned_subtitles_allowed` to `false` for generated video clips. Captions may exist as `audio/captions.srt` for preview/post-production, but final video prompts must not ask the video model to render subtitles unless the user explicitly approves generated on-screen text.
- For domestic Chinese workflows, include a Chinese SRT deliverable even when the voiceover is English. If the VO is English, package both `英文字幕.srt` and `中文字幕.srt` in `最终交付/03_口播与字幕/`.
- If narration is external voiceover rather than on-camera speech, do not include the exact VO lines in copy-ready video prompts. Keep spoken copy in `audio/voiceover_script.md`, `audio/tts_lines.json`, and SRT files; video prompts should only say the VO is added in post.
- Copy-ready video prompts must explicitly say the video model should not generate background music for each clip. Music direction belongs to post-production or whole-film audio planning, because per-clip generated music creates hard seams during assembly.
- Every copy-ready video prompt must include per-shot SFX/sound-design cues. SFX cues are part of the clip brief; background music is not.
- Do not use a `Negative prompt` / `负面提示词` field in final video prompts. Prefer positive generation requirements and clear policy fields such as `画面文字策略`.
- Avoid unlicensed celebrity likenesses, copyrighted characters, trademark-heavy style imitation, or deceptive real-person depictions unless the user provides rights and the request is allowed. Convert risky requests into original characters, original brands, or generic style language.
- If the user provides reference images or videos for style, treat them as `reference_style` assets: extract transferable color, lighting, camera, pacing, framing, and packaging rules, but do not copy subjects, plot, branding, protected characters, creator identity, or a living artist/director's protected style. Use the distilled rules and safe reference frames to guide native image generation and final video prompts.
- When a user wants a reusable style approach, offer three project style modes: `original`, `use_style_template`, or `create_style_template_from_reference`.
- Treat `visual_style_preset_id` as a lightweight look card for storyboard frames and video prompts. It is separate from `template_id`: presets lock image look, color, light, texture, and camera feel; templates lock a full director method including rhythm, editing, sound, and prompt structure.
- Official style templates live in `style_templates/<template_id>/` and are applied as a complete director archive through `template_id`; do not ask for or write a template strength.
- When a style template is selected, user ideas override template defaults: explicit user ideas, supplied assets, brand/copy constraints, and project-specific creative directions come first. Capture these as `template_user_overrides` and make the output follow the user first.
- Do not maintain `light` / `medium` / `high` variants for official templates. If the user wants a variation, treat it as a project-specific override rather than a new template strength.
- Do not use a draft style template for a final project unless the user explicitly opts in with `allow_draft_template: true`.
- A style template transfers creative rules such as rhythm, palette, camera language, sound policy, and prompt structure; it never authorizes copying reference subjects, exact shots, dialogue, branding, subtitles, watermarks, or creator identity.

## Pipeline

### Step 0: Workflow Entry Mode

Gate: the user starts a new video-master project or opens an existing project for major changes.

Offer two entry modes:

- `autopilot`: full delegation. The user gives the brief and assets, then Codex makes reasonable assumptions, logs them, and only asks when blocked by missing rights, unsafe claims, missing core assets, or irreversible creative choices.
- `guided`: collaborative director mode. Codex confirms key information, offers visual/style/rhythm options, brainstorms with the user, then implements after confirmation.

Record the decision in `brief/spec_lock.md`:

- `workflow_mode: autopilot | guided`
- `confirmation_policy: ask_only_blockers | confirm_each_phase`
- `assumption_policy: auto_fill_with_log | require_user_confirmation`

When the user says to proceed quickly, default to `autopilot`. When the user wants brainstorming, comparison, or creative control, default to `guided`.

### Step 1: Input Readiness Check

Gate: the user has provided a video idea, source material, or rough requirement.

Classify the input mode before creative work:

- `idea-only`: the user has only a concept; Codex may propose product, story, scene, copy, and visual assumptions.
- `asset-assisted`: the user has partial assets such as product photos, logo, copy, selling points, reference videos, or target platform.
- `material-locked`: the user has approved assets/copy/brand rules; Codex must structure and adapt them without inventing unsupported claims or changing key wording.

Before video-mode confirmation, classify the style route:

- `original`: create a new style from the project brief.
- `use_style_template`: use an official template from `style_templates/`.
- `create_style_template_from_reference`: analyze reference assets and produce a draft template package for user confirmation.

If using a template, capture `template_id`, whether draft templates are allowed, and `template_user_overrides` from any user-supplied ideas or constraints.

Before storyboard work, classify the visual style preset route:

- `preset`: use one visual style card from `references/visual_style_presets.json`.
- `custom`: user supplies a custom look in natural language.
- `reference-derived`: derive the look from user-provided reference assets and record safe transfer rules.

If the mode is unclear, ask one concise question. Otherwise proceed with explicit assumptions.

Write:

- `strategy/input_readiness.md`

Capture available materials, missing materials, what may be invented, what must be preserved, and any required source files in `sources/`.

When the user uploads reference images or videos, label each asset's role explicitly:

- `reference_style`: use only for transferable style rules such as palette, contrast, lighting, pacing, camera language, framing, transition rhythm, and visual packaging. Captions/subtitles may be analyzed as packaging observations, but final image/video prompts must not ask models to reproduce burned subtitles or subtitle styling unless `subtitle_rendering_policy` and `burned_subtitles_allowed` explicitly allow generated text.
- `reference_subject`: use for permitted product/person/object continuity when the user owns or provides the asset.
- `do-not-copy`: note any protected characters, celebrity likenesses, brand marks, plots, slogans, or recognizable creator-specific style that must not be replicated.

### Step 2: Video Mode Confirmation

Gate: Step 1 complete.

Confirm the video mode before writing the script. Use `references/video-modes.md`.

Common modes:

- `fast-paced-tvc`
- `product-promo-short`
- `narrative-short`
- `animation`
- `tutorial-explainer`
- `brand-film`
- `ecommerce-conversion-short`

Present the recommended mode and the impact on structure, rhythm, audio, storyboard coverage, and deliverables. Wait for confirmation unless the user already specified the mode or explicitly said to proceed.

Write:

- `strategy/video_mode.md`

### Step 3: Production Lock

Gate: input mode and video mode are known.

Create the project folders:

```text
video_projects/<project_slug>_<YYYYMMDD_HHMM>/
  sources/
  brief/
  strategy/
  script/
  storyboard/frames/
  prompts/
  audio/
  characters/
    character_bible.md
    character_manifest.json
    reference_images/
  packaging/
    title_packaging_plan.json
    title_packaging_prompts.md
    title_cards/
    alpha_mov/
  references/
  references/reference_keyframes/
  最终交付/
    01_分镜图/
    02_提示词/
    03_口播与字幕/
    04_分镜总览/
    05_预览视频/
    06_制作总表/
    07_title_packaging/
  qa/metadata/
```

Present the Production Lock as a bundled recommendation and wait for confirmation unless the user has supplied the decisions or explicitly allowed assumptions:

1. Workflow mode: `autopilot` or `guided`, with confirmation and assumption policy
2. Input mode and asset authority
3. Video mode
4. Objective and CTA
5. Audience and platform
6. Aspect ratio and target duration
7. Prompt language and target video model/profile; default target video model: `seedance-2.0`, unless the user explicitly names another video model.
8. Copy/VO language, caption language, and subtitle rendering policy (`post-production-only` by default)
9. Narrative style, visual style, and pacing style
10. Visual style preset: choose one preset from `references/visual_style_presets.json`, custom, or reference-derived. Present 2-4 relevant cards with a recommended default instead of an unstructured open-ended style question.
11. Character/product/brand continuity rules, including whether fixed people need a character-design lock before storyboard generation
12. Claims/compliance boundaries
13. Storyboard image coverage: every shot, key shots, or selected scenes
14. Reference style usage: mimic color grading, camera language, edit rhythm, typography/packaging, or only general mood
15. Style route: `original`, `use_style_template`, or `create_style_template_from_reference`
16. Style template fields when applicable: `template_id`, `allow_draft_template`, and `template_user_overrides`
17. Template application summary: what is inherited from the template, what is overridden by the user's ideas, and what must not be copied
18. Optional title packaging: ask whether to generate `main_title`, `chapter_card`, `lower_third`/`name_tag`, `data_callout`/`counter`, `cta_card`/`end_card`, or none. Capture exact copy, style references, PNG-only vs real animated overlay need, and `title_packaging_enabled`. This is a sidecar branch and does not modify video prompts.

Write:

- `brief/creative_brief.md`
- `brief/spec_lock.md`

Use `references/output-contract.md` for the required sections.

### Step 3.5: Reference Style Analysis

Gate: reference images or videos exist and the user wants them used for style.

Write:

- `references/style_analysis.md`
- `references/color_style.md`
- `references/editing_style.md`
- `references/reference_style_manifest.md`
- `references/reference_keyframes/` when frames are extracted or selected

Measure objective traits with local tooling when possible: duration, aspect ratio, FPS, scene count, average shot length, keyframes, color palette, brightness, contrast, saturation, and motion density. Then synthesize them into creative rules that can be reused without copying the source content.

The final style rules must answer:

- What should be mimicked: palette, contrast, lighting, lens language, shot duration pattern, camera movement, transitions, and packaging. Subtitle behavior may be recorded as an analysis-only/post-production observation, not as a generation instruction unless the subtitle policy explicitly allows generated text.
- What must not be copied: people, brand marks, exact scenes, plot, dialogue, slogans, copyrighted characters, or protected creator style.
- How the rules affect storyboard image prompts and video prompts.

### Step 3.6: Visual Style Preset Lock

Gate: Production Lock is confirmed, and reference-style analysis is complete when reference assets are used.

Use `references/visual-style-presets.md` and `references/visual_style_presets.json`. This step must be complete before `prompts/storyboard_image_prompts.md` is written.

Ask or confirm one of:

- One preset card, such as `imax_70mm_realism`, `photoreal_commercial`, `eastern_fantasy_3d`, `hyperreal_3d_render`, `graphic_2d_editorial`, `soft_storybook_2d`, `anime_cinematic_light`, `noir_gothic`, or `future_tech_clean`.
- `custom`, when the user describes a look that does not fit a preset.
- `reference-derived`, when reference assets define the look.

When recommending, present 2-4 relevant cards, name the recommended one, and explain the tradeoff in one sentence. Record the selected preset in `brief/spec_lock.md` under `visual_style`:

- `visual_style_lock`
- `visual_style_preset_id`
- `visual_style_preset_name`
- `medium`
- `realism_level`
- `art_direction`
- `color_palette`
- `lighting`
- `texture`
- `camera_language`
- `storyboard_prompt_rules`
- `video_prompt_rules`
- `visual_style_overrides`

If a full `template_id` is also selected, the template's prompt rules remain the larger director method, while the visual style preset supplies the exact look card unless the user overrides it. Do not ask for exact living-artist or studio imitation; convert those requests into descriptive traits.

### Step 3.7: Character Design Lock

Gate: Production Lock and Visual Style Preset Lock are complete, and the project has recurring characters or the user requests fixed人物/主持人/创始人/采访对象/演员/虚拟角色 continuity.

Ask or confirm whether the project needs fixed-character continuity. If not, record `character_lock_enabled: false` and continue. If yes, lock the visual identity before writing storyboard image prompts:

- Define stable character IDs such as `host_a`, `founder_b`, or `guest_c`.
- Record each character's role, age range, face/hairstyle/body-shape descriptors, wardrobe rules, temperament, forbidden changes, and allowed variations.
- Generate or collect reference images when available: face/front, half-body or full-body, and any required wardrobe or expression references.
- Store the character bible and manifest in `characters/`.
- Record prompt rules that require downstream storyboard and video prompts to reference the locked character IDs instead of reinventing the person.

Write when enabled:

- `characters/character_bible.md`
- `characters/character_manifest.json`
- `characters/reference_images/`

Record the selected policy in `brief/spec_lock.md` under `character_design`:

- `character_lock_enabled`
- `character_lock_status`
- `fixed_characters`
- `character_reference_dir`
- `character_prompt_rules`

### Step 4: Creative Strategy And Rhythm Map

Gate: `creative_brief.md` and `spec_lock.md` exist, and character design is locked or explicitly skipped.

Write:

- `strategy/creative_strategy.md`
- `strategy/rhythm_map.md`

The rhythm map must allocate non-uniform shot durations unless the confirmed mode genuinely calls for uniform timing. For advertising modes, design hook, product memory, proof, and CTA beats deliberately. Do not default to equal shot lengths.

Act like a creative director, not a spreadsheet. For high-motion subjects such as racing, sport, chase sequences, launch films, and fast-paced TVC, design at least one rapid-cut cluster of very short shots before or after longer emotional shots. Use shot durations such as `0.6s`, `0.8s`, `1.2s`, and `2s` when the moment calls for velocity, then contrast them with longer breath shots. Mark camera energy explicitly: stable, handheld, vehicle-mounted vibration, impact shake, whip pan, hard push-in, POV, pass-by, or locked-off.

Use `references/video-modes.md`, `references/platform-and-model-profiles.md`, and any `references/style_analysis.md`.

If `template_id` is present, read `style_templates/<template_id>/template.md`, `director_notes.md`, `rhythm_rules.json`, `editing_craft.md`, `shot_motifs.json`, and `prompt_rules.md` before writing the rhythm map.

When a style template is selected, `strategy/rhythm_map.md` must name the template and explain how the complete template method is adapted to the current subject, duration, and `template_user_overrides`.

### Step 5: Script, Copy, And Audio Extraction

Gate: creative strategy and rhythm map exist.

Write:

- `script/script.md`
- `audio/voiceover_script.md`
- `audio/tts_lines.json`
- `audio/captions.srt`
- `audio/captions_en.srt` and/or `audio/captions_zh.srt` when multilingual subtitle deliverables are needed
- `audio/music_sfx_cue_sheet.md`
- `audio/audio_generation_prompt.md`

Use `references/audio-and-copy.md`. Keep audio copy centralized so TTS, captions, and final video prompts stay consistent.
If `template_id` is present, read `style_templates/<template_id>/template.md`, `director_notes.md`, and `prompt_rules.md` before writing script, copy, and audio files so rhythm, sound policy, and copy posture remain aligned with the selected style template while preserving user-provided copy direction.
Confirm whether the spoken copy is Chinese, English, bilingual, or user-supplied before writing `audio/voiceover_script.md`. Treat `audio/captions.srt` as a post-production subtitle asset unless `burned_subtitles_allowed` is explicitly true. For Chinese-facing delivery, create Chinese localized captions even if the spoken VO is English, and keep the VO-language transcript as a separate SRT.
In `audio/music_sfx_cue_sheet.md`, map an SFX cue to every shot. Keep background music as a whole-film post-production direction unless the user explicitly asks to generate or mix music later.

### Step 6: Shot List And Storyboard Plan

Gate: script and audio files exist.

Write:

- `storyboard/shot_list.md`
- `storyboard/shot_list.json`

Use a compact overview table plus per-shot detail blocks. Avoid a single very wide Markdown table for all fields. Every shot must include timing, beat, visual action, framing, camera, movement, lighting, audio/copy references, continuity notes, image prompt seed, and video prompt seed.

If `template_id` is present, read `style_templates/<template_id>/template.md`, `director_notes.md`, `rhythm_rules.json`, `shot_motifs.json`, `editing_craft.md`, `example_shot_list.md`, and `prompt_rules.md` before writing the shot list and storyboard plan. Apply the template as a complete director method while redesigning the subject, plot, characters, product, and brand details around the user's own ideas.

### Step 7: Storyboard Image Prompts And Native Images

Gate: `shot_list.md` exists and storyboard coverage is known.

Read `brief/spec_lock.md`, `references/storyboard-and-video-prompts.md`, `references/visual-style-presets.md`, `characters/character_bible.md` when present, and any `references/style_analysis.md`.
If `template_id` is present, also read `style_templates/<template_id>/prompt_rules.md` and carry the template's safe prompt rules as defaults. User ideas and approved assets override template defaults when they conflict.

Write `prompts/storyboard_image_prompts.md` before generating images. Generate storyboard frames with native image generation:

- Every storyboard image prompt must carry the locked visual style preset fields from `brief/spec_lock.md`: `visual_style_preset_id`, medium, realism level, art direction, color palette, lighting, texture, camera language, and storyboard prompt rules.
- If `character_lock_enabled` is true, every storyboard image prompt involving a fixed character must reference the stable character ID and the locked character bible. Do not vary face, age, hairstyle, body type, or signature wardrobe unless `character_bible.md` allows it.
- If shot count is manageable and the user requested detailed storyboard images, generate one frame per shot.
- If shot count is high, generate key frames unless the user explicitly asks for every shot.
- If `reference_style` assets exist, inject the distilled style rules and safe reference keyframe paths into every storyboard image prompt. Use native image generation with reference images when the available tool supports it; otherwise include the keyframe paths and style rules in the prompt text. Never ask the model to reproduce the exact source video or image.
- For recurring characters or products, create or identify visual anchors in `references/` when possible. If reference-image conditioning is unavailable, tighten every prompt with identical character/product descriptors and visually check for drift.
- After generating key frames, inspect continuity before marking the manifest complete. Regenerate any frame whose character, product, palette, or composition clearly conflicts with `spec_lock.md`.
- Copy project-bound images into `storyboard/frames/` and final selected frames into `最终交付/01_分镜图/`.

Write:

- `storyboard/storyboard_manifest.md`

### Step 8: Video Generation Prompts

Gate: `shot_list.md`, storyboard prompts, image statuses, and audio files are ready.

Write:

- `prompts/video_prompts.md`
- `最终交付/02_提示词/视频生成提示词.md`
- `最终交付/02_提示词/图片生成提示词.md`

If no other target video model is specified, write the final prompts for Seedance 2.0. If the target workflow is Chinese, Seedance 2.0, or another domestic Chinese video model, final copy-ready prompts must be Chinese-first. Keep `prompts/video_prompts.md` detailed for review, and make `最终交付/02_提示词/视频生成提示词.md` easy to copy into a video model.

Use `references/storyboard-and-video-prompts.md`, `references/platform-and-model-profiles.md`, and any `references/style_analysis.md`. If `reference_style` assets exist, final video prompts must carry the same safe style rules used for native image generation so generated video matches the reference look and editing language without copying protected content.
When a style template is selected, storyboard image prompts and video prompts must carry the template's safe prompt rules as a whole, adapted around `template_user_overrides` and the current subject.
For Seedance 2.0, each copy-ready shot prompt must include a `目标模型：Seedance 2.0` line and a `动态时间切片` section. Split the shot duration into time-coded segments such as `(00-1.5s)` and `(1.5-3.0s)`. Each segment should combine camera movement, changing light/environment, subject action, and micro-expression or material motion where relevant. The block must also keep subject stability constraints such as clear face, stable identity, normal anatomy, consistent wardrobe/product, and smooth continuous motion.
Separate external audio from generated visuals. Use fields such as `Voiceover/audio` or `声音/口播` for post-production narration, and `On-screen text policy` or `画面文字策略` for visual text. Do not use mixed labels such as `声音/字幕`; they can cause video models to burn VO lines into the picture. When `subtitle_rendering_policy` is `post-production-only`, every copy-ready prompt should say the model-generated picture should not include subtitles, captions, dialogue text, lyrics, or burned-in text.

For external voiceover, never paste the actual VO sentence into the video prompt. Write `声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。` and keep the line itself in the audio/SRT files. Each shot block should also include `背景音乐：不要生成背景音乐；整片音乐后期统一处理。` and an `SFX音效` line. Do not include a `负面提示词` section in final prompts.

### Step 8.5: Optional Title Packaging Sidecar

Gate: the user explicitly asks for title packaging, commercial title cards, lower thirds, number animations, alpha overlays, or packaging text.

This branch runs beside the video prompts. It must not rewrite `prompts/video_prompts.md`, must not edit `最终交付/02_提示词/视频生成提示词.md`, and must not insert title-packaging instructions into any copy-ready video prompt.

In the formal Production Lock, ask the user whether they need any of these packaging images:

- `main_title`: main title or campaign title.
- `chapter_card`: chapter, section, location, or day title.
- `lower_third` / `name_tag`: person name, role, location label, interview ID.
- `data_callout` / `counter`: key number, ranking, percentage, year, distance, price, milestone.
- `cta_card` / `end_card`: ending slogan, follow/subscribe, campaign CTA.

If the user is unsure, recommend PNG-only packaging first. MOV is optional and should be used only for meaningful animation such as stroke reveal, route drawing, counter ticking, mask wipe, glow sweep, or designed motion; do not render MOV for a simple static image with fade/position offset.

Write:

- `packaging/title_packaging_plan.json`
- `packaging/title_packaging_prompts.md`
- `packaging/title_cards/`
- `packaging/alpha_mov/`
- `qa/metadata/title_packaging_manifest.json`
- `最终交付/07_title_packaging/`

Use reference packaging assets as `reference_style` only: extract typography mood, composition, material, lighting, spacing, commercial polish, motion intent, and layout grammar. Do not copy the original title names, exact layout, logos, brand marks, watermarks, or recognizable source artwork.

When native image generation is available, use it to create designed packaging looks. Without API-native transparency, generate the packaging on a pure chroma-key background, remove the key locally, and verify the transparent PNG. For exact Chinese/English text, counters, lower thirds, and editor-ready static overlays, render deterministic PNG assets with:

```bash
python3 ${SKILL_DIR}/scripts/render_title_packaging.py <project_path>
```

The default output is transparent PNG only. Use `--alpha-mov` only when the user explicitly requests animated alpha overlay delivery and the motion is more than a trivial fade or offset. In `packaging/title_packaging_plan.json`, set `motion_template` to a production template such as `brush_reveal`, `mask_wipe`, `glow_sweep`, `route_light_trail`, `odometer`, or `marker_annotation`. For designed main titles, put the native-image-generation result through chroma-key cleanup first, then pass the transparent PNG as `design_asset`; the script handles exact alpha MOV motion and keeps the asset outside video prompts. The MOV output is a ProRes 4444 alpha overlay meant for editing software, not a video-generation prompt input.

### Step 9: Deliverables Package

Gate: script, shot list, audio files, storyboard manifest, generated frames, and video prompts exist.

Write:

- `最终交付/00_使用说明.md`
- `最终交付/03_口播与字幕/口播稿.md`
- `最终交付/03_口播与字幕/中文字幕.srt` and/or `最终交付/03_口播与字幕/英文字幕.srt`
- Any model/platform-specific final files requested by the user
- Optional title packaging files in `最终交付/07_title_packaging/` only when `title_packaging_enabled` is true or the user requested the sidecar branch

If the user wants a voiced preview and dependencies/network are available, generate a TTS track from the centralized copy:

```bash
python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project_path>
```

If the user already has narration, place it in `最终交付/03_口播与字幕/` or pass it to the preview tool with `--voiceover-audio`.

Generate the storyboard overview:

```bash
python3 ${SKILL_DIR}/scripts/make_storyboard_overview.py <project_path>
```

Generate the production workbook:

```bash
python3 ${SKILL_DIR}/scripts/export_production_workbook.py <project_path>
```

Generate the storyboard animatic preview:

```bash
python3 ${SKILL_DIR}/scripts/make_animatic.py <project_path>
```

The default preview profile is `draft`: 12fps and an output size inferred from `brief/spec_lock.md` `aspect_ratio` such as `1280x720` for `16:9` or `720x1280` for `9:16`. Use `--preview-profile smooth` when the user prioritizes playback polish, or `--preview-profile off` when the user only wants the core storyboard and prompt package. The default motion style is `none` so storyboard frames stay stable; use `--motion-style center-zoom` or `--motion-style pan-zoom` only when movement is intentionally desired. The animatic preview should include an opening card, ending card, shot overlays, burned-in captions when available, and any provided or generated voiceover. Music and sound-effect mixing is intentionally not part of this step yet; keep those as planning cues for now.

Generate the local WebUI state snapshot:

```bash
python3 ${SKILL_DIR}/scripts/project_state.py <project_path> --write
```

The first WebUI is a read-only control surface for project inspection. It displays the entry mode, workflow nodes, storyboard frames, prompt snippets, title-packaging status, and deliverables from canonical project files. To inspect a local project visually, run:

```bash
python3 ${SKILL_DIR}/scripts/serve_webui.py --host 127.0.0.1 --port 8765
```

Future UI edit requests should be recorded as workflow events before Codex reconciles them into canonical files. Do not treat `qa/metadata/project_state.json` as the source of truth.

The `最终交付/` folder is the user-facing package. Work-in-progress files stay in `brief/`, `strategy/`, `script/`, `storyboard/`, `prompts/`, and `audio/`. Internal machine records such as manifests and fallback HTML belong in `qa/metadata/`, not the user-facing package.

### Step 10: QA

Gate: all deliverables exist.

Run the checklist in `references/quality-check.md`. If project files exist locally, run:

```bash
python3 ${SKILL_DIR}/scripts/validate_video_project.py <project_path>
```

Fix issues before finishing. Final response should list the output folder, the user-facing deliverables folder, generated image count/status, validation result, and any remaining manual actions.

## Reference Files

- `references/output-contract.md`: v2 project structure and file schemas.
- `references/video-modes.md`: mode routing and rhythm rules.
- `references/platform-and-model-profiles.md`: platform/model prompt language and constraints.
- `references/audio-and-copy.md`: VO, TTS, captions, SFX, and copy extraction.
- `references/visual-style-presets.md` and `references/visual_style_presets.json`: lightweight visual look cards for storyboard image prompts and video prompts.
- `references/storyboard-and-video-prompts.md`: image and video prompt patterns.
- `references/quality-check.md`: final QA checklist and validator use.
- `scripts/project_state.py` and `scripts/serve_webui.py`: local read-only project state and WebUI helpers.
