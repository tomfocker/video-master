# Video Master Output Contract

Use this reference when creating project files for `video-master`.

## Project Structure

```text
video_projects/<project_slug>_<YYYYMMDD_HHMM>/
  sources/
  brief/
    creative_brief.md
    spec_lock.md
  strategy/
    input_readiness.md
    video_mode.md
    creative_strategy.md
    rhythm_map.md
  script/
    script.md
  storyboard/
    shot_list.md
    shot_list.json
    storyboard_manifest.md
    frames/
  prompts/
    storyboard_image_prompts.md
    video_prompts.md
  audio/
    voiceover_script.md
    tts_lines.json
    captions.srt
    captions_en.srt
    captions_zh.srt
    music_sfx_cue_sheet.md
    audio_generation_prompt.md
  packaging/
    title_packaging_plan.json
    title_packaging_prompts.md
    title_cards/
    alpha_mov/
  references/
    visual_style_presets.json
    style_analysis.md
    color_style.md
    editing_style.md
    reference_style_manifest.md
    reference_keyframes/
  最终交付/
    00_使用说明.md
    01_分镜图/
      S01.png
    02_提示词/
      视频生成提示词.md
      图片生成提示词.md
    03_口播与字幕/
      口播稿.md
      口播文本.txt
      中文字幕.srt
      英文字幕.srt
      口播音频.mp3
    04_分镜总览/
      分镜总览图.png
    05_预览视频/
      分镜预览.mp4
    06_制作总表/
      制作总表.xlsx
    07_title_packaging/
      main_title.png
      main_title.mov
  qa/
    metadata/
      storyboard_overview.html
      preview_manifest.json
      tts_manifest.json
      title_packaging_manifest.json
```

## input_readiness.md

```markdown
# Input Readiness

## Input Mode
- Mode: idea-only | asset-assisted | material-locked
- Reason:

## Provided Materials
| Type | Path / Source | Authority | Notes |
| ---- | ------------- | --------- | ----- |

## Missing Materials
- Product image:
- Logo:
- Brand colors:
- Approved copy:
- Reference videos:

## Invention Rules
- Codex may invent:
- Codex must preserve:
- Codex must ask before changing:
```

## video_mode.md

```markdown
# Video Mode

- Selected mode:
- Why this mode:
- Impact on structure:
- Impact on rhythm:
- Impact on audio:
- Impact on storyboard coverage:
- Impact on deliverables:
```

## creative_brief.md

```markdown
# Creative Brief

## Project
- Name:
- Source request:
- Goal:
- Call to action:
- Audience:
- Platform:
- Aspect ratio:
- Target duration:
- Delivery language:
- Copy language:
- Voiceover language:
- Caption language:
- Subtitle rendering policy:

## Input And Production Mode
- Input mode:
- Video mode:
- Target model/profile:
- Prompt language:

## Creative Direction
- Genre:
- Tone:
- Narrative structure:
- Pacing:
- Visual style:
- Color and lighting:
- Music and sound:

## Continuity
- Characters:
- Product/brand:
- Locations:
- Props:
- Must include:
- Must avoid:

## Claims And Safety
- Allowed claims:
- Forbidden claims:
- Rights/brand notes:

## Assumptions
- ...
```

## spec_lock.md

Keep this short and data-oriented. Downstream phases re-read it before writing each shot prompt or generating each storyboard frame.

