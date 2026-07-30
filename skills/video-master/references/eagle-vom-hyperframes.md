# Eagle + VOM + HyperFrames Full Chain

Use this route when a HyperFrames project needs an approved Eagle music bed and an Open TTS Desktop narrator or character voice.

## Preconditions

- Eagle is running with its official MCP server at `http://127.0.0.1:41596/mcp`.
- Open TTS Desktop is reachable at `http://h3c:8765`; use the Tailnet domain only after its APIs are verified.
- The selected Eagle asset has a confirmed role and the selected TTS voice is `built_in` or `authorized`.
- Never create, upload, or change an Eagle item or a voice-library entry during this route.

## Execution

1. Create the Composer plan first; it creates `audio/tts_lines.json` and the canonical timing.
2. Inspect role IDs without exposing reference paths:

   ```bash
   python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project> --engine open-tts-desktop --list-open-tts-voices
   ```

3. Put only `tts_base_url`, `tts_model`, `tts_voice`, direction, and rendering settings in `audio/voice_profile.json`. Then generate:

   ```bash
   python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project> --tts-timeout 180
   ```

4. Confirm `qa/metadata/tts_manifest.json` has an approved status, a non-empty `voice_routing`, a measured `audio_duration_seconds`, and an existing final WAV or MP3 under `最终交付/03_口播与字幕/`. Update the Composer timeline to that real duration before its final render.
5. After the user confirms the selected Eagle track, record a project-local copy without changing Eagle:

   ```bash
   python3 ${SKILL_DIR}/scripts/eagle_asset_intake.py <project> --item-id <EAGLE_ITEM_ID> --role background_music --copy
   ```

6. Render with the explicit approved item ID:

   ```bash
   python3 ${SKILL_DIR}/scripts/ai_animation/render_composer.py <project> --eagle-background-music-id <EAGLE_ITEM_ID> --background-music-volume 0.18
   ```

7. Verify `qa/metadata/ai_animation_manifest.json`: `voiceover` must be non-empty, `background_music_source.type` must be `eagle_manifest`, and the final MP4 must have H.264 video plus AAC audio. Run the project validator before handoff.

## Failure Prevention

- Do not pass `voice=default` to the current VoxCPM2 adapter; it rejects that field. The renderer omits it automatically.
- Do not pass an authorized character ID straight to VoxCPM2. The renderer uses the model's capability list and its managed reference route when required.
- Do not store or report managed reference-audio paths or transcripts. The service resolves them transiently.
- Treat a returned `audio_url` as a URL, not a filesystem path. The renderer encodes Chinese filenames before downloading.
- An authorized-role synthesis can exceed one minute on the local service. Use `--tts-timeout 180`; when an orchestration shell has a shorter wait limit, verify the finished `tts_manifest.json` and final WAV/MP3 before declaring the synthesis failed.
- Do not let a fixed visual plan truncate a longer delivered narration. The returned audio has total duration but no word timestamps; use forced alignment when scene cuts or kinetic copy must follow words.
- Composer discovers canonical final narration at `最终交付/03_口播与字幕/口播音频.wav` or `.mp3`; do not assume only `audio/voiceover.*` is mixed.
- HyperFrames uses a stable user-scoped npm cache automatically. Override it only with `VIDEO_MASTER_NPM_CACHE` when a managed environment requires a different location.
