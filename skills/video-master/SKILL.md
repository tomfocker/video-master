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
- If a dedicated `imagegen` skill/tool is available, follow it for image generation and project-bound save-path handling.
- If native image generation is unavailable, create the complete image prompt set, mark each affected frame `Needs-Generation`, and continue with the remaining package.
- Do not claim a storyboard image file exists until its path has been verified.
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

## Pipeline

### Step 1: Input Readiness Check

Gate: the user has provided a video idea, source material, or rough requirement.

Classify the input mode before creative work:

- `idea-only`: the user has only a concept; Codex may propose product, story, scene, copy, and visual assumptions.
- `asset-assisted`: the user has partial assets such as product photos, logo, copy, selling points, reference videos, or target platform.
- `material-locked`: the user has approved assets/copy/brand rules; Codex must structure and adapt them without inventing unsupported claims or changing key wording.

If the mode is unclear, ask one concise question. Otherwise proceed with explicit assumptions.

Write:

- `strategy/input_readiness.md`

Capture available materials, missing materials, what may be invented, what must be preserved, and any required source files in `sources/`.

When the user uploads reference images or videos, label each asset's role explicitly:

- `reference_style`: use only for transferable style rules such as palette, contrast, lighting, pacing, camera language, framing, transition rhythm, captions, and packaging.
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
  references/
  references/reference_keyframes/
  最终交付/
    01_分镜图/
    02_提示词/
    03_口播与字幕/
    04_分镜总览/
    05_预览视频/
    06_制作总表/
  qa/metadata/
```

Present the Production Lock as a bundled recommendation and wait for confirmation unless the user has supplied the decisions or explicitly allowed assumptions:

1. Input mode and asset authority
2. Video mode
3. Objective and CTA
4. Audience and platform
5. Aspect ratio and target duration
6. Prompt language and target video model/profile
7. Copy/VO language, caption language, and subtitle rendering policy (`post-production-only` by default)
8. Narrative style, visual style, and pacing style
9. Character/product/brand continuity rules
10. Claims/compliance boundaries
11. Storyboard image coverage: every shot, key shots, or selected scenes
12. Reference style usage: mimic color grading, camera language, edit rhythm, typography/packaging, or only general mood

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

- What should be mimicked: palette, contrast, lighting, lens language, shot duration pattern, camera movement, transitions, subtitles, packaging.
- What must not be copied: people, brand marks, exact scenes, plot, dialogue, slogans, copyrighted characters, or protected creator style.
- How the rules affect storyboard image prompts and video prompts.

### Step 4: Creative Strategy And Rhythm Map

Gate: `creative_brief.md` and `spec_lock.md` exist.

Write:

- `strategy/creative_strategy.md`
- `strategy/rhythm_map.md`

The rhythm map must allocate non-uniform shot durations unless the confirmed mode genuinely calls for uniform timing. For advertising modes, design hook, product memory, proof, and CTA beats deliberately. Do not default to equal shot lengths.

Act like a creative director, not a spreadsheet. For high-motion subjects such as racing, sport, chase sequences, launch films, and fast-paced TVC, design at least one rapid-cut cluster of very short shots before or after longer emotional shots. Use shot durations such as `0.6s`, `0.8s`, `1.2s`, and `2s` when the moment calls for velocity, then contrast them with longer breath shots. Mark camera energy explicitly: stable, handheld, vehicle-mounted vibration, impact shake, whip pan, hard push-in, POV, pass-by, or locked-off.

Use `references/video-modes.md`, `references/platform-and-model-profiles.md`, and any `references/style_analysis.md`.

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
Confirm whether the spoken copy is Chinese, English, bilingual, or user-supplied before writing `audio/voiceover_script.md`. Treat `audio/captions.srt` as a post-production subtitle asset unless `burned_subtitles_allowed` is explicitly true. For Chinese-facing delivery, create Chinese localized captions even if the spoken VO is English, and keep the VO-language transcript as a separate SRT.
In `audio/music_sfx_cue_sheet.md`, map an SFX cue to every shot. Keep background music as a whole-film post-production direction unless the user explicitly asks to generate or mix music later.

### Step 6: Shot List And Storyboard Plan

Gate: script and audio files exist.

Write:

- `storyboard/shot_list.md`
- `storyboard/shot_list.json`

Use a compact overview table plus per-shot detail blocks. Avoid a single very wide Markdown table for all fields. Every shot must include timing, beat, visual action, framing, camera, movement, lighting, audio/copy references, continuity notes, image prompt seed, and video prompt seed.

### Step 7: Storyboard Image Prompts And Native Images

Gate: `shot_list.md` exists and storyboard coverage is known.

Read `brief/spec_lock.md`, `references/storyboard-and-video-prompts.md`, and any `references/style_analysis.md`.

Write `prompts/storyboard_image_prompts.md` before generating images. Generate storyboard frames with native image generation:

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

If the target workflow is Chinese or domestic Chinese video models are named, final copy-ready prompts must be Chinese-first. Keep `prompts/video_prompts.md` detailed for review, and make `最终交付/02_提示词/视频生成提示词.md` easy to copy into a video model.

Use `references/storyboard-and-video-prompts.md`, `references/platform-and-model-profiles.md`, and any `references/style_analysis.md`. If `reference_style` assets exist, final video prompts must carry the same safe style rules used for native image generation so generated video matches the reference look and editing language without copying protected content.
Separate external audio from generated visuals. Use fields such as `Voiceover/audio` or `声音/口播` for post-production narration, and `On-screen text policy` or `画面文字策略` for visual text. Do not use mixed labels such as `声音/字幕`; they can cause video models to burn VO lines into the picture. When `subtitle_rendering_policy` is `post-production-only`, every copy-ready prompt should say the model-generated picture should not include subtitles, captions, dialogue text, lyrics, or burned-in text.

For external voiceover, never paste the actual VO sentence into the video prompt. Write `声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。` and keep the line itself in the audio/SRT files. Each shot block should also include `背景音乐：不要生成背景音乐；整片音乐后期统一处理。` and an `SFX音效` line. Do not include a `负面提示词` section in final prompts.

### Step 9: Deliverables Package

Gate: script, shot list, audio files, storyboard manifest, generated frames, and video prompts exist.

Write:

- `最终交付/00_使用说明.md`
- `最终交付/03_口播与字幕/口播稿.md`
- `最终交付/03_口播与字幕/中文字幕.srt` and/or `最终交付/03_口播与字幕/英文字幕.srt`
- Any model/platform-specific final files requested by the user

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
- `references/storyboard-and-video-prompts.md`: image and video prompt patterns.
- `references/quality-check.md`: final QA checklist and validator use.
