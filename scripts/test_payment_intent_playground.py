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


def test_wallet_action_controls_are_disabled_with_explicit_guard_reasons() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="wallet-guard-panel"',
        'id="wallet-action-button"',
        'disabled aria-disabled="true"',
        'id="wallet-guard-reasons"',
        'Wallet action unavailable',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function getWalletGuardReasons(intent)",
        "Wrong chain: expected Arc Testnet chain ID 5042002 (0x4cef52).",
        "RPC unavailable: no live browser RPC probe is enabled in this local-only demo.",
        "Unverified docs/constants: re-check Arc MCP/docs before any signing PR.",
        "Missing recipient: enter a 0x-prefixed Arc Testnet recipient before review.",
        "Invalid amount or decimals: use a positive USDC amount with at most 6 decimal places.",
        "Expired intent: choose a future expiry before enabling wallet review.",
        "User approval required: real signing must open an external wallet confirmation.",
        "renderWalletGuardPanel(intent)",
    ):
        assert_contains(js, marker, JS)


def test_intent_json_includes_arc_network_readiness_fields() -> None:
    js = read(JS)
    for marker in (
        "networkReadiness: {",
        "chainId: ARC_TESTNET_STATUS.expectedChainIdDecimal",
        "chainIdHex: ARC_TESTNET_STATUS.expectedChainIdHex",
        "rpcUrl: ARC_TESTNET_STATUS.rpcUrl",
        "explorerUrl: ARC_TESTNET_STATUS.explorerUrl",
        "assetAddress: ARC_TESTNET_STATUS.erc20UsdcAddress",
        "assetDecimals: ARC_TESTNET_STATUS.erc20UsdcDecimals",
        "nativeGasDecimals: ARC_TESTNET_STATUS.nativeGasDecimals",
        "statusSource: ARC_TESTNET_STATUS.statusSource",
    ):
        assert_contains(js, marker, JS)


def test_signing_preflight_report_is_rendered_without_wallet_actions() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="signing-preflight-panel"',
        'Signing preflight report',
        'id="signing-preflight-report"',
        'Manual copy for wallet PR review',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function buildSigningPreflightReport(intent)",
        "walletAction: 'blocked'",
        "nextRequiredReview: 'separate testnet-only wallet PR'",
        "guardReasons: getWalletGuardReasons(intent)",
        "chainGate: {",
        "recipientFormat: {",
        "amountFormat: {",
        "expiryWindow: {",
        "humanApproval: {",
        "renderSigningPreflightReport(intent)",
    ):
        assert_contains(js, marker, JS)


def test_signing_preflight_report_can_be_copied_without_network_or_wallet() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="copy-preflight-report"',
        'Copy preflight report',
        'aria-describedby="signing-preflight-copy-help"',
        'id="signing-preflight-copy-help"',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function serializeSigningPreflightReport(intent)",
        "function copySigningPreflightReport()",
        "function logEvent(status, message)",
        "await navigator.clipboard.writeText(reportText)",
        "logEvent('copied_preflight_report'",
        "copyPreflightButton.addEventListener('click'",
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
    test_wallet_action_controls_are_disabled_with_explicit_guard_reasons()
    test_intent_json_includes_arc_network_readiness_fields()
    test_signing_preflight_report_is_rendered_without_wallet_actions()
    test_signing_preflight_report_can_be_copied_without_network_or_wallet()
    test_playground_javascript_stays_local_only()
    print("payment intent playground tests passed")
