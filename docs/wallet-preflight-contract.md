# Wallet preflight contract

> Scope: a secret-free contract shared by the local payment-intent playground and the separate guarded Arc Testnet send lab. It describes the exact data a wallet adapter must display, validate, and freeze before a human can approve a request. This document itself does not connect a wallet, create a payment, submit a transaction, or store credentials.

## Why this exists

The payment-intent playground produces a local signing preflight report, and the separate guarded lab implements the narrow browser-wallet send slice. Reviewers need one stable contract they can compare against both UIs, their tests, and any later extension.

Use this page as the handoff between:

1. the local-only playground;
2. the separate disabled-by-default guarded Arc Testnet send lab;
3. any later wallet, verifier, custody, or mainnet proposal that requires its own review.

## Non-negotiable boundary

The preflight contract is allowed to contain only public or user-entered payment intent fields:

- expected network and chain ID;
- connected wallet address, once a wallet preview exists;
- recipient address;
- asset symbol and token address;
- amount in decimal USDC;
- amount in ERC-20 base units;
- unsigned ERC-20 transaction draft fields for review (`to`, `value`, `data`, decoded recipient, decoded amount);
- transaction draft consistency checks that decode calldata back to reviewed fields;
- wallet handoff readiness manifest fields (`walletRequestEnabled`, `canRequestWallet`, `sendPrRequired`, required guard IDs);
- memo / resource binding;
- expiry;
- guard reasons;
- user-visible approval state;
- transaction hash returned by the guarded send lab after wallet confirmation.

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

The guarded wallet adapter must render these fields before enabling its transaction-request button.

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
| `transactionDraft.unsignedOnly` | `true` in the local playground; the guarded lab freezes the same draft before wallet handoff | Block if draft creation itself can trigger wallet UI. |
| `transactionDraft.to` | reviewed Arc Testnet USDC token address | Block if transfer target differs from the reviewed token address. |
| `transactionDraft.value` | `0x0` for ERC-20 transfer | Block native-value transfers for the first USDC send PR. |
| `transactionDraft.data` | deterministic `transfer(address,uint256)` calldata | Block if decoded recipient or base units differ from the frozen intent. |
| `transactionDraftConsistency.allPassed` | `true` before the guarded wallet handoff | Block if calldata cannot be decoded back to the reviewed recipient and amount. |
| `walletHandoffReadiness.walletRequestEnabled` | `false` in the local playground | Block the local preview from opening a wallet request. |
| `walletHandoffReadiness.canRequestWallet` | `false` in the local playground | Block if local guard manifests can flip into a wallet action. |
| `walletHandoffReadiness.sendPrRequired` | `true` in the local playground | Keep wallet/send isolated from preview guards. |
| `walletHandoffReadiness.requiredBeforeSend` | validation, frozen intent, human approval, final confirmation, draft consistency, wallet chain proof | Block if any required guard is omitted from the handoff manifest. |
| `intent.memo` | visible user-facing description | Block hidden memo/resource changes after review starts. |
| `intent.expiry` | future timestamp | Block expired intents before signing. |
| `approval.humanRequired` | `true` | Block any auto-submit or unattended spending path. |
| `approval.finalConfirmation` | local marker before any guarded wallet request | Block unless user confirms the frozen fields immediately before wallet handoff. |
| `safety.transactionBroadcast` | `false` in local preview; the guarded lab can request one wallet transaction only after confirmation | Block any background or repeated broadcast. |

## JSON shape

The local playground produces a report with this shape:

```json
{
  "walletAction": "blocked",
  "nextRequiredReview": "separate guarded Arc Testnet send lab",
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
    "expiry": "2030-05-30T00:00"
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
  "transactionDraftConsistency": {
    "type": "local_unsigned_transaction_consistency_check",
    "localOnly": true,
    "walletRequestEnabled": false,
    "allPassed": true,
    "decodedCalldata": {
      "method": "transfer(address,uint256)",
      "recipient": "0x1111111111111111111111111111111111111111",
      "amountBaseUnits": "5000000"
    }
  },
  "walletHandoffReadiness": {
    "type": "wallet_handoff_readiness_manifest",
    "localOnly": true,
    "walletRequestEnabled": false,
    "canRequestWallet": false,
    "sendPrRequired": true,
    "allLocalPrerequisitesPassed": false,
    "requiredBeforeSend": [
      "valid-intent-fields",
      "frozen-intent-present",
      "human-approval-recorded",
      "final-confirmation-recorded",
      "unsigned-draft-consistent",
      "wallet-chain-observed",
      "wallet-request-still-disabled"
    ]
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
- [x] Unsigned transaction draft consistency is checked by decoding calldata back to reviewed fields.
- [x] Wallet handoff readiness manifest keeps wallet requests disabled and lists required send-PR guards.
- [x] The local playground cannot call `sendTransaction`, `eth_sendTransaction`, or equivalent write APIs.
- [x] Tests prove that the no-broadcast path remains default in the local playground.
- [x] The local playground remains usable when no wallet is present.

## Send PR acceptance criteria

The separate guarded Arc Testnet send lab may submit one testnet transaction only if all preview criteria are already met and these additional rules pass:

- [ ] Wallet handoff readiness manifest passes immediately before wallet prompt creation.
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

This repository implements the safe local side of the contract in the payment-intent playground: deterministic amount parsing, optional read-only injected-wallet preview state, explicit wrong-chain/provider/account guard reasons, frozen reviewed intent fields, unsigned transaction draft generation, calldata consistency checks, a wallet handoff readiness manifest, a copyable preflight report, and disabled wallet actions. A separate disabled-by-default Arc Testnet lab implements the narrow reviewed send slice with an injected user-controlled wallet. Custody, mainnet, autonomous spending, and live settlement remain future work requiring separate security reviews.
