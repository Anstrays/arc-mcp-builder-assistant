#!/usr/bin/env python3
"""Run the dependency-free local regression suite.

This is the canonical quickstart/CI command for the repo. Individual test
scripts remain useful for targeted debugging, but new builders should be able
to run one command and get a clear pass/fail result.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = [
    "scripts/test_payment_intent_playground.py",
    "scripts/test_x402_boundary.py",
    "scripts/test_arc_production_deployment.py",
    "scripts/test_receipt_verifier_playground.py",
    "scripts/test_transaction_status_playground.py",
    "scripts/test_agent_commerce_components.py",
    "scripts/test_agent_commerce_flows.py",
    "scripts/test_agent_commerce_review_packet.py",
    "scripts/test_agent_identity_profile_preview.py",
    "scripts/test_job_escrow_simulator.py",
    "scripts/test_operator_evidence.py",
    "scripts/test_operator_evidence_draft.py",
    "scripts/validate_repo.py",
]


def run_check(relative: str) -> None:
    command = [sys.executable, relative]
    print(f"[test_all] running: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(f"[test_all] failed: {relative} exited with {completed.returncode}")


def main() -> int:
    for relative in CHECKS:
        run_check(relative)
    print(f"[test_all] all checks passed ({len(CHECKS)} commands)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
