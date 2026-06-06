#!/usr/bin/env python3
"""Failure-path tests for the safe-scope completion checker."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_completion.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("completion_checker_under_test", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompletionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_checker()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checker.ROOT = self.root

    def write(self, relative: str, text: str = "") -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_required_surfaces_fail_closed_when_one_is_missing(self) -> None:
        with self.assertRaisesRegex(SystemExit, "missing required surface"):
            self.checker.check_required_surfaces()

    def test_canonical_suite_rejects_unlisted_regression_script(self) -> None:
        self.write("scripts/test_all.py", "scripts/validate_repo.py\nscripts/check_completion.py\n")
        self.write("scripts/test_new_behavior.py")

        with self.assertRaisesRegex(SystemExit, "test_new_behavior.py"):
            self.checker.check_canonical_suite()

    def test_safety_boundary_rejects_mainnet_enabled_example(self) -> None:
        self.write(
            "docs/completion-contract.md",
            "\n".join(
                (
                    "no private keys",
                    "no wallet connection",
                    "no custody",
                    "no mainnet support",
                    "no transaction broadcast",
                )
            ),
        )
        self.write("README.md", "no private keys\nno mainnet\nno autonomous spending\n")
        self.write(
            "examples/x402-local-challenge-server/server.py",
            '"transactionBroadcast": False\nX402_DEMO_MAINNET_ENABLED\n',
        )
        self.write(".gitignore", ".env\n*.operator-evidence.local.json\n")
        self.write(".env.example", "X402_DEMO_MAINNET_ENABLED=true\n")

        with self.assertRaisesRegex(SystemExit, "must keep x402 mainnet disabled"):
            self.checker.check_safety_boundary()


if __name__ == "__main__":
    unittest.main()

