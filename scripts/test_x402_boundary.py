#!/usr/bin/env python3
"""Regression tests for the local x402 verifier boundary example."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "examples" / "x402-local-challenge-server" / "server.py"
DEMO_ENV_KEYS = [
    "X402_DEMO_NETWORK",
    "X402_DEMO_ASSET",
    "X402_DEMO_AMOUNT",
    "X402_DEMO_PAY_TO",
    "X402_DEMO_MAINNET_ENABLED",
]


def clean_demo_env(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in DEMO_ENV_KEYS:
        env.pop(key, None)
    env.update(overrides)
    return env


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

    def test_mcp_manifest_exposes_safe_arc_paid_agent_tools(self) -> None:
        manifest = self.server.build_mcp_manifest(self.config)

        self.assertEqual(manifest["name"], "arc-local-x402-paid-agent")
        self.assertEqual(manifest["network"]["chainId"], 5042002)
        self.assertEqual(manifest["network"]["chainIdHex"], "0x4cef52")
        self.assertEqual(manifest["payment"]["amount"], "0.01")
        self.assertEqual(manifest["payment"]["asset"], "USDC")
        self.assertTrue(manifest["safety"]["testnetOnly"])
        self.assertTrue(manifest["safety"]["humanApprovalRequired"])
        self.assertTrue(manifest["safety"]["localDemoProofOnly"])
        self.assertFalse(manifest["safety"]["transactionBroadcast"])
        self.assertIn("Circle Gateway/x402", manifest["productionReplacementBoundary"])
        tool_names = {tool["name"] for tool in manifest["tools"]}
        self.assertEqual(tool_names, {"get_paid_resource", "inspect_payment_challenge"})

    def test_402_response_includes_manifest_for_agent_discovery(self) -> None:
        response = self.server.handle_protected_request({}, self.config)

        self.assertEqual(response.status, 402)
        self.assertIn("mcpManifest", response.body)
        self.assertEqual(response.body["mcpManifest"]["name"], "arc-local-x402-paid-agent")
        self.assertFalse(response.body["mcpManifest"]["safety"]["transactionBroadcast"])

    def test_paid_response_includes_manifest_metadata(self) -> None:
        challenge = self.server.build_payment_challenge(self.config)
        proof = f"local-demo:{challenge['id']}:{self.config.amount}"

        response = self.server.handle_protected_request({"X-Payment": proof}, self.config)

        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["mcpManifest"]["name"], "arc-local-x402-paid-agent")
        self.assertEqual(response.body["unitEconomics"]["priceMicroUsd"], 10000)
        self.assertEqual(response.body["unitEconomics"]["displayPrice"], "0.01 USDC")

    def test_demo_config_is_safe_by_default(self) -> None:
        self.assertEqual(self.config.network, "arc-testnet")
        self.assertTrue(self.config.human_approval_required)
        self.assertFalse(self.config.mainnet_enabled)
        self.assertIn("0x", self.config.pay_to)

    def test_env_config_defaults_match_demo_config(self) -> None:
        config = self.server.PaymentConfig.from_env({})

        self.assertEqual(config, self.config)

    def test_env_override_changes_challenge_and_manifest(self) -> None:
        pay_to = "0xBEEF000000000000000000000000000000000000"
        config = self.server.PaymentConfig.from_env(
            {
                "X402_DEMO_AMOUNT": "0.05",
                "X402_DEMO_PAY_TO": pay_to,
            }
        )
        challenge = self.server.build_payment_challenge(config)
        manifest = self.server.build_mcp_manifest(config)

        self.assertEqual(challenge["accepts"][0]["amount"], "0.05")
        self.assertEqual(challenge["accepts"][0]["payTo"], pay_to)
        self.assertEqual(challenge["unitEconomics"]["priceMicroUsd"], 50000)
        self.assertEqual(manifest["payment"]["amount"], "0.05")
        self.assertEqual(manifest["payment"]["payTo"], pay_to)

    def test_env_rejects_invalid_amount(self) -> None:
        with self.assertRaisesRegex(ValueError, "X402_DEMO_AMOUNT"):
            self.server.PaymentConfig.from_env({"X402_DEMO_AMOUNT": "0.0000001"})
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            self.server.PaymentConfig.from_env({"X402_DEMO_AMOUNT": "0"})

    def test_env_rejects_invalid_pay_to_address(self) -> None:
        with self.assertRaisesRegex(ValueError, "X402_DEMO_PAY_TO"):
            self.server.PaymentConfig.from_env({"X402_DEMO_PAY_TO": "not-an-address"})

    def test_env_rejects_mainnet_and_non_arc_network(self) -> None:
        with self.assertRaisesRegex(ValueError, "arc-testnet"):
            self.server.PaymentConfig.from_env({"X402_DEMO_NETWORK": "ethereum-mainnet"})
        with self.assertRaisesRegex(ValueError, "MAINNET"):
            self.server.PaymentConfig.from_env({"X402_DEMO_MAINNET_ENABLED": "true"})

    def test_jsonrpc_initialize_returns_mcp_capabilities(self) -> None:
        response = self.server.process_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["result"]["serverInfo"]["name"], "arc-local-x402-paid-agent")
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertFalse(response["result"]["safety"]["transactionBroadcast"])

    def test_jsonrpc_tools_list_exposes_manifest_tools(self) -> None:
        response = self.server.process_jsonrpc_request({"jsonrpc": "2.0", "id": "tools", "method": "tools/list"})

        tool_names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(tool_names, {"get_paid_resource", "inspect_payment_challenge"})
        self.assertTrue(all("inputSchema" in tool for tool in response["result"]["tools"]))

    def test_jsonrpc_inspect_payment_challenge_returns_structured_content(self) -> None:
        response = self.server.process_jsonrpc_request(
            {"jsonrpc": "2.0", "id": "inspect", "method": "tools/call", "params": {"name": "inspect_payment_challenge", "arguments": {}}}
        )

        structured = response["result"]["structuredContent"]
        self.assertEqual(structured["challenge"]["resource"], self.config.resource)
        self.assertEqual(structured["mcpManifest"]["name"], "arc-local-x402-paid-agent")
        self.assertIn("402", response["result"]["content"][0]["text"])

    def test_jsonrpc_get_paid_resource_requires_valid_demo_proof(self) -> None:
        challenge = self.server.build_payment_challenge(self.config)
        proof = f"local-demo:{challenge['id']}:{self.config.amount}"
        response = self.server.process_jsonrpc_request(
            {"jsonrpc": "2.0", "id": "paid", "method": "tools/call", "params": {"name": "get_paid_resource", "arguments": {"xPayment": proof}}}
        )

        structured = response["result"]["structuredContent"]
        self.assertEqual(structured["status"], 200)
        self.assertEqual(structured["body"]["receipt"]["verifierMode"], "local-simulation")
        self.assertFalse(structured["body"]["receipt"]["transactionBroadcast"])

    def test_jsonrpc_unknown_tool_returns_error_without_crashing(self) -> None:
        response = self.server.process_jsonrpc_request(
            {"jsonrpc": "2.0", "id": "bad", "method": "tools/call", "params": {"name": "send_money", "arguments": {}}}
        )

        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("unknown tool", response["error"]["message"])

    def test_jsonrpc_notifications_do_not_emit_responses(self) -> None:
        response = self.server.process_jsonrpc_request({"jsonrpc": "2.0", "method": "notifications/initialized"})

        self.assertIsNone(response)

    def test_mcp_stdio_mode_suppresses_notification_responses(self) -> None:
        payload = (
            json.dumps({"jsonrpc": "2.0", "id": "stdio", "method": "tools/list"})
            + "\n"
            + json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
            + "\n"
        )

        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--mcp-stdio"],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(),
            timeout=5,
        )

        lines = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["id"], "stdio")

    def test_mcp_stdio_mode_processes_newline_delimited_json(self) -> None:
        payload = json.dumps({"jsonrpc": "2.0", "id": "stdio", "method": "tools/list"}) + "\n"

        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--mcp-stdio"],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(),
            timeout=5,
        )

        lines = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(lines[0]["id"], "stdio")
        self.assertIn("get_paid_resource", {tool["name"] for tool in lines[0]["result"]["tools"]})

    def test_mcp_stdio_mode_uses_env_config(self) -> None:
        payload = json.dumps({"jsonrpc": "2.0", "id": "inspect", "method": "tools/call", "params": {"name": "inspect_payment_challenge"}}) + "\n"

        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--mcp-stdio"],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(X402_DEMO_AMOUNT="0.05"),
            timeout=5,
        )

        response = json.loads(completed.stdout)
        structured = response["result"]["structuredContent"]
        self.assertEqual(structured["challenge"]["accepts"][0]["amount"], "0.05")
        self.assertEqual(structured["mcpManifest"]["payment"]["amount"], "0.05")

    def test_cli_print_manifest_emits_safe_agent_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--print-manifest"],
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(),
            timeout=5,
        )

        manifest = json.loads(completed.stdout)
        self.assertEqual(manifest["name"], "arc-local-x402-paid-agent")
        self.assertFalse(manifest["safety"]["transactionBroadcast"])
        self.assertFalse(manifest["safety"]["privateKeysAccepted"])

    def test_cli_print_challenge_includes_local_demo_proof_hint(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--print-challenge"],
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(),
            timeout=5,
        )

        challenge = json.loads(completed.stdout)
        self.assertEqual(challenge["status"], 402)
        self.assertEqual(challenge["localDemoProof"], f"local-demo:{challenge['challenge']['id']}:{self.config.amount}")
        self.assertFalse(challenge["challenge"]["transactionBroadcast"])

    def test_cli_verify_payment_emits_rejected_and_accepted_receipts(self) -> None:
        rejected = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--verify-payment", "bad-proof"],
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(),
            timeout=5,
        )
        rejected_body = json.loads(rejected.stdout)
        self.assertEqual(rejected_body["status"], 402)
        self.assertFalse(rejected_body["body"]["transactionBroadcast"])

        challenge = self.server.build_payment_challenge(self.config)
        proof = f"local-demo:{challenge['id']}:{self.config.amount}"
        accepted = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--verify-payment", proof],
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(),
            timeout=5,
        )
        accepted_body = json.loads(accepted.stdout)
        self.assertEqual(accepted_body["status"], 200)
        self.assertFalse(accepted_body["body"]["receipt"]["transactionBroadcast"])

    def test_cli_helpers_use_env_config(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--print-challenge"],
            text=True,
            capture_output=True,
            check=True,
            env=clean_demo_env(X402_DEMO_AMOUNT="0.05"),
            timeout=5,
        )

        challenge = json.loads(completed.stdout)
        self.assertEqual(challenge["challenge"]["accepts"][0]["amount"], "0.05")
        self.assertEqual(challenge["mcpManifest"]["payment"]["amount"], "0.05")

    def test_cli_invalid_env_exits_with_clear_error(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--print-challenge"],
            text=True,
            capture_output=True,
            env=clean_demo_env(X402_DEMO_MAINNET_ENABLED="true"),
            timeout=5,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Invalid x402 demo configuration", completed.stderr)
        self.assertIn("MAINNET", completed.stderr)

    def test_http_server_rejects_external_bind_and_invalid_port(self) -> None:
        external = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--host", "0.0.0.0"],
            text=True,
            capture_output=True,
            env=clean_demo_env(),
            timeout=5,
        )
        invalid_port = subprocess.run(
            [sys.executable, str(SERVER_PATH), "--port", "70000"],
            text=True,
            capture_output=True,
            env=clean_demo_env(),
            timeout=5,
        )

        self.assertNotEqual(external.returncode, 0)
        self.assertIn("local-only demo", external.stderr)
        self.assertNotEqual(invalid_port.returncode, 0)
        self.assertIn("between 1 and 65535", invalid_port.stderr)


if __name__ == "__main__":
    unittest.main()
