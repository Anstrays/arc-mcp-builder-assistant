#!/usr/bin/env python3
"""x402 Verified API — paid endpoint prototype for Arc Testnet.

Returns 402 Payment Required for unauthenticated requests. Accepts an
X-Payment header with an Arc Testnet transaction hash and verifies the
on-chain USDC Transfer event via read-only RPC before serving content.

Safety: read-only RPC only, no keys, no broadcast, testnet-only.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib import request as urllib_request

PORT = int(os.environ.get("PORT", "8094"))

# Arc Testnet constants
ARC_TESTNET_RPC_URL = "https://rpc.testnet.arc.network"
ARC_TESTNET_CHAIN_ID = 5042002
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TX_HASH_RE = __import__("re").compile(r"^0x[a-fA-F0-9]{64}$")

# The pay-to address for this demo — CHANGE to your own wallet
PAY_TO = "0x0cd9b933302d90bfe295471deac7f4eafd9ea401"
AMOUNT_USDC = "1.00"

PROTECTED_CONTENT = {
    "ok": True,
    "message": "This is the protected resource, served after valid x402 payment verification.",
    "network": "arc-testnet",
    "chainId": ARC_TESTNET_CHAIN_ID,
    "asset": "USDC",
    "timestamp": None,  # filled at response time
}


def rpc_call(method: str, params: list[Any]) -> dict[str, Any] | None:
    """Make a read-only JSON-RPC call to Arc Testnet."""
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib_request.Request(
        ARC_TESTNET_RPC_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
    except Exception:
        return None
    return result


def verify_payment(tx_hash: str) -> dict[str, Any]:
    """Verify an on-chain USDC payment via read-only RPC."""
    if not TX_HASH_RE.match(tx_hash):
        return {"verified": False, "reason": "invalid tx hash format"}

    receipt = rpc_call("eth_getTransactionReceipt", [tx_hash])
    if not receipt or not isinstance(receipt.get("result"), dict):
        return {"verified": False, "reason": "transaction not found on Arc Testnet"}

    result = receipt["result"]
    status = result.get("status")
    if status == "0x0":
        return {"verified": False, "reason": "transaction reverted"}

    logs = result.get("logs", [])
    for log in logs:
        topics = log.get("topics", [])
        if len(topics) >= 3 and topics[0] == TRANSFER_TOPIC:
            log_addr = log.get("address", "")
            if log_addr.lower() != USDC_CONTRACT.lower():
                continue
            to_addr = "0x" + topics[2][-40:]
            if to_addr.lower() != PAY_TO.lower():
                continue
            return {"verified": True, "txHash": tx_hash, "to": to_addr}

    return {"verified": False, "reason": "no matching USDC Transfer event"}


class VerifiedAPIHandler(BaseHTTPRequestHandler):
    def _json(self, data: object, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _challenge(self) -> dict[str, Any]:
        return {
            "status": "payment_required",
            "network": "arc-testnet",
            "chainId": ARC_TESTNET_CHAIN_ID,
            "asset": "USDC",
            "amount": AMOUNT_USDC,
            "payTo": PAY_TO,
            "accepts": [
                {
                    "scheme": "exact",
                    "network": "arc-testnet",
                    "asset": "USDC",
                    "amount": AMOUNT_USDC,
                    "payTo": PAY_TO,
                }
            ],
        }

    def do_GET(self) -> None:
        if self.path != "/protected":
            self._json({"service": "arc-x402-verified-api", "endpoints": ["/protected"]})
            return

        tx_hash = self.headers.get("X-Payment", "").strip()

        if not tx_hash:
            # No payment proof — return 402 challenge
            self._json(self._challenge(), 402)
            return

        # Verify the payment
        result = verify_payment(tx_hash)
        if not result.get("verified"):
            self._json({"ok": False, "error": "payment verification failed", "detail": result}, 402)
            return

        from datetime import datetime, timezone
        PROTECTED_CONTENT["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._json(PROTECTED_CONTENT)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: N802
        sys.stderr.write(f"[x402-verified-api] {args[0]} {args[1]} {args[2]}\n")


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), VerifiedAPIHandler)
    print(f"[x402-verified-api] x402 Verified API prototype on http://127.0.0.1:{PORT}")
    print(f"[x402-verified-api] PAY_TO: {PAY_TO}, Amount: {AMOUNT_USDC} USDC")
    print(f"[x402-verified-api] Endpoints: GET /protected")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
