#!/usr/bin/env python3
"""Failure-path tests for repository workflow security validation."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_repo.py"
PINNED_SETUP_PYTHON = "a309ff8b426b58ec0e2a45f0f869d46889d02405"
PINNED_SETUP_NODE = "48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"


def load_validator():
    spec = importlib.util.spec_from_file_location("repo_validator_under_test", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workflow(permissions: str, trigger: str = "workflow_dispatch:", setup_node_ref: str = PINNED_SETUP_NODE) -> str:
    return f"""name: test
on:
  {trigger}
permissions:
{permissions}
jobs:
  test:
    steps:
      - uses: actions/setup-python@{PINNED_SETUP_PYTHON}
        with:
          python-version: "3.12"
      - uses: actions/setup-node@{setup_node_ref}
        with:
          node-version: "22"
      - run: python scripts/test_all.py
"""


class WorkflowSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.temp = tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.validator.ROOT = self.root
        self.write_workflows()

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_workflows(self) -> None:
        self.write(".github/workflows/validate.yml", workflow("  contents: read"))
        self.write(
            ".github/workflows/pages.yml",
            workflow("  contents: read\n  pages: write\n  id-token: write"),
        )

    def test_current_runtime_and_permission_contract_passes(self) -> None:
        self.validator.validate_workflow_security()

    def test_unpinned_action_ref_fails_closed(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: read", setup_node_ref="v6"),
        )
        with self.assertRaisesRegex(SystemExit, "full commit SHA"):
            self.validator.validate_workflow_security()

    def test_commented_runtime_markers_cannot_spoof_active_steps(self) -> None:
        spoofed = workflow("  contents: read")
        spoofed = spoofed.replace(
            f"      - uses: actions/setup-node@{PINNED_SETUP_NODE}",
            f"      # uses: actions/setup-node@{PINNED_SETUP_NODE}",
        ).replace(
            '          node-version: "22"',
            '          # node-version: "22"',
        )
        self.write(".github/workflows/validate.yml", spoofed)
        with self.assertRaisesRegex(SystemExit, "missing active runtime setup action"):
            self.validator.validate_workflow_security()

    def test_privileged_trigger_fails_closed(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: read", trigger="pull_request_target:"),
        )
        with self.assertRaisesRegex(SystemExit, "forbidden privileged workflow trigger"):
            self.validator.validate_workflow_security()

    def test_validation_write_permission_fails_closed(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: write"),
        )
        with self.assertRaisesRegex(SystemExit, "permissions must be exactly"):
            self.validator.validate_workflow_security()

    def test_validation_additional_write_permission_fails_closed(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: read\n  issues: write"),
        )
        with self.assertRaisesRegex(SystemExit, "permissions must be exactly"):
            self.validator.validate_workflow_security()

    def test_permission_shorthand_fails_closed(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: read").replace(
                "permissions:\n  contents: read",
                "permissions: write-all\n# contents: read",
            ),
        )
        with self.assertRaisesRegex(SystemExit, "explicit top-level map"):
            self.validator.validate_workflow_security()

    def test_inline_permission_map_cannot_be_spoofed_by_other_yaml(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: read").replace(
                "permissions:\n  contents: read",
                "permissions: { contents: write }\nenv:\n  contents: read",
            ),
        )
        with self.assertRaisesRegex(SystemExit, "explicit top-level map"):
            self.validator.validate_workflow_security()

    def test_job_level_permission_block_fails_closed(self) -> None:
        self.write(
            ".github/workflows/validate.yml",
            workflow("  contents: read").replace(
                "    steps:",
                "    permissions:\n      issues: write\n    steps:",
            ),
        )
        with self.assertRaisesRegex(SystemExit, "exactly one permissions block"):
            self.validator.validate_workflow_security()

    def test_pages_additional_read_permission_fails_closed(self) -> None:
        self.write(
            ".github/workflows/pages.yml",
            workflow("  contents: read\n  pages: write\n  id-token: write\n  packages: read"),
        )
        with self.assertRaisesRegex(SystemExit, "permissions must be exactly"):
            self.validator.validate_workflow_security()


if __name__ == "__main__":
    unittest.main()
