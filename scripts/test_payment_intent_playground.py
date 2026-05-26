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
        'id="wallet-provider-state"',
        'id="wallet-address-state"',
        'id="wallet-chain-state"',
        'Read-only wallet preview state',
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
        "Wallet adapter feature flag is off: this UI only previews provider/address/chain state.",
        "Wallet provider not detected: no injected browser wallet was observed.",
        "Wallet account unknown: this guard does not request accounts or permissions.",
        "Frozen intent changed: restart review before any future wallet action.",
        "function getWalletPreviewState(intent)",
        "requestMethodsCalled: false",
        "walletActionEnabled: false",
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


def test_usdc_unit_preview_distinguishes_erc20_units_from_native_gas() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="unit-preview-panel"',
        'USDC unit preview',
        'id="erc20-base-units"',
        'id="native-gas-decimals"',
        'ERC-20 USDC uses 6 decimals',
        'Native gas accounting uses 18 decimals',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function formatUsdcBaseUnits(amount)",
        "baseUnits: formatUsdcBaseUnits(intent.amount)",
        "erc20Decimals: ARC_TESTNET_STATUS.erc20UsdcDecimals",
        "nativeGasDecimals: ARC_TESTNET_STATUS.nativeGasDecimals",
        "function renderUnitPreview(intent)",
        "renderUnitPreview(intent)",
    ):
        assert_contains(js, marker, JS)


def test_unsigned_transaction_draft_preview_is_local_only() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="unsigned-transaction-panel"',
        'Unsigned transaction draft',
        'ERC-20 transfer payload preview',
        'id="unsigned-transaction-draft"',
        'It is unsigned JSON only',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function buildErc20TransferCalldata(intent)",
        "function buildUnsignedTransactionDraft(intent)",
        "type: 'unsigned_erc20_transfer_preview'",
        "walletRequestEnabled: false",
        "unsignedOnly: true",
        "gasEstimateIncluded: false",
        "simulationIncluded: false",
        "method: 'transfer(address,uint256)'",
        "renderUnsignedTransactionDraft(intent)",
        "unsignedTransactionDraft: buildUnsignedTransactionDraft(intent)",
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
        "validationSummary: buildValidationSummary(intent)",
        "chainGate: {",
        "recipientFormat: {",
        "amountFormat: {",
        "expiryWindow: {",
        "walletPreview: getWalletPreviewState(intent)",
        "frozenIntent: frozenIntentSnapshot ? frozenIntentSnapshot.fields : null",
        "frozenIntent: {",
        "humanApproval: {",
        "renderSigningPreflightReport(intent)",
    ):
        assert_contains(js, marker, JS)


def test_validation_summary_panel_shows_local_readiness_without_wallet_actions() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="validation-summary-panel"',
        'Validation summary',
        'id="validation-summary-list"',
        'Local readiness checks',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function buildValidationSummary(intent)",
        "id: 'recipient'",
        "label: 'Recipient format'",
        "id: 'amount'",
        "label: 'USDC amount'",
        "id: 'expiry'",
        "label: 'Future expiry'",
        "id: 'approval'",
        "label: 'Human approval marker'",
        "function renderValidationSummary(intent)",
        "validationSummaryList.replaceChildren(",
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


def test_default_demo_values_are_reviewable_without_real_wallet_details() -> None:
    html = read(HTML)

    for marker in (
        'value="0x1111111111111111111111111111111111111111"',
        'value="5.00"',
        'value="2026-05-30T00:00"',
    ):
        assert_contains(html, marker, HTML)


def test_status_state_machine_uses_review_safe_vocabulary() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="status-state-list"',
        'Status states',
        'data-status-step="draft"',
        'data-status-step="ready_for_review"',
        'data-status-step="approved_local"',
        'data-status-step="final_review_confirmed"',
        'data-status-step="blocked_wallet_unavailable"',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "const STATUS_STATES = Object.freeze([",
        "id: 'draft'",
        "id: 'ready_for_review'",
        "id: 'approved_local'",
        "id: 'final_review_confirmed'",
        "id: 'blocked_wallet_unavailable'",
        "function nextStatusAfterPrepare(intent)",
        "function markStatusStep(currentStatusId)",
        "currentStatus === 'approved_local'",
        "function freezeIntentForReview(intent)",
        "function hasFrozenIntentChanged(intent)",
        "appendEvent('ready_for_review'",
        "appendEvent('final_review_confirmed'",
        "appendEvent('blocked_wallet_unavailable'",
    ):
        assert_contains(js, marker, JS)

    for removed_status in (
        "pending_human_approval",
        "approved_locally",
        "submitted_simulation",
    ):
        assert removed_status not in js, f"old status vocabulary still present in {JS.relative_to(ROOT)}: {removed_status}"


def test_final_confirmation_gate_is_local_only_and_keeps_transactions_disabled() -> None:
    html = read(HTML)
    js = read(JS)

    for marker in (
        'id="final-confirmation-panel"',
        'Final confirmation, still no transaction',
        'id="final-confirmation-checkbox"',
        'id="final-confirmation-button"',
        'Confirm final review locally',
        'id="final-confirmation-reasons"',
    ):
        assert_contains(html, marker, HTML)

    for marker in (
        "function getFinalConfirmationReasons(intent)",
        "function canRecordFinalConfirmation(intent)",
        "function renderFinalConfirmationPanel(intent)",
        "finalConfirmationRecorded = false",
        "finalConfirmationButton.disabled = !canConfirm",
        "transactionRequestEnabled: false",
        "appendEvent('final_review_confirmed'",
    ):
        assert_contains(js, marker, JS)


def test_playground_javascript_stays_local_only() -> None:
    js = read(JS)
    forbidden_markers = (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "ethereum.request",
        "eth_sendTransaction",
        "wallet_switchEthereumChain",
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
    test_usdc_unit_preview_distinguishes_erc20_units_from_native_gas()
    test_unsigned_transaction_draft_preview_is_local_only()
    test_signing_preflight_report_is_rendered_without_wallet_actions()
    test_validation_summary_panel_shows_local_readiness_without_wallet_actions()
    test_signing_preflight_report_can_be_copied_without_network_or_wallet()
    test_default_demo_values_are_reviewable_without_real_wallet_details()
    test_status_state_machine_uses_review_safe_vocabulary()
    test_final_confirmation_gate_is_local_only_and_keeps_transactions_disabled()
    test_playground_javascript_stays_local_only()
    print("payment intent playground tests passed")
