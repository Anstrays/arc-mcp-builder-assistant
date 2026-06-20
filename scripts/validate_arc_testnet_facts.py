#!/usr/bin/env python3
"""Validate the canonical offline Arc Testnet facts contract and its consumers.

In addition to checking the pinned targets for exact canonical markers, this
script scans README, docs, examples, scripts, and index.html for dangerous
Arc Testnet fact drift (wrong chain IDs, RPC/explorer URLs, and swapped
ERC-20/native gas decimals) and fails closed unless the dangerous value sits in
an explicit "do not use / forbidden" phrase on the same line.
"""

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

# Values that must not appear in repository surfaces unless inside an explicit
# negative-test fixture or a documented "do not use / forbidden" context.
DANGEROUS_VALUES: dict[str, list[str]] = {
    "network.chainId": ["1244", "1"],
    "network.chainIdHex": ["0x4d4", "0x1"],
    "network.rpcUrl": [
        "https://rpc.arc.network",
        "https://rpc.mainnet.arc.network",
        "https://mainnet.arc.network",
    ],
    "network.explorerUrl": [
        "https://arcscan.io",
        "https://explorer.arc.network",
        "https://mainnet.arcscan.app",
    ],
}

# Explicit negative phrases that allow a dangerous value to appear on the same
# line. The value must be paired with one of these phrases directly in the
# matched line; a nearby safe word in an unrelated sentence must not suppress
# the failure.
SAFE_CONTEXT_MARKERS = (
    "do not use",
    "do not",
    "must not",
    "must never",
    "forbidden",
    "not allowed",
    "not supported",
    "not valid",
    "do not configure",
    "do not set",
)

# Explicit fixture/test markers. A dangerous value may appear inside a test
# fixture or negative example if the line itself identifies it as such.
FIXTURE_CONTEXT_MARKERS = (
    "fixture",
    "negative test",
    "negative example",
    "invalid example",
    "rejected value",
)

# File patterns scanned for dangerous value drift. Keep dependency-free.
SCAN_GLOBS = (
    "README.md",
    "docs/**/*.md",
    "examples/**/*.js",
    "examples/**/*.html",
    "examples/**/*.json",
    "scripts/**/*.py",
    "scripts/**/*.mjs",
    "scripts/**/*.js",
    "index.html",
)

SCAN_EXCLUDES = (
    "config/arc_testnet.facts.json",
    "scripts/validate_arc_testnet_facts.py",
    "scripts/test_arc_testnet_facts.py",
)


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


def _collect_scan_files(root: Path = ROOT) -> list[Path]:
    files: set[Path] = set()
    for pattern in SCAN_GLOBS:
        for path in root.glob(pattern):
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                if relative not in SCAN_EXCLUDES:
                    files.add(path)
    return sorted(files)


def _context_allows_dangerous(
    line: str, fact_name: str | None = None, dangerous: str | None = None
) -> bool:
    """Return True only if the matched line itself negates the dangerous value.

    When fact_name and dangerous are supplied, the negation must be explicitly
    tied to that specific value on the same line. Generic "do not", "fixture",
    "negative" or "wrong" text in an unrelated clause is not sufficient.
    """
    lower = line.lower()

    # The only broad exception: the specific inline comment used to mark
    # negative test fixtures in behavior harness files.
    if "do not use: negative test fixture" in lower:
        # When a value is supplied, the fixture comment must be on the same line
        # as the dangerous value it annotates.
        if dangerous is not None and dangerous in line:
            return True
        # Decimal-confusion path calls without a value; keep the marker valid.
        return fact_name is None and dangerous is None

    if fact_name is None or dangerous is None:
        # Decimal-confusion path: keep broad same-line markers.
        return any(marker in lower for marker in SAFE_CONTEXT_MARKERS) or any(
            marker in lower for marker in FIXTURE_CONTEXT_MARKERS
        )

    # Strip URL scheme for prose matching ("rpc.arc.network" in "https://...").
    display_value = dangerous
    if display_value.startswith(("http://", "https://")):
        display_value = display_value.split("://", 1)[1]

    value_re = re.escape(display_value)

    # Build an optional chain-id key phrase prefix for chainId facts.
    if "chainid" in fact_name.lower():
        key_prefix = r"(?:chainidhex|chainid|chain\s+id\s+hex|chain-id-hex|chain\s+id|chain-id)\s*[:=\s]*"
        negation_patterns = [
            # "Do not use chainId 1", "Must never configure chain-id = 1244"
            rf"(?:do\s+not|must\s+not|must\s+never)\s+(?:use|configure|set)\s+{key_prefix}['\"`]?{value_re}['\"`]?",
            # "chainId: 1 is forbidden", "Chain ID 1244 is not allowed"
            rf"{key_prefix}['\"`]?{value_re}['\"`]?\s+is\s+forbidden",
            rf"{key_prefix}['\"`]?{value_re}['\"`]?\s+is\s+not\s+(?:allowed|supported|valid)",
        ]
    else:
        negation_patterns = [
            # "Do not configure https://rpc.arc.network"
            rf"(?:do\s+not|must\s+not|must\s+never)\s+(?:use|configure|set)\s+(?:https?://)?['\"`]?{value_re}['\"`]?",
            # "https://rpc.arc.network is forbidden"
            rf"(?:https?://)?['\"`]?{value_re}['\"`]?\s+is\s+forbidden",
            rf"(?:https?://)?['\"`]?{value_re}['\"`]?\s+is\s+not\s+(?:allowed|supported|valid)",
        ]

    return any(re.search(pattern, lower) for pattern in negation_patterns)


