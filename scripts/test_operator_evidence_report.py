#!/usr/bin/env python3
"""Regression tests for the read-only operator evidence readiness report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from generate_operator_evidence_draft import build_draft
from validate_operator_evidence import DEFAULT_PACKET

ROOT = Path(__file__).resolve().parents[1]
REPORTER = ROOT / "scripts" / "report_operator_evidence.py"
REVIEWED_COMMIT = "3" * 40


def run_report(path: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPORTER), str(path), *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )


class OperatorEvidenceReportTests(unittest.TestCase):
    def test_complete_example_is_strictly_ready(self) -> None:
        completed = run_report(DEFAULT_PACKET)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["strictValidationReady"])
        self.assertEqual(report["readiness"], "strict_validation_ready")
        self.assertEqual(report["gaps"], [])
        self.assertFalse(report["liveSendApproved"])

    def test_draft_lists_all_incomplete_gates(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "draft.operator-evidence.local.json"
            path.write_text(json.dumps(build_draft(REVIEWED_COMMIT)), encoding="utf-8")
            completed = run_report(path, "--expect-commit", REVIEWED_COMMIT)

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertFalse(report["strictValidationReady"])
        self.assertEqual(report["readiness"], "incomplete_or_unsafe")
        self.assertIn("packetStatus", report["gaps"])
        self.assertIn("controls.noSecretsObserved", report["gaps"])
        self.assertIn("evidence.testsPassed", report["gaps"])
        self.assertTrue(report["commitMatchesExpected"])
        self.assertFalse(report["liveSendApproved"])

    def test_expected_commit_mismatch_is_reported(self) -> None:
        completed = run_report(DEFAULT_PACKET, "--expect-commit", "4" * 40)
        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn("review.reviewedCommit", report["gaps"])
        self.assertFalse(report["commitMatchesExpected"])

    def test_malformed_expected_commit_exits_two(self) -> None:
        completed = run_report(DEFAULT_PACKET, "--expect-commit", "HEAD")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("full lowercase commit SHA", completed.stdout)

    def test_malformed_json_exits_two(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "broken.operator-evidence.local.json"
            path.write_text("{broken", encoding="utf-8")
            completed = run_report(path)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("not valid JSON", completed.stdout)

    def test_credential_like_value_is_reported_without_echoing_it(self) -> None:
        secret = "ghp_" + ("z" * 24)
        packet = json.loads(DEFAULT_PACKET.read_text(encoding="utf-8"))
        packet["decision"]["reason"] = f"Unsafe review note contains {secret}"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "secret.operator-evidence.local.json"
            path.write_text(json.dumps(packet), encoding="utf-8")
            completed = run_report(path)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("credentialLikeValueDetected", completed.stdout)
        self.assertNotIn(secret, completed.stdout)

    def test_credential_like_key_is_reported_without_echoing_it(self) -> None:
        secret = "ghp_" + ("k" * 24)
        packet = json.loads(DEFAULT_PACKET.read_text(encoding="utf-8"))
        packet[secret] = "unsafe unknown field"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "secret-key.operator-evidence.local.json"
            path.write_text(json.dumps(packet), encoding="utf-8")
            completed = run_report(path)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("credentialLikeValueDetected", completed.stdout)
        self.assertNotIn(secret, completed.stdout)

    def test_report_does_not_expose_absolute_workspace_path(self) -> None:
        completed = run_report(DEFAULT_PACKET)
        self.assertNotIn(str(ROOT), completed.stdout)

    def test_report_redacts_credential_like_filename(self) -> None:
        secret = "ghp_" + ("p" * 24)
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / f"{secret}.operator-evidence.local.json"
            path.write_text(DEFAULT_PACKET.read_text(encoding="utf-8"), encoding="utf-8")
            completed = run_report(path)
        self.assertEqual(completed.returncode, 0)
        self.assertIn("[REDACTED_PATH]", completed.stdout)
        self.assertNotIn(secret, completed.stdout)


if __name__ == "__main__":
    unittest.main()
