# Agent commerce components

Reusable local-first components for Arc agent-commerce demos. These are product and data-shape primitives, not wallet code. Use them to make future Arc Testnet PRs smaller, easier to review, and safer to hand off.

## Safety boundary

- Local-only first: components create reviewable JSON and UI states before any wallet integration.
- No private keys, seed phrases, entity secrets, or browser wallet requests.
- No transaction broadcast, no autonomous spending, no mainnet path.
- Human approval remains mandatory before any future Arc Testnet send step.
- Arc facts must stay source-grounded: chain ID `5042002`, Arc Testnet only, USDC as the native gas asset, ERC-20 USDC uses 6 decimals.

## Component set

### Agent card

Purpose: show who is asking for payment or offering work.

Required fields:

- `agentId` — stable local identifier or future ERC-8004 identity pointer.
- `displayName` — human-readable agent name.
- `role` — e.g. `research`, `api-gateway`, `creator-payout-agent`, `escrow-worker`.
- `trustLevel` — local label such as `unverified`, `docs-grounded`, or `reviewed`.
- `sourceNotes` — what docs, prompts, or manifests back the agent claim.

Never include secrets, API keys, private prompts, or signing authority in the card.

### Payment request card

Purpose: freeze the money-relevant fields before a user reviews or a future wallet adapter signs.

Required fields:

- `intentId`
- `purpose`
- `recipient`
- `amount`
- `asset: USDC`
- `assetDecimals: 6`
- `network: arc-testnet`
- `chainId: 5042002`
- `expiresAt`
- `humanApprovalRequired: true`

Do not let AI-generated copy silently mutate recipient, amount, asset, chain, or expiry after review.

### Receipt card

Purpose: make result verification observable.

Required fields:

- `receiptId`
- `intentId`
- `status` — `not_checked`, `pending`, `confirmed`, `failed`, `simulated`.
- `transactionHash` — optional until a real testnet transaction exists.
- `explorerUrl` — ArcScan URL only when a hash is present.
- `checks` — list of pass/fail checks for chain, asset, recipient, amount, expiry, and intent binding.

### Event log

Purpose: show what happened without hiding approval boundaries.

Required fields:

- `at`
- `actor` — `human`, `agent`, `system`, or `verifier`.
- `event`
- `requiresHumanReview`
- `walletActionEnabled`
- `transactionBroadcast`

A useful log separates agent suggestions from human approvals and verifier observations.

## Starter object

```json
{
  "schema": "arc-mcp-builder-assistant.agentCommerce.components.v1",
  "network": {
    "name": "arc-testnet",
    "chainId": 5042002,
    "nativeGasAsset": "USDC",
    "erc20UsdcDecimals": 6
  },
  "agent": {
    "agentId": "research-agent.local",
    "displayName": "Research Agent",
    "role": "docs-grounded-research",
    "trustLevel": "unverified-local-demo"
  },
  "paymentRequest": {
    "intentId": "intent-local-001",
    "purpose": "Pay for a cited Arc docs summary",
    "recipient": "0x1111111111111111111111111111111111111111",
    "amount": "3.50",
    "asset": "USDC",
    "assetDecimals": 6,
    "network": "arc-testnet",
    "chainId": 5042002,
    "humanApprovalRequired": true
  },
  "receipt": {
    "status": "simulated",
    "transactionBroadcast": false
  }
}
```

## Recommended flow

1. Render the agent card from a local manifest or reviewed prompt output.
2. Build a payment request with frozen money fields.
3. Show a human review step before any wallet path.
4. Record local approval or rejection in the event log.
5. Only in a separate reviewed PR, map the frozen request into a wallet submission path with chain gating.
6. After testnet confirmation exists, render a receipt card using ArcScan and verifier checks.

## Add-vs-skip tradeoff

Add this component layer when the repo needs reusable UI/data contracts across paid API, creator payout, job escrow, and report-agent demos. Skip live settlement until production Gateway/x402 credentials, wallet chain gating, and user approval are in scope.
