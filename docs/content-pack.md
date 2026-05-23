# Blog and contest content pack

This pack is for turning the Arc MCP Builder Assistant into posts, screenshots, thumbnails, and short demo videos without overclaiming. Use it for a Telegram build log, X post, Discord/Arc House update, contest form, or a 30-90 second clip.

## Ground rules

Keep these lines close to every public post:

- Independent builder resource, not an official Arc product.
- Local-first demo today: docs, prompts, playgrounds, simulators, and reviewable JSON.
- No wallet connection today.
- No private keys.
- No backend custody.
- No transaction broadcast.
- Testnet wiring should be a separate guarded PR with chain checks and manual confirmation.

Do not use official Arc logos, Circle logos, or brand marks in generated images unless the contest rules or brand guidelines explicitly allow it. A screenshot of this repo or local UI is safer.

## Core angle

Short thesis:

> AI agents should be able to prepare payment and escrow actions, but humans should still review the JSON and approve the wallet step. This repo makes that boundary visible before any testnet transaction exists.

Plain version:

> It is a builder kit for safer agent-commerce demos: Arc docs context, MCP prompts, a payment-intent playground, a job escrow simulator, and a local x402 boundary.

## Russian Telegram post

Use this for a Telegram channel or contest update:

```text
Собрал локальный Arc MCP Builder Assistant для agent-commerce демо.

Идея простая: агент может подготовить payment intent или escrow job, но человек сначала видит JSON, статусы и preflight. Wallet/signing пока заблокированы намеренно.

Что уже есть:
- styled docs viewer
- Arc docs map + MCP prompts
- payment-intent playground
- job escrow simulator
- x402 local boundary
- demo script для конкурса

Главный safety point: no wallet, no keys, no custody, no broadcast. Сейчас это честный public proof-of-work, а не фейковый "мы уже платим ончейн".

Следующий шаг: guarded Arc Testnet slice: read-only status, chain checks, wallet availability, ручное подтверждение, потом testnet tx.
```

Shorter Telegram version:

```text
Arc MCP Builder Assistant update:

Сделал local-first kit для agent-commerce демо: docs viewer, Arc docs map, payment-intent playground, job escrow simulator и x402 boundary.

Фокус не на хайпе, а на safety boundary: агент готовит intent, человек видит JSON и approve state, wallet/signing пока намеренно заблокированы.

No wallet. No keys. No custody. No broadcast.
Next: guarded Arc Testnet status/signing.
```

## X post

```text
Built a local-first Arc MCP kit for agent-commerce demos: docs viewer, Arc map, payment-intent playground, escrow simulator, x402 boundary. No wallet/keys/broadcast yet, just reviewable JSON + human approval before testnet wiring.
```

## Discord or Arc House update

```text
I shipped a new public-ready slice for Arc MCP Builder Assistant.

The project is still deliberately local-first: docs viewer, Arc docs map, MCP prompt library, payment-intent playground, job escrow simulator, and an x402 local challenge boundary.

The important part is the safety boundary. The payment playground now shows review-safe states before anything wallet-related:

- draft
- ready_for_review
- approved_local
- blocked_wallet_unavailable

That means the demo can show an agent preparing a payment intent without pretending it already broadcasts transactions. No wallet connection, no private keys, no custody, no real payment yet.

Next slice: guarded Arc Testnet integration. Read-only status first, chain checks, wallet availability checks, preflight report, then manually confirmed signing.
```

## Contest form summary

Use this when the form asks "what did you build?":

```text
Arc MCP Builder Assistant is an independent local-first builder kit for safer agent-commerce demos on Arc. It turns Arc docs and MCP context into practical public artifacts: a styled docs viewer, Arc docs map, MCP prompt library, payment-intent playground, job escrow simulator, x402 local boundary, and contest-ready demo script.

The demo makes the human approval boundary visible. An agent can prepare reviewable payment or escrow JSON, but wallet/signing is blocked until a separate guarded testnet integration. Current version has no wallet connection, no private-key handling, no backend custody, and no transaction broadcast.
```

## Screenshot checklist

Capture these five screenshots for posts or a contest gallery:

1. Landing page hero with the terminal-style prompt.
2. Docs viewer on `arc-docs-map.md`.
3. Payment-intent playground after **Prepare intent**.
4. Payment-intent playground after **Mark submitted**, showing `blocked_wallet_unavailable`.
5. Job escrow simulator with stage list and JSON visible.

Optional sixth image: `contest-demo-script.md` open in the styled docs viewer.

## Thumbnail prompt

Use this for a blog thumbnail, YouTube preview, or contest image generator. Keep the image abstract. Do not ask it to copy official logos.

```text
Dark futuristic browser UI screenshot style, an AI agent preparing a stablecoin payment intent, visible JSON card with amount, asset, recipient, status, a bright human approval checkpoint between the agent and wallet, Arc testnet builder vibe, neon green and deep navy palette, clean technical composition, sharp typography, no real brand logos, no private keys, no QR codes, no transaction hash, 16:9, high contrast, polished but not corporate.
```

