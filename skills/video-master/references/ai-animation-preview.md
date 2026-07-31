# AI Animation Preview Contract

Use this route for “做个样片”, “试试看”, “直接看效果”, or an explicit AI 一站动画 request. It is the default for deterministic HyperFrames concept, science, and typography tests when a complete production package was not requested.

## Minimal contract

Create only:

```text
animation/
  preview_spec.json
  ai_animation_plan.json
  compositions/ or index.html
  renders/<project>-preview.mp4
audio/
  voiceover_script.md                 # only when narration is used
  voice_alignment.json                # only when word/phrase sync is requested
  tts_manifest.json                   # only when OpenTTS is used
qa/metadata/
  ai_animation_manifest.json
```

`animation/preview_spec.json` must set `workflow_profile: ai-animation-preview`, capture the requested duration, format, visual intent, selected modules, and whether narration/alignment are enabled. Preserve real TTS alignment without modifying timestamps.

Do not create storyboard frames, image/video prompt packs, an animatic, a workbook, `最终交付/`, or main-flow package metadata. Do not run `validate_video_project.py`.

## Execution

1. Use a registered module whenever one fits; record any project-local prototype explicitly in the plan.
2. If narration is requested, generate it with the authorized voice workflow. For word or phrase sync, request service-returned alignment and use its `start_seconds` as the render trigger.
3. Use the motion grammar: a meaningful change within two seconds, continuous point-to-point camera movement, near-sharp/far-soft depth cues, spatial or semantic transition continuity, subtle-only ambient float, no flat slides, and no element jumps.
4. Run HyperFrames lint/check, render the MP4, mux audio when applicable, and write `qa/metadata/ai_animation_manifest.json` with the actual source, output, duration, and audio/alignment provenance.
5. Run `scripts/ai_animation/validate_preview.py <project_path>` and immediately show the final MP4. Perform optional contact sheets or conversion into the full production flow only after the user asks.

## Preview validator contract

The plan must set `enabled: true`, `engine: hyperframes`, `execution_mode: hyperframes | hybrid`, and have at least one existing composition source with a positive duration. The manifest must set `ai_animation: true`, identify HyperFrames, and list each rendered output. The validator checks that the output contains a video stream and that its duration is within 0.5 seconds of the declared composition duration. When `timing_policy` is `service-returned-start-seconds`, it also checks that the alignment file exists and contains ordered numeric token boundaries. Zero-duration tokens are valid source data and must not be rewritten.
