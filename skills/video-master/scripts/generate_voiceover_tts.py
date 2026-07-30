#!/usr/bin/env python3
"""Generate or prepare a TTS voiceover track from audio/tts_lines.json."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import TTS_MANIFEST, VOICEOVER_AUDIO, VOICEOVER_AUDIO_WAV, VOICEOVER_TEXT


DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_VOXCPM2_BASE_URL = "http://100.64.0.3:8808"
DEFAULT_VOXCPM2_PERSONA = "小潮院长"
DEFAULT_VOXCPM2_CONTROL_INSTRUCTION = "中文口播，语速中等，清晰稳定，自然有表现力。"
DEFAULT_OPEN_TTS_BASE_URL = "http://h3c:8765"
DEFAULT_OPEN_TTS_MODEL = "voxcpm2"
DEFAULT_OPEN_TTS_VOICE = "default"
DEFAULT_OPEN_TTS_VOICE_PROMPT = "中文口播，语速中等，清晰稳定，自然有表现力。"
VOICE_PROFILE_RELATIVE = Path("audio") / "voice_profile.json"
VOICE_PROFILE_FIELDS = {
    "engine",
    "voice",
    "rate",
    "volume",
    "pitch",
    "tts_base_url",
    "persona",
    "control_instruction",
    "cfg_value",
    "do_normalize",
    "denoise",
    "dit_steps",
    "timeout",
    "tts_model",
    "tts_voice",
    "voice_prompt",
    "tts_language",
    "response_format",
    "tts_speed",
    "tts_pitch",
}


def load_tts_lines(project: Path) -> list[dict]:
    path = project / "audio" / "tts_lines.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing TTS lines: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("audio/tts_lines.json must be a non-empty list")
    lines = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"TTS line {index} must be an object")
        text = str(item.get("text", "")).strip()
        if not text:
            raise ValueError(f"TTS line {index} has empty text")
        lines.append({**item, "text": text})
    return lines


def build_voiceover_text(lines: list[dict]) -> str:
    chunks = []
    for line in lines:
        text = str(line["text"]).strip()
        pause = line.get("pause_after_ms")
        chunks.append(text)
        if pause:
            chunks.append("")
    return "\n".join(chunks).strip() + "\n"


def measure_audio_duration(path: Path) -> tuple[float | None, str | None]:
    """Measure the delivered file; service-reported durations can be stale or zero."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            try:
                value = float(result.stdout.strip())
                if value >= 0:
                    return value, "ffprobe"
            except ValueError:
                pass
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as handle:
                rate = handle.getframerate()
                if rate > 0:
                    return handle.getnframes() / rate, "wave"
        except (wave.Error, OSError):
            pass
    return None, None


def default_voice_options() -> dict:
    return {
        "engine": "edge-tts",
        "voice": DEFAULT_VOICE,
        "rate": "+0%",
        "volume": "+0%",
        "pitch": "+0Hz",
        "tts_base_url": None,
        "persona": DEFAULT_VOXCPM2_PERSONA,
        "control_instruction": DEFAULT_VOXCPM2_CONTROL_INSTRUCTION,
        "cfg_value": 2.0,
        "do_normalize": False,
        "denoise": False,
        "dit_steps": 10,
        "timeout": 300.0,
        "tts_model": os.environ.get("VIDEO_MASTER_OPEN_TTS_MODEL", DEFAULT_OPEN_TTS_MODEL),
        "tts_voice": os.environ.get("VIDEO_MASTER_OPEN_TTS_VOICE", DEFAULT_OPEN_TTS_VOICE),
        "voice_prompt": DEFAULT_OPEN_TTS_VOICE_PROMPT,
        "tts_language": "zh",
        "response_format": "wav",
        "tts_speed": 1.0,
        "tts_pitch": 0,
    }


def resolve_voice_profile_path(project: Path, explicit: Path | None) -> Path:
    candidate = explicit.expanduser() if explicit is not None else project / VOICE_PROFILE_RELATIVE
    if not candidate.is_absolute():
        candidate = project / candidate
    return candidate.resolve()


