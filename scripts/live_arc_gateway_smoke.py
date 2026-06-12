#!/usr/bin/env python3
"""Safe live-smoke checks for a deployed Arc/x402 paid-agent endpoint.

This script validates the HTTP boundary only. It never creates payments, signs
wallet messages, stores credentials, or broadcasts transactions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Any

MAX_RESPONSE_BYTES = 1_000_000


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Return redirect responses to the caller instead of forwarding proofs."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise urllib.error.HTTPError(
            req.full_url,
            code,
            "redirects are disabled for live smoke requests",
            headers,
            fp,
        )


NO_REDIRECT_OPENER = urllib.request.build_opener(NoRedirectHandler())


@dataclass(frozen=True)
class SmokeConfig:
    target_url: str
    x_payment: str | None
    expect_402_only: bool
    timeout_seconds: float


def redact(value: str | None) -> str:
    if not value:
        return "[REDACTED:empty]"
    if len(value) <= 8:
        return "[REDACTED]"
    return f"{value[:4]}...[REDACTED]...{value[-4:]}"


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-check an Arc/x402 paid-agent endpoint without creating payments.",
    )
    parser.add_argument(
        "--expect-402-only",
        action="store_true",
        help="Stop after validating the unpaid 402 challenge when no live X-Payment proof is configured.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="HTTP timeout per request.",
    )
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> SmokeConfig:
    target_url = os.environ.get("ARC_PAID_AGENT_URL", "").strip()
    if not target_url:
        raise SystemExit(
            "Missing ARC_PAID_AGENT_URL. Set it to the deployed protected endpoint URL. "
            "No payments were created; this smoke script only performs HTTP checks."
        )
    return SmokeConfig(
        target_url=target_url,
        x_payment=os.environ.get("ARC_LIVE_X_PAYMENT", "").strip() or None,
        expect_402_only=args.expect_402_only or env_flag("EXPECT_402_ONLY"),
        timeout_seconds=args.timeout_seconds,
    )


def validate_smoke_config(config: SmokeConfig) -> None:
    """Reject malformed targets and unsafe proof transmission settings."""
    parsed = urlparse(config.target_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit("ARC_PAID_AGENT_URL must be a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise SystemExit("ARC_PAID_AGENT_URL must not contain embedded credentials.")
    if not 0 < config.timeout_seconds <= 60:
        raise SystemExit("--timeout-seconds must be greater than 0 and at most 60.")
    if config.x_payment and parsed.scheme != "https":
        raise SystemExit(
            "Refusing to send ARC_LIVE_X_PAYMENT to a non-HTTPS or malformed ARC_PAID_AGENT_URL. "
            "Run without ARC_LIVE_X_PAYMENT and --expect-402-only for local challenge checks."
        )


def decode_json_object(response: Any) -> dict[str, Any]:
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("HTTP response exceeds the 1 MB safety limit")
    value = json.loads(body.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("HTTP response must be a JSON object")
    return value


def http_json(url: str, timeout: float, x_payment: str | None = None) -> tuple[int, dict[str, Any]]:
    headers = {"Accept": "application/json"}
    if x_payment:
        headers["X-Payment"] = x_payment
    request = urllib.request.Request(url, headers=headers)
    try:
        with NO_REDIRECT_OPENER.open(request, timeout=timeout) as response:
            return response.status, decode_json_object(response)
    except urllib.error.HTTPError as error:
        try:
            try:
                payload = decode_json_object(error)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                payload = {"error": "non_json_or_oversized_http_error_body"}
            return error.code, payload
        finally:
            error.close()


def validate_402(status: int, payload: dict[str, Any]) -> None:
    if status != 402:
        raise SystemExit(f"Expected unpaid request to return HTTP 402, got {status}.")
    accepts = payload.get("accepts")
    manifest = payload.get("mcpManifest")
    if not isinstance(accepts, list) or not accepts:
        raise SystemExit("402 challenge is missing a non-empty accepts array.")
    if not isinstance(manifest, dict):
        raise SystemExit("402 challenge is missing mcpManifest.")
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        raise SystemExit("mcpManifest is missing safety flags.")
    if safety.get("transactionBroadcast") is not False:
        raise SystemExit("mcpManifest safety.transactionBroadcast must be false for this smoke gate.")
    if safety.get("humanApprovalRequired") is not True:
        raise SystemExit("mcpManifest safety.humanApprovalRequired must be true for this smoke gate.")
    first = accepts[0]
    if not isinstance(first, dict) or first.get("network") != "arc-testnet":
        raise SystemExit("402 challenge must declare Arc Testnet payment terms.")
    if first.get("asset") != "USDC":
        raise SystemExit("402 challenge must declare the pinned USDC asset.")
    if payload.get("mainnetEnabled") is not False:
        raise SystemExit("402 challenge mainnetEnabled must be false for this smoke gate.")


def validate_200(status: int, payload: dict[str, Any]) -> None:
    if status != 200:
        raise SystemExit(f"Expected paid retry to return HTTP 200, got {status}.")
    receipt = payload.get("receipt")
    if not isinstance(receipt, dict):
        raise SystemExit("Paid response is missing receipt.")
    if receipt.get("accepted") is not True:
        raise SystemExit("Paid response receipt.accepted must be true.")
    if receipt.get("transactionBroadcast") is not False:
        raise SystemExit("Paid response receipt.transactionBroadcast must remain false in this smoke gate.")


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args)
        validate_smoke_config(config)
        status, payload = http_json(config.target_url, config.timeout_seconds)
        validate_402(status, payload)
        print(
            "unpaid 402 challenge accepted: "
            f"network={payload['accepts'][0].get('network')} "
            "transactionBroadcast=false"
        )

        if not config.x_payment:
            if config.expect_402_only:
                print("stopped after 402-only check; no ARC_LIVE_X_PAYMENT was supplied")
                return 0
            raise SystemExit(
                "ARC_LIVE_X_PAYMENT is not set. Re-run with --expect-402-only for a challenge-only gate, "
                "or provide an externally created X-Payment proof. No payments were created."
            )

        paid_status, paid_payload = http_json(config.target_url, config.timeout_seconds, config.x_payment)
        validate_200(paid_status, paid_payload)
        print(
            "paid retry accepted: receipt.accepted=true "
            f"xPayment={redact(config.x_payment)} transactionBroadcast=false"
        )
        return 0
    except SystemExit as error:
        message = str(error)
        if message:
            print(message, file=sys.stderr)
        return 2
    except Exception as error:  # pragma: no cover - defensive CLI boundary
        print(f"smoke check failed safely: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
