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
  HOST, PORT          — local server bind (default: 127.0.0.1:8080)

Run:
    python3 examples/payment-intent-demo/server.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# ── project root ─────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── config ───────────────────────────────────────────
HOST = os.environ.get("HOST", "127.0.0.1")
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
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_REQUEST_BODY_BYTES = 64 * 1024
MAX_TEXT_FIELD_LENGTH = 500
SEND_CONFIRMATION = "SEND ARC TESTNET USDC"
MAX_REAL_TRANSFER_USDC = Decimal("1.00")
EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
USDC_AMOUNT_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$")

# ── in-memory store ─────────────────────────────────
intents: dict[str, dict] = {}


# ── helpers ──────────────────────────────────────────


def json_response(data: Any, status: int = 200) -> tuple[bytes, int, dict]:
    body = json.dumps(data, indent=2).encode()
    return body, status, {"Content-Type": "application/json"}


def validate_runtime_config() -> None:
    if HOST not in LOCAL_HOSTS:
        raise ValueError("HOST must remain localhost-only for the wallet-backed demo")
    if not 1 <= PORT <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    if CHAIN != "ARC-TESTNET":
        raise ValueError("CIRCLE_CHAIN must be exactly ARC-TESTNET")
    if not EVM_ADDRESS_RE.fullmatch(WALLET_ADDR):
        raise ValueError("CIRCLE_WALLET_ADDR must be a valid EVM address")
    if not EVM_ADDRESS_RE.fullmatch(USDC_TOKEN) or int(USDC_TOKEN[2:], 16) == 0:
        raise ValueError("CIRCLE_USDC_TOKEN must be a non-zero EVM address")
    parsed_rpc = urlparse(RPC_URL)
    local_http = parsed_rpc.scheme == "http" and parsed_rpc.hostname in LOCAL_HOSTS
    if (
        not parsed_rpc.hostname
        or (parsed_rpc.scheme != "https" and not local_http)
        or parsed_rpc.username
        or parsed_rpc.password
        or parsed_rpc.query
        or parsed_rpc.fragment
    ):
        raise ValueError(
            "CIRCLE_RPC_URL must use HTTPS or local HTTP without credentials or query data"
        )


def validate_intent_input(data: Any) -> tuple[dict[str, str] | None, str | None]:
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"
    recipient = data.get("recipient", "")
    amount = data.get("amount", "")
    agent = data.get("agent", "Payment Agent")
    memo = data.get("memo", "")
    asset = data.get("asset", "USDC")
    if not isinstance(recipient, str) or not EVM_ADDRESS_RE.fullmatch(recipient):
        return None, "recipient must be a valid EVM address"
    try:
        parsed_amount = Decimal(amount) if isinstance(amount, str) else Decimal(0)
    except InvalidOperation:
        parsed_amount = Decimal(0)
    if not isinstance(amount, str) or not USDC_AMOUNT_RE.fullmatch(amount) or parsed_amount <= 0:
        return None, "amount must be a positive USDC decimal with at most 6 places"
    if asset != "USDC":
        return None, "asset must be USDC"
    for name, value in (("agent", agent), ("memo", memo)):
        if (
            not isinstance(value, str)
            or len(value) > MAX_TEXT_FIELD_LENGTH
            or any(char in value for char in "\r\n\0")
        ):
            return None, (
                f"{name} must be a single line of at most "
                f"{MAX_TEXT_FIELD_LENGTH} characters"
            )
    return {
        "agent": agent or "Payment Agent",
        "recipient": recipient,
        "amount": amount,
        "asset": "USDC",
        "memo": memo,
    }, None


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
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._send_json(json_response({"error": "Invalid Content-Length"}, 400))
            return
        if content_length < 0 or content_length > MAX_REQUEST_BODY_BYTES:
            self._send_json(json_response({"error": "Request body exceeds 64 KB limit"}, 413))
            return
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(json_response({"error": "Invalid JSON"}, 400))
            return
        if not isinstance(data, dict):
            self._send_json(json_response({"error": "Request body must be a JSON object"}, 400))
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
        normalized, error = validate_intent_input(data)
        if error or normalized is None:
            self._send_json(json_response({"error": error}, 400))
            return
        intent_id = str(uuid.uuid4())[:8]
        intent = {
            "id": intent_id,
            **normalized,
            "status": "pending_user_approval",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tx_hash": None,
            "estimate": None,
            "send_attempted": False,
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

        requested_real = data.get("real") is True
        if requested_real and data.get("confirmation") != SEND_CONFIRMATION:
            self._send_json(
                json_response({"error": "Exact Arc Testnet send confirmation is required"}, 400)
            )
            return
        if requested_real and intent.get("send_attempted"):
            self._send_json(json_response({"error": "This intent already used its one send attempt"}, 409))
            return
        if requested_real and REAL_TRANSFER and Decimal(amount) > MAX_REAL_TRANSFER_USDC:
            self._send_json(
                json_response(
                    {"error": f"Real transfer cap is {MAX_REAL_TRANSFER_USDC} USDC"},
                    400,
                )
            )
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

        # Step 2: real transfer requires server opt-in and an exact typed phrase.
        do_real = REAL_TRANSFER and requested_real

        if do_real:
            intent["send_attempted"] = True
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
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"[PaymentIntentDemo] {args[0]} {args[1]} {args[2]}\n")


# ── entry point ──────────────────────────────────────


def main() -> None:
    validate_runtime_config()
    mode = "REAL" if REAL_TRANSFER else "ESTIMATE-ONLY"
    print("┌─────────────────────────────────────────────────────────────────┐")
    print("│  Arc Payment Intent Demo — Circle Wallet Integration            │")
    print(f"│  http://localhost:{PORT}/                                                  │")
    print(f"│  Wallet: {WALLET_ADDR}       │")
    print(f"│  Chain:  {CHAIN:44s}│")
    print(f"│  Mode:   {mode:44s}│")
    print("│                                                                 │")
    print("│  API endpoints:                                                │")
    print("│  GET  /api/wallet         — Wallet info + balance               │")
    print("│  GET  /api/transactions   — Transaction history (last 20)       │")
    print("│  POST /api/intent         — Create payment intent (auto-est.)   │")
    print("│  POST /api/approve        — Estimate or execute transfer        │")
    print("│  GET  /api/estimate       — Dry-run estimate                    │")
    print("│  GET  /api/network        — Arc Testnet info                    │")
    print("│  GET  /api/intents        — List intents                        │")
    print("│  GET  /api/status/<id>    — Intent status                       │")
    print("└─────────────────────────────────────────────────────────────────┘")
    if not REAL_TRANSFER:
        print("  ⚠  REAL_TRANSFER=0 — estimates only. Set REAL_TRANSFER=1 to enable.")
    print("  👛  Balance: $CIRCLE_WALLET_BALANCE (run demo to see real value)")
    try:
        server = HTTPServer((HOST, PORT), PaymentIntentHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
