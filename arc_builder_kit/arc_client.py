"""
Arc Docs MCP Client
-------------------
Thin HTTP client for Arc's official MCP server at https://docs.arc.network/mcp.

Arc exposes two tools:
  - search(query: str)  → find relevant doc snippets
  - get_page(path: str) → retrieve full doc page content
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

ARC_MCP_URL = "https://docs.arc.network/mcp"
ARC_LLMS_TXT = "https://docs.arc.network/llms.txt"
TIMEOUT_SEC = 30


# ── data models ─────────────────────────────────────────────────


@dataclass
class DocResult:
    """A single documentation snippet or page result."""

    content: str
    source: str = ""
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ── MCP JSON-RPC helpers ────────────────────────────────────────


def _make_request(method: str, params: dict[str, Any] | None = None, req_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": req_id,
    }


def _parse_tool_call_result(raw: dict) -> list[DocResult]:
    """Extract content from an MCP tool_call result."""
    results: list[DocResult] = []
    content_list = raw.get("result", {}).get("content", [])
    for item in content_list:
        if isinstance(item, dict):
            text = item.get("text", "")
            if text:
                results.append(
                    DocResult(
                        content=text,
                        source=item.get("source", ""),
                        metadata={k: v for k, v in item.items() if k not in ("text", "source")},
                    )
                )
        elif isinstance(item, str):
            results.append(DocResult(content=item))
    return results


# ── client ──────────────────────────────────────────────────────


class ArcDocsClient:
    """Client for the Arc MCP documentation server."""

    def __init__(self, url: str = ARC_MCP_URL, timeout: int = TIMEOUT_SEC) -> None:
        self._url = url
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    # ── public API ───────────────────────────────────────────

    async def search(self, query: str, limit: int = 5) -> list[DocResult]:
        """Search Arc docs for relevant snippets matching *query*."""
        payload = _make_request(
            "tools/call",
            {
                "name": "search",
                "arguments": {"query": query, "limit": limit},
            },
        )
        resp = await self._client.post(self._url, json=payload)
        resp.raise_for_status()
        return _parse_tool_call_result(resp.json())

    async def get_page(self, path: str) -> DocResult | None:
        """Retrieve the full content of a documentation page by path."""
        payload = _make_request(
            "tools/call",
            {
                "name": "get_page",
                "arguments": {"path": path},
            },
        )
        resp = await self._client.post(self._url, json=payload)
        resp.raise_for_status()
        results = _parse_tool_call_result(resp.json())
        return results[0] if results else None

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools (for discovery)."""
        payload = _make_request("tools/list")
        resp = await self._client.post(self._url, json=payload)
        resp.raise_for_status()
        return resp.json().get("result", {}).get("tools", [])

    async def fetch_llms_txt(self) -> str:
        """Fetch the llms.txt index (machine-readable doc index)."""
        resp = await self._client.get(ARC_LLMS_TXT)
        resp.raise_for_status()
        return resp.text

    async def close(self) -> None:
        await self._client.aclose()

    # ── sync helper (for testing) ────────────────────────────

    def _run_sync(self, coro):
        """Run an async method synchronously. For tests only."""
        import asyncio
        return asyncio.run(coro)
