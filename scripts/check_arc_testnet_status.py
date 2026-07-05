#!/usr/bin/env python3
"""Read-only Arc Testnet RPC status check.

This script is intentionally dependency-free and secret-free. It performs only
read-only JSON-RPC calls so builders can verify that the configured Arc Testnet
RPC endpoint reports the expected chain ID before any wallet or transaction work
is added to the project.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from urllib.parse import urlparse
from typing import Any

EXPECTED_CHAIN_ID_DECIMAL = 5042002
EXPECTED_CHAIN_ID_HEX = hex(EXPECTED_CHAIN_ID_DECIMAL)
DEFAULT_RPC_URL = "https://rpc.testnet.arc.network"
DEFAULT_EXPLORER_URL = "https://testnet.arcscan.app"
MAX_RESPONSE_BYTES = 1_000_000


def validate_endpoint(url: str, name: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be a valid HTTP or HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError(f"{name} must not contain embedded credentials")


def validate_timeout(timeout: int) -> None:
    if not 1 <= timeout <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")


def decode_json_object(response: Any) -> dict[str, Any]:
    payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise RuntimeError("RPC response exceeds the 1 MB safety limit")
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("RPC response must be a JSON object")
    return value


def rpc_call(rpc_url: str, method: str, params: list[Any] | None = None, timeout: int = 10) -> Any:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = decode_json_object(response)
    if "error" in body:
        raise RuntimeError(f"{method} failed: {body['error']}")
    return body.get("result")


def parse_hex_quantity(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"expected hex quantity, got {value!r}")
    return int(value, 16)


def build_status(rpc_url: str, explorer_url: str, timeout: int) -> dict[str, Any]:
    chain_id_hex = rpc_call(rpc_url, "eth_chainId", timeout=timeout)
    block_number_hex = rpc_call(rpc_url, "eth_blockNumber", timeout=timeout)
    chain_id_decimal = parse_hex_quantity(chain_id_hex)
    block_number_decimal = parse_hex_quantity(block_number_hex)
    expected = chain_id_decimal == EXPECTED_CHAIN_ID_DECIMAL
    return {
        "network": "Arc Testnet",
        "rpcUrl": rpc_url,
        "explorerUrl": explorer_url,
        "chainIdHex": chain_id_hex,
        "chainIdDecimal": chain_id_decimal,
        "expectedChainIdHex": EXPECTED_CHAIN_ID_HEX,
        "expectedChainIdDecimal": EXPECTED_CHAIN_ID_DECIMAL,
        "chainIdMatches": expected,
        "latestBlockHex": block_number_hex,
        "latestBlockDecimal": block_number_decimal,
        "nativeGasAsset": "USDC",
        "nativeGasDecimals": 18,
        "erc20UsdcAddress": "0x3600000000000000000000000000000000000000",
        "erc20UsdcDecimals": 6,
        "rpcChainIdMatchesArcTestnet": expected,
        "signingRequiresWalletChainGateAndHumanApproval": True,
        "note": "Read-only status check. This script does not connect wallets, approve signing, or submit transactions.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check read-only Arc Testnet RPC status.")
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL, help="Arc Testnet JSON-RPC URL")
    parser.add_argument("--explorer-url", default=DEFAULT_EXPLORER_URL, help="ArcScan explorer base URL")
    parser.add_argument("--timeout", type=int, default=10, help="RPC timeout in seconds")
    args = parser.parse_args()

    try:
        validate_endpoint(args.rpc_url, "RPC URL")
        validate_endpoint(args.explorer_url, "explorer URL")
        validate_timeout(args.timeout)
        status = build_status(args.rpc_url, args.explorer_url, args.timeout)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    print(json.dumps({"ok": status["chainIdMatches"], "status": status}, indent=2, sort_keys=True))
    return 0 if status["chainIdMatches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
