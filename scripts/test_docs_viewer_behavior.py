#!/usr/bin/env python3
"""Run the dependency-free actual-JavaScript docs viewer behavior harness."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "docs_viewer_behavior_harness.mjs"


def main() -> None:
    node = shutil.which("node")
    if not node:
        raise SystemExit("docs viewer behavior test requires Node.js 18+; no npm packages are required")
    completed = subprocess.run(
        [node, str(HARNESS)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout or "docs viewer behavior harness failed")
    print(completed.stdout.strip())


if __name__ == "__main__":
    main()
