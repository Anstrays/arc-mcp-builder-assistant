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
from typing import Any, Mapping, Sequence, cast
from urllib import request as urllib_request
from urllib.parse import urlsplit

ARC_TESTNET_BLOCKCHAIN = "ARC-TESTNET"
ARC_TESTNET_CHAIN_ID = 5_042_002
ARC_TESTNET_CHAIN_ID_HEX = "0x4cef52"
ARC_TESTNET_RPC_URL = "https://rpc.testnet.arc.network"
ARC_TESTNET_USDC_ADDRESS = "0x3600000000000000000000000000000000000000"
SDK_PYTHON_PACKAGE = "circle-developer-controlled-wallets"
SDK_TYPESCRIPT_PACKAGE = "@circle-fin/developer-controlled-wallets"
REQUIRED_ENVIRONMENT = ("CIRCLE_API_KEY", "CIRCLE_ENTITY_SECRET")
OPTIONAL_ENVIRONMENT = ("CIRCLE_WALLET_SET_ID", "CIRCLE_API_BASE_URL")
ACCOUNT_TYPES = ("EOA", "SCA")
MAX_WALLET_COUNT = 50
DEFAULT_WALLET_SET_NAME = "arc-agent-wallets"
ARC_RPC_FALLBACKS: tuple[str, ...] = ()
RPC_CALL_TIMEOUT = 15
MAX_RPC_RESPONSE_BYTES = 1_000_000
READ_ONLY_RPC_METHODS = frozenset(
    {
        "eth_blockNumber",
        "eth_call",
        "eth_chainId",
        "eth_estimateGas",
        "eth_gasPrice",
        "eth_getBalance",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getLogs",
        "eth_getTransactionByHash",
        "eth_getTransactionReceipt",
        "eth_maxPriorityFeePerGas",
        "net_version",
        "web3_clientVersion",
    }
)
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,62}$")
_EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def _rpc_url_error(url: object) -> str | None:
    if not isinstance(url, str) or not url.strip():
        return "RPC URL must be a non-empty string"
    if any(ord(character) < 32 or ord(character) == 127 for character in url):
        return "RPC URL must not contain control characters"
    try:
        parsed = urlsplit(url.strip())
        local_http = parsed.scheme == "http" and parsed.hostname in {
            "127.0.0.1",
            "localhost",
            "::1",
        }
        if (
            not parsed.hostname
            or (parsed.scheme != "https" and not local_http)
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            return "RPC URL must use HTTPS or local HTTP without credentials or query data"
    except ValueError:
        return "RPC URL is malformed"
    return None


def _resolve_rpc_urls(
    rpc_urls: Sequence[str] | None,
    env: Mapping[str, str] | None,
) -> tuple[str, ...]:
    source = os.environ if env is None else env
    if rpc_urls is None:
        raw_urls: list[object] = [ARC_TESTNET_RPC_URL]
        raw_urls.extend(
            value.strip()
            for value in source.get("ARC_RPC_FALLBACKS", "").split(",")
            if value.strip()
        )
        raw_urls.extend(ARC_RPC_FALLBACKS)
    else:
        raw_urls = list(rpc_urls)

    if not raw_urls:
        raise ValueError("at least one RPC URL is required")

    resolved: list[str] = []
    for raw_url in raw_urls:
        error = _rpc_url_error(raw_url)
        if error:
            raise ValueError(error)
        url = cast(str, raw_url).strip()
        if url not in resolved:
            resolved.append(url)
    return tuple(resolved)


def rpc_call(
    method: str,
    params: list[Any] | None = None,
    *,
    rpc_urls: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = RPC_CALL_TIMEOUT,
) -> dict[str, Any]:
    """Run a bounded read-only RPC call with sequential endpoint fallback."""

    if method not in READ_ONLY_RPC_METHODS:
        return {"ok": False, "error": f"RPC method is not in the read-only allowlist: {method!r}"}
    if params is not None and not isinstance(params, list):
        return {"ok": False, "error": "RPC params must be a list"}
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return {"ok": False, "error": "timeout must be positive"}
    try:
        endpoints = _resolve_rpc_urls(rpc_urls, env)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    errors: list[str] = []
    for index, endpoint in enumerate(endpoints):
        try:
            response = _rpc_call(endpoint, method, params or [], timeout)
            if "error" in response:
                rpc_error = response.get("error")
                if isinstance(rpc_error, Mapping):
                    detail = rpc_error.get("message", "RPC error")
                else:
                    detail = rpc_error or "RPC error"
                errors.append(f"{endpoint}: {detail}")
                continue
            return {
                "ok": True,
                "result": response.get("result"),
                "endpoint": endpoint,
                "source": "primary" if index == 0 else f"fallback-{index}",
            }
        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")
    return {
        "ok": False,
        "error": "all RPC endpoints failed: " + "; ".join(errors),
        "attempted": len(endpoints),
    }


def check_arc_rpc_health(
    rpc_urls: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    timeout: float = RPC_CALL_TIMEOUT,
) -> dict[str, Any]:
    """Prove that a selected read-only RPC endpoint is Arc Testnet."""

    result = rpc_call(
        "eth_chainId",
        rpc_urls=rpc_urls,
        env=env,
        timeout=timeout,
    )
    if not result.get("ok"):
        return result
    chain_hex = result.get("result")
    if not isinstance(chain_hex, str):
        return {"ok": False, "error": f"unexpected chain ID response: {chain_hex!r}"}
    try:
        chain_id = int(chain_hex, 16)
    except ValueError:
        return {"ok": False, "error": f"could not decode chain ID hex: {chain_hex!r}"}
    if chain_id != ARC_TESTNET_CHAIN_ID:
        return {
            "ok": False,
            "error": (
                f"wrong chain {chain_id} ({chain_hex}), expected "
                f"{ARC_TESTNET_CHAIN_ID} ({ARC_TESTNET_CHAIN_ID_HEX})"
            ),
            "endpoint": result.get("endpoint"),
        }
    return {
        "ok": True,
        "chainId": chain_id,
        "chainIdHex": chain_hex.lower(),
        "endpoint": result.get("endpoint"),
        "source": result.get("source"),
    }


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


def build_wallet_status_summary() -> dict[str, object]:
    """Return a combined wallet guard status summary."""

    env_state = summarize_environment(os.environ)
    return {
        "manifest": build_sdk_guard_manifest(),
        "environment": env_state,
        "safety": {
            "testnetOnly": True,
            "liveSdkExecution": False,
            "humanApprovalRequired": True,
            "privateKeysAccepted": False,
            "transactionBroadcast": False,
            "mainnetEnabled": False,
        },
    }


def get_usdc_balance(
    address: str,
    *,
    rpc_url: str | None = None,
    usdc_address: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 30,
) -> dict[str, object]:
    """Read-only: check USDC balance of an address on Arc Testnet via eth_call."""

    if not isinstance(address, str) or not _EVM_ADDRESS_RE.fullmatch(address):
        return {"ok": False, "error": "invalid EVM address", "address": address}
    source = os.environ if env is None else env
    configured_rpc = rpc_url or source.get("CIRCLE_RPC_URL")
    resolved_usdc = usdc_address or source.get("CIRCLE_USDC_TOKEN") or ARC_TESTNET_USDC_ADDRESS
    if not isinstance(resolved_usdc, str) or not _EVM_ADDRESS_RE.fullmatch(resolved_usdc):
        return {"ok": False, "error": "invalid USDC token address", "address": address}
    if int(resolved_usdc[2:], 16) == 0:
        return {"ok": False, "error": "USDC token address must not be the zero address", "address": address}
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return {"ok": False, "error": "timeout must be positive", "address": address}

    # balanceOf(address) selector = keccak256("balanceOf(address)")[:4] = 0x70a08231
    # padded address (32 bytes, left-padded with zeros)
    padded = "0x" + "0" * 24 + address[2:]
    data = f"0x70a08231{padded[2:]}"

    rpc_candidates: list[str] | None = None
    if configured_rpc:
        rpc_candidates = [configured_rpc]
        rpc_candidates.extend(
            value.strip()
            for value in source.get("ARC_RPC_FALLBACKS", "").split(",")
            if value.strip()
        )
        rpc_candidates.extend(ARC_RPC_FALLBACKS)

    try:
        health = check_arc_rpc_health(
            rpc_urls=rpc_candidates,
            env=source,
            timeout=timeout,
        )
        if not health.get("ok"):
            return {
                "ok": False,
                "error": f"RPC health check failed: {health.get('error')}",
                "address": address,
            }
        selected_rpc = health.get("endpoint")
        if not isinstance(selected_rpc, str):
            return {
                "ok": False,
                "error": "RPC health check did not return a selected endpoint",
                "address": address,
            }
        response = _rpc_call(
            selected_rpc,
            "eth_call",
            [{"to": resolved_usdc, "data": data}, "latest"],
            timeout,
        )
    except Exception as exc:
        return {"ok": False, "error": f"rpc call failed: {exc}", "address": address}

    result = response.get("result")
    if not isinstance(result, str) or not result.startswith("0x"):
        error = response.get("error", {})
        return {
            "ok": False,
            "error": error.get("message", f"unexpected RPC response: {response!r}"),
            "address": address,
        }

    try:
        raw_balance = int(result, 16)
    except (ValueError, TypeError):
        return {"ok": False, "error": f"could not decode balance hex: {result!r}", "address": address}

    display = f"{raw_balance / 10**6:.6f}"
    return {
        "ok": True,
        "address": address,
        "rawBalanceHex": result,
        "rawBalanceWei": raw_balance,
        "balanceUSDC": display,
        "decimals": 6,
        "network": "ARC-TESTNET",
        "chainId": ARC_TESTNET_CHAIN_ID,
        "rpcUrl": selected_rpc,
        "rpcSource": health.get("source"),
        "tokenAddress": resolved_usdc,
        "safety": {"readOnlyRpc": True, "noBroadcast": True, "noKeys": True},
    }


def _rpc_call(
    rpc_url: str,
    method: str,
    params: list[object],
    timeout: float,
) -> dict[str, object]:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode("utf-8")
    request = urllib_request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_RPC_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RPC_RESPONSE_BYTES:
        raise ValueError("RPC response exceeds the 1 MB safety limit")
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("RPC response must be a JSON object")
    return parsed


def prepare_send_intent(
    *,
    to_address: str,
    amount: str,
    network: str = "ARC-TESTNET",
    asset: str = "USDC",
) -> dict[str, object]:
    """Prepare a guarded USDC send intent for human review (NOT auto-executed)."""
    # Validate address
    if not isinstance(to_address, str) or not to_address.startswith("0x") or len(to_address) != 42:
        return {"ok": False, "error": "invalid EVM address", "toAddress": to_address}
    # Validate amount
    try:
        whole, dot, frac = amount.partition(".")
        if not whole.isdigit() or (dot and not frac.isdigit()):
            raise ValueError
        if len(frac) > 6:
            return {"ok": False, "error": "USDC amounts use at most 6 decimal places", "amount": amount}
        total = int(whole + (frac.ljust(6, "0") if dot else ""))
        if total <= 0:
            return {"ok": False, "error": "amount must be greater than zero", "amount": amount}
    except (ValueError, TypeError):
        return {"ok": False, "error": "amount must be a positive decimal string", "amount": amount}
    # Validate network is testnet
    if "mainnet" in network.lower():
        return {"ok": False, "error": f"mainnet network rejected (testnet-only): {network!r}", "network": network}

    return {
        "ok": True,
        "intent": {
            "network": network,
            "asset": asset,
            "amount": amount,
            "toAddress": to_address,
            "status": "pending_human_approval",
        },
        "execution": {
            "liveExecution": False,
            "humanApprovalRequired": True,
            "autoExecute": False,
            "transactionBroadcast": False,
        },
        "safety": {
            "testnetOnly": True,
            "humanApprovalRequired": True,
            "transactionBroadcast": False,
            "privateKeysAccepted": False,
            "readOnlyRpc": False,
            "mainnetEnabled": False,
            "autonomousSpending": False,
        },
        "nextSteps": [
            f"Verify recipient {to_address} on Arc Testnet (https://testnet.arcscan.app).",
            "Confirm amount and network in a human review.",
            "Execute actual USDC transfer via MetaMask, Circle SDK, or another wallet.",
            "After sending, verify receipt with: arc-builder x402 verify <url> <txhash>",
        ],
    }


__all__ = [
    "ACCOUNT_TYPES",
    "ARC_RPC_FALLBACKS",
    "ARC_TESTNET_BLOCKCHAIN",
    "ARC_TESTNET_CHAIN_ID",
    "ARC_TESTNET_CHAIN_ID_HEX",
    "ARC_TESTNET_RPC_URL",
    "ARC_TESTNET_USDC_ADDRESS",
    "MAX_WALLET_COUNT",
    "MAX_RPC_RESPONSE_BYTES",
    "READ_ONLY_RPC_METHODS",
    "REQUIRED_ENVIRONMENT",
    "RPC_CALL_TIMEOUT",
    "build_sdk_guard_manifest",
    "build_wallet_creation_plan",
    "build_wallet_status_summary",
    "check_arc_rpc_health",
    "generate_python_sdk_snippet",
    "get_usdc_balance",
    "prepare_send_intent",
    "rpc_call",
    "summarize_environment",
]