```markdown
# Spec Lock

## format
- aspect_ratio:
- target_duration_seconds:
- target_platform:
- delivery_language:
- prompt_language:
- prompt_dialect:
- target_model:

## production_mode
- input_mode:
- video_mode:
- storyboard_coverage:
- deliverables_profile:

## story
- objective:
- cta:
- structure:
- tone:
- hook_rule:

## rhythm
- pacing_style:
- shot_count_target:
- duration_distribution_rule:
- hook_seconds:
- cta_seconds:

## visual_style
- visual_style_lock: confirmed | assumed | reference-derived | custom
- visual_style_preset_id: imax_70mm_realism | photoreal_commercial | eastern_fantasy_3d | hyperreal_3d_render | graphic_2d_editorial | soft_storybook_2d | anime_cinematic_light | noir_gothic | future_tech_clean | custom
- visual_style_preset_name:
- medium:
- realism_level:
- art_direction:
- color_palette:
- lighting:
- texture:
- camera_language:
- storyboard_prompt_rules:
- video_prompt_rules:
- visual_style_overrides:

## reference_style
- source_assets:
- authorized_usage:
- mimic:
- do_not_copy:
- keyframe_paths:

## style_route
- style_route: original | use_style_template | create_style_template_from_reference
- template_id: <template_id when style_route is use_style_template>
- allow_draft_template: false
- template_user_overrides: <explicit user ideas, supplied assets, brand/copy constraints, or creative directions that override template defaults; leave empty when none>
- template_application_summary: <conditional summary of what is inherited from the template, what user ideas override, and what is not copied when a style template is selected>

## continuity
- character_bible:
- product_bible:
- location_bible:
- wardrobe:
- props:
- brand_rules:
- reference_assets:

## audio
- copy_language:
- voiceover_language:
- caption_language:
- localized_caption_languages:
- subtitle_rendering_policy: post-production-only | model-generated-text-allowed
- burned_subtitles_allowed: false
- onscreen_text_policy:
- voice_style:
- music_style:
- sfx_style:
- caption_style:

## prompt_safety
- allowed:
- avoid:
- sensitive_flags:

## title_packaging
- title_packaging_enabled: false
- title_packaging_assets: main_title | chapter_card | lower_third | name_tag | data_callout | counter | cta_card | end_card
- title_packaging_reference_assets:
- title_packaging_alpha_mov_required: false
- title_packaging_motion_need: none | stroke_reveal | route_draw | counter_tick | mask_wipe | glow_sweep | custom
```

## Visual Style Preset Lock

Before writing `prompts/storyboard_image_prompts.md`, lock one visual style preset, a custom look, or a reference-derived look. Use `references/visual-style-presets.md` and `references/visual_style_presets.json`.

The preset lock belongs in `brief/spec_lock.md` under `visual_style`. It is lightweight: it controls storyboard image and video-prompt look fields, but it does not replace `style_templates/<template_id>/` when a full director template is selected.

Example:

```markdown
## visual_style
- visual_style_lock: confirmed
- visual_style_preset_id: photoreal_commercial
- visual_style_preset_name: Photoreal Commercial
- medium: photoreal commercial photography and video
- realism_level: photoreal
- art_direction: clean, aspirational, polished, product-led
- color_palette: brand-friendly palette, clear product color, gentle contrast, controlled whites
- lighting: softbox, rim light, specular product highlights, clean shadow control
- texture: high-resolution product materials, skin, fabric, condensation, glass, metal, food texture
- camera_language: macro inserts, hero product angles, smooth slider moves, controlled depth of field
- storyboard_prompt_rules: Prioritize product readability, clean surfaces, and premium commercial lighting; use macro detail shots and hero compositions when the product is the memory anchor.
- video_prompt_rules: Describe smooth camera moves and product-safe continuity; keep product shape, color, material, label policy, and scale consistent.
- visual_style_overrides:
```

## Reference Style Files

When reference images or videos are provided for style, create these files before writing storyboard image prompts.

`references/reference_style_manifest.md`:

```markdown
# Reference Style Manifest

| Asset | Role | Source Path | User Authority | Allowed Usage | Do Not Copy |
| ----- | ---- | ----------- | -------------- | ------------- | ----------- |
| R01 | reference_style | sources/reference.mp4 | user-provided | color, rhythm, camera language | people, plot, brand marks |
```

`references/style_analysis.md`:

