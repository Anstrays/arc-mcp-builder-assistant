# Payment Status Tutorial

This tutorial turns the local payment-intent playground into a repeatable status-tracking exercise. It is still browser-local: no wallet connection, no backend call, no private key handling, and no transaction broadcast.

Use it after the [payment-intent quickstart](./payment-intent-quickstart.md) and before any future wallet PR.

## Goal

Show reviewers how a payment request should move through explicit states before real Arc Testnet signing exists:

1. Draft intent created from agent context.
2. Human reviews JSON and validation summary.
3. Human marks the request as approved or rejected.
4. A future wallet/testnet PR replaces the local-only submission marker with verified ArcScan or app-log status.
5. The build log records what was verified and what remains unknown.

## Safety boundary

The current repository does **not** submit an Arc transaction. Treat every status shown by the playground as local UI state unless a later PR adds a reviewed testnet integration.

Keep these rules intact:

- Never paste seed phrases, private keys, or production API keys into the playground or AI prompts.
- Never enable signing in the same PR that adds a new status UI without separate test coverage and review.
- Keep wallet controls disabled until chain ID, wallet address, amount, expiry, human approval, and docs freshness are all checked.
- Record transaction hashes only after a real testnet transaction exists; until then, use placeholders such as `not-broadcast`.

## Step 1 — Run the local playground

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080/examples/payment-intent-playground/
```

Confirm the page still says:

- No wallet connection.
- No backend calls.
- No private keys.
- Wallet action unavailable.

## Step 2 — Create a reviewable intent

Use demo-safe values only:

- Recipient: a placeholder `0x` address from test data, not a real payout target.
- Amount: a small USDC amount with at most 6 decimals.
- Memo: describe the agent task in plain language.
- Expiry: a future timestamp.

Click **Prepare intent** and inspect the JSON. The important fields for status review are:

- `status` — local approval state.
- `networkReadiness.chainId` — expected Arc Testnet chain ID.
- `networkReadiness.rpcUrl` — expected read-only RPC URL.
- `networkReadiness.assetAddress` — expected USDC asset constant.
- `networkReadiness.statusSource` — where the status assumptions came from.

## Step 3 — Review the validation summary

Before any future wallet work, the local readiness summary should answer four questions:

- Is the recipient shaped like an address?
- Is the amount positive and USDC-decimal safe?
- Is the expiry still in the future?
- Has a human explicitly approved the next action?

If any answer is no, keep the status as draft or rejected.

## Step 4 — Copy the signing preflight report

Click **Copy preflight report** and save the JSON into an issue, PR comment, or build note.

For contest or community review, summarize it like this:

```text
Payment status exercise:
- Intent: local-only
- Wallet action: blocked
- Transaction broadcast: false
- Chain expectation: Arc Testnet 5042002 / 0x4cef52
- Asset: USDC constant from repo docs
- Next required review: separate testnet-only wallet PR
```

## Step 5 — Future testnet status checklist

A later wallet/testnet PR should only replace local markers with real status after it can prove:

- The connected wallet is on Arc Testnet.
- The requested asset and decimals match the current Arc docs/MCP context.
- The user saw and approved the exact amount, recipient, memo, and expiry.
- The app stores a transaction hash or explicit failure reason.
- The UI links to ArcScan for submitted transactions.
- Failed, rejected, expired, pending, submitted, and confirmed states are visible.
- Tests prove no mainnet or production credential path is enabled by default.

## Suggested status vocabulary

Use a small vocabulary until the prototype has real settlement:

- `draft` — intent exists but is not approved.
- `ready_for_review` — fields are valid enough for human review.
- `approved_local` — human approved the local exercise only.
- `rejected_local` — human rejected the local exercise.
- `blocked_wallet_unavailable` — signing remains disabled by guardrails.
- `submitted_testnet` — future state for a reviewed Arc Testnet transaction.
- `confirmed_testnet` — future state after verified explorer/app-log confirmation.
- `failed_testnet` — future state with a captured failure reason.

## What to publish

When sharing progress, be precise:

- Good: "The playground now demonstrates local payment status review and preflight reporting. No transaction is broadcast."
- Bad: "The app pays agents on Arc."

Link the reviewer to:

- [Payment-intent playground](../examples/payment-intent-playground/)
- [Payment-intent quickstart](./payment-intent-quickstart.md)
- [Arc Testnet integration runbook](./arc-testnet-integration-runbook.md)
- [Arc wallet integration notes](./arc-wallet-integration-notes.md)
