#!/usr/bin/env python3
"""Failure-path tests for the offline Arc Testnet facts contract."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_arc_testnet_facts.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("arc_testnet_facts_under_test", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArcTestnetFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.facts = self.validator.load_facts(self.validator.DEFAULT_FACTS)

    def test_committed_facts_and_targets_are_consistent(self) -> None:
        self.validator.validate_facts(self.facts)
        self.assertGreater(self.validator.validate_targets(self.facts), 20)

    def test_rejects_duplicate_json_keys(self) -> None:
        raw = json.dumps(self.facts)
        duplicate = raw[:-1] + ',"scope":"duplicate"}'
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            path = Path(tmp) / "facts.json"
            path.write_text(duplicate, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                self.validator.load_facts(path)

    def test_rejects_chain_id_hex_mismatch(self) -> None:
        changed = copy.deepcopy(self.facts)
        changed["network"]["chainIdHex"] = "0x1"
        with self.assertRaisesRegex(ValueError, "network.chainIdHex"):
            self.validator.validate_facts(changed)

    def test_rejects_unreviewed_but_internally_consistent_chain(self) -> None:
        changed = copy.deepcopy(self.facts)
        changed["network"]["chainId"] = 1
        changed["network"]["chainIdHex"] = "0x1"
        with self.assertRaisesRegex(ValueError, "reviewed baseline network.chainId"):
            self.validator.validate_facts(changed)

    def test_rejects_unsafe_urls(self) -> None:
        for key, unsafe in (
            ("rpcUrl", "http://rpc.testnet.arc.network"),
            ("explorerUrl", "https://user:password@testnet.arcscan.app"),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.facts)
                changed["network"][key] = unsafe
                with self.assertRaisesRegex(ValueError, f"network.{key}"):
                    self.validator.validate_facts(changed)

    def test_rejects_malformed_usdc_address(self) -> None:
        changed = copy.deepcopy(self.facts)
        changed["erc20Usdc"]["address"] = "0x1234"
        with self.assertRaisesRegex(ValueError, "20-byte EVM address"):
            self.validator.validate_facts(changed)

    def test_rejects_unreviewed_rpc_usdc_decimals_and_source_drift(self) -> None:
        changes = (
            (("network", "rpcUrl"), "https://example.invalid/rpc", "network.rpcUrl"),
            (
                ("erc20Usdc", "address"),
                "0x1111111111111111111111111111111111111111",
                "erc20Usdc.address",
            ),
            (("erc20Usdc", "decimals"), 18, "erc20Usdc.decimals"),
            (
                ("sources", "connect"),
                "https://docs.arc.io/arc/references/evm-differences",
                "sources.connect",
            ),
        )
        for path, value, label in changes:
            with self.subTest(label=label):
                changed = copy.deepcopy(self.facts)
                changed[path[0]][path[1]] = value
                with self.assertRaisesRegex(ValueError, f"reviewed baseline {label}"):
                    self.validator.validate_facts(changed)

    def test_rejects_mainnet_wallet_or_implicit_network_enablement(self) -> None:
        for key, unsafe in (
            ("mainnetSupported", True),
            ("walletRequired", True),
            ("networkChecksOptIn", False),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.facts)
                changed["policy"][key] = unsafe
                with self.assertRaisesRegex(ValueError, f"policy.{key}"):
                    self.validator.validate_facts(changed)

    def test_rejects_unknown_fields(self) -> None:
        changed = copy.deepcopy(self.facts)
        changed["network"]["unreviewed"] = True
        with self.assertRaisesRegex(ValueError, "network must contain exactly"):
            self.validator.validate_facts(changed)

    def test_target_drift_fails_closed(self) -> None:
        relative, build_marker = self.validator.FACT_TARGETS["network.chainId"][0]
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            for targets in self.validator.FACT_TARGETS.values():
                for target_relative, _ in targets:
                    source = ROOT / target_relative
                    destination = root / target_relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            path = root / relative
            path.write_text(
                path.read_text(encoding="utf-8").replace(build_marker(self.facts), "EXPECTED_CHAIN_ID_DECIMAL = 1"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "exactly one canonical network.chainId"):
                self.validator.validate_targets(self.facts, root)

    def test_duplicate_target_marker_fails_closed(self) -> None:
        relative, build_marker = self.validator.FACT_TARGETS["network.rpcUrl"][0]
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            for targets in self.validator.FACT_TARGETS.values():
                for target_relative, _ in targets:
                    source = ROOT / target_relative
                    destination = root / target_relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            path = root / relative
            path.write_text(
                path.read_text(encoding="utf-8") + "\n" + build_marker(self.facts) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "exactly one canonical network.rpcUrl"):
                self.validator.validate_targets(self.facts, root)

    def test_dangerous_chain_id_in_surface_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_doc = root / "docs" / "bad.md"
            bad_doc.parent.mkdir(parents=True, exist_ok=True)
            bad_doc.write_text("Use chainId: 1244 for ARC Testnet.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dangerous value for network.chainId"):
                self.validator.scan_for_dangerous_values(self.facts, root)

    def test_dangerous_hex_chain_id_in_surface_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_js = root / "examples" / "bad" / "bad.js"
            bad_js.parent.mkdir(parents=True, exist_ok=True)
            bad_js.write_text('const chainIdHex = "0x1";\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dangerous value for network.chainIdHex"):
                self.validator.scan_for_dangerous_values(self.facts, root)

    def test_dangerous_rpc_url_in_surface_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_html = root / "index.html"
            bad_html.write_text(
                '<script>const RPC = "https://rpc.arc.network";</script>\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "dangerous value for network.rpcUrl"):
                self.validator.scan_for_dangerous_values(self.facts, root)

    def test_dangerous_values_allowed_in_explicit_safe_context(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            safe_doc = root / "docs" / "forbidden.md"
            safe_doc.parent.mkdir(parents=True, exist_ok=True)
            safe_doc.write_text(
                "Do not use chainId 1244.\n"
                "Do not configure https://rpc.arc.network.\n"
                "Those values are forbidden.\n",
                encoding="utf-8",
            )
            count = self.validator.scan_for_dangerous_values(self.facts, root)
            self.assertGreaterEqual(count, 1)

    def test_dangerous_value_not_hidden_by_nearby_safe_word(self) -> None:
        """A safe word on the same line must not suppress a real dangerous value."""
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_doc = root / "docs" / "bad.md"
            bad_doc.parent.mkdir(parents=True, exist_ok=True)
            bad_doc.write_text(
                "This is wrong. Configure the wallet with chainId: 1 for speed.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "dangerous value for network.chainId"):
                self.validator.scan_for_dangerous_values(self.facts, root)

    def test_markdown_chain_id_variants_fail_closed(self) -> None:
        """Prose/markdown spellings of chain id must still be caught."""
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_doc = root / "docs" / "bad.md"
            bad_doc.parent.mkdir(parents=True, exist_ok=True)
            bad_doc.write_text(
                "Set Chain ID: 1244.\n"
                "Use chain-id = \"1\".\n"
                "The chain id is 1244.\n"
                "Chain ID: `0x4d4`.\n"
                "chainIdHex: `0x1`.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "detected dangerous Arc Testnet fact drift"):
                self.validator.scan_for_dangerous_values(self.facts, root)

    def test_chain_id_regex_no_false_positives(self) -> None:
        """Canonical values, tx status 0x1, and plain list numbers must pass."""
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            good_doc = root / "docs" / "ok.md"
            good_doc.parent.mkdir(parents=True, exist_ok=True)
            good_doc.write_text(
                "1. Connect to Arc Testnet with Chain ID: 5042002.\n"
                "2. Chain ID: `0x4cef52` is the hex form.\n"
                "The receipt status is 0x1.\n"
                "Log topic value is 0x1.\n"
                "1. Do not use chainId 1 is documented as forbidden.\n"
            )
            count = self.validator.scan_for_dangerous_values(self.facts, root)
            self.assertGreaterEqual(count, 1)

    def test_decimal_confusion_fails_closed_for_usdc(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_doc = root / "docs" / "bad.md"
            bad_doc.parent.mkdir(parents=True, exist_ok=True)
            bad_doc.write_text("ERC-20 USDC uses 18 decimals.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ERC-20 USDC decimals appears to be 18"):
                self.validator.scan_for_decimal_confusion(root)

    def test_decimal_confusion_fails_closed_for_native_gas(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            bad_doc = root / "docs" / "bad.md"
            bad_doc.parent.mkdir(parents=True, exist_ok=True)
            bad_doc.write_text("Native gas uses 6 decimals.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "native gas decimals appears to be 6"):
                self.validator.scan_for_decimal_confusion(root)

    def test_decimal_confusion_allows_correct_dual_statement(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            doc = root / "docs" / "ok.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text(
                "Native gas accounting uses 18 decimals, while the optional "
                "ERC-20 USDC interface uses 6 decimals.\n",
                encoding="utf-8",
            )
            count = self.validator.scan_for_decimal_confusion(root)
            self.assertGreaterEqual(count, 1)

    def test_safe_context_must_be_tied_to_the_dangerous_value(self) -> None:
        """Generic 'do not' or 'fixture' text must not suppress a real dangerous value."""
        cases = [
            ("Do not skip review; configure chainId: 1", "network.chainId"),
            ("This fixture is useful; chainId: 1", "network.chainId"),
            ("Do not skip; use https://rpc.arc.network", "network.rpcUrl"),
        ]
        for content, fact_name in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
                    root = Path(tmp)
                    bad_doc = root / "docs" / "bad.md"
                    bad_doc.parent.mkdir(parents=True, exist_ok=True)
                    bad_doc.write_text(content + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, f"dangerous value for {fact_name}"):
                        self.validator.scan_for_dangerous_values(self.facts, root)

    def test_explicit_negation_of_dangerous_value_passes(self) -> None:
        """Allowed safe contexts explicitly mention the dangerous value."""
        cases = [
            "Do not use chainId 1",
            "chainId: 1 is forbidden",
            "Chain ID 1244 is not allowed",
            "Must never configure chain-id = \"1\"",
            "// do not use: negative test fixture; chainId: '0x1'",
            "Do not configure https://rpc.arc.network",
            "https://rpc.arc.network is forbidden",
        ]
        for content in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
                    root = Path(tmp)
                    safe_doc = root / "docs" / "safe.md"
                    safe_doc.parent.mkdir(parents=True, exist_ok=True)
                    safe_doc.write_text(content + "\n", encoding="utf-8")
                    count = self.validator.scan_for_dangerous_values(self.facts, root)
                    self.assertGreaterEqual(count, 1)

    def test_no_duplicate_test_method_names(self) -> None:
        """Regress against accidental duplicate test_* method definitions."""
        source = (ROOT / "scripts" / "test_arc_testnet_facts.py").read_text(encoding="utf-8")
        names = re.findall(r"^\s+def\s+(test_\w+)\s*\(", source, re.MULTILINE)
        counts: dict[str, int] = {}
        for name in names:
            counts[name] = counts.get(name, 0) + 1
        duplicates = {name: count for name, count in counts.items() if count > 1}
        self.assertEqual(duplicates, {}, f"duplicate test method definitions: {duplicates}")


if __name__ == "__main__":
    unittest.main()
