#!/usr/bin/env python3
"""Minimal agent marketplace demo on Arc Testnet.

Endpoints:
  GET  /intents       — list open payment intents
  POST /fulfill       — submit a fulfillment with local-demo proof
  GET  /intent/<id>   — get details of a specific intent

Safety: local-only mock data, no broadcast, no keys.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse

PORT = int(os.environ.get("PORT", "8092"))
DEMO_INTENTS = [
    {
        "id": "demo-1",
        "description": "AI data processing job",
        "amount": "10.00",
        "asset": "USDC",
        "network": "arc-testnet",
        "status": "open",
        "buyer": "0xBuyerAddress000000000000000000000000000001",
    },
    {
        "id": "demo-2",
        "description": "Model inference request",
        "amount": "5.50",
        "asset": "USDC",
        "network": "arc-testnet",
        "status": "open",
        "buyer": "0xBuyerAddress000000000000000000000000000002",
    },
]


class MarketplaceHandler(BaseHTTPRequestHandler):
    def _json(self, data: object, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/intents":
            open_intents = [i for i in DEMO_INTENTS if i["status"] == "open"]
            self._json({"ok": True, "intents": open_intents, "count": len(open_intents)})

        elif path.startswith("/intent/"):
            intent_id = path.split("/")[-1]
            for intent in DEMO_INTENTS:
                if intent["id"] == intent_id:
                    self._json({"ok": True, "intent": intent})
                    return
            self._json({"ok": False, "error": "intent not found"}, 404)

        else:
            self._json({"ok": True, "service": "arc-marketplace-demo", "endpoints": ["/intents", "/intent/<id>", "/fulfill"]})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/fulfill":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._json({"ok": False, "error": "invalid JSON"}, 400)
                return

            intent_id = data.get("intentId", "")
            seller = data.get("seller", "")
            proof = data.get("proof", "")

            if not intent_id or not seller:
                self._json({"ok": False, "error": "intentId and seller are required"}, 400)
                return

            for intent in DEMO_INTENTS:
                if intent["id"] == intent_id:
                    if intent["status"] != "open":
                        self._json({"ok": False, "error": "intent already fulfilled"}, 409)
                        return
                    # Simulate fulfillment
                    intent["status"] = "fulfilled"
                    intent["seller"] = seller
                    intent["proof"] = proof or "local-demo"
                    self._json({
                        "ok": True,
                        "fulfillment": {
                            "intentId": intent_id,
                            "seller": seller,
                            "proof": intent["proof"],
                            "status": "pending_verification",
                        },
                        "note": "In production, broadcast a USDC transfer and verify on-chain.",
                    }, 201)
                    return

            self._json({"ok": False, "error": "intent not found"}, 404)
        else:
            self._json({"ok": False, "error": "not found"}, 404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: N802
        sys.stderr.write(f"[marketplace] {args[0]} {args[1]} {args[2]}\n")


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), MarketplaceHandler)
    print(f"[marketplace] Arc Agent Marketplace demo on http://127.0.0.1:{PORT}")
    print("[marketplace] Endpoints: GET /intents, GET /intent/<id>, POST /fulfill")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
