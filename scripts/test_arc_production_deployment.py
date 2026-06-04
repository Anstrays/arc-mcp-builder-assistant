#!/usr/bin/env python3
"""Regression tests for production-facing Arc/x402 deployment assets."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = ROOT / "scripts" / "live_arc_gateway_smoke.py"
RUNBOOK = ROOT / "docs" / "arc-production-deployment.md"
ENV_EXAMPLE = ROOT / "examples" / "x402-local-challenge-server" / ".env.example"
LOCAL_SERVER = ROOT / "examples" / "x402-local-challenge-server" / "server.py"


class ArcProductionDeploymentTests(unittest.TestCase):
    def test_production_runbook_documents_safe_gateway_handoff(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        lowered = text.lower()

        for marker in (
            "arc_paid_agent_url",
            "arc_live_x_payment",
            "--expect-402-only",
            "circle gateway",
            "x402",
            "rollback",
            "human approval",
            "no private keys",
            "no seed phrases",
            "does not create payments",
        ):
            self.assertIn(marker, lowered)

    def test_runbook_has_explicit_production_gap_list_before_real_verifier(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        lowered = text.lower()

        for marker in (
            "production gap list",
            "nonce",
            "replay protection",
            "settlement finality",
            "redacted audit log",
            "testnet-only wallet approval",
            "feature flag",
            "fail closed",
        ):
            self.assertIn(marker, lowered)

    def test_env_example_contains_only_placeholder_configuration(self) -> None:
        text = ENV_EXAMPLE.read_text(encoding="utf-8")
        lowered = text.lower()

        for marker in (
            "arc_paid_agent_url=",
            "arc_live_x_payment=",
            "circle_gateway_api" "_key=",
            "x402_gateway_verifier_url=",
            "expect_402_only=true",
            "placeholder only",
        ):
            self.assertIn(marker, lowered)
        self.assertNotIn("local-demo:", text)
        self.assertNotIn("-----BEGIN", text)
        self.assertNotIn("sk-", text)

    def test_live_smoke_fails_safely_without_target_url(self) -> None:
        env = dict(os.environ)
        env.pop("ARC_PAID_AGENT_URL", None)
        env.pop("ARC_LIVE_X_PAYMENT", None)
        completed = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT)],
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 2)
        combined = completed.stdout + completed.stderr
        self.assertIn("ARC_PAID_AGENT_URL", combined)
        self.assertIn("no payments were created", combined.lower())

    def test_live_smoke_accepts_local_402_only_mode(self) -> None:
        port = "8091"
        server = subprocess.Popen(
            [sys.executable, str(LOCAL_SERVER), "--port", port],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            time.sleep(0.5)
            env = dict(os.environ)
            env["ARC_PAID_AGENT_URL"] = f"http://127.0.0.1:{port}/protected"
            env.pop("ARC_LIVE_X_PAYMENT", None)
            completed = subprocess.run(
                [sys.executable, str(SMOKE_SCRIPT), "--expect-402-only"],
                text=True,
                capture_output=True,
                env=env,
                timeout=10,
            )
        finally:
            server.terminate()
            try:
                server.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.communicate(timeout=5)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("unpaid 402 challenge accepted", completed.stdout.lower())
        self.assertIn("transactionbroadcast=false", completed.stdout.lower())

    def test_live_smoke_refuses_to_send_payment_proof_to_http_url(self) -> None:
        env = dict(os.environ)
        env["ARC_PAID_AGENT_URL"] = "http://127.0.0.1:8091/protected"
        env["ARC_LIVE_X_PAYMENT"] = "live-proof-placeholder"
        completed = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT)],
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 2)
        combined = completed.stdout + completed.stderr
        self.assertIn("refusing to send arc_live_x_payment", combined.lower())
        self.assertIn("non-https", combined.lower())


if __name__ == "__main__":
    unittest.main()
