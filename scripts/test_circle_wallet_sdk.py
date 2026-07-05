#!/usr/bin/env python3
"""Tests for the dependency-free Circle Wallet SDK integration guard."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arc_builder_kit import circle_wallet_sdk as sdk  # noqa: E402


def rpc_response(payload: dict[str, object]) -> mock.MagicMock:
    response = mock.MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class CircleWalletSdkManifestTests(unittest.TestCase):
    def test_guard_manifest_pins_arc_testnet_and_sdk_package(self) -> None:
        manifest = sdk.build_sdk_guard_manifest()
        self.assertEqual(manifest["name"], "circle-wallet-sdk-arc-testnet-guard")
        self.assertEqual(manifest["blockchain"], "ARC-TESTNET")
        self.assertEqual(manifest["chainId"], 5_042_002)
        self.assertEqual(manifest["chainIdHex"], "0x4cef52")
        self.assertEqual(manifest["sdk"]["pythonPackage"], "circle-developer-controlled-wallets")
        self.assertIn("CIRCLE_API_KEY", manifest["requiredEnvironment"])
        self.assertIn("CIRCLE_ENTITY_SECRET", manifest["requiredEnvironment"])
        self.assertTrue(manifest["safety"]["testnetOnly"])
        self.assertTrue(manifest["safety"]["humanApprovalRequired"])
        self.assertFalse(manifest["safety"]["liveSdkExecution"])
        self.assertFalse(manifest["safety"]["transactionBroadcast"])
        self.assertFalse(manifest["safety"]["mainnetEnabled"])

    def test_build_wallet_creation_plan_validates_bounds_and_account_type(self) -> None:
        plan = sdk.build_wallet_creation_plan(account_type="SCA", count=3, wallet_set_name="arc-agents")
        self.assertEqual(plan["walletSet"]["name"], "arc-agents")
        self.assertEqual(plan["wallets"]["blockchains"], ["ARC-TESTNET"])
        self.assertEqual(plan["wallets"]["accountType"], "SCA")
        self.assertEqual(plan["wallets"]["count"], 3)
        self.assertFalse(plan["execution"]["liveSdkExecution"])
        self.assertTrue(plan["execution"]["requiresExplicitHumanRunApproval"])

        with self.assertRaises(ValueError):
            sdk.build_wallet_creation_plan(account_type="mainnet", count=1)
        with self.assertRaises(ValueError):
            sdk.build_wallet_creation_plan(account_type="EOA", count=0)
        with self.assertRaises(ValueError):
            sdk.build_wallet_creation_plan(account_type="EOA", count=51)

    def test_environment_summary_redacts_secret_values(self) -> None:
        env = {
            "CIRCLE_API_KEY": "circle_test_key_should_not_leak",
            "CIRCLE_ENTITY_SECRET": "entity_secret_should_not_leak",
            "CIRCLE_WALLET_SET_ID": "wallet-set-123",
        }
        summary = sdk.summarize_environment(env)
        encoded = json.dumps(summary)
        self.assertTrue(summary["readyForManualSdkRun"])
        self.assertTrue(summary["variables"]["CIRCLE_API_KEY"]["present"])
        self.assertEqual(summary["variables"]["CIRCLE_API_KEY"]["value"], "[REDACTED]")
        self.assertNotIn("circle_test_key_should_not_leak", encoded)
        self.assertNotIn("entity_secret_should_not_leak", encoded)

    def test_environment_summary_marks_missing_required_values(self) -> None:
        summary = sdk.summarize_environment({})
        self.assertFalse(summary["readyForManualSdkRun"])
        self.assertIn("CIRCLE_API_KEY", summary["missingRequired"])
        self.assertIn("CIRCLE_ENTITY_SECRET", summary["missingRequired"])

    def test_python_sdk_snippet_is_arc_testnet_only_and_secret_safe(self) -> None:
        snippet = sdk.generate_python_sdk_snippet(account_type="EOA", count=2)
        self.assertIn("circle.web3", snippet)
        self.assertIn('"ARC-TESTNET"', snippet)
        self.assertIn('"accountType": "EOA"', snippet)
        self.assertIn('"count": 2', snippet)
        self.assertIn('os.environ["CIRCLE_API_KEY"]', snippet)
        self.assertIn('os.environ["CIRCLE_ENTITY_SECRET"]', snippet)
        forbidden_literals = (
            "Your API KEY",
            "Your entity secret",
            "api_key=\"",
            "entity_secret=\"",
            "PRIVATE_KEY",
            "MAINNET",
        )
        for marker in forbidden_literals:
            self.assertNotIn(marker, snippet)

    def test_balance_uses_configured_rpc_and_token_after_chain_proof(self) -> None:
        address = "0x1111111111111111111111111111111111111111"
        token = "0x2222222222222222222222222222222222222222"
        responses = [
            rpc_response({"jsonrpc": "2.0", "id": 1, "result": "0x4cef52"}),
            rpc_response({"jsonrpc": "2.0", "id": 1, "result": "0xf4240"}),
        ]
        with mock.patch.object(sdk.urllib_request, "urlopen", side_effect=responses) as opened:
            result = sdk.get_usdc_balance(
                address,
                env={"CIRCLE_RPC_URL": "https://rpc.example.test", "CIRCLE_USDC_TOKEN": token},
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["balanceUSDC"], "1.000000")
        self.assertEqual(result["tokenAddress"], token)
        self.assertEqual(opened.call_count, 2)
        balance_payload = json.loads(opened.call_args_list[1].args[0].data)
        self.assertEqual(balance_payload["method"], "eth_call")
        self.assertEqual(balance_payload["params"][0]["to"], token)

    def test_balance_rejects_wrong_chain_before_eth_call(self) -> None:
        response = rpc_response({"jsonrpc": "2.0", "id": 1, "result": "0x1"})
        with mock.patch.object(sdk.urllib_request, "urlopen", return_value=response) as opened:
            result = sdk.get_usdc_balance("0x1111111111111111111111111111111111111111")
        self.assertFalse(result["ok"])
        self.assertIn("chain mismatch", result["error"])
        self.assertEqual(opened.call_count, 1)

    def test_balance_rejects_unsafe_rpc_and_token_configuration(self) -> None:
        address = "0x1111111111111111111111111111111111111111"
        unsafe_rpc = sdk.get_usdc_balance(address, rpc_url="http://rpc.example.test")
        self.assertFalse(unsafe_rpc["ok"])
        self.assertIn("HTTPS or local HTTP", unsafe_rpc["error"])
        zero_token = sdk.get_usdc_balance(address, usdc_address="0x" + "0" * 40)
        self.assertFalse(zero_token["ok"])
        self.assertIn("zero address", zero_token["error"])


if __name__ == "__main__":
    unittest.main()
