#!/usr/bin/env python3
"""Arc Testnet paid API endpoint prototype.

This example models a production-shaped paid API boundary while staying safe by
construction:
- no private keys are accepted;
- no wallet signing or transaction broadcast happens here;
- all payment verification is read-only Arc Testnet receipt inspection;
- a human must provide a transaction hash as the X-Payment proof.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Mapping, Protocol
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arc_builder_kit import x402_client as x402  # noqa: E402

DEFAULT_NETWORK = "arc-testnet"
DEFAULT_ASSET = "USDC"
DEFAULT_AMOUNT = "0.01"
DEFAULT_PAY_TO = "0xA11CE00000000000000000000000000000000000"
DEFAULT_RESOURCE = "arc-paid-api-endpoint.prototype.report.v1"
ZERO_EVM_ADDRESS = "0x0000000000000000000000000000000000000000"
LOCAL_BIND_HOSTS = {"127.0.0.1", "localhost"}
TRUTHY = {"1", "true", "yes", "on"}
FALSY = {"", "0", "false", "no", "off"}
MAX_PAYMENT_PROOF_BYTES = 256


@dataclass(frozen=True)
class PaidApiConfig:
    network: str
    asset: str
    amount: str
    pay_to: str
    resource: str
    rpc_url: str = x402.ARC_TESTNET_RPC_URL
    human_approval_required: bool = True
    mainnet_enabled: bool = False

    @classmethod
    def demo(cls) -> "PaidApiConfig":
        return cls(
            network=DEFAULT_NETWORK,
            asset=DEFAULT_ASSET,
            amount=DEFAULT_AMOUNT,
            pay_to=DEFAULT_PAY_TO,
            resource=DEFAULT_RESOURCE,
        )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PaidApiConfig":
        values = os.environ if env is None else env
        forbidden_secret_keys = (
            "ARC_PAID_API_PRIVATE_KEY",
            "PRIVATE_KEY",
            "WALLET_PRIVATE_KEY",
            "MNEMONIC",
            "SEED_PHRASE",
        )
        for key in forbidden_secret_keys:
            if values.get(key):
                raise ValueError(f"private key or seed input is forbidden: {key}")
        config = cls(
            network=(values.get("ARC_PAID_API_NETWORK", DEFAULT_NETWORK).strip() or DEFAULT_NETWORK),
            asset=(values.get("ARC_PAID_API_ASSET", DEFAULT_ASSET).strip() or DEFAULT_ASSET),
            amount=(values.get("ARC_PAID_API_AMOUNT", DEFAULT_AMOUNT).strip() or DEFAULT_AMOUNT),
            pay_to=(values.get("ARC_PAID_API_PAY_TO", DEFAULT_PAY_TO).strip() or DEFAULT_PAY_TO),
            resource=DEFAULT_RESOURCE,
            rpc_url=(values.get("ARC_PAID_API_RPC_URL", x402.ARC_TESTNET_RPC_URL).strip() or x402.ARC_TESTNET_RPC_URL),
            mainnet_enabled=parse_env_bool(values.get("ARC_PAID_API_MAINNET_ENABLED", "false"), "ARC_PAID_API_MAINNET_ENABLED"),
        )
        validate_config(config)
        return config


@dataclass(frozen=True)
class ReceiptCheck:
    verified: bool
    reason: str
    tx_hash: str
    chain_id: int | None = None
    from_address: str | None = None
    to_address: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "reason": self.reason,
            "txHash": self.tx_hash,
            "chainId": self.chain_id,
            "from": self.from_address,
            "to": self.to_address,
        }


@dataclass(frozen=True)
class Response:
    status: int
    body: dict[str, object]


class ReceiptVerifier(Protocol):
    def verify(self, tx_hash: str, challenge: Mapping[str, object], config: PaidApiConfig) -> ReceiptCheck:
        ...


class ArcReceiptVerifier:
    """Read-only Arc Testnet receipt verifier."""

    def verify(self, tx_hash: str, challenge: Mapping[str, object], config: PaidApiConfig) -> ReceiptCheck:
        parsed = x402.parse_challenge(challenge)
        result = x402.verify_receipt(
            tx_hash,
            challenge=parsed,
            rpc_url=config.rpc_url,
            expected_chain_id=x402.ARC_TESTNET_CHAIN_ID,
        )
        return ReceiptCheck(
            verified=result.verified,
            reason=result.reason,
            tx_hash=tx_hash,
            chain_id=result.chain_id,
            from_address=result.from_address,
            to_address=result.to_address,
        )


def parse_env_bool(value: str | None, name: str) -> bool:
    normalized = (value or "").strip().lower()
    if normalized in TRUTHY:
        return True
    if normalized in FALSY:
        return False
    raise ValueError(f"{name} must be one of true/false/1/0/yes/no/on/off")


def validate_config(config: PaidApiConfig) -> None:
    if config.network != DEFAULT_NETWORK:
        raise ValueError("ARC_PAID_API_NETWORK must stay arc-testnet; mainnet is not supported")
    if config.asset != DEFAULT_ASSET:
        raise ValueError("ARC_PAID_API_ASSET must stay USDC")
    x402.validate_amount(config.amount)
    if amount_to_micro_usd(config.amount) <= 0:
        raise ValueError("ARC_PAID_API_AMOUNT must be greater than 0")
    x402.validate_evm_address(config.pay_to)
    if config.pay_to.lower() == ZERO_EVM_ADDRESS:
        raise ValueError("ARC_PAID_API_PAY_TO must be a non-zero EVM address")
    if config.resource != DEFAULT_RESOURCE:
        raise ValueError("resource must stay pinned to the reviewed prototype resource")
    if config.human_approval_required is not True:
        raise ValueError("human approval must remain required")
    if config.mainnet_enabled is not False:
        raise ValueError("ARC_PAID_API_MAINNET_ENABLED must remain false; mainnet is disabled")
    if not (config.rpc_url.startswith("https://") or config.rpc_url.startswith("http://127.0.0.1") or config.rpc_url.startswith("http://localhost")):
        raise ValueError("ARC_PAID_API_RPC_URL must be https or localhost for tests")


def validate_bind_target(host: str, port: int) -> None:
    if host.strip().lower() not in LOCAL_BIND_HOSTS:
        raise ValueError("paid API prototype must bind to localhost/127.0.0.1 by default")
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")


def amount_to_micro_usd(amount: str) -> int:
    whole, dot, fractional = amount.partition(".")
    if not whole.isdigit() or (dot and not fractional.isdigit()):
        raise ValueError("amount must be a positive decimal string")
    if len(fractional) > x402.USDC_DECIMALS:
        raise ValueError("USDC uses at most 6 decimal places")
    return int(whole) * 1_000_000 + int(fractional.ljust(6, "0") or "0")


def build_challenge(config: PaidApiConfig) -> dict[str, object]:
    validate_config(config)
    challenge_id = f"{config.resource}:{config.network}:{config.asset}:{config.amount}:{config.pay_to.lower()}"
    return {
        "id": challenge_id,
        "x402Version": "arc-paid-api-prototype-v1",
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
        "humanApprovalRequired": True,
        "mainnetEnabled": False,
        "transactionBroadcast": False,
        "privateKeysAccepted": False,
        "instructions": "Send exactly the reviewed Arc Testnet USDC payment yourself, then retry with X-Payment: <tx-hash>.",
    }


def build_manifest(config: PaidApiConfig) -> dict[str, object]:
    validate_config(config)
    return {
        "name": "arc-paid-api-endpoint-prototype",
        "version": "0.1.0",
        "description": "Local Arc Testnet paid API prototype with read-only tx-hash receipt verification.",
        "network": {
            "name": "Arc Testnet",
            "chainId": x402.ARC_TESTNET_CHAIN_ID,
            "chainIdHex": x402.ARC_TESTNET_CHAIN_ID_HEX,
            "rpc": x402.ARC_TESTNET_RPC_URL,
            "explorer": x402.ARC_TESTNET_EXPLORER_URL,
        },
        "payment": {
            "network": config.network,
            "asset": config.asset,
            "assetDecimals": x402.USDC_DECIMALS,
            "amount": config.amount,
            "priceMicroUsd": amount_to_micro_usd(config.amount),
            "payTo": config.pay_to,
            "resource": config.resource,
        },
        "endpoints": {
            "health": "/health",
            "manifest": "/manifest",
            "protected": "/protected",
        },
        "safety": {
            "testnetOnly": True,
            "humanApprovalRequired": True,
            "readOnlyReceiptVerification": True,
            "privateKeysAccepted": False,
            "transactionBroadcast": False,
            "autonomousSpending": False,
            "mainnetEnabled": False,
        },
    }


def extract_payment_hash(headers: object) -> str | None:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        raw_values = get_all("X-Payment") or []
        if isinstance(raw_values, list):
            values = [value for value in raw_values if isinstance(value, str)]
        else:
            values = []
    elif isinstance(headers, Mapping):
        values = [value for key, value in headers.items() if isinstance(key, str) and key.lower() == "x-payment" and isinstance(value, str)]
    else:
        values = []
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("exactly one X-Payment header is required")
    proof = values[0]
    if not isinstance(proof, str) or not proof:
        raise ValueError("X-Payment must be a non-empty transaction hash")
    if len(proof.encode("utf-8")) > MAX_PAYMENT_PROOF_BYTES:
        raise ValueError("X-Payment exceeds safety size limit")
    if any(character in proof for character in "\r\n\0"):
        raise ValueError("X-Payment contains forbidden control characters")
    x402.validate_tx_hash(proof)
    return proof


def payment_required(config: PaidApiConfig, error: str = "payment_required", reason: str | None = None) -> Response:
    body: dict[str, object] = {
        "error": error,
        **build_challenge(config),
        "manifest": build_manifest(config),
        "settled": False,
        "transactionBroadcast": False,
    }
    if reason:
        body["reason"] = reason
    return Response(status=HTTPStatus.PAYMENT_REQUIRED, body=body)


def handle_protected_request(
    headers: Mapping[str, str],
    config: PaidApiConfig | None = None,
    verifier: ReceiptVerifier | None = None,
) -> Response:
    config = config or PaidApiConfig.demo()
    verifier = verifier or ArcReceiptVerifier()
    try:
        tx_hash = extract_payment_hash(headers)
    except ValueError as error:
        return payment_required(config, error="invalid_x_payment", reason=str(error))
    if tx_hash is None:
        return payment_required(config)

    challenge = build_challenge(config)
    try:
        receipt = verifier.verify(tx_hash, challenge, config)
    except Exception:
        return payment_required(config, error="payment_verifier_unavailable")
    if not isinstance(receipt, ReceiptCheck):
        return payment_required(config, error="invalid_verifier_result")
    if not receipt.verified:
        return payment_required(config, error="payment_verification_failed", reason=receipt.reason)

    return Response(
        status=HTTPStatus.OK,
        body={
            "ok": True,
            "data": {
                "kind": "paid-api-prototype",
                "message": "Protected Arc paid API resource unlocked after read-only receipt verification.",
                "resource": config.resource,
            },
            "receipt": receipt.to_dict(),
            "manifest": build_manifest(config),
            "safety": build_manifest(config)["safety"],
        },
    )


class PaidApiHandler(BaseHTTPRequestHandler):
    config = PaidApiConfig.demo()

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlsplit(self.path).path
        if path in ("/", "/health"):
            self._send(Response(status=HTTPStatus.OK, body={"ok": True, "service": "arc-paid-api-endpoint"}))
            return
        if path == "/manifest":
            self._send(Response(status=HTTPStatus.OK, body=build_manifest(self.config)))
            return
        if path == "/protected":
            self._send(handle_protected_request(self.headers, self.config))
            return
        self._send(Response(status=HTTPStatus.NOT_FOUND, body={"error": "not_found"}))

    def _send(self, response: Response) -> None:
        body = json.dumps(response.body, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(int(response.status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Arc Testnet paid API endpoint prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8098)
    parser.add_argument("--print-manifest", action="store_true", help="Print manifest JSON and exit.")
    parser.add_argument("--print-challenge", action="store_true", help="Print protected endpoint 402 challenge JSON and exit.")
    args = parser.parse_args()

    try:
        config = PaidApiConfig.from_env()
    except ValueError as error:
        raise SystemExit(f"Invalid paid API prototype configuration: {error}") from error

    if args.print_manifest:
        print_json(build_manifest(config))
        return
    if args.print_challenge:
        print_json(build_challenge(config))
        return

    try:
        validate_bind_target(args.host, args.port)
    except ValueError as error:
        raise SystemExit(f"Invalid local server bind target: {error}") from error
    PaidApiHandler.config = config
    server = ThreadingHTTPServer((args.host, args.port), PaidApiHandler)
    print(f"Arc paid API prototype listening on http://{args.host}:{args.port}")
    print("GET /protected returns 402 until X-Payment carries a human-approved Arc Testnet tx hash.")
    server.serve_forever()


if __name__ == "__main__":
    main()
