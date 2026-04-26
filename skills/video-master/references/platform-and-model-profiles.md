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

### `model-agnostic`

Use labeled prompts with visual, motion, camera, continuity, external audio policy, background music policy, SFX, on-screen text policy, and generation requirements.

### `domestic-cn`

Use when the user names 可灵、即梦、通义万相、Vidu、海螺, or a Chinese video-generation workflow.

- Final prompts default to Chinese.
- Use short, concrete action descriptions.
- Keep one main action per shot.
- Avoid negative-prompt fields in final copy-ready prompts; express constraints through `画面文字策略`, `背景音乐`, `SFX音效`, and positive generation requirements.
- Preserve optional English camera tags only when useful: `macro close-up`, `shallow depth of field`, `slow push-in`, `hero shot`.

### `sora-style`

Emphasize physical continuity, scene evolution, cinematic camera movement, and temporal detail.

### `runway-pika-style`

Keep prompts compact. Make camera and motion explicit. Mention reference image use if available.

### `kling-style`

Separate subject movement from camera movement. Keep action grounded and duration-appropriate.

## Prompt Language Rule

- If the user writes in Chinese and names no foreign model, set `prompt_language: zh-CN`.
- If the user names a domestic Chinese model, set `prompt_dialect: domestic-cn`.
- If the user names Sora/Runway/Pika and asks for English, use English.
- If uncertain, use Chinese final prompts plus optional English technical tags.
