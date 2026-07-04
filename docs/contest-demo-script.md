# Contest Demo Script

Use this page to record a 60-90 second demo video or write a short community update about the Arc MCP Builder Assistant. The goal is to show public proof-of-work without implying that local demos broadcast transactions or that the guarded Arc Testnet lab is a production payment system.

## Positioning

One-line description:

> Arc MCP Builder Assistant is an independent local-first builder kit that turns Arc docs and MCP context into safe agent-commerce demos: payment intents, job escrow, reviewable JSON, and explicit human approval states.

What is real today:

- Styled docs viewer for the public GitHub Pages site.
- Source-grounded Arc docs map and prompt library.
- Local payment-intent playground with explicit states: `draft`, `ready_for_review`, `approved_local`, `blocked_wallet_unavailable`.
- Local job escrow simulator for post, accept, fund, submit, and approve-style states.
- Local x402 HTTP 402 challenge boundary for future paid API settlement work.
- Separate disabled-by-default Arc Testnet browser-wallet lab for one manually reviewed USDC transaction.

What is intentionally not real yet:

- No wallet request on page load or from local-only demos.
- No private-key handling.
- No backend custody.
- No mainnet, autonomous spending, or live settlement.
- No transaction broadcast from local-only demos or automated checks.
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

### 70-90 seconds — close with the safety boundary

Voiceover:

> The current artifact is a public builder kit. Local demos stay wallet-free, and a separate disabled-by-default Arc Testnet lab can request one manually reviewed transaction after explicit chain and payload checks. Custody, mainnet, autonomous spending, and live settlement remain blocked.

On screen:

- Open `docs/view.html#arc-testnet-integration-runbook.md`.
- End on the GitHub repo or landing page.

## Fast 45-second version

Use this when a contest form wants a compact demo:

1. Landing page: independent Arc MCP + agent-commerce builder kit.
2. Docs viewer: Arc context and payment-safety notes are readable and source-controlled.
3. Payment playground: `draft` -> `ready_for_review` -> `approved_local` -> `blocked_wallet_unavailable`.
4. Job escrow simulator: local escrow-style workflow with human payout approval.
5. Close: local demos request no wallet or broadcast; the separate guarded lab is Arc Testnet-only and human-operated.

## Recording checklist

Before recording:

- Run `python3 scripts/test_all.py`.
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

> Shipped an Arc MCP Builder Assistant update: local-only playgrounds, read-only status checks, and a separate disabled-by-default Arc Testnet browser-wallet lab for one manually reviewed transaction. No private keys, custody, mainnet, autonomous spending, or live settlement.

## Contest submission bullets

Use these bullets in forms or judging notes:

- **Problem:** Agent-commerce demos often skip the human-review boundary and jump too quickly to wallet actions.
- **Solution:** A local-first builder kit that turns Arc docs/MCP context into safe reviewable prototypes.
- **Current proof:** Docs viewer, source-grounded Arc docs map, local playgrounds, x402 local challenge boundary, read-only Arc status checks, and a separate guarded Arc Testnet wallet-send lab.
- **Safety:** No wallet request on page load, private keys, backend custody, mainnet, autonomous spending, or local-demo broadcast.
- **Next step:** Independently review a disposable-wallet testnet smoke or a live x402 verifier handoff without widening custody/mainnet scope.

## X / short social copy

Under 280 characters:

> Built an Arc agent-commerce kit with local-only demos, read-only checks, and a separate guarded Arc Testnet wallet-send lab. No keys, custody, mainnet, autonomous spending, or live settlement.

## Honest Q&A

**Is this an official Arc project?**

No. It is an independent builder resource.

**Does it send a production payment?**

No. The payment playground is browser-local and blocks wallet submission. The separate guarded lab can request one manually reviewed Arc Testnet transaction, which is not production settlement.

**Why is that useful?**

It makes the human approval boundary visible before adding real settlement. Reviewers can inspect the states, JSON, docs, and safety claims without risking funds.

**What should be reviewed next?**

Use the guarded wallet-send runbook for a separately approved disposable-wallet smoke, or extend the live x402 verifier boundary without adding custody or mainnet.
