#!/usr/bin/env python3
"""Tests for the Arc Builder release packet generator.

All tests run the generator as a subprocess so that any import side effects or
stdout noise stay isolated. Every test uses a unique temporary directory under
the repository root.
"""

from __future__ import annotations

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
GENERATOR = ROOT / "scripts" / "generate_arc_release_packet.py"
FACTS = ROOT / "config" / "arc_testnet.facts.json"


class ReleasePacketGeneratorTests(unittest.TestCase):
    def run_generator(self, *extra_args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
        argv = [sys.executable, str(GENERATOR), *extra_args]
        return subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def temp_out_dir(self) -> Path:
        """Return a unique temp directory under the repo root."""
        temp_dir = tempfile.mkdtemp(prefix=".arc-packet-test-", dir=ROOT)
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        return Path(temp_dir)

    def test_generates_expected_files(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "all")
        self.assertEqual(result.returncode, 0, result.stderr)

        expected = {
            "arc-builder-doctor.md",
            "arc-testnet-facts.md",
            "readiness-checklist.md",
            "examples-index.md",
            "arc-testnet-facts.json",
            "release-packet.json",
        }
        found = {p.name for p in out.iterdir() if p.is_file()}
        self.assertTrue(expected.issubset(found), f"missing files: {expected - found}")

        # The generated facts JSON must match the canonical config file.
        generated_facts = json.loads((out / "arc-testnet-facts.json").read_text(encoding="utf-8"))
        canonical_facts = json.loads(FACTS.read_text(encoding="utf-8"))
        self.assertEqual(generated_facts, canonical_facts)

    def test_refuses_existing_dir_without_force(self) -> None:
        out = self.temp_out_dir()
        (out / "stale.txt").write_text("stale", encoding="utf-8")
        result = self.run_generator("--out", str(out), "--format", "all")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertIn("--force", result.stderr)

    def test_force_overwrites(self) -> None:
        out = self.temp_out_dir()
        (out / "stale.txt").write_text("stale", encoding="utf-8")
        result = self.run_generator("--out", str(out), "--force", "--format", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((out / "stale.txt").exists())
        self.assertTrue((out / "release-packet.json").exists())

    def test_rejects_output_outside_repo_root(self) -> None:
        # Use a sibling directory, not tempfile, so the test stays outside the
        # repo root even when CI overrides TMPDIR for isolation.
        outside = ROOT.parent / f"arc-packet-outside-{os.urandom(4).hex()}"
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        result = self.run_generator("--out", str(outside), "--force", "--format", "all")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside repo root", result.stderr)

    def test_json_schema_fields(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)

        packet = json.loads((out / "release-packet.json").read_text(encoding="utf-8"))
        self.assertEqual(packet["kind"], "arc_builder_release_packet")
        self.assertEqual(packet["schemaVersion"], 1)
        for key in (
            "generatedAt",
            "repoHead",
            "branch",
            "arcFacts",
            "outputs",
            "safetyBoundaries",
            "recommendedChecks",
            "disclaimer",
        ):
            self.assertIn(key, packet)

        self.assertIn("release-packet.json", packet["outputs"])
        self.assertIn("arc-testnet-facts.json", packet["outputs"])

    def test_packet_includes_arc_testnet_constants(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "all")
        self.assertEqual(result.returncode, 0, result.stderr)

        for name in ("arc-testnet-facts.md", "release-packet.json"):
            text = (out / name).read_text(encoding="utf-8")
            self.assertIn("5042002", text)
            self.assertIn("0x4cef52", text)

    def test_packet_has_no_unsafe_claims(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "all")
        self.assertEqual(result.returncode, 0, result.stderr)

        packet = json.loads((out / "release-packet.json").read_text(encoding="utf-8"))
        boundaries = packet["safetyBoundaries"]
        for key in (
            "walletConnected",
            "privateKeysAccepted",
            "signingEnabled",
            "transactionBroadcast",
            "custodyEnabled",
            "mainnetEnabled",
            "autonomousSpending",
            "secretsRead",
        ):
            self.assertIs(boundaries[key], False, key)
        self.assertIs(boundaries["localOnly"], True)
        self.assertIs(boundaries["networkChecksOptIn"], True)

        # Markdown must repeat the explicit non-perform declaration.
        readiness = (out / "readiness-checklist.md").read_text(encoding="utf-8")
        self.assertIn("target any mainnet", readiness)
        self.assertIn("claim live settlement", readiness)
        self.assertIn("sign or broadcast", readiness)

        # No production-ready / custody / mainnet claims.
        all_text = " ".join(
            (out / name).read_text(encoding="utf-8")
            for name in ("readiness-checklist.md", "examples-index.md", "arc-testnet-facts.md")
        )
        self.assertNotRegex(all_text.lower(), re.compile(r"\bproduction[\s\-]ready\b"))
        self.assertNotRegex(all_text.lower(), re.compile(r"\bmainnet\s+ready\b"))
        self.assertNotRegex(all_text.lower(), re.compile(r"\blive\s+settlement\s+proof\b"))

    def test_no_env_or_secrets_copied(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "all")
        self.assertEqual(result.returncode, 0, result.stderr)

        # None of the generated artifacts should mention reading .env or contain
        # obvious secret-key patterns.
        for path in out.iterdir():
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("PRIVATE KEY", text)
                self.assertNotIn("-----BEGIN", text)
                self.assertNotRegex(text, re.compile(r"gh[oprsu]_[A-Za-z0-9_]{16,}"))

        # The generator itself must not import or read .env files.
        generator_source = GENERATOR.read_text(encoding="utf-8")
        self.assertNotIn("dotenv", generator_source)
        self.assertNotIn("load_dotenv", generator_source)
        # Reading .env is not implemented; the only allowed .env mention is the
        # hard boundary in the readiness checklist.
        env_reads = re.findall(r'\.env[\s"\']', generator_source)
        self.assertEqual(env_reads, [])

    def test_markdown_format_only_generates_markdown(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "markdown")
        self.assertEqual(result.returncode, 0, result.stderr)

        files = {p.name for p in out.iterdir() if p.is_file()}
        self.assertIn("arc-builder-doctor.md", files)
        self.assertIn("readiness-checklist.md", files)
        self.assertNotIn("release-packet.json", files)
        self.assertNotIn("arc-testnet-facts.json", files)

    def test_json_format_only_generates_json(self) -> None:
        out = self.temp_out_dir()
        result = self.run_generator("--out", str(out), "--force", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)

        files = {p.name for p in out.iterdir() if p.is_file()}
        self.assertIn("release-packet.json", files)
        self.assertIn("arc-testnet-facts.json", files)
        self.assertNotIn("arc-builder-doctor.md", files)


if __name__ == "__main__":
    unittest.main()
