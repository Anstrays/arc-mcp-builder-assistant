#!/usr/bin/env python3
"""Regression checks for agent commerce live evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/agent-commerce-live-evidence.md"
HTML = ROOT / "examples/agent-commerce-live/index.html"
JS = ROOT / "examples/agent-commerce-live/commerce-live.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_agent_commerce_live_files_exist() -> None:
    assert DOC.is_file(), f"Missing {DOC}"
    assert HTML.is_file(), f"Missing {HTML}"
    assert JS.is_file(), f"Missing {JS}"


def test_doc_contains_real_transaction_hashes() -> None:
    text = read(DOC)
    for tx_hash in (
        "0xb570a204eb4d81d3610694cce5e33d647312924ef7e1448e01ce8f42fa733dd1",
        "0x490df63904f7722c369a76bc656f8d59f2223846274b52e41b626e187ee13aa8",
        "0xda2ed5d09c781cbf5c475e4d9fc697e479c35b6e5cef866ab4dd78d86f247fca",
        "0x7855802e76412ee50a7f7ffe445ae291fade450914103154277960974b623f15",
    ):
        assert tx_hash in text, f"Missing tx hash in doc: {tx_hash}"


def test_doc_contains_arc_testnet_constants() -> None:
    text = read(DOC)
    for marker in (
        "5042002",
        "0x4cef52",
        "0x3600000000000000000000000000000000000000",
        "domain 26",
        "Arc Testnet",
    ):
        assert marker in text, f"Missing marker in doc: {marker}"


def test_doc_contains_wallet_address_and_safety() -> None:
    text = read(DOC)
    for marker in (
        "0x0cd9b933302d90bfe295471deac7f4eafd9ea401",
        "Testnet only",
        "No private keys",
        "No custody",
        "No mainnet",
        "No autonomous spending",
        "No secrets committed",
    ):
        assert marker in text, f"Missing marker in doc: {marker}"


def test_html_contains_live_evidence_elements() -> None:
    html = read(HTML)
    for marker in (
        "agent-commerce-live",
        "wallet-state",
        "tx-log",
        "unit-economics",
        "Arc Testnet",
        "5042002",
    ):
        assert marker in html, f"Missing element in HTML: {marker}"


def test_html_contains_safety_boundary() -> None:
    html = read(HTML)
    for marker in (
        "testnet only",
        "no private keys",
        "no custody",
        "no mainnet",
        "no autonomous spending",
        "human-approved",
    ):
        assert marker.lower() in html.lower(), f"Missing safety marker in HTML: {marker}"


def test_js_contains_no_wallet_signing_or_secrets() -> None:
    js = read(JS)
    forbidden = (
        "private_key",
        "privateKey",
        "seed phrase",
        "eth_sign",
        "personal_sign",
        "signTypedData",
        "eth_sendRawTransaction",
        "api_key",
        "apiKey",
        "entity_secret",
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "websocket",
        "window.ethereum",
    )
    for pattern in forbidden:
        assert pattern not in js, f"Forbidden pattern in JS: {pattern}"


def test_js_contains_transaction_data() -> None:
    js = read(JS)
    for marker in (
        "WALLET_ADDRESS",
        "ARC_TESTNET_CHAIN_ID",
        "0x0cd9b933302d90bfe295471deac7f4eafd9ea401",
        "0x4cef52",
        "0x490df63904f7722c36",
        "0xda2ed5d09c781cbf5c",
        "0xb570a204eb4d81d36",
        "COMPLETE",
        "TRANSFER",
        "CCTP",
    ):
        assert marker in js, f"Missing data marker in JS: {marker}"


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"agent commerce live checks passed ({len(tests)} tests)")