Negative prompt:

```text
official logo, fake partnership badge, seed phrase, private key, QR code, real transaction hash, photorealistic person, clutter, meme coin aesthetic, "guaranteed profit", "mainnet live", "official Arc product"
```

## Blog header prompt

```text
Wide editorial header for a technical blog post about safe AI agent payments: local docs viewer, reviewable JSON, human approval gate, wallet locked until testnet checks pass, dark UI panels, subtle grid background, green accent lights, clean developer-tool aesthetic, no logos, no faces, no hype text, 16:9.
```

## Vertical short video storyboard

Format: 9:16, 30-45 seconds.

### Scene 1, 0-4s

Visual: landing page hero.

Overlay:

```text
AI agents can prepare payments.
They should not spend blindly.
```

Voiceover:

> I built a local-first Arc MCP kit for safer agent-commerce demos.

### Scene 2, 4-10s

Visual: docs viewer, Arc docs map.

Overlay:

```text
Docs first.
MCP context first.
```

Voiceover:

> The repo keeps Arc docs context and prompts readable, so reviewers can see what the agent is using.

### Scene 3, 10-20s

Visual: payment-intent playground. Click Prepare intent.

Overlay:

```text
Agent prepares JSON.
Human reviews it.
```

Voiceover:

> The agent prepares a payment intent, but the user sees the JSON before any wallet action.

### Scene 4, 20-28s

Visual: click Approve manually, then Mark submitted.

Overlay:

```text
approved_local
blocked_wallet_unavailable
```

Voiceover:

> Manual approval is local only. Submission stays blocked until a real testnet wallet flow exists.

### Scene 5, 28-36s

Visual: job escrow simulator.

Overlay:

```text
Same idea for escrow jobs.
Review before payout.
```

Voiceover:

> The same boundary works for job escrow: post, accept, fund, submit, review, then payout later.

### Scene 6, 36-45s

Visual: contest demo script or repo.

Overlay:

```text
No wallet. No keys. No broadcast.
Next: guarded Arc Testnet.
```

Voiceover:

> Current version is public proof-of-work. Next is read-only status, chain checks, and manually confirmed testnet signing.

## Carousel slides

Use this for Telegram, X thread images, or a LinkedIn-style carousel.

1. **AI payments need a review boundary**
   - Agents can draft actions.
   - Humans approve spending.
2. **What shipped**
   - Arc docs map
   - MCP prompts
   - payment-intent playground
   - job escrow simulator
   - x402 local boundary
3. **Payment states**
   - `draft`
   - `ready_for_review`
   - `approved_local`
   - `blocked_wallet_unavailable`
4. **What is not live yet**
   - no wallet
   - no keys
   - no custody
   - no transaction broadcast
5. **Next PR**
   - read-only Arc status
   - chain ID checks
   - wallet availability
   - preflight report
   - manual testnet signing

## Short blog outline

Title options:

- Building a safer AI payment demo on Arc before touching a wallet
- Agent-commerce demos need a human approval boundary
- From Arc MCP context to a local payment-intent playground

Outline:

1. The problem: agent-commerce demos often skip the review step.
2. The constraint: no wallet or transaction broadcast until the flow is inspectable.
3. What the repo ships today: docs, prompts, playground, escrow simulator, x402 boundary.
4. The payment-intent state machine.
5. Why local proof-of-work matters before testnet.
6. Next step: guarded Arc Testnet integration.

## One-minute voiceover

```text
This is Arc MCP Builder Assistant, an independent local-first kit for safer agent-commerce demos.

The idea is simple. An AI agent can prepare a payment intent or escrow job, but the human should see the JSON and approve the next step before any wallet action happens.

The repo already has a styled docs viewer, Arc docs map, MCP prompt library, payment-intent playground, job escrow simulator, and x402 local challenge boundary.

In the payment playground, the flow is explicit: draft, ready_for_review, approved_local, and blocked_wallet_unavailable. That last state matters. It prevents the demo from pretending that wallet signing or transaction broadcast exists before it has been reviewed.

So the current artifact is public proof-of-work, not a fake mainnet claim. No wallet, no keys, no custody, no broadcast.

Next step is a guarded Arc Testnet slice: read-only status, chain checks, wallet availability checks, preflight report, and manually confirmed signing.
```

## Submission checklist

Before posting or submitting:

- Run `python3 scripts/validate_repo.py`.
- Record the local site or GitHub Pages site, not private dashboards.
- Show the payment state names on screen.
- Say "local-first" or "local-only" for the current payment playground.
- Say "next step" when talking about testnet signing.
- Do not imply real funds moved.
- Do not paste secrets, RPC keys, wallet phrases, or private addresses.
- Link the repo and the exact docs page used in the demo.

## Reusable closing line

```text
The win is not that an agent can spend money automatically. The win is making the approval boundary visible before money can move.
```
