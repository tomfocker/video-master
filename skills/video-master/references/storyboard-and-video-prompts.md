# Storyboard And Video Prompt Patterns

Use this reference when writing `storyboard_image_prompts.md`, `video_prompts.md`, and `最终交付/02_提示词/*`.

If the project matches a scene director pattern such as product showcase, live-commerce spokesperson, short drama, music beat montage, one-take transition, video extension, video edit, science visualization, fantasy action, motion poster, or animation action, read `references/scene-director-patterns.md` and adapt one primary pattern into shot-specific beats. For Seedance 2.0 or 15-second web video generation, also read `references/seedance2-practical-playbook.md` before writing image prompts or copy-ready video prompts.

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
Scene setting: <stable location/set/tabletop/stage, time, atmosphere, set dressing, light direction, and recurring visible character/product placement when applicable>
Scene anchor reference: <references/scene_anchors/<scene_id>.png or final selected wide scene frame when available>
Scene character anchors: <recurring/high-frequency character IDs, visible face/hair/body/wardrobe cues, signature props, and starting positions when applicable>
Detailed visual style description: <风格核心, 视觉基调, 色彩与影调, 摄影机与镜头, 材质与特效, 动作质感, 风格边界>
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

## Scene Anchor / Wide Reference Frame

For 15-second Seedance segments, multi-shot sequences, recurring locations, or product environments where spatial continuity matters, create a wide scene-anchor frame before action keyframes. If recurring people, hosts, actors, mascots, or hero products appear repeatedly in the scene, the scene anchor or companion notes should also lock their starting placement and visible identity cues.

Scene anchor prompt fields:

```text
Use case: scene continuity anchor
Asset type: wide scene reference for <project name>, segment <segment id>
Primary request: Create a wide establishing frame that locks the full playable space for later video generation.
Aspect ratio: <locked aspect ratio>
Scene setting: <location/set/tabletop/stage, time, weather/room tone, background, floor/table/terrain, main props, recurring character/product placement when applicable>
Character/product anchors: <stable IDs plus visible descriptors, wardrobe/material rules, signature props, scale, and allowed movement zone>
Action-safe layout: <where characters/products can move; where title-safe negative space remains>
Lighting direction: <key light, rim light, window/sun/studio direction>
Visual style preset: <locked preset id/name>
Detailed visual style: <style core, visual base, color/shadow, camera/lens, material/VFX, motion texture, style boundaries>
Continuity rules: keep this scene layout, prop placement, recurring character/product placement, lighting direction, and material language consistent across all segment action frames and video prompts
Avoid: readable text, random logos, subtitles, clutter that will fight the action, protected source elements
```

Name scene anchors distinctly, such as `SEG01_SCENE.png`, and reference them separately from action keyframes.

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
- Sync sound / room tone:
- SFX accents:
- Generation requirements:
- Parameters/assumptions:
```

## Copy-Ready Chinese Prompt Block

Use this for `最终交付/02_提示词/视频生成提示词.md` when `prompt_language` is `zh-CN` and the user has explicitly selected a non-Seedance model-agnostic format. Otherwise use the Seedance 2.0 block below.

```markdown
## S01 - <镜头名>（<秒数> / <比例> / <目标模型或平台> / 参考图：<相对路径>）

场景设定：<中文描述稳定场景、空间布局、时间、环境状态、主要道具和不可漂移内容；如有高频人物，写明角色ID、可见外貌/发型/身形/服装/道具、初始站位和与场景的关系>
画面风格说明：
风格核心：<中文描述核心风格、媒介和真实感；真实场景规避 AI 感时使用“超写实、极致逼真、Photorealism-真人实景拍摄”>
视觉基调：<中文描述电影/摄影/画幅/构图/运动质感>
色彩与影调：<中文描述主色、对比度、饱和度、高光暗部、胶片/滤镜/自然光规则>
摄影机与镜头：<中文描述机身/镜头质感、焦段行为、景深、动态模糊、手持或稳定方式>
材质与特效：<中文描述材质渲染、粒子/VFX/CG边界、真实纹理规则>
动作质感：<中文描述速度、重量、惯性、停顿和避免僵硬 AI 感的规则>
风格边界：<中文描述不要出现的视觉模式、媒介漂移、氛围偏差或风格误读；文字、logo、水印等执行约束写入生成要求>
参考风格：<如有 reference_style，写明参考风格规则和安全关键帧路径；只迁移调色、构图、镜头语言和剪辑节奏，不复制原片内容>
画面与动作：<中文描述主体、动作、场景互动和构图；镜头、光线、色彩只在上面的画面风格说明中定义>
视觉连续性：<固定角色/产品/服装/场景/材质规则>
生成要求：
稳定性：<五官/人体/产品/材质/场景稳定规则>
音频：背景音乐不要生成；同期声请生成与画面动作自然同步的现场声、环境声、空间氛围声和可见材质互动声；SFX只强调本镜头重点拟音/冲击音/转场音，不限制其他自然声音。
字幕与文字：不要生成字幕、caption、对白文字、烧录文字、随机logo、水印或未经授权IP标识；公益标语、包装文字、标题和所有可读文字默认后期添加。
执行要求：<连续运动、真实物理惯性、清晰主体、稳定构图、自然表情或材质变化>
```

If a character visibly speaks on camera, the prompt may describe the performance and lip movement. If the line is external narration or later TTS/VO, never paste the actual narration sentence into the video model prompt.

Per-clip background music should stay off. Current segmented video models often produce different music beds per clip, which makes assembly cuts feel hard. Keep music direction in the whole-film audio plan and keep final video prompts focused on visual motion, natural synchronous sound, and shot-specific SFX accents.

## Seedance 2.0 Copy-Ready Prompt Block

Seedance 2.0 is the default target video model/profile. Use this for `最终交付/02_提示词/视频生成提示词.md` unless the user explicitly names another video model. It keeps the single-shot prompt easy to paste while adding the motion detail Seedance expects.

For 15-second generation workflows, treat each segment as a mini sequence. Use multiple reference frames when a segment has character introductions, transformations, handoffs, multi-state transitions, or an ending/title-safe setup. The copy-ready prompt should use an integrated timeline where each time slice combines visual action, camera movement, dialogue mouth cue or performance, natural synchronous sound, and SFX accents.

Time slices should be rhythm-driven instead of mechanically equal. Use whole-second ranges in final model-facing prompts; avoid decimal/sub-second timing because it can imply unreliable frame-level precision. Equal timing is allowed only when the confirmed rhythm deliberately uses a fixed beat grid. For most scenes, vary slice lengths around hook, reveal, reaction, proof, impact, hold, and transition beats.

Each 15-second segment should also include a motivated camera/editing chain, such as entry texture -> reveal or acceleration -> focus/hold -> transition bridge. Do not leave camera movement as a separate afterthought; build quick push-in, whip pan, snap zoom, object wipe, match cut, rack focus, orbit, crane reveal, or a similar motivated move into the relevant time slice.

When `references/scene-director-patterns.md` applies, use its rhythm pattern and required locks to shape the `动态时间切片`, but keep the final prompt specific to the current storyboard, assets, characters, product, and safety rules.

```markdown
## S01 - <镜头名>（<秒数> / <比例> / Seedance 2.0 / 参考图：<场景锚点图 + 动作关键帧路径>）

