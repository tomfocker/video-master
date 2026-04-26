#!/usr/bin/env python3
"""Generate or prepare a TTS voiceover track from audio/tts_lines.json."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import TTS_MANIFEST, VOICEOVER_AUDIO, VOICEOVER_TEXT


DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


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


def write_manifest(
    path: Path,
    *,
    source: Path,
    output: Path,
    text_path: Path,
    voice: str,
    line_count: int,
    dry_run: bool,
) -> None:
    manifest = {
        "source": str(source.resolve()),
        "output": str(output.resolve()),
        "text_path": str(text_path.resolve()),
        "voice": voice,
        "line_count": line_count,
        "dry_run": dry_run,
        "engine": "edge-tts",
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a TTS voiceover from audio/tts_lines.json.")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts voice name")
    parser.add_argument("--rate", default="+0%", help="edge-tts rate, e.g. +8%% or -5%%")
    parser.add_argument("--volume", default="+0%", help="edge-tts volume, e.g. +0%%")
    parser.add_argument("--pitch", default="+0Hz", help="edge-tts pitch, e.g. +0Hz")
    parser.add_argument("--dry-run", action="store_true", help="Write text/manifest without calling TTS")
    parser.add_argument("-o", "--output", type=Path, help="Output MP3 path")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not project.is_dir():
        print(f"ERROR: project directory does not exist: {project}")
        return 2

    output = args.output or project / VOICEOVER_AUDIO
    text_path = project / VOICEOVER_TEXT
    manifest_path = project / TTS_MANIFEST
    output.parent.mkdir(parents=True, exist_ok=True)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        lines = load_tts_lines(project)
        text = build_voiceover_text(lines)
        text_path.write_text(text, encoding="utf-8")
        if not args.dry_run:
            asyncio.run(synthesize_with_edge_tts(text, args.voice, output, args.rate, args.volume, args.pitch))
        write_manifest(
            manifest_path,
            source=project / "audio" / "tts_lines.json",
            output=output,
            text_path=text_path,
            voice=args.voice,
            line_count=len(lines),
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Voiceover text: {text_path}")
    if args.dry_run:
        print(f"TTS manifest: {manifest_path}")
    else:
        print(f"Voiceover audio: {output}")
        print(f"TTS manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
