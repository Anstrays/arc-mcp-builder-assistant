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
import os
import re
import sys
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator, Mapping, Protocol
from urllib.parse import urlsplit

DEFAULT_NETWORK = "arc-testnet"
DEFAULT_ASSET = "USDC"
DEFAULT_AMOUNT = "0.01"
DEFAULT_PAY_TO = "0xA11CE00000000000000000000000000000000000"
DEFAULT_RESOURCE = "arc-mcp-builder-assistant.local-report.v1"
ZERO_EVM_ADDRESS = "0x0000000000000000000000000000000000000000"
EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
TRUTHY = {"1", "true", "yes", "on"}
FALSY = {"", "0", "false", "no", "off"}
LOCAL_BIND_HOSTS = {"127.0.0.1", "localhost"}
MAX_MCP_LINE_BYTES = 1_000_000
MAX_PAYMENT_PROOF_BYTES = 4_096


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
            network=DEFAULT_NETWORK,
            asset=DEFAULT_ASSET,
            amount=DEFAULT_AMOUNT,
            pay_to=DEFAULT_PAY_TO,
            resource=DEFAULT_RESOURCE,
        )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PaymentConfig":
        values = os.environ if env is None else env
        config = cls(
            network=values.get("X402_DEMO_NETWORK", DEFAULT_NETWORK).strip() or DEFAULT_NETWORK,
            asset=values.get("X402_DEMO_ASSET", DEFAULT_ASSET).strip() or DEFAULT_ASSET,
            amount=values.get("X402_DEMO_AMOUNT", DEFAULT_AMOUNT).strip() or DEFAULT_AMOUNT,
            pay_to=values.get("X402_DEMO_PAY_TO", DEFAULT_PAY_TO).strip() or DEFAULT_PAY_TO,
            resource=DEFAULT_RESOURCE,
            mainnet_enabled=parse_env_bool(values.get("X402_DEMO_MAINNET_ENABLED", "false"), "X402_DEMO_MAINNET_ENABLED"),
        )
        validate_payment_config(config)
        return config


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


def require_exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        unknown = sorted(observed - expected)
        raise ValueError(f"{label} keys must match exactly; missing={missing}, unknown={unknown}")


def validate_payment_proof(proof: str) -> str:
    if not isinstance(proof, str):
        raise ValueError("X-Payment proof must be a string")
    if not proof:
        raise ValueError("X-Payment proof must not be empty")
    if len(proof.encode("utf-8")) > MAX_PAYMENT_PROOF_BYTES:
        raise ValueError("X-Payment proof exceeds the 4 KB safety limit")
    if any(character in proof for character in "\r\n\0"):
        raise ValueError("X-Payment proof contains forbidden control characters")
    return proof


def extract_payment_proof(headers: Mapping[str, str]) -> str | None:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        values = get_all("X-Payment") or []
    else:
        values = [
            value
            for key, value in headers.items()
            if isinstance(key, str) and key.lower() == "x-payment"
        ]
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("exactly one X-Payment header is required")
    return validate_payment_proof(values[0])


def parse_env_bool(value: str | None, name: str) -> bool:
    normalized = (value or "").strip().lower()
    if normalized in TRUTHY:
        return True
    if normalized in FALSY:
        return False
    raise ValueError(f"{name} must be one of true/false/1/0/yes/no/on/off")


def amount_to_micro_usd(amount: str) -> int:
    """Convert a decimal USDC string to integer microUSD for agents."""

    whole, dot, fractional = amount.partition(".")
    if not whole.isdigit() or (dot and not fractional.isdigit()):
        raise ValueError("amount must be a positive decimal string")
    if len(fractional) > 6:
        raise ValueError("USDC demo amounts use at most 6 decimal places")
    return int(whole) * 1_000_000 + int(fractional.ljust(6, "0") or "0")


