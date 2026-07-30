#!/usr/bin/env python3
"""Preflight the official Eagle MCP and optionally install its bundled Skill for Codex."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from eagle_mcp_client import DEFAULT_EAGLE_MCP_URL, EagleMcpClient, EagleMcpError


OFFICIAL_SKILL_NAME = "eagle-skill"


def codex_home() -> Path:
    """Return Codex's standard home without depending on a particular shell."""

    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def official_skill_source_candidates() -> list[Path]:
    """Return known Eagle MCP plugin locations that bundle the official Skill."""

    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Eagle" / "Plugins" / "mcp-server" / "skills" / OFFICIAL_SKILL_NAME)
    candidates.extend(
        [
            Path.home() / "Library" / "Application Support" / "Eagle" / "Plugins" / "mcp-server" / "skills" / OFFICIAL_SKILL_NAME,
            Path.home() / ".config" / "Eagle" / "Plugins" / "mcp-server" / "skills" / OFFICIAL_SKILL_NAME,
        ]
    )
    return candidates


def locate_official_skill_source() -> Path | None:
    for candidate in official_skill_source_candidates():
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def installed_skill_path() -> Path:
    return codex_home() / "skills" / OFFICIAL_SKILL_NAME


def redact_app_info(value: Any) -> dict[str, Any]:
    """Retain compatibility diagnostics without printing private library paths."""

    info = value if isinstance(value, dict) else {}
    return {key: info[key] for key in ("version", "build", "platform", "locale", "arch") if key in info}


def preflight(mcp_url: str) -> dict[str, Any]:
    installed = installed_skill_path()
    source = locate_official_skill_source()
    result: dict[str, Any] = {
        "endpoint": mcp_url,
        "official_skill": {
            "installed": (installed / "SKILL.md").is_file(),
            "installed_path": str(installed),
            "plugin_bundle_found": source is not None,
        },
    }
    try:
        result["app"] = redact_app_info(EagleMcpClient(mcp_url).call_tool("get_app_info"))
        result["status"] = "ready" if result["official_skill"]["installed"] else "mcp_ready_skill_missing"
    except EagleMcpError as exc:
        result["status"] = "mcp_unavailable"
        result["error"] = str(exc)
    return result


def install_official_skill(*, overwrite: bool) -> Path:
    source = locate_official_skill_source()
    if source is None:
        raise FileNotFoundError(
            "Official Eagle Skill bundle was not found. In Eagle, install and enable the Eagle MCP plugin first."
        )
    destination = installed_skill_path()
    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"Official Eagle Skill is already installed: {destination}")
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-url", default=DEFAULT_EAGLE_MCP_URL)
    parser.add_argument("--json", action="store_true", help="print machine-readable status")
    parser.add_argument(
        "--install-official-skill",
        action="store_true",
        help="copy Eagle MCP's bundled official Skill into CODEX_HOME/skills",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace an existing official Eagle Skill")
    args = parser.parse_args()

    if args.overwrite and not args.install_official_skill:
        parser.error("--overwrite requires --install-official-skill")
    if args.install_official_skill:
        try:
            destination = install_official_skill(overwrite=args.overwrite)
        except (FileNotFoundError, FileExistsError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"Installed official Eagle Skill: {destination}")

    result = preflight(args.mcp_url)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Eagle MCP: {result['status']}")
        if result.get("app"):
            app = result["app"]
            print(f"Eagle: {app.get('version', '?')} (Build {app.get('build', '?')}) on {app.get('platform', '?')}")
        if result.get("error"):
            print(f"Detail: {result['error']}")
        skill = result["official_skill"]
        print(f"Official Eagle Skill: {'installed' if skill['installed'] else 'missing'}")
        if result["status"] == "mcp_unavailable":
            print("Fix: open Eagle, then install and enable the 'Eagle MCP' plugin (default endpoint: 127.0.0.1:41596).")
        elif not skill["installed"]:
            print("Fix: run this command with --install-official-skill after the Eagle MCP plugin is installed.")
    return 0 if result["status"] in {"ready", "mcp_ready_skill_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
