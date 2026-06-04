# Platform And Model Profiles

Use this reference after video mode is confirmed.

## Platform Constraints

| Platform | Practical Rules |
| -------- | --------------- |
| 小红书 | Strong cover/first frame, clean lifestyle visuals, readable captions, less hard-sell tone, 3s hook still matters |
| 抖音 | Faster hook, high visual contrast or clear action, captions and CTA must be immediate, rhythm can be punchier |
| 朋友圈 | More polished brand tone, less noisy editing, CTA can be softer, trust and taste matter |
| B站 | More tolerance for explanation and longer structure, voiceover clarity matters |
| 电商详情/投放 | Product visibility, offer/benefit clarity, CTA and compliance language matter most |

Always consider safe zones for subtitles and UI overlays. Avoid placing critical text at top/bottom edges.

## Model Profiles

### Default Target Model

Default to `seedance-2.0` / Seedance 2.0 for video generation prompts unless the user explicitly names another video model. Record both fields in `brief/spec_lock.md`:

```text
- target_model: seedance-2.0
- prompt_dialect: seedance-2.0
```

When a user names another model, keep the selected model in `target_model` and use the closest profile below.

### `seedance-2.0`

Use for the default workflow and for users who name Seedance, Seedance 2.0, 豆包视频, or a Seedance-compatible Chinese video-generation workflow.

- For hands-on production rules, read `references/seedance2-practical-playbook.md` before writing storyboard image prompts or final copy-ready video prompts.
- For scene-specific directing patterns, also read `references/scene-director-patterns.md` when the project fits product showcase, short drama, music beat montage, one-take transition, video extension, video edit, science visualization, fantasy action, or motion poster. Apply the pattern through Seedance-style time slices and explicit asset-role binding.
- Final prompts default to Chinese-first, with optional English camera tags only when they add precision.
- Write one copy-ready block per shot, not one long film prompt.
- For 15-second clip workflows, treat each prompt as a mini sequence with internal beats. Generate multiple reference images when a segment includes introductions, transitions, transformations, multi-state process visuals, or ending/title-safe staging.
- For scene consistency, add `场景设定` and, when the set/location/product stage matters, reference a wide scene-anchor image in the shot heading alongside action keyframes. `场景设定` should include recurring/high-frequency character anchors when present, not only the physical environment.
- Add `画面风格说明` before the time slices, split into `风格核心`, `视觉基调`, `色彩与影调`, `摄影机与镜头`, `材质与特效`, `动作质感`, and `风格边界` for style-heavy or realistic scenes.
- For realistic live-action scenes where the user wants to avoid AI feel, include `超写实`, `极致逼真`, and `Photorealism-真人实景拍摄` in the realism/style section. Do not use those anchors for intentionally stylized animation, anime, 2D, toy-like 3D, or graphic motion.
- Put model, duration, aspect ratio, and reference-frame path in the shot heading. Do not repeat them as standalone body fields.
- Inside each shot, add a `动态时间切片` section with rhythm-driven whole-second segments such as `(00-1s)`, `(1-3s)`, and `(3-6s)`. Avoid decimal/sub-second time codes in final model-facing prompts.
- Every time slice should be inferred from the storyboard beat: combine framing, camera movement, subject action, prop interaction, environment motion, dialogue mouth cue or character performance, natural synchronous sound, and SFX accents. Do not reuse a generic motion template across shots, do not imply frame-level timing precision, and do not default to equal timing unless a fixed beat grid is intentionally chosen.
- Keep motion continuous and physically plausible: slow, smooth, connected, natural, not abrupt unless the shot deliberately calls for impact.
- Add stability constraints: clear face when a face appears, stable identity, normal anatomy, consistent wardrobe/product, no flicker, no ghosting, no watermarks or accidental text.
- Keep final prompt bodies compact. Do not repeat standalone `运镜与焦段` or `光线与风格` after the time slices; those belong in `画面风格说明`. Put stability, audio, subtitle/text, and execution policies under one `生成要求` section, with simple model-facing wording such as `音频：背景音乐不要生成；同期声...；SFX...` and `字幕与文字：不要生成字幕、caption、对白文字或烧录文字`. Do not add subtitle-file paths, packaging-file notes, or external-VO explanations. SFX cues are accents and should not suppress other natural sounds.

### `model-agnostic`

Use labeled prompts with visual, motion, camera, continuity, and generation requirements. For copy-ready prompts, group external audio policy, background music policy, synchronous sound / room tone, SFX accents, on-screen text policy, and stability rules under `生成要求`.

### `domestic-cn`

Use when the user names 可灵、即梦、通义万相、Vidu、海螺, or a Chinese video-generation workflow.

- Final prompts default to Chinese.
- Use short, concrete action descriptions.
- Keep one main action per shot.
- Avoid negative-prompt fields in final copy-ready prompts; express constraints through `生成要求` lines such as `画面文字策略` / `字幕与文字`, `音频`, and positive generation requirements.
- Preserve optional English camera tags only when useful: `macro close-up`, `shallow depth of field`, `slow push-in`, `hero shot`.

### `sora-style`

Emphasize physical continuity, scene evolution, cinematic camera movement, and temporal detail.

### `runway-pika-style`

Keep prompts compact. Make camera and motion explicit. Mention reference image use if available.

### `kling-style`

Separate subject movement from camera movement. Keep action grounded and duration-appropriate.

## Prompt Language Rule

- If the user names no target video model, use `target_model: seedance-2.0` and `prompt_dialect: seedance-2.0`.
- If the user writes in Chinese and names no foreign model, set `prompt_language: zh-CN`.
- If the user names a domestic Chinese model, set `prompt_dialect: domestic-cn`.
- If the user names Seedance 2.0, set `prompt_dialect: seedance-2.0`.
- If the user names Sora/Runway/Pika and asks for English, use English.
- If uncertain, use Chinese final prompts plus optional English technical tags.