场景设定：<中文描述稳定场景、空间布局、时间、环境状态、主要道具、光线方向、动作安全区和不可漂移内容；如有高频人物，写明角色ID、可见外貌/发型/身形/服装/道具、初始站位和与场景的关系>
画面风格说明：
风格核心：<中文描述核心风格、媒介和真实感；真实场景规避 AI 感时使用“超写实、极致逼真、Photorealism-真人实景拍摄”>
视觉基调：<中文描述电影/摄影/画幅/构图/运动质感>
色彩与影调：<中文描述主色、对比度、饱和度、高光暗部、胶片/滤镜/自然光规则>
摄影机与镜头：<中文描述机身/镜头质感、焦段行为、景深、动态模糊、手持或稳定方式>
材质与特效：<中文描述材质渲染、粒子/VFX/CG边界、真实纹理规则>
动作质感：<中文描述速度、重量、惯性、停顿和避免僵硬 AI 感的规则>
风格边界：<中文描述不要出现的视觉模式、媒介漂移、氛围偏差或风格误读；文字、logo、水印等执行约束写入生成要求>
画面：<中文描述主体、场景、构图、风格>
视觉连续性：<固定角色/产品/服装/场景/材质规则；固定人物需重复角色ID、脸部/发型/体态/服装锚点，不临时改造身份>

动态时间切片：
(00-1s): <根据该分镜分析出的起势动作、景别、第一段运镜、角色口型或表情、同期声/SFX，不复用固定模板>。
(1-3s): <该分镜最重要的动作推进、道具/角色/环境互动、机位变化、对白口型或反应、自然环境声>。
(3-5s): <收束到本镜头的关键视觉点、表情/材质/产品细节、同期声延续、SFX 或转场方向；按本镜头实际时长删改>。

生成要求：
稳定性：五官清晰、面部稳定、人体结构正常、同一角色、服装一致、发型不变；产品造型、材质和比例稳定；无闪烁、无重影。
音频：背景音乐不要生成；同期声请生成与画面动作自然同步的现场声、环境声、空间氛围声和可见材质互动声，不要只依据手动列出的音效；SFX只强调本镜头重点拟音/冲击音/转场音，不限制其他自然声音。
字幕与文字：不要生成字幕、caption、对白文字、烧录文字、随机logo、水印或未经授权IP标识；公益标语、标题、包装文字和所有可读文字默认后期添加。
运动与画面：连续运动、真实物理惯性、清晰主体、稳定构图、自然表情或材质变化。
```

Keep the prompt body compact. Do not add standalone `目标模型`, `时长`, `画幅`, or `参考图` lines; keep those in the heading so users can copy the useful prompt body quickly. Do not add packaging-file notes, subtitle-file paths, or external-VO explanations inside the copy-ready video prompt.

Do not add standalone `运镜与焦段` or `光线与风格` lines after `动态时间切片`; those details belong in `画面风格说明` under `摄影机与镜头`, `视觉基调`, and `色彩与影调`. Put stability, audio, subtitle/text, and execution constraints under one `生成要求` section.
The instruction to avoid `Negative prompt` / `负面提示词` fields is an internal formatting rule for the agent; do not paste that sentence into copy-ready model prompts.

Time-slice count should follow duration and rhythm: 2s can use 1-2 slices, 3-5s usually uses 2-3 slices, 10s uses about 4-6 slices, and 15s uses enough slices to cover the internal beats without overloading the prompt. Use whole-second ranges such as `(00-1s)`, `(1-3s)`, and `(3-6s)` in final prompts; avoid decimal/sub-second timing. Avoid automatic equal divisions such as five 3-second blocks for every 15-second segment. Use uneven whole-second ranges when the scene needs fast impact, a pause, a reaction hold, a material proof, or a transition bridge. Do not make every slice a new unrelated scene; the slices describe how one segment evolves over time. Each slice must be inferred from that specific storyboard: choose shot-specific framing, camera movement, action beats, prop interaction, environmental motion, character mouth cues, natural synchronous sound, and SFX accents. Do not reuse generic phrases such as `gentle dolly 或 tabletop camera movement` or `镜头继续完成本镜头节拍`.

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