# Chain-id key phrases we treat as equivalent (case-insensitive).
_CHAIN_ID_KEY_PATTERN = (
    r"chainidhex|chainid|chain\s+id\s+hex|chain-id-hex|chain\s+id|chain-id"
)


def _dangerous_value_matches(line: str, fact_name: str, dangerous: str) -> bool:
    """Return True if this line contains the dangerous value in a chainId context.

    This is intentionally strict: a bare "1" in a numbered list, a transaction
    receipt status "0x1", or the correct Arc Testnet values must not be flagged.
    """
    if dangerous.startswith("http://") or dangerous.startswith("https://"):
        return dangerous in line

    # Hex values: reject transaction/status/log contexts first.
    if dangerous.startswith("0x"):
        if re.search(r"\bstatus\b|\breceipt\b|\bsuccess\b|\bfailed\b|\blog\b", line, re.IGNORECASE):
            return False

    # Match chain-id key phrase, optional separator (:, =, or prose "is"),
    # optional quotes/backticks, then the dangerous value.
    quote_group = r"([\"'\`])"
    if dangerous.startswith("0x"):
        tail = r"(?![0-9A-Fa-f])"
    else:
        tail = r"(?![0-9])"

    # Explicit separator / prose "is" form (chainId: 1244, chain id is 1244).
    explicit_pattern = (
        rf"(?i)\b({_CHAIN_ID_KEY_PATTERN})\s*(?:[:=]|\bis\b)\s*"
        rf"{quote_group}?{re.escape(dangerous)}{quote_group}?{tail}"
    )
    if re.search(explicit_pattern, line):
        return True

    # Whitespace-only form, e.g. "Do not use chainId 1244" or "Chain ID `0x4d4`".
    whitespace_pattern = (
        rf"(?i)\b({_CHAIN_ID_KEY_PATTERN})\s+{quote_group}?{re.escape(dangerous)}{quote_group}?{tail}"
    )
    return re.search(whitespace_pattern, line) is not None


def scan_for_dangerous_values(facts: dict[str, Any], root: Path = ROOT) -> int:
    """Fail closed if a dangerous value appears without an explicit safe context."""
    files = _collect_scan_files(root)
    issues: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = text.splitlines()
        for fact_name, dangerous_values in DANGEROUS_VALUES.items():
            for dangerous in dangerous_values:
                for i, line in enumerate(lines):
                    if not _dangerous_value_matches(line, fact_name, dangerous):
                        continue
                    if _context_allows_dangerous(line, fact_name, dangerous):
                        continue
                    issues.append(
                        f"{path.relative_to(root).as_posix()}:{i + 1}: "
                        f"dangerous value for {fact_name} ({dangerous!r}) "
                        f"appears without an explicit negation on the same line"
                    )
    if issues:
        fail("\n".join(["detected dangerous Arc Testnet fact drift:"] + issues))
    return len(files)


def scan_for_decimal_confusion(root: Path = ROOT) -> int:
    """Fail closed if ERC-20 USDC and native gas decimals are swapped.

    Splits each line into clauses so a single sentence that correctly mentions
    both native gas (18) and ERC-20 USDC (6) is not misread as drift.
    """
    files = _collect_scan_files(root)
    issues: list[str] = []
    clause_delimiters = re.compile(r"[,;()—–]|\band\b|\bwhile\b|\bbut\b")
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if _context_allows_dangerous(line):
                continue
            lower = line.lower()
            for clause in clause_delimiters.split(lower):
                if "usdc" in clause and "decimals" in clause and re.search(r"(?<![0-9])18(?![0-9])", clause):
                    # Only flag USDC decimals = 18 in an ERC-20 context.
                    if "erc" in clause or "erc-20" in clause or "erc20" in clause:
                        issues.append(
                            f"{path.relative_to(root).as_posix()}:{i + 1}: "
                            f"ERC-20 USDC decimals appears to be 18 (expected 6)"
                        )
                if ("native" in clause or "gas" in clause) and "decimals" in clause and re.search(r"(?<![0-9])6(?![0-9])", clause):
                    # Do not flag if the clause is actually about ERC-20 USDC.
                    if "erc" in clause or "erc-20" in clause or "erc20" in clause:
                        continue
                    issues.append(
                        f"{path.relative_to(root).as_posix()}:{i + 1}: "
                        f"native gas decimals appears to be 6 (expected 18)"
                    )
    if issues:
        fail("\n".join(["detected Arc Testnet decimal confusion:"] + issues))
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        facts = load_facts(args.facts)
        validate_facts(facts)
        target_count = validate_targets(facts, args.root)
        scanned_count = scan_for_dangerous_values(facts, args.root)
        scan_for_decimal_confusion(args.root)
    except ValueError as error:
        raise SystemExit(f"Arc Testnet facts invalid: {error}") from error
    print(
        f"Arc Testnet facts valid: {len(FACT_TARGETS)} facts across {target_count} "
        f"pinned targets and {scanned_count} scanned files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
