# Storyboard And Video Prompt Patterns

Use this reference when writing `storyboard_image_prompts.md`, `video_prompts.md`, and `最终交付/02_提示词/*`.

## Shared Style Bible

Derive this from `brief/spec_lock.md` and reuse it across every prompt:

```text
Aspect ratio: <ratio>
Target video model/profile: <seedance-2.0 by default, or explicitly named model>
Prompt language: <zh-CN / en / bilingual>
Copy language: <zh-CN / en / bilingual / user-supplied>
Voiceover language: <zh-CN / en / bilingual / none>
Subtitle rendering policy: <post-production only by default; model-generated text only if explicitly approved>
Video mode: <mode>
Visual style preset: <visual_style_preset_id and display name, or custom/reference-derived>
Visual style: <medium, realism, art direction>
Color and lighting: <palette, contrast, time of day, mood>
Camera language: <lens feel, framing tendencies, movement style>
Texture/material rules: <grain, material response, surface, illustration texture, render qualities>
Storyboard prompt rules: <locked rules from visual style preset>
Video prompt rules: <locked rules from visual style preset>
Continuity: <characters, product, wardrobe, locations, props>
Reference frames/assets: <paths when available>
Reference style source: <references/style_analysis.md and references/reference_keyframes/* when available>
Style transfer rules: <transfer palette, contrast, lighting, camera language, edit rhythm, typography/packaging; do not copy subjects, plot, branding, or protected style>
Avoid: <watermarks, unwanted text, unsafe or off-brand elements>
```

## Storyboard Image Prompt

One prompt creates one still frame. Avoid words like "video", "motion", or "animation" unless describing implied direction.

Video Master defaults to Codex native image generation. Do not treat missing CLI/API credentials or a missing tool listing as proof that image generation is unavailable; attempt the native image path first and only then record a failure if the generation call itself fails.

```text
Use case: ads-marketing
Asset type: storyboard frame for <project name>, shot <shot id>
Primary request: Create a single cinematic storyboard frame showing <subject/action>.
Aspect ratio: <locked aspect ratio>
Scene/backdrop: <location and environment>
Subject: <characters/product/objects with continuity details>
Composition/framing: <wide/medium/close-up, rule of thirds, foreground/background>
Camera: <angle, lens feel, depth of field>
Lighting/mood: <specific lighting and emotional tone>
Visual style preset: <locked preset id/name from spec_lock.md>
Style/medium: <locked visual style>
Color palette: <locked palette>
Texture/material: <locked texture and material response>
Preset prompt rules: <storyboard_prompt_rules from spec_lock.md>
Constraints: consistent character/product design; no watermark; no accidental logos
Style transfer rules: <if reference_style assets exist, mimic only the approved color grading, lighting, framing, lens language, texture, and visual packaging rules from references/style_analysis.md; use safe reference keyframes with native image generation when supported>
Avoid: distorted anatomy, extra fingers, illegible text, random UI, captions, subtitles, duplicate subjects
```

If the frame needs readable text, add:

```text
Text (verbatim): "<exact short text>"
```

Keep text short. Prefer adding captions in post-production rather than inside generated images.

## Style Confirmation Gate

For formal projects with generated storyboard images, use `style_confirmation_gate` before batch image generation. Create or confirm the character anchor first, then generate only the first storyboard frame (S01). Present the character anchor and first storyboard frame to the user, record `style_gate_status: pending`, and do not batch-generate remaining storyboard frames until the user approves the style. Explicit simulation/test runs may record `style_gate_status: skipped` with a reason before continuing.

## Copy Language And Subtitle Policy

Prompt language and copy language are separate decisions. Confirm whether the video copy/VO should be Chinese, English, bilingual, or user-supplied before writing script, TTS, captions, or final prompts.

Default subtitle policy: `post-production only`. `audio/captions.srt` is for preview/post-production subtitle workflows, not an instruction for the video model to create text in the picture. Unless `burned_subtitles_allowed` is explicitly true, every copy-ready final video prompt should use the compact line `字幕：不要生成字幕、caption、对白文字或烧录文字`.

Keep VO, TTS, caption, and packaging details in their own files. For review-only prompt drafts you may keep separate audio or visual-text notes, but copy-ready final prompts should not include external VO explanations, subtitle file paths, packaging file paths, or mixed labels such as `声音/字幕`.

## Reference Style Transfer

When users provide reference images or videos for style, do not treat them as content to reproduce. Convert them into a safe style bible before writing storyboard image prompts or video prompts.

Use `references/style_analysis.md`, `references/color_style.md`, `references/editing_style.md`, and `references/reference_keyframes/` when present.

Style transfer rules:

