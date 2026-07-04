#!/usr/bin/env python3
"""Run the dependency-free transaction-status behavioral harness."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "transaction_status_behavior_harness.mjs"


def main() -> int:
    node = shutil.which("node")
    if not node:
        raise SystemExit(
            "transaction status behavior test requires Node.js 18+; no npm packages are required"
        )
    completed = subprocess.run(
        [node, str(HARNESS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "transaction status behavior harness failed:\n"
            f"{completed.stdout}{completed.stderr}"
        )
    print(completed.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