def load_voice_profile(project: Path, explicit: Path | None, disabled: bool) -> tuple[dict, Path | None]:
    if disabled:
        return {}, None
    path = resolve_voice_profile_path(project, explicit)
    if not path.is_file():
        if explicit is not None:
            raise FileNotFoundError(f"voice profile does not exist: {path}")
        return {}, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid voice profile JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"voice profile must be a JSON object: {path}")
    if value.get("schema_version", 1) != 1:
        raise ValueError("voice profile schema_version must be 1")
    unknown = sorted(set(value) - VOICE_PROFILE_FIELDS - {"schema_version"})
    if unknown:
        raise ValueError("voice profile contains unsupported fields: " + ", ".join(unknown))
    profile = {key: value[key] for key in VOICE_PROFILE_FIELDS if key in value}
    if "engine" in profile and profile["engine"] not in {"edge-tts", "voxcpm2", "open-tts-desktop"}:
        raise ValueError("voice profile engine must be edge-tts, voxcpm2, or open-tts-desktop")
    for key in {"cfg_value", "timeout", "tts_speed"} & set(profile):
        try:
            profile[key] = float(profile[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"voice profile {key} must be numeric") from exc
    if "dit_steps" in profile:
        try:
            profile["dit_steps"] = int(profile["dit_steps"])
        except (TypeError, ValueError) as exc:
            raise ValueError("voice profile dit_steps must be an integer") from exc
    if "tts_pitch" in profile:
        try:
            profile["tts_pitch"] = int(profile["tts_pitch"])
        except (TypeError, ValueError) as exc:
            raise ValueError("voice profile tts_pitch must be an integer") from exc
    for key in {"do_normalize", "denoise"} & set(profile):
        if not isinstance(profile[key], bool):
            raise ValueError(f"voice profile {key} must be true or false")
    return profile, path


def resolve_voice_options(project: Path, args: argparse.Namespace) -> tuple[dict, Path | None]:
    options = default_voice_options()
    profile, profile_path = load_voice_profile(project, args.voice_profile, args.no_voice_profile)
    options.update(profile)
    for key in VOICE_PROFILE_FIELDS:
        value = getattr(args, key, None)
        if value is not None:
            options[key] = value
    if options["engine"] not in {"edge-tts", "voxcpm2", "open-tts-desktop"}:
        raise ValueError("engine must be edge-tts, voxcpm2, or open-tts-desktop")
    if not str(options.get("tts_base_url") or "").strip():
        if options["engine"] == "open-tts-desktop":
            options["tts_base_url"] = os.environ.get("VIDEO_MASTER_OPEN_TTS_BASE_URL", DEFAULT_OPEN_TTS_BASE_URL)
        else:
            options["tts_base_url"] = os.environ.get("VIDEO_MASTER_VOXCPM2_BASE_URL", DEFAULT_VOXCPM2_BASE_URL)
    if float(options["timeout"]) <= 0:
        raise ValueError("tts timeout must be positive")
    if int(options["dit_steps"]) <= 0:
        raise ValueError("dit_steps must be positive")
    if not 0.25 <= float(options["tts_speed"]) <= 4:
        raise ValueError("tts_speed must be between 0.25 and 4")
    if int(options["tts_pitch"]) < -12 or int(options["tts_pitch"]) > 12:
        raise ValueError("tts_pitch must be between -12 and 12")
    if options["response_format"] not in {"wav", "mp3"}:
        raise ValueError("response_format must be wav or mp3")
    return options, profile_path


async def synthesize_with_edge_tts(text: str, voice: str, output: Path, rate: str, volume: str, pitch: str) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("edge-tts is required for synthesis. Run: python3 -m pip install -r requirements.txt") from exc

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume, pitch=pitch)
    await communicate.save(str(output))


def normalize_voxcpm2_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    if not base_url:
        raise ValueError("VoxCPM2 base URL cannot be empty")
    if base_url.endswith("/ui"):
        base_url = base_url[:-3]
    return base_url.rstrip("/")


def synthesize_with_voxcpm2(
    text: str,
    output: Path,
    *,
    base_url: str,
    persona: str,
    control_instruction: str,
    cfg_value: float,
    do_normalize: bool,
    denoise: bool,
    dit_steps: int,
    api_key: str | None,
    timeout: float,
) -> dict:
    normalized_base_url = normalize_voxcpm2_base_url(base_url)
    endpoint = f"{normalized_base_url}/api/tts"
    payload = {
        "text": text,
        "persona": persona,
        "control_instruction": control_instruction,
        "cfg_value": cfg_value,
        "do_normalize": do_normalize,
        "denoise": denoise,
        "dit_steps": dit_steps,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            audio = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"VoxCPM2 TTS request failed with HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach VoxCPM2 TTS service at {endpoint}: {exc.reason}") from exc
    if not audio:
        raise RuntimeError(f"VoxCPM2 TTS service returned an empty response from {endpoint}")
    output.write_bytes(audio)
    return {
        "base_url": normalized_base_url,
        "api_endpoint": endpoint,
        "content_type": content_type,
        "byte_count": len(audio),
    }