def validate_payment_config(config: PaymentConfig) -> None:
    """Reject config that would weaken the local Arc Testnet boundary."""

    if config.network != DEFAULT_NETWORK:
        raise ValueError("X402_DEMO_NETWORK must stay arc-testnet for this Arc-focused demo")
    if config.asset != DEFAULT_ASSET:
        raise ValueError("X402_DEMO_ASSET must stay USDC because this demo uses USDC 6-decimal economics")
    try:
        amount_micro_usd = amount_to_micro_usd(config.amount)
    except ValueError as error:
        raise ValueError(f"X402_DEMO_AMOUNT invalid: {error}") from error
    if amount_micro_usd <= 0:
        raise ValueError("X402_DEMO_AMOUNT must be greater than 0")
    if not EVM_ADDRESS_RE.match(config.pay_to):
        raise ValueError("X402_DEMO_PAY_TO must be a 42-character EVM address")
    if config.pay_to.lower() == ZERO_EVM_ADDRESS:
        raise ValueError("X402_DEMO_PAY_TO must be a non-zero EVM address")
    if config.resource != DEFAULT_RESOURCE:
        raise ValueError("payment resource must stay pinned to the reviewed local demo resource")
    if config.verifier_mode != "local-simulation":
        raise ValueError("verifier mode must stay local-simulation in this demo")
    if config.human_approval_required is not True:
        raise ValueError("human approval must remain required in this demo")
    if config.mainnet_enabled is not False:
        raise ValueError("X402_DEMO_MAINNET_ENABLED must remain false in this local demo")


def validate_bind_target(host: str, port: int) -> None:
    """Keep the local proof demo unavailable on external interfaces."""
    if host.strip().lower() not in LOCAL_BIND_HOSTS:
        raise ValueError("--host must stay 127.0.0.1 or localhost for this local-only demo")
    if not 1 <= port <= 65535:
        raise ValueError("--port must be between 1 and 65535")


def build_unit_economics(config: PaymentConfig) -> dict[str, object]:
    """Return integer-priced demo economics without float ambiguity."""

    validate_payment_config(config)
    return {
        "asset": config.asset,
        "assetDecimals": 6,
        "priceMicroUsd": amount_to_micro_usd(config.amount),
        "displayPrice": f"{config.amount} {config.asset}",
        "billingModel": "one local demo proof unlocks one protected report response",
    }


def build_payment_challenge(config: PaymentConfig) -> dict[str, object]:
    """Return an x402-shaped payment challenge with safe local metadata."""

    challenge_id = f"{config.resource}:{config.network}:{config.asset}:{config.amount}:{config.pay_to.lower()}"
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
        "unitEconomics": build_unit_economics(config),
        "verifierMode": config.verifier_mode,
        "humanApprovalRequired": config.human_approval_required,
        "mainnetEnabled": config.mainnet_enabled,
        "transactionBroadcast": False,
        "instructions": "Approve locally only, then send X-Payment: local-demo:<challenge-id>:<amount>.",
    }


