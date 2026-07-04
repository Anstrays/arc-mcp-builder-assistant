#!/usr/bin/env python3
"""Adversarial source checks for the guarded Arc Testnet wallet send lab."""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/arc-testnet-wallet-send-gate/index.html"
JS = ROOT / "examples/arc-testnet-wallet-send-gate/wallet-send-gate.js"
RUNBOOK = ROOT / "docs/guarded-wallet-send-runbook.md"
GATES = ROOT / "docs/custody-and-mainnet-gates.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, source: Path) -> None:
    assert marker in text, f"missing marker in {source.relative_to(ROOT)}: {marker}"


def compute_sri_hash(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return f"sha384-{base64.b64encode(digest).decode('ascii')}"


def test_page_is_disabled_by_default_and_requires_explicit_human_gates() -> None:
    html = read(HTML)
    js = read(JS)
    for marker in (
        "Disabled by default",
        "Arc Testnet only",
        "One attempt per page load",
        "No automatic retry",
        'id="risk-acknowledgement"',
        'id="connect-wallet"',
        'id="switch-network"',
        'id="freeze-intent"',
        'id="confirmation-phrase"',
        'id="final-send-confirmation"',
        'id="send-transaction"',
        "[hidden] { display: none !important; }",
        'id="transaction-link" class="submitted-link" hidden',
    ):
        assert_contains(html, marker, HTML)
    for marker in (
        "enableArcTestnetSend",
        "reviewed-testnet-only",
        "elements.riskAcknowledgement.checked",
        "elements.confirmationPhrase.value === REQUIRED_CONFIRMATION",
        "elements.finalSendConfirmation.checked",
        "sendAttempted: false",
        "sendAttempted = true",
        "function canAttemptSend()",
        "const ALLOWED_WALLET_METHODS = new Set",
        "if (!ALLOWED_WALLET_METHODS.has(request.method))",
        "topLevelContext: window.top === window.self",
        "['top-level-context', state.topLevelContext",
        "!state.topLevelContext",
        "Risk acknowledgement cleared. Freeze and review the intent again.",
    ):
        assert_contains(js, marker, JS)


def test_security_headers_and_csp_are_present_and_strict() -> None:
    html = read(HTML)
    assert_contains(html, '<meta name="robots" content="noindex,nofollow" />', HTML)
    assert_contains(html, '<meta http-equiv="X-Content-Type-Options" content="nosniff" />', HTML)
    assert_contains(html, "frame-ancestors 'none'", HTML)
    assert_contains(html, "connect-src 'none'", HTML)
    assert_contains(html, "script-src 'self'", HTML)
    assert_contains(html, "object-src 'none'", HTML)
    assert_contains(html, "base-uri 'none'", HTML)
    assert_contains(html, "form-action 'none'", HTML)


def test_script_tag_has_subresource_integrity_matching_current_source() -> None:
    html = read(HTML)
    js = read(JS)
    script_match = re.search(
        r'<script[^>]*src="\./wallet-send-gate\.js"[^>]*integrity="(sha384-[A-Za-z0-9+/=]+)"[^>]*>',
        html,
    )
    assert script_match, "wallet-send-gate.js script tag must have an integrity attribute"
    observed_integrity = script_match.group(1)
    expected_integrity = compute_sri_hash(JS)
    assert observed_integrity == expected_integrity, (
        f"SRI hash mismatch: expected {expected_integrity}, got {observed_integrity}. "
        "Recompute with: openssl dgst -sha384 -binary examples/arc-testnet-wallet-send-gate/wallet-send-gate.js | openssl base64 -A"
    )
    assert 'crossorigin="anonymous"' in html, "SRI script tag must use crossorigin=\"anonymous\""


def test_transaction_shape_is_pinned_to_arc_testnet_usdc_and_frozen_payload() -> None:
    js = read(JS)
    for marker in (
        "const ARC_TESTNET = Object.freeze",
        "chainId: 5042002",
        "chainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "usdcDecimals: 6",
        "maxAmountBaseUnits: 1000000n",
        "const TRANSFER_SELECTOR = 'a9059cbb'",
        "function parseUsdcAmount",
        "function isNonZeroAddress",
        "function encodeTransferCalldata",
        "function decodeTransferCalldata",
        "function intentMatchesFrozen",
        "function draftMatchesFrozenIntent",
        "chainId: ARC_TESTNET.chainIdHex",
        "rebuilt.chainId === ARC_TESTNET.chainIdHex",
        "value: '0x0'",
        "Recipient cannot be the pinned USDC token contract address.",
        "const failedPrerequisite = report.checks.find",
        "throw new Error(failedPrerequisite.detail",
    ):
        assert_contains(js, marker, JS)


def test_only_reviewed_wallet_methods_are_present_and_no_request_runs_on_load() -> None:
    js = read(JS)
    for marker in (
        "method: 'eth_requestAccounts'",
        "method: 'eth_chainId'",
        "method: 'eth_accounts'",
        "method: 'wallet_switchEthereumChain'",
        "method: 'wallet_addEthereumChain'",
        "method: 'eth_sendTransaction'",
        "const internalMessage = error instanceof Error ? error.message : ''",
    ):
        assert_contains(js, marker, JS)
    first_listener = js.index("elements.riskAcknowledgement.addEventListener")
    send_request = js.index("method: 'eth_sendTransaction'")
    assert send_request < first_listener, "send request must be defined before event wiring, not invoked during startup"
    startup = js[first_listener:]
    assert "requestWallet(" not in startup, "startup/event wiring block must not request the wallet"
    for forbidden in (
        "personal_sign",
        "eth_sign",
        "signTransaction",
        "eth_sendRawTransaction",
        "PRIVATE_KEY",
        "seed phrase",
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "setInterval",
        "setTimeout",
    ):
        assert forbidden not in js, f"forbidden guarded-send marker: {forbidden}"
    lock_position = js.index("state.sendAttempted = true", js.index("async function requestOneTransaction"))
    live_preflight_position = js.index("method: 'eth_chainId'", js.index("async function requestOneTransaction"))
    send_position = js.index("method: 'eth_sendTransaction'", js.index("async function requestOneTransaction"))
    assert lock_position < live_preflight_position < send_position, "one-shot lock must engage before async wallet preflight and send"


def test_custody_and_mainnet_are_fail_closed_documented_boundaries() -> None:
    runbook = read(RUNBOOK).lower()
    gates = read(GATES).lower()
    for marker in (
        "injected user-controlled browser wallet",
        "wallet confirmation dialog is the only signing path",
        "one attempt per page load",
        "no automatic retry",
        "rollback",
    ):
        assert marker in runbook, f"missing runbook marker: {marker}"
    for marker in (
        "non-custodial",
        "mainnet remains blocked",
        "upcoming",
        "no fake mainnet constants",
        "secret manager",
        "separate security review",
        "static site",
    ):
        assert marker in gates, f"missing custody/mainnet marker: {marker}"


if __name__ == "__main__":
    test_page_is_disabled_by_default_and_requires_explicit_human_gates()
    test_security_headers_and_csp_are_present_and_strict()
    test_script_tag_has_subresource_integrity_matching_current_source()
    test_transaction_shape_is_pinned_to_arc_testnet_usdc_and_frozen_payload()
    test_only_reviewed_wallet_methods_are_present_and_no_request_runs_on_load()
    test_custody_and_mainnet_are_fail_closed_documented_boundaries()
    print("guarded Arc Testnet wallet send gate tests passed")
