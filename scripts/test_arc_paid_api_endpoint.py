#!/usr/bin/env python3
"""Regression tests for the Arc Testnet paid API endpoint prototype."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "examples" / "arc-paid-api-endpoint" / "server.py"
DOC = ROOT / "docs" / "arc-paid-api-endpoint.md"
README = ROOT / "README.md"
VIEWER = ROOT / "docs" / "viewer.js"
VALIDATOR = ROOT / "arc_builder_kit" / "validate_repo.py"

PAY_TO = "0x1111111111111111111111111111111111111111"
TX_HASH = "0x" + "a" * 64


def load_server_module():
    spec = importlib.util.spec_from_file_location("arc_paid_api_endpoint", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SERVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PaidApiEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = load_server_module()
        self.config = self.server.PaidApiConfig.demo()

    def test_missing_payment_returns_x402_challenge_for_human_review(self) -> None:
        response = self.server.handle_protected_request({}, self.config)

        self.assertEqual(response.status, 402)
        self.assertEqual(response.body["error"], "payment_required")
        self.assertEqual(response.body["accepts"][0]["network"], "arc-testnet")
        self.assertEqual(response.body["accepts"][0]["asset"], "USDC")
        self.assertTrue(response.body["humanApprovalRequired"])
        self.assertFalse(response.body["transactionBroadcast"])
        self.assertFalse(response.body["privateKeysAccepted"])

    def test_invalid_x_payment_header_fails_closed(self) -> None:
        for proof in ("", "not-a-tx", "0x" + "g" * 64, "0x" + "a" * 63, "0x" + "a" * 65):
            with self.subTest(proof=proof):
                response = self.server.handle_protected_request({"X-Payment": proof}, self.config)
                self.assertEqual(response.status, 402)
                self.assertEqual(response.body["error"], "invalid_x_payment")
                self.assertFalse(response.body["settled"])
                self.assertFalse(response.body["transactionBroadcast"])

    def test_verified_arc_testnet_tx_unlocks_protected_resource_with_no_broadcast(self) -> None:
        class VerifiedVerifier:
            def verify(self, tx_hash, challenge, config):
                return self_module.ReceiptCheck(
                    verified=True,
                    reason="usdc_transfer_event_confirmed",
                    tx_hash=tx_hash,
                    chain_id=5042002,
                    from_address="0x2222222222222222222222222222222222222222",
                    to_address=config.pay_to,
                )

        self_module = self.server
        response = self.server.handle_protected_request(
            {"X-Payment": TX_HASH},
            self.config,
            verifier=VerifiedVerifier(),
        )

        self.assertEqual(response.status, 200)
        self.assertTrue(response.body["ok"])
        self.assertEqual(response.body["data"]["kind"], "paid-api-prototype")
        self.assertEqual(response.body["receipt"]["txHash"], TX_HASH)
        self.assertEqual(response.body["receipt"]["chainId"], 5042002)
        self.assertFalse(response.body["safety"]["transactionBroadcast"])
        self.assertFalse(response.body["safety"]["privateKeysAccepted"])

    def test_unverified_receipt_does_not_unlock_resource(self) -> None:
        class RejectedVerifier:
            def verify(self, tx_hash, challenge, config):
                return self_module.ReceiptCheck(
                    verified=False,
                    reason="no_usdc_transfer_event_found",
                    tx_hash=tx_hash,
                    chain_id=5042002,
                )

        self_module = self.server
        response = self.server.handle_protected_request(
            {"X-Payment": TX_HASH},
            self.config,
            verifier=RejectedVerifier(),
        )

        self.assertEqual(response.status, 402)
        self.assertEqual(response.body["error"], "payment_verification_failed")
        self.assertEqual(response.body["reason"], "no_usdc_transfer_event_found")
        self.assertFalse(response.body["settled"])
        self.assertFalse(response.body["transactionBroadcast"])

    def test_config_fails_closed_for_mainnet_keys_and_external_bind(self) -> None:
        with self.assertRaisesRegex(ValueError, "mainnet"):
            self.server.PaidApiConfig.from_env({"ARC_PAID_API_MAINNET_ENABLED": "true"})
        with self.assertRaisesRegex(ValueError, "private"):
            self.server.PaidApiConfig.from_env({"ARC_PAID_API_PRIVATE_KEY": "0x" + "1" * 64})
        with self.assertRaisesRegex(ValueError, "localhost"):
            self.server.validate_bind_target("0.0.0.0", 8098)

    def test_manifest_and_docs_wire_the_endpoint(self) -> None:
        manifest = self.server.build_manifest(self.config)
        self.assertEqual(manifest["name"], "arc-paid-api-endpoint-prototype")
        self.assertEqual(manifest["network"]["chainId"], 5042002)
        self.assertEqual(manifest["payment"]["payTo"], self.config.pay_to)
        self.assertTrue(manifest["safety"]["humanApprovalRequired"])
        self.assertTrue(manifest["safety"]["readOnlyReceiptVerification"])
        self.assertFalse(manifest["safety"]["transactionBroadcast"])

        for path in (DOC, README, VIEWER, VALIDATOR):
            self.assertIn("arc-paid-api-endpoint", path.read_text(encoding="utf-8"))

    def test_cli_print_manifest_smoke(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--print-manifest"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["name"], "arc-paid-api-endpoint-prototype")
        self.assertFalse(payload["safety"]["transactionBroadcast"])


if __name__ == "__main__":
    unittest.main()
