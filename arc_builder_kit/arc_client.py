"""Async-friendly, standard-library client for Arc's documentation MCP."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Coroutine
from urllib import request as urllib_request
from urllib.parse import urlsplit

ARC_MCP_URL = "https://docs.arc.network/mcp"
ARC_LLMS_TXT = "https://docs.arc.network/llms.txt"
TIMEOUT_SEC = 30
MAX_RESPONSE_BYTES = 2_000_000
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass
class DocResult:
    """A single documentation snippet or page result."""

    content: str
    source: str = ""
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _validate_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("documentation URL must not contain credentials or a fragment")
    if parsed.scheme == "https" and parsed.hostname:
        return url
    if parsed.scheme == "http" and parsed.hostname in LOCAL_HOSTS:
        return url
    raise ValueError("documentation URL must use HTTPS or local HTTP")


def _read_response(response: Any) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared:
        try:
            if int(declared) > MAX_RESPONSE_BYTES:
                raise ValueError("documentation response exceeds the 2 MB safety limit")
        except ValueError as exc:
            if "safety limit" in str(exc):
                raise
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("documentation response exceeds the 2 MB safety limit")
    return body


def _post_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib_request.Request(
        _validate_url(url),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(request, timeout=timeout) as response:
        parsed = json.loads(_read_response(response).decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Arc docs MCP response must be a JSON object")
    return parsed


def _get_text(url: str, timeout: int) -> str:
    request = urllib_request.Request(
        _validate_url(url),
        headers={"Accept": "text/plain"},
        method="GET",
    )
    with urllib_request.urlopen(request, timeout=timeout) as response:
        return _read_response(response).decode("utf-8")


def _make_request(
    method: str,
    params: dict[str, Any] | None = None,
    req_id: int = 1,
) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": req_id,
    }


def _parse_tool_call_result(raw: dict[str, Any]) -> list[DocResult]:
    """Extract text content from an MCP tool-call result."""

    results: list[DocResult] = []
    content_list = raw.get("result", {}).get("content", [])
    if not isinstance(content_list, list):
        return results
    for item in content_list:
        if isinstance(item, dict):
            text = item.get("text", "")
            if isinstance(text, str) and text:
                results.append(
                    DocResult(
                        content=text,
                        source=item.get("source", "") if isinstance(item.get("source", ""), str) else "",
                        metadata={key: value for key, value in item.items() if key not in ("text", "source")},
                    )
                )
        elif isinstance(item, str):
            results.append(DocResult(content=item))
    return results


class ArcDocsClient:
    """Client for the Arc MCP documentation server without third-party deps."""

    def __init__(self, url: str = ARC_MCP_URL, timeout: int = TIMEOUT_SEC) -> None:
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("timeout must be a positive integer")
        self._url = _validate_url(url)
        self._timeout = timeout

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(_post_json, self._url, payload, self._timeout)

    async def search(self, query: str, limit: int = 5) -> list[DocResult]:
        payload = _make_request(
            "tools/call",
            {"name": "search", "arguments": {"query": query, "limit": limit}},
        )
        return _parse_tool_call_result(await self._post(payload))

    async def get_page(self, path: str) -> DocResult | None:
        payload = _make_request(
            "tools/call",
            {"name": "get_page", "arguments": {"path": path}},
        )
        results = _parse_tool_call_result(await self._post(payload))
        return results[0] if results else None

    async def list_tools(self) -> list[dict[str, Any]]:
        raw = await self._post(_make_request("tools/list"))
        tools = raw.get("result", {}).get("tools", [])
        return tools if isinstance(tools, list) else []

    async def fetch_llms_txt(self) -> str:
        return await asyncio.to_thread(_get_text, ARC_LLMS_TXT, self._timeout)

    async def close(self) -> None:
        """Retained for API compatibility; stdlib requests hold no client state."""

    def _run_sync(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run one client coroutine synchronously."""

        return asyncio.run(coro)


__all__ = ["ArcDocsClient", "DocResult"]
