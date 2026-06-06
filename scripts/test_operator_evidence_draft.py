#!/usr/bin/env python3
"""Regression tests for the safe operator evidence draft generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from generate_operator_evidence_draft import build_draft
from validate_operator_evidence import EvidenceValidationError, validate_packet

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_operator_evidence_draft.py"
REVIEWED_COMMIT = "2" * 40


class OperatorEvidenceDraftTests(unittest.TestCase):
    def test_draft_is_commit_bound_and_fail_closed(self) -> None:
        draft = build_draft(REVIEWED_COMMIT)
        self.assertEqual(draft["review"]["reviewedCommit"], REVIEWED_COMMIT)
        self.assertEqual(draft["packetStatus"], "draft_operator_evidence")
        self.assertEqual(draft["decision"]["status"], "blocked_pending_separate_guarded_pr")
        self.assertFalse(draft["controls"]["transactionBroadcast"])
        self.assertFalse(draft["controls"]["signingEnabled"])
        self.assertFalse(draft["controls"]["noSecretsObserved"])
        self.assertTrue(draft["controls"]["ethSendTransactionForbidden"])
        evidence_gates = [
            value
            for key, value in draft["evidence"].items()
            if key.endswith("Reviewed") or key.endswith("Passed")
        ]
        self.assertTrue(all(value is False for value in evidence_gates))

    def test_draft_intentionally_fails_strict_validation(self) -> None:
        with self.assertRaisesRegex(
            EvidenceValidationError,
            "packetStatus must be local_operator_evidence",
        ):
            validate_packet(build_draft(REVIEWED_COMMIT))

    def test_cli_creates_ignored_local_draft(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "review.operator-evidence.local.json"
            relative = output.relative_to(ROOT)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--reviewed-commit",
                    REVIEWED_COMMIT,
                    "--output",
                    str(relative),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["review"]["reviewedCommit"], REVIEWED_COMMIT)
            self.assertEqual(packet["packetStatus"], "draft_operator_evidence")
            self.assertIn('"strictValidationReady": false', completed.stdout)
            self.assertIn('"manualSecretReviewComplete": false', completed.stdout)
            ignored = subprocess.run(
                ["git", "check-ignore", "--quiet", str(relative)],
                cwd=ROOT,
                timeout=10,
            )
            self.assertEqual(ignored.returncode, 0)

    def test_cli_refuses_to_overwrite_existing_file(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "review.operator-evidence.local.json"
            output.write_text("keep-me", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--reviewed-commit",
                    REVIEWED_COMMIT,
                    "--output",
                    str(output.relative_to(ROOT)),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("refusing to overwrite", completed.stdout)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep-me")

    def test_cli_rejects_output_outside_repository(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--reviewed-commit",
                REVIEWED_COMMIT,
                "--output",
                "../outside.operator-evidence.local.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("repository-relative", completed.stdout)

    def test_cli_requires_local_draft_suffix(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--reviewed-commit",
                REVIEWED_COMMIT,
                "--output",
                "operator-evidence.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn(".operator-evidence.local.json", completed.stdout)

    def test_cli_rejects_git_metadata_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--reviewed-commit",
                REVIEWED_COMMIT,
                "--output",
                ".GIT/review.operator-evidence.local.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("must not be inside .git", completed.stdout)

    def test_cli_rejects_malformed_reviewed_commit(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--reviewed-commit",
                "HEAD",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("full lowercase commit SHA", completed.stdout)


if __name__ == "__main__":
    unittest.main()