- Transfer color grading, contrast, saturation, black level, highlight behavior, lighting direction, lens feel, framing density, edit rhythm, transition language, and packaging motifs.
- Treat reference subtitle placement or caption styling as analysis-only/post-production observations. Do not ask image or video models to reproduce burned subtitles, caption placement, or subtitle styling unless `subtitle_rendering_policy` and `burned_subtitles_allowed` explicitly allow generated text.
- Use safe keyframes as visual references for native image generation when the image tool supports reference inputs; otherwise cite the keyframe paths and style rules in the prompt text.
- Keep the new project's original subjects, plot, characters, products, copy, and brand rules.
- Do not copy subjects, plot, branding, or protected style from the reference.
- Do not ask for an exact remake, frame-by-frame match, identifiable creator style, celebrity likeness, copyrighted character, real brand mark, or recognizable scene from the reference.
- If the uploaded reference is a user-owned brand asset, preserve only the specific brand elements the user authorizes in `brief/spec_lock.md`.

## Visual Style Preset Application

Use this section before writing `prompts/storyboard_image_prompts.md`. Read `references/visual-style-presets.md`, `references/visual_style_presets.json`, and the locked `visual_style` section in `brief/spec_lock.md`.

- Every storyboard image prompt must include the selected `visual_style_preset_id`, medium, realism level, art direction, palette, lighting, texture/material rules, camera language, and `storyboard_prompt_rules`.
- Every video prompt should preserve the same look through `video_prompt_rules`, camera language, lighting, and texture descriptions.
- If the user selected `custom`, write a compact custom style bible with the same fields as a preset.
- If the user selected `reference-derived`, use `references/style_analysis.md` and safe keyframes as the source of the same fields.
- If a full style template is also selected, apply the template as the director method and the visual preset as the look card unless the user explicitly overrides it.
- Do not ask for a specific living artist, exact studio look, existing character, exact frame remake, brand mark, or protected source scene.

## Title Packaging Prompt Sidecar

Use this section only for `packaging/title_packaging_prompts.md`. It is not part of storyboard prompts or copy-ready video prompts.

Title packaging may use native image generation for designed packaging images. Without API-native transparency, generate the asset on a pure chroma-key background and remove the key locally. Exact readable text should be rendered or verified by the deterministic packaging script.

Prompt fields:

```text
Use case: commercial title packaging sidecar
Asset type: title_card | chapter_card | lower_third | name_tag | counter | data_callout | cta_card | end_card
Transparent background: yes
Text (verbatim): "<exact short title or name>"
Subtitle (optional): "<exact short subtitle>"
Composition: <center / lower third / top left / bottom right>
Typography mood: <premium editorial / sports broadcast / documentary / tech launch>
Material and light: <glass, metal, paper, ink, glow, shadow, rim light>
Reference packaging style: <use only typography mood, spacing, hierarchy, material, light, and commercial polish from reference_style assets>
Do not copy: exact source title names, layouts, logos, watermarks, or source artwork
Delivery note: final exact text, transparent PNG overlays, and optional alpha MOV overlays are rendered by scripts/render_title_packaging.py
```

Never paste these sidecar prompts into `prompts/video_prompts.md` or `最终交付/02_提示词/视频生成提示词.md`.

Default to transparent PNG packaging. Request MOV only when the user needs a real animated overlay such as stroke reveal, route drawing, counter ticking, mask wipe, glow sweep, or a custom motion. A simple fade or position shift is not enough reason to create MOV. When MOV is needed, record the chosen `motion_template` in `packaging/title_packaging_plan.json`; supported templates include `brush_reveal`, `mask_wipe`, `glow_sweep`, `route_light_trail`, `odometer`, `number_roll`, `marker_annotation`, and `annotation_arrow`. If native image generation created a designed transparent title layer, reference it as `design_asset` and let `scripts/render_title_packaging.py` animate the alpha overlay.

## Style Template Application

Use this section when applying a style template to storyboard image prompts and video prompts.

When `brief/spec_lock.md` contains `template_id`, prompt writing must read `style_templates/<template_id>/prompt_rules.md`. For shot planning, also use `shot_motifs.json`, `editing_craft.md`, and `director_notes.md` when present.

- Apply the style template as a whole director method rather than choosing a strength tier.
- Explicit user ideas override template defaults: subject, copy, brand rules, supplied assets, required scenes, and compliance constraints come first.
- Use the template for transferable visual language, rhythm structure, camera grammar, edit strategy, sound policy, and prompt fields.
- If user ideas conflict with the template, preserve the user's intent and adapt the template's method around it.

Final video prompts must remain subject-specific and must not mention copying the reference video.

## Detailed Video Prompt Block

Use this for `prompts/video_prompts.md`.

```markdown
## S01 - <short shot name>

- Duration:
- Reference frame:
- Reference style:
- Visual prompt:
- Motion prompt:
- Camera prompt:
- Subject/action prompt:
- Continuity:
- Voiceover/audio:
- On-screen text policy:
- Background music policy:
- Audio/SFX:
- Generation requirements:
- Parameters/assumptions:
```

## Copy-Ready Chinese Prompt Block

