#!/usr/bin/env python3
"""Regression tests for production-facing Arc/x402 deployment assets."""

from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = ROOT / "scripts" / "live_arc_gateway_smoke.py"
RUNBOOK = ROOT / "docs" / "arc-production-deployment.md"
ENV_EXAMPLE = ROOT / "examples" / "x402-local-challenge-server" / ".env.example"
LOCAL_SERVER = ROOT / "examples" / "x402-local-challenge-server" / "server.py"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location("live_arc_gateway_smoke_under_test", SMOKE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SMOKE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ArcProductionDeploymentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.smoke = load_smoke_module()

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

    def test_local_server_uses_exact_protected_route_and_nosniff_header(self) -> None:
        port = "8092"
        server = subprocess.Popen(
            [sys.executable, str(LOCAL_SERVER), "--port", port],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            time.sleep(0.5)
            with self.assertRaises(urllib.error.HTTPError) as protected:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/protected?inspect=1", timeout=5)
            with self.assertRaises(urllib.error.HTTPError) as wrong_route:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/protected-extra", timeout=5)
        finally:
            server.terminate()
            try:
                server.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.communicate(timeout=5)

        self.assertEqual(protected.exception.code, 402)
        self.assertEqual(protected.exception.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(wrong_route.exception.code, 404)
        protected.exception.close()
        wrong_route.exception.close()

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

    def test_live_smoke_rejects_unsupported_url_scheme_without_proof(self) -> None:
        env = dict(os.environ)
        env["ARC_PAID_AGENT_URL"] = "file:///tmp/protected.json"
        env.pop("ARC_LIVE_X_PAYMENT", None)
        completed = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--expect-402-only"],
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("valid http or https url", (completed.stdout + completed.stderr).lower())

    def test_live_smoke_rejects_url_credentials_and_invalid_timeout(self) -> None:
        env = dict(os.environ)
        env["ARC_PAID_AGENT_URL"] = "https://user:password@example.invalid/protected"
        env.pop("ARC_LIVE_X_PAYMENT", None)
        credentials = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--expect-402-only"],
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
        )
        timeout = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--expect-402-only", "--timeout-seconds", "0"],
            text=True,
            capture_output=True,
            env={**env, "ARC_PAID_AGENT_URL": "https://example.invalid/protected"},
            timeout=10,
        )

        self.assertEqual(credentials.returncode, 2)
        self.assertIn("embedded credentials", (credentials.stdout + credentials.stderr).lower())
        self.assertEqual(timeout.returncode, 2)
        self.assertIn("at most 60", (timeout.stdout + timeout.stderr).lower())

    def test_live_smoke_response_must_be_bounded_json_object(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON object"):
            self.smoke.decode_json_object(io.BytesIO(b"[]"))
        with self.assertRaisesRegex(ValueError, "1 MB safety limit"):
            self.smoke.decode_json_object(
                io.BytesIO(b"{" + b" " * self.smoke.MAX_RESPONSE_BYTES + b"}")
            )

    def test_live_smoke_requires_usdc_and_mainnet_false(self) -> None:
        payload = {
            "accepts": [{"network": "arc-testnet", "asset": "USDC"}],
            "mainnetEnabled": False,
            "mcpManifest": {
                "safety": {
                    "transactionBroadcast": False,
                    "humanApprovalRequired": True,
                }
            },
        }
        self.smoke.validate_402(402, payload)

        changed_asset = {**payload, "accepts": [{"network": "arc-testnet", "asset": "EURC"}]}
        with self.assertRaisesRegex(SystemExit, "pinned USDC"):
            self.smoke.validate_402(402, changed_asset)

        changed_mainnet = {**payload, "mainnetEnabled": True}
        with self.assertRaisesRegex(SystemExit, "mainnetEnabled"):
            self.smoke.validate_402(402, changed_mainnet)

    def test_live_smoke_never_follows_redirects_or_forwards_payment_header(self) -> None:
        requests: list[tuple[str, str | None]] = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
                requests.append((self.path, self.headers.get("X-Payment")))
                body = b"{}"
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/target")
                else:
                    self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, _payload = self.smoke.http_json(
                f"http://127.0.0.1:{server.server_port}/redirect",
                timeout=5,
                x_payment="proof-must-not-be-forwarded",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(status, 302)
        self.assertEqual(requests, [("/redirect", "proof-must-not-be-forwarded")])


if __name__ == "__main__":
    unittest.main()
