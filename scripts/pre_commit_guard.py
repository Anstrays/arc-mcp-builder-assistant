#!/usr/bin/env python3
"""Reject secret-like and generated files from the staged commit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

BLOCKED_DIRECTORIES = {
    ".arc-release-packet",
    ".graphify-out",
    ".hermes",
    "build",
    "dist",
    "graphify-out",
    "node_modules",
}
BLOCKED_SUFFIXES = {".key", ".p12", ".pem", ".pfx"}
ALLOWED_ENV_FILES = {".env.example"}


def blocked_reason(raw_path: str) -> str | None:
    """Return a stable reason without reading or printing file contents."""
    normalized = raw_path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    path = PurePosixPath(normalized)
    lowered_parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()

    if any(part in BLOCKED_DIRECTORIES for part in lowered_parts):
        return "generated or local-only directory"
    if any(part.startswith(".arc-test-") for part in lowered_parts):
        return "temporary Arc test artifact"
    if any(part.endswith(".egg-info") for part in lowered_parts):
        return "Python build metadata"
    if name == ".env" or (name.startswith(".env.") and name not in ALLOWED_ENV_FILES):
        return "environment or credential file"
    if path.suffix.lower() in BLOCKED_SUFFIXES:
        return "private-key or credential container"
    return None


def staged_paths() -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
            "-z",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("unable to inspect staged paths")
    return [
        entry.decode("utf-8", "surrogateescape")
        for entry in result.stdout.split(b"\0")
        if entry
    ]


def main() -> int:
    try:
        paths = staged_paths()
    except (OSError, RuntimeError) as exc:
        print(f"pre-commit guard failed closed: {exc}", file=sys.stderr)
        return 1

    blocked = [(path, reason) for path in paths if (reason := blocked_reason(path))]
    if blocked:
        print("pre-commit guard blocked local or sensitive paths:", file=sys.stderr)
        for path, reason in blocked:
            print(f"  - {path}: {reason}", file=sys.stderr)
        return 1
    print(f"pre-commit path guard passed ({len(paths)} staged paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
