#!/usr/bin/env python3
"""Dependency-free tests for the installable Arc Builder Kit layout."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SOURCE = ROOT / "arc_builder_kit"
BUILD_SUPPORT_PATH = ROOT / "build_support.py"


def load_build_support():
    spec = importlib.util.spec_from_file_location("arc_build_support_under_test", BUILD_SUPPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {BUILD_SUPPORT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_support = load_build_support()


class ResourceBuildTests(unittest.TestCase):
    def test_reviewed_resources_include_all_public_surfaces(self) -> None:
        relative = {
            path.relative_to(ROOT).as_posix()
            for path in build_support.iter_package_resources(ROOT)
        }
        self.assertGreaterEqual(len(relative), 44)
        self.assertIn("config/arc_testnet.facts.json", relative)
        self.assertIn("templates/payment-intent-starter/index.html", relative)
        self.assertIn("examples/payment-intent-receipt-matcher/matcher.js", relative)
        self.assertIn("examples/x402-local-challenge-server/.env.example", relative)

    def test_secret_like_resource_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="arc-package-resource-") as temp:
            source = Path(temp)
            for directory in build_support.RESOURCE_DIRS:
                (source / directory).mkdir()
            (source / "examples" / ".env").write_text("blocked fixture\n", encoding="utf-8")
            with self.assertRaises(build_support.ResourceBuildError):
                build_support.iter_package_resources(source)

    def test_unknown_resource_type_requires_review(self) -> None:
        with tempfile.TemporaryDirectory(prefix="arc-package-resource-") as temp:
            source = Path(temp)
            for directory in build_support.RESOURCE_DIRS:
                (source / directory).mkdir()
            (source / "templates" / "payload.bin").write_bytes(b"unreviewed")
            with self.assertRaises(build_support.ResourceBuildError):
                build_support.iter_package_resources(source)

    def test_manifest_and_build_hook_do_not_rely_on_symlinks(self) -> None:
        manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        setup = (ROOT / "setup.py").read_text(encoding="utf-8")
        self.assertIn("include config/arc_testnet.facts.json", manifest)
        self.assertIn("examples/x402-local-challenge-server/.env.example", manifest)
        self.assertIn("copy_package_resources", setup)
        for name in build_support.RESOURCE_DIRS:
            self.assertFalse((PACKAGE_SOURCE / name).exists(), f"stale package symlink: {name}")

    def test_source_and_package_entry_points_share_release_version(self) -> None:
        _version = re.search(r'__version__\s*=\s*"([^"]+)"', (PACKAGE_SOURCE / "__init__.py").read_text()).group(1)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{_version}"', pyproject)
        self.assertIn("from arc_builder_kit.cli import main", (ROOT / "scripts/arc_builder_cli.py").read_text(encoding="utf-8"))
        self.assertIn("from arc_builder_kit.mcp_server import main", (ROOT / "scripts/arc_builder_mcp_server.py").read_text(encoding="utf-8"))
        self.assertIn('requires-python = ">=3.10"', pyproject)
        self.assertNotIn('"Programming Language :: Python :: 3.9"', pyproject)


class InstalledLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.mkdtemp(prefix="arc-installed-layout-")
        cls.temp_root = Path(cls.temp)
        cls.stage = cls.temp_root / "site-packages"
        cls.package = cls.stage / "arc_builder_kit"
        cls.workspace = cls.temp_root / "workspace"
        cls.workspace.mkdir(parents=True)
        cls.package.mkdir(parents=True)
        for source in PACKAGE_SOURCE.glob("*.py"):
            shutil.copy2(source, cls.package / source.name)
        build_support.copy_package_resources(ROOT, cls.package)
        cls.env = os.environ.copy()
        cls.env["PYTHONPATH"] = str(cls.stage)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temp, ignore_errors=True)

    def run_cli(
        self,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "arc_builder_kit", *args],
            cwd=self.workspace,
            env=env or self.env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def test_version_templates_facts_and_manifest_work(self) -> None:
        version = self.run_cli("--version")
        self.assertEqual(version.returncode, 0, version.stderr)
        _version = re.search(r'__version__\s*=\s*"([^"]+)"', (PACKAGE_SOURCE / "__init__.py").read_text()).group(1)
        self.assertIn(_version, version.stdout)

        templates = self.run_cli("templates", "--json")
        self.assertEqual(templates.returncode, 0, templates.stderr)
        self.assertIn("payment-intent-starter", json.loads(templates.stdout)["templates"])

        facts = self.run_cli("facts", "--json")
        self.assertEqual(facts.returncode, 0, facts.stderr)
        self.assertEqual(json.loads(facts.stdout)["network"]["chainId"], 5042002)

        manifest = self.run_cli("manifest")
        self.assertEqual(manifest.returncode, 0, manifest.stderr)
        manifest_payload = json.loads(manifest.stdout)
        self.assertEqual(manifest_payload["network"]["chainId"], 5042002)
        self.assertFalse(manifest_payload["safety"]["mainnetEnabled"])

    def test_installed_wallet_sdk_plan_is_secret_safe(self) -> None:
        plan = self.run_cli("wallet", "sdk-plan", "--json", "--account-type", "SCA", "--count", "2")
        self.assertEqual(plan.returncode, 0, plan.stderr)
        payload = json.loads(plan.stdout)
        self.assertEqual(payload["manifest"]["blockchain"], "ARC-TESTNET")
        self.assertEqual(payload["plan"]["wallets"]["accountType"], "SCA")
        self.assertFalse(payload["manifest"]["safety"]["liveSdkExecution"])

        env = self.env.copy()
        env["CIRCLE_API_KEY"] = "secret-value"
        env["CIRCLE_ENTITY_SECRET"] = "secret-entity"
        check = self.run_cli("wallet", "env-check", "--json", env=env)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("[REDACTED]", check.stdout)
        self.assertNotIn("secret-value", check.stdout)
        self.assertNotIn("secret-entity", check.stdout)

    def test_installed_validate_and_doctor_pass(self) -> None:
        validation = self.run_cli("validate")
        self.assertEqual(validation.returncode, 0, validation.stderr)
        self.assertIn("installed package validation passed", validation.stdout)

        doctor = self.run_cli("doctor")
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        report = json.loads(doctor.stdout)
        self.assertIn(report["overallStatus"], ("pass", "warn"))
        ids = {check["id"] for check in report["checks"]}
        self.assertIn("package.integrity", ids)

    def test_release_packet_defaults_to_workspace(self) -> None:
        result = self.run_cli("release-packet", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = self.workspace / ".arc-release-packet" / "release-packet.json"
        self.assertTrue(packet.is_file())
        payload = json.loads(packet.read_text(encoding="utf-8"))
        self.assertFalse(payload["safetyBoundaries"]["mainnetEnabled"])

    def test_release_packet_force_cannot_delete_outside_workspace(self) -> None:
        outside = self.temp_root / "outside"
        outside.mkdir(exist_ok=True)
        sentinel = outside / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        result = self.run_cli("release-packet", "--output", str(outside), "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(sentinel.is_file())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_mcp_server_reports_package_version_and_tools(self) -> None:
        requests = "\n".join(
            (
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            )
        ) + "\n"
        result = subprocess.run(
            [sys.executable, "-m", "arc_builder_kit.mcp_server"],
            cwd=self.workspace,
            env=self.env,
            input=requests,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        _version = re.search(r'__version__\s*=\s*"([^"]+)"', (PACKAGE_SOURCE / "__init__.py").read_text()).group(1)
        self.assertEqual(responses[0]["result"]["serverInfo"]["version"], _version)
        tool_names = {tool["name"] for tool in responses[1]["result"]["tools"]}
        self.assertIn("x402_paid_request", tool_names)
        self.assertIn("x402_fetch_challenge", tool_names)
        self.assertIn("x402_verify_receipt", tool_names)
        self.assertIn("wallet_status", tool_names)
        self.assertIn("wallet_balance", tool_names)
        self.assertIn("wallet_prepare_send", tool_names)
        self.assertEqual(len(tool_names), 14)

    def test_mainnet_override_remains_blocked(self) -> None:
        env = self.env.copy()
        env["X402_DEMO_MAINNET_ENABLED"] = "true"
        result = self.run_cli("manifest", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MAINNET", result.stderr.upper())


if __name__ == "__main__":
    unittest.main()
