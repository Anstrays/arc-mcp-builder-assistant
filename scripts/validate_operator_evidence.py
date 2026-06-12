#!/usr/bin/env python3
"""Validate a fail-closed Arc Testnet operator evidence packet."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "examples" / "arc-testnet-operator-evidence" / "evidence.example.json"
SCHEMA = "arc-mcp-builder-assistant.arcTestnet.operatorEvidence.v1"
MAX_PACKET_BYTES = 1_000_000

TOP_LEVEL_KEYS = {"schema", "packetStatus", "network", "review", "evidence", "controls", "decision"}
NETWORK_KEYS = {"name", "chainId", "chainIdHex"}
REVIEW_KEYS = {"reviewedCommit", "reviewedSurface", "manualReviewRequired"}
EVIDENCE_KEYS = {
    "frozenIntentReviewed",
    "unsignedDraftMatchesIntent",
    "finalLocalConfirmationReviewed",
    "walletRequestSpyResult",
    "testsPassed",
    "browserSmokePassed",
    "arcStatusCheckPassed",
    "references",
}
CONTROL_KEYS = {
    "walletConnected",
    "signingEnabled",
    "transactionBroadcast",
    "backendSignerEnabled",
    "mainnetEnabled",
    "autonomousSpendingEnabled",
    "ethSendTransactionForbidden",
    "noSecretsObserved",
    "humanApprovalRequired",
    "separateGuardedPrRequired",
}
DECISION_KEYS = {"status", "reason", "rollbackOwner", "rollbackAction"}

FALSE_CONTROLS = {
    "walletConnected",
    "signingEnabled",
    "transactionBroadcast",
    "backendSignerEnabled",
    "mainnetEnabled",
    "autonomousSpendingEnabled",
}
TRUE_CONTROLS = {
    "ethSendTransactionForbidden",
    "noSecretsObserved",
    "humanApprovalRequired",
    "separateGuardedPrRequired",
}
TRUE_EVIDENCE = {
    "frozenIntentReviewed",
    "unsignedDraftMatchesIntent",
    "finalLocalConfirmationReviewed",
    "testsPassed",
    "browserSmokePassed",
    "arcStatusCheckPassed",
}
SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b0x[0-9a-fA-F]{64}\b"),
)


class EvidenceValidationError(ValueError):
    """Raised when an operator evidence packet violates the safety contract."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceValidationError("duplicate JSON key is not allowed")
        result[key] = value
    return result


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"{location} must be a JSON object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], location: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        raise EvidenceValidationError(f"{location} missing required fields: {', '.join(missing)}")
    if unknown:
        raise EvidenceValidationError(f"{location} contains unknown fields (count: {len(unknown)})")


