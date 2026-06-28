"""Circle Wallet SDK guard helpers for Arc Testnet.

This module intentionally does not import Circle's SDK, open wallets, sign, or
broadcast. It builds reviewable manifests, environment readiness summaries, and
copy-paste snippets for a human-approved Circle Developer-Controlled Wallet SDK
run on Arc Testnet.
"""

from __future__ import annotations

import json
import os
import re
from typing import Mapping, cast

ARC_TESTNET_BLOCKCHAIN = "ARC-TESTNET"
ARC_TESTNET_CHAIN_ID = 5_042_002
ARC_TESTNET_CHAIN_ID_HEX = "0x4cef52"
SDK_PYTHON_PACKAGE = "circle-developer-controlled-wallets"
SDK_TYPESCRIPT_PACKAGE = "@circle-fin/developer-controlled-wallets"
REQUIRED_ENVIRONMENT = ("CIRCLE_API_KEY", "CIRCLE_ENTITY_SECRET")
OPTIONAL_ENVIRONMENT = ("CIRCLE_WALLET_SET_ID", "CIRCLE_API_BASE_URL")
ACCOUNT_TYPES = ("EOA", "SCA")
MAX_WALLET_COUNT = 50
DEFAULT_WALLET_SET_NAME = "arc-agent-wallets"
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,62}$")


def _validate_account_type(account_type: str) -> str:
    normalized = account_type.strip().upper()
    if normalized not in ACCOUNT_TYPES:
        raise ValueError(f"account_type must be one of {', '.join(ACCOUNT_TYPES)}")
    return normalized


def _validate_count(count: int) -> int:
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValueError("count must be an integer")
    if not 1 <= count <= MAX_WALLET_COUNT:
        raise ValueError(f"count must be between 1 and {MAX_WALLET_COUNT}")
    return count


def _validate_wallet_set_name(name: str) -> str:
    value = name.strip()
    if not value:
        raise ValueError("wallet_set_name must be non-empty")
    if any(ch in value for ch in "\r\n\0"):
        raise ValueError("wallet_set_name contains forbidden control characters")
    if not _NAME_RE.match(value):
        raise ValueError("wallet_set_name must start with an alphanumeric character and use only simple label characters")
    return value


def build_sdk_guard_manifest() -> dict[str, object]:
    """Return the reviewed Circle Wallet SDK integration guard manifest."""

    return {
        "name": "circle-wallet-sdk-arc-testnet-guard",
        "version": "0.1.0",
        "purpose": "Human-reviewed Circle Developer-Controlled Wallet SDK bootstrap for Arc Testnet.",
        "blockchain": ARC_TESTNET_BLOCKCHAIN,
        "chainId": ARC_TESTNET_CHAIN_ID,
        "chainIdHex": ARC_TESTNET_CHAIN_ID_HEX,
        "sdk": {
            "pythonPackage": SDK_PYTHON_PACKAGE,
            "typescriptPackage": SDK_TYPESCRIPT_PACKAGE,
            "product": "Circle Developer-Controlled Wallets",
            "docs": [
                "https://developers.circle.com/wallets/dev-controlled/create-your-first-wallet",
                "https://developers.circle.com/sdks/developer-controlled-wallets-python-sdk",
            ],
        },
        "requiredEnvironment": list(REQUIRED_ENVIRONMENT),
        "optionalEnvironment": list(OPTIONAL_ENVIRONMENT),
        "supportedAccountTypes": list(ACCOUNT_TYPES),
        "walletCountLimit": MAX_WALLET_COUNT,
        "safety": {
            "testnetOnly": True,
            "humanApprovalRequired": True,
            "liveSdkExecution": False,
            "privateKeysAccepted": False,
            "rawSigning": False,
            "transactionBroadcast": False,
            "custodyInRepo": False,
            "mainnetEnabled": False,
            "secretsPrinted": False,
        },
        "reviewedOperations": [
            "create_wallet_set",
            "create_wallet on ARC-TESTNET",
            "list_wallets / inspect wallet metadata",
        ],
        "nonGoals": [
            "No committed API keys or entity secrets.",
            "No autonomous SDK execution from this repo command.",
            "No mainnet wallet creation.",
            "No token transfer, contract execution, signing, or broadcast.",
        ],
    }