```markdown
# Style Analysis

## Objective Measurements
- Duration:
- Aspect ratio:
- FPS:
- Scene count:
- Average shot length:
- Color palette:
- Brightness / contrast / saturation:
- Motion density:

## Director Interpretation
- Overall mood:
- Visual grammar:
- Edit rhythm:
- Camera language:
- Packaging / subtitle behavior:

## Transfer Rules
- Apply:
- Avoid:
- Impact on storyboard image prompts:
- Impact on video prompts:
```

`references/color_style.md` should describe palette, contrast, saturation, black level, highlight behavior, grain/noise, and lighting direction.

`references/editing_style.md` should describe shot length distribution, cut density, transition type, motion density, subtitle/graphic placement, and pacing implications.

`references/reference_keyframes/` should contain extracted or selected safe keyframes used only as style references.

## creative_strategy.md

```markdown
# Creative Strategy

## Strategic Thesis

## Audience Insight

## Message Hierarchy
1. Hook:
2. Product proof:
3. Emotional or practical payoff:
4. CTA:

## Visual System

## Audio System

## Platform Notes
```

## rhythm_map.md

Use non-uniform timing unless the mode requires a fixed beat grid.

High-motion work must include director rhythm, not only beat math. For racing, sport, chase, action, or fast-paced launch films, include at least one rapid-cut cluster of three or more shots at 2 seconds or less, plus contrasting breath shots. Name camera energy in the map: stable, handheld, vehicle-mounted vibration, impact shake, whip pan, hard push-in, POV, pass-by, or locked-off.

```markdown
# Rhythm Map

| Beat | Time | Duration | Purpose | Energy | Notes |
| ---- | ---- | -------- | ------- | ------ | ----- |
| B01 | 00:00-00:03 | 3s | Hook | High | ... |

## Timing Rationale
- ...
```

## script.md

```markdown
# Script

## Title

## Logline

## Synopsis

## Beat Outline
| Beat | Time | Purpose | Content |
| ---- | ---- | ------- | ------- |

## Full Script
| Time | Visual | Voiceover/Dialog | On-screen Text | Audio/SFX |
| ---- | ------ | ---------------- | -------------- | --------- |
```

## Audio Files

`voiceover_script.md`:

```markdown
# Voiceover Script

## Full Read

## Lines
| ID | Time | Text | Tone | Notes |
```

`tts_lines.json`:

```json
[
  {
    "id": "VO01",
    "start": "00:00",
    "end": "00:03",
    "text": "",
    "tone": "",
    "speed": "",
    "pause_after_ms": 0
  }
]
```

`captions.srt`: valid SRT timing and caption text. This is the default subtitle track used by previews.

`captions_en.srt` and `captions_zh.srt`: optional source subtitle files when the project needs both VO-language transcript subtitles and localized Chinese subtitles.

Captions are a post-production subtitle asset by default. Unless `burned_subtitles_allowed` is `true`, final video prompts must treat subtitles as `post-production only` and must say the model-generated picture should not include subtitles in the video frames.
For domestic Chinese workflows, include a Chinese `.srt` even when the voiceover is English.

`music_sfx_cue_sheet.md`:

```markdown
# Music And SFX Cue Sheet

| Cue | Time | Type | Description | Purpose |
| --- | ---- | ---- | ----------- | ------- |
```

`audio_generation_prompt.md`: one complete prompt for whole-film music direction, per-shot SFX direction, voice direction, and any TTS voice constraints. Do not instruct segmented video generation models to create background music per clip.

## shot_list.md

Use a compact table plus detail blocks.

```markdown
# Shot List

| Shot | Time | Duration | Beat | Purpose |
| ---- | ---- | -------- | ---- | ------- |

## S01 - <shot name>
- Time range:
- Narrative purpose:
- Subject/action:
- Scene/location:
- Framing/composition:
- Lens/depth cue:
- Camera movement:
- Camera energy:
- Lighting/color:
- Character/product continuity:
- Audio/copy references:
- Transition:
- Storyboard image prompt seed:
- Video prompt seed:
```

## shot_list.json

Use valid JSON.

