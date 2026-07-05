#!/usr/bin/env python3
"""Regression checks for the local-only Arc receipt verifier playground."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/receipt-verifier-playground/index.html"
JS = ROOT / "examples/receipt-verifier-playground/verifier.js"
DOC = ROOT / "docs/receipt-verifier-playground.md"
README = ROOT / "README.md"
INDEX = ROOT / "index.html"
VIEWER = ROOT / "docs/viewer.js"
VALIDATOR = ROOT / "arc_builder_kit/validate_repo.py"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, source: Path) -> None:
    assert marker in text, f"missing marker in {source.relative_to(ROOT)}: {marker}"


def test_receipt_verifier_page_has_safe_review_ui() -> None:
    html = read(HTML)
    for marker in (
        "Receipt Verifier Playground",
        'id="receipt-json"',
        'id="verify-receipt"',
        'id="reset-receipt"',
        'id="verdict-pill"',
        'id="receipt-check-list"',
        'id="normalized-receipt"',
        "local-only receipt review",
        "No wallet connection",
        "No transaction broadcast",
        "No backend calls",
    ):
        assert_contains(html, marker, HTML)


def test_receipt_verifier_checks_arc_payment_receipt_fields() -> None:
    js = read(JS)
    for marker in (
        "const ARC_RECEIPT_EXPECTATIONS",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "asset: 'USDC'",
        "assetDecimals: 6",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "function normalizeReceipt(rawReceipt)",
        "function verifyReceipt(receipt)",
        "function isValidAddress(value)",
        "!/^0x0{40}$/.test(normalized)",
        "normalized !== '0x3600000000000000000000000000000000000000'",
        "const DEFAULT_RECEIPT_EXPIRY_MS = 24 * 60 * 60 * 1000",
        "expiry: new Date(Date.now() + DEFAULT_RECEIPT_EXPIRY_MS).toISOString()",
        "id: 'chainId'",
        "id: 'recipient'",
        "id: 'amount'",
        "id: 'asset'",
        "id: 'intentHash'",
        "id: 'expiry'",
        "id: 'transactionHash'",
        "function renderVerification(result)",
    ):
        assert_contains(js, marker, JS)


def test_receipt_verifier_is_static_and_never_signs_or_broadcasts() -> None:
    js = read(JS)
    for marker in (
        "walletConnected: false",
        "backendCalls: false",
        "transactionBroadcast: false",
        "signingEnabled: false",
        "localOnly: true",
    ):
        assert_contains(js, marker, JS)
    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "ethereum.request",
        "sendTransaction",
        "signTransaction",
        "personal_sign",
        "PRIVATE_KEY",
        "seed phrase",
    ):
        assert forbidden not in js, f"forbidden marker in {JS.relative_to(ROOT)}: {forbidden}"


def test_receipt_verifier_is_documented_and_linked() -> None:
    doc = read(DOC)
    readme = read(README)
    index = read(INDEX)
    viewer = read(VIEWER)
    validator = read(VALIDATOR)
    for marker in (
        "# Receipt verifier playground",
        "What this verifier checks",
        "What it does not prove",
        "local-only",
        "no wallet signing",
        "no transaction broadcast",
    ):
        assert_contains(doc, marker, DOC)
    for marker in (
        "examples/receipt-verifier-playground/index.html",
        "docs/receipt-verifier-playground.md",
    ):
        assert_contains(readme, marker, README)
        assert_contains(index, marker, INDEX)
        assert_contains(validator, marker, VALIDATOR)
    assert_contains(viewer, "id: 'receipt-verifier-playground.md'", VIEWER)


if __name__ == "__main__":
    test_receipt_verifier_page_has_safe_review_ui()
    test_receipt_verifier_checks_arc_payment_receipt_fields()
    test_receipt_verifier_is_static_and_never_signs_or_broadcasts()
    test_receipt_verifier_is_documented_and_linked()
    print("receipt verifier playground tests passed")
