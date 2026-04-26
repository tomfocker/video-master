# Roadmap

## Phase 1: Skill Core

- Define the serial workflow from requirement intake to final production package.
- Provide output contracts for brief, script, shot list, storyboard manifest, and prompts.
- Use native image generation for storyboard frames when available.

## Phase 2: V2 Production Workflow

- Add input readiness routing: `idea-only`, `asset-assisted`, `material-locked`.
- Add video mode confirmation: TVC, product promo short, narrative short, animation, tutorial/explainer, brand film, ecommerce conversion short.
- Add rhythm maps so shot durations follow narrative, director intent, platform needs, and high-motion rapid-cut clusters instead of equal segmenting.
- Add centralized audio/copy files for TTS, captions, whole-film music direction, per-shot SFX, and audio prompts.
- Add final user-facing `最终交付/` with copy-ready prompts, storyboard frames, audio/caption files, overview, preview, and workbook.
- Add Chinese-first final prompt rules for domestic video model workflows.
- Add deterministic project validation.
- Declare optional/recommended local dependencies for best-effort media tooling.
- Add production workbook export.
- Add packaged storyboard animatic preview generation with title/end cards, overlays, captions, subtle motion, and optional voiceover.
- Add optional TTS voiceover generation from centralized `tts_lines.json`.

## Phase 3: Production Tooling

- Add a project initializer script.
- Add model-specific prompt exporters for 可灵、即梦、海螺、Vidu、Sora、Runway、Pika.
- Add brand/product asset ingestion helpers.
- Add music/SFX mixing for animatic previews after the cue-sheet workflow is stable.
- Add curated example projects under `examples/`.
- Add a lightweight UI or CLI if repeated editing and preview workflows need it.
