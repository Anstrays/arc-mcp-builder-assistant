#!/usr/bin/env python3
"""Regression checks for the local-only ERC-8004 identity profile preview."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/agent-identity-profile-preview.md'
HTML = ROOT / 'examples/agent-identity-profile-preview/index.html'
JS = ROOT / 'examples/agent-identity-profile-preview/identity.js'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_identity_preview_files_exist() -> None:
    assert DOC.is_file()
    assert HTML.is_file()
    assert JS.is_file()


def test_identity_preview_uses_official_arc_registry_addresses() -> None:
    combined = read(DOC) + '\n' + read(JS)
    for marker in (
        '0x8004A818BFB912233c491871b3d84c89A494BD9e',
        '0x8004B663056A597Dffe9eCcC1965A193B7388713',
        '0x8004Cb1BF31DAf7788923b405b754f57acEB4272',
        'chainId: 5042002',
        "chainIdHex: '0x4cef52'",
        'https://docs.arc.network/arc/tutorials/register-your-first-ai-agent',
    ):
        assert marker in combined


def test_identity_preview_exposes_profile_schema_and_review_states() -> None:
    js = read(JS)
    for marker in (
        "schema: 'arc-mcp-builder-assistant.agentIdentity.preview.v1'",
        "state = 'draft_profile'",
        "state = 'profile_frozen_for_review'",
        "status: 'unregistered_local_preview'",
        "metadataUri: 'not_uploaded'",
        "agentId: 'unknown_until_registered'",
        'ownerCannotSelfValidate: true',
        'futureRegistrationRequiresSeparatePr: true',
        "const profileFrozen = state === 'profile_frozen_for_review'",
        "field.disabled = profileFrozen",
        "buttons.freeze.disabled = profileFrozen",
    ):
        assert marker in js


def test_identity_preview_keeps_live_surfaces_disabled() -> None:
    js = read(JS)
    for marker in (
        'localOnly: true',
        'statusImpliesRegistration: false',
        'walletConnected: false',
        'walletActionEnabled: false',
        'metadataUploaded: false',
        'registrationTransactionPrepared: false',
        'reputationTransactionPrepared: false',
        'validationTransactionPrepared: false',
        'signingEnabled: false',
        'transactionBroadcast: false',
        'backendCalls: false',
        'remoteRpcCalls: false',
        'humanApprovalRequired: true',
        'mainnetEnabled: false',
    ):
        assert marker in js


def test_identity_preview_forbids_wallet_network_and_secret_markers() -> None:
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
        'circle_api_key',
        'entity_secret',
        'private_key',
        'seed phrase',
        'localstorage',
    ):
        assert forbidden not in combined


if __name__ == '__main__':
    tests = [value for name, value in globals().items() if name.startswith('test_')]
    for test in tests:
        test()
    print(f'agent identity profile preview checks passed ({len(tests)} tests)')
