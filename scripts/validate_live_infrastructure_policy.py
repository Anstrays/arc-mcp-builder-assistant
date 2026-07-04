#!/usr/bin/env python3
"""Validate the fail-closed Arc live-infrastructure policy example."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = (
    ROOT
    / "examples"
    / "arc-testnet-wallet-send-gate"
    / "live-infrastructure-policy.example.json"
)


def fail(message: str) -> None:
    raise ValueError(message)


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        fail(f"{label} must be {expected!r}; got {actual!r}")


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        fail(f"{label} must contain exactly {sorted(expected)!r}; got {sorted(actual)!r}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key is not allowed: {key}")
        result[key] = value
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    require_exact_keys(
        policy,
        {"schemaVersion", "scope", "activeProfile", "profiles", "custody"},
        "policy",
    )
    require_equal(policy.get("schemaVersion"), 1, "schemaVersion")
    require_equal(policy.get("scope"), "arc-live-infrastructure-gates", "scope")
    require_equal(policy.get("activeProfile"), "arc-testnet-injected-wallet", "activeProfile")

    profiles = policy.get("profiles")
    if not isinstance(profiles, dict):
        fail("profiles must be an object")
    if set(profiles) != {"arcTestnet", "arcMainnet"}:
        fail("profiles must contain only arcTestnet and blocked arcMainnet")
    testnet = profiles.get("arcTestnet")
    blocked_network = profiles.get("arcMainnet")
    if not isinstance(testnet, dict) or not isinstance(blocked_network, dict):
        fail("profiles must contain arcTestnet and arcMainnet objects")
    require_exact_keys(
        testnet,
        {
            "enabled",
            "network",
            "chainId",
            "chainIdHex",
            "rpcUrl",
            "explorerUrl",
            "asset",
            "signing",
            "broadcast",
        },
        "profiles.arcTestnet",
    )
    require_exact_keys(
        blocked_network,
        {"enabled", "status", "chainId", "chainIdHex", "rpcUrl", "explorerUrl"},
        "profiles.arcMainnet",
    )

    for key, expected in (
        ("enabled", True),
        ("network", "Arc Testnet"),
        ("chainId", 5042002),
        ("chainIdHex", "0x4cef52"),
        ("rpcUrl", "https://rpc.testnet.arc.network"),
        ("explorerUrl", "https://testnet.arcscan.app"),
    ):
        require_equal(testnet.get(key), expected, f"profiles.arcTestnet.{key}")

    asset = testnet.get("asset")
    signing = testnet.get("signing")
    broadcast = testnet.get("broadcast")
    if not all(isinstance(value, dict) for value in (asset, signing, broadcast)):
        fail("testnet asset, signing, and broadcast policies must be objects")
    require_exact_keys(
        asset,
        {"symbol", "tokenAddress", "decimals", "maxBaseUnitsPerRequest"},
        "profiles.arcTestnet.asset",
    )
    require_exact_keys(
        signing,
        {"mode", "autonomous", "rawPrivateKeysAccepted"},
        "profiles.arcTestnet.signing",
    )
    require_exact_keys(
        broadcast,
        {
            "method",
            "transactionChainIdRequired",
            "explicitHumanApprovalRequired",
            "topLevelBrowsingContextRequired",
            "zeroAddressAllowed",
            "tokenContractRecipientAllowed",
            "maxAttemptsPerPageLoad",
            "automaticRetry",
        },
        "profiles.arcTestnet.broadcast",
    )
    for key, expected in (
        ("symbol", "USDC"),
        ("tokenAddress", "0x3600000000000000000000000000000000000000"),
        ("decimals", 6),
        ("maxBaseUnitsPerRequest", "1000000"),
    ):
        require_equal(asset.get(key), expected, f"profiles.arcTestnet.asset.{key}")
    for key, expected in (
        ("mode", "external_wallet_confirmation_only"),
        ("autonomous", False),
        ("rawPrivateKeysAccepted", False),
    ):
        require_equal(signing.get(key), expected, f"profiles.arcTestnet.signing.{key}")
    for key, expected in (
        ("method", "eth_sendTransaction"),
        ("transactionChainIdRequired", "0x4cef52"),
        ("explicitHumanApprovalRequired", True),
        ("topLevelBrowsingContextRequired", True),
        ("zeroAddressAllowed", False),
        ("tokenContractRecipientAllowed", False),
        ("maxAttemptsPerPageLoad", 1),
        ("automaticRetry", False),
    ):
        require_equal(broadcast.get(key), expected, f"profiles.arcTestnet.broadcast.{key}")

    require_equal(blocked_network.get("enabled"), False, "profiles.arcMainnet.enabled")
    require_equal(
        blocked_network.get("status"),
        "blocked_official_configuration_upcoming",
        "profiles.arcMainnet.status",
    )
    for key in ("chainId", "chainIdHex", "rpcUrl", "explorerUrl"):
        require_equal(blocked_network.get(key), None, f"profiles.arcMainnet.{key}")

    custody = policy.get("custody")
    if not isinstance(custody, dict):
        fail("custody must be an object")
    require_exact_keys(
        custody,
        {"implemented", "mode", "staticSiteMayHoldSecrets", "requiredBeforeEnable"},
        "custody",
    )
    for key, expected in (
        ("implemented", False),
        ("mode", "non-custodial"),
        ("staticSiteMayHoldSecrets", False),
    ):
        require_equal(custody.get(key), expected, f"custody.{key}")
    required = custody.get("requiredBeforeEnable")
    expected_custody_gates = {
        "owned_backend_or_reviewed_provider",
        "secret_manager_hsm_or_mpc",
        "chain_asset_method_and_address_allowlists",
        "per_transaction_and_cumulative_limits",
        "idempotency_replay_and_nonce_controls",
        "immutable_redacted_audit_logs",
        "kill_switch_and_incident_runbook",
        "separate_security_review",
    }
    if (
        not isinstance(required, list)
        or len(required) != len(expected_custody_gates)
        or set(required) != expected_custody_gates
    ):
        fail("custody.requiredBeforeEnable must contain the exact reviewed custody gates")


def load_policy(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not load policy: {error}")
    if not isinstance(payload, dict):
        fail("policy root must be an object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    try:
        validate_policy(load_policy(args.path))
    except ValueError as error:
        raise SystemExit(f"live infrastructure policy invalid: {error}") from error
    print("live infrastructure policy valid: Arc Testnet guarded, custody/mainnet blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
