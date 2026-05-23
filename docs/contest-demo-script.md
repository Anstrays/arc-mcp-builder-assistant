# Contest Demo Script

Use this page to record a 60-90 second demo video or write a short community update about the Arc MCP Builder Assistant. The goal is to show public proof-of-work without implying the project already broadcasts real transactions.

## Positioning

One-line description:

> Arc MCP Builder Assistant is an independent local-first builder kit that turns Arc docs and MCP context into safe agent-commerce demos: payment intents, job escrow, reviewable JSON, and explicit human approval states.

What is real today:

- Styled docs viewer for the public GitHub Pages site.
- Source-grounded Arc docs map and prompt library.
- Local payment-intent playground with explicit states: `draft`, `ready_for_review`, `approved_local`, `blocked_wallet_unavailable`.
- Local job escrow simulator for post, accept, fund, submit, and approve-style states.
- Local x402 HTTP 402 challenge boundary for future paid API settlement work.

What is intentionally not real yet:

- No wallet connection.
- No private-key handling.
- No backend custody.
- No transaction broadcast.
- No claim of official Arc endorsement.

## 90-second video script

### 0-10 seconds — open with the problem

Voiceover:

> AI agents can draft useful payment or escrow actions, but builders need a safe review boundary before anything touches a wallet. This project starts with that boundary.

On screen:

- Open the landing page.
- Point to the independent builder-resource framing.
- Click **Open playground** or the payment-intent docs link.

### 10-25 seconds — show source-grounded docs

Voiceover:

> The repo keeps Arc context as readable docs and prompts. The docs viewer lets reviewers inspect setup notes, the Arc docs map, payment-intent notes, and safety constraints without digging through raw Markdown.

On screen:

- Open `docs/view.html#arc-docs-map.md`.
- Open `docs/view.html#payment-status-tutorial.md`.
- Mention that the docs are plain Markdown in the repo and easy to review.

### 25-55 seconds — show the payment-intent playground

Voiceover:

> In the playground, an agent can prepare a USDC payment intent, but the user sees JSON first. Preparing the intent moves it to `ready_for_review`. Manual approval moves it to `approved_local`. Trying to submit stays blocked as `blocked_wallet_unavailable`, because wallet integration is intentionally out of scope until a separate verified testnet PR.

On screen:

- Open `examples/payment-intent-playground/`.
- Click **Prepare intent**.
- Click **Approve manually**.
- Click **Mark submitted**.
- Show the status pill and status-state list.
- Show the signing preflight report.

### 55-70 seconds — show the job escrow simulator

Voiceover:

> The same review-first idea applies to job escrow: post a job, accept it, simulate funding, submit work, then require human approval before payout. It is useful for explaining agent-commerce flows before connecting real settlement.

On screen:

- Open `examples/job-escrow-simulator/`.
- Show the stage list and JSON panel.

### 70-90 seconds — close with next step

Voiceover:

> The current artifact is a public, local-first builder kit. The next step is a guarded Arc Testnet integration: read-only status first, explicit chain checks, and only then wallet signing with human confirmation.

On screen:

- Open `docs/view.html#arc-testnet-integration-runbook.md`.
- End on the GitHub repo or landing page.

## Fast 45-second version

Use this when a contest form wants a compact demo:

1. Landing page: independent Arc MCP + agent-commerce builder kit.
2. Docs viewer: Arc context and payment-safety notes are readable and source-controlled.
3. Payment playground: `draft` -> `ready_for_review` -> `approved_local` -> `blocked_wallet_unavailable`.
4. Job escrow simulator: local escrow-style workflow with human payout approval.
5. Close: no wallet, no private keys, no broadcast today; next slice is guarded Arc Testnet status and signing.

## Recording checklist

Before recording:

- Run `python3 scripts/validate_repo.py`.
- Run `python3 scripts/test_payment_intent_playground.py`.
- Run `python3 scripts/test_x402_boundary.py`.
- Serve locally with `python3 -m http.server 8090`.
- Use browser tabs for:
  - `/`
  - `/docs/view.html#arc-docs-map.md`
  - `/docs/view.html#payment-status-tutorial.md`
  - `/examples/payment-intent-playground/`
  - `/examples/job-escrow-simulator/`

Do not show:

- Wallet seed phrases.
- API keys.
- Private dashboards.
- Real customer or counterparty data.
- Any claim that the demo has already settled onchain.

## Community post draft

Short builder update:

> Shipped a local-first Arc MCP Builder Assistant update: styled docs viewer, Arc docs map, payment-intent playground, job escrow simulator, and x402 boundary. The payment flow now has explicit review-safe states: `draft`, `ready_for_review`, `approved_local`, `blocked_wallet_unavailable`. No wallet, no keys, no broadcast yet — the next step is guarded Arc Testnet status/signing.

## Contest submission bullets

Use these bullets in forms or judging notes:

- **Problem:** Agent-commerce demos often skip the human-review boundary and jump too quickly to wallet actions.
- **Solution:** A local-first builder kit that turns Arc docs/MCP context into safe reviewable prototypes.
- **Current proof:** Docs viewer, source-grounded Arc docs map, payment-intent playground, job escrow simulator, and x402 local challenge boundary.
- **Safety:** No wallet connection, no private keys, no backend custody, no transaction broadcast.
- **Next step:** Read-only Arc Testnet status, chain checks, and guarded wallet signing in a separate PR.

## X / short social copy

Under 280 characters:

> Built a local-first Arc MCP Builder Assistant for safer agent-commerce demos: docs viewer, Arc docs map, payment-intent playground, job escrow simulator, and x402 boundary. No wallet/keys/broadcast yet — just reviewable JSON + human approval states before testnet wiring.

## Honest Q&A

**Is this an official Arc project?**

No. It is an independent builder resource.

**Does it send a real payment?**

No. The current playground is browser-local and blocks wallet submission.

**Why is that useful?**

It makes the human approval boundary visible before adding real settlement. Reviewers can inspect the states, JSON, docs, and safety claims without risking funds.

**What should be built next?**

A guarded testnet slice: read-only Arc status, chain ID checks, wallet availability checks, preflight report, and only then a manually confirmed testnet transaction.
