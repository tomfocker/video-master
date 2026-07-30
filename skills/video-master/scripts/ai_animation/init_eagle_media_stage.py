#!/usr/bin/env python3
"""Create a project-local HyperFrames stage from an approved Eagle image or video."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any


MANIFEST_RELATIVE = Path("sources") / "eagle_assets_manifest.json"
IMAGE_EXTENSIONS = {"avif", "bmp", "gif", "jpeg", "jpg", "png", "svg", "tif", "tiff", "webp"}
VIDEO_EXTENSIONS = {"avi", "m4v", "mkv", "mov", "mp4", "mpeg", "mpg", "webm"}


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def safe_id(value: str, label: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError(f"{label} must use lowercase hyphen-case: {value}")
    return value


def default_composition_id(asset_id: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", "-", asset_id.lower()).strip("-") or "asset"
    return f"eagle-media-{compact}"


def canvas_size(aspect_ratio: str) -> tuple[int, int]:
    sizes = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
    if aspect_ratio not in sizes:
        raise ValueError(f"unsupported aspect ratio: {aspect_ratio}")
    return sizes[aspect_ratio]


def asset_kind(asset: dict[str, Any]) -> str:
    kind = str(asset.get("kind") or "").lower()
    if kind in {"image", "video"}:
        return kind
    ext = str(asset.get("ext") or "").lower().lstrip(".")
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    raise ValueError(f"Eagle asset {asset.get('id')} is not an image or video")


def project_source(project: Path, asset: dict[str, Any]) -> Path:
    relative = asset.get("project_path")
    if isinstance(relative, str) and relative:
        candidate = (project / relative).resolve()
        if candidate.is_relative_to(project) and candidate.is_file():
            return candidate
    original = Path(str(asset.get("original_path") or "")).expanduser().resolve()
    if original.is_file():
        return original
    raise FileNotFoundError(f"Eagle asset source is unavailable: {original}")


def composition_html(*, title: str, caption: str, asset_src: str, kind: str, duration_seconds: float, width: int, height: int) -> str:
    variables = [
        {"id": "assetSrc", "type": "string", "label": "素材文件", "default": asset_src},
        {"id": "assetKind", "type": "enum", "label": "素材类型", "default": kind, "options": [{"value": "image", "label": "图片"}, {"value": "video", "label": "视频"}]},
        {"id": "title", "type": "string", "label": "标题", "default": title},
        {"id": "caption", "type": "string", "label": "说明", "default": caption},
        {"id": "accent", "type": "color", "label": "强调色", "default": "#5EEAD4"},
        {"id": "exportMode", "type": "enum", "label": "导出模式", "default": "mp4", "hidden": True, "options": [{"value": "mp4", "label": "MP4"}]},
    ]
    variables_attribute = html.escape(json.dumps(variables, ensure_ascii=False), quote=True)
    fallback = json.dumps({item["id"]: item["default"] for item in variables}, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-CN" data-composition-variables='{variables_attribute}'>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <title>{html.escape(title)}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ box-sizing: border-box; }}
      html, body {{ width: {width}px; height: {height}px; margin: 0; overflow: hidden; background: #070a12; }}
      #root {{ position: relative; width: {width}px; height: {height}px; overflow: hidden; color: #f7f9ff; font-family: "Microsoft YaHei", sans-serif; background: #070a12; }}
      #wash, #grain {{ position: absolute; inset: 0; pointer-events: none; }}
      #wash {{ background: radial-gradient(circle at 72% 22%, color-mix(in srgb, var(--accent) 28%, transparent), transparent 34%), linear-gradient(135deg, rgba(7,10,18,.88), rgba(7,10,18,.22)); z-index: 2; }}
      #grain {{ opacity: .15; background-image: radial-gradient(rgba(255,255,255,.34) .7px, transparent .7px); background-size: 8px 8px; mix-blend-mode: soft-light; z-index: 5; }}
      #backdrop {{ position: absolute; inset: -10%; background-size: cover; background-position: center; filter: blur(38px) saturate(.78) brightness(.45); transform: scale(1.16); opacity: .82; }}
      #media-wrap {{ position: absolute; inset: 9% 11%; display: grid; place-items: center; overflow: hidden; border: 1px solid color-mix(in srgb, var(--accent) 56%, transparent); box-shadow: 0 26px 100px rgba(0,0,0,.5); }}
      .media {{ width: 100%; height: 100%; display: block; object-fit: cover; }}
      #video {{ display: none; }}
      #label {{ position: absolute; left: 9%; bottom: 8%; z-index: 6; max-width: 68%; text-shadow: 0 2px 24px rgba(0,0,0,.7); }}
      #title {{ margin: 0; font-size: {max(44, round(width * 0.045))}px; line-height: 1.1; letter-spacing: -.04em; }}
      #caption {{ margin-top: 16px; color: rgba(247,249,255,.76); font-size: {max(20, round(width * 0.018))}px; line-height: 1.45; }}
      #edge {{ position: absolute; inset: 0; z-index: 4; pointer-events: none; border: 16px solid color-mix(in srgb, var(--accent) 22%, transparent); mix-blend-mode: screen; }}
    </style>
  </head>
  <body>
    <main id="root" data-composition-id="main" data-width="{width}" data-height="{height}" data-start="0" data-duration="{duration_seconds:g}">
      <div id="backdrop"></div><div id="media-wrap"><img id="image" class="media" alt="" /><video id="video" class="media" muted playsinline loop></video></div>
      <div id="wash"></div><div id="edge"></div><div id="label"><h1 id="title"></h1><div id="caption"></div></div><div id="grain"></div>
    </main>
    <script>
      const fallback = {fallback};
      const v = window.__hyperframes?.getVariables ? window.__hyperframes.getVariables() : fallback;
      document.documentElement.style.setProperty("--accent", v.accent || fallback.accent);
      title.textContent = v.title || ""; caption.textContent = v.caption || "";
      const source = new URL(v.assetSrc || fallback.assetSrc, window.location.href).href;
      backdrop.style.backgroundImage = `url("${{source}}")`;
      if ((v.assetKind || fallback.assetKind) === "video") {{ video.style.display = "block"; video.src = source; video.play().catch(() => {{}}); }}
      else {{ image.src = source; }}
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#backdrop", {{ opacity: 0, scale: 1.28 }}, {{ opacity: .82, scale: 1.16, duration: 1.2, ease: "power2.out" }}, 0)
        .fromTo("#media-wrap", {{ opacity: 0, scale: 1.08, clipPath: "inset(16% 13% 16% 13%)" }}, {{ opacity: 1, scale: 1, clipPath: "inset(0% 0% 0% 0%)", duration: .86, ease: "expo.out" }}, .18)
        .fromTo("#label", {{ opacity: 0, y: 42 }}, {{ opacity: 1, y: 0, duration: .58, ease: "power3.out" }}, .58)
        .to("#media-wrap", {{ scale: 1.035, duration: {max(1.0, duration_seconds - 2.3):g}, ease: "none" }}, 1.1)
        .to("#root", {{ opacity: 0, duration: .42, ease: "power2.in" }}, {max(0.0, duration_seconds - .42):g});
      window.__timelines.main = tl;
    </script>
  </body>
</html>
"""


