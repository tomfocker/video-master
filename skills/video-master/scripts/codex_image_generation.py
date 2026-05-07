#!/usr/bin/env python3
"""Codex-authenticated storyboard image generation helpers for Video Master."""

from __future__ import annotations

import base64
import json
import os
import re
import stat
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import FINAL_STORYBOARD_DIR, METADATA_DIR


CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_CODEX_ISSUER = "https://auth.openai.com"
DEFAULT_CODEX_RESPONSES_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_IMAGE_MODEL = "gpt-image-2"
DEFAULT_ORCHESTRATOR_MODEL = "gpt-5.4"
DEFAULT_IMAGE_TIMEOUT_SECONDS = 20 * 60
TOKEN_REFRESH_SKEW_SECONDS = 5 * 60
IMAGE_GENERATION_MANIFEST = METADATA_DIR / "image_generation_manifest.json"


class CodexImageGenerationError(RuntimeError):
    """Raised when Codex auth or image generation fails."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def codex_auth_file() -> Path:
    override = os.environ.get("VIDEO_MASTER_CODEX_AUTH_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex" / "video-master" / "codex_oauth.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: Path, payload: Any, *, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if private:
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass


def trim_slashes(value: str) -> str:
    return value.rstrip("/")


def codex_issuer() -> str:
    return trim_slashes(os.environ.get("CODEX_AUTH_ISSUER", DEFAULT_CODEX_ISSUER).strip() or DEFAULT_CODEX_ISSUER)


def codex_responses_base_url() -> str:
    return trim_slashes(
        os.environ.get("CODEX_RESPONSES_BASE_URL", DEFAULT_CODEX_RESPONSES_BASE_URL).strip()
        or DEFAULT_CODEX_RESPONSES_BASE_URL
    )


def image_model() -> str:
    return os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL).strip() or DEFAULT_IMAGE_MODEL


def orchestrator_model() -> str:
    return os.environ.get("CODEX_ORCHESTRATOR_MODEL", DEFAULT_ORCHESTRATOR_MODEL).strip() or DEFAULT_ORCHESTRATOR_MODEL


def image_timeout_seconds() -> int:
    raw = os.environ.get("CODEX_IMAGE_TIMEOUT_SECONDS") or os.environ.get("OPENAI_IMAGE_TIMEOUT_MS", "")
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_IMAGE_TIMEOUT_SECONDS
    if raw == os.environ.get("OPENAI_IMAGE_TIMEOUT_MS"):
        parsed = max(1, parsed // 1000)
    return parsed if parsed > 0 else DEFAULT_IMAGE_TIMEOUT_SECONDS


def parse_json_response(response: Any) -> Any:
    raw = response.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CodexImageGenerationError("Codex 服务返回内容无法解析。") from exc


def post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return parse_json_response(response)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise CodexImageGenerationError(f"Codex 服务请求失败：HTTP {exc.code} {body[:300]}") from exc
    except URLError as exc:
        raise CodexImageGenerationError(f"Codex 服务暂时不可用：{exc.reason}") from exc


def base64_url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def parse_jwt_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    try:
        payload = json.loads(base64_url_decode(parts[1]).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def token_expires_at(payload: dict[str, Any], fallback: str | None = None) -> str:
    claims = parse_jwt_claims(str(payload.get("access_token") or ""))
    exp = claims.get("exp")
    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
    expires_in = payload.get("expires_in")
    if isinstance(expires_in, (int, float)):
        return (utc_now() + timedelta(seconds=float(expires_in))).isoformat()
    return fallback or (utc_now() + timedelta(hours=1)).isoformat()


def normalize_token_payload(payload: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = fallback or {}
    access_token = str(payload.get("access_token") or fallback.get("access_token") or "").strip()
    refresh_token = str(payload.get("refresh_token") or fallback.get("refresh_token") or "").strip()
    id_token = str(payload.get("id_token") or fallback.get("id_token") or "").strip()
    if not access_token or not refresh_token or not id_token:
        raise CodexImageGenerationError("Codex 登录服务没有返回完整令牌。")

    id_claims = parse_jwt_claims(id_token)
    profile = id_claims.get("https://api.openai.com/profile")
    auth = id_claims.get("https://api.openai.com/auth")
    if not isinstance(profile, dict):
        profile = {}
    if not isinstance(auth, dict):
        auth = {}

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "id_token": id_token,
        "email": payload.get("email") or id_claims.get("email") or profile.get("email") or fallback.get("email"),
        "account_id": payload.get("account_id") or auth.get("chatgpt_account_id") or fallback.get("account_id"),
        "expires_at": token_expires_at(payload, fallback.get("expires_at")),
        "refreshed_at": iso_now(),
        "updated_at": iso_now(),
    }


def read_auth_tokens() -> dict[str, Any] | None:
    data = read_json(codex_auth_file(), None)
    return data if isinstance(data, dict) else None


def store_auth_tokens(payload: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_token_payload(payload, fallback)
    normalized["created_at"] = (fallback or {}).get("created_at") or iso_now()
    write_json(codex_auth_file(), normalized, private=True)
    return normalized


def logout_codex() -> dict[str, Any]:
    path = codex_auth_file()
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return {"ok": True, "auth": get_auth_status()}


def session_is_expiring(tokens: dict[str, Any]) -> bool:
    expires_at = tokens.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at:
        return True
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    return parsed <= utc_now() + timedelta(seconds=TOKEN_REFRESH_SKEW_SECONDS)


def refresh_codex_tokens(tokens: dict[str, Any]) -> dict[str, Any] | None:
    refresh_token = str(tokens.get("refresh_token") or "").strip()
    if not refresh_token:
        return None
    payload = {
        "client_id": CODEX_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    refreshed = post_json(f"{codex_issuer()}/oauth/token", payload)
    if not isinstance(refreshed, dict):
        raise CodexImageGenerationError("Codex 登录刷新响应无法识别。")
    return store_auth_tokens(refreshed, tokens)


def get_valid_codex_session() -> dict[str, Any] | None:
    tokens = read_auth_tokens()
    if not tokens or not tokens.get("access_token"):
        return None
    if session_is_expiring(tokens):
        tokens = refresh_codex_tokens(tokens)
    if not tokens or not tokens.get("access_token"):
        return None
    return {
        "access_token": tokens["access_token"],
        "account_id": tokens.get("account_id"),
        "expires_at": tokens.get("expires_at"),
    }


def get_auth_status() -> dict[str, Any]:
    tokens = read_auth_tokens()
    available = bool(tokens and tokens.get("access_token") and tokens.get("refresh_token"))
    return {
        "provider": "codex" if available else "none",
        "openai_configured": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
        "codex": {
            "available": available,
            "email": tokens.get("email") if tokens else None,
            "account_id": tokens.get("account_id") if tokens else None,
            "expires_at": tokens.get("expires_at") if tokens else None,
            "refreshed_at": tokens.get("refreshed_at") if tokens else None,
        },
    }


def start_codex_device_login() -> dict[str, Any]:
    issuer = codex_issuer()
    payload = post_json(
        f"{issuer}/api/accounts/deviceauth/usercode",
        {"client_id": CODEX_CLIENT_ID},
    )
    if not isinstance(payload, dict):
        raise CodexImageGenerationError("Codex 登录服务返回内容无法识别。")
    device_auth_id = payload.get("device_auth_id") or payload.get("deviceAuthId")
    user_code = payload.get("user_code") or payload.get("usercode") or payload.get("userCode")
    if not device_auth_id or not user_code:
        raise CodexImageGenerationError("Codex 登录服务没有返回设备码。")
    interval = int(payload.get("interval") or 5)
    expires_in = int(payload.get("expires_in") or 15 * 60)
    return {
        "deviceAuthId": device_auth_id,
        "userCode": user_code,
        "verificationUrl": f"{issuer}/codex/device",
        "interval": interval,
        "expiresIn": expires_in,
        "expiresAt": (utc_now() + timedelta(seconds=expires_in)).isoformat(),
    }


def exchange_authorization_code(authorization_code: str, code_verifier: str) -> dict[str, Any]:
    issuer = codex_issuer()
    body = urlencode(
        {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": f"{issuer}/deviceauth/callback",
            "client_id": CODEX_CLIENT_ID,
            "code_verifier": code_verifier,
        }
    )
    request = Request(
        f"{issuer}/oauth/token",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = parse_json_response(response)
    except HTTPError as exc:
        raise CodexImageGenerationError(f"Codex 登录换取令牌失败：HTTP {exc.code}") from exc
    except URLError as exc:
        raise CodexImageGenerationError(f"Codex 登录换取令牌失败：{exc.reason}") from exc
    if not isinstance(payload, dict):
        raise CodexImageGenerationError("Codex 登录令牌响应无法识别。")
    return store_auth_tokens(payload)


def poll_codex_device_login(device_auth_id: str, user_code: str) -> dict[str, Any]:
    issuer = codex_issuer()
    request = Request(
        f"{issuer}/api/accounts/deviceauth/token",
        data=json.dumps({"device_auth_id": device_auth_id, "user_code": user_code}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            payload = parse_json_response(response)
    except HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": raw}
    except URLError as exc:
        raise CodexImageGenerationError(f"Codex 登录服务暂时不可用：{exc.reason}") from exc

    if status == 200 and isinstance(payload, dict):
        authorization_code = payload.get("authorization_code") or payload.get("authorizationCode")
        code_verifier = payload.get("code_verifier") or payload.get("codeVerifier")
        if authorization_code and code_verifier:
            exchange_authorization_code(str(authorization_code), str(code_verifier))
            return {"status": "authorized", "auth": get_auth_status()}

    error_code = payload.get("error") if isinstance(payload, dict) else ""
    if error_code in {"authorization_pending", "slow_down"} or status in {403, 404}:
        return {"status": "pending", "interval": int(payload.get("interval") or 5) if isinstance(payload, dict) else 5}
    if error_code == "expired_token":
        return {"status": "expired", "message": "Codex 登录码已过期，请重新开始登录。"}
    if error_code == "access_denied":
        return {"status": "denied", "message": "Codex 登录已被取消。"}
    raise CodexImageGenerationError("Codex 登录轮询失败，请稍后重试。")


def create_codex_responses_request_body(
    *,
    prompt: str,
    size: str,
    quality: str,
    output_format: str,
    image_model: str,
    orchestrator_model: str,
    reference_image_data_url: str | None = None,
) -> dict[str, Any]:
    content = [{"type": "input_text", "text": prompt}]
    if reference_image_data_url:
        content.append({"type": "input_image", "image_url": reference_image_data_url})
    return {
        "model": orchestrator_model,
        "store": False,
        "instructions": "Create exactly one high-quality storyboard image using the image_generation tool. If input images are provided, edit or transform them according to the prompt.",
        "input": [{"type": "message", "role": "user", "content": content}],
        "tools": [
            {
                "type": "image_generation",
                "model": image_model,
                "size": size,
                "quality": quality,
                "output_format": output_format,
                "background": "opaque",
                "partial_images": 0,
            }
        ],
        "tool_choice": {"type": "allowed_tools", "mode": "required", "tools": [{"type": "image_generation"}]},
        "stream": True,
    }


def parse_codex_responses_events_from_sse(text: str) -> list[Any]:
    events: list[Any] = []
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal data_lines
        if not data_lines:
            return
        data = "\n".join(data_lines).strip()
        data_lines = []
        if not data or data == "[DONE]":
            return
        try:
            events.append(json.loads(data))
        except json.JSONDecodeError:
            events.append(data)

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if not line:
            flush()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    flush()
    return events


def extract_codex_image_base64_from_response_events(events: list[Any]) -> list[str]:
    images: list[str] = []
    seen: set[str] = set()
    for event in events:
        for image in extract_images_from_value(event):
            if image not in seen:
                seen.add(image)
                images.append(image)
    return images


def extract_images_from_value(value: Any) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        if value.get("type") == "image_generation_call" and isinstance(value.get("result"), str):
            result.append(value["result"])
        for child in value.values():
            result.extend(extract_images_from_value(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(extract_images_from_value(child))
        return result
    return []


def codex_request_headers(session: dict[str, Any]) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session['access_token']}",
        "User-Agent": "codex_cli_rs/0.0.0 (video-master)",
        "originator": "codex_cli_rs",
    }
    account_id = session.get("account_id")
    if account_id:
        headers["ChatGPT-Account-ID"] = str(account_id)
    return headers


def read_images_from_stream(response: Any) -> list[str]:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return extract_codex_image_base64_from_response_events([parse_json_response(response)])

    buffer = ""
    data_lines: list[str] = []

    def flush() -> list[str]:
        nonlocal data_lines
        if not data_lines:
            return []
        data = "\n".join(data_lines).strip()
        data_lines = []
        if not data or data == "[DONE]":
            return []
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            event = data
        return extract_codex_image_base64_from_response_events([event])

    while True:
        chunk = response.read(8192)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.rstrip("\r")
            if not line:
                images = flush()
                if images:
                    return images
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())

    if buffer.strip():
        if buffer.startswith("data:"):
            data_lines.append(buffer[5:].strip())
        else:
            data_lines.append(buffer.strip())
    return flush()


def request_codex_image(prompt: str, *, size: str, quality: str = "high", output_format: str = "png") -> str:
    session = get_valid_codex_session()
    if not session:
        raise CodexImageGenerationError("没有可用的 Codex 登录会话，请先在 WebUI 点击 Codex 登录。")
    body = create_codex_responses_request_body(
        prompt=prompt,
        size=size,
        quality=quality,
        output_format=output_format,
        image_model=image_model(),
        orchestrator_model=orchestrator_model(),
    )
    request = Request(
        f"{codex_responses_base_url()}/responses",
        data=json.dumps(body).encode("utf-8"),
        headers=codex_request_headers(session),
        method="POST",
    )
    try:
        with urlopen(request, timeout=image_timeout_seconds()) as response:
            images = read_images_from_stream(response)
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise CodexImageGenerationError(f"Codex 图像服务请求失败：HTTP {exc.code} {body_text[:300]}") from exc
    except URLError as exc:
        raise CodexImageGenerationError(f"Codex 图像服务暂时不可用：{exc.reason}") from exc
    if not images:
        raise CodexImageGenerationError("Codex 图像服务没有返回图像结果。")
    return images[0]


def read_project_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def storyboard_size_for_project(project: Path) -> tuple[int, int]:
    spec = read_project_text(project / "brief" / "spec_lock.md")
    matches = re.findall(r"aspect_ratio\s*:\s*([0-9.]+\s*:\s*[0-9.]+)", spec, flags=re.IGNORECASE)
    ratio = matches[-1].replace(" ", "") if matches else ""
    if ratio == "16:9":
        return 1920, 1088
    if ratio == "9:16":
        return 1088, 1920
    if ratio == "1:1":
        return 1536, 1536
    if ratio == "4:3":
        return 1536, 1152
    return 1536, 1024


def split_prompt_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line[3:].split()[0].strip()
            blocks.setdefault(current, [raw_line])
        elif current:
            blocks[current].append(raw_line)
    return {key: "\n".join(lines).strip() for key, lines in blocks.items()}


def load_shot(project: Path, shot_id: str) -> dict[str, Any]:
    shots = read_json(project / "storyboard" / "shot_list.json", [])
    if not isinstance(shots, list):
        return {}
    for shot in shots:
        if isinstance(shot, dict) and str(shot.get("shot_id")) == shot_id:
            return shot
    return {}


def storyboard_prompt_for_shot(project: Path, shot_id: str, override: str | None = None) -> str:
    if override and override.strip():
        return override.strip()
    prompt_blocks = split_prompt_blocks(read_project_text(project / "prompts" / "storyboard_image_prompts.md"))
    prompt = prompt_blocks.get(shot_id, "").strip()
    if prompt:
        return prompt
    final_blocks = split_prompt_blocks(read_project_text(project / "最终交付" / "02_提示词" / "图片生成提示词.md"))
    prompt = final_blocks.get(shot_id, "").strip()
    if prompt:
        return prompt
    shot = load_shot(project, shot_id)
    parts = [
        shot.get("image_prompt_seed", ""),
        shot.get("visual_action", ""),
        shot.get("framing", ""),
        shot.get("camera", ""),
        shot.get("movement", ""),
        shot.get("lighting", ""),
    ]
    prompt = "，".join(str(part).strip() for part in parts if str(part).strip())
    if not prompt:
        prompt = f"{shot_id} 高质量电影分镜参考图"
    return (
        f"{prompt}\n"
        "生成一张高质量视频分镜参考图，保持画面清晰、电影感构图、无字幕、无水印、无多余文字。"
    )


def strip_data_url_prefix(value: str) -> str:
    match = re.match(r"^data:image/[^;,]+;base64,(.+)$", value.strip(), flags=re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else value.strip()


def load_generation_manifest(project: Path) -> dict[str, Any]:
    manifest = read_json(project / IMAGE_GENERATION_MANIFEST, {})
    if not isinstance(manifest, dict):
        manifest = {}
    manifest.setdefault("schema_version", 1)
    manifest.setdefault("shots", {})
    if not isinstance(manifest["shots"], dict):
        manifest["shots"] = {}
    return manifest


def save_generation_manifest(project: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = iso_now()
    write_json(project / IMAGE_GENERATION_MANIFEST, manifest)


def update_manifest_shot(project: Path, shot_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    manifest = load_generation_manifest(project)
    current = manifest["shots"].get(shot_id, {})
    if not isinstance(current, dict):
        current = {}
    current.update(payload)
    manifest["shots"][shot_id] = current
    save_generation_manifest(project, manifest)
    return current


def save_storyboard_image_result(
    *,
    project: Path,
    shot_id: str,
    prompt: str,
    image_base64: str,
    model: str,
    size: str,
    quality: str,
    output_format: str,
    operation: str,
) -> dict[str, Any]:
    data = base64.b64decode(strip_data_url_prefix(image_base64), validate=True)
    output_dir = project / FINAL_STORYBOARD_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    extension = "jpg" if output_format == "jpeg" else output_format
    relative_path = FINAL_STORYBOARD_DIR / f"{shot_id}.{extension}"
    output_path = project / relative_path
    output_path.write_bytes(data)
    generated_at = iso_now()
    job = update_manifest_shot(
        project,
        shot_id,
        {
            "status": "succeeded",
            "operation": operation,
            "model": model,
            "size": size,
            "quality": quality,
            "output_format": output_format,
            "prompt": prompt,
            "path": str(relative_path),
            "generated_at": generated_at,
            "job_id": f"{shot_id}_{int(time.time() * 1000)}",
        },
    )
    return {
        "job": job,
        "asset": {
            "path": str(relative_path),
            "mime_type": f"image/{'jpeg' if extension == 'jpg' else extension}",
            "generated_at": generated_at,
        },
    }


def generate_storyboard_image_for_project(
    project: Path,
    shot_id: str,
    operation: str = "regenerate_image",
    prompt: str | None = None,
) -> dict[str, Any]:
    project = project.resolve()
    width, height = storyboard_size_for_project(project)
    size = f"{width}x{height}"
    output_format = "png"
    quality = "high"
    resolved_prompt = storyboard_prompt_for_shot(project, shot_id, prompt)
    update_manifest_shot(
        project,
        shot_id,
        {
            "status": "running",
            "operation": operation,
            "model": image_model(),
            "size": size,
            "quality": quality,
            "output_format": output_format,
            "prompt": resolved_prompt,
            "started_at": iso_now(),
        },
    )
    try:
        image_base64 = request_codex_image(resolved_prompt, size=size, quality=quality, output_format=output_format)
        return save_storyboard_image_result(
            project=project,
            shot_id=shot_id,
            prompt=resolved_prompt,
            image_base64=image_base64,
            model=image_model(),
            size=size,
            quality=quality,
            output_format=output_format,
            operation=operation,
        )
    except Exception as exc:
        update_manifest_shot(
            project,
            shot_id,
            {
                "status": "failed",
                "operation": operation,
                "error": str(exc),
                "failed_at": iso_now(),
            },
        )
        raise
