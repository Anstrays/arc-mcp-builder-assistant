#!/usr/bin/env python3
"""Regression tests for the Arc Testnet operator evidence packet."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from validate_operator_evidence import DEFAULT_PACKET, EvidenceValidationError, validate_packet

ROOT = Path(__file__).resolve().parents[1]


def example_packet() -> dict:
    return json.loads(DEFAULT_PACKET.read_text(encoding="utf-8"))


class OperatorEvidenceTests(unittest.TestCase):
    def test_example_packet_passes(self) -> None:
        packet = validate_packet(example_packet())
        self.assertEqual(packet["network"]["chainId"], 5042002)
        self.assertFalse(packet["controls"]["transactionBroadcast"])

    def test_cli_validates_default_packet(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_operator_evidence.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn('"ok": true', completed.stdout)
        self.assertIn('"transactionBroadcast": false', completed.stdout)
        self.assertIn('"packet": "examples/arc-testnet-operator-evidence/evidence.example.json"', completed.stdout)
        self.assertIn('"expectedCommitChecked": false', completed.stdout)
        self.assertIn('"commitMatchesExpected": null', completed.stdout)
        self.assertNotIn(str(ROOT), completed.stdout)

    def test_cli_accepts_matching_expected_commit(self) -> None:
        reviewed_commit = example_packet()["review"]["reviewedCommit"]
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_operator_evidence.py"),
                str(DEFAULT_PACKET),
                "--expect-commit",
                reviewed_commit,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn('"commitMatchesExpected": true', completed.stdout)
        self.assertIn(f'"reviewedCommit": "{reviewed_commit}"', completed.stdout)

    def test_cli_rejects_mismatched_expected_commit(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_operator_evidence.py"),
                str(DEFAULT_PACKET),
                "--expect-commit",
                "1" * 40,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("does not match expected commit", completed.stdout)

    def test_cli_rejects_malformed_expected_commit(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_operator_evidence.py"),
                str(DEFAULT_PACKET),
                "--expect-commit",
                "HEAD",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("expected commit must be a full lowercase commit SHA", completed.stdout)

    def test_wrong_chain_fails_closed(self) -> None:
        packet = example_packet()
        packet["network"]["chainId"] = 1
        with self.assertRaisesRegex(EvidenceValidationError, "Arc Testnet"):
            validate_packet(packet)

    def test_placeholder_commit_fails_closed(self) -> None:
        packet = example_packet()
        packet["review"]["reviewedCommit"] = "0" * 40
        with self.assertRaisesRegex(EvidenceValidationError, "full lowercase commit SHA"):
            validate_packet(packet)

    def test_non_string_commit_fails_closed(self) -> None:
        packet = example_packet()
        packet["review"]["reviewedCommit"] = 6540
        with self.assertRaisesRegex(EvidenceValidationError, "full lowercase commit SHA"):
            validate_packet(packet)

    def test_broadcast_enabled_fails_closed(self) -> None:
        packet = example_packet()
        packet["controls"]["transactionBroadcast"] = True
        with self.assertRaisesRegex(EvidenceValidationError, "transactionBroadcast must be false"):
            validate_packet(packet)

    def test_unknown_field_fails_closed(self) -> None:
        packet = example_packet()
        packet["controls"]["unexpectedApproval"] = True
        with self.assertRaisesRegex(EvidenceValidationError, "unknown fields"):
            validate_packet(packet)

    def test_missing_evidence_fails_closed(self) -> None:
        packet = example_packet()
        del packet["evidence"]["testsPassed"]
        with self.assertRaisesRegex(EvidenceValidationError, "missing required fields"):
            validate_packet(packet)

    def test_decision_cannot_approve_live_send(self) -> None:
        packet = example_packet()
        packet["decision"]["status"] = "approved_for_live_send"
        with self.assertRaisesRegex(EvidenceValidationError, "blocked_pending_separate_guarded_pr"):
            validate_packet(packet)

    def test_non_repository_reference_fails_closed(self) -> None:
        packet = copy.deepcopy(example_packet())
        packet["evidence"]["references"] = ["../outside-repository.txt"]
        with self.assertRaisesRegex(EvidenceValidationError, "repository-relative"):
            validate_packet(packet)

    def test_duplicate_reference_fails_closed(self) -> None:
        packet = copy.deepcopy(example_packet())
        packet["evidence"]["references"].append(packet["evidence"]["references"][0])
        with self.assertRaisesRegex(EvidenceValidationError, "must not contain duplicates"):
            validate_packet(packet)

    def test_credential_like_value_fails_closed(self) -> None:
        packet = example_packet()
        packet["decision"]["reason"] = "Do not include " + "ghp_" + ("a" * 24) + " in evidence."
        with self.assertRaisesRegex(EvidenceValidationError, "credential-like"):
            validate_packet(packet)

    def test_cli_missing_packet_has_clear_error(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_operator_evidence.py"),
                "missing-operator-evidence.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn('"ok": false', completed.stdout)
        self.assertIn("packet file not found", completed.stdout)


if __name__ == "__main__":
    unittest.main()
