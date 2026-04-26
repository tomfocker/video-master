# Prompt Rules

## Storyboard Image Prompts

- Include: black-and-white Chiaroscuro contrast, high-contrast near-monochrome, crushed blacks, wet silver highlights, rare red signal accent.
- Use black and white as information compression: remove decorative color and force attention onto speed, life/death stakes, texture, rain grain, carbon fiber, metal, skin, fire, and light cuts.
- Use tactile image anchors: visor reflection, gloved hand, gauge needle, tire spray, metal texture, breath fog, rain, smoke, carbon fiber.
- Use scale contrast: extreme close-up against vast negative-space wide shots.
- For flow-state shots, use calm surreal expansion instead of literal explanation.
- If user ideas override a motif, translate the motif's function into the user's subject instead of forcing racing imagery.
- Do not ask for reference-frame copying, real team marks, watermarks, burned subtitles, or real driver likenesses.

## Video Prompts

Each final video prompt block must include these fields:

- 画面
- 动作
- 镜头
- 声音/口播
- 背景音乐
- SFX音效
- 画面文字策略

For external voiceover, write:

```text
声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。
```

For music, write:

```text
背景音乐：不要生成背景音乐；整片音乐后期统一处理。
```

For text, write:

```text
画面文字策略：无；不要生成字幕、caption、对白文字或烧录文字，字幕使用 SRT 后期添加。
```

Do not include a `负面提示词` or `Negative prompt` field.

For SFX and audio design, each shot should specify whether it belongs to the external noise field or the subjective inner field:

- High-pressure shots: engine or machine roar, gearbox scream, gear bite, wind pressure, rain spray, tactile friction, fragmented breath, warning tones.
- Threshold shot: sound peaks, then drops abruptly.
- Flow-state shots: deep space low-frequency bed, controlled breath, minimal resonance, no per-clip music.

## User Overrides

When `brief/spec_lock.md` contains `template_user_overrides`, those ideas lead the prompt. Keep the template's pressure-to-flow method, but rewrite objects, scenes, subject actions, copy posture, and compliance details around the user's own direction.
