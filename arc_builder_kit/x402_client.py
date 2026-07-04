#!/usr/bin/env python3
"""x402 challenge/response client for Arc Testnet.

This module is a *helper* that prepares and verifies x402 payment flows.
It does NOT send transactions, sign messages, or handle private keys.

Flow:
1. ``fetch_challenge(url)`` — HTTP GET to an x402-enabled endpoint.
   The server returns HTTP 402 with a payment challenge body.
2. ``parse_challenge(body)`` — parse the challenge JSON (accepts an array
   with scheme/network/asset/amount/payTo).
3. ``prepare_payment_intent(challenge)`` — build a reviewable, human-approved
   payment intent JSON. This is NOT auto-executed.
4. ``verify_receipt(tx_hash, challenge, ...)`` — verify a payment receipt by
   checking on-chain USDC Transfer events via Arc Testnet RPC
   (https://rpc.testnet.arc.network). Read-only calls only:
   eth_getTransactionReceipt, eth_getTransactionByHash.

Safety:
- No private keys, no signing, no transaction broadcast.
- Human approval required for every payment step.
- testnet-only (chainId 5042002, fail-closed on mainnet).
- Read-only RPC calls only.
- The client prepares and verifies — it does NOT send transactions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from urllib import error as urllib_error
from urllib import request as urllib_request

# ---------------------------------------------------------------------------
# Arc Testnet constants (sourced from config/arc_testnet.facts.json)
# ---------------------------------------------------------------------------

ARC_TESTNET_CHAIN_ID = 5042002
ARC_TESTNET_CHAIN_ID_HEX = "0x4cef52"
ARC_TESTNET_RPC_URL = "https://rpc.testnet.arc.network"
ARC_TESTNET_EXPLORER_URL = "https://testnet.arcscan.app"

# ERC-20 USDC on Arc Testnet
USDC_CONTRACT_ADDRESS = "0x3600000000000000000000000000000000000000"
USDC_DECIMALS = 6

# The Transfer event signature for ERC-20 tokens:
# Transfer(address indexed from, address indexed to, uint256 value)
# keccak256("Transfer(address,address,uint256)") =
# 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Safety flags
SAFETY_FLAGS: dict[str, Any] = {
    "testnetOnly": True,
    "humanApprovalRequired": True,
    "transactionBroadcast": False,
    "privateKeysAccepted": False,
    "noSigning": True,
    "noBroadcast": True,
    "readOnlyRpc": True,
    "autonomousSpending": False,
    "mainnetEnabled": False,
}

# Regex for EVM addresses and transaction hashes
EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
TX_HASH_RE = re.compile(r"^0x[a-fA-F0-9]{64}$")

# HTTP status for Payment Required
HTTP_PAYMENT_REQUIRED = 402

# Maximum response body size (1 MB)
MAX_RESPONSE_BYTES = 1_048_576

# Request timeout in seconds
REQUEST_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChallengeRequirement:
    """A single payment requirement from a 402 challenge."""

    scheme: str
    network: str
    asset: str
    amount: str
    pay_to: str

    def to_dict(self) -> dict[str, str]:
        return {
            "scheme": self.scheme,
            "network": self.network,
            "asset": self.asset,
            "amount": self.amount,
            "payTo": self.pay_to,
        }


@dataclass(frozen=True)
class ParsedChallenge:
    """A parsed 402 challenge with all payment requirements."""

    raw: dict[str, Any]
    requirements: tuple[ChallengeRequirement, ...]
    resource: str | None = None
    accepts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "requirements": [r.to_dict() for r in self.requirements],
            "resource": self.resource,
            "accepts": self.accepts,
        }


@dataclass(frozen=True)
class PaymentIntent:
    """A reviewable, human-approved payment intent (NOT auto-executed)."""

    network: str
    asset: str
    amount: str
    pay_to: str
    resource: str | None
    status: str  # always "pending_human_approval"
    human_approval_required: bool = True
    auto_execute: bool = False
    transaction_broadcast: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "network": self.network,
            "asset": self.asset,
            "amount": self.amount,
            "payTo": self.pay_to,
            "resource": self.resource,
            "status": self.status,
            "humanApprovalRequired": self.human_approval_required,
            "autoExecute": self.auto_execute,
            "transactionBroadcast": self.transaction_broadcast,
        }


@dataclass(frozen=True)
class ReceiptVerification:
    """Result of verifying an on-chain payment receipt."""

    verified: bool
    tx_hash: str
    chain_id: int | None = None
    from_address: str | None = None
    to_address: str | None = None
    transfer_found: bool = False
    status: str | None = None
    reason: str = ""
    raw_receipt: dict[str, Any] | None = None
    raw_transaction: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "txHash": self.tx_hash,
            "chainId": self.chain_id,
            "from": self.from_address,
            "to": self.to_address,
            "transferFound": self.transfer_found,
            "status": self.status,
            "reason": self.reason,
            "rawReceipt": self.raw_receipt,
            "rawTransaction": self.raw_transaction,
        }


@dataclass(frozen=True)
class X402Result:
    """Structured result containing all x402 flow data and safety flags."""

    challenge: ParsedChallenge | None
    payment_intent: PaymentIntent | None
    receipt_verification: ReceiptVerification | None
    safety: dict[str, Any]
    resource_content: str | None = None
    resource_status: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenge": self.challenge.to_dict() if self.challenge else None,
            "paymentIntent": self.payment_intent.to_dict() if self.payment_intent else None,
            "receiptVerification": (
                self.receipt_verification.to_dict() if self.receipt_verification else None
            ),
            "safety": self.safety,
            "resourceContent": self.resource_content,
            "resourceStatus": self.resource_status,
        }


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_evm_address(address: str) -> str:
    """Validate and return a 42-character EVM address."""
    if not isinstance(address, str):
        raise ValueError("EVM address must be a string")
    if not EVM_ADDRESS_RE.match(address):
        raise ValueError(
            f"invalid EVM address: {address!r}; expected 0x-prefixed 40 hex chars"
        )
    return address


def validate_tx_hash(tx_hash: str) -> str:
    """Validate and return a 66-character transaction hash."""
    if not isinstance(tx_hash, str):
        raise ValueError("transaction hash must be a string")
    if not TX_HASH_RE.match(tx_hash):
        raise ValueError(
            f"invalid transaction hash: {tx_hash!r}; expected 0x-prefixed 64 hex chars"
        )
    return tx_hash


def validate_amount(amount: str) -> str:
    """Validate a decimal USDC amount string."""
    if not isinstance(amount, str) or not amount:
        raise ValueError("amount must be a non-empty string")
    whole, dot, fractional = amount.partition(".")
    if not whole.isdigit() or (dot and not fractional.isdigit()):
        raise ValueError(f"amount must be a positive decimal string: {amount!r}")
    if len(fractional) > USDC_DECIMALS:
        raise ValueError(f"USDC amounts use at most {USDC_DECIMALS} decimal places")
    return amount


def validate_network(network: str) -> str:
    """Validate the network identifier. Must be arc-testnet or known testnet."""
    if not isinstance(network, str) or not network:
        raise ValueError("network must be a non-empty string")
    # Fail-closed: reject known mainnet identifiers
    mainnet_indicators = ("mainnet", "ethereum", "homestead", "1", "137", "42161")
    normalized = network.lower().strip()
    for indicator in mainnet_indicators:
        if normalized == indicator or normalized.endswith(f"-{indicator}"):
            raise ValueError(
                f"mainnet network rejected (testnet-only): {network!r}"
            )
    return network


# ---------------------------------------------------------------------------
# Challenge parsing
# ---------------------------------------------------------------------------


def parse_challenge(body: Any) -> ParsedChallenge:
    """Parse a 402 challenge JSON body.

    Accepts a challenge body that may contain:
    - An ``accepts`` array with objects having scheme/network/asset/amount/payTo
    - A top-level array of requirement objects
    - A single requirement object
    """
    if isinstance(body, str):
        body = json.loads(body)
    if not isinstance(body, dict):
        raise ValueError(f"challenge body must be a JSON object, got {type(body).__name__}")

    # Extract the accepts array — this is the standard x402 challenge shape
    accepts = body.get("accepts", [])
    if not isinstance(accepts, list):
        raise ValueError("challenge 'accepts' must be an array")

    requirements: list[ChallengeRequirement] = []
    for entry in accepts:
        req = _parse_requirement(entry)
        requirements.append(req)

    if not requirements:
        # Some challenges may put the requirement at top level
        if "scheme" in body and "network" in body:
            req = _parse_requirement(body)
            requirements.append(req)
        else:
            raise ValueError("challenge has no payment requirements (empty 'accepts')")

    resource = body.get("resource")
    return ParsedChallenge(
        raw=body,
        requirements=tuple(requirements),
        resource=resource if isinstance(resource, str) else None,
        accepts=accepts,
    )


def _parse_requirement(entry: Any) -> ChallengeRequirement:
    """Parse a single payment requirement object."""
    if not isinstance(entry, dict):
        raise ValueError(
            f"payment requirement must be an object, got {type(entry).__name__}"
        )
    scheme = entry.get("scheme", "exact")
    network = entry.get("network", "")
    asset = entry.get("asset", "")
    amount = entry.get("amount", "")
    pay_to = entry.get("payTo", entry.get("pay_to", ""))

    if not isinstance(scheme, str) or not scheme:
        raise ValueError("payment requirement 'scheme' must be a non-empty string")
    if not isinstance(network, str) or not network:
        raise ValueError("payment requirement 'network' must be a non-empty string")
    if not isinstance(asset, str) or not asset:
        raise ValueError("payment requirement 'asset' must be a non-empty string")
    validate_amount(amount)
    validate_evm_address(pay_to)
    validate_network(network)

    return ChallengeRequirement(
        scheme=scheme,
        network=network,
        asset=asset,
        amount=amount,
        pay_to=pay_to,
    )


# ---------------------------------------------------------------------------
# Payment intent preparation
# ---------------------------------------------------------------------------


def prepare_payment_intent(challenge: ParsedChallenge) -> PaymentIntent:
    """Prepare a reviewable, human-approved payment intent.

    The intent is NOT auto-executed. It must be reviewed and approved by a
    human before any transaction is made (outside this client).
    """
    if not challenge.requirements:
        raise ValueError("cannot prepare payment intent: challenge has no requirements")
    req = challenge.requirements[0]
    return PaymentIntent(
        network=req.network,
        asset=req.asset,
        amount=req.amount,
        pay_to=req.pay_to,
        resource=challenge.resource,
        status="pending_human_approval",
        human_approval_required=True,
        auto_execute=False,
        transaction_broadcast=False,
    )


# ---------------------------------------------------------------------------
# HTTP challenge fetching
# ---------------------------------------------------------------------------


def fetch_challenge(url: str, *, timeout: float = REQUEST_TIMEOUT_SECONDS) -> X402Result:
    """Fetch a 402 challenge from an x402-enabled endpoint.

    Performs an HTTP GET. If the server returns 402, parses the challenge body.
    If the server returns 200 (e.g. after a payment proof header), returns the
    resource content.
    """
    if not isinstance(url, str) or not url:
        raise ValueError("url must be a non-empty string")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("url must start with http:// or https://")

    req = urllib_request.Request(url, method="GET")
    req.add_header("Accept", "application/json")

    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body_bytes = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(body_bytes) > MAX_RESPONSE_BYTES:
                raise ValueError("response body exceeds 1 MB safety limit")
            body_text = body_bytes.decode("utf-8")
    except urllib_error.HTTPError as exc:
        status = exc.code
        body_bytes = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(body_bytes) > MAX_RESPONSE_BYTES:
            raise ValueError("response body exceeds 1 MB safety limit") from exc
        body_text = body_bytes.decode("utf-8")
    except urllib_error.URLError as exc:
        raise ValueError(f"failed to fetch challenge from {url}: {exc.reason}") from exc

    # Try to parse JSON
    try:
        body_json: Any = json.loads(body_text)
    except json.JSONDecodeError:
        body_json = None

    if status == HTTP_PAYMENT_REQUIRED and body_json is not None:
        challenge = parse_challenge(body_json)
        intent = prepare_payment_intent(challenge)
        return X402Result(
            challenge=challenge,
            payment_intent=intent,
            receipt_verification=None,
            safety=SAFETY_FLAGS,
            resource_content=None,
            resource_status=status,
        )

    # Non-402 response: return the resource content
    return X402Result(
        challenge=None,
        payment_intent=None,
        receipt_verification=None,
        safety=SAFETY_FLAGS,
        resource_content=body_text if status == 200 else None,
        resource_status=status,
    )


# ---------------------------------------------------------------------------
# RPC helpers (read-only)
# ---------------------------------------------------------------------------


def _rpc_call(
    method: str,
    params: list[Any],
    *,
    rpc_url: str = ARC_TESTNET_RPC_URL,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> Any:
    """Make a read-only JSON-RPC call to an Ethereum-compatible RPC endpoint."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }).encode("utf-8")

    req = urllib_request.Request(rpc_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            body_bytes = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(body_bytes) > MAX_RESPONSE_BYTES:
                raise ValueError("RPC response exceeds 1 MB safety limit")
            result = json.loads(body_bytes.decode("utf-8"))
    except urllib_error.URLError as exc:
        raise ValueError(f"RPC call failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"RPC response was not valid JSON: {exc}") from exc

    if "error" in result:
        raise ValueError(f"RPC error: {result['error']}")
    return result.get("result")


def get_transaction_receipt(
    tx_hash: str,
    *,
    rpc_url: str = ARC_TESTNET_RPC_URL,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """Read-only: fetch a transaction receipt via eth_getTransactionReceipt."""
    validate_tx_hash(tx_hash)
    result = _rpc_call(
        "eth_getTransactionReceipt",
        [tx_hash],
        rpc_url=rpc_url,
        timeout=timeout,
    )
    if result is None:
        return None
    if not isinstance(result, dict):
        raise ValueError("RPC returned non-object receipt")
    return result


def get_transaction_by_hash(
    tx_hash: str,
    *,
    rpc_url: str = ARC_TESTNET_RPC_URL,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """Read-only: fetch a transaction via eth_getTransactionByHash."""
    validate_tx_hash(tx_hash)
    result = _rpc_call(
        "eth_getTransactionByHash",
        [tx_hash],
        rpc_url=rpc_url,
        timeout=timeout,
    )
    if result is None:
        return None
    if not isinstance(result, dict):
        raise ValueError("RPC returned non-object transaction")
    return result


def get_chain_id(
    *,
    rpc_url: str = ARC_TESTNET_RPC_URL,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> int:
    """Read-only: fetch the chain ID via eth_chainId."""
    result = _rpc_call("eth_chainId", [], rpc_url=rpc_url, timeout=timeout)
    if not isinstance(result, str):
        raise ValueError(f"eth_chainId returned non-string: {result!r}")
    # Parse hex chain ID
    chain_id = int(result, 16)
    return chain_id


# ---------------------------------------------------------------------------
# Receipt verification
# ---------------------------------------------------------------------------


def _decode_hex_amount(hex_amount: str) -> int:
    """Decode a hex-encoded uint256 amount to int."""
    if not isinstance(hex_amount, str) or not hex_amount.startswith("0x"):
        raise ValueError(f"invalid hex amount: {hex_amount!r}")
    return int(hex_amount, 16)


def _check_transfer_event(
    log: dict[str, Any],
    expected_pay_to: str | None,
) -> tuple[bool, str | None, str | None, int | None]:
    """Check if a log entry is a USDC Transfer event.

    Returns (is_transfer, from_address, to_address, amount).
    """
    topics = log.get("topics", [])
    if not isinstance(topics, list) or len(topics) < 3:
        return False, None, None, None

    # First topic should be the Transfer event signature
    if topics[0] != TRANSFER_EVENT_TOPIC:
        return False, None, None, None

    # Check the log address is the USDC contract
    log_address = log.get("address", "")
    if log_address.lower() != USDC_CONTRACT_ADDRESS.lower():
        return False, None, None, None

    # topics[1] = from (padded to 32 bytes), topics[2] = to (padded to 32 bytes)
    try:
        from_address = "0x" + topics[1][-40:]
        to_address = "0x" + topics[2][-40:]
    except (IndexError, TypeError):
        return False, None, None, None

    # Decode the amount from data
    data = log.get("data", "0x0")
    try:
        amount = _decode_hex_amount(data)
    except ValueError:
        amount = 0

    # If we have an expected pay_to, check it matches
    if expected_pay_to is not None:
        if to_address.lower() != expected_pay_to.lower():
            return False, None, None, None

    return True, from_address, to_address, amount


def verify_receipt(
    tx_hash: str,
    challenge: ParsedChallenge | None = None,
    *,
    rpc_url: str = ARC_TESTNET_RPC_URL,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
    expected_pay_to: str | None = None,
    expected_chain_id: int = ARC_TESTNET_CHAIN_ID,
) -> ReceiptVerification:
    """Verify a payment receipt by checking on-chain USDC Transfer events.

    Uses read-only RPC calls only:
    - eth_getTransactionReceipt
    - eth_getTransactionByHash

    Fail-closed on mainnet (wrong chain ID).
    """
    validate_tx_hash(tx_hash)

    # Determine expected pay_to
    if expected_pay_to is None and challenge is not None:
        if challenge.requirements:
            expected_pay_to = challenge.requirements[0].pay_to

    # Fetch transaction receipt
    try:
        receipt = get_transaction_receipt(tx_hash, rpc_url=rpc_url, timeout=timeout)
    except ValueError as exc:
        return ReceiptVerification(
            verified=False,
            tx_hash=tx_hash,
            reason=f"rpc_error: {exc}",
        )

    if receipt is None:
        return ReceiptVerification(
            verified=False,
            tx_hash=tx_hash,
            reason="transaction_not_found",
        )

    # Fetch transaction for chain ID verification
    try:
        transaction = get_transaction_by_hash(tx_hash, rpc_url=rpc_url, timeout=timeout)
    except ValueError as exc:
        return ReceiptVerification(
            verified=False,
            tx_hash=tx_hash,
            reason=f"rpc_error_getting_transaction: {exc}",
            raw_receipt=receipt,
        )

    if transaction is None:
        return ReceiptVerification(
            verified=False,
            tx_hash=tx_hash,
            reason="transaction_not_found",
            raw_receipt=receipt,
        )

    # Check transaction status (1 = success, 0 = failure)
    tx_status = receipt.get("status")
    if tx_status == "0x0":
        return ReceiptVerification(
            verified=False,
            tx_hash=tx_hash,
            reason="transaction_reverted",
            status="reverted",
            raw_receipt=receipt,
            raw_transaction=transaction,
        )

    # Check chain ID from transaction
    tx_chain_id_hex = transaction.get("chainId")
    if tx_chain_id_hex is not None:
        try:
            tx_chain_id = int(tx_chain_id_hex, 16)
        except (ValueError, TypeError):
            tx_chain_id = None

        if tx_chain_id is not None and tx_chain_id != expected_chain_id:
            return ReceiptVerification(
                verified=False,
                tx_hash=tx_hash,
                chain_id=tx_chain_id,
                reason=(
                    f"wrong_chain_id: expected {expected_chain_id}, "
                    f"got {tx_chain_id}"
                ),
                status="wrong_chain",
                raw_receipt=receipt,
                raw_transaction=transaction,
            )

    # Check for USDC Transfer events in the receipt logs
    logs = receipt.get("logs", [])
    if not isinstance(logs, list):
        logs = []

    transfer_found = False
    from_address: str | None = None
    to_address: str | None = None

    for log in logs:
        if not isinstance(log, dict):
            continue
        is_transfer, frm, to, _amount = _check_transfer_event(log, expected_pay_to)
        if is_transfer:
            transfer_found = True
            from_address = frm
            to_address = to
            break

    if not transfer_found:
        return ReceiptVerification(
            verified=False,
            tx_hash=tx_hash,
            transfer_found=False,
            reason="no_usdc_transfer_event_found",
            status="no_transfer",
            raw_receipt=receipt,
            raw_transaction=transaction,
        )

    return ReceiptVerification(
        verified=True,
        tx_hash=tx_hash,
        chain_id=expected_chain_id,
        from_address=from_address,
        to_address=to_address,
        transfer_found=True,
        status="verified",
        reason="usdc_transfer_event_confirmed",
        raw_receipt=receipt,
        raw_transaction=transaction,
    )


# ---------------------------------------------------------------------------
# Full paid request flow
# ---------------------------------------------------------------------------


def paid_request(
    url: str,
    payment_proof: str | None = None,
    *,
    rpc_url: str = ARC_TESTNET_RPC_URL,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> X402Result:
    """Handle an x402 paid request.

    If no payment_proof (transaction hash) is provided:
    - Fetches the 402 challenge and returns it for human review.

    If a payment_proof (transaction hash) is provided:
    - Verifies the on-chain receipt against Arc Testnet RPC.
    - If verified, fetches the protected resource with the payment proof header.
    """
    if payment_proof is None or payment_proof == "":
        # Phase 1: fetch challenge for human review
        return fetch_challenge(url, timeout=timeout)

    # Phase 2: verify receipt and fetch protected resource
    validate_tx_hash(payment_proof)

    # First fetch the challenge to know what we're verifying against
    challenge_result = fetch_challenge(url, timeout=timeout)
    challenge = challenge_result.challenge

    # Verify the on-chain receipt
    verification = verify_receipt(
        payment_proof,
        challenge=challenge,
        rpc_url=rpc_url,
        timeout=timeout,
    )

    # Build the result
    intent = (
        prepare_payment_intent(challenge) if challenge else None
    )

    # If verified, try to fetch the protected resource with the payment header
    resource_content = None
    resource_status = None
    if verification.verified:
        req = urllib_request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        req.add_header("X-Payment", payment_proof)
        try:
            with urllib_request.urlopen(req, timeout=timeout) as resp:
                resource_status = resp.status
                body_bytes = resp.read(MAX_RESPONSE_BYTES + 1)
                if len(body_bytes) <= MAX_RESPONSE_BYTES:
                    resource_content = body_bytes.decode("utf-8")
        except urllib_error.HTTPError as exc:
            resource_status = exc.code
        except urllib_error.URLError:
            resource_status = None

    return X402Result(
        challenge=challenge,
        payment_intent=intent,
        receipt_verification=verification,
        safety=SAFETY_FLAGS,
        resource_content=resource_content,
        resource_status=resource_status,
    )
