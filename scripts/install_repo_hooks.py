#!/usr/bin/env python3
"""Install repository-owned hooks without overwriting unknown local hooks."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "hooks" / "pre-commit"
MANAGED_MARKER = "arc-builder-managed-hook:v1"


def resolve_hooks_dir() -> Path:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "rev-parse",
            "--git-path",
            "hooks",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("unable to resolve the repository hooks directory")
    candidate = Path(result.stdout.strip())
    return (ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()


def install() -> Path:
    if not SOURCE.is_file():
        raise RuntimeError(f"managed hook source is missing: {SOURCE}")
    hooks_dir = resolve_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / "pre-commit"
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if MANAGED_MARKER not in existing:
            raise RuntimeError(
                f"refusing to overwrite an unmanaged pre-commit hook: {target}"
            )
    shutil.copy2(SOURCE, target)
    target.chmod(target.stat().st_mode | 0o111)
    return target


def main() -> int:
    try:
        target = install()
    except (OSError, RuntimeError) as exc:
        print(f"hook installation failed: {exc}", file=sys.stderr)
        return 1
    print(f"installed repository pre-commit guard: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
