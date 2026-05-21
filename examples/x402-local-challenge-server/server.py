#!/usr/bin/env python3
"""Local-only x402-style challenge server for Arc builder demos.

This example is intentionally production-shaped but not production-connected:
- it returns a deterministic 402 challenge for protected resources;
- it verifies a local demo proof through a verifier interface;
- it never opens a wallet, settles funds, or broadcasts transactions.

Replace ``LocalDemoVerifier`` with a real Circle/x402 verifier only after the
payment network, asset, recipient, and replay/expiry rules are fully scoped.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping, Protocol


@dataclass(frozen=True)
class PaymentConfig:
    """Safe-by-default payment request configuration for the demo boundary."""

    network: str
    asset: str
    amount: str
    pay_to: str
    resource: str
    verifier_mode: str = "local-simulation"
    human_approval_required: bool = True
    mainnet_enabled: bool = False

    @classmethod
    def demo(cls) -> "PaymentConfig":
        return cls(
            network="arc-testnet",
            asset="USDC",
            amount="0.01",
            pay_to="0xA11CE00000000000000000000000000000000000",
            resource="arc-mcp-builder-assistant.local-report.v1",
        )


@dataclass(frozen=True)
class Response:
    status: int
    body: dict[str, object]


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str
    receipt: dict[str, object]


class PaymentVerifier(Protocol):
    """Boundary for swapping local proof checks with a real verifier later."""

    def verify(self, proof: str, challenge: Mapping[str, object], config: PaymentConfig) -> VerificationResult:
        ...


class LocalDemoVerifier:
    """Accepts only explicit local demo proofs.

    Valid proof shape:
        local-demo:<challenge-id>:<amount>

    This is deliberately not a signature scheme. It is a deterministic local
    switch that lets the example model the 402 -> proof -> 200 flow without
    pretending that funds moved.
    """

    def verify(self, proof: str, challenge: Mapping[str, object], config: PaymentConfig) -> VerificationResult:
        expected = f"local-demo:{challenge['id']}:{config.amount}"
        if proof != expected:
            return VerificationResult(
                ok=False,
                reason="invalid_local_demo_proof",
                receipt={
                    "settled": False,
                    "transactionBroadcast": False,
                    "verifierMode": config.verifier_mode,
                },
            )
        return VerificationResult(
            ok=True,
            reason="local_demo_proof_accepted",
            receipt={
                "settled": False,
                "transactionBroadcast": False,
                "mainnetEnabled": config.mainnet_enabled,
                "verifierMode": config.verifier_mode,
                "challengeId": challenge["id"],
                "network": config.network,
                "asset": config.asset,
                "amount": config.amount,
            },
        )


def build_payment_challenge(config: PaymentConfig) -> dict[str, object]:
    """Return an x402-shaped payment challenge with safe local metadata."""

    challenge_id = f"{config.resource}:{config.network}:{config.asset}:{config.amount}"
    return {
        "id": challenge_id,
        "x402Version": "demo-boundary-v1",
        "resource": config.resource,
        "accepts": [
            {
                "scheme": "exact",
                "network": config.network,
                "asset": config.asset,
                "amount": config.amount,
                "payTo": config.pay_to,
            }
        ],
        "verifierMode": config.verifier_mode,
        "humanApprovalRequired": config.human_approval_required,
        "mainnetEnabled": config.mainnet_enabled,
        "transactionBroadcast": False,
        "instructions": "Approve locally only, then send X-Payment: local-demo:<challenge-id>:<amount>.",
    }


def payment_required_response(config: PaymentConfig, error: str = "payment_required") -> Response:
    challenge = build_payment_challenge(config)
    return Response(
        status=HTTPStatus.PAYMENT_REQUIRED,
        body={
            "error": error,
            **challenge,
        },
    )


def handle_protected_request(
    headers: Mapping[str, str],
    config: PaymentConfig | None = None,
    verifier: PaymentVerifier | None = None,
) -> Response:
    """Return 402 until a local verifier accepts the proof header."""

    config = config or PaymentConfig.demo()
    verifier = verifier or LocalDemoVerifier()
    proof = headers.get("X-Payment") or headers.get("x-payment")
    if not proof:
        return payment_required_response(config)

    challenge = build_payment_challenge(config)
    verification = verifier.verify(proof, challenge, config)
    if not verification.ok:
        return Response(
            status=HTTPStatus.PAYMENT_REQUIRED,
            body={
                "error": "payment_verification_failed",
                "reason": verification.reason,
                "settled": False,
                "transactionBroadcast": False,
                "challenge": challenge,
            },
        )

    return Response(
        status=HTTPStatus.OK,
        body={
            "ok": True,
            "data": {
                "message": "Protected Arc builder resource unlocked.",
                "resource": config.resource,
            },
            "receipt": verification.receipt,
        },
    )


class DemoHandler(BaseHTTPRequestHandler):
    config = PaymentConfig.demo()

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path in ("/", "/health"):
            self._send(Response(status=HTTPStatus.OK, body={"ok": True, "service": "x402-local-challenge-server"}))
            return
        if self.path.startswith("/protected"):
            self._send(handle_protected_request(self.headers, self.config))
            return
        self._send(Response(status=HTTPStatus.NOT_FOUND, body={"error": "not_found"}))

    def _send(self, response: Response) -> None:
        body = json.dumps(response.body, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(int(response.status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local-only x402 challenge server demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8087)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    print(f"local x402 challenge server listening on http://{args.host}:{args.port}")
    print("GET /protected returns a 402 challenge. No funds move in this demo.")
    server.serve_forever()


if __name__ == "__main__":
    main()
