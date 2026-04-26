# Video Master Quality Check

Run this checklist before final delivery.

## Required Files

- `strategy/input_readiness.md` exists.
- `strategy/video_mode.md` exists.
- `brief/creative_brief.md` exists.
- `brief/spec_lock.md` exists and contains format, production mode, story, rhythm, visual style, visual style preset lock, continuity, audio, and safety sections.
- `strategy/creative_strategy.md` exists.
- `strategy/rhythm_map.md` exists.
- `script/script.md` exists and matches the target duration.
- `audio/voiceover_script.md`, `audio/tts_lines.json`, `audio/captions.srt`, `audio/music_sfx_cue_sheet.md`, and `audio/audio_generation_prompt.md` exist.
- `最终交付/03_口播与字幕/` contains final `.srt` files for the user.
- `storyboard/shot_list.md` and `storyboard/shot_list.json` exist.
- `prompts/storyboard_image_prompts.md` exists when storyboard images are requested.
- `storyboard/storyboard_manifest.md` records every planned frame.
- `prompts/video_prompts.md` has one block per shot.
- `最终交付/00_使用说明.md` exists.
- `最终交付/04_分镜总览/分镜总览图.png` exists.
- `最终交付/06_制作总表/制作总表.xlsx` exists when dependencies are installed.
- `qa/metadata/preview_manifest.json` exists when dependencies are installed and records whether the animatic was generated or intentionally skipped.
- `最终交付/05_预览视频/分镜预览.mp4` exists when dependencies are installed unless `preview_profile` is `off`.
- `最终交付/02_提示词/视频生成提示词.md` exists.
- `最终交付/01_分镜图/` contains final storyboard frames.
- If title packaging is requested, `packaging/title_packaging_plan.json`, `qa/metadata/title_packaging_manifest.json`, and `最终交付/07_title_packaging/` exist.

## Rhythm

- Shot durations add up to the target duration or clearly explain any variance.
- Advertising modes do not default to identical shot durations.
- High-motion subjects include at least one rapid-cut cluster and explicit impact/POV/handheld/vehicle-mounted camera language unless the user confirmed a deliberately meditative treatment.
- Hook appears in the first 1-3 seconds for short-form videos.
- CTA has enough time to read or hear.
- No shot is too overloaded for its duration.

## Audio And Copy

- `spec_lock.md` records `copy_language`, `voiceover_language`, `caption_language`, `localized_caption_languages`, `subtitle_rendering_policy`, and `burned_subtitles_allowed`.
- VO, captions, and video prompt dialogue all come from the same source copy.
- `tts_lines.json` is valid JSON and has non-empty text per line.
- Captions are readable and platform-safe.
- Captions are treated as `post-production only` unless the user explicitly approved generated on-screen subtitles.
- For domestic Chinese workflows, a Chinese SRT is included even when the VO is English; English VO projects should package both `captions_en.srt` and `captions_zh.srt`.
- Music/SFX cues map to the rhythm map.
- Every shot has an SFX cue. Per-clip video prompts explicitly say not to generate background music; whole-film music remains a post-production direction.
- If a voiced preview is requested, `最终交付/03_口播与字幕/口播音频.mp3` or a user-supplied narration file is used by `make_animatic.py`.
- Music/SFX are documented as cues only; they are not mixed into the animatic in the current workflow.

## Continuity

- Character names, appearance, wardrobe, and props stay consistent.
- Product and brand details stay consistent.
- Locations and time of day do not drift accidentally.
- Visual style matches `spec_lock.md` across all prompts.
- `spec_lock.md` records `visual_style_lock`, `visual_style_preset_id`, `visual_style_preset_name`, and preset prompt rules before storyboard image prompts are generated.
- If `reference_style` assets exist, `references/style_analysis.md`, `references/color_style.md`, `references/editing_style.md`, and `references/reference_style_manifest.md` exist before prompts are finalized.
- Reference style rules are abstracted into palette, lighting, camera language, pacing, transitions, and packaging; prompts do not copy source subjects, plot, branding, or protected style.
- Recurring characters and products are visually consistent enough for storyboard use, or the manifest/package notes any drift.
- Frames with obvious character/product/style drift have been regenerated once before final delivery.

## Storyboard Images

