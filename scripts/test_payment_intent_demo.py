#!/usr/bin/env python3
"""Security and behavior tests for the wallet-backed Payment Intent Demo."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "examples" / "payment-intent-demo" / "server.py"
HTML = ROOT / "examples" / "payment-intent-demo" / "index.html"
JS = ROOT / "examples" / "payment-intent-demo" / "app.js"


def load_server():
    spec = importlib.util.spec_from_file_location("payment_intent_demo_under_test", SERVER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SERVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


server = load_server()


class PaymentIntentDemoTests(unittest.TestCase):
    def setUp(self) -> None:
        server.intents.clear()

    def test_page_uses_external_integrity_pinned_script(self) -> None:
        html = HTML.read_text(encoding="utf-8")
        expected = "sha384-" + base64.b64encode(hashlib.sha384(JS.read_bytes()).digest()).decode()
        match = re.search(r'<script src="\./app\.js" integrity="([^"]+)"', html)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), expected)
        self.assertNotIn("<script>", html)
        self.assertNotRegex(html, r"\son[a-z]+=")

    def test_browser_code_avoids_html_injection_and_background_polling(self) -> None:
        javascript = JS.read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", javascript)
        self.assertNotIn("insertAdjacentHTML", javascript)
        self.assertNotIn("setInterval", javascript)
        self.assertIn("SEND ARC TESTNET USDC", javascript)
        self.assertIn("credentials: 'same-origin'", javascript)

    def test_runtime_config_rejects_external_bind_and_non_arc_chain(self) -> None:
        with mock.patch.object(server, "HOST", "0.0.0.0"):
            with self.assertRaisesRegex(ValueError, "localhost-only"):
                server.validate_runtime_config()
        with mock.patch.object(server, "CHAIN", "ETH-MAINNET"):
            with self.assertRaisesRegex(ValueError, "exactly ARC-TESTNET"):
                server.validate_runtime_config()

    def test_intent_validation_is_usdc_only_and_bounded(self) -> None:
        valid, error = server.validate_intent_input(
            {
                "agent": "Research Agent",
                "recipient": "0x" + "1" * 40,
                "amount": "1.000001",
                "asset": "USDC",
                "memo": "reviewed",
            }
        )
        self.assertIsNone(error)
        self.assertEqual(valid["asset"], "USDC")
        for changed in (
            {"recipient": "bad"},
            {"amount": "0"},
            {"amount": "1.0000001"},
            {"asset": "EURC"},
            {"memo": "line one\nline two"},
        ):
            payload = {
                "agent": "Agent",
                "recipient": "0x" + "1" * 40,
                "amount": "1.00",
                "asset": "USDC",
                "memo": "reviewed",
                **changed,
            }
            self.assertIsNotNone(server.validate_intent_input(payload)[1])

    def test_real_transfer_requires_exact_confirmation_before_broadcast_call(self) -> None:
        intent_id = "intent-1"
        server.intents[intent_id] = {
            "id": intent_id,
            "recipient": "0x" + "1" * 40,
            "amount": "1.00",
            "asset": "USDC",
            "status": "pending_user_approval",
            "estimate": None,
        }
        handler = object.__new__(server.PaymentIntentHandler)
        handler._send_json = mock.Mock()
        estimate = {"ok": True, "data": {"networkFeeAmount": "0.01"}}
        with (
            mock.patch.object(server, "REAL_TRANSFER", True),
            mock.patch.object(server, "_run_circle", return_value=estimate) as run_circle,
        ):
            handler._handle_approve_intent({"intent_id": intent_id, "real": True})
        run_circle.assert_not_called()
        body, status, _headers = handler._send_json.call_args.args[0]
        self.assertEqual(status, 400)
        self.assertIn(b"confirmation", body)

    def test_real_transfer_is_capped_and_one_shot(self) -> None:
        intent_id = "intent-1"
        server.intents[intent_id] = {
            "id": intent_id,
            "recipient": "0x" + "1" * 40,
            "amount": "1.00",
            "asset": "USDC",
            "status": "pending_user_approval",
            "estimate": None,
            "send_attempted": False,
        }
        handler = object.__new__(server.PaymentIntentHandler)
        handler._send_json = mock.Mock()
        estimate = {"ok": True, "data": {"networkFeeAmount": "0.01"}}
        transfer = {"ok": True, "data": {"txHash": "0x" + "a" * 64}}
        request = {
            "intent_id": intent_id,
            "real": True,
            "confirmation": server.SEND_CONFIRMATION,
        }
        with (
            mock.patch.object(server, "REAL_TRANSFER", True),
            mock.patch.object(server, "_run_circle", side_effect=[estimate, transfer]) as run_circle,
        ):
            handler._handle_approve_intent(request)
            handler._handle_approve_intent(request)
        self.assertTrue(server.intents[intent_id]["send_attempted"])
        self.assertEqual(run_circle.call_count, 2)
        body, status, _headers = handler._send_json.call_args.args[0]
        self.assertEqual(status, 409)
        self.assertIn(b"one send attempt", body)

        server.intents[intent_id]["send_attempted"] = False
        server.intents[intent_id]["amount"] = "1.01"
        handler._send_json.reset_mock()
        with (
            mock.patch.object(server, "REAL_TRANSFER", True),
            mock.patch.object(server, "_run_circle") as run_circle,
        ):
            handler._handle_approve_intent(request)
        run_circle.assert_not_called()
        body, status, _headers = handler._send_json.call_args.args[0]
        self.assertEqual(status, 400)
        self.assertIn(b"cap", body)

    def test_server_source_has_request_limit_and_no_wildcard_cors(self) -> None:
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn("MAX_REQUEST_BODY_BYTES", source)
        self.assertIn('HOST = os.environ.get("HOST", "127.0.0.1")', source)
        self.assertNotIn('Access-Control-Allow-Origin", "*"', source)
        self.assertNotIn('__import__("datetime")', source)


if __name__ == "__main__":
    unittest.main()