```json
[
  {
    "shot_id": "S01",
    "start": "00:00",
    "end": "00:03",
    "duration_seconds": 3,
    "beat": "",
    "purpose": "",
    "visual_action": "",
    "framing": "",
    "camera_angle": "",
    "lens_depth": "",
    "camera_movement": "",
    "camera_energy": "",
    "lighting": "",
    "location": "",
    "subjects": [],
    "props": [],
    "transition": "",
    "audio_refs": [],
    "onscreen_text_refs": [],
    "continuity_notes": "",
    "image_prompt_seed": "",
    "video_prompt_seed": ""
  }
]
```

## Deliverables

`最终交付/00_使用说明.md`:

```markdown
# Production Handoff

## Overview
- Project:
- Input mode:
- Video mode:
- Duration:
- Platform:
- Aspect ratio:
- Prompt language:
- Copy language:
- Voiceover language:
- Subtitle rendering policy:
- Burned subtitles allowed:
- Target model/profile:

## Final Files
- Storyboard frames:
- Copy-ready video prompts:
- Copy-ready image prompts:
- Voiceover:
- Captions:
- English captions:
- Chinese captions:
- Subtitle usage:

## Storyboard Status
| Shot | Status | Frame Path / Reason |
| ---- | ------ | ------------------- |

## Usage Notes
- ...
```

`最终交付/02_提示词/视频生成提示词.md` should contain only final prompts meant to be copied into the video generator. It must separate external voiceover/audio from visual text instructions. Use `声音/口播` or `Voiceover/audio` for narration that will be added outside the video model, and use `画面文字策略` or `On-screen text policy` for allowed/forbidden generated text. Do not use mixed fields such as `声音/字幕`. When narration is external VO, do not paste the actual VO sentence into the video prompt; keep exact copy in audio/SRT files. When `subtitle_rendering_policy` is `post-production-only`, each prompt should say the model-generated picture should not include subtitles, captions, dialogue text, lyrics, or burned-in text. Each shot block must include `背景音乐：不要生成背景音乐；整片音乐后期统一处理。` and `SFX音效：...`. Do not include a `Negative prompt` or `负面提示词` field in final video prompts.

`最终交付/02_提示词/图片生成提示词.md` should contain copy-ready image prompts.

`最终交付/01_分镜图/` should contain selected final frames, named by shot id.

`最终交付/03_口播与字幕/` should contain the final audio/caption files the user needs. For English VO with Chinese-facing delivery, include both `英文字幕.srt` and `中文字幕.srt`. Tool manifests belong in `qa/metadata/`, not here.

`最终交付/04_分镜总览/分镜总览图.png` is required. Generate it with:

```bash
python3 ${SKILL_DIR}/scripts/make_storyboard_overview.py <project_path>
```

The script also writes a dependency-free HTML fallback to `qa/metadata/storyboard_overview.html`; it is internal metadata, not part of the user-facing final package.

`最终交付/06_制作总表/制作总表.xlsx` is required when dependencies are installed. Generate it with:

```bash
python3 ${SKILL_DIR}/scripts/export_production_workbook.py <project_path>
```

`最终交付/05_预览视频/分镜预览.mp4` is required when dependencies are installed unless the preview profile is explicitly `off`. Generate it with:

```bash
python3 ${SKILL_DIR}/scripts/make_animatic.py <project_path>
```

The default profile is `draft`: 12fps and an output size inferred from `brief/spec_lock.md` `aspect_ratio` such as `1280x720` for `16:9` or `720x1280` for `9:16`. Use `--preview-profile smooth` for a higher-polish 15fps preview using the same project ratio, or `--preview-profile off` to skip MP4 generation while still writing a skip manifest. The default motion style is `none` so storyboard frames stay stable; use `--motion-style center-zoom` or `--motion-style pan-zoom` only when movement is intentional. The animatic is a packaged preview, not a dry still-frame stack. It should include title/end cards, shot overlays, burned captions when `audio/captions.srt` exists, and a voiceover track when one is provided or generated.