- Every planned frame is marked `Generated`, `Needs-Generation`, or `Skipped`.
- Generated frame paths are verified before being referenced.
- Missing images have final prompts and clear reasons.
- Image prompts describe still frames, not video clips.
- Storyboard image prompts include the locked visual style preset, medium, realism level, art direction, palette, lighting, texture/material rules, and storyboard prompt rules.
- If reference keyframes exist, storyboard image prompts cite safe style rules and reference paths, and native image generation uses reference images when available.
- Final selected frames are copied into `最终交付/01_分镜图/`.
- A storyboard overview has been generated with `scripts/make_storyboard_overview.py`.
- A packaged storyboard animatic preview has been generated with `scripts/make_animatic.py` when dependencies are installed, or the manifest explicitly records `preview_profile: off`.
- The default preview profile is `draft` at 12fps and follows the project aspect ratio; use `smooth` only when playback polish matters more than render time.
- The default motion style is `none`; use `center-zoom` or `pan-zoom` only when intentional movement is desired.
- The preview manifest records title/end cards, shot overlays, captions, motion style, voiceover status, and skipped status.

## Video Prompts

- Every shot has visual, motion, camera, continuity, external audio policy, background music policy, SFX, on-screen text policy, and parameter/assumption fields.
- If `reference_style` assets exist, every final video prompt includes the approved transferable style rules and avoids reproducing the source content.
- Final video prompts preserve the selected visual style preset through camera language, lighting, texture, and `video_prompt_rules`.
- Final copy-ready prompts are easy to paste into a model.
- If `prompt_language` is `zh-CN`, final prompts are Chinese-first.
- Final prompts separate external voiceover/audio from visual text using `声音/口播` or `Voiceover/audio`, plus `画面文字策略` or `On-screen text policy`.
- If `burned_subtitles_allowed` is false, final prompts say `do not generate subtitles`, captions, dialogue text, or burned-in text.
- Final prompts do not use mixed labels such as `声音/字幕`.
- External VO prompts do not paste the actual narration sentence into the video model prompt.
- Final prompts include no `Negative prompt` or `负面提示词` field; use positive generation requirements instead.
- Final prompts include per-shot SFX and a no-background-music policy.
- Model-specific language appears only when the user named or confirmed a target model/profile.

## Optional Title Packaging

- Title packaging is treated as a sidecar branch and does not alter storyboard, script, audio, or video-prompt generation.
- The Production Lock records whether the user wants `main_title`, `chapter_card`, `lower_third`/`name_tag`, `data_callout`/`counter`, `cta_card`/`end_card`, or no packaging.
- Copy-ready video prompts contain no `title_packaging`, `alpha_mov`, `07_title_packaging`, or packaging file-path instructions.
- Native image generation is used for designed packaging images; without API-native transparency, use pure chroma-key generation plus local key removal.
- Exact title text, lower thirds, counters, and static transparent PNG overlays are generated or verified through `scripts/render_title_packaging.py`.
- MOV is not generated by default. It is created only when the user explicitly requests animated alpha overlay delivery and the motion is meaningful enough to justify video.
- Requested MOV overlays use an explicit `motion_template` such as `brush_reveal`, `mask_wipe`, `glow_sweep`, `route_light_trail`, `odometer`, or `marker_annotation`; a plain fade, scale, or position offset is rejected as unnecessary.
- When a designed title image is used, the cleaned transparent PNG is referenced as `design_asset`, and the final MOV is verified as ProRes 4444 with alpha.
- Reference title-package images are used only as `reference_style`; prompts do not copy exact title names, layouts, logos, watermarks, or source artwork.
- The manifest lists every transparent PNG and optional ProRes 4444 alpha MOV delivered in `最终交付/07_title_packaging/`.

## Platform And Claims

- Platform constraints are reflected in rhythm, captions, cover/first frame, and CTA.
- Claims stay inside the allowed boundaries in `spec_lock.md`.
- Prompts avoid accidental copyrighted characters, celebrity likenesses, trademark drift, and unsupported medical/financial claims.

## Deterministic Validation

When project files exist locally, run:

```bash
python3 ${SKILL_DIR}/scripts/validate_video_project.py <project_path>
```

Fix all reported errors before final delivery.
