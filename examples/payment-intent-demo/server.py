#!/usr/bin/env python3
"""
Payment Intent Demo — Backend Server (Circle Wallet Integration)
===============================================================
Minimal HTTP API server using stdlib only (no Flask/FastAPI).

Integrates with Circle CLI (`circle wallet`) for real wallet data,
balance checks, fee estimation, and optional real USDC transfers
on Arc Testnet.

Endpoints:
  GET  /                  — serve static UI
  POST /api/intent        — create a payment intent
  GET  /api/intents       — list payment intents
  POST /api/approve       — estimate or execute transfer via Circle CLI
  GET  /api/status/<id>   — check intent status
  GET  /api/wallet        — real wallet info (address, balance, chain)
  GET  /api/transactions  — real transaction history from Circle
  GET  /api/estimate      — dry-run estimate for a transfer
  GET  /api/network       — Arc Testnet info

Environment variables:
  CIRCLE_WALLET_ADDR  — wallet address (default: 0x0cd9b933302d90bfe295471deac7f4eafd9ea401)
  CIRCLE_CHAIN        — blockchain name (default: ARC-TESTNET)
  CIRCLE_RPC_URL      — RPC endpoint (default: https://rpc.testnet.arc.network)
  CIRCLE_USDC_TOKEN   — USDC token address for ERC-20 transfers (default: 0x3600000000000000000000000000000000000000)
  REAL_TRANSFER       — set to "1" to allow real transfers (default: estimate-only)
  HOST, PORT          — server bind (default: 0.0.0.0:8080)

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

# ── project root ─────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── config ───────────────────────────────────────────
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
WALLET_ADDR = os.environ.get(
    "CIRCLE_WALLET_ADDR",
    "0x0cd9b933302d90bfe295471deac7f4eafd9ea401",
)
CHAIN = os.environ.get("CIRCLE_CHAIN", "ARC-TESTNET")
RPC_URL = os.environ.get(
    "CIRCLE_RPC_URL",
    "https://rpc.testnet.arc.network",
)
USDC_TOKEN = os.environ.get(
    "CIRCLE_USDC_TOKEN",
    "0x3600000000000000000000000000000000000000",
)
REAL_TRANSFER = os.environ.get("REAL_TRANSFER", "0") == "1"

CIRCLE_CMD = "circle"

# ── in-memory store ─────────────────────────────────
intents: dict[str, dict] = {}


# ── helpers ──────────────────────────────────────────


def json_response(data: Any, status: int = 200) -> tuple[bytes, int, dict]:
    body = json.dumps(data, indent=2).encode()
    return body, status, {"Content-Type": "application/json"}


def _run_circle(args: list[str], timeout: int = 30) -> dict:
    """Run a ``circle`` CLI command and return parsed JSON output.

    Strips known deprecation warnings from stderr.
    Returns ``{"ok": True, "data": ...}`` or ``{"ok": False, "error": ...}``.
    """
    try:
        proc = subprocess.run(
            [CIRCLE_CMD, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if proc.returncode != 0:
            return {
                "ok": False,
                "error": proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}",
            }

        # stdout is the JSON response; try to parse it directly
        out = proc.stdout.strip()
        if not out:
            return {"ok": False, "error": "empty response from Circle CLI"}

        # Some Circle CLI responses wrap in {"data": ...}, some don't.
        # Try direct parse; if that fails, try to fish out the JSON block.
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            # Fallback: find first complete JSON object or array
            start = out.find("{")
            if start == -1:
                start = out.find("[")
            if start >= 0:
                try:
                    data = json.loads(out[start:])
                except json.JSONDecodeError:
                    return {"ok": False, "error": f"could not parse Circle CLI output: {out[:200]}"}
            else:
                return {"ok": True, "data": {"raw": out}}

        return {"ok": True, "data": data}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Circle CLI timed out"}
    except FileNotFoundError:
        return {"ok": False, "error": "Circle CLI not found. Install: npm install -g @circle-fin/cli"}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── request handler ──────────────────────────────────


class PaymentIntentHandler(SimpleHTTPRequestHandler):
    """HTTP handler with Circle wallet integration."""

    def __init__(self, *args, **kwargs):
        static_dir = str(ROOT / "examples" / "payment-intent-demo")
        super().__init__(*args, directory=static_dir, **kwargs)

    # ── GET ──────────────────────────────────────────

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        handlers = {
            "/api/intents": self._handle_list_intents,
            "/api/wallet": self._handle_wallet,
            "/api/transactions": self._handle_transactions,
            "/api/estimate": self._handle_estimate,
            "/api/network": self._handle_network,
        }

        # Status route has a path param
        if path.startswith("/api/status/"):
            self._handle_intent_status(path)
            return

        handler = handlers.get(path)
        if handler:
            handler()
            return

        super().do_GET()

    def _handle_list_intents(self) -> None:
        self._send_json(json_response(list(intents.values())))

    def _handle_intent_status(self, path: str) -> None:
        intent_id = path.split("/")[-1]
        intent = intents.get(intent_id)
        if not intent:
            self._send_json(json_response({"error": "Intent not found"}, 404))
            return
        self._send_json(json_response({"id": intent_id, **intent}))

    def _handle_wallet(self) -> None:
        """Real wallet info from Circle CLI."""
        balance_result = _run_circle([
            "wallet", "balance",
            "--address", WALLET_ADDR,
            "--chain", CHAIN,
            "--output", "json",
        ])
        tx_result = _run_circle([
            "transaction", "list",
            "--address", WALLET_ADDR,
            "--chain", CHAIN,
            "--limit", "5",
            "--output", "json",
        ])

        wallet_info = {
            "address": WALLET_ADDR,
            "chain": CHAIN,
            "rpc_url": RPC_URL,
            "real_transfer_enabled": REAL_TRANSFER,
            "balance_ok": balance_result.get("ok", False),
            "balance_error": balance_result.get("error") if not balance_result.get("ok") else None,
            "tx_ok": tx_result.get("ok", False),
            "tx_error": tx_result.get("error") if not tx_result.get("ok") else None,
        }

        if balance_result.get("ok"):
            wallet_info["balances"] = balance_result["data"].get("data", balance_result["data"])

        if tx_result.get("ok"):
            wallet_info["recent_transactions"] = tx_result["data"].get("data", tx_result["data"])

        self._send_json(json_response(wallet_info))

    def _handle_transactions(self) -> None:
        """Real transaction history from Circle CLI."""
        result = _run_circle([
            "transaction", "list",
            "--address", WALLET_ADDR,
            "--chain", CHAIN,
            "--limit", "20",
            "--output", "json",
        ])
        if result.get("ok"):
            self._send_json(json_response(result["data"].get("data", result["data"])))
        else:
            self._send_json(json_response({"error": result.get("error")}, 502))

    def _handle_estimate(self) -> None:
        """Estimate fee for a transfer via Circle CLI."""
        recipient = self._query_param("to") or "0xRecipientAddressPlaceholder"
        amount = self._query_param("amount") or "1.0"

        result = _run_circle([
            "wallet", "transfer", recipient,
            "--amount", amount,
            "--token", USDC_TOKEN,
            "--address", WALLET_ADDR,
            "--chain", CHAIN,
            "--rpc-url", RPC_URL,
            "--estimate",
            "--output", "json",
        ])
        if result.get("ok"):
            self._send_json(json_response({
                "ok": True,
                "estimate": result["data"].get("data", result["data"]),
                "recipient": recipient,
                "amount": amount,
                "note": "Estimate only. No funds moved.",
            }))
        else:
            self._send_json(json_response({
                "ok": False,
                "error": result.get("error"),
                "recipient": recipient,
                "amount": amount,
            }))

    def _handle_network(self) -> None:
        self._send_json(
            json_response({
                "network": "Arc Testnet",
                "rpc_url": RPC_URL,
                "chain_id": 5042002,
                "currency": "USDC",
                "explorer": "https://testnet.arcscan.app",
                "circle_wallet": WALLET_ADDR,
                "usdc_token": USDC_TOKEN,
            })
        )

    def _query_param(self, name: str) -> str | None:
        """Extract query parameter from URL."""
        parsed = urlparse(self.path)
        if not parsed.query:
            return None
        for part in parsed.query.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                if k == name:
                    return v
        return None

    # ── POST ─────────────────────────────────────────

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

        handlers = {
            "/api/intent": lambda: self._handle_create_intent(data),
            "/api/approve": lambda: self._handle_approve_intent(data),
        }
        handler = handlers.get(path)
        if handler:
            handler()
        else:
            self._send_json(json_response({"error": "Not found"}, 404))

    def _handle_create_intent(self, data: dict) -> None:
        intent_id = str(uuid.uuid4())[:8]
        intent = {
            "id": intent_id,
            "agent": data.get("agent", "Payment Agent"),
            "recipient": data.get("recipient", ""),
            "amount": data.get("amount", "0"),
            "asset": data.get("asset", "USDC"),
            "memo": data.get("memo", ""),
            "status": "pending_user_approval",
            "created_at": str(__import__("datetime").datetime.now()),
            "tx_hash": None,
            "estimate": None,
        }

        # Auto-run estimate when creating the intent
        if intent["recipient"] and intent["amount"]:
            est = _run_circle([
                "wallet", "transfer", intent["recipient"],
                "--amount", intent["amount"],
                "--token", USDC_TOKEN,
                "--address", WALLET_ADDR,
                "--chain", CHAIN,
                "--rpc-url", RPC_URL,
                "--estimate",
                "--output", "json",
            ])
            if est.get("ok"):
                intent["estimate"] = est["data"].get("data", est["data"])

        intents[intent_id] = intent
        self._send_json(json_response(intent, 201))

    def _handle_approve_intent(self, data: dict) -> None:
        intent_id = data.get("intent_id", "")
        intent = intents.get(intent_id)
        if not intent:
            self._send_json(json_response({"error": "Intent not found"}, 404))
            return

        recipient = intent["recipient"]
        amount = intent["amount"]

        if not recipient or not amount:
            self._send_json(json_response({"error": "Intent missing recipient or amount"}, 400))
            return

        # Step 1: estimate
        est = _run_circle([
            "wallet", "transfer", recipient,
            "--amount", amount,
            "--token", USDC_TOKEN,
            "--address", WALLET_ADDR,
            "--chain", CHAIN,
            "--rpc-url", RPC_URL,
            "--estimate",
            "--output", "json",
        ])

        if not est.get("ok"):
            intent["status"] = "failed"
            error_msg = est.get("error", "Unknown error during estimation")
            self._send_json(json_response({
                "error": error_msg,
                "id": intent_id,
                "status": "failed",
            }))
            return

        estimate_data = est["data"].get("data", est["data"])
        intent["estimate"] = estimate_data

        # Step 2: real transfer (only if REAL_TRANSFER=1 and body has real=true)
        do_real = REAL_TRANSFER and data.get("real", False)

        if do_real:
            tx = _run_circle([
                "wallet", "transfer", recipient,
                "--amount", amount,
                "--token", USDC_TOKEN,
                "--address", WALLET_ADDR,
                "--chain", CHAIN,
                "--rpc-url", RPC_URL,
                "--output", "json",
            ], timeout=60)

            if tx.get("ok"):
                tx_data = tx["data"].get("data", tx["data"])
                intent["status"] = "submitted"
                intent["tx_hash"] = tx_data.get("txHash") or tx_data.get("transactionHash") or str(tx_data)
                self._send_json(json_response({
                    "id": intent_id,
                    "status": "submitted",
                    "estimate": estimate_data,
                    "transaction": tx_data,
                    "message": "Transaction submitted to Arc Testnet.",
                }))
            else:
                intent["status"] = "failed"
                self._send_json(json_response({
                    "id": intent_id,
                    "status": "failed",
                    "error": tx.get("error"),
                    "estimate": estimate_data,
                }))
        else:
            intent["status"] = "estimated"
            self._send_json(json_response({
                "id": intent_id,
                "status": "estimated",
                "estimate": estimate_data,
                "message": "Estimate ready. Set REAL_TRANSFER=1 and pass real=true to execute.",
            }))

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


# ── entry point ──────────────────────────────────────


def main() -> None:
    mode = "REAL" if REAL_TRANSFER else "ESTIMATE-ONLY"
    print(f"┌─────────────────────────────────────────────────────────────────┐")
    print(f"│  Arc Payment Intent Demo — Circle Wallet Integration            │")
    print(f"│  http://localhost:{PORT}/                                                  │")
    print(f"│  Wallet: {WALLET_ADDR}       │")
    print(f"│  Chain:  {CHAIN:44s}│")
    print(f"│  Mode:   {mode:44s}│")
    print(f"│                                                                 │")
    print(f"│  API endpoints:                                                │")
    print(f"│  GET  /api/wallet         — Wallet info + balance               │")
    print(f"│  GET  /api/transactions   — Transaction history (last 20)       │")
    print(f"│  POST /api/intent         — Create payment intent (auto-est.)   │")
    print(f"│  POST /api/approve        — Estimate or execute transfer        │")
    print(f"│  GET  /api/estimate       — Dry-run estimate                    │")
    print(f"│  GET  /api/network        — Arc Testnet info                    │")
    print(f"│  GET  /api/intents        — List intents                        │")
    print(f"│  GET  /api/status/<id>    — Intent status                       │")
    print(f"└─────────────────────────────────────────────────────────────────┘")
    if not REAL_TRANSFER:
        print(f"  ⚠  REAL_TRANSFER=0 — estimates only. Set REAL_TRANSFER=1 to enable.")
    print(f"  👛  Balance: $CIRCLE_WALLET_BALANCE (run demo to see real value)")
    try:
        server = HTTPServer((HOST, PORT), PaymentIntentHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
