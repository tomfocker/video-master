# Video Master V2 Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `video-master` from a first-pass video package generator into a routed production workflow that handles input readiness, video mode, rhythm, audio, deliverables, Chinese-first model environments, and validation.

**Architecture:** Keep the installable skill self-contained under `skills/video-master/`. Put durable workflow rules in `SKILL.md`, detailed schemas and model/platform guidance in `references/`, and deterministic project checks in `scripts/validate_video_project.py`. Repository docs and examples explain how to use the upgraded workflow without bloating skill context.

**Tech Stack:** Markdown skill files, YAML frontmatter, Python 3 standard library, `unittest`, Codex skill validator.

---

### Task 1: Add Project Validator

**Files:**
- Create: `tests/test_validate_video_project.py`
- Create: `skills/video-master/scripts/validate_video_project.py`

- [x] **Step 1: Write failing validator tests**

Create `tests/test_validate_video_project.py` with fixtures that assert the validator fails an evenly timed ad sequence and passes a v2-shaped project with deliverables, audio files, Chinese prompt language, and non-uniform timing.

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_validate_video_project.py -v`

Expected: FAIL or ERROR because `skills/video-master/scripts/validate_video_project.py` does not exist yet.

- [x] **Step 3: Implement minimal validator**

Create `skills/video-master/scripts/validate_video_project.py` using only the Python standard library. It must check required files, JSON validity, total duration, generated frame existence, non-uniform rhythm warning/failure for advertising modes, deliverables presence, audio extraction files, and prompt language metadata.

- [x] **Step 4: Run tests to verify pass**

Run: `python3 -m unittest tests/test_validate_video_project.py -v`

Expected: PASS.

### Task 2: Upgrade Core Skill Workflow

**Files:**
- Modify: `skills/video-master/SKILL.md`

- [x] **Step 1: Replace v1 pipeline with v2 pipeline**

Add explicit phases:
Input Readiness Check, Video Mode Confirmation, Production Lock, Creative Strategy, Script/Copy/Audio Extraction, Shot List/Storyboard Plan, Native Storyboard Images, Video Prompt Generation, Deliverables, QA.

- [x] **Step 2: Add routing rules**

Define `idea-only`, `asset-assisted`, and `material-locked` input modes. Define video modes: fast-paced TVC, product promo short, narrative short, animation, tutorial/explainer, brand film, ecommerce conversion short.

- [x] **Step 3: Add output language and domestic model guidance**

Default final prompts to the user's language. For Chinese domestic video models, default final prompt language to Chinese with optional English camera/style tags.

### Task 3: Expand Output Contract

**Files:**
- Modify: `skills/video-master/references/output-contract.md`

- [x] **Step 1: Add v2 project structure**

Add `strategy/`, `audio/`, `deliverables/`, `references/`, and `qa/` directories.

- [x] **Step 2: Add schemas**

Document `input_readiness.md`, `video_mode.md`, `creative_strategy.md`, `rhythm_map.md`, `voiceover_script.md`, `tts_lines.json`, `captions.srt`, `music_sfx_cue_sheet.md`, `audio_generation_prompt.md`, and deliverable file formats.

### Task 4: Add Prompt, Mode, Platform, And Audio References

**Files:**
- Modify: `skills/video-master/references/storyboard-and-video-prompts.md`
- Create: `skills/video-master/references/video-modes.md`
- Create: `skills/video-master/references/platform-and-model-profiles.md`
- Create: `skills/video-master/references/audio-and-copy.md`

- [x] **Step 1: Upgrade prompt patterns**

Add Chinese-first final prompt blocks, copy-ready prompt format, reference frame rules, and prompt dialect selection.

- [x] **Step 2: Add mode rules**

Define how each video mode affects structure, shot count, shot duration, image coverage, audio strategy, and deliverables.

- [x] **Step 3: Add platform/model rules**

Define platform constraints and model profile guidance for model-agnostic, domestic Chinese models, Sora-style, Runway/Pika-style, and Kling-style.

- [x] **Step 4: Add audio/copy rules**

Define how to extract VO, captions, TTS lines, SFX cues, music direction, CTA copy, and slogan options.

### Task 5: Upgrade QA

**Files:**
- Modify: `skills/video-master/references/quality-check.md`

- [x] **Step 1: Add v2 QA categories**

Check rhythm, audio extraction, deliverables, prompt language, platform constraints, claims safety, and traceability.

- [x] **Step 2: Reference deterministic validator**

Instruct agents to run `scripts/validate_video_project.py <project_path>` when project files are present.

### Task 6: Update Repository Docs And Examples

**Files:**
- Modify: `README.md`
- Modify: `docs/roadmap.md`
- Modify: `examples/sample-request.md`
- Modify: `skills/video-master/agents/openai.yaml`

- [x] **Step 1: Document v2 usage**

Explain the v2 intake, routing, deliverables, audio, and Chinese-first prompt behavior.

- [x] **Step 2: Update sample request**

Make the example include input readiness, video mode, target platform/model, and available assets.

### Task 7: Sync Installed Skill And Verify

**Files:**
- Copy updated `skills/video-master/` to `~/.codex/skills/video-master/`

- [x] **Step 1: Validate repository skill**

Run: `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/video-master`

Expected: `Skill is valid!`

- [x] **Step 2: Validate installed skill**

Run: `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/video-master`

Expected: `Skill is valid!`

- [x] **Step 3: Run project validator tests**

Run: `python3 -m unittest tests/test_validate_video_project.py -v`

Expected: PASS.

- [x] **Step 4: Check repository status**

Run: `git status --short`

Expected: shows intentional v2 changes only.
