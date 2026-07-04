#!/usr/bin/env python3
"""Regression checks for Circle agent wallet integration docs and example page."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/circle-wallet-integration.md"
HTML = ROOT / "examples/circle-wallet-integration/index.html"
JS = ROOT / "examples/circle-wallet-integration/wallet-lab.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_circle_wallet_files_exist() -> None:
    assert DOC.is_file(), f"Missing {DOC}"
    assert HTML.is_file(), f"Missing {HTML}"
    assert JS.is_file(), f"Missing {JS}"


def test_doc_contains_arc_testnet_constants() -> None:
    text = read(DOC)
    for marker in (
        "0x3600000000000000000000000000000000000000",
        "Arc Testnet",
        "5042002",
        "0x4cef52",
        "domain 26",
        "TokenMessengerV2",
        "GatewayWallet",
        "GatewayMinter",
    ):
        assert marker in text, f"Missing marker in doc: {marker}"


def test_doc_contains_bootstrap_and_safety_sections() -> None:
    text = read(DOC)
    for section in (
        "## Bootstrap flow",
        "## Developer-Controlled Wallet SDK guard",
        "## On-chain operations on Arc Testnet",
        "## Gateway (Nanopayments)",
        "## x402 marketplace",
        "## Safety boundaries",
        "## CLI reference",
    ):
        assert section in text, f"Missing section in doc: {section}"


def test_doc_contains_cli_commands() -> None:
    text = read(DOC)
    for cmd in (
        "circle wallet login",
        "circle wallet create",
        "circle wallet fund",
        "circle wallet balance",
        "circle wallet transfer",
        "circle bridge transfer",
        "circle gateway balance",
        "circle gateway deposit",
        "circle transaction list",
        "circle services search",
        "arc-builder wallet sdk-plan",
        "arc-builder wallet env-check",
        "arc-builder wallet sdk-snippet",
        "circle-developer-controlled-wallets",
        "ARC-TESTNET",
    ):
        assert cmd in text, f"Missing CLI command in doc: {cmd}"


def test_html_contains_safety_boundary() -> None:
    html = read(HTML)
    for marker in (
        "Arc Testnet",
        "no private keys",
        "no custody",
        "no mainnet",
        "human approval",
        "testnet only",
    ):
        assert marker.lower() in html.lower(), f"Missing safety marker in HTML: {marker}"


def test_html_contains_circle_wallet_lab_elements() -> None:
    html = read(HTML)
    for marker in (
        "circle-wallet-lab",
        "wallet-status",
        "wallet-address",
        "wallet-balance",
        "Arc Testnet",
        "5042002",
        "0x4cef52",
    ):
        assert marker in html, f"Missing element in HTML: {marker}"


def test_js_contains_no_wallet_signing_or_secrets() -> None:
    """The example page must not contain private keys, signing, or secret handling."""
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
    )
    for pattern in forbidden:
        assert pattern not in js, f"Forbidden pattern in JS: {pattern}"


def test_js_contains_circle_wallet_lab_logic() -> None:
    js = read(JS)
    for marker in (
        "ARC_TESTNET_CHAIN_ID",
        "0x4cef52",
        "circleWalletLab",
        "walletAddress",
        "renderStatus",
        "renderBalance",
    ):
        assert marker in js, f"Missing logic marker in JS: {marker}"


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"circle wallet integration checks passed ({len(tests)} tests)")
