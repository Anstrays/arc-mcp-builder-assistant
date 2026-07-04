#!/usr/bin/env python3
"""Regression tests for the read-only Arc Testnet status helper."""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts" / "check_arc_testnet_status.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("arc_status_helper_under_test", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ArcTestnetStatusHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.helper = load_helper()

    def test_default_endpoints_and_timeout_are_safe(self) -> None:
        self.helper.validate_endpoint(self.helper.DEFAULT_RPC_URL, "RPC URL")
        self.helper.validate_endpoint(self.helper.DEFAULT_EXPLORER_URL, "explorer URL")
        self.helper.validate_timeout(10)

    def test_endpoint_rejects_unsupported_scheme_and_credentials(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTP or HTTPS"):
            self.helper.validate_endpoint("file:///tmp/rpc.json", "RPC URL")
        with self.assertRaisesRegex(ValueError, "embedded credentials"):
            self.helper.validate_endpoint("https://user:password@example.invalid", "RPC URL")

    def test_timeout_rejects_zero_and_excessive_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 60"):
            self.helper.validate_timeout(0)
        with self.assertRaisesRegex(ValueError, "between 1 and 60"):
            self.helper.validate_timeout(61)

    def test_hex_quantity_parser_fails_closed(self) -> None:
        self.assertEqual(self.helper.parse_hex_quantity("0x4cef52"), 5042002)
        with self.assertRaisesRegex(ValueError, "expected hex quantity"):
            self.helper.parse_hex_quantity("5042002")

    def test_rpc_response_must_be_bounded_json_object(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "JSON object"):
            self.helper.decode_json_object(io.BytesIO(b"[]"))
        with self.assertRaisesRegex(RuntimeError, "1 MB safety limit"):
            self.helper.decode_json_object(
                io.BytesIO(b"{" + b" " * self.helper.MAX_RESPONSE_BYTES + b"}")
            )


if __name__ == "__main__":
    unittest.main()
