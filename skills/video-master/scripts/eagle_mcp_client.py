#!/usr/bin/env python3
"""Small read-only client for Eagle's official local MCP plugin."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


DEFAULT_EAGLE_MCP_URL = "http://127.0.0.1:41596/mcp"
MCP_PROTOCOL_VERSION = "2025-03-26"


class EagleMcpError(RuntimeError):
    """Raised when Eagle's official MCP plugin cannot complete a read."""


def decode_mcp_message(payload: str) -> dict[str, Any]:
    """Decode either JSON or the single-message SSE response used by Eagle MCP."""

    text = payload.strip()
    if not text:
        raise EagleMcpError("Eagle MCP returned an empty response")
    if text.startswith("{"):
        message = json.loads(text)
    else:
        lines = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
        if not lines:
            raise EagleMcpError("Eagle MCP did not return a JSON-RPC message")
        message = json.loads("\n".join(lines))
    if not isinstance(message, dict):
        raise EagleMcpError("Eagle MCP response must be a JSON object")
    if isinstance(message.get("error"), dict):
        detail = message["error"].get("message") or message["error"]
        raise EagleMcpError(f"Eagle MCP error: {detail}")
    return message


def decode_tool_result(message: dict[str, Any]) -> Any:
    """Extract the structured object embedded in an MCP tool result."""

    result = message.get("result")
    if not isinstance(result, dict):
        raise EagleMcpError("Eagle MCP response is missing result")
    if result.get("isError") is True:
        raise EagleMcpError("Eagle MCP tool reported an error")
    content = result.get("content")
    if not isinstance(content, list):
        raise EagleMcpError("Eagle MCP tool response is missing content")
    text_parts = [str(item.get("text", "")) for item in content if isinstance(item, dict) and item.get("type") == "text"]
    if not text_parts:
        raise EagleMcpError("Eagle MCP tool response contains no text payload")
    try:
        value = json.loads("\n".join(text_parts))
    except json.JSONDecodeError as exc:
        raise EagleMcpError("Eagle MCP tool response is not valid JSON") from exc
    if isinstance(value, dict) and value.get("success") is False:
        raise EagleMcpError(str(value.get("message") or "Eagle MCP tool failed"))
    return value.get("data") if isinstance(value, dict) and "data" in value else value


def coerce_item_list(value: Any) -> list[dict[str, Any]]:
    """Normalize the item-list shapes returned by the official MCP plugin."""

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "results", "data"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    raise EagleMcpError("Eagle MCP did not return an item list")


class EagleMcpClient:
    """Read-only operations used by the video-project asset intake path."""

    def __init__(self, base_url: str = DEFAULT_EAGLE_MCP_URL, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        request_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:240]
            raise EagleMcpError(f"Eagle MCP HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise EagleMcpError(f"Unable to reach Eagle MCP at {self.base_url}: {exc}") from exc
        return decode_tool_result(decode_mcp_message(body))

    def selected_items(self) -> list[dict[str, Any]]:
        return coerce_item_list(self.call_tool("item_get_selected", {"fullDetails": True}))

    def items_by_id(self, item_ids: list[str]) -> list[dict[str, Any]]:
        return coerce_item_list(self.call_tool("item_get", {"ids": item_ids, "fullDetails": True, "limit": len(item_ids)}))

    def query_items(self, query: str, *, full_details: bool = True) -> list[dict[str, Any]]:
        """Run Eagle's text query without implying any library mutation."""

        return coerce_item_list(self.call_tool("item_query", {"query": query, "fullDetails": full_details}))
