#!/usr/bin/env python3
"""Regression checks for local-only agent commerce flow templates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'examples/agent-commerce-flows/index.html'
JS = ROOT / 'examples/agent-commerce-flows/flows.js'
DOC = ROOT / 'docs/agent-commerce-flow-library.md'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_agent_commerce_flow_files_exist() -> None:
    assert HTML.is_file()
    assert JS.is_file()
    assert DOC.is_file()


def test_agent_commerce_flow_templates_are_present() -> None:
    combined = read(HTML) + '\n' + read(JS) + '\n' + read(DOC)
    for marker in (
        'paid-api-call',
        'creator-payout',
        'ai-agent-commerce',
        'Paid API call',
        'Creator payout',
        'AI-agent commerce',
        'id="flow-nav"',
        'id="freeze-flow"',
        'id="approve-flow"',
        'id="simulate-receipt"',
    ):
        assert marker in combined


def test_agent_commerce_flow_json_exposes_arc_and_safety_contract() -> None:
    js = read(JS)
    for marker in (
        'const ARC_FLOW_EXPECTATIONS = Object.freeze',
        "network: 'arc-testnet'",
        'chainId: 5042002',
        "chainIdHex: '0x4cef52'",
        "nativeGasAsset: 'USDC'",
        'erc20UsdcDecimals: 6',
        "schema: 'arc-mcp-builder-assistant.agentCommerce.flow.v1'",
        'humanApprovalRequired: true',
        'walletActionEnabled: false',
        'signingEnabled: false',
        'transactionBroadcast: false',
        'backendCalls: false',
        'remoteRpcCalls: false',
        'liveX402Verification: false',
        'mainnetEnabled: false',
    ):
        assert marker in js


def test_agent_commerce_flow_state_transitions_are_auditable() -> None:
    js = read(JS)
    for marker in (
        "state = 'fields_frozen'",
        "state = 'approved_local_no_broadcast'",
        "state = 'receipt_simulated'",
        'frozenBeforeWallet: Boolean(frozenAt)',
        "const moneyFieldsFrozen = state !== 'draft_review'",
        'field.disabled = moneyFieldsFrozen',
        "buttons.freeze.disabled = state !== 'draft_review'",
        "|| !amountIsValid(fields.amount.value)",
        "|| !recipientIsValid(fields.recipient.value)",
        'Human froze flow money fields before wallet handoff',
        'Human recorded local approval; no transaction was broadcast',
        'System generated simulated receipt for the selected flow',
    ):
        assert marker in js


def test_agent_commerce_flows_reject_invalid_money_and_zero_recipient_template() -> None:
    js = read(JS)
    for marker in (
        'function amountIsValid(value)',
        'function recipientIsValid(value)',
        '&& Number(value) > 0',
        "? Number(fields.amount.value).toFixed(2) : '0.00'",
        '!recipientIsValid(fields.recipient.value)',
    ):
        assert marker in js
    assert "recipient: '0x0000000000000000000000000000000000000000'" not in js


def test_agent_commerce_flows_forbid_wallet_network_and_secret_surface() -> None:
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
        'seed phrase',
        'localstorage',
    ):
        assert forbidden not in combined


if __name__ == '__main__':
    tests = [value for name, value in globals().items() if name.startswith('test_')]
    for test in tests:
        test()
    print(f'agent commerce flow checks passed ({len(tests)} tests)')
