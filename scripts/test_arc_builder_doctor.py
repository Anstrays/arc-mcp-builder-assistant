#!/usr/bin/env python3
"""Safety-boundary tests for the Arc Builder Doctor orchestrator.

Standard-library unittest only. Credential-shaped fixtures are assembled at
runtime so this source never contains a literal secret.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "arc_builder_doctor.py"


def load_doctor():
    spec = importlib.util.spec_from_file_location("arc_builder_doctor_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_doctor()


def fake_child(returncode: int = 0, stdout: str = "", stderr: str = "", timed_out: bool = False):
    return doctor.ChildResult(returncode=returncode, stdout=stdout, stderr=stderr, timed_out=timed_out)


def canned_run_child(argv, timeout):
    """A local-only stand-in: success for version probes and python scripts."""
    if any(str(part).endswith("--version") or part == "--version" for part in argv):
        return fake_child(stdout="v22.0.0")
    return fake_child(stdout="passed")


def network_blocker(*args, **kwargs):
    raise AssertionError("network call attempted in a context that must stay offline")


class RedactionTests(unittest.TestCase):
    def test_redacts_credential_shapes(self) -> None:
        token = "gh" + "p_" + ("A" * 32)
        aws = "AKIA" + ("B" * 16)
        hexblob = "ab" * 40
        bearer = "Bearer " + ("x" * 24)
        keyval = "api" + "_key=" + ("Z" * 18)
        for raw in (token, aws, hexblob, bearer, keyval):
            redacted = doctor.redact(raw)
            self.assertIn(doctor._REDACTED, redacted, raw[:6])
            self.assertNotIn(raw, redacted)

    def test_safe_detail_bounds_and_collapses(self) -> None:
        detail = doctor.safe_detail("line one\nline two\t\tmore   spaces", limit=240)
        self.assertNotIn("\n", detail)
        self.assertNotIn("\t", detail)
        long_detail = doctor.safe_detail("x" * 1000, limit=50)
        self.assertLessEqual(len(long_detail), 50)
        self.assertTrue(long_detail.endswith("..."))


class CheckHelperTests(unittest.TestCase):
    def test_make_check_rejects_unknown_status(self) -> None:
        with self.assertRaises(ValueError):
            doctor.make_check("x.y", "X", "bogus", "detail")

    def test_make_check_redacts_detail(self) -> None:
        secret = "gh" + "p_" + ("Q" * 30)
        check = doctor.make_check("x.y", "X", "pass", f"leaked {secret}")
        self.assertNotIn(secret, check["detail"])

    def test_overall_status_precedence(self) -> None:
        self.assertEqual(doctor.overall_status([{"status": "pass"}]), "pass")
        self.assertEqual(
            doctor.overall_status([{"status": "pass"}, {"status": "warn"}]), "warn"
        )
        self.assertEqual(
            doctor.overall_status([{"status": "warn"}, {"status": "fail"}]), "fail"
        )
        self.assertEqual(
            doctor.overall_status([{"status": "pass"}, {"status": "skip"}]), "pass"
        )


class ChildProcessSafetyTests(unittest.TestCase):
    def test_oversized_output_is_bounded(self) -> None:
        completed = mock.Mock(returncode=0, stdout="x" * 100000, stderr="y" * 100000)
        with mock.patch.object(subprocess, "run", return_value=completed):
            result = doctor.run_child(["noop"], timeout=5)
        self.assertLessEqual(len(result.stdout), doctor.MAX_CHILD_CAPTURE)
        self.assertLessEqual(len(result.stderr), doctor.MAX_CHILD_CAPTURE)

    def test_timeout_fails_closed(self) -> None:
        with mock.patch.object(
            subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="noop", timeout=5)
        ):
            result = doctor.run_child(["noop"], timeout=5)
        self.assertTrue(result.timed_out)
        self.assertNotEqual(result.returncode, 0)

    def test_script_timeout_becomes_fail_check(self) -> None:
        with mock.patch.object(doctor, "run_child", return_value=fake_child(timed_out=True)):
            check = doctor.check_public_claims(doctor.Options())
        self.assertEqual(check["status"], "fail")

    def test_no_shell_execution(self) -> None:
        captured = {}

        def capture(argv, **kwargs):
            captured["shell"] = kwargs.get("shell", False)
            captured["argv_is_list"] = isinstance(argv, list)
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(subprocess, "run", side_effect=capture):
            doctor.run_child(["echo", "hi"], timeout=5)
        self.assertFalse(captured["shell"])
        self.assertTrue(captured["argv_is_list"])


class DefaultModeBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.options = doctor.Options()

    def test_default_mode_makes_zero_network_calls(self) -> None:
        recorded = []

        def record(argv, timeout):
            recorded.append(list(argv))
            return canned_run_child(argv, timeout)

        with mock.patch.object(doctor, "_fetch_public", side_effect=network_blocker), mock.patch.object(
            doctor, "run_child", side_effect=record
        ):
            report = doctor.build_report(self.options)
        # No child invoked the Arc RPC helper, and no public-site fetch happened.
        for argv in recorded:
            joined = " ".join(argv)
            self.assertNotIn("check_arc_testnet_status.py", joined)
        ids = [check["id"] for check in report["checks"]]
        self.assertNotIn("arc_testnet.read_only_status", ids)
        for check in report["checks"]:
            self.assertFalse(check["id"].startswith("public_site."))

    def test_default_mode_does_not_read_dotenv(self) -> None:
        opened_paths = []
        real_open = open

        def recording_open(file, *args, **kwargs):
            opened_paths.append(str(file))
            return real_open(file, *args, **kwargs)

        with mock.patch.object(doctor, "run_child", side_effect=canned_run_child), mock.patch(
            "builtins.open", side_effect=recording_open
        ):
            doctor.build_report(self.options)
        for path in opened_paths:
            self.assertFalse(path.endswith(".env"), path)

    def test_default_mode_has_no_wallet_or_signing_argv(self) -> None:
        recorded = []

        def record(argv, timeout):
            recorded.append(" ".join(str(part) for part in argv))
            return canned_run_child(argv, timeout)

        with mock.patch.object(doctor, "run_child", side_effect=record):
            doctor.build_report(self.options)
        forbidden = (
            "eth_sendTransaction",
            "personal_sign",
            "eth_sign",
            "sendRawTransaction",
            "wallet_",
            "mainnet",
        )
        for argv in recorded:
            for token in forbidden:
                self.assertNotIn(token, argv)

    def test_report_schema_and_safety(self) -> None:
        with mock.patch.object(doctor, "run_child", side_effect=canned_run_child):
            report = doctor.build_report(self.options)
        parsed = json.loads(json.dumps(report))  # must be JSON-serializable, no reprs
        self.assertEqual(parsed["kind"], "arc_builder_doctor_report")
        self.assertEqual(parsed["schemaVersion"], 1)
        self.assertIn(parsed["overallStatus"], ("pass", "warn", "fail"))
        safety = parsed["safety"]
        self.assertTrue(safety["networkChecksOptIn"])
        for key in (
            "walletConnected",
            "privateKeysAccepted",
            "signingEnabled",
            "transactionBroadcast",
            "custodyEnabled",
            "mainnetEnabled",
            "autonomousSpending",
        ):
            self.assertFalse(safety[key], key)
        for check in parsed["checks"]:
            self.assertIn(check["status"], doctor.VALID_STATUSES)
            self.assertGreaterEqual(check["durationMs"], 0)

    def test_deterministic_check_ordering(self) -> None:
        with mock.patch.object(doctor, "run_child", side_effect=canned_run_child):
            first = [c["id"] for c in doctor.build_report(doctor.Options())["checks"]]
            second = [c["id"] for c in doctor.build_report(doctor.Options())["checks"]]
        self.assertEqual(first, second)
        self.assertEqual(first[0], "runtime.python")


class RuntimeCheckTests(unittest.TestCase):
    def test_missing_node_is_warning(self) -> None:
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            check = doctor.check_node(doctor.Options())
        self.assertEqual(check["status"], "warn")
        self.assertEqual(check["id"], "runtime.node")


class ArcRpcCheckTests(unittest.TestCase):
    def test_skipped_unless_requested(self) -> None:
        with mock.patch.object(doctor, "run_child", side_effect=canned_run_child):
            ids = [c["id"] for c in doctor.build_report(doctor.Options())["checks"]]
        self.assertNotIn("arc_testnet.read_only_status", ids)

    def test_accepts_exact_arc_testnet_chain(self) -> None:
        payload = json.dumps(
            {"ok": True, "status": {"chainIdDecimal": 5042002, "chainIdHex": "0x4cef52"}}
        )
        with mock.patch.object(doctor, "run_child", return_value=fake_child(stdout=payload)):
            check = doctor.check_arc_testnet_status(doctor.Options(include_arc_rpc=True))
        self.assertEqual(check["status"], "pass")

    def test_wrong_chain_id_fails(self) -> None:
        payload = json.dumps(
            {"ok": False, "status": {"chainIdDecimal": 1, "chainIdHex": "0x1"}}
        )
        with mock.patch.object(doctor, "run_child", return_value=fake_child(stdout=payload)):
            check = doctor.check_arc_testnet_status(doctor.Options(include_arc_rpc=True))
        self.assertEqual(check["status"], "fail")

    def test_expected_chain_with_nonzero_helper_exit_is_not_pass(self) -> None:
        payload = json.dumps(
            {"ok": True, "status": {"chainIdDecimal": 5042002, "chainIdHex": "0x4cef52"}}
        )
        with mock.patch.object(
            doctor, "run_child", return_value=fake_child(returncode=2, stdout=payload)
        ):
            relaxed = doctor.check_arc_testnet_status(doctor.Options(include_arc_rpc=True))
            strict = doctor.check_arc_testnet_status(
                doctor.Options(include_arc_rpc=True, strict=True)
            )
        self.assertEqual(relaxed["status"], "warn")
        self.assertEqual(strict["status"], "fail")

    def test_expected_chain_without_explicit_ok_is_not_pass(self) -> None:
        payload = json.dumps(
            {"ok": False, "status": {"chainIdDecimal": 5042002, "chainIdHex": "0x4cef52"}}
        )
        with mock.patch.object(doctor, "run_child", return_value=fake_child(stdout=payload)):
            relaxed = doctor.check_arc_testnet_status(doctor.Options(include_arc_rpc=True))
            strict = doctor.check_arc_testnet_status(
                doctor.Options(include_arc_rpc=True, strict=True)
            )
        self.assertEqual(relaxed["status"], "warn")
        self.assertEqual(strict["status"], "fail")

    def test_malformed_output_fails_closed(self) -> None:
        with mock.patch.object(doctor, "run_child", return_value=fake_child(stdout="not json")):
            relaxed = doctor.check_arc_testnet_status(doctor.Options(include_arc_rpc=True))
            strict = doctor.check_arc_testnet_status(
                doctor.Options(include_arc_rpc=True, strict=True)
            )
        self.assertEqual(relaxed["status"], "warn")
        self.assertEqual(strict["status"], "fail")
        self.assertNotEqual(relaxed["status"], "pass")


class PublicSiteCheckTests(unittest.TestCase):
    def test_skipped_unless_requested(self) -> None:
        with mock.patch.object(doctor, "run_child", side_effect=canned_run_child):
            ids = [c["id"] for c in doctor.build_report(doctor.Options())["checks"]]
        self.assertFalse(any(i.startswith("public_site.") for i in ids))

    def test_foreign_redirect_is_rejected(self) -> None:
        with mock.patch.object(
            doctor, "_fetch_public", side_effect=doctor.ForeignRedirectError("evil.example")
        ):
            check = doctor._check_public_site_target(
                doctor.Options(include_public_site=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("Arc MCP Builder Assistant",),
            )
        self.assertEqual(check["status"], "fail")

    def test_unavailable_is_warn_then_fail_under_strict(self) -> None:
        from urllib import error as urllib_error

        with mock.patch.object(
            doctor, "_fetch_public", side_effect=urllib_error.URLError("offline")
        ):
            relaxed = doctor._check_public_site_target(
                doctor.Options(include_public_site=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("marker",),
            )
            strict = doctor._check_public_site_target(
                doctor.Options(include_public_site=True, strict=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("marker",),
            )
        self.assertEqual(relaxed["status"], "warn")
        self.assertEqual(strict["status"], "fail")

    def test_incomplete_http_response_is_warn_then_fail_under_strict(self) -> None:
        with mock.patch.object(
            doctor,
            "_fetch_public",
            side_effect=doctor.http_client.IncompleteRead(b"partial"),
        ):
            relaxed = doctor._check_public_site_target(
                doctor.Options(include_public_site=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("marker",),
            )
            strict = doctor._check_public_site_target(
                doctor.Options(include_public_site=True, strict=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("marker",),
            )
        self.assertEqual(relaxed["status"], "warn")
        self.assertEqual(strict["status"], "fail")

    def test_missing_marker_is_not_pass(self) -> None:
        with mock.patch.object(doctor, "_fetch_public", return_value=(200, "unrelated body")):
            check = doctor._check_public_site_target(
                doctor.Options(include_public_site=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("REQUIRED-MARKER",),
            )
        self.assertNotEqual(check["status"], "pass")

    def test_oversized_public_response_fails_closed(self) -> None:
        with mock.patch.object(
            doctor,
            "_fetch_public",
            side_effect=doctor.OversizedResponseError("too large"),
        ):
            check = doctor._check_public_site_target(
                doctor.Options(include_public_site=True),
                "public_site.root",
                "Public site root",
                doctor.CANONICAL_BASE_URL,
                ("marker",),
            )
        self.assertEqual(check["status"], "fail")

    def test_fetch_public_rejects_oversized_response(self) -> None:
        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self):
                return doctor.CANONICAL_BASE_URL

            def read(self, limit):
                return b"x" * limit

        fake_opener = mock.Mock()
        fake_opener.open.return_value = FakeResponse()
        with mock.patch.object(doctor.urllib_request, "build_opener", return_value=fake_opener):
            with self.assertRaises(doctor.OversizedResponseError):
                doctor._fetch_public(doctor.CANONICAL_BASE_URL, timeout=5, max_bytes=10)


class SourceBoundaryTests(unittest.TestCase):
    def test_module_introduces_no_signing_or_broadcast_path(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "eth_sendTransaction",
            "eth_sendRawTransaction",
            "personal_sign",
            "signTransaction",
            "PRIVATE_KEY",
            "seed phrase",
            "window.ethereum",
        ):
            self.assertNotIn(forbidden, source, forbidden)

    def test_strict_does_not_enable_network_by_itself(self) -> None:
        options = doctor.Options(strict=True)
        self.assertFalse(options.include_arc_rpc)
        self.assertFalse(options.include_public_site)
        with mock.patch.object(doctor, "_fetch_public", side_effect=network_blocker), mock.patch.object(
            doctor, "run_child", side_effect=canned_run_child
        ):
            report = doctor.build_report(options)
        ids = [c["id"] for c in report["checks"]]
        self.assertNotIn("arc_testnet.read_only_status", ids)
        self.assertFalse(any(i.startswith("public_site.") for i in ids))


if __name__ == "__main__":
    unittest.main()
