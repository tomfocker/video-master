#!/usr/bin/env python3
"""Initialize a project-local HyperFrames AI-animation workspace."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2]
TYPOGRAPHY_DIR = SKILL_DIR / "ai_animation" / "typography"
CATALOG_PATH = TYPOGRAPHY_DIR / "catalog.json"
RUNTIME_FILES = [
    TYPOGRAPHY_DIR / "runtime" / "text-effects-catalog.js",
    TYPOGRAPHY_DIR / "runtime" / "text-effects-runtime.js",
    TYPOGRAPHY_DIR / "runtime" / "text-effects.css",
]


def canvas_size(aspect_ratio: str) -> tuple[int, int]:
    sizes = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
    if aspect_ratio not in sizes:
        raise ValueError(f"unsupported aspect ratio: {aspect_ratio}")
    return sizes[aspect_ratio]


def composition_html(*, text: str, effect_id: str, duration_seconds: float, width: int, height: int) -> str:
    safe_text = json.dumps(text, ensure_ascii=False).replace("</", "<\\/")
    safe_effect = json.dumps(effect_id).replace("</", "<\\/")
    title = html.escape(text)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="runtime/text-effects.css" />
    <style>
      * {{ box-sizing: border-box; }}
      @font-face {{ font-family: "Video Master Sans"; src: local("Microsoft YaHei"), local("PingFang SC"), local("Noto Sans CJK SC"); }}
      html, body {{ width: 100%; height: 100%; margin: 0; overflow: hidden; background: #070a12; }}
      [data-composition-id] {{
        width: {width}px; height: {height}px; display: grid; place-items: center; overflow: hidden;
        background: radial-gradient(circle at 70% 24%, rgba(94, 234, 212, .16), transparent 34%), #070a12;
        color: #f7f9ff; font-family: "Video Master Sans", sans-serif;
      }}
      #headline {{ width: 84%; min-height: 220px; font-size: {max(64, round(width * 0.064))}px; font-weight: 760; line-height: 1.12; text-align: center; letter-spacing: -.04em; }}
    </style>
  </head>
  <body>
    <main data-composition-id="main" data-width="{width}" data-height="{height}" data-start="0" data-duration="{duration_seconds:g}">
      <div id="headline" aria-label="{title}"></div>
    </main>
    <script src="runtime/text-effects-catalog.js"></script>
    <script src="runtime/text-effects-runtime.js"></script>
    <script>
      VideoMasterTextEffects.play({{
        target: "#headline",
        effectId: {safe_effect},
        text: {safe_text},
        startMs: 300,
        autoplay: new URLSearchParams(location.search).has("autoplay"),
      }});
      window.__timelines = window.__timelines || {{}};
      window.__timelines.main = {{
        pause() {{ return this; }},
        seek() {{ return this; }},
        duration() {{ return {duration_seconds:g}; }},
        totalDuration() {{ return {duration_seconds:g}; }},
      }};
    </script>
  </body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--execution-mode", choices=["hyperframes", "hybrid"], default="hyperframes")
    parser.add_argument("--aspect-ratio", choices=["16:9", "9:16", "1:1", "4:5"], default="16:9")
    parser.add_argument("--duration-seconds", type=float, default=6.0)
    parser.add_argument("--effect-id", default="focus-blur-rise")
    parser.add_argument("--text", default="从现象，进入原理")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.duration_seconds <= 0:
        parser.error("--duration-seconds must be positive")
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    effect_ids = {item["id"] for item in catalog["effects"]}
    if args.effect_id not in effect_ids:
        parser.error(f"unknown typography effect: {args.effect_id}")

    project = args.project.resolve()
    animation = project / "animation"
    runtime = animation / "runtime"
    compositions = animation / "compositions"
    renders = animation / "renders"
    final_dir = project / "最终交付" / "08_ai_animation"
    plan_path = animation / "ai_animation_plan.json"
    composition_path = animation / "index.html"
    if not args.force and (plan_path.exists() or composition_path.exists()):
        parser.error("AI animation files already exist; pass --force to replace the scaffold")

    for directory in [runtime, composition_path.parent, compositions, renders, final_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    for source in RUNTIME_FILES:
        shutil.copy2(source, runtime / source.name)
    shutil.copy2(TYPOGRAPHY_DIR / "THIRD_PARTY_NOTICES.md", runtime / "THIRD_PARTY_NOTICES.md")
    shutil.copy2(TYPOGRAPHY_DIR / "licenses" / "sakura-animate-text-MIT.txt", runtime / "sakura-animate-text-MIT.txt")

    width, height = canvas_size(args.aspect_ratio)
    composition_path.write_text(
        composition_html(
            text=args.text,
            effect_id=args.effect_id,
            duration_seconds=args.duration_seconds,
            width=width,
            height=height,
        ),
        encoding="utf-8",
    )
    plan = {
        "schema_version": 1,
        "enabled": True,
        "engine": "hyperframes",
        "execution_mode": args.execution_mode,
        "modules": ["typography"],
        "typography": {
            "effects": [
                {
                    "element_id": "main_title",
                    "effect_id": args.effect_id,
                    "text_source": "animation/index.html",
                    "start_ms": 300,
                    "duration_ms": next(item["duration_ms"] for item in catalog["effects"] if item["id"] == args.effect_id),
                }
            ]
        },
        "compositions": [
            {
                "id": "main",
                "source": "animation/index.html",
                "duration_seconds": args.duration_seconds,
                "aspect_ratio": args.aspect_ratio,
            }
        ],
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(plan_path)
    print(composition_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
