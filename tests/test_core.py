"""Unit tests for the current public Arc Builder Kit surfaces."""

from __future__ import annotations

import unittest
from unittest import mock

from arc_builder_kit import __version__
from arc_builder_kit.arc_client import ArcDocsClient, _make_request, _parse_tool_call_result
from arc_builder_kit.circle_wallet_sdk import build_sdk_guard_manifest
from arc_builder_kit.cli import COMMANDS, build_parser
from arc_builder_kit.mcp_server import TOOLS, handle_request


class VersionTests(unittest.TestCase):
    def test_package_version_matches_current_release(self) -> None:
        self.assertEqual(__version__, "0.4.1")


class ArcDocsClientTests(unittest.TestCase):
    def test_request_and_result_helpers_follow_json_rpc_shape(self) -> None:
        request = _make_request("tools/list")
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["method"], "tools/list")
        results = _parse_tool_call_result(
            {"result": {"content": [{"type": "text", "text": "Arc docs"}]}}
        )
        self.assertEqual([result.content for result in results], ["Arc docs"])

    def test_search_uses_stdlib_transport_and_parses_results(self) -> None:
        client = ArcDocsClient(url="https://example.test/mcp")
        response = {
            "result": {
                "content": [
                    {"type": "text", "text": "Arc Testnet", "source": "/arc/testnet"}
                ]
            }
        }
        with mock.patch("arc_builder_kit.arc_client._post_json", return_value=response) as post:
            results = client._run_sync(client.search("testnet", limit=3))
        self.assertEqual(results[0].source, "/arc/testnet")
        payload = post.call_args.args[1]
        self.assertEqual(payload["params"]["arguments"], {"query": "testnet", "limit": 3})

    def test_remote_plain_http_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTPS or local HTTP"):
            ArcDocsClient(url="http://example.com/mcp")


class McpServerTests(unittest.TestCase):
    def test_tool_registry_matches_handlers(self) -> None:
        expected = {
            "arc_builder_doctor",
            "list_templates",
            "scaffold_project",
            "validate_repo",
            "get_arc_testnet_facts",
            "x402_manifest",
            "generate_release_packet",
            "list_examples",
            "x402_paid_request",
            "x402_fetch_challenge",
            "x402_verify_receipt",
        }
        self.assertEqual(set(TOOLS), expected)

    def test_tools_list_returns_all_current_tools(self) -> None:
        response = handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        self.assertIsNotNone(response)
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(names, set(TOOLS))

    def test_unknown_tool_fails_closed(self) -> None:
        response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "unknown", "arguments": {}},
            }
        )
        self.assertEqual(response["error"]["code"], -32601)


class CliTests(unittest.TestCase):
    def test_parser_and_dispatch_table_expose_current_commands(self) -> None:
        expected = {
            "doctor",
            "validate",
            "templates",
            "scaffold",
            "facts",
            "manifest",
            "mcp",
            "release-packet",
            "x402",
            "wallet",
        }
        self.assertEqual(set(COMMANDS), expected)
        self.assertEqual(build_parser().parse_args(["facts"]).command, "facts")

    def test_wallet_manifest_remains_testnet_only_and_non_broadcasting(self) -> None:
        manifest = build_sdk_guard_manifest()
        self.assertEqual(manifest["chainId"], 5_042_002)
        self.assertTrue(manifest["safety"]["testnetOnly"])
        self.assertFalse(manifest["safety"]["transactionBroadcast"])
        self.assertFalse(manifest["safety"]["mainnetEnabled"])


if __name__ == "__main__":
    unittest.main()
