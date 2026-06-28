#!/usr/bin/env python3
"""Tests for the read-only Arc Testnet x402 client."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arc_builder_kit import x402_client as x402

PAY_TO = "0x1111111111111111111111111111111111111111"
FROM = "0x2222222222222222222222222222222222222222"
TX_HASH = "0x" + "a" * 64
TRANSFER_TOPIC = x402.TRANSFER_EVENT_TOPIC


def challenge_body(network: str = "arc-testnet", amount: str = "0.01") -> dict:
    return {
        "id": "challenge-1",
        "resource": "https://example.test/report",
        "accepts": [
            {
                "scheme": "exact",
                "network": network,
                "asset": "USDC",
                "amount": amount,
                "payTo": PAY_TO,
            }
        ],
    }


def topic_addr(address: str) -> str:
    return "0x" + "0" * 24 + address[2:].lower()


def receipt(amount_micro: int = 10_000, to: str = PAY_TO) -> dict:
    return {
        "status": "0x1",
        "logs": [
            {
                "address": x402.USDC_CONTRACT_ADDRESS,
                "topics": [TRANSFER_TOPIC, topic_addr(FROM), topic_addr(to)],
                "data": hex(amount_micro),
            }
        ],
    }


def transaction(chain_id: int = x402.ARC_TESTNET_CHAIN_ID) -> dict:
    return {
        "chainId": hex(chain_id),
        "from": FROM,
        "to": x402.USDC_CONTRACT_ADDRESS,
    }


class X402ClientTests(unittest.TestCase):
    def test_parse_challenge_and_payment_intent_are_review_only(self) -> None:
        parsed = x402.parse_challenge(challenge_body())
        self.assertEqual(parsed.requirements[0].network, "arc-testnet")
        self.assertEqual(parsed.requirements[0].pay_to, PAY_TO)

        intent = x402.prepare_payment_intent(parsed).to_dict()
        self.assertEqual(intent["status"], "pending_human_approval")
        self.assertTrue(intent["humanApprovalRequired"])
        self.assertFalse(intent["autoExecute"])
        self.assertFalse(intent["transactionBroadcast"])

    def test_mainnet_challenge_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "mainnet"):
            x402.parse_challenge(challenge_body(network="mainnet"))

    def test_verify_receipt_with_mocked_rpc_transfer(self) -> None:
        parsed = x402.parse_challenge(challenge_body())
        old_receipt = x402.get_transaction_receipt
        old_tx = x402.get_transaction_by_hash
        try:
            x402.get_transaction_receipt = lambda *a, **k: receipt()
            x402.get_transaction_by_hash = lambda *a, **k: transaction()
            result = x402.verify_receipt(TX_HASH, challenge=parsed)
        finally:
            x402.get_transaction_receipt = old_receipt
            x402.get_transaction_by_hash = old_tx

        self.assertTrue(result.verified)
        self.assertTrue(result.transfer_found)
        self.assertIsNotNone(result.to_address)
        self.assertEqual((result.to_address or "").lower(), PAY_TO.lower())
        self.assertEqual(result.reason, "usdc_transfer_event_confirmed")

    def test_verify_receipt_rejects_wrong_chain_id(self) -> None:
        parsed = x402.parse_challenge(challenge_body())
        old_receipt = x402.get_transaction_receipt
        old_tx = x402.get_transaction_by_hash
        try:
            x402.get_transaction_receipt = lambda *a, **k: receipt()
            x402.get_transaction_by_hash = lambda *a, **k: transaction(chain_id=1)
            result = x402.verify_receipt(TX_HASH, challenge=parsed)
        finally:
            x402.get_transaction_receipt = old_receipt
            x402.get_transaction_by_hash = old_tx

        self.assertFalse(result.verified)
        self.assertEqual(result.status, "wrong_chain")
        self.assertIn("wrong_chain_id", result.reason)

    def test_transfer_topic_is_canonical_erc20_topic(self) -> None:
        self.assertEqual(
            x402.TRANSFER_EVENT_TOPIC,
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        )

    def test_safety_flags_are_fail_closed(self) -> None:
        safety = x402.SAFETY_FLAGS
        self.assertTrue(safety["testnetOnly"])
        self.assertTrue(safety["humanApprovalRequired"])
        self.assertTrue(safety["readOnlyRpc"])
        self.assertFalse(safety["transactionBroadcast"])
        self.assertFalse(safety["privateKeysAccepted"])
        self.assertFalse(safety["autonomousSpending"])
        self.assertFalse(safety["mainnetEnabled"])


if __name__ == "__main__":
    unittest.main()
