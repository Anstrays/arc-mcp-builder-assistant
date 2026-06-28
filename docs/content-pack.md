# Blog and contest content pack

This pack is for turning the Arc MCP Builder Assistant into posts, screenshots, thumbnails, and short demo videos without overclaiming. Use it for a Telegram build log, X post, Discord/Arc House update, contest form, or a 30-90 second clip.

## Ground rules

Keep these lines close to every public post:

- Independent builder resource, not an official Arc product.
- Local-only demos: docs, prompts, playgrounds, simulators, and reviewable JSON.
- No wallet request on page load or from local-only demos.
- No private keys.
- No backend custody.
- No mainnet, autonomous spending, or live settlement.
- The separate guarded Arc Testnet lab permits only one manually reviewed browser-wallet transaction.

Do not use official Arc logos, Circle logos, or brand marks in generated images unless the contest rules or brand guidelines explicitly allow it. A screenshot of this repo or local UI is safer.

## Core angle

Short thesis:

> AI agents should be able to prepare payment and escrow actions, but humans should still review the exact JSON and approve the wallet step. This repo keeps local demos wallet-free and isolates one guarded Arc Testnet send path.

Plain version:

> It is a builder kit for safer agent-commerce demos: Arc docs context, MCP prompts, a payment-intent playground, a job escrow simulator, and a local x402 boundary.

## Russian Telegram post

Use this for a Telegram channel or contest update:

```text
Собрал локальный Arc MCP Builder Assistant для agent-commerce демо.

Идея простая: агент может подготовить payment intent или escrow job, но человек сначала видит JSON, статусы и preflight. Local-only demos не запрашивают wallet.

Что уже есть:
- styled docs viewer
- Arc docs map + MCP prompts
- payment-intent playground
- job escrow simulator
- x402 local boundary
- отдельная guarded Arc Testnet wallet-send lab
- demo script для конкурса

Главный safety point: no private keys, no custody, no mainnet, no autonomous spending. Guarded lab разрешает только одну вручную подтверждённую Arc Testnet транзакцию.

Следующий шаг: отдельный review disposable-wallet smoke или live x402 verifier handoff без расширения custody/mainnet scope.
```

Shorter Telegram version:

```text
Arc MCP Builder Assistant update:

Сделал local-first kit для agent-commerce демо: docs viewer, Arc docs map, payment-intent playground, job escrow simulator и x402 boundary.

Фокус не на хайпе, а на safety boundary: агент готовит intent, человек видит JSON и approve state, а wallet action изолирован в отдельной guarded testnet lab.

No keys. No custody. No mainnet. No autonomous spending.
Guarded Arc Testnet send: one manual attempt only.
```

## X post

```text
Shipped arc-builder-kit on PyPI: local-only Arc agent-commerce demos, read-only testnet checks, CLI + MCP server, 3 starter templates. No keys, custody, mainnet, or autonomous spending. pip install arc-builder-kit
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

That means the local demo can show an agent preparing a payment intent without pretending it broadcasts transactions. The separate guarded lab can request one manually reviewed Arc Testnet transaction; there are no private keys, custody, mainnet, or live settlement claims.

Next review: a separately approved disposable-wallet smoke or a live x402 verifier handoff without widening custody/mainnet scope.
```

## Contest form summary

Use this when the form asks "what did you build?":

```text
Arc MCP Builder Assistant is an independent builder kit for safer agent-commerce demos on Arc. It turns Arc docs and MCP context into practical public artifacts: a styled docs viewer, Arc docs map, MCP prompt library, local payment and escrow playgrounds, an x402 local boundary, read-only status checks, and a separate guarded Arc Testnet wallet-send lab.

The local demos make the human approval boundary visible and never request a wallet or broadcast. The separate disabled-by-default lab permits one manually reviewed Arc Testnet transaction through an injected user-controlled wallet. There is no private-key handling, backend custody, mainnet, autonomous spending, or live settlement.
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
Local demos: no wallet request or broadcast.
Guarded Arc Testnet lab: one manual attempt.
```

Voiceover:

> Current version is public proof-of-work: local demos stay wallet-free, while the separate guarded Arc Testnet lab permits one manually confirmed attempt.

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
   - guarded Arc Testnet wallet-send lab
3. **Payment states**
   - `draft`
   - `ready_for_review`
   - `approved_local`
   - `blocked_wallet_unavailable`
4. **What remains blocked**
   - no keys
   - no custody
   - no mainnet
   - no autonomous spending
   - no live settlement
5. **Next review**
   - disposable-wallet testnet smoke
   - live x402 verifier handoff

## Short blog outline

Title options:

- Building a safer AI payment demo on Arc before touching a wallet
- Agent-commerce demos need a human approval boundary
- From Arc MCP context to a local payment-intent playground

Outline:

1. The problem: agent-commerce demos often skip the review step.
2. The constraint: local demos stay wallet-free and any testnet send stays isolated and inspectable.
3. What the repo ships today: docs, prompts, local playgrounds, escrow simulator, x402 boundary, read-only checks, and guarded send lab.
4. The payment-intent state machine.
5. Why local proof-of-work matters before testnet.
6. Next review: disposable-wallet smoke or live x402 verifier handoff.

## One-minute voiceover

```text
This is Arc MCP Builder Assistant, an independent local-first kit for safer agent-commerce demos.

The idea is simple. An AI agent can prepare a payment intent or escrow job, but the human should see the JSON and approve the next step before any wallet action happens.

The repo already has a styled docs viewer, Arc docs map, MCP prompt library, payment-intent playground, job escrow simulator, and x402 local challenge boundary.

In the payment playground, the flow is explicit: draft, ready_for_review, approved_local, and blocked_wallet_unavailable. That last state matters. It prevents the demo from pretending that wallet signing or transaction broadcast exists before it has been reviewed.

So the current artifact is public proof-of-work, not a fake mainnet claim. Local demos request no wallet or broadcast; the separate guarded lab permits one manual Arc Testnet attempt. No keys, custody, mainnet, autonomous spending, or live settlement.

Next review is a separately approved disposable-wallet smoke or a live x402 verifier handoff without widening custody/mainnet scope.
```

## Submission checklist

Before posting or submitting:

- Run `python3 scripts/test_all.py`.
- Record the local site or GitHub Pages site, not private dashboards.
- Show the payment state names on screen.
- Say "local-first" or "local-only" for the current payment playground.
- Distinguish the local-only playgrounds from the separate guarded Arc Testnet send lab.
- Do not imply real funds moved.
- Do not paste secrets, RPC keys, wallet phrases, or private addresses.
- Link the repo and the exact docs page used in the demo.

## Reusable closing line

```text
The win is not that an agent can spend money automatically. The win is making the approval boundary visible before money can move.
```