`qa/metadata/preview_manifest.json` is required when the animatic is generated or explicitly skipped:

```json
{
  "title": "",
  "preview_profile": "draft",
  "output": "",
  "fps": 12,
  "size": "1280x720",
  "shot_count": 0,
  "frame_count": 0,
  "duration_seconds": 0,
  "skipped": false,
  "title_card": true,
  "end_card": true,
  "shot_overlays": true,
  "burned_captions": true,
  "ken_burns_motion": false,
  "motion_style": "none",
  "voiceover_audio": false
}
```

When `--preview-profile off` is used, `output` is `false`, `skipped` is `true`, `motion_style` is `none`, and `分镜预览.mp4` is not required.

`最终交付/03_口播与字幕/口播音频.mp3` is optional but recommended for voiced previews. Generate it from `audio/tts_lines.json` when TTS is desired:

```bash
python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project_path>
```

This also writes `最终交付/03_口播与字幕/口播文本.txt` and `qa/metadata/tts_manifest.json`. Use `--dry-run` to prepare the text/manifest without calling a TTS service.

## Optional Title Packaging Sidecar

Title packaging is optional and separate from video prompt generation. Do not place title-packaging instructions, alpha-MOV paths, lower-third notes, or packaging file references inside `最终交付/02_提示词/视频生成提示词.md`.

`packaging/title_packaging_plan.json`:

```json
{
  "aspect_ratio": "16:9",
  "generate_alpha_mov": false,
  "duration_seconds": 2.0,
  "fps": 24,
  "items": [
    {
      "id": "main_title",
      "type": "title_card",
      "text": "项目标题",
      "subtitle": "可选副标题",
      "position": "center",
      "animation": "fade-up",
      "color": "#FFFFFFFF",
      "accent_color": "#D6B46AFF",
      "motion_template": "brush_reveal",
      "design_asset": "packaging/generated_design/main_title_alpha.png"
    }
  ]
}
```

Supported item types are `title_card`, `chapter_card`, `lower_third`, `name_tag`, `counter`, `data_callout`, `cta_card`, and `end_card`. For `counter` or `data_callout`, use `start_value`, `end_value`, `prefix`, `suffix`, and `decimals` when a number should be rendered.

When alpha MOV delivery is explicitly requested, use `motion_template` instead of relying on a trivial fade. Supported production templates are `brush_reveal`, `mask_wipe`, `glow_sweep`, `route_light_trail`, `route_draw`, `odometer`, `number_roll`, `marker_annotation`, and `annotation_arrow`. `design_asset` may point to a cleaned transparent PNG generated during native look development; the renderer uses it as the visual layer and applies the selected alpha-channel motion template.

The default packaging deliverable is a transparent PNG. Set `generate_alpha_mov: true` only when the user explicitly needs animated overlay delivery and the motion is meaningful, such as stroke reveal, route drawing, counter ticking, mask wipe, glow sweep, or a specified custom motion. Do not create MOV just for a static image with fade or position offset.

`packaging/title_packaging_prompts.md` contains style-exploration prompts for native image generation when needed. It is not copied into video prompts.

`qa/metadata/title_packaging_manifest.json`:

```json
{
  "title_packaging": true,
  "plan": "packaging/title_packaging_plan.json",
  "canvas": "1920x1080",
  "fps": 24,
  "alpha_mov_codec": "prores_ks/prores_4444",
  "items": [
    {
      "id": "main_title",
      "type": "title_card",
      "text": "项目标题",
      "transparent_png": "最终交付/07_title_packaging/main_title.png",
      "motion_template": null,
      "alpha_mov": null,
      "duration_seconds": 2.0
    }
  ]
}
```

Generate deterministic packaging assets with:

```bash
python3 ${SKILL_DIR}/scripts/render_title_packaging.py <project_path>
```

Use `--alpha-mov` only for requested animated delivery. The generated transparent PNG files, and optional MOV files when requested, are post-production overlays for editing software.
