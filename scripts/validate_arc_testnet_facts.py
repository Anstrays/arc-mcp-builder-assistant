#!/usr/bin/env python3
"""Validate the canonical offline Arc Testnet facts contract and its consumers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FACTS = ROOT / "config" / "arc_testnet.facts.json"
REVIEWED_BASELINE = {
    "network.chainId": 5042002,
    "network.chainIdHex": "0x4cef52",
    "network.rpcUrl": "https://rpc.testnet.arc.network",
    "network.explorerUrl": "https://testnet.arcscan.app",
    "nativeGas.decimals": 18,
    "erc20Usdc.address": "0x3600000000000000000000000000000000000000",
    "erc20Usdc.decimals": 6,
    "sources.connect": "https://docs.arc.io/arc/references/connect-to-arc",
    "sources.contracts": "https://docs.arc.io/arc/references/contract-addresses",
    "sources.deploymentModel": "https://docs.arc.io/arc/concepts/deployment-model",
}


def fail(message: str) -> None:
    raise ValueError(message)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key is not allowed: {key}")
        result[key] = value
    return result


def require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        fail(f"{label} must contain exactly {sorted(expected)!r}; got {sorted(actual)!r}")
    return value


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        fail(f"{label} must be {expected!r}; got {actual!r}")


def require_positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        fail(f"{label} must be a positive integer")
    return value


def require_https_url(value: Any, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be an HTTPS URL")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        fail(f"{label} must be an HTTPS URL without credentials, query, or fragment")
    return value


def load_facts(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not load facts contract: {error}")
    if not isinstance(value, dict):
        fail("facts contract root must be an object")
    return value


def validate_facts(facts: dict[str, Any]) -> None:
    require_exact_keys(
        facts,
        {"schemaVersion", "scope", "network", "nativeGas", "erc20Usdc", "policy", "sources"},
        "facts",
    )
    require_equal(facts.get("schemaVersion"), 1, "schemaVersion")
    require_equal(facts.get("scope"), "arc-testnet-facts", "scope")

    network = require_exact_keys(
        facts.get("network"),
        {"name", "chainId", "chainIdHex", "rpcUrl", "explorerUrl"},
        "network",
    )
    require_equal(network.get("name"), "Arc Testnet", "network.name")
    chain_id = require_positive_int(network.get("chainId"), "network.chainId")
    require_equal(network.get("chainIdHex"), hex(chain_id), "network.chainIdHex")
    require_https_url(network.get("rpcUrl"), "network.rpcUrl")
    require_https_url(network.get("explorerUrl"), "network.explorerUrl")

    native_gas = require_exact_keys(facts.get("nativeGas"), {"symbol", "decimals"}, "nativeGas")
    require_equal(native_gas.get("symbol"), "USDC", "nativeGas.symbol")
    require_positive_int(native_gas.get("decimals"), "nativeGas.decimals")

    erc20 = require_exact_keys(facts.get("erc20Usdc"), {"symbol", "address", "decimals"}, "erc20Usdc")
    require_equal(erc20.get("symbol"), "USDC", "erc20Usdc.symbol")
    address = erc20.get("address")
    if not isinstance(address, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
        fail("erc20Usdc.address must be a 20-byte EVM address")
    require_positive_int(erc20.get("decimals"), "erc20Usdc.decimals")

    policy = require_exact_keys(
        facts.get("policy"),
        {"mainnetSupported", "walletRequired", "networkChecksOptIn", "recheckBeforePublication"},
        "policy",
    )
    for key, expected in (
        ("mainnetSupported", False),
        ("walletRequired", False),
        ("networkChecksOptIn", True),
        ("recheckBeforePublication", True),
    ):
        require_equal(policy.get(key), expected, f"policy.{key}")

    sources = require_exact_keys(
        facts.get("sources"),
        {"connect", "contracts", "deploymentModel"},
        "sources",
    )
    for key, value in sources.items():
        require_https_url(value, f"sources.{key}")
        if urlparse(value).netloc != "docs.arc.io":
            fail(f"sources.{key} must use the official docs.arc.io host")

    reviewed_values = {
        "network.chainId": network["chainId"],
        "network.chainIdHex": network["chainIdHex"],
        "network.rpcUrl": network["rpcUrl"],
        "network.explorerUrl": network["explorerUrl"],
        "nativeGas.decimals": native_gas["decimals"],
        "erc20Usdc.address": erc20["address"],
        "erc20Usdc.decimals": erc20["decimals"],
        "sources.connect": sources["connect"],
        "sources.contracts": sources["contracts"],
        "sources.deploymentModel": sources["deploymentModel"],
    }
    for label, expected in REVIEWED_BASELINE.items():
        require_equal(reviewed_values[label], expected, f"reviewed baseline {label}")


MarkerFactory = Callable[[dict[str, Any]], str]


def marker(path: str, build: MarkerFactory) -> tuple[str, MarkerFactory]:
    return path, build


FACT_TARGETS: dict[str, tuple[tuple[str, MarkerFactory], ...]] = {
    "network.chainId": (
        marker("scripts/check_arc_testnet_status.py", lambda f: f"EXPECTED_CHAIN_ID_DECIMAL = {f['network']['chainId']}"),
        marker("scripts/arc_builder_doctor.py", lambda f: f"EXPECTED_CHAIN_ID_DECIMAL = {f['network']['chainId']}"),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"expectedChainIdDecimal: {f['network']['chainId']}"),
        marker("examples/transaction-status-playground/status.js", lambda f: f"expectedChainId: {f['network']['chainId']}"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"chainId: {f['network']['chainId']}"),
        marker("examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json", lambda f: f"\"chainId\": {f['network']['chainId']}"),
        marker("docs/arc-docs-map.md", lambda f: f"| Chain ID | `{f['network']['chainId']}` |"),
    ),
    "network.chainIdHex": (
        marker("scripts/arc_builder_doctor.py", lambda f: f"EXPECTED_CHAIN_ID_HEX = \"{f['network']['chainIdHex']}\""),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"expectedChainIdHex: '{f['network']['chainIdHex']}'"),
        marker("examples/transaction-status-playground/status.js", lambda f: f"expectedChainIdHex: '{f['network']['chainIdHex']}'"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"chainIdHex: '{f['network']['chainIdHex']}'"),
        marker("examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json", lambda f: f"\"chainIdHex\": \"{f['network']['chainIdHex']}\""),
    ),
    "network.rpcUrl": (
        marker("scripts/check_arc_testnet_status.py", lambda f: f"DEFAULT_RPC_URL = \"{f['network']['rpcUrl']}\""),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"rpcUrl: '{f['network']['rpcUrl']}'"),
        marker("examples/transaction-status-playground/status.js", lambda f: f"rpcUrl: '{f['network']['rpcUrl']}'"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"rpcUrl: '{f['network']['rpcUrl']}'"),
        marker("examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json", lambda f: f"\"rpcUrl\": \"{f['network']['rpcUrl']}\""),
        marker("docs/arc-docs-map.md", lambda f: f"| RPC URL | `{f['network']['rpcUrl']}` |"),
    ),
    "network.explorerUrl": (
        marker("scripts/check_arc_testnet_status.py", lambda f: f"DEFAULT_EXPLORER_URL = \"{f['network']['explorerUrl']}\""),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"explorerUrl: '{f['network']['explorerUrl']}'"),
        marker("examples/transaction-status-playground/status.js", lambda f: f"explorerUrl: '{f['network']['explorerUrl']}'"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"explorerUrl: '{f['network']['explorerUrl']}'"),
        marker("examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json", lambda f: f"\"explorerUrl\": \"{f['network']['explorerUrl']}\""),
        marker("docs/arc-docs-map.md", lambda f: f"| Explorer | `{f['network']['explorerUrl']}` |"),
    ),
    "nativeGas.decimals": (
        marker("scripts/check_arc_testnet_status.py", lambda f: f"\"nativeGasDecimals\": {f['nativeGas']['decimals']}"),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"nativeGasDecimals: {f['nativeGas']['decimals']}"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"nativeGasDecimals: {f['nativeGas']['decimals']}"),
        marker("docs/arc-docs-map.md", lambda f: f"Native gas accounting uses {f['nativeGas']['decimals']} decimals"),
    ),
    "erc20Usdc.address": (
        marker("scripts/check_arc_testnet_status.py", lambda f: f"\"erc20UsdcAddress\": \"{f['erc20Usdc']['address']}\""),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"erc20UsdcAddress: '{f['erc20Usdc']['address']}'"),
        marker("examples/transaction-status-playground/status.js", lambda f: f"usdcAddress: '{f['erc20Usdc']['address']}'"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"usdcAddress: '{f['erc20Usdc']['address']}'"),
        marker("examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json", lambda f: f"\"tokenAddress\": \"{f['erc20Usdc']['address']}\""),
        marker("docs/arc-docs-map.md", lambda f: f"| USDC | `{f['erc20Usdc']['address']}` |"),
    ),
    "erc20Usdc.decimals": (
        marker("scripts/check_arc_testnet_status.py", lambda f: f"\"erc20UsdcDecimals\": {f['erc20Usdc']['decimals']}"),
        marker("examples/payment-intent-playground/playground.js", lambda f: f"erc20UsdcDecimals: {f['erc20Usdc']['decimals']}"),
        marker("examples/transaction-status-playground/status.js", lambda f: f"usdcDecimals: {f['erc20Usdc']['decimals']}"),
        marker("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js", lambda f: f"usdcDecimals: {f['erc20Usdc']['decimals']}"),
        marker("examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json", lambda f: f"\"decimals\": {f['erc20Usdc']['decimals']}"),
        marker("docs/arc-docs-map.md", lambda f: f"optional ERC-20 USDC interface uses {f['erc20Usdc']['decimals']} decimals"),
    ),
}


def validate_targets(facts: dict[str, Any], root: Path = ROOT) -> int:
    checked = 0
    for fact_name, targets in FACT_TARGETS.items():
        for relative, build_marker in targets:
            path = root / relative
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as error:
                fail(f"{fact_name} target missing or unreadable: {relative}: {error}")
            expected = build_marker(facts)
            occurrences = text.count(expected)
            if occurrences != 1:
                fail(
                    f"{relative} must contain exactly one canonical {fact_name} marker; "
                    f"found {occurrences}"
                )
            checked += 1
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        facts = load_facts(args.facts)
        validate_facts(facts)
        target_count = validate_targets(facts, args.root)
    except ValueError as error:
        raise SystemExit(f"Arc Testnet facts invalid: {error}") from error
    print(f"Arc Testnet facts valid: {len(FACT_TARGETS)} facts across {target_count} pinned targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
