#!/usr/bin/env python3
"""Verify the measurable completion contract for the current safe scope."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SURFACES = (
    "README.md",
    ".env.example",
    ".gitattributes",
    ".github/workflows/readiness-monitor.yml",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "index.html",
    "docs/view.html",
    "docs/viewer.js",
    "docs/completion-contract.md",
    "docs/current-readiness-report.md",
    "docs/arc-builder-readiness-checklist.md",
    "docs/arc-testnet-operator-evidence.md",
    "docs/guarded-wallet-send-runbook.md",
    "docs/custody-and-mainnet-gates.md",
    "docs/arc-agent-treasury-lab.md",
    "docs/receipt-viewer.md",
    "examples/receipt-viewer/index.html",
    "examples/receipt-viewer/receipt-viewer.js",
    "scripts/test_receipt_viewer.py",
    "scripts/receipt_viewer_behavior_harness.mjs",
    "examples/arc-agent-treasury-lab/index.html",
    "examples/arc-agent-treasury-lab/treasury.js",
    "scripts/test_arc_agent_treasury_lab.py",
    "scripts/arc_agent_treasury_behavior_harness.mjs",
    "examples/arc-testnet-wallet-send-gate/index.html",
    "examples/arc-testnet-wallet-send-gate/wallet-send-gate.js",
    "examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json",
    "scripts/validate_live_infrastructure_policy.py",
    "scripts/test_arc_testnet_wallet_send_behavior.py",
    "scripts/wallet_send_behavior_harness.mjs",
    "scripts/test_transaction_status_behavior.py",
    "scripts/transaction_status_behavior_harness.mjs",
    "scripts/test_all.py",
    "scripts/validate_repo.py",
    "scripts/arc_builder_doctor.py",
    "scripts/test_arc_builder_doctor.py",
    "config/arc_testnet.facts.json",
    "scripts/validate_arc_testnet_facts.py",
    "scripts/test_arc_testnet_facts.py",
    "docs/arc-builder-doctor.md",
    "docs/release-checklist.md",
    "scripts/generate_operator_evidence_draft.py",
    "scripts/report_operator_evidence.py",
    "scripts/validate_operator_evidence.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"completion check failed: {message}")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def check_required_surfaces() -> int:
    for relative in REQUIRED_SURFACES:
        if not (ROOT / relative).is_file():
            fail(f"missing required surface: {relative}")
    for surface in ("README.md", "index.html", "docs/viewer.js"):
        if "completion-contract.md" not in read(surface):
            fail(f"{surface} does not link the completion contract")
    return len(REQUIRED_SURFACES)


def check_canonical_suite() -> int:
    """Ensure every dependency-free regression script is in test_all.py."""
    runner = read("scripts/test_all.py")
    expected = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "scripts").glob("test_*.py")
        if path.name != "test_all.py"
    }
    expected.update({"scripts/check_completion.py", "scripts/validate_repo.py"})
    missing = sorted(relative for relative in expected if relative not in runner)
    if missing:
        fail(f"scripts/test_all.py is missing checks: {', '.join(missing)}")
    for marker in (
        "CHECK_TIMEOUT_SECONDS",
        "subprocess.TimeoutExpired",
        "timed out after",
        "TemporaryDirectory",
        '".arc-test-"',
        '"TMPDIR"',
        '"TEMP"',
        '"TMP"',
    ):
        if marker not in runner:
            fail(f"scripts/test_all.py is missing runner isolation marker: {marker}")
    return len(expected)


def check_safety_boundary() -> int:
    contract = read("docs/completion-contract.md").lower()
    readme = read("README.md").lower()
    server = read("examples/x402-local-challenge-server/server.py")
    gitignore = read(".gitignore")
    env_example = read(".env.example")

    required_contract_markers = (
        "no private keys",
        "no wallet connection on page load",
        "no custody",
        "no mainnet support",
        "no transaction broadcast on page load",
        "one attempt per page load",
    )
    for marker in required_contract_markers:
        if marker not in contract:
            fail(f"completion contract is missing safety marker: {marker}")
    for marker in ("no private keys", "no mainnet", "no autonomous spending"):
        if marker not in readme:
            fail(f"README is missing safety marker: {marker}")
    for marker in ('"transactionBroadcast": False', "X402_DEMO_MAINNET_ENABLED"):
        if marker not in server:
            fail(f"x402 server is missing fail-closed marker: {marker}")
    for marker in (".env", ".hermes/", "*.operator-evidence.local.json"):
        if marker not in gitignore:
            fail(f".gitignore is missing local-secret/evidence rule: {marker}")
    if "X402_DEMO_MAINNET_ENABLED=false" not in env_example:
        fail(".env.example must keep x402 mainnet disabled")
    guarded_send = read("examples/arc-testnet-wallet-send-gate/wallet-send-gate.js")
    for marker in ("reviewed-testnet-only", "sendAttempted = true", "method: 'eth_sendTransaction'"):
        if marker not in guarded_send:
            fail(f"guarded send lab is missing safety marker: {marker}")
    return len(required_contract_markers) + 11


def main() -> int:
    surfaces = check_required_surfaces()
    suite_checks = check_canonical_suite()
    safety_checks = check_safety_boundary()
    print(
        "completion check passed: "
        f"{surfaces} surfaces, {suite_checks} canonical checks, "
        f"{safety_checks} safety assertions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