Use this for `最终交付/02_提示词/视频生成提示词.md` when `prompt_language` is `zh-CN` and the user has explicitly selected a non-Seedance model-agnostic format. Otherwise use the Seedance 2.0 block below.

```markdown
## S01 - <镜头名>（<秒数> / <比例> / <目标模型或平台> / 参考图：<相对路径>）

画面：<中文描述主体、场景、构图、风格>
动作：<中文描述人物/产品/环境运动>
镜头：<中文描述机位、景别、运动，可保留 macro close-up / shallow depth of field 等英文标签>
光线与风格：<中文描述光线、色彩、质感、统一性>
参考风格：<如有 reference_style，写明参考风格规则和安全关键帧路径；只迁移调色、构图、镜头语言和剪辑节奏，不复制原片内容>
背景音乐：不要生成背景音乐
SFX音效：<本镜头需要的现场声/拟音/冲击音，例如引擎、雨声、手套摩擦、按钮声、呼吸声>
字幕：不要生成字幕、caption、对白文字或烧录文字
生成要求：<用正向约束描述稳定主体、连续动作、清晰构图、授权标识策略；不要写“负面提示词”字段>
```

If a character visibly speaks on camera, the prompt may describe the performance and lip movement. If the line is external narration or later TTS/VO, never paste the actual narration sentence into the video model prompt.

Per-clip background music should stay off. Current segmented video models often produce different music beds per clip, which makes assembly cuts feel hard. Keep music direction in the whole-film audio plan and keep final video prompts focused on visual motion plus shot-specific SFX.

## Seedance 2.0 Copy-Ready Prompt Block

Seedance 2.0 is the default target video model/profile. Use this for `最终交付/02_提示词/视频生成提示词.md` unless the user explicitly names another video model. It keeps the single-shot prompt easy to paste while adding the motion detail Seedance expects.

```markdown
## S01 - <镜头名>（<秒数> / <比例> / Seedance 2.0 / 参考图：<相对路径>）

画面：<中文描述主体、场景、构图、风格>
视觉连续性：<固定角色/产品/服装/场景/材质规则>

动态时间切片：
(00-1.0s): <根据该分镜分析出的起势动作、景别和第一段运镜，不复用固定模板>。
(1.0-2.2s): <该分镜最重要的动作推进、道具/角色/环境互动和机位变化>。
(2.2-3.0s): <收束到本镜头的关键视觉点、表情/材质/产品细节或转场方向>。

运镜与焦段：<景别、机位、镜头运动，可保留 slow dolly in / handheld / macro close-up / shallow depth of field 等英文标签>
光线与风格：<中文描述光线、色彩、质感、统一性>
稳定性要求：五官清晰、面部稳定、人体结构正常、同一角色、服装一致、发型不变；产品造型、材质和比例稳定；无闪烁、无重影。
背景音乐：不要生成背景音乐
SFX音效：<本镜头需要的现场声/拟音/冲击音>
字幕：不要生成字幕、caption、对白文字或烧录文字
生成要求：连续运动、真实物理惯性、清晰主体、稳定构图、自然表情或材质变化；不要写“负面提示词”字段
```

Keep the prompt body compact. Do not add standalone `目标模型`, `时长`, `画幅`, or `参考图` lines; keep those in the heading so users can copy the useful prompt body quickly. Do not add packaging-file notes, subtitle-file paths, or external-VO explanations inside the copy-ready video prompt.

Time-slice count should follow duration: 2s can use 2 slices, 3-5s usually uses 3-4 slices, 10s uses about 8 slices, and 15s uses about 12 slices. Do not make every slice a new scene; the slices describe how one shot evolves over time. Each slice must be inferred from that specific storyboard: choose shot-specific framing, camera movement, action beats, prop interaction, and environmental motion. Do not reuse generic phrases such as `gentle dolly 或 tabletop camera movement` or `镜头继续完成本镜头节拍`.

## Prompt Dialect Notes

- Seedance 2.0: default profile; use Chinese-first prompts with `动态时间切片`, explicit camera movement, environment interaction, micro-expression/material motion, and stability constraints.
- Model-agnostic: use clear natural language with labeled fields.
- Domestic Chinese models: default Chinese prompts; keep actions concrete; keep one dominant action per shot; add reference image paths when supported.
- Sora-style: emphasize scene physics, continuity, cinematic movement, and temporal progression.
- Runway/Pika-style: keep prompts compact; make camera and motion explicit; use reference image notes.
- Kling-style: specify subject movement and camera movement separately; keep action concrete.

Do not overfit to a named model unless the user explicitly names it.

## Consistency Rules

- Reuse identical character names and continuity descriptors across all shots.
- Use the same product descriptors, materials, colors, and logo policy across all shots.
- Keep camera moves physically plausible for the shot duration.
- Keep one dominant action per shot.
- Avoid style drift unless the script calls for it.
- When a generated frame drifts, regenerate once or mark the drift in `storyboard_manifest.md` and `最终交付/00_使用说明.md`.
