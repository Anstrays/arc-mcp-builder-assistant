#!/usr/bin/env python3
"""Regression checks for the read-only Arc receipt viewer."""

from __future__ import annotations

import base64
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/receipt-viewer/index.html"
JS = ROOT / "examples/receipt-viewer/receipt-viewer.js"
DOC = ROOT / "docs/receipt-viewer.md"
README = ROOT / "README.md"
INDEX = ROOT / "index.html"
VIEWER = ROOT / "docs/viewer.js"
VALIDATOR = ROOT / "arc_builder_kit/validate_repo.py"
SITEMAP = ROOT / "sitemap.xml"
HARNESS = ROOT / "scripts" / "receipt_viewer_behavior_harness.mjs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, source: Path) -> None:
    assert marker in text, f"missing marker in {source.relative_to(ROOT)}: {marker}"


def compute_sri_hash(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return f"sha384-{base64.b64encode(digest).decode('ascii')}"


def test_receipt_viewer_page_has_read_only_receipt_ui() -> None:
    html = read(HTML)
    for marker in (
        "Agent Payment Receipt Viewer",
        'id="transaction-hash"',
        'id="load-receipt"',
        'id="reset-receipt"',
        'id="status-pill"',
        'id="receipt-summary-list"',
        'id="transfer-log-list"',
        'id="receipt-json"',
        "Read-only Arc Testnet RPC",
        "USDC Transfer logs",
        "No wallet connection",
        "No transaction broadcast",
        "connect-src 'self' https://rpc.testnet.arc.network",
        'crossorigin="anonymous"',
    ):
        assert_contains(html, marker, HTML)


def test_receipt_viewer_script_tag_has_matching_sri() -> None:
    html = read(HTML)
    script_match = re.search(
        r'<script[^>]*src="\./receipt-viewer\.js"[^>]*integrity="(sha384-[A-Za-z0-9+/=]+)"[^>]*>',
        html,
    )
    assert script_match, "receipt-viewer.js script tag must have an integrity attribute"
    observed_integrity = script_match.group(1)
    expected_integrity = compute_sri_hash(JS)
    assert observed_integrity == expected_integrity, (
        f"SRI hash mismatch: expected {expected_integrity}, got {observed_integrity}. "
        "Recompute with: openssl dgst -sha384 -binary examples/receipt-viewer/receipt-viewer.js | openssl base64 -A"
    )


def test_receipt_viewer_js_uses_receipt_only_read_only_rpc() -> None:
    js = read(JS)
    for marker in (
        "const ARC_RECEIPT_VIEWER = Object.freeze",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "usdcDecimals: 6",
        "const RPC_TIMEOUT_MS = 15_000",
        "const MAX_RPC_RESPONSE_BYTES = 1_000_000",
        "const RPC_REQUEST_ID = 'arc-receipt-viewer-read-only'",
        "const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'",
        "method: 'eth_chainId'",
        "method: 'eth_getTransactionReceipt'",
        "new AbortController()",
        "new TextEncoder().encode(responseText).byteLength",
        "window.clearTimeout(timeout)",
        "Request timed out after 15 seconds.",
        "RPC response must be a JSON object",
        "RPC response envelope did not match the request",
        "RPC response must contain exactly one result or error field",
        "function decodeUsdcTransferLog(log)",
        "function extractUsdcTransferLogs(receipt)",
        "function classifyReceiptStatus(chainIdHex, receipt, expectedTransactionHash)",
        "success_receipt_observed",
        "reverted_receipt_observed",
        "receipt_not_found",
        "unknown_wrong_chain",
        "unknown_hash_mismatch",
        "settlementProven: false",
        "businessAcceptanceProven: false",
    ):
        assert_contains(js, marker, JS)
    assert "eth_getTransactionByHash" not in js, "receipt viewer must not fetch full transactions"


def test_receipt_viewer_forbids_wallet_signing_storage_or_broadcast_surface() -> None:
    combined = read(HTML) + "\n" + read(JS)
    for marker in (
        "walletConnected: false",
        "backendCalls: false",
        "readOnlyRpcCheckOnly: true",
        "transactionBroadcast: false",
        "signingEnabled: false",
        "autonomousSpending: false",
        "humanApprovalRequired: true",
    ):
        assert_contains(combined, marker, JS)
    for forbidden in (
        "window.ethereum",
        "ethereum.request",
        "personal_sign",
        "eth_sendTransaction",
        "eth_sendRawTransaction",
        "wallet_switchEthereumChain",
        "sendTransaction",
        "signTransaction",
        "PRIVATE_KEY",
        "localStorage",
        "sessionStorage",
    ):
        assert forbidden not in combined, f"forbidden marker in receipt viewer: {forbidden}"


def test_receipt_viewer_doc_site_and_validator_are_registered() -> None:
    doc = read(DOC)
    readme = read(README)
    index = read(INDEX)
    viewer = read(VIEWER)
    validator = read(VALIDATOR)
    sitemap = read(SITEMAP)
    for marker in (
        "# Agent payment receipt viewer",
        "eth_getTransactionReceipt",
        "USDC Transfer logs",
        "15-second timeout",
        "1 MB safety limit",
        "no wallet signing",
        "no transaction broadcast",
        "does not prove business acceptance",
    ):
        assert_contains(doc, marker, DOC)
    for marker in (
        "examples/receipt-viewer/index.html",
        "docs/receipt-viewer.md",
    ):
        assert_contains(readme, marker, README)
        assert_contains(index, marker, INDEX)
        assert_contains(validator, marker, VALIDATOR)
    assert_contains(viewer, "id: 'receipt-viewer.md'", VIEWER)
    assert_contains(sitemap, "examples/receipt-viewer/", SITEMAP)


def test_actual_receipt_viewer_javascript_behavior() -> None:
    node = shutil.which("node")
    if not node:
        raise AssertionError("receipt viewer behavior test requires Node.js 18+; no npm packages are required")
    completed = subprocess.run(
        [node, str(HARNESS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "receipt viewer behavior harness failed:\n"
            f"{completed.stdout}{completed.stderr}"
        )
    assert_contains(completed.stdout, "receipt viewer behavior harness passed", HARNESS)


if __name__ == "__main__":
    test_receipt_viewer_page_has_read_only_receipt_ui()
    test_receipt_viewer_script_tag_has_matching_sri()
    test_receipt_viewer_js_uses_receipt_only_read_only_rpc()
    test_receipt_viewer_forbids_wallet_signing_storage_or_broadcast_surface()
    test_receipt_viewer_doc_site_and_validator_are_registered()
    test_actual_receipt_viewer_javascript_behavior()
    print("receipt viewer tests passed")
