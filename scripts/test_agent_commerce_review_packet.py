#!/usr/bin/env python3
"""Regression checks for the local-only agent commerce review packet."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/agent-commerce-review-packet.md'
HTML = ROOT / 'examples/agent-commerce-review-packet/index.html'
JS = ROOT / 'examples/agent-commerce-review-packet/packet.js'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_review_packet_files_exist() -> None:
    assert DOC.is_file()
    assert HTML.is_file()
    assert JS.is_file()


def test_review_packet_schema_and_arc_constants_are_present() -> None:
    combined = read(DOC) + '\n' + read(JS)
    for marker in (
        'arc-mcp-builder-assistant.agentCommerce.reviewPacket.v1',
        "status: 'local_review_packet'",
        "name: 'arc-testnet'",
        'chainId: 5042002',
        "chainIdHex: '0x4cef52'",
        "status: 'unregistered_local_preview'",
    ):
        assert marker in combined


def test_review_packet_outcomes_and_freeze_state_are_explicit() -> None:
    combined = read(HTML) + '\n' + read(JS)
    for marker in (
        'pending_local_review',
        'approved_for_local_demo',
        'rejected_no_payout',
        'disputed_manual_review',
        'expired_no_payout',
        'cancelled_no_payout',
        "packetState = 'draft_packet'",
        "packetState = 'packet_frozen_for_review'",
        "moneyFieldsFrozen: packetState === 'packet_frozen_for_review'",
        "const packetFrozen = packetState === 'packet_frozen_for_review'",
        'field.disabled = packetFrozen',
        'buttons.freeze.disabled = packetFrozen || !amountIsValid(fields.amount.value)',
        "payoutReleased: false",
    ):
        assert marker in combined


def test_review_packet_rejects_invalid_money_before_freeze() -> None:
    js = read(JS)
    for marker in (
        'function amountIsValid(value)',
        '&& Number(value) > 0',
        "? Number(fields.amount.value).toFixed(2) : '0.00'",
    ):
        assert marker in js


def test_review_packet_controls_keep_live_surfaces_disabled() -> None:
    js = read(JS)
    for marker in (
        'localOnly: true',
        'walletConnected: false',
        'walletActionEnabled: false',
        'signingEnabled: false',
        'transactionBroadcast: false',
        'networkCallsEnabled: false',
        'backendCalls: false',
        'remoteRpcCalls: false',
        'settlementEnabled: false',
        'reputationWritten: false',
        'validationRequested: false',
        'secretRequired: false',
        'mainnetEnabled: false',
        'humanApprovalRequired: true',
    ):
        assert marker in js


def test_review_packet_forbids_wallet_network_and_secret_markers() -> None:
    combined = (read(HTML) + '\n' + read(JS)).lower()
    for forbidden in (
        'fetch(',
        'xmlhttprequest',
        'websocket',
        'window.ethereum',
        'ethereum.request',
        'eth_sendtransaction',
        'wallet_switchethereumchain',
        'sendtransaction',
        'signtransaction',
        'private_key',
        'entity_secret',
        'api_key',
        'seed phrase',
        'localstorage',
    ):
        assert forbidden not in combined


if __name__ == '__main__':
    tests = [value for name, value in globals().items() if name.startswith('test_')]
    for test in tests:
        test()
    print(f'agent commerce review packet checks passed ({len(tests)} tests)')
