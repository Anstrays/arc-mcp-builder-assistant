#!/usr/bin/env python3
"""Tests for scripts/arc_builder_cli.py.

Standard-library unittest only. No network calls.
"""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "arc_builder_cli.py"


def load_cli():
    spec = importlib.util.spec_from_file_location("arc_builder_cli_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cli = load_cli()


class ParserTests(unittest.TestCase):
    def test_all_subcommands_parse(self) -> None:
        for command in ("doctor", "validate", "templates", "scaffold", "facts", "manifest", "release-packet", "mcp"):
            with self.subTest(command=command):
                if command == "scaffold":
                    cli.build_parser().parse_args([command, "payment-intent-starter", "./out"])
                elif command == "release-packet":
                    cli.build_parser().parse_args([command, "--output", "./out"])
                else:
                    cli.build_parser().parse_args([command])

    def test_doctor_flags(self) -> None:
        args = cli.build_parser().parse_args(["doctor", "--full", "--include-arc-rpc"])
        self.assertTrue(args.full)
        self.assertTrue(args.include_arc_rpc)
        self.assertFalse(args.include_public_site)


class TemplateTests(unittest.TestCase):
    def test_list_templates_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = cli.cmd_templates(cli.build_parser().parse_args(["templates", "--json"]))
        self.assertEqual(rc, 0)
        data = json.loads(stdout.getvalue())
        self.assertIn("payment-intent-starter", data["templates"])
        self.assertIn("x402-agent-starter", data["templates"])
        self.assertIn("job-escrow-starter", data["templates"])

    def test_list_templates_human(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = cli.cmd_templates(cli.build_parser().parse_args(["templates"]))
        self.assertEqual(rc, 0)
        self.assertIn("payment-intent-starter", stdout.getvalue())


class ScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="arc-builder-cli-test-")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scaffold_payment_intent(self) -> None:
        out = Path(self.tmp) / "my-demo"
        rc = cli.cmd_scaffold(cli.build_parser().parse_args(["scaffold", "payment-intent-starter", str(out)]))
        self.assertEqual(rc, 0)
        self.assertTrue((out / "README.md").exists())
        self.assertTrue((out / "index.html").exists())

    def test_scaffold_unknown_fails(self) -> None:
        out = Path(self.tmp) / "bad"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            rc = cli.main(["scaffold", "not-a-template", str(out)])
        self.assertNotEqual(rc, 0)
        self.assertIn("unknown template", stderr.getvalue())

    def test_scaffold_existing_without_force_fails(self) -> None:
        out = Path(self.tmp) / "dup"
        out.mkdir()
        (out / "keep.txt").write_text("keep")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            rc = cli.main(["scaffold", "payment-intent-starter", str(out)])
        self.assertNotEqual(rc, 0)
        self.assertEqual((out / "keep.txt").read_text(), "keep")

    def test_scaffold_force_overwrites(self) -> None:
        out = Path(self.tmp) / "dup"
        out.mkdir()
        (out / "keep.txt").write_text("keep")
        rc = cli.main(["scaffold", "payment-intent-starter", str(out), "--force"])
        self.assertEqual(rc, 0)
        self.assertFalse((out / "keep.txt").exists())
        self.assertTrue((out / "index.html").exists())


class FactsTests(unittest.TestCase):
    def test_facts_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = cli.cmd_facts(cli.build_parser().parse_args(["facts", "--json"]))
        self.assertEqual(rc, 0)
        data = json.loads(stdout.getvalue())
        self.assertIn("chainId", data["network"])


class OrchestratorTests(unittest.TestCase):
    def test_doctor_runs_as_script(self) -> None:
        completed = mock.Mock(returncode=0, stdout='{"status":"pass"}', stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            rc = cli.cmd_doctor(cli.build_parser().parse_args(["doctor"]))
        self.assertEqual(rc, 0)
        mocked.assert_called_once()
        self.assertIn("arc_builder_doctor.py", str(mocked.call_args[0][0][1]))
        self.assertIn("--json", mocked.call_args[0][0])

    def test_validate_runs_as_script(self) -> None:
        completed = mock.Mock(returncode=0, stdout="validation passed", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            rc = cli.cmd_validate(cli.build_parser().parse_args(["validate"]))
        self.assertEqual(rc, 0)
        mocked.assert_called_once()
        self.assertIn("validate_repo.py", str(mocked.call_args[0][0][1]))

    def test_manifest_runs_x402_server(self) -> None:
        completed = mock.Mock(returncode=0, stdout="{}", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            rc = cli.cmd_manifest(cli.build_parser().parse_args(["manifest"]))
        self.assertEqual(rc, 0)
        mocked.assert_called_once()
        self.assertIn("server.py", str(mocked.call_args[0][0][1]))
        self.assertIn("--print-manifest", mocked.call_args[0][0])

    def test_release_packet_runs_generator(self) -> None:
        completed = mock.Mock(returncode=0, stdout="generated", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mocked:
            rc = cli.cmd_release_packet(cli.build_parser().parse_args(["release-packet", "--output", "./out"]))
        self.assertEqual(rc, 0)
        mocked.assert_called_once()
        self.assertIn("generate_arc_release_packet.py", str(mocked.call_args[0][0][1]))
        self.assertIn("--out", mocked.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