def build_mcp_manifest(config: PaymentConfig) -> dict[str, object]:
    """Return a machine-readable paid-agent manifest for local MCP-style discovery."""

    return {
        "name": "arc-local-x402-paid-agent",
        "version": "0.1.0",
        "description": "Local-only Arc Testnet x402-style paid agent boundary for builders.",
        "network": {
            "name": "Arc Testnet",
            "chainId": 5_042_002,
            "chainIdHex": "0x4cef52",
            "rpc": "https://rpc.testnet.arc.network",
            "explorer": "https://testnet.arcscan.app",
        },
        "payment": {
            "network": config.network,
            "asset": config.asset,
            "assetDecimals": 6,
            "amount": config.amount,
            "payTo": config.pay_to,
            "resource": config.resource,
        },
        "unitEconomics": build_unit_economics(config),
        "safety": {
            "testnetOnly": True,
            "humanApprovalRequired": config.human_approval_required,
            "localDemoProofOnly": True,
            "mainnetEnabled": config.mainnet_enabled,
            "transactionBroadcast": False,
            "privateKeysAccepted": False,
            "autonomousSpending": False,
        },
        "productionReplacementBoundary": (
            "Replace LocalDemoVerifier with Circle Gateway/x402 verification only after "
            "network, asset, pay-to ownership, expiry, replay protection, logging, "
            "and settlement finality rules are reviewed."
        ),
        "builderContext": {
            "verifiedFacts": [
                "Arc Testnet chain ID is 5042002 / 0x4cef52.",
                "ERC-20 USDC amounts use 6 decimal places.",
            ],
            "repoChoices": [
                "This demo uses deterministic local proof strings instead of live settlement.",
                "The HTTP server binds to localhost by default.",
            ],
            "assumptionsAndUnknowns": [
                "A production verifier, nonce store, and wallet approval path are not implemented here.",
            ],
            "nonGoals": [
                "No wallet signing.",
                "No transaction broadcast.",
                "No mainnet payment processing.",
            ],
        },
        "tools": [
            {
                "name": "inspect_payment_challenge",
                "description": "Return the current local x402-style challenge without requiring a proof.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "get_paid_resource",
                "description": "Return the protected local report when X-Payment carries the accepted demo proof.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"xPayment": {"type": "string"}},
                    "required": ["xPayment"],
                    "additionalProperties": False,
                },
            },
        ],
    }


def payment_required_response(config: PaymentConfig, error: str = "payment_required") -> Response:
    challenge = build_payment_challenge(config)
    return Response(
        status=HTTPStatus.PAYMENT_REQUIRED,
        body={
            "error": error,
            **challenge,
            "mcpManifest": build_mcp_manifest(config),
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
    try:
        proof = extract_payment_proof(headers)
    except ValueError as error:
        return Response(
            status=HTTPStatus.PAYMENT_REQUIRED,
            body={
                "error": "invalid_x_payment",
                "reason": str(error),
                "settled": False,
                "transactionBroadcast": False,
            },
        )
    if not proof:
        return payment_required_response(config)

    challenge = build_payment_challenge(config)
    try:
        verification = verifier.verify(proof, challenge, config)
    except Exception:
        return Response(
            status=HTTPStatus.PAYMENT_REQUIRED,
            body={
                "error": "payment_verifier_unavailable",
                "settled": False,
                "transactionBroadcast": False,
                "challenge": challenge,
            },
        )
    if not isinstance(verification, VerificationResult):
        return Response(
            status=HTTPStatus.PAYMENT_REQUIRED,
            body={
                "error": "invalid_verifier_result",
                "settled": False,
                "transactionBroadcast": False,
                "challenge": challenge,
            },
        )
    if not verification.ok:
        return Response(
            status=HTTPStatus.PAYMENT_REQUIRED,
            body={
                "error": "payment_verification_failed",
                "reason": "proof_not_accepted",
                "settled": False,
                "transactionBroadcast": False,
                "challenge": challenge,
            },
        )
    if (
        verification.receipt.get("settled") is not False
        or verification.receipt.get("transactionBroadcast") is not False
    ):
        return Response(
            status=HTTPStatus.PAYMENT_REQUIRED,
            body={
                "error": "unsafe_verifier_result",
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
            "unitEconomics": build_unit_economics(config),
            "mcpManifest": build_mcp_manifest(config),
        },
    )


def make_jsonrpc_result(request_id: object, result: dict[str, object]) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def make_jsonrpc_error(request_id: object, code: int, message: str) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key is not allowed: {key}")
        result[key] = value
    return result


def bounded_mcp_lines() -> Iterator[bytes | None]:
    """Yield bounded stdin lines and use None for rejected oversized input."""

    stream = sys.stdin.buffer
    while True:
        payload = stream.readline(MAX_MCP_LINE_BYTES + 1)
        if not payload:
            return
        if len(payload) > MAX_MCP_LINE_BYTES:
            while payload and not payload.endswith(b"\n"):
                payload = stream.readline(MAX_MCP_LINE_BYTES + 1)
            yield None
            continue
        yield payload


def call_manifest_tool(name: str, arguments: Mapping[str, object] | None = None, config: PaymentConfig | None = None) -> dict[str, object]:
    """Dispatch the local manifest tools without wallet/RPC side effects."""

    config = config or PaymentConfig.demo()
    arguments = arguments or {}
    if name == "inspect_payment_challenge":
        require_exact_keys(arguments, set(), "inspect_payment_challenge arguments")
        challenge = build_payment_challenge(config)
        structured = {
            "status": HTTPStatus.PAYMENT_REQUIRED,
            "challenge": challenge,
            "mcpManifest": build_mcp_manifest(config),
        }
        return {
            "content": [{"type": "text", "text": "Local 402 challenge for Arc Testnet USDC demo payment."}],
            "structuredContent": structured,
        }
    if name == "get_paid_resource":
        require_exact_keys(arguments, {"xPayment"}, "get_paid_resource arguments")
        x_payment = arguments.get("xPayment")
        if not isinstance(x_payment, str):
            raise ValueError("get_paid_resource xPayment must be a string")
        response = handle_protected_request({"X-Payment": x_payment}, config)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Local paid resource response status: {int(response.status)}. No funds moved.",
                }
            ],
            "structuredContent": {"status": int(response.status), "body": response.body},
        }
    raise ValueError(f"unknown tool: {name}")


