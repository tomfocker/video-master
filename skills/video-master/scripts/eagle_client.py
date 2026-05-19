#!/usr/bin/env python3
"""Read-only helpers for Eagle local libraries and Web API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, NamedTuple


DEFAULT_EAGLE_BASE_URL = "http://localhost:41595"
MEDIA_SUFFIXES = {
    ".aac",
    ".aif",
    ".aiff",
    ".flac",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".png",
    ".wav",
}


class EagleClientError(RuntimeError):
    """Raised when Eagle API or library access fails."""


class ResolvedEagleItem(NamedTuple):
    item_id: str
    name: str
    ext: str
    path: Path
    library_path: Path
    thumbnail_path: Path | None
    metadata: dict[str, Any]

    def source_manifest(self) -> dict[str, Any]:
        return {
            "type": "eagle",
            "item_id": self.item_id,
            "name": self.name,
            "ext": self.ext,
            "path": str(self.path.resolve()),
            "library_path": str(self.library_path.resolve()),
            "thumbnail_path": str(self.thumbnail_path.resolve()) if self.thumbnail_path else False,
        }


def normalize_library_paths(paths: list[str | Path]) -> list[Path]:
    normalized: list[Path] = []
    seen: set[str] = set()
    for raw_path in paths:
        value = str(raw_path).strip()
        if not value:
            continue
        path = Path(value.rstrip("/")).expanduser()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(path)
    return normalized


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def item_dir_for(library_path: str | Path, item_id: str) -> Path:
    return Path(library_path).expanduser() / "images" / f"{item_id}.info"


def is_original_media_file(path: Path, preferred_ext: str) -> bool:
    if not path.is_file():
        return False
    if path.name == "metadata.json" or path.name.endswith("_thumbnail.png"):
        return False
    suffix = path.suffix.lower()
    if preferred_ext and suffix == f".{preferred_ext.lower().lstrip('.')}":
        return True
    return suffix in MEDIA_SUFFIXES


def resolve_item_file(item_id: str, library_path: str | Path) -> ResolvedEagleItem:
    library = Path(library_path).expanduser()
    item_dir = item_dir_for(library, item_id)
    if not item_dir.is_dir():
        raise FileNotFoundError(f"Eagle item directory does not exist: {item_dir}")

    metadata = read_json(item_dir / "metadata.json", {})
    if not isinstance(metadata, dict):
        metadata = {}
    ext = str(metadata.get("ext") or "").lower().lstrip(".")
    candidates = sorted(
        [path for path in item_dir.iterdir() if is_original_media_file(path, ext)],
        key=lambda path: (path.suffix.lower() != f".{ext}" if ext else False, path.name),
    )
    if not candidates:
        raise FileNotFoundError(f"No original media file found for Eagle item: {item_dir}")

    thumbnail_candidates = sorted(item_dir.glob("*_thumbnail.png"))
    media_path = candidates[0]
    return ResolvedEagleItem(
        item_id=str(metadata.get("id") or item_id),
        name=str(metadata.get("name") or media_path.stem),
        ext=ext or media_path.suffix.lower().lstrip("."),
        path=media_path,
        library_path=library,
        thumbnail_path=thumbnail_candidates[0] if thumbnail_candidates else None,
        metadata=metadata,
    )


def resolve_item_file_from_libraries(item_id: str, library_paths: list[str | Path]) -> ResolvedEagleItem:
    errors: list[str] = []
    for library_path in normalize_library_paths(library_paths):
        try:
            return resolve_item_file(item_id, library_path)
        except FileNotFoundError as exc:
            errors.append(str(exc))
    joined = "\n".join(errors) if errors else "no Eagle library paths were provided"
    raise FileNotFoundError(f"Could not resolve Eagle item {item_id}.\n{joined}")


class EagleClient:
    def __init__(self, base_url: str = DEFAULT_EAGLE_BASE_URL, timeout: float = 8.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise EagleClientError(f"Unable to reach Eagle at {self.base_url}: {exc}") from exc
        data = json.loads(payload)
        if data.get("status") != "success":
            raise EagleClientError(str(data.get("message") or data.get("data") or data))
        return data.get("data")

    def application_info(self) -> dict[str, Any]:
        data = self.get("/api/application/info")
        return data if isinstance(data, dict) else {}

    def library_info(self) -> dict[str, Any]:
        data = self.get("/api/library/info")
        return data if isinstance(data, dict) else {}

    def library_history(self) -> list[Path]:
        data = self.get("/api/library/history")
        if not isinstance(data, list):
            return []
        return normalize_library_paths(data)

    def item_list(self, **params: Any) -> list[dict[str, Any]]:
        data = self.get("/api/item/list", params)
        return data if isinstance(data, list) else []

    def library_candidates(self) -> list[Path]:
        candidates: list[str | Path] = []
        info = self.library_info()
        library = info.get("library") if isinstance(info, dict) else None
        if isinstance(library, dict) and library.get("path"):
            candidates.append(str(library["path"]))
        candidates.extend(self.library_history())
        return normalize_library_paths(candidates)


def resolve_item_file_from_eagle(
    item_id: str,
    library_path: str | Path | None = None,
    client: EagleClient | None = None,
) -> ResolvedEagleItem:
    if library_path:
        return resolve_item_file(item_id, library_path)
    client = client or EagleClient()
    return resolve_item_file_from_libraries(item_id, client.library_candidates())
