#!/usr/bin/env python3
"""Serve the lightweight video-master WebUI and project-state APIs."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_state import ProjectStateError, build_project_state, write_project_state
from generate_voiceover_tts import (
    DEFAULT_VOICE,
    DEFAULT_VOXCPM2_BASE_URL,
    DEFAULT_VOXCPM2_CONTROL_INSTRUCTION,
    DEFAULT_VOXCPM2_PERSONA,
    generate_voiceover as generate_voiceover_track,
)
from codex_image_generation import (
    CodexImageGenerationError,
    generate_storyboard_image_for_project,
    get_auth_status,
    logout_codex,
    poll_codex_device_login,
    start_codex_device_login,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
WEBUI_DIR = SKILL_DIR / "webui"
DEFAULT_PROJECT_ROOT = REPO_ROOT / "video_projects"
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
HERO_MEDIA_OVERRIDE: Path | None = None
CODEX_SHOT_REQUESTS = Path("qa") / "metadata" / "codex_shot_requests.json"
CODEX_SHOT_OPERATION_REQUESTS = Path("qa") / "metadata" / "codex_shot_operation_requests.json"
CODEX_CANVAS_SYNC_REQUESTS = Path("qa") / "metadata" / "codex_canvas_sync_requests.json"


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


def project_file_payload(project: Path, path: Path) -> dict[str, object]:
    try:
        relative = str(path.resolve().relative_to(project.resolve()))
    except ValueError:
        relative = str(path)
    return {
        "path": relative,
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def coerce_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def coerce_float(value: object, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("numeric voiceover option is invalid") from exc


def coerce_int(value: object, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("integer voiceover option is invalid") from exc


def resolve_project_output_path(project: Path, value: object) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    output = Path(raw)
    resolved = output.resolve() if output.is_absolute() else (project / output).resolve()
    try:
        resolved.relative_to(project.resolve())
    except ValueError as exc:
        raise ValueError("voiceover output must stay inside the project directory") from exc
    return resolved


def generate_voiceover_for_webui(project: Path, payload: dict[str, object]) -> dict[str, object]:
    engine = str(payload.get("engine") or "voxcpm2").strip() or "voxcpm2"
    if engine not in {"edge-tts", "voxcpm2"}:
        raise ValueError("engine must be edge-tts or voxcpm2")
    result = generate_voiceover_track(
        project,
        engine=engine,
        voice=str(payload.get("voice") or DEFAULT_VOICE).strip() or DEFAULT_VOICE,
        rate=str(payload.get("rate") or "+0%").strip() or "+0%",
        volume=str(payload.get("volume") or "+0%").strip() or "+0%",
        pitch=str(payload.get("pitch") or "+0Hz").strip() or "+0Hz",
        tts_base_url=str(payload.get("tts_base_url") or DEFAULT_VOXCPM2_BASE_URL).strip() or DEFAULT_VOXCPM2_BASE_URL,
        persona=str(payload.get("persona") or DEFAULT_VOXCPM2_PERSONA).strip() or DEFAULT_VOXCPM2_PERSONA,
        control_instruction=str(payload.get("control_instruction") or DEFAULT_VOXCPM2_CONTROL_INSTRUCTION).strip()
        or DEFAULT_VOXCPM2_CONTROL_INSTRUCTION,
        cfg_value=coerce_float(payload.get("cfg_value"), 2.0),
        do_normalize=coerce_bool(payload.get("do_normalize"), False),
        denoise=coerce_bool(payload.get("denoise"), False),
        dit_steps=coerce_int(payload.get("dit_steps"), 10),
        api_key=str(payload.get("api_key") or "").strip() or None,
        timeout=coerce_float(payload.get("timeout"), 300.0),
        dry_run=coerce_bool(payload.get("dry_run"), False),
        output=resolve_project_output_path(project, payload.get("output")),
    )
    return {
        "ok": True,
        "engine": result["engine"],
        "dry_run": result["dry_run"],
        "audio": project_file_payload(project, result["output"]),
        "text": project_file_payload(project, result["text_path"]),
        "manifest": project_file_payload(project, result["manifest_path"]),
        "manifest_data": result["manifest"],
    }


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


def read_json_file(path: Path, default: object) -> object:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json_file(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_shot_id(shots: list[dict[str, object]]) -> str:
    highest = 0
    for shot in shots:
        raw_id = str(shot.get("shot_id", ""))
        if raw_id.startswith("S") and raw_id[1:].isdigit():
            highest = max(highest, int(raw_id[1:]))
    return f"S{highest + 1:02d}"


def seconds_label(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value):02d}"
    return f"{value:04.1f}".rstrip("0").rstrip(".")


def reflow_shot_times(shots: list[dict[str, object]]) -> None:
    current = 0.0
    for shot in shots:
        try:
            duration = float(shot.get("duration_seconds", 3))
        except (TypeError, ValueError):
            duration = 3.0
        duration = max(0.1, duration)
        start = current
        end = current + duration
        shot["duration_seconds"] = int(duration) if duration.is_integer() else duration
        shot["start"] = f"00:{seconds_label(start)}"
        shot["end"] = f"00:{seconds_label(end)}"
        shot["time"] = f"{shot['start']}-{shot['end']}"
        current = end


def clean_shot_payload(raw: object, fallback_id: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError("shot payload must be an object")
    shot_id = str(raw.get("shot_id") or fallback_id).strip()
    if not shot_id:
        shot_id = fallback_id
    cleaned: dict[str, object] = {"shot_id": shot_id}
    text_fields = [
        "beat",
        "purpose",
        "visual_action",
        "framing",
        "camera",
        "movement",
        "lighting",
        "image_prompt_seed",
        "video_prompt_seed",
    ]
    for field in text_fields:
        if field in raw:
            cleaned[field] = str(raw.get(field) or "").strip()
    if "duration_seconds" in raw:
        try:
            duration = float(raw.get("duration_seconds"))
        except (TypeError, ValueError) as exc:
            raise ValueError("duration_seconds must be numeric") from exc
        cleaned["duration_seconds"] = max(0.1, duration)
    return cleaned


def update_project_shot(project: Path, payload: dict[str, object]) -> dict[str, object]:
    shot_list_path = project / "storyboard" / "shot_list.json"
    raw_shots = read_json_file(shot_list_path, [])
    if not isinstance(raw_shots, list):
        raise ValueError("storyboard/shot_list.json must be a list")
    shots = [shot for shot in raw_shots if isinstance(shot, dict)]
    mode = str(payload.get("mode") or "update").lower()
    if mode not in {"add", "update"}:
        raise ValueError("mode must be add or update")

    fallback_id = next_shot_id(shots)
    incoming = clean_shot_payload(payload.get("shot"), fallback_id)
    saved_shot: dict[str, object]

    if mode == "add":
        incoming["shot_id"] = next_shot_id(shots)
        after_shot_id = str(payload.get("after_shot_id") or "").strip()
        insert_at = len(shots)
        for index, shot in enumerate(shots):
            if str(shot.get("shot_id")) == after_shot_id:
                insert_at = index + 1
                break
        shots.insert(insert_at, incoming)
        saved_shot = incoming
    else:
        shot_id = str(incoming.get("shot_id") or "").strip()
        if not shot_id:
            raise ValueError("shot.shot_id is required for update")
        for index, shot in enumerate(shots):
            if str(shot.get("shot_id")) == shot_id:
                shot.update({key: value for key, value in incoming.items() if key != "shot_id"})
                saved_shot = shot
                break
        else:
            raise ValueError(f"shot not found: {shot_id}")

    reflow_shot_times(shots)
    write_json_file(shot_list_path, shots)
    return saved_shot


def append_codex_shot_request(project: Path, payload: dict[str, object]) -> dict[str, object]:
    idea = str(payload.get("idea") or "").strip()
    if not idea:
        raise ValueError("idea is required")
    try:
        x = float(payload.get("x", 520))
        y = float(payload.get("y", 160))
    except (TypeError, ValueError) as exc:
        raise ValueError("x and y must be numeric") from exc
    request_path = project / CODEX_SHOT_REQUESTS
    raw_requests = read_json_file(request_path, [])
    requests = raw_requests if isinstance(raw_requests, list) else []
    now = datetime.now(timezone.utc)
    request = {
        "request_id": f"idea_{now.strftime('%Y%m%dT%H%M%S%fZ')}",
        "status": "pending",
        "idea": idea,
        "x": int(x) if x.is_integer() else x,
        "y": int(y) if y.is_integer() else y,
        "insert_after_shot_id": str(payload.get("insert_after_shot_id") or "").strip(),
        "created_at": now.isoformat(),
    }
    requests.append(request)
    write_json_file(request_path, requests)
    return request


def append_codex_shot_operation_request(project: Path, payload: dict[str, object]) -> dict[str, object]:
    shot_id = str(payload.get("shot_id") or "").strip()
    operation = str(payload.get("operation") or "").strip()
    if not shot_id:
        raise ValueError("shot_id is required")
    if not operation:
        raise ValueError("operation is required")
    allowed_operations = {
        "rewrite_prompt",
        "replace_image",
        "image_variant",
        "locked_rewrite",
        "regenerate_image",
    }
    if operation not in allowed_operations:
        raise ValueError(f"unsupported operation: {operation}")
    shot = payload.get("shot")
    if shot is not None and not isinstance(shot, dict):
        raise ValueError("shot must be an object")
    request_path = project / CODEX_SHOT_OPERATION_REQUESTS
    raw_requests = read_json_file(request_path, [])
    requests = raw_requests if isinstance(raw_requests, list) else []
    now = datetime.now(timezone.utc)
    request = {
        "request_id": f"shotop_{now.strftime('%Y%m%dT%H%M%S%fZ')}",
        "status": "pending",
        "source": "webui_shot_card",
        "shot_id": shot_id,
        "operation": operation,
        "note": str(payload.get("note") or "").strip(),
        "preserve_locks": bool(payload.get("preserve_locks")),
        "shot": shot or {},
        "created_at": now.isoformat(),
    }
    requests.append(request)
    write_json_file(request_path, requests)
    return request


def append_canvas_sync_request(project: Path, payload: dict[str, object]) -> dict[str, object]:
    canvas_state = payload.get("canvas_state")
    if not isinstance(canvas_state, dict):
        raise ValueError("canvas_state must be an object")
    note = str(payload.get("note") or "").strip()
    request_path = project / CODEX_CANVAS_SYNC_REQUESTS
    raw_requests = read_json_file(request_path, [])
    requests = raw_requests if isinstance(raw_requests, list) else []
    now = datetime.now(timezone.utc)
    request = {
        "request_id": f"canvas_{now.strftime('%Y%m%dT%H%M%S%fZ')}",
        "status": "pending",
        "source": "webui_canvas",
        "note": note,
        "canvas_state": canvas_state,
        "created_at": now.isoformat(),
    }
    requests.append(request)
    write_json_file(request_path, requests)
    return request


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

    def read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

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

        if route == "/api/auth/codex/status":
            self.send_json(get_auth_status())
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/api/shot":
            try:
                payload = self.read_json_body()
                project = resolve_local_path(str(payload.get("project") or ""))
                if not project.is_dir():
                    self.send_json({"error": "project path not found"}, 404)
                    return
                saved_shot = update_project_shot(project, payload)
                state = build_project_state(project)
            except (ProjectStateError, ValueError) as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"ok": True, "shot": saved_shot, "state": state})
            return

        if route == "/api/shot-request":
            try:
                payload = self.read_json_body()
                project = resolve_local_path(str(payload.get("project") or ""))
                if not project.is_dir():
                    self.send_json({"error": "project path not found"}, 404)
                    return
                request = append_codex_shot_request(project, payload)
                state = build_project_state(project)
            except (ProjectStateError, ValueError) as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"ok": True, "request": request, "state": state})
            return

        if route == "/api/shot-operation":
            try:
                payload = self.read_json_body()
                project = resolve_local_path(str(payload.get("project") or ""))
                if not project.is_dir():
                    self.send_json({"error": "project path not found"}, 404)
                    return
                request = append_codex_shot_operation_request(project, payload)
                state = build_project_state(project)
            except (ProjectStateError, ValueError) as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"ok": True, "request": request, "state": state})
            return

        if route == "/api/canvas-sync":
            try:
                payload = self.read_json_body()
                project = resolve_local_path(str(payload.get("project") or ""))
                if not project.is_dir():
                    self.send_json({"error": "project path not found"}, 404)
                    return
                request = append_canvas_sync_request(project, payload)
                state = build_project_state(project)
            except (ProjectStateError, ValueError) as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"ok": True, "request": request, "state": state})
            return

        if route == "/api/voiceover/generate":
            try:
                payload = self.read_json_body()
                project = resolve_local_path(str(payload.get("project") or ""))
                if not project.is_dir():
                    self.send_json({"error": "project path not found"}, 404)
                    return
                result = generate_voiceover_for_webui(project, payload)
                result["state"] = build_project_state(project)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 502)
                return
            except (ProjectStateError, ValueError, FileNotFoundError) as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json(result)
            return

        if route == "/api/auth/codex/device/start":
            try:
                self.send_json(start_codex_device_login())
            except CodexImageGenerationError as exc:
                self.send_json({"error": str(exc)}, 502)
            return

        if route == "/api/auth/codex/device/poll":
            try:
                payload = self.read_json_body()
                device_auth_id = str(payload.get("deviceAuthId") or payload.get("device_auth_id") or "").strip()
                user_code = str(payload.get("userCode") or payload.get("user_code") or "").strip()
                if not device_auth_id or not user_code:
                    self.send_json({"error": "Codex 登录轮询缺少设备码"}, 400)
                    return
                self.send_json(poll_codex_device_login(device_auth_id, user_code))
            except (ValueError, CodexImageGenerationError) as exc:
                self.send_json({"error": str(exc)}, 502)
            return

        if route == "/api/auth/codex/logout":
            self.send_json(logout_codex())
            return

        if route == "/api/storyboard-image/generate":
            try:
                payload = self.read_json_body()
                project = resolve_local_path(str(payload.get("project") or ""))
                if not project.is_dir():
                    self.send_json({"error": "project path not found"}, 404)
                    return
                shot_id = str(payload.get("shot_id") or "").strip()
                if not shot_id:
                    self.send_json({"error": "shot_id is required"}, 400)
                    return
                result = generate_storyboard_image_for_project(
                    project,
                    shot_id,
                    operation=str(payload.get("operation") or "regenerate_image"),
                    prompt=str(payload.get("prompt") or "").strip() or None,
                )
                state = build_project_state(project)
            except (ProjectStateError, ValueError, CodexImageGenerationError) as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"ok": True, "result": result, "state": state})
            return

        self.send_json({"error": "not found"}, 404)


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
