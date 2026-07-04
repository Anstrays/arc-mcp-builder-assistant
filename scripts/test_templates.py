#!/usr/bin/env python3
"""Tests for builder starter templates.

Standard-library unittest only. Verifies structure, safety labels, and that the
x402 starter server runs in print-only modes without network dependencies.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"

TEMPLATES = ["payment-intent-starter", "x402-agent-starter", "job-escrow-starter"]


class StructureTests(unittest.TestCase):
    def test_each_template_has_readme(self) -> None:
        for name in TEMPLATES:
            with self.subTest(template=name):
                readme = TEMPLATES_DIR / name / "README.md"
                self.assertTrue(readme.exists(), f"missing {readme}")
                text = readme.read_text(encoding="utf-8")
                self.assertIn("Arc", text)
                self.assertIn("Testnet", text)

    def test_payment_intent_has_index_html(self) -> None:
        path = TEMPLATES_DIR / "payment-intent-starter" / "index.html"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Arc Testnet", text)
        self.assertIn("does not sign", text)
        self.assertIn("./index.js", text)

    def test_payment_intent_has_index_js(self) -> None:
        path = TEMPLATES_DIR / "payment-intent-starter" / "index.js"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("addEventListener", text)

    def test_job_escrow_has_index_html(self) -> None:
        path = TEMPLATES_DIR / "job-escrow-starter" / "index.html"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Job escrow", text)
        self.assertIn("human-approved", text)
        self.assertIn("./index.js", text)

    def test_job_escrow_has_index_js(self) -> None:
        path = TEMPLATES_DIR / "job-escrow-starter" / "index.js"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("addEventListener", text)

    def test_x402_starter_has_server(self) -> None:
        path = TEMPLATES_DIR / "x402-agent-starter" / "server.py"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("mainnet is disabled", text)
        self.assertIn("USDC", text)
        self.assertIn("local-demo", text)


class SafetyTests(unittest.TestCase):
    def test_no_inline_event_handlers_forbidden_by_validator(self) -> None:
        # validate_repo.py already checks this; here we guard templates explicitly.
        for name in TEMPLATES:
            for html in (TEMPLATES_DIR / name).glob("*.html"):
                with self.subTest(template=name, file=html.name):
                    text = html.read_text(encoding="utf-8")
                    self.assertNotRegex(text, r"\son\w+\s*=\s*['\"]", msg="inline event handler found")

    def test_x402_mainnet_gate(self) -> None:
        env = os.environ.copy()
        env["X402_DEMO_MAINNET_ENABLED"] = "true"
        result = subprocess.run(
            [sys.executable, str(TEMPLATES_DIR / "x402-agent-starter" / "server.py"), "--print-manifest"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mainnet is disabled", result.stderr)


class RuntimeTests(unittest.TestCase):
    def test_x402_print_manifest(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TEMPLATES_DIR / "x402-agent-starter" / "server.py"), "--print-manifest"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        manifest = json.loads(result.stdout)
        self.assertEqual(manifest["network"], "arc-testnet")
        self.assertEqual(manifest["asset"], "USDC")
        self.assertTrue(manifest["safety"]["noPrivateKeys"])

    def test_x402_print_challenge(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TEMPLATES_DIR / "x402-agent-starter" / "server.py"), "--print-challenge"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        challenge = json.loads(result.stdout)
        self.assertIn("localDemoProof", challenge)
        self.assertTrue(challenge["localDemoProof"].startswith("local-demo:"))


if __name__ == "__main__":
    unittest.main()
