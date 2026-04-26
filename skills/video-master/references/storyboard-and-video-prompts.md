# Storyboard And Video Prompt Patterns

Use this reference when writing `storyboard_image_prompts.md`, `video_prompts.md`, and `最终交付/02_提示词/*`.

## Shared Style Bible

Derive this from `brief/spec_lock.md` and reuse it across every prompt:

```text
Aspect ratio: <ratio>
Prompt language: <zh-CN / en / bilingual>
Copy language: <zh-CN / en / bilingual / user-supplied>
Voiceover language: <zh-CN / en / bilingual / none>
Subtitle rendering policy: <post-production only by default; model-generated text only if explicitly approved>
Video mode: <mode>
Visual style: <medium, realism, art direction>
Color and lighting: <palette, contrast, time of day, mood>
Camera language: <lens feel, framing tendencies, movement style>
Continuity: <characters, product, wardrobe, locations, props>
Reference frames/assets: <paths when available>
Reference style source: <references/style_analysis.md and references/reference_keyframes/* when available>
Style transfer rules: <transfer palette, contrast, lighting, camera language, edit rhythm, typography/packaging; do not copy subjects, plot, branding, or protected style>
Avoid: <watermarks, unwanted text, unsafe or off-brand elements>
```

## Storyboard Image Prompt

One prompt creates one still frame. Avoid words like "video", "motion", or "animation" unless describing implied direction.

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
Style/medium: <locked visual style>
Color palette: <locked palette>
Constraints: consistent character/product design; no watermark; no accidental logos
Style transfer rules: <if reference_style assets exist, mimic only the approved color grading, lighting, framing, lens language, texture, and visual packaging rules from references/style_analysis.md; use safe reference keyframes with native image generation when supported>
Avoid: distorted anatomy, extra fingers, illegible text, random UI, captions, subtitles, duplicate subjects
```

If the frame needs readable text, add:

```text
Text (verbatim): "<exact short text>"
```

Keep text short. Prefer adding captions in post-production rather than inside generated images.

## Copy Language And Subtitle Policy

Prompt language and copy language are separate decisions. Confirm whether the video copy/VO should be Chinese, English, bilingual, or user-supplied before writing script, TTS, captions, or final prompts.

Default subtitle policy: `post-production only`. `audio/captions.srt` is for preview/post-production subtitle workflows, not an instruction for the video model to create text in the picture. Unless `burned_subtitles_allowed` is explicitly true, every final video prompt must say `do not generate subtitles`, captions, dialogue text, lyrics, or burned-in text.

Use separate fields:

- `Voiceover/audio` / `声音/口播`: external narration, TTS, or post-production audio.
- `On-screen text policy` / `画面文字策略`: whether generated visual text is allowed. Default is none.

Avoid a single mixed field that combines narration and subtitles; video models often read that as a request to burn VO lines into the generated clip.

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

Use this for `最终交付/02_提示词/视频生成提示词.md` when `prompt_language` is `zh-CN`.

```markdown
## S01 - <镜头名>

时长：<秒数>
参考图：<相对路径>
画面：<中文描述主体、场景、构图、风格>
动作：<中文描述人物/产品/环境运动>
镜头：<中文描述机位、景别、运动，可保留 macro close-up / shallow depth of field 等英文标签>
光线与风格：<中文描述光线、色彩、质感、统一性>
参考风格：<如有 reference_style，写明参考风格规则和安全关键帧路径；只迁移调色、构图、镜头语言和剪辑节奏，不复制原片内容>
声音/口播：<外部配音或后期音频说明；如果是画外音，不写具体台词，只写后期添加>
背景音乐：不要生成背景音乐；整片音乐后期统一处理
SFX音效：<本镜头需要的现场声/拟音/冲击音，例如引擎、雨声、手套摩擦、按钮声、呼吸声>
画面文字策略：<默认无；如需片内文字，写明准确文字和用户授权>
字幕策略：post-production only；字幕使用 audio/captions.srt 后期添加，模型生成画面不添加字幕、caption、对白文字或烧录字幕
生成要求：<用正向约束描述稳定主体、连续动作、清晰构图、授权标识策略；不要写“负面提示词”字段>
```

If a character visibly speaks on camera, the prompt may describe the performance and lip movement. If the line is external narration or later TTS/VO, never paste the actual narration sentence into the video model prompt.

Per-clip background music should stay off. Current segmented video models often produce different music beds per clip, which makes assembly cuts feel hard. Keep music direction in the whole-film audio plan and keep final video prompts focused on visual motion plus shot-specific SFX.

## Prompt Dialect Notes

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
