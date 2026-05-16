# Arc Testnet integration runbook

This runbook turns the local payment-intent and job-escrow simulators into a safe checklist for a future Arc Testnet integration. It is intentionally conservative: agents can prepare data and explain risks, but humans keep wallet approval and signing control.

> Status: planning guide. The current demos remain local-only and do not connect to wallets, broadcast transactions, or talk to a backend.

## What this adds

Use this page when you are ready to move from a static/local proof-of-work toward a testnet-connected prototype.

The goal is not to make the agent autonomous. The goal is to add a narrow, reviewable path:

1. Read Arc context through MCP or the official docs.
2. Create a typed intent object.
3. Validate the chain, asset, amount, recipient, expiry, and memo.
4. Ask the human to approve in a wallet UI.
5. Observe the transaction or contract event.
6. Store a receipt object that can be shown in the app and shared in build logs.

## Source-grounding checklist

Before writing or changing code, ask the coding assistant to retrieve and cite current docs for these topics:

- Arc MCP server and docs retrieval.
- Arc Testnet chain configuration.
- Arc Testnet contract addresses.
- Gas and fees: USDC is the native gas token; Arc docs currently describe the native gas token as 18 decimals.
- App Kit, Unified Balance, Bridge, or Circle Wallet notes if the flow depends on them.
- Contract event monitoring if the prototype emits receipts, escrow events, or payout events.

Do not accept an implementation plan that cannot separate:

- retrieved Arc/Circle facts;
- repo-specific implementation choices;
- assumptions or unknowns.

## Safety boundaries

Keep these boundaries in the first testnet version:

- Testnet only.
- No private keys in the repo, screenshots, issues, prompts, or logs.
- No seed phrases or raw wallet export material in AI chats.
- No backend custody.
- No autonomous spending.
- No hidden recipient changes after a human reviews the intent.
- No mainnet fallback.
- No claims of official Arc endorsement.

The agent may draft JSON, explain the next action, and flag risk. The human submits or rejects the wallet action.

## Minimal payment-intent object

Start with a small JSON object that the user can inspect before any wallet action:

```json
{
  "kind": "arc.payment_intent.v1",
  "network": "arc-testnet",
  "chainId": 5042002,
  "asset": {
    "symbol": "USDC",
    "decimals": 18,
    "kind": "native-gas-token"
  },
  "amount": "5.00",
  "recipient": "0x0000000000000000000000000000000000000000",
  "memo": "Research report delivery",
  "expiresAt": "2026-01-01T00:00:00Z",
  "status": "draft",
  "humanApprovalRequired": true
}
```

Validation rules:

- `kind` must match the supported object version.
- `network` must be `arc-testnet`.
- `chainId` must be `5042002`.
- `asset.symbol` must be `USDC` for the first prototype.
- `asset.kind` and `asset.decimals` must be sourced from the current Arc/Circle docs before implementation. For Arc's native gas token, Arc docs currently describe USDC as 18 decimals; do not assume ERC-20 6-decimal USDC unless a specific contract address and docs citation are used.
- `amount` must be a decimal string, not a floating-point number.
- `recipient` must be shown to the user before signing.
- `memo` must be visible in the review UI.
- `expiresAt` must be checked before submission.
- `humanApprovalRequired` must remain `true`.

## Status model

Use explicit states instead of a vague pending/success flag:

| State | Meaning | User action |
| --- | --- | --- |
| `draft` | Agent or app prepared the intent. | Review fields. |
| `ready_for_review` | Local validation passed. | Confirm or reject. |
| `rejected` | Human rejected or edited the intent. | No transaction. |
| `wallet_opened` | Wallet prompt was requested. | Inspect wallet details. |
| `submitted` | Transaction was submitted to testnet. | Wait for result. |
| `observed` | App saw a transaction or event. | Compare with expected fields. |
| `settled` | Receipt matches expected intent. | Save/share receipt. |
| `failed` | Wallet, RPC, or validation failed. | Show reason and retry path. |

## Receipt object

After a submitted action, save a separate receipt. Do not mutate the original intent silently.

```json
{
  "kind": "arc.payment_receipt.v1",
  "intentId": "local-demo-intent-001",
  "network": "arc-testnet",
  "chainId": 5042002,
  "status": "observed",
  "transactionHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "observedAt": "2026-01-01T00:01:00Z",
  "explorerUrl": "https://testnet.arcscan.app/tx/0x0000000000000000000000000000000000000000000000000000000000000000",
  "checks": {
    "chainMatches": true,
    "recipientMatches": true,
    "amountMatches": true,
    "assetMatches": true
  }
}
```

## Wallet integration path

A careful implementation sequence:

1. Keep the existing local playground as the baseline.
2. Add pure validation functions for intent and receipt objects.
3. Add tests or validator checks for invalid chain, recipient, amount, expiry, and status transitions.
4. Add a disabled wallet section that explains what will be submitted.
5. Add a testnet-only wallet adapter behind a clear feature flag.
6. Before submission, read the connected chain and require Arc Testnet.
7. After submission, store a receipt object and link to ArcScan.
8. Publish a build log that lists verified facts and unresolved questions.

## Failure states to design first

Do not wait until wallet integration to design failure UX:

- Wrong network selected.
- Wallet rejected by user.
- Intent expired before approval.
- Recipient changed between review and wallet prompt.
- Amount formatting mismatch between display and base units.
- RPC unavailable or rate-limited.
- Transaction submitted but receipt observation failed.
- Receipt observed but fields do not match the original intent.

## Copy for the UI

Recommended review copy:

```text
This is an Arc Testnet action. The agent prepared the request, but you control the wallet approval. Verify network, recipient, amount, and memo before signing. This app does not need your private key or seed phrase.
```

Recommended failure copy:

```text
Submission stopped. The app could not verify that the connected wallet is on Arc Testnet, or the reviewed intent no longer matches the wallet action. No retry will happen automatically.
```

## Useful MCP prompt

```text
Use Arc MCP/docs context and this repository to plan a testnet-only payment-intent integration. Return: cited Arc/Circle facts, repo files to change, data validation rules, failure states, and a step-by-step implementation plan. Do not suggest mainnet, custody, private-key handling, or autonomous spending.
```

## Done criteria

A testnet integration is ready to demo only when:

- The app rejects non-Arc-Testnet chain IDs.
- The user sees network, recipient, amount, asset, memo, and expiry before wallet action.
- The original intent and final receipt are separate objects.
- The receipt links to ArcScan or equivalent testnet status.
- Failure states are visible and do not auto-retry spending.
- The README and Arc House submission draft describe exactly what is verified and what is still simulated.
