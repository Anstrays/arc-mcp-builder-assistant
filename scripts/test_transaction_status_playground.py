#!/usr/bin/env python3
"""Regression checks for the read-only Arc transaction status playground."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/transaction-status-playground/index.html"
JS = ROOT / "examples/transaction-status-playground/status.js"
DOC = ROOT / "docs/transaction-status-playground.md"
README = ROOT / "README.md"
INDEX = ROOT / "index.html"
VIEWER = ROOT / "docs/viewer.js"
VALIDATOR = ROOT / "scripts/validate_repo.py"
SITEMAP = ROOT / "sitemap.xml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, source: Path) -> None:
    assert marker in text, f"missing marker in {source.relative_to(ROOT)}: {marker}"


def test_transaction_status_page_has_read_only_lookup_ui() -> None:
    html = read(HTML)
    for marker in (
        "Transaction Status Playground",
        'id="transaction-hash"',
        'id="check-transaction"',
        'id="reset-transaction"',
        'id="status-pill"',
        'id="status-check-list"',
        'id="transaction-status-json"',
        "Read-only Arc Testnet RPC",
        "No wallet connection",
        "No transaction broadcast",
        "No private keys",
        "connect-src 'self' https://rpc.testnet.arc.network",
    ):
        assert_contains(html, marker, HTML)


def test_transaction_status_js_uses_narrow_read_only_rpc_methods() -> None:
    js = read(JS)
    for marker in (
        "const ARC_TRANSACTION_STATUS = Object.freeze",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "method: 'eth_chainId'",
        "method: 'eth_getTransactionByHash'",
        "method: 'eth_getTransactionReceipt'",
        "readOnlyRpcCheckOnly: true",
        "transactionBroadcast: false",
        "signingRequiresWalletChainGateAndHumanApproval: true",
        "function classifyTransactionStatus(chainIdHex, transaction, receipt)",
        "state: 'not_checked'",
        "state: 'pending'",
        "state: 'confirmed'",
        "state: 'failed'",
        "state: 'unknown'",
    ):
        assert_contains(js, marker, JS)


def test_transaction_status_playground_forbids_wallet_or_signing_surface() -> None:
    combined = read(HTML) + "\n" + read(JS)
    for marker in (
        "walletConnected: false",
        "backendCalls: false",
        "transactionBroadcast: false",
        "autonomousSpending: false",
        "humanApprovalRequired: true",
        "readOnlyRpcCheckOnly: true",
    ):
        assert_contains(combined, marker, JS)
    for forbidden in (
        "window.ethereum",
        "ethereum.request",
        "personal_sign",
        "eth_sendTransaction",
        "wallet_switchEthereumChain",
        "signTransaction",
        "PRIVATE_KEY",
        "seed phrase",
        "localStorage",
    ):
        assert forbidden not in combined, f"forbidden marker in transaction status playground: {forbidden}"


def test_transaction_status_doc_and_site_links_are_registered() -> None:
    doc = read(DOC)
    readme = read(README)
    index = read(INDEX)
    viewer = read(VIEWER)
    validator = read(VALIDATOR)
    sitemap = read(SITEMAP)
    for marker in (
        "# Transaction status playground",
        "Read-only status states",
        "What it can verify",
        "What it cannot verify",
        "eth_getTransactionByHash",
        "eth_getTransactionReceipt",
        "no wallet signing",
        "no transaction broadcast",
    ):
        assert_contains(doc, marker, DOC)
    for marker in (
        "examples/transaction-status-playground/index.html",
        "docs/transaction-status-playground.md",
    ):
        assert_contains(readme, marker, README)
        assert_contains(index, marker, INDEX)
        assert_contains(validator, marker, VALIDATOR)
    assert_contains(viewer, "id: 'transaction-status-playground.md'", VIEWER)
    assert_contains(sitemap, "examples/transaction-status-playground/", SITEMAP)


if __name__ == "__main__":
    test_transaction_status_page_has_read_only_lookup_ui()
    test_transaction_status_js_uses_narrow_read_only_rpc_methods()
    test_transaction_status_playground_forbids_wallet_or_signing_surface()
    test_transaction_status_doc_and_site_links_are_registered()
    print("transaction status playground tests passed")
