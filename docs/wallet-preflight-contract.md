# Wallet preflight contract

> Scope: a secret-free contract for the **next** Arc Testnet wallet PR. It describes the exact data a future wallet adapter must display, validate, and freeze before a human can sign. This document does not connect a wallet, create a payment, submit a transaction, or store credentials.

## Why this exists

The current payment-intent playground already produces a local signing preflight report. Before adding any wallet adapter, the project needs a stable contract that reviewers can compare against the UI, tests, and future transaction builder.

Use this page as the handoff between:

1. the local-only playground;
2. a future browser-wallet preview PR;
3. a later human-approved testnet send PR.

## Non-negotiable boundary

The preflight contract is allowed to contain only public or user-entered payment intent fields:

- expected network and chain ID;
- connected wallet address, once a wallet preview exists;
- recipient address;
- asset symbol and token address;
- amount in decimal USDC;
- amount in ERC-20 base units;
- unsigned ERC-20 transaction draft fields for review (`to`, `value`, `data`, decoded recipient, decoded amount);
- memo / resource binding;
- expiry;
- guard reasons;
- user-visible approval state;
- transaction hash after a later send PR.

It must never contain:

- private keys;
- seed phrases;
- Circle API keys;
- Entity Secrets;
- OTP codes;
- raw authorization headers;
- production x402 payment proofs;
- hidden recipient or amount mutations.

## Required preflight fields

A future wallet adapter must render these fields before enabling any signing button.

| Field | Required value / source | Fail-closed rule |
| --- | --- | --- |
| `network.name` | `Arc Testnet` | Block if another network is selected. |
| `network.chainId` | `5042002` | Block unless the connected wallet reports this chain ID. |
| `network.chainIdHex` | `0x4cef52` | Block if decimal and hex chain IDs disagree. |
| `network.rpcUrl` | `https://rpc.testnet.arc.network` or a reviewed equivalent | Block if RPC status is unknown for a send PR. |
| `asset.symbol` | `USDC` for the first send PR | Block unsupported assets until a separate asset review exists. |
| `asset.tokenAddress` | `0x3600000000000000000000000000000000000000` | Block if the transfer target is not the reviewed Arc Testnet USDC interface. |
| `asset.decimals` | `6` | Block if amount parsing uses any other ERC-20 decimals. |
| `nativeGas.decimals` | `18` | Display only; never use this for ERC-20 transfer base units. |
| `intent.recipient` | 0x-prefixed 40-byte address | Block invalid, empty, or changed-after-review recipients. |
| `intent.amountDecimal` | positive decimal with at most 6 fractional digits | Block zero, negative, scientific notation, or more than 6 decimals. |
| `intent.amountBaseUnits` | deterministic 6-decimal parse of `amountDecimal` | Block if base units do not match the decimal display. |
| `transactionDraft.unsignedOnly` | `true` until a separate send PR | Block if a draft can trigger wallet UI by itself. |
| `transactionDraft.to` | reviewed Arc Testnet USDC token address | Block if transfer target differs from the reviewed token address. |
| `transactionDraft.value` | `0x0` for ERC-20 transfer | Block native-value transfers for the first USDC send PR. |
| `transactionDraft.data` | deterministic `transfer(address,uint256)` calldata | Block if decoded recipient or base units differ from the frozen intent. |
| `intent.memo` | visible user-facing description | Block hidden memo/resource changes after review starts. |
| `intent.expiry` | future timestamp | Block expired intents before signing. |
| `approval.humanRequired` | `true` | Block any auto-submit or unattended spending path. |
| `approval.finalConfirmation` | local-only marker before any later wallet request | Block unless user confirms the frozen fields immediately before wallet handoff. |
| `safety.transactionBroadcast` | `false` for preview PR, `true` only in a later send PR after wallet confirmation | Block any background broadcast. |

## JSON shape

The local playground or a future wallet-preview component should be able to produce a report with this shape:

```json
{
  "walletAction": "blocked",
  "nextRequiredReview": "separate testnet-only wallet PR",
  "network": {
    "name": "Arc Testnet",
    "chainId": 5042002,
    "chainIdHex": "0x4cef52",
    "rpcUrl": "https://rpc.testnet.arc.network",
    "explorerUrl": "https://testnet.arcscan.app"
  },
  "asset": {
    "symbol": "USDC",
    "tokenAddress": "0x3600000000000000000000000000000000000000",
    "decimals": 6,
    "nativeGasDecimals": 18
  },
  "intent": {
    "recipient": "0x1111111111111111111111111111111111111111",
    "amountDecimal": "5.00",
    "amountBaseUnits": "5000000",
    "memo": "Paid data/API task for Arc market research report.",
    "expiry": "2026-05-30T00:00"
  },
  "transactionDraft": {
    "type": "unsigned_erc20_transfer_preview",
    "unsignedOnly": true,
    "walletRequestEnabled": false,
    "to": "0x3600000000000000000000000000000000000000",
    "value": "0x0",
    "data": "0xa9059cbb000000000000000000000000111111111111111111111111111111111111111100000000000000000000000000000000000000000000000000000000004c4b40",
    "decoded": {
      "method": "transfer(address,uint256)",
      "recipient": "0x1111111111111111111111111111111111111111",
      "amountBaseUnits": "5000000"
    }
  },
  "approval": {
    "humanRequired": true,
    "status": "ready_for_review",
    "finalConfirmation": {
      "recorded": false,
      "transactionRequestEnabled": false
    }
  },
  "safety": {
    "walletConnected": false,
    "backendCalls": false,
    "transactionBroadcast": false,
    "autonomousSpending": false
  },
  "guardReasons": [
    "Wrong chain: expected Arc Testnet chain ID 5042002 (0x4cef52).",
    "RPC unavailable: no live browser RPC probe is enabled in this local-only demo.",
    "User approval required: real signing must open an external wallet confirmation."
  ]
}
```

## Preview PR acceptance criteria

The first wallet-related PR should still avoid sending funds. It is acceptable when all of these are true:

- [x] Wallet detection is optional and feature-flagged.
- [x] Wrong-chain state is visible and blocks all signing controls.
- [x] Connected address is displayed before review when an injected wallet exposes it without a permission request.
- [x] The preflight report can be copied without network writes.
- [x] Recipient, amount, token address, chain ID, memo, and expiry are frozen once review starts.
- [x] Final local confirmation is explicit and still does not enable a transaction request.
- [x] Unsigned transaction draft is inspectable and cannot trigger a wallet request.
- [x] The app cannot call `sendTransaction`, `eth_sendTransaction`, or equivalent write APIs.
- [x] Tests prove that the no-broadcast path remains default.
- [x] The local playground remains usable when no wallet is present.

## Send PR acceptance criteria

A later send PR may submit a testnet transaction only if all preview criteria are already met and these additional rules pass:

- [ ] Unsigned transaction draft decodes back to the frozen recipient, amount, token address, and chain before wallet handoff.
- [ ] The user clicks an explicit final confirmation button.
- [ ] The wallet confirmation dialog is the only signing path.
- [ ] The transfer is Arc Testnet only.
- [ ] ERC-20 base units are derived from 6 decimals, not native gas decimals.
- [ ] The recipient and amount cannot change between preflight and wallet request.
- [ ] The UI records the returned transaction hash and links to ArcScan.
- [ ] Receipt polling is read-only and handles pending, confirmed, failed, and unknown states.
- [ ] Rejection, timeout, wrong chain, and RPC errors fail closed without retrying automatically.

## Reviewer checklist

Before approving any wallet PR, verify:

1. No private key, seed phrase, API key, Entity Secret, or payment proof appears in the diff.
2. No default mainnet chain or fallback exists.
3. No background timer can trigger a wallet request.
4. No hidden field can replace recipient, token address, amount, memo, or chain ID after review.
5. Browser console does not log authorization headers, wallet payloads, or opaque payment proofs.
6. The static local demo still works without a wallet extension installed.

## Current status

This repository currently implements the safe local side of the contract: deterministic amount parsing, optional read-only injected-wallet preview state, explicit wrong-chain/provider/account guard reasons, frozen reviewed intent fields, a copyable preflight report, and disabled wallet actions. Real wallet permission requests, signing, and transaction submission remain future work and must land in separate reviewed PRs.
