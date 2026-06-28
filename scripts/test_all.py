#!/usr/bin/env python3
"""Run the dependency-free local regression suite.

This is the canonical quickstart/CI command for the repo. Individual test
scripts remain useful for targeted debugging, but new builders should be able
to run one command and get a clear pass/fail result.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_TIMEOUT_SECONDS = 120
CHECKS = [
    "scripts/check_completion.py",
    "scripts/test_completion_contract.py",
    "scripts/test_public_claims.py",
    "scripts/test_docs_viewer_security.py",
    "scripts/test_docs_viewer_behavior.py",
    "scripts/test_workflow_security.py",
    "scripts/test_arc_builder_doctor.py",
    "scripts/test_arc_release_packet.py",
    "scripts/test_arc_testnet_facts.py",
    "scripts/test_payment_intent_playground.py",
    "scripts/test_x402_boundary.py",
    "scripts/test_x402_client.py",
    "scripts/test_arc_production_deployment.py",
    "scripts/test_arc_testnet_status_helper.py",
    "scripts/test_receipt_verifier_playground.py",
    "scripts/test_receipt_viewer.py",
    "scripts/test_payment_intent_receipt_matcher.py",
    "scripts/test_transaction_status_playground.py",
    "scripts/test_transaction_status_behavior.py",
    "scripts/test_arc_testnet_wallet_send_gate.py",
    "scripts/test_arc_testnet_wallet_send_behavior.py",
    "scripts/validate_live_infrastructure_policy.py",
    "scripts/test_live_infrastructure_policy.py",
    "scripts/scan_for_secrets.py",
    "scripts/test_agent_commerce_components.py",
    "scripts/test_agent_commerce_flows.py",
    "scripts/test_agent_commerce_review_packet.py",
    "scripts/test_agent_identity_profile_preview.py",
    "scripts/test_job_escrow_simulator.py",
    "scripts/test_arc_agent_treasury_lab.py",
    "scripts/test_circle_wallet_integration.py",
    "scripts/test_agent_commerce_live.py",
    "scripts/test_operator_evidence.py",
    "scripts/test_operator_evidence_draft.py",
    "scripts/test_operator_evidence_report.py",
    "scripts/test_arc_builder_cli.py",
    "scripts/test_arc_builder_mcp_server.py",
    "scripts/test_templates.py",
    "scripts/test_package_distribution.py",
    "scripts/test_pre_commit_guard.py",
    "scripts/test_release_version.py",
    "scripts/validate_repo.py",
]


def run_check(relative: str, child_env: dict[str, str]) -> None:
    command = [sys.executable, relative]
    print(f"[test_all] running: {' '.join(command)}", flush=True)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=child_env,
            timeout=CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise SystemExit(
            f"[test_all] timed out after {CHECK_TIMEOUT_SECONDS}s: {relative}"
        ) from error
    if completed.returncode != 0:
        raise SystemExit(f"[test_all] failed: {relative} exited with {completed.returncode}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as temp_dir:
        child_env = os.environ.copy()
        for variable in ("TMPDIR", "TEMP", "TMP"):
            child_env[variable] = temp_dir
        for relative in CHECKS:
            run_check(relative, child_env)
    print(f"[test_all] all checks passed ({len(CHECKS)} commands)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
