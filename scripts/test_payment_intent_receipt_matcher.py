#!/usr/bin/env python3
"""Smoke tests for the payment-intent receipt matcher static example."""

from __future__ import annotations

import hashlib
import base64
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "examples" / "payment-intent-receipt-matcher" / "index.html"
JS = ROOT / "examples" / "payment-intent-receipt-matcher" / "matcher.js"
HARNESS = ROOT / "scripts" / "payment_intent_receipt_matcher_behavior_harness.mjs"


def compute_sri_hash(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


def test_payment_intent_receipt_matcher_files_exist() -> None:
    assert HTML.exists(), f"Missing {HTML}"
    assert JS.exists(), f"Missing {JS}"
    assert HARNESS.exists(), f"Missing {HARNESS}"


def test_payment_intent_receipt_matcher_html_has_required_elements() -> None:
    content = HTML.read_text(encoding="utf-8")
    required = [
        '<title>Payment Intent Receipt Matcher',
        'id="payment-intent"',
        'id="transaction-hash"',
        'id="match-receipt"',
        'id="reset-matcher"',
        'id="status-pill"',
        'id="match-summary-list"',
        'id="transfer-log-list"',
        'id="match-json"',
        "Read-only Arc Testnet RPC",
        "No wallet connection",
        "No signing",
        "No transaction broadcast",
    ]
    for fragment in required:
        assert fragment in content, f"Missing fragment in HTML: {fragment}"


def test_payment_intent_receipt_matcher_script_tag_has_matching_sri() -> None:
    content = HTML.read_text(encoding="utf-8")
    match = re.search(
        r'<script[^>]*src="\.\/matcher\.js"[^>]*integrity="(sha384-[A-Za-z0-9+/=]+)"[^>]*>',
        content,
    )
    assert match, "matcher.js script tag is missing or lacks an integrity attribute"
    observed_integrity = match.group(1)
    expected_integrity = compute_sri_hash(JS)
    assert observed_integrity == expected_integrity, (
        f"SRI hash mismatch: expected {expected_integrity}, got {observed_integrity}. "
        "Run a SHA-384 hash over matcher.js and update the integrity attribute."
    )


def test_payment_intent_receipt_matcher_js_has_required_functions() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "function parseIntent",
        "function classifyMatch",
        "function runMatch",
        "function safetyBoundary",
        "ARC_MATCHER",
        "eth_chainId",
        "eth_getTransactionReceipt",
        "Transfer",
        "intentMatched",
        "settlementProven",
        "businessAcceptanceProven",
    ]
    for fragment in required:
        assert fragment in content, f"Missing fragment in JS: {fragment}"


def test_payment_intent_receipt_matcher_has_no_forbidden_patterns() -> None:
    content = JS.read_text(encoding="utf-8")
    forbidden = [
        "privateKey",
        "private_key",
        "seedPhrase",
        "mnemonic",
        "sendTransaction",
        "eth_sendTransaction",
        "eth_sign",
        "personal_sign",
        "walletConnected: true",
        "transactionBroadcast: true",
        "signingEnabled: true",
        "autonomousSpending: true",
    ]
    for fragment in forbidden:
        assert fragment not in content, f"Forbidden pattern in matcher JS: {fragment}"


def test_payment_intent_receipt_matcher_harness_runs() -> None:
    result = subprocess.run(
        ["node", str(HARNESS)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Behavior harness failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "passed" in result.stdout.lower(), result.stdout


def main() -> int:
    tests = [
        test_payment_intent_receipt_matcher_files_exist,
        test_payment_intent_receipt_matcher_html_has_required_elements,
        test_payment_intent_receipt_matcher_script_tag_has_matching_sri,
        test_payment_intent_receipt_matcher_js_has_required_functions,
        test_payment_intent_receipt_matcher_has_no_forbidden_patterns,
        test_payment_intent_receipt_matcher_harness_runs,
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as error:
            print(f"FAIL: {test.__name__}: {error}")
            failures += 1
    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nAll payment-intent receipt matcher tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
