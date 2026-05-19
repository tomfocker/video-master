#!/usr/bin/env python3
"""Generate or prepare a TTS voiceover track from audio/tts_lines.json."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import TTS_MANIFEST, VOICEOVER_AUDIO, VOICEOVER_AUDIO_WAV, VOICEOVER_TEXT


DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_VOXCPM2_BASE_URL = "http://100.64.0.3:8808"
DEFAULT_VOXCPM2_PERSONA = "小潮院长"
DEFAULT_VOXCPM2_CONTROL_INSTRUCTION = "中文口播，语速中等，清晰稳定，自然有表现力。"


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
) -> dict:
    project = project.resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"project directory does not exist: {project}")
    if engine not in {"edge-tts", "voxcpm2"}:
        raise ValueError("engine must be edge-tts or voxcpm2")

    if output:
        output_path = output
    elif engine == "voxcpm2":
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
        else:
            asyncio.run(synthesize_with_edge_tts(text, voice, output_path, rate, volume, pitch))

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
    parser.add_argument("--engine", choices=["edge-tts", "voxcpm2"], default="edge-tts", help="TTS engine to use")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts voice name")
    parser.add_argument("--rate", default="+0%", help="edge-tts rate, e.g. +8%% or -5%%")
    parser.add_argument("--volume", default="+0%", help="edge-tts volume, e.g. +0%%")
    parser.add_argument("--pitch", default="+0Hz", help="edge-tts pitch, e.g. +0Hz")
    parser.add_argument(
        "--tts-base-url",
        default=os.environ.get("VIDEO_MASTER_VOXCPM2_BASE_URL", DEFAULT_VOXCPM2_BASE_URL),
        help="VoxCPM2 service base URL; /ui suffix is accepted and normalized",
    )
    parser.add_argument("--persona", default=DEFAULT_VOXCPM2_PERSONA, help="VoxCPM2 persona name")
    parser.add_argument(
        "--control-instruction",
        default=DEFAULT_VOXCPM2_CONTROL_INSTRUCTION,
        help="VoxCPM2 voice control instruction",
    )
    parser.add_argument("--cfg-value", type=float, default=2.0, help="VoxCPM2 CFG value")
    parser.add_argument("--normalize", action="store_true", help="Enable VoxCPM2 text normalization")
    parser.add_argument("--denoise", action="store_true", help="Enable VoxCPM2 reference denoise")
    parser.add_argument("--dit-steps", type=int, default=10, help="VoxCPM2 diffusion steps")
    parser.add_argument("--api-key", help="Optional VoxCPM2 API key; defaults to VOXCPM_API_KEY")
    parser.add_argument("--tts-timeout", type=float, default=300.0, help="VoxCPM2 request timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Write text/manifest without calling TTS")
    parser.add_argument("-o", "--output", type=Path, help="Output audio path")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not project.is_dir():
        print(f"ERROR: project directory does not exist: {project}")
        return 2

    try:
        result = generate_voiceover(
            project,
            engine=args.engine,
            voice=args.voice,
            rate=args.rate,
            volume=args.volume,
            pitch=args.pitch,
            tts_base_url=args.tts_base_url,
            persona=args.persona,
            control_instruction=args.control_instruction,
            cfg_value=args.cfg_value,
            do_normalize=args.normalize,
            denoise=args.denoise,
            dit_steps=args.dit_steps,
            api_key=args.api_key,
            timeout=args.tts_timeout,
            dry_run=args.dry_run,
            output=args.output,
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