def process_jsonrpc_request(message: Mapping[str, object], config: PaymentConfig | None = None) -> dict[str, object] | None:
    """Process one newline-delimited JSON-RPC/MCP-style request."""

    config = config or PaymentConfig.demo()
    has_id = "id" in message
    request_id = message.get("id") if has_id else None
    if message.get("jsonrpc") != "2.0":
        return make_jsonrpc_error(request_id, -32600, "request jsonrpc must be exactly 2.0")
    if has_id and (
        isinstance(request_id, bool)
        or not isinstance(request_id, (str, int, type(None)))
    ):
        return make_jsonrpc_error(None, -32600, "request id must be a string, integer, or null")
    method = message.get("method")
    if not isinstance(method, str):
        return make_jsonrpc_error(request_id, -32600, "request method must be a string")
    allowed_request_keys = {"jsonrpc", "method"} | ({"id"} if has_id else set())
    if "params" in message:
        allowed_request_keys.add("params")
    try:
        require_exact_keys(message, allowed_request_keys, "JSON-RPC request")
    except ValueError as error:
        return make_jsonrpc_error(request_id, -32600, str(error))
    if not has_id:
        return None
    manifest = build_mcp_manifest(config)

    if method == "initialize":
        return make_jsonrpc_result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": manifest["name"], "version": manifest["version"]},
                "capabilities": {"tools": {"listChanged": False}},
                "safety": manifest["safety"],
            },
        )

    if method == "tools/list":
        return make_jsonrpc_result(request_id, {"tools": manifest["tools"], "safety": manifest["safety"]})

    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, Mapping):
            return make_jsonrpc_error(request_id, -32602, "tools/call params must be an object")
        try:
            require_exact_keys(params, {"name", "arguments"}, "tools/call params")
        except ValueError as error:
            return make_jsonrpc_error(request_id, -32602, str(error))
        name = params.get("name")
        arguments = params.get("arguments")
        if not isinstance(name, str):
            return make_jsonrpc_error(request_id, -32602, "tools/call requires a string tool name")
        if not isinstance(arguments, Mapping):
            return make_jsonrpc_error(request_id, -32602, "tools/call arguments must be an object")
        try:
            return make_jsonrpc_result(request_id, call_manifest_tool(name, arguments, config))
        except ValueError as error:
            return make_jsonrpc_error(request_id, -32602, str(error))

    return make_jsonrpc_error(request_id, -32601, f"unknown method: {method}")


