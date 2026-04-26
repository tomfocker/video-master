# video-master

`video-master` is a Codex skill for turning a video idea or existing campaign materials into an AI video production package: intake analysis, video-mode routing, creative strategy, script/copy/audio extraction, detailed storyboard, native image-generated storyboard frames, and copy-ready video prompts.

This repository follows the same broad shape as `ppt-master`: the product core lives in `skills/video-master/`, while repository-level docs and examples explain how to install, use, test, and evolve it.

## Repository Layout

```text
video-master/
  skills/
    video-master/
      SKILL.md
      agents/openai.yaml
      scripts/
        make_storyboard_overview.py
        make_animatic.py
        generate_voiceover_tts.py
        export_production_workbook.py
        validate_video_project.py
      references/
        audio-and-copy.md
        output-contract.md
        platform-and-model-profiles.md
        quality-check.md
        storyboard-and-video-prompts.md
        video-modes.md
  docs/
    roadmap.md
    superpowers/plans/
  examples/
    sample-request.md
  tests/
    test_validate_video_project.py
```

## Current Scope

- Classify whether the user has only an idea, partial assets, or locked brand/copy materials.
- Confirm the video mode before scriptwriting: TVC, product promo, narrative short, animation, tutorial, brand film, or ecommerce conversion.
- Confirm copy/voiceover language separately from prompt language, then lock subtitle rendering policy before final prompts.
- Design non-uniform rhythm maps instead of defaulting to equal shot durations, including rapid-cut clusters and impact camera language for high-motion subjects.
- Extract voiceover, TTS lines, captions, whole-film music direction, per-shot SFX cues, and audio-generation prompts.
- Package final `.srt` files under `最终交付/03_口播与字幕/`; English VO projects for Chinese-facing delivery can include both `英文字幕.srt` and `中文字幕.srt`.
- Use Codex native image generation for storyboard frames when requested.
- Analyze user-provided reference images or videos as `reference_style` assets, then carry safe style rules into native image generation and video prompts without copying source content.
- Produce Chinese-first final prompts for domestic Chinese video-generation workflows.
- Keep subtitles as post-production assets by default; final video prompts tell the video model not to generate or burn subtitles unless explicitly approved.
- Package final user-facing outputs under `最终交付/`.
- Generate a storyboard overview HTML and PNG contact sheet.
- Generate a packaged MP4 storyboard animatic preview with title/end cards, shot overlays, captions, and optional voiceover. The default preview profile is 12fps and follows the locked project aspect ratio with still frames kept stable; it can be skipped with `--preview-profile off`.
- Keep exact external VO copy out of final video prompts, require no per-clip background music, require per-shot SFX cues, and avoid negative-prompt fields in copy-ready video prompts.
- Generate or package a TTS voiceover track from centralized `tts_lines.json`.
- Export a production workbook for shot lists, voiceover, and handoff files.
- Validate project structure, timing, audio files, prompt language, and final delivery files with a local script.

## Install For Codex

The active local install is:

```text
~/.codex/skills/video-master
```

To update the installed copy from this repository after edits:

```bash
rsync -a --delete skills/video-master/ ~/.codex/skills/video-master/
```

## Recommended Dependencies

`video-master` works as a skill without extra packages, but this repository also includes local helper tools. Install the recommended Python dependencies for the best output quality:

```bash
python3 -m pip install -r requirements.txt
```

Recommended dependencies currently support:

- `Pillow`: storyboard contact sheets and image preparation.
- `openpyxl`: production workbook export.
- `imageio[ffmpeg]` + `numpy`: MP4 storyboard animatic preview.
- `edge-tts`: optional TTS voiceover generation.
- `pydantic`: stronger JSON schema validation.
- `pysubs2`: subtitle validation.

## Validate

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/video-master
python3 -m unittest discover -s tests
python3 -m unittest tests/test_validate_video_project.py -v
python3 -m unittest tests/test_storyboard_overview.py -v
python3 -m unittest tests/test_export_production_workbook.py -v
python3 -m unittest tests/test_make_animatic.py -v
python3 -m unittest tests/test_generate_voiceover_tts.py -v
```

For a generated project:

```bash
python3 skills/video-master/scripts/make_storyboard_overview.py video_projects/<project>
python3 skills/video-master/scripts/export_production_workbook.py video_projects/<project>
python3 skills/video-master/scripts/generate_voiceover_tts.py video_projects/<project>
python3 skills/video-master/scripts/make_animatic.py video_projects/<project>
python3 skills/video-master/scripts/validate_video_project.py video_projects/<project>
```

Animatic preview profiles:

```bash
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --preview-profile draft
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --preview-profile smooth
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --preview-profile off
```

Motion styles:

```bash
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --motion-style center-zoom
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --motion-style pan-zoom
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --motion-style none
```

## Example Invocation

```text
Use $video-master 帮我做一个 30 秒小红书美妆新品广告。
我目前只有产品想法，没有品牌素材。
视频模式倾向快节奏广告 TVC，目标模型是可灵，最终提示词请用中文。
需要剧本、配音文案、字幕、详细分镜、关键分镜图和可直接复制的视频提示词。
```
