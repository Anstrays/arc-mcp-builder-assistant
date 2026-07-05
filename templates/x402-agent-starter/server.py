#!/usr/bin/env python3
"""Minimal local x402 paid-agent boundary starter for Arc Testnet.

Dependency-free. No wallet, signing, or broadcast. The local demo proof is a
deterministic switch, not a real payment credential.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

NETWORK = "arc-testnet"
ASSET = "USDC"
DEFAULT_AMOUNT = "0.01"
DEFAULT_PAY_TO = "0xA11CE00000000000000000000000000000000000"
MAX_AMOUNT_LEN = 24
MAX_PAYMENT_HEADER = 4096


def _load_config() -> dict[str, str]:
    mainnet = os.environ.get("X402_DEMO_MAINNET_ENABLED", "false").lower()
    if mainnet in ("1", "true", "yes"):
        print("error: mainnet is disabled in this starter", file=sys.stderr)
        sys.exit(1)
    amount = os.environ.get("X402_DEMO_AMOUNT", DEFAULT_AMOUNT)
    pay_to = os.environ.get("X402_DEMO_PAY_TO", DEFAULT_PAY_TO)
    if not _valid_amount(amount):
        raise ValueError(f"invalid amount: {amount}")
    if not _valid_address(pay_to):
        raise ValueError(f"invalid pay-to address: {pay_to}")
    return {"network": NETWORK, "asset": ASSET, "amount": amount, "pay_to": pay_to}


def _valid_amount(amount: str) -> bool:
    if not isinstance(amount, str) or not amount:
        return False
    if len(amount) > MAX_AMOUNT_LEN:
        return False
    return bool(re.fullmatch(r"[0-9]+(\.[0-9]{1,6})?", amount)) and float(amount) > 0


def _valid_address(addr: str) -> bool:
    return (
        isinstance(addr, str)
        and len(addr) == 42
        and addr.startswith("0x")
        and addr.lower() != "0x" + "0" * 40
        and bool(re.fullmatch(r"0x[0-9a-fA-F]{40}", addr))
    )


def _challenge_id(config: dict[str, str]) -> str:
    payload = f"{config['network']}:{config['asset']}:{config['amount']}:{config['pay_to']}:starter"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _proof_hint(config: dict[str, str]) -> str:
    return f"local-demo:{_challenge_id(config)}:{config['amount']}"


class Handler(BaseHTTPRequestHandler):
    config: dict[str, str]

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass

    def _json(self, status: int, body: object) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, indent=2).encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/protected":
            self._handle_protected()
        elif parsed.path == "/manifest":
            self._handle_manifest()
        else:
            self._json(404, {"error": "not found"})

    def _handle_protected(self) -> None:
        payment = self.headers.get("X-Payment", "")
        if _valid_payment(payment, self.config):
            self._json(200, {
                "message": "paid resource",
                "receipt": {
                    "settled": False,
                    "transactionBroadcast": False,
                    "network": self.config["network"],
                    "asset": self.config["asset"],
                    "amount": self.config["amount"],
                },
            })
            return
        self._json(402, {
            "id": _challenge_id(self.config),
            "accepts": {
                "network": self.config["network"],
                "asset": self.config["asset"],
                "amount": self.config["amount"],
                "payTo": self.config["pay_to"],
            },
            "localDemoProof": _proof_hint(self.config),
        })

    def _handle_manifest(self) -> None:
        self._json(200, {
            "name": "arc-x402-agent-starter",
            "network": self.config["network"],
            "asset": self.config["asset"],
            "amount": self.config["amount"],
            "payTo": self.config["pay_to"],
            "safety": {
                "testnetOnly": True,
                "humanApproval": True,
                "noPrivateKeys": True,
                "noAutonomousSpending": True,
            },
        })


def _valid_payment(header: str, config: dict[str, str]) -> bool:
    if not isinstance(header, str) or len(header) > MAX_PAYMENT_HEADER:
        return False
    if re.search(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", header):
        return False
    parts = header.split(":")
    if len(parts) != 3:
        return False
    scheme, challenge, amount = parts
    return (
        scheme == "local-demo"
        and challenge == _challenge_id(config)
        and amount == config["amount"]
    )


def _print_manifest(config: dict[str, str]) -> None:
    print(json.dumps({
        "name": "arc-x402-agent-starter",
        "network": config["network"],
        "asset": config["asset"],
        "amount": config["amount"],
        "payTo": config["pay_to"],
        "localDemoProof": _proof_hint(config),
        "safety": {
            "testnetOnly": True,
            "humanApproval": True,
            "noPrivateKeys": True,
            "noAutonomousSpending": True,
        },
    }, indent=2))


def _print_challenge(config: dict[str, str]) -> None:
    print(json.dumps({
        "id": _challenge_id(config),
        "accepts": {
            "network": config["network"],
            "asset": config["asset"],
            "amount": config["amount"],
            "payTo": config["pay_to"],
        },
        "localDemoProof": _proof_hint(config),
    }, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Arc x402 paid-agent starter")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--print-manifest", action="store_true")
    parser.add_argument("--print-challenge", action="store_true")
    args = parser.parse_args(argv)
    config = _load_config()
    if args.print_manifest:
        _print_manifest(config)
        return 0
    if args.print_challenge:
        _print_challenge(config)
        return 0
    Handler.config = config
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Arc x402 starter running on http://127.0.0.1:{args.port}/protected")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
