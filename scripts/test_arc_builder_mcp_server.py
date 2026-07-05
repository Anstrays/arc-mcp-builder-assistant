#!/usr/bin/env python3
"""Tests for scripts/arc_builder_mcp_server.py.

Standard-library unittest only. No network calls by default.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arc_builder_kit import mcp_server as server  # noqa: E402


def rpc_request(method: str, params: dict | None = None, req_id: int = 1):
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}


class InitializeTests(unittest.TestCase):
    def test_initialize_returns_protocol_and_safety(self) -> None:
        req = rpc_request("initialize")
        resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertEqual(resp["result"]["protocolVersion"], server.PROTOCOL_VERSION)
        self.assertEqual(resp["result"]["serverInfo"]["name"], server.SERVER_NAME)
        self.assertTrue(resp["result"]["safety"]["noWallet"])
        self.assertTrue(resp["result"]["safety"]["testnetOnly"])


class ToolsListTests(unittest.TestCase):
    def test_tools_list_includes_expected_tools(self) -> None:
        req = rpc_request("tools/list")
        resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "arc_builder_doctor",
            "list_templates",
            "scaffold_project",
            "validate_repo",
            "get_arc_testnet_facts",
            "x402_manifest",
            "x402_paid_request",
            "x402_fetch_challenge",
            "x402_verify_receipt",
            "generate_release_packet",
            "list_examples",
        }
        self.assertEqual(names, expected)
        self.assertEqual(len(names), 11)


class ToolCallTests(unittest.TestCase):
    def test_get_arc_testnet_facts(self) -> None:
        req = rpc_request("tools/call", {"name": "get_arc_testnet_facts", "arguments": {}})
        resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertFalse(resp["result"]["isError"])
        self.assertIn("chainId", resp["result"]["structuredContent"]["network"])

    def test_list_templates(self) -> None:
        req = rpc_request("tools/call", {"name": "list_templates", "arguments": {}})
        resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertIn("payment-intent-starter", resp["result"]["structuredContent"]["templates"])

    def test_x402_manifest(self) -> None:
        completed = mock.Mock(returncode=0, stdout="{}", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            req = rpc_request("tools/call", {"name": "x402_manifest", "arguments": {}})
            resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertIn("server.py", str(mocked.call_args[0][0][1]))

    def test_validate_repo(self) -> None:
        with mock.patch.object(server, "validate_main", return_value=None) as mocked:
            req = rpc_request("tools/call", {"name": "validate_repo", "arguments": {}})
            resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertTrue(resp["result"]["structuredContent"]["ok"])
        mocked.assert_called_once_with()

    def test_arc_builder_doctor(self) -> None:
        def doctor(args):
            print('{"status":"pass"}')
            return 0

        with mock.patch.object(server, "doctor_main", side_effect=doctor) as mocked:
            req = rpc_request("tools/call", {"name": "arc_builder_doctor", "arguments": {}})
            resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertEqual(resp["result"]["structuredContent"]["report"]["status"], "pass")
        self.assertIn("--json", mocked.call_args.args[0])

    def test_generate_release_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(server, "release_packet_main", return_value=0) as mocked:
                req = rpc_request(
                    "tools/call",
                    {"name": "generate_release_packet", "arguments": {"output": temp}},
                )
                resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertTrue(resp["result"]["structuredContent"]["ok"])
        self.assertIn("--out", mocked.call_args.args[0])

    def test_list_examples(self) -> None:
        req = rpc_request("tools/call", {"name": "list_examples", "arguments": {}})
        resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertFalse(resp["result"]["isError"])
        self.assertGreater(resp["result"]["structuredContent"]["count"], 0)

    def test_unknown_tool(self) -> None:
        req = rpc_request("tools/call", {"name": "no_such_tool", "arguments": {}})
        resp = server.handle_request(req)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32601)


class RequestValidationTests(unittest.TestCase):
    def test_invalid_json_rpc_version(self) -> None:
        req = {"jsonrpc": "1.0", "id": 1, "method": "initialize"}
        resp = server.handle_request(req)
        self.assertEqual(resp["error"]["code"], -32600)

    def test_unknown_method(self) -> None:
        req = rpc_request("nope")
        resp = server.handle_request(req)
        self.assertEqual(resp["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
