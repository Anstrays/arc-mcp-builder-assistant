#!/usr/bin/env python3
"""Regression and security checks for the local Arc Agent Treasury lab."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples" / "arc-agent-treasury-lab" / "index.html"
JS = ROOT / "examples" / "arc-agent-treasury-lab" / "treasury.js"
HARNESS = ROOT / "scripts" / "arc_agent_treasury_behavior_harness.mjs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, marker: str, path: Path) -> None:
    if marker not in text:
        raise AssertionError(f"{path.relative_to(ROOT)} missing marker: {marker}")


def assert_not_contains(text: str, marker: str, path: Path) -> None:
    if marker in text:
        raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden marker: {marker}")


def test_product_surface_is_complete() -> None:
    html = read(HTML)
    for marker in (
        "Arc Agent Treasury Lab",
        'id="opening-balance"',
        'id="reserve"',
        'id="daily-cap"',
        'id="single-task-cap"',
        'id="min-profit"',
        'id="request-id"',
        'id="receipt-id"',
        'id="review-task"',
        'id="run-loop"',
        'id="ledger"',
        'id="snapshot"',
        "No wallet, custody, mainnet, backend, signing, settlement, or transaction broadcast.",
        "Failed verification never emits a success claim",
    ):
        assert_contains(html, marker, HTML)


def test_domain_exposes_fail_closed_policy_and_loop() -> None:
    js = read(JS)
    for marker in (
        "const MICRO_USDC = 1_000_000",
        "parseUsdc",
        "single_task_cap_exceeded",
        "daily_spend_cap_exceeded",
        "protected_reserve_would_be_breached",
        "minimum_profit_not_met",
        "request_replay_detected",
        "receipt_replay_detected",
        "Runtime spend preflight failed closed",
        "failed_manual_review",
        "manualRefundReviewRequired",
        "outputVerified",
        "settled: false",
        "transactionBroadcast: false",
        "autonomousSpendingEnabled: false",
        "mainnetEnabled: false",
        "custodyEnabled: false",
        "chainId: 5042002",
        "chainIdHex: '0x4cef52'",
    ):
        assert_contains(js, marker, JS)


def test_local_lab_forbids_wallet_network_storage_and_secrets() -> None:
    for text, path in ((read(HTML), HTML), (read(JS), JS)):
        for marker in (
            "fetch(",
            "XMLHttpRequest",
            "WebSocket",
            "window.ethereum",
            "ethereum.request",
            "eth_sendTransaction",
            "eth_sendRawTransaction",
            "personal_sign",
            "signTypedData",
            "localStorage",
            "sessionStorage",
            "PRIVATE_KEY",
            "seed phrase",
            "setInterval(",
        ):
            assert_not_contains(text, marker, path)


def test_actual_javascript_behavior() -> None:
    result = subprocess.run(
        ["node", str(HARNESS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    assert_contains(result.stdout, "arc agent treasury behavior harness passed", HARNESS)


if __name__ == "__main__":
    test_product_surface_is_complete()
    test_domain_exposes_fail_closed_policy_and_loop()
    test_local_lab_forbids_wallet_network_storage_and_secrets()
    test_actual_javascript_behavior()
    print("arc agent treasury lab tests passed")
