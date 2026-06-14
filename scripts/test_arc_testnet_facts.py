#!/usr/bin/env python3
"""Failure-path tests for the offline Arc Testnet facts contract."""

from __future__ import annotations

import copy
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
