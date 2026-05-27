#!/usr/bin/env python3
"""Regression checks for the local-only job escrow simulator."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples" / "job-escrow-simulator" / "index.html"
JS = ROOT / "examples" / "job-escrow-simulator" / "simulator.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, path: Path) -> None:
    if marker not in text:
        raise AssertionError(f"{path.relative_to(ROOT)} missing marker: {marker}")


def assert_not_contains(text: str, marker: str, path: Path) -> None:
    if marker in text:
        raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden marker: {marker}")


def test_job_escrow_review_loop_controls_are_present() -> None:
    html = read(HTML)
    for marker in (
        'id="request-changes"',
        'id="revise-work"',
        'id="revision-note"',
        "Request changes",
        "Revise work",
        "changes are simulated review notes",
        "No private keys, no custody, no mainnet, no autonomous spending.",
    ):
        assert_contains(html, marker, HTML)


def test_job_escrow_json_exposes_review_and_arc_safety_flags() -> None:
    js = read(JS)
    for marker in (
        "changes_requested",
        "changesRequestedCount",
        "latestRevisionNote",
        "payoutRelease: 'simulated_only_after_human_approval'",
        "arcTestnetChainId: 5042002",
        "arcTestnetChainIdHex: '0x4cef52'",
        "walletActionEnabled: false",
        "signingEnabled: false",
        "transactionBroadcast: false",
        "localOnly: true",
        "realEscrowContract: false",
    ):
        assert_contains(js, marker, JS)


def test_job_escrow_state_machine_allows_revisions_before_payout() -> None:
    js = read(JS)
    for marker in (
        "buttons.requestChanges.disabled = status !== 'work_submitted'",
        "buttons.revise.disabled = status !== 'changes_requested'",
        "setStatus('changes_requested', 'Reviewer requested changes before payout approval')",
        "setStatus('work_submitted', 'Agent resubmitted revised work for review')",
        "buttons.approve.disabled = status !== 'work_submitted'",
    ):
        assert_contains(js, marker, JS)


def test_job_escrow_simulator_forbids_wallet_network_and_secret_surface() -> None:
    html = read(HTML)
    js = read(JS)
    for text, path in ((html, HTML), (js, JS)):
        for marker in (
            "fetch(",
            "XMLHttpRequest",
            "WebSocket",
            "window.ethereum",
            "ethereum.request",
            "eth_sendTransaction",
            "wallet_switchEthereumChain",
            "sendTransaction",
            "signTransaction",
            "PRIVATE_KEY",
            "localStorage",
        ):
            assert_not_contains(text, marker, path)


if __name__ == "__main__":
    test_job_escrow_review_loop_controls_are_present()
    test_job_escrow_json_exposes_review_and_arc_safety_flags()
    test_job_escrow_state_machine_allows_revisions_before_payout()
    test_job_escrow_simulator_forbids_wallet_network_and_secret_surface()
    print("job escrow simulator tests passed")
