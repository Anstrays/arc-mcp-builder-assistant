#!/usr/bin/env python3
"""Lightweight repository validation for the Arc MCP Builder Assistant.

This script enforces a few cheap, deterministic invariants so that the
GitHub Pages site cannot accidentally regress on:

- presence of the documents required by the project
- absence of obvious credential patterns
- safe HTML (no executable scripts, no inline event handlers, no broken
  anchors, external links carry rel=noopener noreferrer, images carry
  alt text)
- presence of the SEO/meta basics (lang, viewport, description, charset)

It is intentionally dependency-free so it can run in CI without setup.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "index.html",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".editorconfig",
    ".github/workflows/validate.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    "docs/arc-mcp-setup.md",
    "docs/deploy-contracts-arc.md",
    "docs/builder-workflows.md",
    "docs/payment-intent-demo.md",
    "prompts/explain-arc-docs.md",
    "prompts/build-payment-intent-demo.md",
    "prompts/register-agent-notes.md",
    "prompts/deploy-contracts-on-arc.md",
    "examples/payment-intent-demo/index.html",
]

# Every HTML file in the repo is checked with these full invariants.
HTML_FILES_TO_VALIDATE = [
    "index.html",
    "examples/payment-intent-demo/index.html",
]

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}"),  # Telegram bot token shape
    re.compile(
        r"(?i)(api[_-]?key|secret|password|private[_-]?key|entity[_-]?secret|bot[_-]?token)"
        r"\s*=\s*['\"][^'\"]{8,}['\"]"
    ),
    re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
]

# Files we never want to scan for secrets — they only describe patterns,
# not real credentials.
SECRET_SCAN_SKIP = {
    Path("scripts/validate_repo.py"),
}

# script type values that are inert (no JavaScript execution).
INERT_SCRIPT_TYPES = {
    "application/ld+json",
    "application/json",
    "text/plain",
}


class HtmlInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.html_lang: str | None = None
        self.has_charset = False
        self.has_viewport = False
        self.has_description = False
        self.script_type_stack: list[str] = []
        self.script_text_segments: list[str] = []
        self._in_inert_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "") for key, value in attrs}
        self.elements.append((tag, attr))
        if "id" in attr:
            self.ids.add(attr["id"])
        if tag == "html":
            self.html_lang = attr.get("lang")
        if tag == "meta":
            if attr.get("charset"):
                self.has_charset = True
            name = attr.get("name", "").lower()
            if name == "viewport":
                self.has_viewport = True
            if name == "description" and attr.get("content"):
                self.has_description = True
        if tag == "script":
            script_type = attr.get("type", "").lower()
            self.script_type_stack.append(script_type)
            self._in_inert_script = script_type in INERT_SCRIPT_TYPES

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.script_type_stack:
            self.script_type_stack.pop()
            self._in_inert_script = bool(
                self.script_type_stack
                and self.script_type_stack[-1] in INERT_SCRIPT_TYPES
            )

    def handle_data(self, data: str) -> None:
        if self.script_type_stack and not self._in_inert_script and data.strip():
            self.script_text_segments.append(data)


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def validate_required_files() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required file: {relative}")


def validate_no_secrets() -> None:
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative in SECRET_SCAN_SKIP:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"potential secret pattern in {relative}")


def validate_html_file(relative: str) -> None:
    html_path = ROOT / relative
    html = html_path.read_text(encoding="utf-8")
    if "<!doctype html>" not in html.lower():
        fail(f"{relative} is missing doctype")

    inspector = HtmlInspector()
    inspector.feed(html)

    if inspector.script_text_segments:
        fail(
            f"{relative} should not contain executable scripts; "
            "only inert types (e.g. application/ld+json) are allowed"
        )

    for tag, attrs in inspector.elements:
        if tag == "script":
            script_type = attrs.get("type", "").lower()
            if script_type and script_type not in INERT_SCRIPT_TYPES:
                fail(f"{relative}: executable script type is not allowed: {script_type}")
            if attrs.get("src"):
                fail(f"{relative}: external scripts are not allowed")
        for key in attrs:
            if key.lower().startswith("on"):
                fail(f"{relative}: inline event handler is not allowed on <{tag}>: {key}")
        if tag == "img":
            if "alt" not in attrs:
                fail(f"{relative}: <img> missing alt attribute (src={attrs.get('src','?')})")
        if tag == "a":
            href = attrs.get("href", "")
            normalized_href = href.strip().lower()
            if normalized_href.startswith("javascript:"):
                fail(f"{relative}: unsafe javascript URL: {href}")
            if href.startswith("#") and len(href) > 1 and href[1:] not in inspector.ids:
                fail(f"{relative}: broken anchor link: {href}")
            if attrs.get("target", "").strip().lower() == "_blank":
                rel = {value.lower() for value in attrs.get("rel", "").split()}
                if not {"noopener", "noreferrer"}.issubset(rel):
                    fail(f"{relative}: external link missing rel noopener noreferrer: {href}")

    if not inspector.html_lang:
        fail(f"{relative}: <html> tag must declare a lang attribute")
    if not inspector.has_charset:
        fail(f"{relative}: missing <meta charset>")
    if not inspector.has_viewport:
        fail(f"{relative}: missing <meta name=\"viewport\">")
    if not inspector.has_description:
        fail(f"{relative}: missing a non-empty <meta name=\"description\">")


def validate_html() -> None:
    for relative in HTML_FILES_TO_VALIDATE:
        validate_html_file(relative)


def main() -> None:
    validate_required_files()
    validate_no_secrets()
    validate_html()
    print("validation passed", file=sys.stdout)


if __name__ == "__main__":
    main()
