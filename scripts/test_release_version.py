#!/usr/bin/env python3
"""Tests for fail-closed release version validation."""

from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_release_version.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("release_version_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_checker()


class ReleaseVersionTests(unittest.TestCase):
    def test_current_release_tag_matches_all_surfaces(self) -> None:
        self.assertEqual(checker.validate_release_tag("v0.3.0"), "0.3.0")

    def test_missing_v_prefix_fails(self) -> None:
        with self.assertRaises(checker.ReleaseVersionError):
            checker.validate_release_tag("0.2.1")

    def test_malformed_version_fails(self) -> None:
        with self.assertRaises(checker.ReleaseVersionError):
            checker.validate_release_tag("vnext")

    def test_repository_version_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as temp:
            fixture = Path(temp)
            for relative in (
                "pyproject.toml",
                "arc_builder_kit/__init__.py",
                "scripts/arc_builder_cli.py",
                "scripts/arc_builder_mcp_server.py",
            ):
                source = ROOT / relative
                target = fixture / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            package = fixture / "arc_builder_kit/__init__.py"
            package.write_text(
                package.read_text(encoding="utf-8").replace("0.2.1", "0.3.0"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(checker.ReleaseVersionError, "package=0.3.0"):
                checker.validate_release_tag("v0.2.1", fixture)


if __name__ == "__main__":
    unittest.main()
