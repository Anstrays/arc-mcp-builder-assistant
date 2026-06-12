#!/usr/bin/env python3
"""Static security and reliability checks for the dependency-free docs viewer."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "docs" / "viewer.js"


def main() -> None:
    viewer = VIEWER.read_text(encoding="utf-8")
    for marker in (
        "function escapeHtml(value)",
        "let html = escapeHtml(line);",
        "const DOC_TIMEOUT_MS = 8_000;",
        "const MAX_DOC_BYTES = 1_000_000;",
        "async function fetchDocText(path)",
        "new AbortController()",
        "new TextEncoder().encode(markdown).byteLength",
        "window.clearTimeout(timeout)",
        "const markdown = await fetchDocText(page.path);",
        "/^(https?:|mailto:|tel:)/i",
        'rel="noopener noreferrer"',
    ):
        assert marker in viewer, f"docs/viewer.js missing security marker: {marker}"

    for forbidden in ("eval(", "new Function(", "document.write(", "javascript:", "data:text/html"):
        assert forbidden not in viewer, f"docs/viewer.js contains forbidden executable marker: {forbidden}"

    print("docs viewer security tests passed")


if __name__ == "__main__":
    main()
