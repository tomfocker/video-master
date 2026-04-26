# Audio And Copy

Centralize voiceover, captions, and audio prompts before writing final video prompts.

Confirm copy language before writing audio assets:

- `copy_language`: Chinese, English, bilingual, or user-supplied.
- `voiceover_language`: language actually spoken by narrator/TTS.
- `caption_language`: language used in subtitle files.
- `localized_caption_languages`: extra subtitle languages for delivery, especially `zh-CN` for domestic Chinese users when VO is English.
- `subtitle_rendering_policy`: `post-production-only` by default.
- `burned_subtitles_allowed`: `false` by default for generated video clips.

Captions are `post-production only` unless the user explicitly asks for generated on-screen subtitles. `audio/captions.srt` supports previews, editors, and manual upload to platforms; it is not a prompt instruction. Final video prompts should say the model-generated picture should not include subtitles, captions, dialogue text, lyrics, or burned-in text when `burned_subtitles_allowed` is false; include model-friendly wording such as `do not generate subtitles`.
For domestic Chinese workflows, always provide a Chinese `.srt` deliverable. If the voiceover is English, create both the English transcript SRT and a Chinese localized SRT.

## Required Files

- `audio/voiceover_script.md`
- `audio/tts_lines.json`
- `audio/captions.srt`
- `audio/captions_en.srt` and/or `audio/captions_zh.srt` when multilingual subtitles are needed
- `audio/music_sfx_cue_sheet.md`
- `audio/audio_generation_prompt.md`
- `最终交付/03_口播与字幕/口播稿.md`
- `最终交付/03_口播与字幕/英文字幕.srt` and/or `最终交付/03_口播与字幕/中文字幕.srt`
- `最终交付/03_口播与字幕/口播文本.txt`
- `qa/metadata/tts_manifest.json`
- `最终交付/03_口播与字幕/口播音频.mp3` when TTS or recorded narration is available

## Voiceover Script

```markdown
# Voiceover Script

## Direction
- Voice:
- Emotion:
- Speed:
- Pronunciation notes:

## Full Read

## Lines
| ID | Time | Text | Tone | Notes |
| -- | ---- | ---- | ---- | ----- |
```

## TTS Lines

```json
[
  {
    "id": "VO01",
    "start": "00:00",
    "end": "00:03",
    "text": "清晨上妆前，肌肤总差一点水润感？",
    "tone": "轻柔、有共鸣",
    "speed": "medium",
    "pause_after_ms": 200
  }
]
```

## Captions

Generate captions from the same VO/copy source. Do not let captions drift from the spoken lines unless the user wants shorter social captions or localized Chinese subtitles for domestic distribution.

Keep captions separate from video generation prompts. Use `audio/captions.srt` and final audio files for post-production, not fields like `声音/字幕` that combine narration and on-screen text.

If narration is external VO, do not paste the spoken lines into final video prompts. The video prompt should only say that external narration/TTS will be added in post. Keep the exact words in `audio/voiceover_script.md`, `audio/tts_lines.json`, and SRT files.

Recommended naming:

- `英文字幕.srt`: English transcript matching English VO.
- `中文字幕.srt`: Chinese localized subtitles for domestic users.
- `audio/captions.srt`: the default subtitle track used by previews; choose the primary review language for the project.

## TTS Preview Track

When dependencies are installed and the user wants a voiced preview, generate narration from `audio/tts_lines.json`:

```bash
python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project_path>
```

Use `--dry-run` when you only need to package the read text and manifest for a human or external TTS service. `make_animatic.py` automatically uses `最终交付/03_口播与字幕/口播音频.mp3` if it exists, or accepts `--voiceover-audio <path>` for user-supplied narration.

## Music And SFX

`music_sfx_cue_sheet.md` should map each cue to a time range and purpose. Every shot should have at least one SFX cue; whole-film music is optional and should be treated as post-production direction, not per-clip video generation.

```markdown
| Cue | Time | Type | Description | Purpose |
| --- | ---- | ---- | ----------- | ------- |
| M01 | 00:00-00:30 | Music | Whole-film post-production music bed, not generated in video clips | Premium mood |
| S01 | 00:05 | SFX | Glass bottle tap | Product tactility |
```

## Audio Generation Prompt

Write one complete prompt for whole-film music direction and per-shot SFX direction. Include tempo, mood, instrumentation, do-not-use constraints, and voice direction when relevant.

Music and SFX are planning deliverables for now. Do not mix background music or sound effects into `分镜预览.mp4` until that workflow is explicitly enabled. Final video prompts should request no background music per clip, but should include the SFX cue for that shot.

## Copy Assets

When useful, add:

- `script/slogan_bank.md`
- `script/cta_options.md`
- `script/platform_caption_options.md`

Keep claims aligned with `brief/spec_lock.md`.
