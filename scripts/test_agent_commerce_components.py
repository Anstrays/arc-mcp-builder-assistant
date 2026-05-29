#!/usr/bin/env python3
"""Regression checks for the local-only agent commerce component starter."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'examples/agent-commerce-components/index.html'
JS = ROOT / 'examples/agent-commerce-components/components.js'
DOC = ROOT / 'docs/agent-commerce-components.md'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_agent_commerce_component_files_exist() -> None:
    assert HTML.is_file()
    assert JS.is_file()
    assert DOC.is_file()


def test_agent_commerce_component_cards_are_present() -> None:
    html = read(HTML)
    for marker in (
        'id="agent-card"',
        'id="payment-card"',
        'id="receipt-card"',
        'id="event-log"',
        'id="freeze-request"',
        'id="mark-approved"',
        'id="mark-receipt"',
        'Local-only starter kit',
    ):
        assert marker in html


def test_agent_commerce_json_exposes_arc_and_safety_flags() -> None:
    js = read(JS)
    for marker in (
        'const ARC_COMPONENT_EXPECTATIONS = Object.freeze',
        "network: 'arc-testnet'",
        'chainId: 5042002',
        "chainIdHex: '0x4cef52'",
        "nativeGasAsset: 'USDC'",
        'erc20UsdcDecimals: 6',
        "schema: 'arc-mcp-builder-assistant.agentCommerce.components.v1'",
        'humanApprovalRequired: true',
        'walletActionEnabled: false',
        'signingEnabled: false',
        'transactionBroadcast: false',
        'backendCalls: false',
        'mainnetEnabled: false',
    ):
        assert marker in js


def test_agent_commerce_flow_freezes_before_approval_and_receipt() -> None:
    js = read(JS)
    for marker in (
        "status = 'frozen'",
        "status = 'approved'",
        "status = 'receipt_simulated'",
        'moneyFieldsFrozenBeforeWallet: Boolean(frozenAt)',
        "Human froze payment request fields before wallet handoff",
        "Human recorded local approval; no wallet action was enabled",
        "System added simulated receipt card without transaction broadcast",
    ):
        assert marker in js


def test_agent_commerce_forbids_wallet_network_and_secret_surface() -> None:
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
    print(f'agent commerce component checks passed ({len(tests)} tests)')
