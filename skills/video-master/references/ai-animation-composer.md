# AI Animation Composer Contract

Use this contract when a concept, science, tutorial, or data explainer should be assembled from registered code-animation templates.

## Beat brief

```json
{
  "schema_version": 1,
  "title": "Why a model hallucinates",
  "aspect_ratio": "16:9",
  "motion_standard": {
    "max_static_interval_seconds": 2.0,
    "transition_continuity": "spatial-or-semantic-linked",
    "camera_movement": "point-to-point",
    "depth_of_field": "near-sharp-far-soft",
    "flat_slide_forbidden": true,
    "element_jump_forbidden": true,
    "ambient_float": "subtle-only"
  },
  "palette": {"accent": "#FF6B45", "secondary": "#5EEAD4", "foreground": "#F7F4ED"},
  "forbidden_templates": [],
  "beats": [
    {
      "id": "hook",
      "intent": "hook",
      "duration_seconds": 4,
      "voiceover": "The spoken line.",
      "on_screen_copy": "Short visible copy.",
      "preferred_template": "number-impact",
      "variables": {"hero": "?", "label": "AI ANSWER", "value": 100, "unit": "%", "caption": "can sound certain"}
    }
  ]
}
```

Required beat fields are `id`, `intent`, `duration_seconds`, and `voiceover`. Keep IDs in lowercase hyphen-case and durations positive. `on_screen_copy`, `preferred_template`, and `variables` are optional.

When `motion_standard` is omitted, apply the defaults in `references/ai-animation-motion-grammar.md`. Preserve them in the generated plan and composer manifest so later render and QA stages use the same contract.

## Deterministic routing

- `hook`: `number-impact`, then `key-point-marker`
- `definition`: `concept-spotlight`
- `spatial`, `concept-map`, or `mechanism-map`: `spatial-camera`
- `cause` or `reasoning`: `cause-chain`
- `misconception`: `myth-fact-swap`
- `process`: `three-step-flow`
- `recap`, `action`, or `checklist`: `checklist-pop`
- `trend`: `line-chart-draw`, then `turning-point-line`
- `data`: `bar-chart-grow`, then `big-number-card`
- `comparison`: `horizontal-bar-compare`, then `stat-duel`

The preferred template wins only when it is registered and not forbidden. Otherwise choose the first allowed template in the route. Reject a beat when no allowed registered template remains; never silently invent a template.

## Outputs

Run `scripts/ai_animation/compose_explainer.py` to create:

- `animation/ai_animation_plan.json`
- `animation/composer_manifest.json`
- one project-local composition and preset per beat
- `audio/voiceover_script.md`
- `audio/tts_lines.json`
- `audio/captions.srt`

Run `scripts/ai_animation/render_composer.py` to batch-render, normalize scene durations, concatenate the timeline, optionally mux an existing voiceover track, and write:

- `最终交付/08_ai_animation/<project>-ai-animation.mp4`
- `最终交付/03_口播与字幕/中文字幕.srt`
- `qa/metadata/ai_animation_manifest.json`

Keep subtitles separate by default. Do not burn captions unless the production lock explicitly allows it.

For a confirmed Eagle image or video, add its project-local `eagle-media` composition to a generated Composer plan with `init_eagle_media_stage.py --append-to-composer`. The stage is rendered and normalized like every other Composer beat.

For a whole-film audio bed, `render_composer.py` uses an explicit `--background-music` file first, then a project `audio/background_music.*` or `audio/bgm.*`, then the first approved Eagle `background_music` asset in `sources/eagle_assets_manifest.json`. Select a particular approved Eagle track with:

```bash
python3 ${SKILL_DIR}/scripts/ai_animation/render_composer.py <project_path> --eagle-background-music-id <EAGLE_BGM_ID>
```

The renderer loops and fades the BGM to the timeline length, mixes it below voiceover, and records provenance in `qa/metadata/ai_animation_manifest.json`. It only reads the project manifest and source file; it does not call or alter Eagle during rendering.
