#!/usr/bin/env python3
"""Failure-path tests for the Arc live-infrastructure policy validator."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_live_infrastructure_policy.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("live_policy_validator_under_test", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiveInfrastructurePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.policy = self.validator.load_policy(self.validator.DEFAULT_POLICY)

    def test_committed_policy_is_valid(self) -> None:
        self.validator.validate_policy(self.policy)

    def test_rejects_enabled_mainnet_profile(self) -> None:
        changed = copy.deepcopy(self.policy)
        changed["profiles"]["arcMainnet"]["enabled"] = True
        with self.assertRaisesRegex(ValueError, "arcMainnet.enabled"):
            self.validator.validate_policy(changed)

    def test_rejects_unreviewed_network_profile(self) -> None:
        changed = copy.deepcopy(self.policy)
        changed["profiles"]["otherNetwork"] = {"enabled": False}
        with self.assertRaisesRegex(ValueError, "only arcTestnet"):
            self.validator.validate_policy(changed)

    def test_rejects_autonomous_or_raw_key_signing(self) -> None:
        for key in ("autonomous", "rawPrivateKeysAccepted"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.policy)
                changed["profiles"]["arcTestnet"]["signing"][key] = True
                with self.assertRaisesRegex(ValueError, key):
                    self.validator.validate_policy(changed)

    def test_rejects_retry_or_multiple_attempts(self) -> None:
        changed = copy.deepcopy(self.policy)
        changed["profiles"]["arcTestnet"]["broadcast"]["automaticRetry"] = True
        with self.assertRaisesRegex(ValueError, "automaticRetry"):
            self.validator.validate_policy(changed)
        changed = copy.deepcopy(self.policy)
        changed["profiles"]["arcTestnet"]["broadcast"]["maxAttemptsPerPageLoad"] = 2
        with self.assertRaisesRegex(ValueError, "maxAttemptsPerPageLoad"):
            self.validator.validate_policy(changed)

    def test_rejects_embedded_context_or_unsafe_recipient_policy(self) -> None:
        for key, unsafe_value in (
            ("topLevelBrowsingContextRequired", False),
            ("zeroAddressAllowed", True),
            ("tokenContractRecipientAllowed", True),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.policy)
                changed["profiles"]["arcTestnet"]["broadcast"][key] = unsafe_value
                with self.assertRaisesRegex(ValueError, key):
                    self.validator.validate_policy(changed)

    def test_rejects_custody_or_static_secret_storage(self) -> None:
        for key in ("implemented", "staticSiteMayHoldSecrets"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.policy)
                changed["custody"][key] = True
                with self.assertRaisesRegex(ValueError, key):
                    self.validator.validate_policy(changed)

    def test_rejects_missing_custody_gate(self) -> None:
        changed = copy.deepcopy(self.policy)
        changed["custody"]["requiredBeforeEnable"].pop()
        with self.assertRaisesRegex(ValueError, "exact reviewed custody gates"):
            self.validator.validate_policy(changed)

    def test_rejects_duplicate_custody_gate(self) -> None:
        changed = copy.deepcopy(self.policy)
        changed["custody"]["requiredBeforeEnable"][-1] = changed["custody"]["requiredBeforeEnable"][0]
        with self.assertRaisesRegex(ValueError, "exact reviewed custody gates"):
            self.validator.validate_policy(changed)

    def test_rejects_unknown_fields_at_every_policy_boundary(self) -> None:
        for path in (
            (),
            ("profiles", "arcTestnet"),
            ("profiles", "arcTestnet", "asset"),
            ("profiles", "arcTestnet", "signing"),
            ("profiles", "arcTestnet", "broadcast"),
            ("profiles", "arcMainnet"),
            ("custody",),
        ):
            with self.subTest(path=path):
                changed = copy.deepcopy(self.policy)
                target = changed
                for key in path:
                    target = target[key]
                target["unreviewedCapability"] = True
                with self.assertRaisesRegex(ValueError, "must contain exactly"):
                    self.validator.validate_policy(changed)

    def test_load_policy_rejects_duplicate_json_keys(self) -> None:
        raw = json.dumps(self.policy)
        duplicate = raw[:-1] + ',"scope":"unreviewed-duplicate"}'
        with tempfile.TemporaryDirectory(prefix=".arc-test-", dir=ROOT) as tmp:
            path = Path(tmp) / "duplicate-policy.json"
            path.write_text(duplicate, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                self.validator.load_policy(path)


if __name__ == "__main__":
    unittest.main()
