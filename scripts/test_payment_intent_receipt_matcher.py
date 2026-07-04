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
        'id="download-json-evidence"',
        'id="download-markdown-evidence"',
        'disabled>Download JSON evidence',
        'disabled>Download Markdown evidence',
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
        "function buildEvidencePacket",
        "function generateMarkdownEvidence",
        "function downloadEvidenceFile",
        "function updateExportButtons",
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
        "eth_sendRawTransaction",
        "eth_sign",
        "personal_sign",
        "walletConnected: true",
        "transactionBroadcast: true",
        "signingEnabled: true",
        "autonomousSpending: true",
        "localStorage",
        "sessionStorage",
        "window.ethereum",
        "ethereum.request",
    ]
    for fragment in forbidden:
        assert fragment not in content, f"Forbidden pattern in matcher JS: {fragment}"


def test_payment_intent_receipt_matcher_js_pins_arc_testnet_chain() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "chainId !== ARC_MATCHER.expectedChainId",
        "network !== 'Arc Testnet'",
        "'arc-testnet'",
    ]
    for fragment in required:
        assert fragment in content, f"Missing Arc Testnet chain pinning marker: {fragment}"


def test_payment_intent_receipt_matcher_js_pins_usdc_token() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "token !== ARC_MATCHER.usdcAddress.toLowerCase()",
        "asset !== 'USDC'",
    ]
    for fragment in required:
        assert fragment in content, f"Missing pinned USDC token marker: {fragment}"


def test_payment_intent_receipt_matcher_js_enforces_six_decimals() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "usdcDecimals: 6",
        "decimals !== ARC_MATCHER.usdcDecimals",
        "ARC_MATCHER.usdcDecimals",
    ]
    for fragment in required:
        assert fragment in content, f"Missing six-decimal enforcement marker: {fragment}"


def test_payment_intent_receipt_matcher_js_rejects_amount_precision_errors() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "fractionPart.length > ARC_MATCHER.usdcDecimals",
        "positive decimal with at most 6 fractional digits",
        "amountBaseUnits must be a positive base-10 integer string",
    ]
    for fragment in required:
        assert fragment in content, f"Missing amount precision rejection marker: {fragment}"


def test_payment_intent_receipt_matcher_js_rejects_zero_address() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "ZERO_ADDRESS",
        "isNonZeroAddress",
        "recipient must include a valid non-zero 20-byte recipient address",
    ]
    for fragment in required:
        assert fragment in content, f"Missing zero-address rejection marker: {fragment}"


def test_payment_intent_receipt_matcher_js_rejects_mismatched_amount_fields() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "amount and amountBaseUnits do not match",
        "decimalBaseUnits !== amountBaseUnits",
    ]
    for fragment in required:
        assert fragment in content, f"Missing amount/baseUnits mismatch marker: {fragment}"


def test_payment_intent_receipt_matcher_js_rejects_recipient_equal_to_usdc_contract() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "recipient must not be the USDC token contract",
        "recipient === ARC_MATCHER.usdcAddress.toLowerCase()",
    ]
    for fragment in required:
        assert fragment in content, f"Missing recipient-equals-USDC rejection marker: {fragment}"


def test_payment_intent_receipt_matcher_js_export_uses_local_blob_only() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "new Blob",
        "URL.createObjectURL",
        "anchor.download",
        "URL.revokeObjectURL",
    ]
    for fragment in required:
        assert fragment in content, f"Missing local-download marker: {fragment}"
    forbidden = [
        "fetch('/upload",
        "fetch(\"http",
        "XMLHttpRequest",
        "navigator.sendBeacon",
        "localStorage",
        "sessionStorage",
    ]
    for fragment in forbidden:
        assert fragment not in content, f"Forbidden upload/storage pattern in export: {fragment}"


def test_payment_intent_receipt_matcher_js_export_disclaimer_rejects_settlement_custody_mainnet() -> None:
    content = JS.read_text(encoding="utf-8")
    required = [
        "not a proof of settlement",
        "custody",
        "mainnet readiness",
        "EVIDENCE_DISCLAIMER",
    ]
    for fragment in required:
        assert fragment in content, f"Missing export disclaimer marker: {fragment}"


def test_payment_intent_receipt_matcher_html_export_buttons_disabled_before_match() -> None:
    content = HTML.read_text(encoding="utf-8")
    assert 'id="download-json-evidence"' in content
    assert 'id="download-markdown-evidence"' in content
    assert 'disabled>Download JSON evidence</button>' in content
    assert 'disabled>Download Markdown evidence</button>' in content


def test_payment_intent_receipt_matcher_harness_tests_invalid_intent_cases() -> None:
    harness = HARNESS.read_text(encoding="utf-8")
    required = [
        "testInvalidLocalIntentAvoidsRpc",
        "wrong chainId",
        "wrong network",
        "wrong asset",
        "non-USDC token",
        "wrong decimals",
        "zero recipient",
        "recipient is USDC contract",
        "too many fractional digits",
        "zero amount",
        "negative amount",
        "hex amountBaseUnits",
        "mismatched amount/baseUnits",
        "testMalformedReceiptLogs",
        "testWrongTokenAddressAndTopic",
        "testDuplicateMatchingLogs",
        "testAmountFormattingEdgeCases",
        "testZeroAddressHandling",
        "testExportButtonsDisabledBeforeMatch",
        "testJsonExportContainsCanonicalFieldsAndVerdict",
        "testMismatchExportDoesNotClaimSettlement",
        "testRevertExportDoesNotClaimSettlement",
        "testNotFoundExportDoesNotClaimSettlement",
    ]
    for fragment in required:
        assert fragment in harness, f"Missing behavior harness invalid-intent case: {fragment}"


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
        test_payment_intent_receipt_matcher_js_pins_arc_testnet_chain,
        test_payment_intent_receipt_matcher_js_pins_usdc_token,
        test_payment_intent_receipt_matcher_js_enforces_six_decimals,
        test_payment_intent_receipt_matcher_js_rejects_amount_precision_errors,
        test_payment_intent_receipt_matcher_js_rejects_zero_address,
        test_payment_intent_receipt_matcher_js_rejects_mismatched_amount_fields,
        test_payment_intent_receipt_matcher_js_rejects_recipient_equal_to_usdc_contract,
        test_payment_intent_receipt_matcher_js_export_uses_local_blob_only,
        test_payment_intent_receipt_matcher_js_export_disclaimer_rejects_settlement_custody_mainnet,
        test_payment_intent_receipt_matcher_html_export_buttons_disabled_before_match,
        test_payment_intent_receipt_matcher_harness_tests_invalid_intent_cases,
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