def normalize_open_tts_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    if not base_url:
        raise ValueError("Open TTS Desktop base URL cannot be empty")
    return base_url


def read_json_response(response: object, endpoint: str) -> object:
    try:
        raw = response.read()  # type: ignore[attr-defined]
        return json.loads(raw.decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Open TTS Desktop returned invalid JSON from {endpoint}") from exc


def synthesize_with_open_tts_desktop(
    text: str,
    output: Path,
    *,
    base_url: str,
    model: str,
    voice: str,
    voice_prompt: str,
    language: str,
    response_format: str,
    speed: float,
    pitch: int,
    cfg_value: float,
    do_normalize: bool,
    denoise: bool,
    dit_steps: int,
    timeout: float,
) -> dict:
    normalized_base_url = normalize_open_tts_base_url(base_url)
    endpoint = f"{normalized_base_url}/v1/audio/speech"
    voices = fetch_open_tts_voice_records(base_url=normalized_base_url, timeout=timeout)
    selected_voice = next((item for item in voices if str(item.get("id") or "") == voice), None)
    if selected_voice is None:
        raise RuntimeError(f"Open TTS Desktop does not have the requested voice: {voice}")
    authorization_status = str(selected_voice.get("authorization_status") or "")
    if authorization_status not in {"authorized", "built_in"}:
        raise RuntimeError(
            f"Open TTS Desktop voice is not approved for use: {voice} ({authorization_status or 'unknown'})"
        )
    capabilities = get_open_tts_model_capabilities(
        base_url=normalized_base_url,
        model=model,
        timeout=timeout,
    )
    payload = {
        "model": model,
        "input": text,
        "voice_prompt": voice_prompt or None,
        "language": language or None,
        "response_format": response_format,
        "speed": speed,
        "pitch": pitch,
        "cfg": cfg_value,
        "inference_steps": dit_steps,
        "normalize": do_normalize,
        "denoise": denoise,
        "stream": False,
    }
    # Route an approved managed voice according to the selected model's actual
    # request capabilities. VoxCPM2 accepts its managed reference fields, not
    # a `voice` ID; do not expose those reference paths in the project profile
    # or manifest.
    voice_parameter_included = False
    voice_routing = "built_in_default"
    if voice != DEFAULT_OPEN_TTS_VOICE and "voice" in capabilities:
        payload["voice"] = voice
        voice_parameter_included = True
        voice_routing = "managed_voice_id"
    elif voice != DEFAULT_OPEN_TTS_VOICE and "reference_audio" in capabilities:
        reference_audio = str(selected_voice.get("reference_audio") or "").strip()
        if not reference_audio:
            raise RuntimeError(
                f"Open TTS Desktop voice {voice} has no managed reference for model {model}; "
                "select an authorized voice with a managed reference or a model that accepts voice IDs"
            )
        payload["reference_audio"] = reference_audio
        reference_text = str(selected_voice.get("reference_text") or "").strip()
        if reference_text:
            payload["reference_text"] = reference_text
        voice_routing = "managed_reference"
    elif voice != DEFAULT_OPEN_TTS_VOICE:
        raise RuntimeError(
            f"Open TTS Desktop model {model} cannot use managed voice {voice}; "
            "its request capabilities include neither voice nor reference_audio"
        )
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = read_json_response(response, endpoint)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Open TTS Desktop request failed with HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Open TTS Desktop service at {endpoint}: {exc.reason}") from exc
    if not isinstance(result, dict) or not isinstance(result.get("audio_url"), str) or not result["audio_url"]:
        raise RuntimeError(f"Open TTS Desktop response from {endpoint} is missing audio_url")
    # Open TTS Desktop may return an output filename containing Chinese text.
    # Quote only the URL path so urllib can make a standards-compliant HTTP
    # request while preserving any query string the service may provide.
    returned_audio_url = str(result["audio_url"])
    parsed_audio_url = urllib.parse.urlsplit(returned_audio_url)
    encoded_audio_url = urllib.parse.urlunsplit(
        (
            parsed_audio_url.scheme,
            parsed_audio_url.netloc,
            urllib.parse.quote(parsed_audio_url.path, safe="/%"),
            parsed_audio_url.query,
            parsed_audio_url.fragment,
        )
    )
    audio_url = urllib.parse.urljoin(f"{normalized_base_url}/", encoded_audio_url)
    try:
        with urllib.request.urlopen(audio_url, timeout=timeout) as response:
            audio = response.read()
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Open TTS Desktop audio download failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to download Open TTS Desktop audio at {audio_url}: {exc.reason}") from exc
    if not audio:
        raise RuntimeError(f"Open TTS Desktop returned empty audio from {audio_url}")
    output.write_bytes(audio)
    return {
        "base_url": normalized_base_url,
        "api_endpoint": endpoint,
        "audio_url": audio_url,
        "content_type": content_type,
        "byte_count": len(audio),
        "model": str(result.get("model") or model),
        "sample_rate": result.get("sample_rate"),
        "duration_seconds": result.get("duration_seconds"),
        "voice_authorization_status": authorization_status,
        "voice_parameter_included": voice_parameter_included,
        "voice_routing": voice_routing,
    }


def fetch_open_tts_voice_records(*, base_url: str, timeout: float) -> list[dict]:
    normalized_base_url = normalize_open_tts_base_url(base_url)
    endpoint = f"{normalized_base_url}/v1/tts/voices"
    try:
        with urllib.request.urlopen(endpoint, timeout=timeout) as response:
            value = read_json_response(response, endpoint)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Open TTS Desktop voice list failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Open TTS Desktop service at {endpoint}: {exc.reason}") from exc
    if not isinstance(value, list):
        raise RuntimeError(f"Open TTS Desktop returned an invalid voice list from {endpoint}")
    return [item for item in value if isinstance(item, dict)]


def list_open_tts_voices(*, base_url: str, timeout: float) -> list[dict]:
    records = fetch_open_tts_voice_records(base_url=base_url, timeout=timeout)
    return [
        {
            "id": str(item.get("id") or ""),
            "name": str(item.get("name") or ""),
            "authorization_status": str(item.get("authorization_status") or ""),
        }
        for item in records
    ]


def get_open_tts_model_capabilities(*, base_url: str, model: str, timeout: float) -> set[str]:
    normalized_base_url = normalize_open_tts_base_url(base_url)
    endpoint = f"{normalized_base_url}/v1/tts/models"
    try:
        with urllib.request.urlopen(endpoint, timeout=timeout) as response:
            value = read_json_response(response, endpoint)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Open TTS Desktop model list failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Open TTS Desktop model list at {endpoint}: {exc.reason}") from exc
    if not isinstance(value, list):
        raise RuntimeError(f"Open TTS Desktop returned an invalid model list from {endpoint}")
    selected_model = next(
        (item for item in value if isinstance(item, dict) and str(item.get("id") or "") == model),
        None,
    )
    if selected_model is None:
        raise RuntimeError(f"Open TTS Desktop does not have the requested model: {model}")
    raw_capabilities = selected_model.get("request_capabilities")
    if not isinstance(raw_capabilities, list):
        return set()
    return {str(item) for item in raw_capabilities if isinstance(item, str)}


def write_manifest(
    path: Path,
    *,
    source: Path,
    output: Path,
    text_path: Path,
    voice: str,
    engine: str,
    line_count: int,
    dry_run: bool,
    details: dict | None = None,
) -> None:
    manifest = {
        "source": str(source.resolve()),
        "output": str(output.resolve()),
        "text_path": str(text_path.resolve()),
        "voice": voice,
        "line_count": line_count,
        "dry_run": dry_run,
        "engine": engine,
    }
    if details:
        manifest.update(details)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def generate_voiceover(
    project: Path,
    *,
    engine: str = "edge-tts",
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    tts_base_url: str = DEFAULT_VOXCPM2_BASE_URL,
    persona: str = DEFAULT_VOXCPM2_PERSONA,
    control_instruction: str = DEFAULT_VOXCPM2_CONTROL_INSTRUCTION,
    cfg_value: float = 2.0,
    do_normalize: bool = False,
    denoise: bool = False,
    dit_steps: int = 10,
    api_key: str | None = None,
    timeout: float = 300.0,
    dry_run: bool = False,
    output: Path | None = None,
    voice_profile: Path | None = None,
    tts_model: str = DEFAULT_OPEN_TTS_MODEL,
    tts_voice: str = DEFAULT_OPEN_TTS_VOICE,
    voice_prompt: str = DEFAULT_OPEN_TTS_VOICE_PROMPT,
    tts_language: str = "zh",
    response_format: str = "wav",
    tts_speed: float = 1.0,
    tts_pitch: int = 0,
) -> dict:
    project = project.resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"project directory does not exist: {project}")
    if engine not in {"edge-tts", "voxcpm2", "open-tts-desktop"}:
        raise ValueError("engine must be edge-tts, voxcpm2, or open-tts-desktop")

    if output:
        output_path = output
    elif engine in {"voxcpm2", "open-tts-desktop"} and response_format == "wav":
        output_path = project / VOICEOVER_AUDIO_WAV
    else:
        output_path = project / VOICEOVER_AUDIO
    text_path = project / VOICEOVER_TEXT
    manifest_path = project / TTS_MANIFEST
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    lines = load_tts_lines(project)
    text = build_voiceover_text(lines)
    text_path.write_text(text, encoding="utf-8")

    resolved_voice = voice
    details = {}
    if engine == "voxcpm2":
        base_url = normalize_voxcpm2_base_url(tts_base_url)
        resolved_voice = persona
        details = {
            "persona": persona,
            "base_url": base_url,
            "api_endpoint": f"{base_url}/api/tts",
            "control_instruction": control_instruction,
            "cfg_value": cfg_value,
            "do_normalize": do_normalize,
            "denoise": denoise,
            "dit_steps": dit_steps,
            "output_format": output_path.suffix.lstrip(".") or "wav",
        }
    elif engine == "open-tts-desktop":
        base_url = normalize_open_tts_base_url(tts_base_url)
        resolved_voice = tts_voice or DEFAULT_OPEN_TTS_VOICE
        details = {
            "base_url": base_url,
            "api_endpoint": f"{base_url}/v1/audio/speech",
            "model": tts_model,
            "voice_id": resolved_voice,
            "voice_prompt": voice_prompt,
            "language": tts_language,
            "response_format": response_format,
            "speed": tts_speed,
            "pitch": tts_pitch,
            "cfg_value": cfg_value,
            "do_normalize": do_normalize,
            "denoise": denoise,
            "dit_steps": dit_steps,
        }
    if voice_profile is not None:
        details["voice_profile"] = str(voice_profile.resolve())

    if not dry_run:
        if engine == "voxcpm2":
            details.update(
                synthesize_with_voxcpm2(
                    text,
                    output_path,
                    base_url=tts_base_url,
                    persona=persona,
                    control_instruction=control_instruction,
                    cfg_value=cfg_value,
                    do_normalize=do_normalize,
                    denoise=denoise,
                    dit_steps=dit_steps,
                    api_key=api_key or os.environ.get("VOXCPM_API_KEY"),
                    timeout=timeout,
                )
            )
        elif engine == "open-tts-desktop":
            details.update(
                synthesize_with_open_tts_desktop(
                    text,
                    output_path,
                    base_url=tts_base_url,
                    model=tts_model,
                    voice=tts_voice,
                    voice_prompt=voice_prompt,
                    language=tts_language,
                    response_format=response_format,
                    speed=tts_speed,
                    pitch=tts_pitch,
                    cfg_value=cfg_value,
                    do_normalize=do_normalize,
                    denoise=denoise,
                    dit_steps=dit_steps,
                    timeout=timeout,
                )
            )
        else:
            asyncio.run(synthesize_with_edge_tts(text, voice, output_path, rate, volume, pitch))
        measured_duration, measurement_source = measure_audio_duration(output_path)
        if measured_duration is not None:
            details["audio_duration_seconds"] = measured_duration
            details["audio_duration_source"] = measurement_source

    manifest = write_manifest(
        manifest_path,
        source=project / "audio" / "tts_lines.json",
        output=output_path,
        text_path=text_path,
        voice=resolved_voice,
        engine=engine,
        line_count=len(lines),
        dry_run=dry_run,
        details=details,
    )
    return {
        "engine": engine,
        "dry_run": dry_run,
        "output": output_path,
        "text_path": text_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a TTS voiceover from audio/tts_lines.json.")
    parser.add_argument("--engine", choices=["edge-tts", "voxcpm2", "open-tts-desktop"], help="TTS engine to use")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument("--voice", help="edge-tts voice name")
    parser.add_argument("--rate", help="edge-tts rate, e.g. +8%% or -5%%")
    parser.add_argument("--volume", help="edge-tts volume, e.g. +0%%")
    parser.add_argument("--pitch", help="edge-tts pitch, e.g. +0Hz")
    parser.add_argument(
        "--tts-base-url",
        help="VoxCPM2 service base URL; /ui suffix is accepted and normalized",
    )
    parser.add_argument("--persona", help="VoxCPM2 persona name")
    parser.add_argument(
        "--control-instruction",
        help="VoxCPM2 voice control instruction",
    )
    parser.add_argument("--cfg-value", type=float, help="VoxCPM2 CFG value")
    parser.add_argument("--normalize", action="store_true", default=None, help="Enable VoxCPM2 text normalization")
    parser.add_argument("--no-normalize", action="store_false", dest="do_normalize", default=None, help="Disable VoxCPM2 text normalization")
    parser.add_argument("--denoise", action="store_true", default=None, help="Enable VoxCPM2 reference denoise")
    parser.add_argument("--no-denoise", action="store_false", dest="denoise", default=None, help="Disable VoxCPM2 reference denoise")
    parser.add_argument("--dit-steps", type=int, help="VoxCPM2 diffusion steps")
    parser.add_argument("--api-key", help="Optional VoxCPM2 API key; defaults to VOXCPM_API_KEY")
    parser.add_argument("--tts-timeout", type=float, dest="timeout", help="VoxCPM2 request timeout in seconds")
    parser.add_argument("--voice-profile", type=Path, help="Optional JSON voice profile; defaults to audio/voice_profile.json when present")
    parser.add_argument("--no-voice-profile", action="store_true", help="Ignore any project voice profile")
    parser.add_argument("--tts-model", dest="tts_model", help="Open TTS Desktop model ID, e.g. voxcpm2")
    parser.add_argument("--tts-voice", dest="tts_voice", help="Open TTS Desktop managed voice ID")
    parser.add_argument("--voice-prompt", help="Open TTS Desktop voice/control prompt")
    parser.add_argument("--tts-language", help="Open TTS Desktop language hint, e.g. zh")
    parser.add_argument("--response-format", choices=["wav", "mp3"], help="Open TTS Desktop output format")
    parser.add_argument("--tts-speed", type=float, help="Open TTS Desktop speed, from 0.25 to 4")
    parser.add_argument("--tts-pitch", type=int, help="Open TTS Desktop pitch, from -12 to 12")
    parser.add_argument("--list-open-tts-voices", action="store_true", help="List approved managed voices without synthesizing")
    parser.add_argument("--dry-run", action="store_true", help="Write text/manifest without calling TTS")
    parser.add_argument("-o", "--output", type=Path, help="Output audio path")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not project.is_dir():
        print(f"ERROR: project directory does not exist: {project}")
        return 2

    try:
        options, voice_profile = resolve_voice_options(project, args)
        if args.list_open_tts_voices:
            voices = list_open_tts_voices(base_url=options["tts_base_url"], timeout=float(options["timeout"]))
            print(json.dumps({"base_url": normalize_open_tts_base_url(options["tts_base_url"]), "voices": voices}, ensure_ascii=False, indent=2))
            return 0
        result = generate_voiceover(
            project,
            engine=options["engine"],
            voice=options["voice"],
            rate=options["rate"],
            volume=options["volume"],
            pitch=options["pitch"],
            tts_base_url=options["tts_base_url"],
            persona=options["persona"],
            control_instruction=options["control_instruction"],
            cfg_value=float(options["cfg_value"]),
            do_normalize=bool(options["do_normalize"]),
            denoise=bool(options["denoise"]),
            dit_steps=int(options["dit_steps"]),
            api_key=args.api_key,
            timeout=float(options["timeout"]),
            dry_run=args.dry_run,
            output=args.output,
            voice_profile=voice_profile,
            tts_model=options["tts_model"],
            tts_voice=options["tts_voice"],
            voice_prompt=options["voice_prompt"],
            tts_language=options["tts_language"],
            response_format=options["response_format"],
            tts_speed=float(options["tts_speed"]),
            tts_pitch=int(options["tts_pitch"]),
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Voiceover text: {result['text_path']}")
    if args.dry_run:
        print(f"TTS manifest: {result['manifest_path']}")
    else:
        print(f"Voiceover audio: {result['output']}")
        print(f"TTS manifest: {result['manifest_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