def run_mcp_stdio(config: PaymentConfig | None = None) -> None:
    """Run a tiny newline-delimited JSON-RPC loop over stdin/stdout."""

    config = config or PaymentConfig.demo()
    for payload in bounded_mcp_lines():
        if payload is None:
            response = make_jsonrpc_error(None, -32600, "request exceeds the 1 MB safety limit")
            print(json.dumps(response, sort_keys=True), flush=True)
            continue
        if not payload.strip():
            continue
        try:
            line = payload.decode("utf-8")
            message = json.loads(line, object_pairs_hook=reject_duplicate_json_keys)
            if not isinstance(message, Mapping):
                response = make_jsonrpc_error(None, -32600, "request must be a JSON object")
            else:
                response = process_jsonrpc_request(message, config)
        except UnicodeDecodeError:
            response = make_jsonrpc_error(None, -32700, "parse error: request must be UTF-8")
        except json.JSONDecodeError as error:
            response = make_jsonrpc_error(None, -32700, f"parse error: {error.msg}")
        except ValueError as error:
            response = make_jsonrpc_error(None, -32700, f"parse error: {error}")
        if response is None:
            continue
        print(json.dumps(response, sort_keys=True), flush=True)


class DemoHandler(BaseHTTPRequestHandler):
    config = PaymentConfig.demo()

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlsplit(self.path).path
        if path in ("/", "/health"):
            self._send(Response(status=HTTPStatus.OK, body={"ok": True, "service": "x402-local-challenge-server"}))
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


def build_cli_challenge_payload(config: PaymentConfig | None = None) -> dict[str, object]:
    config = config or PaymentConfig.demo()
    challenge = build_payment_challenge(config)
    return {
        "status": int(HTTPStatus.PAYMENT_REQUIRED),
        "challenge": challenge,
        "localDemoProof": f"local-demo:{challenge['id']}:{config.amount}",
        "mcpManifest": build_mcp_manifest(config),
        "safety": {
            "localDemoProofOnly": True,
            "transactionBroadcast": False,
            "privateKeysAccepted": False,
            "mainnetEnabled": config.mainnet_enabled,
        },
    }


def build_cli_verification_payload(proof: str, config: PaymentConfig | None = None) -> dict[str, object]:
    config = config or PaymentConfig.demo()
    response = handle_protected_request({"X-Payment": proof}, config)
    return {"status": int(response.status), "body": response.body}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local-only x402 challenge server demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8087)
    parser.add_argument(
        "--mcp-stdio",
        action="store_true",
        help="Run a newline-delimited JSON-RPC/MCP-style stdio tool server instead of HTTP.",
    )
    parser.add_argument(
        "--print-manifest",
        action="store_true",
        help="Print the safe MCP-style manifest JSON and exit.",
    )
    parser.add_argument(
        "--print-challenge",
        action="store_true",
        help="Print the local 402 challenge, demo proof hint, and manifest JSON and exit.",
    )
    parser.add_argument(
        "--verify-payment",
        metavar="X_PAYMENT",
        help="Verify one local-demo X-Payment value and print the simulated response JSON.",
    )
    args = parser.parse_args()
    try:
        config = PaymentConfig.from_env()
    except ValueError as error:
        raise SystemExit(f"Invalid x402 demo configuration: {error}") from error

    if args.print_manifest:
        print_json(build_mcp_manifest(config))
        return
    if args.print_challenge:
        print_json(build_cli_challenge_payload(config))
        return
    if args.verify_payment is not None:
        print_json(build_cli_verification_payload(args.verify_payment, config))
        return
    if args.mcp_stdio:
        run_mcp_stdio(config)
        return

    try:
        validate_bind_target(args.host, args.port)
    except ValueError as error:
        raise SystemExit(f"Invalid local server bind target: {error}") from error
    DemoHandler.config = config
    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    print(f"local x402 challenge server listening on http://{args.host}:{args.port}")
    print("GET /protected returns a 402 challenge. No funds move in this demo.")
    server.serve_forever()


if __name__ == "__main__":
    main()
