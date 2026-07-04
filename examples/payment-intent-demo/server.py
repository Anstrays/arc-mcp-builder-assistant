#!/usr/bin/env python3
"""
Payment Intent Demo — Backend Server
=====================================
Minimal HTTP API server using stdlib only (no Flask/FastAPI required).

Endpoints:
  GET  /               — serve static UI
  POST /api/intent     — create a payment intent
  GET  /api/intents    — list payment intents
  POST /api/approve    — approve and submit payment
  GET  /api/status/<id> — check transaction status
  GET  /api/network    — get Arc Testnet info
  GET  /api/templates  — get Circle contract templates

Run:
    python3 examples/payment-intent-demo/server.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

# ── in-memory store ────────────────────────────────────────────

intents: dict[str, dict] = {}

# ── JSON response helper ───────────────────────────────────────


def json_response(data: Any, status: int = 200) -> tuple[bytes, int, dict]:
    body = json.dumps(data, indent=2).encode()
    return body, status, {"Content-Type": "application/json"}


# ── request handler ────────────────────────────────────────────


class PaymentIntentHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the payment intent demo."""

    def __init__(self, *args, **kwargs):
        # Serve static files from the examples/payment-intent-demo/ directory
        static_dir = str(ROOT / "examples" / "payment-intent-demo")
        super().__init__(*args, directory=static_dir, **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/intents":
            self._send_json(json_response(list(intents.values())))

        elif path.startswith("/api/status/"):
            intent_id = path.split("/")[-1]
            intent = intents.get(intent_id)
            if not intent:
                self._send_json(json_response({"error": "Intent not found"}, 404))
                return
            self._send_json(json_response({"id": intent_id, **intent}))

        elif path == "/api/network":
            self._send_json(
                json_response(
                    {
                        "network": "Arc Testnet",
                        "rpc_url": "https://rpc.testnet.arc.network",
                        "chain_id": 5042002,
                        "currency": "USDC",
                        "explorer": "https://testnet.arcscan.app",
                        "gas_estimate": "~20 Gwei base fee (paid in USDC)",
                    }
                )
            )

        elif path == "/api/templates":
            self._send_json(
                json_response(
                    {
                        "erc20": {"id": "a1b74add-23e0-4712-88d1-6b3009e85a86", "name": "ERC-20"},
                        "erc721": {"id": "76b83278-50e2-4006-8b63-5b1a2a814533", "name": "ERC-721"},
                        "erc1155": {"id": "aea21da6-0aa2-4971-9a1a-5098842b1248", "name": "ERC-1155"},
                        "airdrop": {"id": "13e322f2-18dc-4f57-8eed-4bddfc50f85e", "name": "Airdrop"},
                    }
                )
            )

        else:
            # Serve static files (index.html, etc.)
            super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(json_response({"error": "Invalid JSON"}, 400))
            return

        if path == "/api/intent":
            intent_id = str(uuid.uuid4())[:8]
            intent = {
                "id": intent_id,
                "agent": data.get("agent", "Payment Agent"),
                "recipient": data.get("recipient", "0x0000000000000000000000000000000000000000"),
                "amount": data.get("amount", "0"),
                "asset": data.get("asset", "USDC"),
                "memo": data.get("memo", ""),
                "status": "pending_user_approval",
                "created_at": str(__import__("datetime").datetime.now()),
                "tx_hash": None,
            }
            intents[intent_id] = intent
            self._send_json(json_response(intent, 201))

        elif path == "/api/approve":
            intent_id = data.get("intent_id", "")
            intent = intents.get(intent_id)
            if not intent:
                self._send_json(json_response({"error": "Intent not found"}, 404))
                return

            # Simulate transaction submission
            intent["status"] = "submitted"
            # In production, this would call CircleWalletClient
            self._send_json(
                json_response(
                    {
                        "id": intent_id,
                        "status": "submitted",
                        "message": "Transaction submitted. In production, this calls Circle Wallet API.",
                        "note": "Set CIRCLE_API_KEY and CIRCLE_ENTITY_SECRET to enable real transactions.",
                    }
                )
            )

        else:
            self._send_json(json_response({"error": "Not found"}, 404))

    def _send_json(self, response: tuple[bytes, int, dict]) -> None:
        body, status, headers = response
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"[PaymentIntentDemo] {args[0]} {args[1]} {args[2]}\n")


# ── entry point ────────────────────────────────────────────────


def main() -> None:
    server = HTTPServer((HOST, PORT), PaymentIntentHandler)
    print(f"┌─────────────────────────────────────────────────────────────┐")
    print(f"│  Arc Payment Intent Demo                                    │")
    print(f"│  http://localhost:{PORT}/                                      │")
    print(f"│                                                            │")
    print(f"│  API endpoints:                                            │")
    print(f"│  GET  /api/network     — Arc Testnet info                  │")
    print(f"│  POST /api/intent      — Create payment intent             │")
    print(f"│  POST /api/approve     — Approve and submit                │")
    print(f"│  GET  /api/status/<id> — Check status                      │")
    print(f"└─────────────────────────────────────────────────────────────┘")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
