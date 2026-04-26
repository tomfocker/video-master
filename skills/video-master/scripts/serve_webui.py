#!/usr/bin/env python3
"""Serve the lightweight video-master WebUI and project-state APIs."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_state import ProjectStateError, build_project_state, write_project_state


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
WEBUI_DIR = SKILL_DIR / "webui"
DEFAULT_PROJECT_ROOT = REPO_ROOT / "video_projects"
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
HERO_MEDIA_OVERRIDE: Path | None = None


def json_bytes(payload: object, status: int = 200) -> tuple[int, bytes, str]:
    return status, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), "application/json; charset=utf-8"


def resolve_local_path(value: str | None, base: Path = REPO_ROOT) -> Path:
    if not value:
        return base
    raw = unquote(value)
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def project_summary(path: Path) -> dict[str, object]:
    try:
        state = build_project_state(path)
        flow_nodes = state.get("flow_nodes", [])
        completed = sum(1 for node in flow_nodes if isinstance(node, dict) and node.get("status") == "complete")
        return {
            "name": path.name,
            "path": str(path),
            "workflow_mode": state.get("workflow", {}).get("workflow_mode", "guided"),
            "shot_count": len(state.get("shots", [])),
            "completed_nodes": completed,
            "total_nodes": len(flow_nodes),
            "status": "ready",
        }
    except Exception as exc:
        return {
            "name": path.name,
            "path": str(path),
            "workflow_mode": "unknown",
            "shot_count": 0,
            "completed_nodes": 0,
            "total_nodes": 0,
            "status": f"unreadable: {exc}",
        }


def file_api_url(project: Path, path: Path) -> str:
    return f"/api/file?project={quote(str(project))}&path={quote(str(path))}"


def media_kind(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return None


def hero_override_summary() -> dict[str, object] | None:
    if HERO_MEDIA_OVERRIDE is None:
        return None
    if not HERO_MEDIA_OVERRIDE.is_file():
        return {"kind": "none", "source": "override", "error": f"hero media not found: {HERO_MEDIA_OVERRIDE}"}
    kind = media_kind(HERO_MEDIA_OVERRIDE)
    if kind is None:
        return {
            "kind": "none",
            "source": "override",
            "error": f"unsupported hero media type: {HERO_MEDIA_OVERRIDE.suffix}",
        }
    return {
        "kind": kind,
        "source": "override",
        "project": "",
        "project_name": HERO_MEDIA_OVERRIDE.stem,
        "path": str(HERO_MEDIA_OVERRIDE),
        "url": "/api/hero-file",
    }


def project_media_candidate(project: Path, patterns: list[str], kind: str) -> dict[str, object] | None:
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(path for path in project.glob(pattern) if path.is_file())
    if candidates:
        chosen = sorted(candidates, key=lambda path: path.stat().st_size, reverse=True)[0]
        relative = chosen.relative_to(project)
        return {
            "kind": kind,
            "source": "project",
            "project": str(project),
            "project_name": project.name,
            "path": str(relative),
            "url": file_api_url(project, relative),
        }
    return None


def hero_media_summary(project_root: Path) -> dict[str, object]:
    override = hero_override_summary()
    if override is not None:
        return override
    if not project_root.is_dir():
        return {"kind": "none", "error": "project root not found"}
    projects = [project for project in sorted(project_root.iterdir(), key=lambda value: value.name.lower()) if project.is_dir()]
    media_tiers = [
        (["**/*.mp4", "**/*.webm"], "video"),
        (["**/*.mov"], "video"),
        (["**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.webp"], "image"),
    ]
    for patterns, kind in media_tiers:
        for project in projects:
            media = project_media_candidate(project, patterns, kind)
            if media:
                return media
    return {"kind": "none"}


class VideoMasterHandler(BaseHTTPRequestHandler):
    server_version = "VideoMasterWebUI/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_payload(self, status: int, body: bytes, content_type: str, extra_headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object, status: int = 200) -> None:
        code, body, content_type = json_bytes(payload, status)
        self.send_payload(code, body, content_type)

    def send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_json({"error": "not found"}, 404)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type = f"{content_type}; charset=utf-8"
        file_size = path.stat().st_size
        headers = {"Accept-Ranges": "bytes"}
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                start_text, end_text = range_header.removeprefix("bytes=").split("-", 1)
                if start_text:
                    start = int(start_text)
                    end = int(end_text) if end_text else file_size - 1
                else:
                    suffix = int(end_text)
                    start = max(file_size - suffix, 0)
                    end = file_size - 1
                if start < 0 or end < start or start >= file_size:
                    self.send_payload(416, b"", content_type, {"Content-Range": f"bytes */{file_size}"})
                    return
                end = min(end, file_size - 1)
                with path.open("rb") as handle:
                    handle.seek(start)
                    body = handle.read(end - start + 1)
                headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
                self.send_payload(206, body, content_type, headers)
                return
            except (TypeError, ValueError):
                self.send_payload(416, b"", content_type, {"Content-Range": f"bytes */{file_size}"})
                return
        self.send_payload(200, path.read_bytes(), content_type, headers)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/api/projects":
            project_root = resolve_local_path(query.get("root", [str(DEFAULT_PROJECT_ROOT)])[0])
            if not project_root.is_dir():
                self.send_json({"projects": [], "root": str(project_root), "error": "project root not found"}, 404)
                return
            projects = []
            for child in sorted(project_root.iterdir(), key=lambda value: value.name.lower()):
                if child.is_dir() and ((child / "brief").exists() or (child / "storyboard").exists() or (child / "qa").exists()):
                    projects.append(project_summary(child))
            self.send_json({"root": str(project_root), "projects": projects})
            return

        if route == "/api/hero-media":
            project_root = resolve_local_path(query.get("root", [str(DEFAULT_PROJECT_ROOT)])[0])
            self.send_json(hero_media_summary(project_root))
            return

        if route == "/api/hero-file":
            if HERO_MEDIA_OVERRIDE is None:
                self.send_json({"error": "hero media is not configured"}, 404)
                return
            self.send_file(HERO_MEDIA_OVERRIDE)
            return

        if route == "/api/project":
            project = resolve_local_path(query.get("path", [""])[0])
            try:
                state = build_project_state(project)
            except ProjectStateError as exc:
                self.send_json({"error": str(exc)}, 404)
                return
            if query.get("write", ["false"])[0].lower() in {"1", "true", "yes"}:
                write_project_state(project, state)
            self.send_json(state)
            return

        if route == "/api/file":
            project = resolve_local_path(query.get("project", [""])[0])
            requested = unquote(query.get("path", [""])[0])
            asset_path = Path(requested)
            file_path = asset_path.resolve() if asset_path.is_absolute() else (project / asset_path).resolve()
            try:
                file_path.relative_to(project.resolve())
            except ValueError:
                self.send_json({"error": "unsafe project file path"}, 400)
                return
            self.send_file(file_path)
            return

        if route == "/":
            self.send_file(WEBUI_DIR / "index.html")
            return

        static_path = (WEBUI_DIR / route.lstrip("/")).resolve()
        try:
            static_path.relative_to(WEBUI_DIR.resolve())
        except ValueError:
            self.send_json({"error": "unsafe path"}, 400)
            return
        self.send_file(static_path)


def main(argv: list[str] | None = None) -> int:
    global HERO_MEDIA_OVERRIDE

    parser = argparse.ArgumentParser(description="Serve the video-master WebUI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--hero-media", default=os.environ.get("VIDEO_MASTER_HERO_MEDIA"), help="Optional intro video/image path")
    args = parser.parse_args(argv)
    if args.hero_media:
        HERO_MEDIA_OVERRIDE = Path(args.hero_media).expanduser().resolve()

    server = ThreadingHTTPServer((args.host, args.port), VideoMasterHandler)
    print(f"Video Master WebUI: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping WebUI server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
