#!/usr/bin/env python3
"""Tests for the repository-owned pre-commit path guard."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "pre_commit_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("arc_pre_commit_guard_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = load_guard()


class PathPolicyTests(unittest.TestCase):
    def test_blocks_generated_and_local_directories(self) -> None:
        for path in (
            "dist/arc_builder_kit.whl",
            "build/lib/module.py",
            "graphify-out/graph.json",
            ".graphify-out/cache.json",
            ".hermes/plans/local.md",
            ".arc-release-packet/report.json",
            ".arc-test-run/output.txt",
            "arc_builder_kit.egg-info/PKG-INFO",
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(guard.blocked_reason(path))

    def test_blocks_secret_like_names(self) -> None:
        for path in (".env", ".env.local", "keys/deployer.pem", "wallet.p12"):
            with self.subTest(path=path):
                self.assertIsNotNone(guard.blocked_reason(path))

    def test_allows_reviewed_source_and_env_examples(self) -> None:
        for path in (
            ".env.example",
            "examples/x402-local-challenge-server/.env.example",
            "arc_builder_kit/cli.py",
            "docs/builder-tooling.md",
            ".graphifyignore",
        ):
            with self.subTest(path=path):
                self.assertIsNone(guard.blocked_reason(path))

    def test_managed_hook_is_local_and_dependency_free(self) -> None:
        hook = (ROOT / "scripts/hooks/pre-commit").read_text(encoding="utf-8")
        self.assertIn("arc-builder-managed-hook:v1", hook)
        self.assertIn("scripts/pre_commit_guard.py", hook)
        self.assertIn("scripts/scan_for_secrets.py", hook)
        self.assertIn("for candidate in python3 python", hook)
        self.assertIn("sys.version_info < (3, 10)", hook)
        self.assertNotIn("graphify ", hook)
        self.assertNotIn("curl ", hook)

    def test_graphify_outputs_are_ignored(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        graphifyignore = (ROOT / ".graphifyignore").read_text(encoding="utf-8")
        self.assertIn("graphify-out/", gitignore)
        self.assertIn("graphify-out/", graphifyignore)


if __name__ == "__main__":
    unittest.main()
