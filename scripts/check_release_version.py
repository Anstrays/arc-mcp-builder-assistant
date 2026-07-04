#!/usr/bin/env python3
"""Fail closed unless a release tag matches every public package version."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[a-z0-9.-]+)?$")


class ReleaseVersionError(ValueError):
    """Raised when release metadata is missing, malformed, or inconsistent."""


def _extract(path: Path, pattern: str, label: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReleaseVersionError(f"unable to read {label}: {path}") from exc
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ReleaseVersionError(f"unable to find {label} in {path}")
    return match.group(1)


def observed_versions(root: Path = ROOT) -> dict[str, str]:
    return {
        "pyproject": _extract(
            root / "pyproject.toml",
            r'^version\s*=\s*"([^"]+)"\s*$',
            "project version",
        ),
        "package": _extract(
            root / "arc_builder_kit/__init__.py",
            r'^__version__\s*=\s*"([^"]+)"\s*$',
            "package version",
        ),
        "source_cli": _extract(
            root / "scripts/arc_builder_cli.py",
            r'version="%\(prog\)s\s+([^"]+)"',
            "source CLI version",
        ),
        "source_mcp": _extract(
            root / "scripts/arc_builder_mcp_server.py",
            r'^SERVER_VERSION\s*=\s*"([^"]+)"\s*$',
            "source MCP version",
        ),
    }


def validate_release_tag(tag: str, root: Path = ROOT) -> str:
    if not tag or not tag.startswith("v"):
        raise ReleaseVersionError("release tag must use the exact v<version> form")
    tag_version = tag[1:]
    if not VERSION_PATTERN.fullmatch(tag_version):
        raise ReleaseVersionError(f"release tag contains an invalid version: {tag}")
    versions = observed_versions(root)
    mismatches = {
        label: version for label, version in versions.items() if version != tag_version
    }
    if mismatches:
        details = ", ".join(f"{label}={value}" for label, value in sorted(mismatches.items()))
        raise ReleaseVersionError(
            f"release tag {tag} does not match repository versions: {details}"
        )
    return tag_version


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        default=os.environ.get("GITHUB_REF_NAME", ""),
        help="release tag to verify (default: GITHUB_REF_NAME)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        version = validate_release_tag(args.tag)
    except ReleaseVersionError as exc:
        print(f"release version check failed: {exc}", file=sys.stderr)
        return 1
    print(f"release version check passed: v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
