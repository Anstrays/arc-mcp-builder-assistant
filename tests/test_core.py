"""Unit tests for arc-builder-kit — uses unittest (no pytest dependency)."""

from __future__ import annotations

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from arc_builder_kit import ArcDocsClient, CircleWalletClient, __version__


def _mock_response(data: dict) -> MagicMock:
    """Create a mock httpx Response with a sync .json() method."""
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    resp.text = json.dumps(data)
    return resp


class TestVersion(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(__version__, "0.2.0")


# ════════════════════════════════════════════════════════════════
# ArcDocsClient tests
# ════════════════════════════════════════════════════════════════


class TestArcDocsClient(unittest.TestCase):
    def _make_client(self) -> ArcDocsClient:
        return ArcDocsClient(url="http://fake.local/mcp")

    def test_search_no_results(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response({"result": {"content": []}})
            results = client._run_sync(client.search("nonexistent"))
            self.assertEqual(results, [])

    def test_search_with_results(self) -> None:
        client = self._make_client()
        fake = {
            "result": {
                "content": [
                    {"type": "text", "text": "Arc is a stablecoin-native L2..."},
                    {"type": "text", "text": "USDC is the native gas token."},
                ]
            }
        }
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(fake)
            results = client._run_sync(client.search("USDC"))
            self.assertEqual(len(results), 2)
            self.assertIn("stablecoin-native", results[0].content)
            self.assertIn("USDC", results[1].content)

    def test_get_page(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(
                {"result": {"content": [{"type": "text", "text": "# Deploy Contracts\n..."}]}}
            )
            result = client._run_sync(client.get_page("/arc/tutorials/deploy-contracts"))
            self.assertIsNotNone(result)
            self.assertIn("Deploy Contracts", result.content)

    def test_get_page_missing(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response({"result": {"content": []}})
            result = client._run_sync(client.get_page("/nonexistent"))
            self.assertIsNone(result)

    def test_list_tools(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(
                {"result": {"tools": [{"name": "search", "description": "Search docs"}]}}
            )
            tools = client._run_sync(client.list_tools())
            self.assertEqual(len(tools), 1)

    def test_fetch_llms_txt(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            resp = MagicMock()
            resp.text = "- /arc/concepts\n- /arc/references\n"
            resp.raise_for_status.return_value = None
            mock_get.return_value = resp
            result = client._run_sync(client.fetch_llms_txt())
            self.assertIn("/arc/concepts", result)


# ════════════════════════════════════════════════════════════════
# CircleWalletClient tests
# ════════════════════════════════════════════════════════════════


class TestCircleWalletClient(unittest.TestCase):
    def _make_client(self) -> CircleWalletClient:
        return CircleWalletClient(
            api_key="test-key",
            entity_secret="test-secret",
            base_url="http://fake.circle.local",
        )

    def test_init_no_api_key(self) -> None:
        with self.assertRaises(ValueError):
            CircleWalletClient(api_key="", entity_secret="secret")

    def test_init_no_entity_secret(self) -> None:
        with self.assertRaises(ValueError):
            CircleWalletClient(api_key="key", entity_secret="")

    def test_list_wallets(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "data": {
                        "wallets": [
                            {
                                "id": "wallet-1",
                                "address": "0xabc",
                                "blockchain": "ARC-TESTNET",
                                "accountType": "SCA",
                                "custodyType": "DEVELOPER",
                                "walletSetId": "set-1",
                                "state": "LIVE",
                            }
                        ]
                    }
                }
            )
            wallets = client._run_sync(client.list_wallets())
            self.assertEqual(len(wallets), 1)
            self.assertEqual(wallets[0].id, "wallet-1")

    def test_wallet_status(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "data": {
                        "wallet": {
                            "id": "w-42",
                            "address": "0x123",
                            "blockchain": "ARC-TESTNET",
                            "accountType": "SCA",
                            "custodyType": "DEVELOPER",
                            "walletSetId": "set-1",
                            "state": "LIVE",
                        }
                    }
                }
            )
            w = client._run_sync(client.get_wallet("w-42"))
            self.assertEqual(w.id, "w-42")
            self.assertEqual(w.address, "0x123")
            self.assertEqual(w.blockchain, "ARC-TESTNET")

    def test_wallet_balance(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "data": {
                        "tokenBalances": [
                            {"amount": "1000000", "token": {"name": "USDC"}, "blockchain": "ARC-TESTNET"}
                        ]
                    }
                }
            )
            balances = client._run_sync(client.get_balance("w-42"))
            self.assertEqual(len(balances), 1)
            self.assertEqual(balances[0].amount, "1000000")

    def test_create_transaction(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(
                {
                    "data": {
                        "transaction": {
                            "id": "tx-1",
                            "state": "PENDING",
                            "blockchain": "ARC-TESTNET",
                            "txHash": "",
                            "amount": "5.00",
                            "tokenId": "USDC",
                        }
                    }
                }
            )
            tx = client._run_sync(
                client.create_transaction(wallet_id="w-42", destination="0xdest", amount="5.00")
            )
            self.assertEqual(tx.id, "tx-1")
            self.assertEqual(tx.state, "PENDING")

    def test_get_transaction(self) -> None:
        client = self._make_client()
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "data": {
                        "transaction": {
                            "id": "tx-1",
                            "state": "COMPLETE",
                            "blockchain": "ARC-TESTNET",
                            "txHash": "0xdeadbeef",
                            "amount": "5.00",
                            "tokenId": "USDC",
                        }
                    }
                }
            )
            tx = client._run_sync(client.get_transaction("tx-1"))
            self.assertEqual(tx.state, "COMPLETE")
            self.assertEqual(tx.tx_hash, "0xdeadbeef")


# ════════════════════════════════════════════════════════════════
# MCP Server tests
# ════════════════════════════════════════════════════════════════


class TestMCPServer(unittest.TestCase):
    def test_tool_registry_has_14_tools(self) -> None:
        from arc_builder_kit.mcp_server import TOOL_REGISTRY

        expected = {
            "search_arc_docs",
            "get_arc_page",
            "list_arc_tools",
            "fetch_llms_txt",
            "wallet_status",
            "wallet_balance",
            "wallet_list",
            "wallet_send",
            "get_transaction",
            "create_wallet_set",
            "arc_docs_overview",
            "quickstart_prompt",
            "template_info",
            "estimate_fee",
        }
        self.assertEqual(set(TOOL_REGISTRY.keys()), expected)

    def test_every_tool_has_schema(self) -> None:
        from arc_builder_kit.mcp_server import TOOL_REGISTRY

        for name, meta in TOOL_REGISTRY.items():
            self.assertIn("inputSchema", meta, f"Tool {name} missing inputSchema")
            self.assertIn("description", meta, f"Tool {name} missing description")
            self.assertIn("fn", meta, f"Tool {name} missing fn")

    def test_contract_templates(self) -> None:
        from arc_builder_kit.mcp_server import CONTRACT_TEMPLATES

        self.assertIn("erc20", CONTRACT_TEMPLATES)
        self.assertIn("erc721", CONTRACT_TEMPLATES)
        self.assertEqual(CONTRACT_TEMPLATES["erc20"]["name"], "ERC-20")

    def test_arc_testnet_info(self) -> None:
        from arc_builder_kit.mcp_server import ARC_TESTNET_INFO

        self.assertEqual(ARC_TESTNET_INFO["chain_id"], 5042002)
        self.assertEqual(ARC_TESTNET_INFO["currency"], "USDC")

    def test_quickstart_prompt(self) -> None:
        from arc_builder_kit.mcp_server import _quickstart_prompt
        import asyncio

        result = asyncio.run(_quickstart_prompt("payment-intent"))
        self.assertIn("USDC", result)

        result2 = asyncio.run(_quickstart_prompt("unknown"))
        self.assertIn("Arc MCP/docs context", result2)

    def test_template_info(self) -> None:
        from arc_builder_kit.mcp_server import _template_info
        import asyncio

        all_t = asyncio.run(_template_info(""))
        self.assertIn("erc20", all_t)

        single = asyncio.run(_template_info("erc20"))
        self.assertIn("a1b74add", single)

        missing = asyncio.run(_template_info("nonexistent"))
        self.assertIn("Unknown template", missing)

    def test_estimate_fee(self) -> None:
        from arc_builder_kit.mcp_server import _estimate_fee
        import asyncio

        result = asyncio.run(_estimate_fee())
        self.assertIn("5042002", result)

    def test_handle_list_tools(self) -> None:
        from arc_builder_kit.mcp_server import _handle_list_tools
        import asyncio

        resp = asyncio.run(_handle_list_tools({"id": 1}))
        self.assertIn("result", resp)
        tools = resp["result"]["tools"]
        self.assertEqual(len(tools), 14)

    def test_handle_call_tool_unknown(self) -> None:
        from arc_builder_kit.mcp_server import _handle_call_tool
        import asyncio

        resp = asyncio.run(_handle_call_tool({"id": 1, "params": {"name": "bogus"}}))
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32601)

    def test_handle_call_tool_quickstart(self) -> None:
        from arc_builder_kit.mcp_server import _handle_call_tool
        import asyncio

        resp = asyncio.run(
            _handle_call_tool(
                {
                    "id": 1,
                    "params": {
                        "name": "quickstart_prompt",
                        "arguments": {"task": "payment-intent"},
                    },
                }
            )
        )
        self.assertIn("result", resp)
        text = resp["result"]["content"][0]["text"]
        self.assertIn("USDC", text)


# ════════════════════════════════════════════════════════════════
# CLI smoke test
# ════════════════════════════════════════════════════════════════


class TestCLI(unittest.TestCase):
    def test_cli_imports(self) -> None:
        from arc_builder_kit import cli

        self.assertTrue(hasattr(cli, "app"))
        self.assertTrue(hasattr(cli, "wallet_app"))
        self.assertTrue(hasattr(cli, "docs_app"))


if __name__ == "__main__":
    unittest.main()
