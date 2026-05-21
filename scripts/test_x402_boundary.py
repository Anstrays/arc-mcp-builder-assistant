#!/usr/bin/env python3
"""Regression tests for the local x402 verifier boundary example."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "examples" / "x402-local-challenge-server" / "server.py"


def load_server_module():
    spec = importlib.util.spec_from_file_location("x402_local_challenge_server", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SERVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class X402BoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = load_server_module()
        self.config = self.server.PaymentConfig.demo()

    def test_missing_payment_returns_402_challenge_without_broadcast(self) -> None:
        response = self.server.handle_protected_request({}, self.config)

        self.assertEqual(response.status, 402)
        self.assertEqual(response.body["error"], "payment_required")
        self.assertTrue(response.body["humanApprovalRequired"])
        self.assertFalse(response.body["transactionBroadcast"])
        self.assertEqual(response.body["accepts"][0]["network"], "arc-testnet")
        self.assertEqual(response.body["accepts"][0]["asset"], "USDC")
        self.assertEqual(response.body["accepts"][0]["amount"], "0.01")
        self.assertEqual(response.body["verifierMode"], "local-simulation")

    def test_invalid_local_proof_is_rejected_and_never_settled(self) -> None:
        response = self.server.handle_protected_request({"X-Payment": "not-a-local-proof"}, self.config)

        self.assertEqual(response.status, 402)
        self.assertEqual(response.body["error"], "payment_verification_failed")
        self.assertFalse(response.body["settled"])
        self.assertFalse(response.body["transactionBroadcast"])

    def test_valid_local_proof_returns_protected_payload_with_receipt(self) -> None:
        challenge = self.server.build_payment_challenge(self.config)
        proof = f"local-demo:{challenge['id']}:{self.config.amount}"

        response = self.server.handle_protected_request({"X-Payment": proof}, self.config)

        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["ok"], True)
        self.assertEqual(response.body["data"]["message"], "Protected Arc builder resource unlocked.")
        self.assertEqual(response.body["receipt"]["verifierMode"], "local-simulation")
        self.assertFalse(response.body["receipt"]["transactionBroadcast"])
        self.assertFalse(response.body["receipt"]["mainnetEnabled"])

    def test_demo_config_is_safe_by_default(self) -> None:
        self.assertEqual(self.config.network, "arc-testnet")
        self.assertTrue(self.config.human_approval_required)
        self.assertFalse(self.config.mainnet_enabled)
        self.assertIn("0x", self.config.pay_to)


if __name__ == "__main__":
    unittest.main()
