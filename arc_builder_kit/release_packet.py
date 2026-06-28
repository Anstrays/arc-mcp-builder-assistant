#!/usr/bin/env python3
"""Generate a local, read-only Arc Builder release packet for PR/release review.

This script is dependency-free and makes zero network calls by default. It
re-uses the existing Arc Builder Doctor orchestrator and Arc Testnet facts file
to produce Markdown/JSON artifacts that a maintainer can inspect, archive, or
attach to a release. It never connects a wallet, signs, broadcasts, handles
secrets, or claims settlement/mainnet readiness.

Output directory default: .arc-release-packet/
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

from arc_builder_kit._paths import CONFIG_DIR, DEFAULT_OUTPUT_ROOT, REPO_ROOT as ROOT

DEFAULT_OUT = DEFAULT_OUTPUT_ROOT / ".arc-release-packet"

KIND = "arc_builder_release_packet"
SCHEMA_VERSION = 1

# Reusable safety text used across generated artifacts.
DISCLAIMER = (
    "This packet is a read-only local review artifact. It is not a settlement "
    "proof, custody claim, mainnet readiness claim, or production release "
    "certificate. No wallet was connected, no private key was handled, no "
    "transaction was signed, and no transaction was broadcast while "
    "generating this packet."
)

EXAMPLES = [
    {
        "id": "payment-intent-receipt-matcher",
        "path": "examples/payment-intent-receipt-matcher",
        "purpose": "Compare a local payment-intent JSON with an Arc Testnet receipt's pinned USDC Transfer logs and emit a match/mismatch/revert/not-found/unknown verdict.",
        "boundary": "Read-only log inspection; no signing, no broadcast, no settlement claim; optional local evidence export via browser Blob only.",
    },
    {
        "id": "arc-testnet-wallet-send-gate",
        "path": "examples/arc-testnet-wallet-send-gate",
        "purpose": "Demonstrate a guarded, human-reviewed Arc Testnet browser-wallet send flow behind an explicit enable gate.",
        "boundary": "Signing and submission are delegated to an external user-controlled wallet; one attempt per page load; 1.00 USDC cap; disabled by default.",
    },
    {
        "id": "payment-intent-playground",
        "path": "examples/payment-intent-playground",
        "purpose": "Prepare reviewable payment-intent JSON with amount, recipient, memo, expiry, and local approval states.",
        "boundary": "Local-only intent drafting; no wallet connection and no broadcast.",
    },
    {
        "id": "receipt-verifier-playground",
        "path": "examples/receipt-verifier-playground",
        "purpose": "Verify receipt fields and decode pinned Arc Testnet USDC Transfer logs locally.",
        "boundary": "Read-only local verification; settlement claims are always false.",
    },
    {
        "id": "transaction-status-playground",
        "path": "examples/transaction-status-playground",
        "purpose": "Look up the status of an Arc Testnet transaction hash with chain-first validation.",
        "boundary": "Read-only; wrong-chain results stop before RPC; no signing or broadcast.",
    },
    {
        "id": "x402-local-challenge-server",
        "path": "examples/x402-local-challenge-server",
        "purpose": "Run a local x402-style paid-agent challenge/response boundary over loopback HTTP.",
        "boundary": "Loopback-only by default; no wallet required; no real settlement or mainnet mode.",
    },
    {
        "id": "arc-agent-treasury-lab",
        "path": "examples/arc-agent-treasury-lab",
        "purpose": "Simulate an agent treasury with x402 revenue, bounded compute spending, and deterministic verify/repair loops.",
        "boundary": "Local simulation only; no real funds, no wallet, no broadcast.",
    },
    {
        "id": "agent-commerce-components",
        "path": "examples/agent-commerce-components",
        "purpose": "Static UI components for agent-commerce screens.",
        "boundary": "Static HTML/JS demo; no network or wallet access.",
    },
    {
        "id": "agent-commerce-flows",
        "path": "examples/agent-commerce-flows",
        "purpose": "Interactive flow library for agent-commerce scenarios.",
        "boundary": "Static local demo; no signing or broadcast.",
    },
    {
        "id": "agent-commerce-review-packet",
        "path": "examples/agent-commerce-review-packet",
        "purpose": "Generate a human-readable review packet for agent-commerce terms.",
        "boundary": "Read-only local preview; no external calls.",
    },
    {
        "id": "agent-identity-profile-preview",
        "path": "examples/agent-identity-profile-preview",
        "purpose": "Preview ERC-8004-style agent identity metadata before registration.",
        "boundary": "Static local preview; no onchain registration.",
    },
    {
        "id": "job-escrow-simulator",
        "path": "examples/job-escrow-simulator",
        "purpose": "Simulate an ERC-8183-style job escrow lifecycle locally.",
        "boundary": "Local simulation; no real funds or dispute resolution.",
    },
    {
        "id": "receipt-viewer",
        "path": "examples/receipt-viewer",
        "purpose": "Read-only viewer for Arc Testnet payment receipts and USDC Transfer logs.",
        "boundary": "Read-only; no signing, no broadcast, settlement claims false.",
    },
]


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def git_info() -> tuple[str, str]:
    """Return (head_commit_sha, current_branch) without touching the network."""
    head = "unknown"
    branch = "unknown"
    for argv, name in (
        (["git", "rev-parse", "HEAD"], "head"),
        (["git", "rev-parse", "--abbrev-ref", "HEAD"], "branch"),
    ):
        try:
            result = subprocess.run(
                argv,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                value = result.stdout.strip()
                if name == "head":
                    head = value
                else:
                    branch = value
        except (OSError, subprocess.TimeoutExpired):
            pass
    return head, branch


def render_arc_testnet_facts_md(facts: dict[str, Any]) -> str:
    network = facts.get("network", {})
    erc20 = facts.get("erc20Usdc", {})
    native = facts.get("nativeGas", {})
    policy = facts.get("policy", {})
    lines = [
        "# Arc Testnet Facts",
        "",
        "Reviewed offline source of truth for Arc Testnet implementation.",
        "",
        "## Network",
        "",
        f"- **Name:** {network.get('name')}",
        f"- **Chain ID (decimal):** {network.get('chainId')}",
        f"- **Chain ID (hex):** {network.get('chainIdHex')}",
        f"- **RPC URL (label):** {network.get('rpcUrl')}",
        f"- **Explorer URL (label):** {network.get('explorerUrl')}",
        "",
        "## Native gas token",
        "",
        f"- **Symbol:** {native.get('symbol')}",
        f"- **Decimals:** {native.get('decimals')}",
        "",
        "## ERC-20 USDC",
        "",
        f"- **Symbol:** {erc20.get('symbol')}",
        f"- **Address:** {erc20.get('address')}",
        f"- **Decimals:** {erc20.get('decimals')}",
        "",
        "## Policy",
        "",
        f"- **Mainnet supported:** {policy.get('mainnetSupported')}",
        f"- **Wallet required:** {policy.get('walletRequired')}",
        f"- **Network checks opt-in:** {policy.get('networkChecksOptIn')}",
        f"- **Recheck before publication:** {policy.get('recheckBeforePublication')}",
        "",
        "## Scope disclaimer",
        "",
        "These facts describe the Arc Testnet only. Mainnet, custody, production",
        "deployment, and live settlement are out of scope for this builder kit.",
        "",
        DISCLAIMER,
        "",
    ]
    return "\n".join(lines)


def render_readiness_checklist_md() -> str:
    lines = [
        "# Release Readiness Checklist",
        "",
        "Run these checks before sharing a release packet or opening a release review.",
        "",
        "## Local verification commands",
        "",
        "- [ ] `python3 scripts/test_all.py` — full local regression suite passes.",
        "- [ ] `python3 scripts/validate_repo.py` — repository validation passes.",
        "- [ ] `python3 scripts/test_public_claims.py` — public claims are consistent.",
        "- [ ] `python3 scripts/arc_builder_doctor.py` — local health report is pass/warn.",
        "- [ ] `python3 scripts/validate_arc_testnet_facts.py` — Arc Testnet facts are consistent.",
        "",
        "## Docs and public-site checks",
        "",
        "- [ ] README describes the current MVP, quickstart, and safety boundaries.",
        "- [ ] Docs viewer links resolve and no malicious Markdown HTML escapes.",
        "- [ ] GitHub Pages site previewed locally or via published Pages URL.",
        "",
        "## Wallet and signing boundary",
        "",
        "- [ ] No private keys, seed phrases, or wallet credentials are committed.",
        "- [ ] Wallet signing happens only in the guarded send lab and only through an injected user wallet.",
        "- [ ] Local examples do not connect a wallet on page load.",
        "",
        "## x402 / local commerce boundary",
        "",
        "- [ ] x402 demo config keeps `X402_DEMO_MAINNET_ENABLED=false`.",
        "- [ ] Local x402 HTTP mode rejects non-loopback hosts.",
        "- [ ] No production verifier credentials are present.",
        "",
        "## Receipt matcher / evidence export boundary",
        "",
        "- [ ] Receipt matcher verdicts are local and read-only.",
        "- [ ] Evidence export uses browser Blob/download only; no upload, no telemetry, no storage.",
        "- [ ] Mismatch/revert/not-found verdicts do not claim settlement.",
        "",
        "## CI summary boundary",
        "",
        "- [ ] Validate workflow publishes the Arc Builder Doctor Markdown summary.",
        "- [ ] Workflow permissions remain `contents: read` for the validate job.",
        "",
        "## Explicit non-perform declaration",
        "",
        "This packet and the repository it describes do **not**:",
        "",
        "- connect to or operate a wallet;",
        "- sign or broadcast transactions;",
        "- hold custody of user funds or private keys;",
        "- target any mainnet;",
        "- claim live settlement, payment finality, or production readiness.",
        "",
        DISCLAIMER,
        "",
    ]
    return "\n".join(lines)


def render_examples_index_md() -> str:
    lines = [
        "# Examples Index",
        "",
        "Local builder-kit examples and their safety boundaries.",
        "",
        "| Example | Path | Purpose | Safety Boundary |",
        "| --- | --- | --- | --- |",
    ]
    for example in EXAMPLES:
        purpose = example["purpose"].replace("\n", " ").replace("|", "\\|")
        boundary = example["boundary"].replace("\n", " ").replace("|", "\\|")
        lines.append(
            f"| {example['id']} | `{example['path']}` | {purpose} | {boundary} |"
        )
    lines.extend(
        [
            "",
            "## Shared invariants",
            "",
            "- Examples are local-first and wallet-free unless explicitly labelled as a guarded wallet lab.",
            "- No example signs or broadcasts on page load.",
            "- No example claims mainnet readiness or live settlement.",
            "",
            DISCLAIMER,
            "",
        ]
    )
    return "\n".join(lines)


def build_release_packet_json(
    facts: dict[str, Any],
    outputs: list[str],
    repo_head: str,
    branch: str,
    doctor_report: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "kind": KIND,
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generator": "scripts/generate_arc_release_packet.py",
        "repoHead": repo_head,
        "branch": branch,
        "arcFacts": {
            "network": facts.get("network", {}),
            "nativeGas": facts.get("nativeGas", {}),
            "erc20Usdc": facts.get("erc20Usdc", {}),
            "policy": facts.get("policy", {}),
        },
        "outputs": outputs,
        "doctorOverallStatus": doctor_report["overallStatus"] if doctor_report else "unknown",
        "safetyBoundaries": {
            "walletConnected": False,
            "privateKeysAccepted": False,
            "signingEnabled": False,
            "transactionBroadcast": False,
            "custodyEnabled": False,
            "mainnetEnabled": False,
            "autonomousSpending": False,
            "networkChecksOptIn": True,
            "localOnly": True,
            "secretsRead": False,
        },
        "recommendedChecks": [
            "python3 scripts/test_all.py",
            "python3 scripts/validate_repo.py",
            "python3 scripts/test_public_claims.py",
            "python3 scripts/arc_builder_doctor.py",
            "python3 scripts/validate_arc_testnet_facts.py",
        ],
        "disclaimer": DISCLAIMER,
    }


def run_doctor_report() -> tuple[dict[str, Any], str]:
    """Build a local-only Arc Builder Doctor report and render Markdown.

    Importing the doctor module re-uses its existing orchestration. Network
    checks are never enabled here.
    """
    from arc_builder_kit.doctor import Options, build_report, render_markdown

    options = Options()
    report = build_report(options)
    markdown = render_markdown(report)
    return report, markdown


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_arc_release_packet",
        description=(
            "Generate a local, read-only Arc Builder release packet for "
            "PR/release review. No wallet, signing, broadcast, custody, "
            "mainnet, secrets, or network calls are used by default."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="output directory (default: .arc-release-packet)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing output directory",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "all"),
        default="all",
        help="artifact formats to generate (default: all)",
    )
    return parser.parse_args(argv)


def validate_output_dir(out_dir: Path) -> Path:
    """Resolve and confirm output stays inside the reviewed output root."""
    try:
        resolved = out_dir.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        fail(f"cannot resolve output path: {exc}")

    # resolve() follows symlinks, so symlink escapes fail.
    try:
        resolved.relative_to(DEFAULT_OUTPUT_ROOT.resolve())
    except ValueError:
        fail(f"output path must be inside output root: {resolved}")

    if resolved == DEFAULT_OUTPUT_ROOT.resolve():
        fail("refusing to use the output root as the output directory")

    return resolved


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = validate_output_dir(args.out)

    if out_dir.exists():
        if not args.force:
            fail(
                f"output directory already exists: {out_dir}; "
                "use --force to overwrite"
            )
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    facts_path = CONFIG_DIR / "arc_testnet.facts.json"
    try:
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(f"failed to read Arc Testnet facts: {exc}")

    doctor_report: dict[str, Any] | None = None
    doctor_md = ""
    try:
        doctor_report, doctor_md = run_doctor_report()
    except Exception as exc:  # pragma: no cover - orchestrator failure surfaces clearly
        fail(f"Arc Builder Doctor failed: {exc}")

    outputs: list[str] = []
    written: dict[str, Path] = {}

    if args.format in ("markdown", "all"):
        written["arc-builder-doctor.md"] = out_dir / "arc-builder-doctor.md"
        written["arc-testnet-facts.md"] = out_dir / "arc-testnet-facts.md"
        written["readiness-checklist.md"] = out_dir / "readiness-checklist.md"
        written["examples-index.md"] = out_dir / "examples-index.md"

    if args.format in ("json", "all"):
        written["arc-testnet-facts.json"] = out_dir / "arc-testnet-facts.json"

    content_map = {
        "arc-builder-doctor.md": doctor_md,
        "arc-testnet-facts.md": render_arc_testnet_facts_md(facts),
        "arc-testnet-facts.json": json.dumps(facts, indent=2) + "\n",
        "readiness-checklist.md": render_readiness_checklist_md(),
        "examples-index.md": render_examples_index_md(),
    }

    for name, path in written.items():
        path.write_text(content_map[name], encoding="utf-8")
        outputs.append(name)

    if args.format in ("json", "all"):
        packet = build_release_packet_json(
            facts=facts,
            outputs=outputs + ["release-packet.json"],
            repo_head=git_info()[0],
            branch=git_info()[1],
            doctor_report=doctor_report,
        )
        (out_dir / "release-packet.json").write_text(
            json.dumps(packet, indent=2) + "\n", encoding="utf-8"
        )
        outputs.append("release-packet.json")

    print(f"Generated Arc Builder release packet in {out_dir}")
    for name in outputs:
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
