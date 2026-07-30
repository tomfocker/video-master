# Open TTS Desktop Character Voice

Use the Open TTS Desktop service at `http://h3c:8765` when a video project needs a repeatable narrator or character voice. It exposes an OpenAI-compatible `POST /v1/audio/speech` endpoint and returns an `audio_url`; Video Master downloads that audio into the project delivery folder. The full Tailnet domain can be used as a fallback only after its API route is verified.

## Safe selection

List only minimal voice metadata before choosing a role:

```bash
python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project_path> --engine open-tts-desktop --list-open-tts-voices
```

Use only voices whose service status is `authorized` or `built_in`. Do not create a voice, upload a reference clip, or use a real person's voice without explicit user authorization.

## Model-aware role routing

`tts_voice` is a stable managed-role ID, not a promise that every model accepts a `voice` field. Before synthesis, the renderer reads `/v1/tts/models` and routes an approved role according to the selected model's `request_capabilities`:

- `built_in` `default`: omit `voice`; the VoxCPM2 adapter selects its built-in narrator.
- Models with `voice`: send the authorized managed-role ID as `voice`.
- Models with `reference_audio` but no `voice`: resolve the selected role's service-managed reference and transcript in memory, then send those fields. VoxCPM2 currently uses this route.
- Neither capability: stop with an actionable error. Do not silently fall back to a random voice.

The managed reference path and transcript must never be written to `audio/voice_profile.json`, `tts_manifest.json`, logs, or delivery files. The manifest records only `voice`, `voice_authorization_status`, and `voice_routing`.

## Timing contract

Open TTS Desktop returns an `audio_url` and a service `duration_seconds`; it does not currently return word, sentence, or phoneme timestamps. The renderer therefore measures the downloaded file and records `audio_duration_seconds` plus `audio_duration_source` in `qa/metadata/tts_manifest.json`. Use that measured duration to set the final timeline; do not assume `audio/tts_lines.json` start/end values remain correct after synthesis.

When subtitles, scene changes, or kinetic typography must follow individual words or phrases, run an approved forced-alignment step against the locked script and delivered audio. Save its reviewable result as `audio/voice_alignment.json` with cue text, `start_seconds`, `end_seconds`, and source-audio checksum. Never fabricate word timings from planned cues or from the service job's wall-clock timestamps.

## Persistent project profile

Store the approved role configuration in `audio/voice_profile.json`. Do not store API keys or source-audio paths there.

```json
{
  "schema_version": 1,
  "engine": "open-tts-desktop",
  "tts_base_url": "http://h3c:8765",
  "tts_model": "voxcpm2",
  "tts_voice": "<authorized-voice-id>",
  "voice_prompt": "中文角色旁白，语速中等，清晰自然。",
  "tts_language": "zh",
  "response_format": "wav",
  "tts_speed": 1.0,
  "tts_pitch": 0,
  "cfg_value": 2.0,
  "dit_steps": 10,
  "do_normalize": false,
  "denoise": false
}
```

Generate from `audio/tts_lines.json` with the saved profile:

```bash
python3 ${SKILL_DIR}/scripts/generate_voiceover_tts.py <project_path>
```

The script checks the selected voice status and selected model capabilities, requests `POST /v1/audio/speech`, downloads the returned audio URL, and records model, voice ID, authorization status, routing mode, audio URL, and profile path in `qa/metadata/tts_manifest.json`. It URL-encodes non-ASCII output filenames before downloading them.

For multiple characters, make one profile and output file per approved role; do not merge different character lines into one synthesis request.