def build_wallet_creation_plan(
    *,
    account_type: str = "SCA",
    count: int = 1,
    wallet_set_name: str = DEFAULT_WALLET_SET_NAME,
) -> dict[str, object]:
    """Build a JSON-ready, non-executing wallet creation plan."""

    normalized_type = _validate_account_type(account_type)
    normalized_count = _validate_count(count)
    normalized_name = _validate_wallet_set_name(wallet_set_name)
    return {
        "walletSet": {
            "name": normalized_name,
            "operation": "create_wallet_set",
        },
        "wallets": {
            "operation": "create_wallet",
            "blockchains": [ARC_TESTNET_BLOCKCHAIN],
            "accountType": normalized_type,
            "count": normalized_count,
        },
        "execution": {
            "liveSdkExecution": False,
            "requiresExplicitHumanRunApproval": True,
            "requiresEnvironment": list(REQUIRED_ENVIRONMENT),
            "allowedFollowUps": ["manual SDK run", "read-only list wallets", "manual faucet funding"],
            "blockedFollowUps": ["mainnet", "private keys", "raw signing", "autonomous transfer", "broadcast"],
        },
        "reviewChecklist": [
            "Confirm Circle account/project is testnet-only for this run.",
            "Confirm CIRCLE_API_KEY and CIRCLE_ENTITY_SECRET are present only in the local shell or secret manager.",
            "Confirm blockchains is exactly ['ARC-TESTNET'] before running SDK code.",
            "Record wallet IDs/addresses without storing secrets in the repo.",
        ],
    }


def summarize_environment(env: Mapping[str, str] | None = None) -> dict[str, object]:
    """Return presence-only Circle SDK environment state, redacting values."""

    source = os.environ if env is None else env
    variables: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    for name in (*REQUIRED_ENVIRONMENT, *OPTIONAL_ENVIRONMENT):
        value = source.get(name, "")
        present = bool(value)
        variables[name] = {
            "present": present,
            "required": name in REQUIRED_ENVIRONMENT,
            "value": "[REDACTED]" if present else "",
        }
        if name in REQUIRED_ENVIRONMENT and not present:
            missing.append(name)
    return {
        "readyForManualSdkRun": not missing,
        "missingRequired": missing,
        "variables": variables,
        "safety": {
            "valuesRedacted": True,
            "secretsPrinted": False,
            "liveSdkExecution": False,
        },
    }


def generate_python_sdk_snippet(
    *,
    account_type: str = "SCA",
    count: int = 1,
    wallet_set_name: str = DEFAULT_WALLET_SET_NAME,
) -> str:
    """Return a secret-safe Python SDK snippet for manual human execution."""

    plan = build_wallet_creation_plan(
        account_type=account_type,
        count=count,
        wallet_set_name=wallet_set_name,
    )
    wallet_set = cast(Mapping[str, object], plan["walletSet"])
    wallets = cast(Mapping[str, object], plan["wallets"])
    payload = {
        "walletSetName": wallet_set["name"],
        "blockchains": wallets["blockchains"],
        "accountType": wallets["accountType"],
        "count": wallets["count"],
    }
    payload_json = json.dumps(payload, indent=4)
    return f'''#!/usr/bin/env python3
"""Manual Circle Developer-Controlled Wallet SDK run for Arc Testnet.

Before running:
- export CIRCLE_API_KEY in your local shell or secret manager
- export CIRCLE_ENTITY_SECRET in your local shell or secret manager
- review that blockchains is exactly ["{ARC_TESTNET_BLOCKCHAIN}"]
"""

import json
import os

from circle.web3 import developer_controlled_wallets, utils

REQUEST = {payload_json}

client = utils.init_developer_controlled_wallets_client(
    api_key=os.environ["CIRCLE_API_KEY"],
    entity_secret=os.environ["CIRCLE_ENTITY_SECRET"],
)
wallet_sets_api = developer_controlled_wallets.WalletSetsApi(client)
wallets_api = developer_controlled_wallets.WalletsApi(client)

wallet_set = wallet_sets_api.create_wallet_set(
    developer_controlled_wallets.CreateWalletSetRequest.from_dict({{
        "name": REQUEST["walletSetName"],
    }})
)
wallet_set_id = wallet_set.data.wallet_set.actual_instance.id

wallets = wallets_api.create_wallet(
    developer_controlled_wallets.CreateWalletRequest.from_dict({{
        "walletSetId": wallet_set_id,
        "blockchains": REQUEST["blockchains"],
        "count": REQUEST["count"],
        "accountType": REQUEST["accountType"],
    }})
)

print(json.dumps(json.loads(wallets.model_dump_json()), indent=2))
'''


__all__ = [
    "ACCOUNT_TYPES",
    "ARC_TESTNET_BLOCKCHAIN",
    "ARC_TESTNET_CHAIN_ID",
    "ARC_TESTNET_CHAIN_ID_HEX",
    "MAX_WALLET_COUNT",
    "REQUIRED_ENVIRONMENT",
    "build_sdk_guard_manifest",
    "build_wallet_creation_plan",
    "generate_python_sdk_snippet",
    "summarize_environment",
]
