"""
Circle Wallet SDK Client
------------------------
Thin Python wrapper around Circle's Developer-Controlled Wallets REST API.

Uses httpx for async HTTP calls. All secrets MUST come from environment
variables — never hardcode API keys or entity secrets.

Reference: https://developers.circle.com/wallets/api-reference
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx

CIRCLE_API_BASE = "https://api.circle.com/v1"
TIMEOUT_SEC = 30


# ── data models ─────────────────────────────────────────────────


@dataclass
class WalletInfo:
    id: str
    address: str
    blockchain: str
    account_type: str
    custody_type: str
    wallet_set_id: str
    name: str = ""
    state: str = "LIVE"


@dataclass
class Balance:
    amount: str
    currency: str
    blockchain: str


@dataclass
class TransactionResult:
    id: str
    state: str
    blockchain: str
    tx_hash: str = ""
    amount: str = ""
    currency: str = ""


# ── client ──────────────────────────────────────────────────────


class CircleWalletClient:
    """Python client for Circle Developer-Controlled Wallets API."""

    def __init__(
        self,
        api_key: str | None = None,
        entity_secret: str | None = None,
        base_url: str = CIRCLE_API_BASE,
        timeout: int = TIMEOUT_SEC,
    ) -> None:
        self._api_key = api_key or os.environ.get("CIRCLE_API_KEY", "")
        self._entity_secret = entity_secret or os.environ.get("CIRCLE_ENTITY_SECRET", "")
        if not self._api_key:
            raise ValueError(
                "CIRCLE_API_KEY is required — set the env var or pass api_key=."
            )
        if not self._entity_secret:
            raise ValueError(
                "CIRCLE_ENTITY_SECRET is required — set the env var or pass entity_secret=."
            )

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            timeout=httpx.Timeout(timeout),
        )

    # ── wallets ──────────────────────────────────────────────

    async def create_wallet_set(self, name: str = "Builder Kit Set") -> dict[str, Any]:
        """Create a new wallet set."""
        resp = await self._client.post(
            "/w3s/walletSets",
            json={"entitySecret": self._entity_secret, "name": name},
        )
        resp.raise_for_status()
        return resp.json()["data"]

    async def create_wallets(
        self,
        blockchain: str = "ARC-TESTNET",
        count: int = 1,
        wallet_set_id: str | None = None,
        account_type: str = "SCA",
    ) -> list[WalletInfo]:
        """Create developer-controlled wallets."""
        payload: dict[str, Any] = {
            "entitySecret": self._entity_secret,
            "blockchains": [blockchain],
            "count": count,
            "accountType": account_type,
        }
        if wallet_set_id:
            payload["walletSetId"] = wallet_set_id

        resp = await self._client.post("/w3s/wallets", json=payload)
        resp.raise_for_status()
        raw = resp.json()["data"]["wallets"]
        return [
            WalletInfo(
                id=w["id"],
                address=w["address"],
                blockchain=w.get("blockchain", blockchain),
                account_type=w.get("accountType", account_type),
                custody_type=w.get("custodyType", "DEVELOPER"),
                wallet_set_id=w.get("walletSetId", ""),
                name=w.get("name", ""),
                state=w.get("state", "LIVE"),
            )
            for w in raw
        ]

    async def list_wallets(self) -> list[WalletInfo]:
        """List all wallets in the account."""
        resp = await self._client.get("/w3s/wallets")
        resp.raise_for_status()
        raw = resp.json()["data"]["wallets"]
        return [
            WalletInfo(
                id=w["id"],
                address=w["address"],
                blockchain=w.get("blockchain", ""),
                account_type=w.get("accountType", ""),
                custody_type=w.get("custodyType", ""),
                wallet_set_id=w.get("walletSetId", ""),
                name=w.get("name", ""),
                state=w.get("state", "LIVE"),
            )
            for w in raw
        ]

    async def get_wallet(self, wallet_id: str) -> WalletInfo:
        """Get a single wallet by ID."""
        resp = await self._client.get(f"/w3s/wallets/{wallet_id}")
        resp.raise_for_status()
        w = resp.json()["data"]["wallet"]
        return WalletInfo(
            id=w["id"],
            address=w["address"],
            blockchain=w.get("blockchain", ""),
            account_type=w.get("accountType", ""),
            custody_type=w.get("custodyType", ""),
            wallet_set_id=w.get("walletSetId", ""),
            name=w.get("name", ""),
            state=w.get("state", "LIVE"),
        )

    # ── balances ─────────────────────────────────────────────

    async def get_balance(self, wallet_id: str) -> list[Balance]:
        """Get token balances for a wallet."""
        resp = await self._client.get(f"/w3s/wallets/{wallet_id}/balances")
        resp.raise_for_status()
        raw = resp.json()["data"]["tokenBalances"]
        return [
            Balance(
                amount=b.get("amount", "0"),
                currency=b.get("token", {}).get("name", "USDC"),
                blockchain=b.get("blockchain", ""),
            )
            for b in raw
        ]

    # ── transactions ─────────────────────────────────────────

    async def create_transaction(
        self,
        wallet_id: str,
        destination: str,
        amount: str,
        currency: str = "USDC",
        blockchain: str = "ARC-TESTNET",
        memo: str = "",
    ) -> TransactionResult:
        """Create and send a payment transaction."""
        payload: dict[str, Any] = {
            "entitySecret": self._entity_secret,
            "walletId": wallet_id,
            "destinationAddress": destination,
            "amount": amount,
            "tokenId": currency,
            "blockchain": blockchain,
        }
        if memo:
            payload["memo"] = memo

        resp = await self._client.post("/w3s/transactions", json=payload)
        resp.raise_for_status()
        tx = resp.json()["data"]["transaction"]
        return TransactionResult(
            id=tx["id"],
            state=tx.get("state", "PENDING"),
            blockchain=tx.get("blockchain", blockchain),
            tx_hash=tx.get("txHash", ""),
            amount=tx.get("amount", amount),
            currency=tx.get("tokenId", currency),
        )

    async def get_transaction(self, tx_id: str) -> TransactionResult:
        """Get transaction details by ID."""
        resp = await self._client.get(f"/w3s/transactions/{tx_id}")
        resp.raise_for_status()
        tx = resp.json()["data"]["transaction"]
        return TransactionResult(
            id=tx["id"],
            state=tx.get("state", "UNKNOWN"),
            blockchain=tx.get("blockchain", ""),
            tx_hash=tx.get("txHash", ""),
            amount=tx.get("amount", ""),
            currency=tx.get("tokenId", ""),
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ── sync helper (for testing) ────────────────────────────

    def _run_sync(self, coro):
        """Run an async method synchronously. For tests only."""
        import asyncio
        return asyncio.run(coro)
