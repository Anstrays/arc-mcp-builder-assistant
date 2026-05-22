#!/usr/bin/env python3
"""Regression checks for the local-only payment intent playground."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/payment-intent-playground/index.html"
JS = ROOT / "examples/payment-intent-playground/playground.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, source: Path) -> None:
    assert marker in text, f"missing marker in {source.relative_to(ROOT)}: {marker}"


def test_arc_testnet_status_panel_is_visible_and_read_only() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="arc-status-panel"',
        'id="arc-chain-id"',
        'id="arc-rpc-url"',
        'id="arc-readonly-state"',
        'Arc Testnet status',
        'Read-only RPC probe',
        'No wallet connection',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "const ARC_TESTNET_STATUS",
        "expectedChainIdDecimal: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "walletConnected: false",
        "transactionBroadcast: false",
        "signingRequiresWalletChainGateAndHumanApproval: true",
        "renderArcStatusPanel()",
    ):
        assert_contains(js, marker, JS)


def test_playground_javascript_stays_local_only() -> None:
    js = read(JS)
    forbidden_markers = (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "ethereum.request",
        "sendTransaction",
        "signTransaction",
        "PRIVATE_KEY",
    )
    for marker in forbidden_markers:
        assert marker not in js, f"forbidden marker in {JS.relative_to(ROOT)}: {marker}"


if __name__ == "__main__":
    test_arc_testnet_status_panel_is_visible_and_read_only()
    test_playground_javascript_stays_local_only()
    print("payment intent playground tests passed")
