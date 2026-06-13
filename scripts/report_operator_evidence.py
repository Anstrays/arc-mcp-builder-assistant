#!/usr/bin/env python3
"""Report all known readiness gaps in an operator evidence packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_operator_evidence import (
    DEFAULT_PACKET,
    FALSE_CONTROLS,
    ROOT,
    SCHEMA,
    SECRET_VALUE_PATTERNS,
    TRUE_CONTROLS,
    TRUE_EVIDENCE,
    EvidenceValidationError,
    display_path,
    load_json_object,
    validate_commit_sha,
    validate_packet,
    validate_references,
    walk_strings,
)


class ReportInputError(ValueError):
    """Raised when no safe readiness report can be produced."""


def as_object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def has_credential_like_value(packet: dict[str, Any]) -> bool:
    return any(
        pattern.search(text)
        for text in walk_strings(packet)
        for pattern in SECRET_VALUE_PATTERNS
    )


def build_report(
    packet: dict[str, Any],
    expected_commit: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    gaps: set[str] = set()

    if packet.get("schema") != SCHEMA:
        gaps.add("schema")
    if packet.get("packetStatus") != "local_operator_evidence":
        gaps.add("packetStatus")

    expected_network = {"name": "arc-testnet", "chainId": 5042002, "chainIdHex": "0x4cef52"}
    if packet.get("network") != expected_network:
        gaps.add("network")

    review = as_object(packet.get("review"))
    try:
        reviewed_commit = validate_commit_sha(review.get("reviewedCommit"), "review.reviewedCommit")
    except EvidenceValidationError:
        reviewed_commit = None
        gaps.add("review.reviewedCommit")
    if review.get("reviewedSurface") != "pre_send_readiness_baseline":
        gaps.add("review.reviewedSurface")
    if review.get("manualReviewRequired") is not True:
        gaps.add("review.manualReviewRequired")

    commit_matches_expected: bool | None = None
    if expected_commit is not None:
        expected = validate_commit_sha(expected_commit, "expected commit")
        commit_matches_expected = reviewed_commit == expected
        if not commit_matches_expected:
            gaps.add("review.reviewedCommit")

    evidence = as_object(packet.get("evidence"))
    for field in TRUE_EVIDENCE:
        if evidence.get(field) is not True:
            gaps.add(f"evidence.{field}")
    if evidence.get("walletRequestSpyResult") != "not_applicable_no_wallet_surface":
        gaps.add("evidence.walletRequestSpyResult")
    try:
        validate_references(evidence.get("references"), root)
    except (EvidenceValidationError, OSError):
        gaps.add("evidence.references")

    controls = as_object(packet.get("controls"))
    for field in FALSE_CONTROLS:
        if controls.get(field) is not False:
            gaps.add(f"controls.{field}")
    for field in TRUE_CONTROLS:
        if controls.get(field) is not True:
            gaps.add(f"controls.{field}")

    decision = as_object(packet.get("decision"))
    if decision.get("status") != "blocked_pending_separate_guarded_pr":
        gaps.add("decision.status")
    for field in ("reason", "rollbackOwner", "rollbackAction"):
        if not isinstance(decision.get(field), str) or not decision[field].strip():
            gaps.add(f"decision.{field}")

    credential_like_value_detected = has_credential_like_value(packet)
    if credential_like_value_detected:
        gaps.add("credentialLikeValueDetected")

    try:
        validate_packet(packet, root)
    except (EvidenceValidationError, OSError):
        gaps.add("strictValidationContract")

    sorted_gaps = sorted(gaps)
    strict_ready = not sorted_gaps
    return {
        "readiness": "strict_validation_ready" if strict_ready else "incomplete_or_unsafe",
        "strictValidationReady": strict_ready,
        "gaps": sorted_gaps,
        "reviewedCommit": reviewed_commit,
        "expectedCommitChecked": expected_commit is not None,
        "commitMatchesExpected": commit_matches_expected,
        "credentialLikeValueDetected": credential_like_value_detected,
        "transactionBroadcast": controls.get("transactionBroadcast"),
        "liveSendApproved": False,
        "note": "Read-only readiness report. This command never approves signing or transaction broadcast.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report read-only Arc Testnet operator evidence readiness gaps."
    )
    parser.add_argument("packet", nargs="?", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--expect-commit", help="Full lowercase commit SHA expected by the operator")
    args = parser.parse_args()

    try:
        if args.expect_commit is not None:
            validate_commit_sha(args.expect_commit, "expected commit")
        packet = load_json_object(args.packet)
        report = build_report(packet, args.expect_commit)
    except (EvidenceValidationError, ReportInputError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    report["ok"] = report["strictValidationReady"]
    report["packet"] = display_path(args.packet)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["strictValidationReady"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
