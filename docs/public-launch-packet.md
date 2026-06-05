# Public launch packet

Use this packet when the Arc MCP Builder Assistant is ready to share publicly. It turns the current public-ready Arc builder kit into safe copy, links, and a submission checklist without posting automatically or overstating what the project does.

## Launch verdict

The project is ready to share as a **public-ready Arc builder kit**: docs, prompts, local playgrounds, review packets, screenshots, CI validation, read-only Arc Testnet checks, and explicit wallet/send guardrails.

Accurate one-line positioning:

```text
Public-ready Arc builder kit with local-only payment and agent-commerce prototypes, read-only Arc Testnet checks, and review-first guardrails for future wallet or verifier integrations.
```

## Do not post automatically

Do not post automatically from this repo or from an agent run. Treat every message below as a draft that a human reviews, edits, and posts manually.

Before any public post, confirm:

- No wallet claim beyond disabled/read-only/local preview surfaces.
- No wallet connection in the current demos.
- No private keys, seed phrases, Entity Secrets, API keys, or production verifier credentials.
- No custody.
- No transaction broadcast.
- No live settlement or real paid-agent unlock claim.
- Not an official Arc product, endorsement, or partnership.
- No mainnet claim.

## Safe public wording

Use this wording when space is short:

```text
Independent local-only Arc agent-commerce builder kit: docs viewer, Arc/MCP prompts, payment-intent playground, job escrow simulator, x402 challenge boundary, read-only testnet checks, and human-approval guardrails. No wallet, no private keys, no custody, no transaction broadcast.
```

## Russian Telegram draft

```text
Запаковал Arc MCP Builder Assistant в public-ready build.

Что это: local-only kit для agent-commerce демо на Arc. Агент готовит payment intent / escrow context / x402 boundary, а человек видит JSON, safety states и review checklist до любого wallet action.

Что уже есть:
• GitHub Pages + styled docs viewer
• Arc docs map + MCP prompts
• payment-intent playground
• job escrow simulator
• x402 challenge boundary
• read-only Arc Testnet status checks
• readiness report и guardrails

Главное: no wallet, no private keys, no custody, no transaction broadcast. Это не "мы уже процессим платежи", а честный builder proof-of-work: безопасная прослойка между AI-agent intent и будущим ручным testnet approval.

Следующий optional slice — только отдельным PR: guarded wallet/testnet send или live x402/Circle verifier handoff.
```

## X draft under 280 chars

```text
Shipped a public-ready Arc builder kit for agent-commerce demos: docs viewer, MCP prompts, payment-intent playground, escrow simulator, x402 boundary, read-only testnet checks. Local-only for now: no wallet, keys, custody, or tx broadcast.
```

## Discord / Arc House update

```text
I shipped the current public-ready version of Arc MCP Builder Assistant.

It is an independent local-only builder kit for safer agent-commerce demos on Arc:
- styled docs viewer and Arc docs map;
- MCP prompt library;
- payment-intent playground with reviewable JSON;
- job escrow simulator;
- x402 challenge boundary;
- read-only Arc Testnet status checks;
- readiness report and wallet/send guardrails.

The important boundary: the project does not pretend to be a production payment app. No wallet connection, no private keys, no custody, no transaction broadcast, and no live settlement claim. The current product is a review-first builder surface that shows where a future testnet wallet or verifier integration would be added safely.

Useful links:
- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Readiness report: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#current-readiness-report.md
- Payment playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Repo: https://github.com/Anstrays/arc-mcp-builder-assistant

Ask: feedback on the safest next optional slice — guarded wallet/testnet send, live x402/Circle verifier handoff, or more builder-facing docs/examples first?
```

## Submission checklist

Run this checklist before sharing the project in Telegram, X, Discord, Arc House, a grant form, or a builder submission:

1. Pull latest `main`.
2. Run `python3 scripts/test_all.py` and confirm `all checks passed`.
3. Run `python3 scripts/check_arc_testnet_status.py` and confirm `ok: true`, Arc Testnet chain ID `5042002 / 0x4cef52`, and a latest block value.
4. Open the live site: `https://anstrays.github.io/arc-mcp-builder-assistant/`.
5. Open the readiness report: `https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#current-readiness-report.md`.
6. Open the payment-intent playground and confirm the wallet handoff remains blocked/disabled.
7. Open the job escrow simulator and confirm payout remains simulated/local-only.
8. Attach screenshots from `assets/screenshots/` or refresh screenshots manually if the UI changed.
9. Review the post text for forbidden claims: production payment app, custodian, mainnet live, official Arc product, autonomous spending, live x402 settlement.
10. Post manually only after human review.

## Links to include

- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repository: https://github.com/Anstrays/arc-mcp-builder-assistant
- Current readiness report: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#current-readiness-report.md
- Payment-intent playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Job escrow simulator: https://anstrays.github.io/arc-mcp-builder-assistant/examples/job-escrow-simulator/
- Build log: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#build-log.md

## Claims to avoid

Do not claim:

- production wallet app;
- custodian;
- mainnet-ready payment processor;
- live settlement service;
- official Arc product;
- official Circle product;
- autonomous spending agent;
- real x402 payment verification unless a separate verifier PR and live smoke prove it;
- transaction broadcast from the local playgrounds.

Prefer this phrase instead:

```text
Local-only Arc builder kit with review-first payment/agent-commerce prototypes and clear guardrails for future testnet wallet or verifier work.
```
