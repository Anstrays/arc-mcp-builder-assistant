#!/usr/bin/env python3
"""Tests for scripts/arc_builder_mcp_server.py.

Standard-library unittest only. No network calls by default.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "arc_builder_mcp_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("arc_builder_mcp_server_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


server = load_server()


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
            "generate_release_packet",
            "list_examples",
        }
        self.assertEqual(names, expected)
        self.assertEqual(len(names), 8)


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
        completed = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            req = rpc_request("tools/call", {"name": "validate_repo", "arguments": {}})
            resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertTrue(resp["result"]["structuredContent"]["ok"])
        self.assertIn("validate_repo.py", str(mocked.call_args[0][0][1]))

    def test_arc_builder_doctor(self) -> None:
        completed = mock.Mock(returncode=0, stdout='{"status":"pass"}', stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            req = rpc_request("tools/call", {"name": "arc_builder_doctor", "arguments": {}})
            resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertEqual(resp["result"]["structuredContent"]["report"]["status"], "pass")
        self.assertIn("--json", mocked.call_args[0][0])

    def test_generate_release_packet(self) -> None:
        completed = mock.Mock(returncode=0, stdout="generated", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            req = rpc_request("tools/call", {"name": "generate_release_packet", "arguments": {"force": True}})
            resp = server.handle_request(req)
        self.assertNotIn("error", resp)
        self.assertTrue(resp["result"]["structuredContent"]["ok"])
        self.assertIn("generate_arc_release_packet.py", str(mocked.call_args[0][0][1]))
        self.assertIn("--out", mocked.call_args[0][0])

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
