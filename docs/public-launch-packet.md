# Public launch packet

Use this packet when the Arc MCP Builder Assistant is ready to share publicly. It turns the current public-ready Arc builder kit into safe copy, links, and a submission checklist without posting automatically or overstating what the project does.

## Launch verdict

The project is ready to share as a **public-ready Arc builder kit**: docs, prompts, local playgrounds, review packets, screenshots, CI validation, read-only Arc Testnet checks, and a separate disabled-by-default browser-wallet send lab.

Accurate one-line positioning:

```text
Public-ready Arc builder kit with local-only payment prototypes, read-only Arc Testnet checks, and a separate guarded human-operated Arc Testnet wallet-send lab.
```

## Do not post automatically

Do not post automatically from this repo or from an agent run. Treat every message below as a draft that a human reviews, edits, and posts manually.

Before any public post, confirm:

- No wallet claim beyond the separate disabled-by-default Arc Testnet send lab.
- No wallet request on page load or from local-only demos.
- No private keys, seed phrases, Entity Secrets, API keys, or production verifier credentials.
- No custody.
- No transaction broadcast on page load, from local-only demos, or from automated checks.
- No live settlement or real paid-agent unlock claim.
- Not an official Arc product, endorsement, or partnership.
- No mainnet claim.

## Safe public wording

Use this wording when space is short:

```text
Independent Arc agent-commerce builder kit: local-only playgrounds, read-only testnet checks, and a separate disabled-by-default Arc Testnet wallet-send lab. No wallet request on page load, no private keys, no custody, no mainnet, and no autonomous spending.
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

Главное: local-only demos не запрашивают wallet и не отправляют транзакции; отдельная guarded Arc Testnet lab разрешает только одну ручную testnet попытку. No private keys, no custody, no mainnet, no autonomous spending.

Следующий optional slice — только отдельным review: disposable-wallet smoke по runbook или live x402/Circle verifier handoff без расширения custody/mainnet scope.
```

## X draft under 280 chars

```text
Shipped an Arc builder kit with local-only agent-commerce demos, read-only testnet checks, and a separate disabled-by-default human-operated Arc Testnet wallet-send lab. No keys, custody, mainnet, or autonomous spending.
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
- guarded Arc Testnet browser-wallet send lab.

The important boundary: the project does not pretend to be a production payment app. No wallet request occurs on page load, and there are no private keys, custody, mainnet, autonomous spending, or live settlement claims. The separate guarded lab can request one manually confirmed Arc Testnet transaction only after every visible guard passes.

Useful links:
- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Readiness report: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#current-readiness-report.md
- Payment playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Repo: https://github.com/Anstrays/arc-mcp-builder-assistant

Ask: feedback on the guarded testnet wallet boundary, custody/mainnet gates, or the next live x402/Circle verifier handoff.
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
8. Open the guarded send lab without its query gate and confirm every wallet control is disabled.
9. Attach screenshots from `assets/screenshots/` or refresh screenshots manually if the UI changed.
10. Review the post text for forbidden claims: production payment app, custodian, mainnet live, official Arc product, autonomous spending, live x402 settlement.
11. Post manually only after human review.

## Links to include

- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repository: https://github.com/Anstrays/arc-mcp-builder-assistant
- Current readiness report: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#current-readiness-report.md
- Payment-intent playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Job escrow simulator: https://anstrays.github.io/arc-mcp-builder-assistant/examples/job-escrow-simulator/
- Guarded Arc Testnet send lab: https://anstrays.github.io/arc-mcp-builder-assistant/examples/arc-testnet-wallet-send-gate/
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
Arc builder kit with local-only prototypes and a separate disabled-by-default, human-operated Arc Testnet browser-wallet send lab.
```