def require_nonempty_text(value: Any, location: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise EvidenceValidationError(f"{location} must be non-empty text")
    return value.strip()


def validate_commit_sha(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[0-9a-f]{40}", value)
        or set(value) == {"0"}
    ):
        raise EvidenceValidationError(f"{location} must be a full lowercase commit SHA")
    return value


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = [str(key) for key in value]
        for nested in value.values():
            strings.extend(walk_strings(nested))
        return strings
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(walk_strings(nested))
        return strings
    return []


def validate_references(references: Any, root: Path) -> None:
    if not isinstance(references, list) or not references:
        raise EvidenceValidationError("evidence.references must be a non-empty list")
    if len(references) != len({str(reference) for reference in references}):
        raise EvidenceValidationError("evidence.references must not contain duplicates")
    root_resolved = root.resolve()
    for index, reference in enumerate(references):
        text = require_nonempty_text(reference, f"evidence.references[{index}]")
        path = Path(text)
        if path.is_absolute() or "\\" in text or ":" in text or ".." in path.parts:
            raise EvidenceValidationError(
                f"evidence.references[{index}] must be a repository-relative path"
            )
        resolved = (root / path).resolve()
        if root_resolved not in (resolved, *resolved.parents) or not resolved.is_file():
            raise EvidenceValidationError(
                f"evidence.references[{index}] does not resolve to a repository file"
            )


def validate_packet(packet: Any, root: Path = ROOT) -> dict[str, Any]:
    packet = require_object(packet, "packet")
    require_exact_keys(packet, TOP_LEVEL_KEYS, "packet")

    if packet["schema"] != SCHEMA:
        raise EvidenceValidationError(f"schema must be {SCHEMA}")
    if packet["packetStatus"] != "local_operator_evidence":
        raise EvidenceValidationError("packetStatus must be local_operator_evidence")

    network = require_object(packet["network"], "network")
    require_exact_keys(network, NETWORK_KEYS, "network")
    if network != {"name": "arc-testnet", "chainId": 5042002, "chainIdHex": "0x4cef52"}:
        raise EvidenceValidationError("network must be Arc Testnet 5042002 / 0x4cef52")

    review = require_object(packet["review"], "review")
    require_exact_keys(review, REVIEW_KEYS, "review")
    validate_commit_sha(review["reviewedCommit"], "review.reviewedCommit")
    if review["reviewedSurface"] != "pre_send_readiness_baseline":
        raise EvidenceValidationError("review.reviewedSurface must be pre_send_readiness_baseline")
    if review["manualReviewRequired"] is not True:
        raise EvidenceValidationError("review.manualReviewRequired must be true")

    evidence = require_object(packet["evidence"], "evidence")
    require_exact_keys(evidence, EVIDENCE_KEYS, "evidence")
    for field in TRUE_EVIDENCE:
        if evidence[field] is not True:
            raise EvidenceValidationError(f"evidence.{field} must be true")
    if evidence["walletRequestSpyResult"] != "not_applicable_no_wallet_surface":
        raise EvidenceValidationError(
            "evidence.walletRequestSpyResult must be not_applicable_no_wallet_surface"
        )
    validate_references(evidence["references"], root)

    controls = require_object(packet["controls"], "controls")
    require_exact_keys(controls, CONTROL_KEYS, "controls")
    for field in FALSE_CONTROLS:
        if controls[field] is not False:
            raise EvidenceValidationError(f"controls.{field} must be false")
    for field in TRUE_CONTROLS:
        if controls[field] is not True:
            raise EvidenceValidationError(f"controls.{field} must be true")

    decision = require_object(packet["decision"], "decision")
    require_exact_keys(decision, DECISION_KEYS, "decision")
    if decision["status"] != "blocked_pending_separate_guarded_pr":
        raise EvidenceValidationError(
            "decision.status must be blocked_pending_separate_guarded_pr"
        )
    require_nonempty_text(decision["reason"], "decision.reason", minimum=20)
    require_nonempty_text(decision["rollbackOwner"], "decision.rollbackOwner", minimum=3)
    require_nonempty_text(decision["rollbackAction"], "decision.rollbackAction", minimum=20)

    for text in walk_strings(packet):
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(text):
                raise EvidenceValidationError("packet contains a credential-like or secret value")

    return packet


def validate_expected_commit(packet: dict[str, Any], expected_commit: Any) -> None:
    expected = validate_commit_sha(expected_commit, "expected commit")
    reviewed = packet["review"]["reviewedCommit"]
    if reviewed != expected:
        raise EvidenceValidationError(
            f"reviewed commit {reviewed} does not match expected commit {expected}"
        )


def display_path(path: Path) -> str:
    try:
        displayed = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        displayed = path.name
    if any(pattern.search(displayed) for pattern in SECRET_VALUE_PATTERNS):
        return "[REDACTED_PATH]"
    return displayed


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = path.read_bytes()
    except FileNotFoundError as exc:
        raise EvidenceValidationError(f"packet file not found: {display_path(path)}") from exc
    except OSError as exc:
        error = exc.strerror or exc.__class__.__name__
        raise EvidenceValidationError(f"could not read packet: {error}") from exc
    if len(payload) > MAX_PACKET_BYTES:
        raise EvidenceValidationError("packet exceeds the 1 MB safety limit")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except UnicodeDecodeError as exc:
        raise EvidenceValidationError("packet must be valid UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceValidationError(f"packet is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceValidationError("packet must be a JSON object")
    return value


def load_packet(path: Path) -> dict[str, Any]:
    value = load_json_object(path)
    return validate_packet(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a local-only Arc Testnet operator evidence packet."
    )
    parser.add_argument("packet", nargs="?", type=Path, default=DEFAULT_PACKET)
    parser.add_argument(
        "--expect-commit",
        help="Fail unless review.reviewedCommit equals this full lowercase commit SHA",
    )
    args = parser.parse_args()

    try:
        packet = load_packet(args.packet)
        if args.expect_commit is not None:
            validate_expected_commit(packet, args.expect_commit)
    except (EvidenceValidationError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "packet": display_path(args.packet),
                "schema": packet["schema"],
                "chainId": packet["network"]["chainId"],
                "decision": packet["decision"]["status"],
                "reviewedCommit": packet["review"]["reviewedCommit"],
                "expectedCommitChecked": args.expect_commit is not None,
                "commitMatchesExpected": True if args.expect_commit is not None else None,
                "transactionBroadcast": packet["controls"]["transactionBroadcast"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