def upsert(items: list[Any], item: dict[str, Any], key: str) -> list[Any]:
    return [current for current in items if not isinstance(current, dict) or current.get(key) != item[key]] + [item]


def include_in_composer_timeline(
    plan: dict[str, Any],
    *,
    composition_id: str,
    asset_id: str,
    duration_seconds: float,
    insert_after: str | None,
) -> None:
    """Insert an Eagle stage into a Composer timeline and reflow its timing."""

    if plan.get("composer") != "ai-animation-composer-v1":
        raise ValueError("--append-to-composer requires an existing ai-animation-composer-v1 plan")
    timeline = plan.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise ValueError("--append-to-composer requires a non-empty composer timeline")
    if insert_after is not None and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", insert_after):
        raise ValueError("--insert-after must use a known lowercase hyphen-case composition id")

    retained: list[dict[str, Any]] = []
    for index, item in enumerate(timeline, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"composer timeline item {index} must be an object")
        item_id = str(item.get("composition_id") or "")
        if not item_id:
            raise ValueError(f"composer timeline item {index} requires composition_id")
        if item_id != composition_id:
            retained.append(dict(item))

    if insert_after is None:
        position = len(retained)
    else:
        position = next((index + 1 for index, item in enumerate(retained) if item.get("composition_id") == insert_after), None)
        if position is None:
            raise ValueError(f"--insert-after composition is not in the composer timeline: {insert_after}")

    stage_beat = {
        "beat_id": composition_id,
        "composition_id": composition_id,
        "intent": "eagle-media",
        "template_id": "eagle-media",
        "source_asset_id": asset_id,
        "duration_seconds": duration_seconds,
    }
    retained.insert(position, stage_beat)
    cursor = 0.0
    for item in retained:
        try:
            duration = float(item.get("duration_seconds", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"composer timeline duration is invalid for {item.get('composition_id')}") from exc
        if duration <= 0:
            raise ValueError(f"composer timeline duration must be positive for {item.get('composition_id')}")
        item["start_seconds"] = cursor
        cursor += duration
        item["end_seconds"] = cursor
    plan["timeline"] = retained
    plan["total_duration_seconds"] = cursor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--composition-id")
    parser.add_argument("--title")
    parser.add_argument("--caption", default="Eagle 已确认素材 · HyperFrames 动态呈现")
    parser.add_argument("--duration-seconds", type=float, default=6.0)
    parser.add_argument("--aspect-ratio", choices=["16:9", "9:16", "1:1", "4:5"], default="16:9")
    parser.add_argument(
        "--append-to-composer",
        action="store_true",
        help="Append this media stage to an existing AI Animation Composer timeline",
    )
    parser.add_argument(
        "--insert-after",
        help="Composer composition ID after which to insert this stage; requires --append-to-composer",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.duration_seconds <= 1:
        parser.error("--duration-seconds must be greater than one second")
    if args.insert_after and not args.append_to_composer:
        parser.error("--insert-after requires --append-to-composer")

    try:
        project = args.project.resolve()
        manifest_path = project / MANIFEST_RELATIVE
        manifest = read_object(manifest_path)
        assets = manifest.get("assets")
        if not isinstance(assets, list):
            raise ValueError("Eagle asset manifest requires an assets list")
        asset = next((item for item in assets if isinstance(item, dict) and str(item.get("id")) == args.asset_id), None)
        if not isinstance(asset, dict):
            raise ValueError(f"Eagle asset is not registered in project manifest: {args.asset_id}")
        kind = asset_kind(asset)
        source = project_source(project, asset)
        composition_id = safe_id(args.composition_id or default_composition_id(args.asset_id), "--composition-id")
        width, height = canvas_size(args.aspect_ratio)
        plan_path = project / "animation" / "ai_animation_plan.json"
        plan = read_object(plan_path) if plan_path.is_file() else {
            "schema_version": 1,
            "enabled": True,
            "engine": "hyperframes",
            "execution_mode": "hyperframes",
            "modules": [],
            "compositions": [],
        }
        if args.append_to_composer:
            if plan.get("composer") != "ai-animation-composer-v1":
                raise ValueError("--append-to-composer requires an existing ai-animation-composer-v1 plan")
            timeline = plan.get("timeline")
            if not isinstance(timeline, list) or not timeline:
                raise ValueError("--append-to-composer requires a non-empty composer timeline")
            if args.insert_after and not any(
                isinstance(item, dict) and item.get("composition_id") == args.insert_after for item in timeline
            ):
                raise ValueError(f"--insert-after composition is not in the composer timeline: {args.insert_after}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    composition = project / "animation" / "compositions" / composition_id
    if composition.exists():
        if not args.force:
            parser.error(f"composition already exists: {composition}; pass --force to replace it")
        shutil.rmtree(composition)
    assets_dir = composition / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    local_asset = assets_dir / source.name
    shutil.copy2(source, local_asset)
    local_source = local_asset.relative_to(composition).as_posix()
    title = args.title or str(asset.get("name") or args.asset_id)
    composition_path = composition / "index.html"
    composition_path.write_text(
        composition_html(title=title, caption=args.caption, asset_src=local_source, kind=kind, duration_seconds=args.duration_seconds, width=width, height=height),
        encoding="utf-8",
    )
    variables_path = composition / "presets" / "project.json"
    variables_path.parent.mkdir(parents=True, exist_ok=True)
    variables_path.write_text(json.dumps({"assetSrc": local_source, "assetKind": kind, "title": title, "caption": args.caption, "accent": "#5EEAD4", "exportMode": "mp4"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    plan["enabled"] = True
    plan["engine"] = "hyperframes"
    modules = plan.get("modules") if isinstance(plan.get("modules"), list) else []
    if "eagle-media" not in modules:
        modules.append("eagle-media")
    plan["modules"] = modules
    stages = plan.get("eagle_media", {}).get("stages") if isinstance(plan.get("eagle_media"), dict) else []
    if not isinstance(stages, list):
        stages = []
    stage = {"composition_id": composition_id, "asset_id": args.asset_id, "asset_kind": kind, "asset_file": local_asset.relative_to(project).as_posix(), "variables_file": variables_path.relative_to(project).as_posix(), "export_mode": "mp4", "composer_timeline": args.append_to_composer}
    plan["eagle_media"] = {"stages": upsert(stages, stage, "composition_id")}
    compositions = plan.get("compositions") if isinstance(plan.get("compositions"), list) else []
    composition_record = {"id": composition_id, "source": composition_path.relative_to(project).as_posix(), "variables_file": variables_path.relative_to(project).as_posix(), "duration_seconds": args.duration_seconds, "target_duration_seconds": args.duration_seconds, "aspect_ratio": args.aspect_ratio, "formats": ["mp4"], "module": "eagle-media", "template_id": "eagle-media"}
    plan["compositions"] = upsert(compositions, composition_record, "id")
    if args.append_to_composer:
        try:
            include_in_composer_timeline(
                plan,
                composition_id=composition_id,
                asset_id=args.asset_id,
                duration_seconds=args.duration_seconds,
                insert_after=args.insert_after,
            )
        except ValueError as exc:
            parser.error(str(exc))
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    stages_for_asset = asset.get("hyperframes_stages") if isinstance(asset.get("hyperframes_stages"), list) else []
    asset["hyperframes_stages"] = upsert(stages_for_asset, {"composition_id": composition_id, "asset_file": stage["asset_file"]}, "composition_id")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(composition_path)
    print(variables_path)
    print(plan_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
