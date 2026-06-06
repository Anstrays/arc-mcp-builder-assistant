#!/usr/bin/env python3
"""Generate an intentionally incomplete, fail-closed operator evidence draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_operator_evidence import ROOT, SCHEMA, display_path, validate_commit_sha

DEFAULT_OUTPUT = Path("arc.operator-evidence.local.json")
LOCAL_DRAFT_SUFFIX = ".operator-evidence.local.json"


class DraftGenerationError(ValueError):
    """Raised when a safe local draft cannot be created."""


def build_draft(reviewed_commit: str) -> dict[str, Any]:
    commit = validate_commit_sha(reviewed_commit, "reviewed commit")
    return {
        "schema": SCHEMA,
        "packetStatus": "draft_operator_evidence",
        "network": {
            "name": "arc-testnet",
            "chainId": 5042002,
            "chainIdHex": "0x4cef52",
        },
        "review": {
            "reviewedCommit": commit,
            "reviewedSurface": "pre_send_readiness_baseline",
            "manualReviewRequired": True,
        },
        "evidence": {
            "frozenIntentReviewed": False,
            "unsignedDraftMatchesIntent": False,
            "finalLocalConfirmationReviewed": False,
            "walletRequestSpyResult": "not_applicable_no_wallet_surface",
            "testsPassed": False,
            "browserSmokePassed": False,
            "arcStatusCheckPassed": False,
            "references": [
                "docs/arc-testnet-send-readiness-gate.md",
                "docs/arc-testnet-operator-runbook.md",
                "scripts/test_all.py",
                "scripts/check_arc_testnet_status.py",
            ],
        },
        "controls": {
            "walletConnected": False,
            "signingEnabled": False,
            "transactionBroadcast": False,
            "backendSignerEnabled": False,
            "mainnetEnabled": False,
            "autonomousSpendingEnabled": False,
            "ethSendTransactionForbidden": True,
            "noSecretsObserved": False,
            "humanApprovalRequired": True,
            "separateGuardedPrRequired": True,
        },
        "decision": {
            "status": "blocked_pending_separate_guarded_pr",
            "reason": (
                "Generated draft is incomplete and cannot approve a live-send implementation."
            ),
            "rollbackOwner": "unassigned_draft_owner",
            "rollbackAction": (
                "Keep wallet and transaction surfaces disabled; discard this local draft if review stops."
            ),
        },
    }


def resolve_output(output: Path) -> Path:
    text = str(output)
    lower_parts = {part.lower() for part in output.parts}
    if (
        output.is_absolute()
        or ":" in text
        or ".." in output.parts
        or ".git" in lower_parts
        or not output.name.endswith(LOCAL_DRAFT_SUFFIX)
    ):
        if not output.name.endswith(LOCAL_DRAFT_SUFFIX):
            raise DraftGenerationError(
                f"output must end with {LOCAL_DRAFT_SUFFIX}"
            )
        if ".git" in lower_parts:
            raise DraftGenerationError("output must not be inside .git")
        raise DraftGenerationError("output must be a repository-relative path")

    resolved = (ROOT / output).resolve()
    root_resolved = ROOT.resolve()
    if root_resolved not in (resolved, *resolved.parents):
        raise DraftGenerationError("output must stay inside the repository")
    resolved_relative = resolved.relative_to(root_resolved)
    if ".git" in {part.lower() for part in resolved_relative.parts}:
        raise DraftGenerationError("resolved output must not be inside .git")
    if not resolved.parent.is_dir():
        raise DraftGenerationError("output parent directory must already exist")
    return resolved


def write_draft(output: Path, packet: dict[str, Any]) -> Path:
    resolved = resolve_output(output)
    payload = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    try:
        with resolved.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise DraftGenerationError(
            f"refusing to overwrite existing file: {display_path(resolved)}"
        ) from exc
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a blocked local Arc Testnet operator evidence draft."
    )
    parser.add_argument(
        "--reviewed-commit",
        required=True,
        help="Full lowercase commit SHA the draft will be bound to",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Repository-relative create-only output ending with {LOCAL_DRAFT_SUFFIX}",
    )
    args = parser.parse_args()

    try:
        packet = build_draft(args.reviewed_commit)
        output = write_draft(args.output, packet)
    except (DraftGenerationError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    except OSError as exc:
        error = exc.strerror or exc.__class__.__name__
        print(
            json.dumps(
                {"ok": False, "error": f"could not create local draft: {error}"},
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "draft": display_path(output),
                "reviewedCommit": packet["review"]["reviewedCommit"],
                "decision": packet["decision"]["status"],
                "packetStatus": packet["packetStatus"],
                "strictValidationReady": False,
                "existingFileOverwritten": False,
                "manualSecretReviewComplete": False,
                "transactionBroadcast": packet["controls"]["transactionBroadcast"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
