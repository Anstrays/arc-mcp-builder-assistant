# Arc MCP Builder Assistant

[![Validate static site](https://github.com/Anstrays/arc-mcp-builder-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/Anstrays/arc-mcp-builder-assistant/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Status: public-ready kit](https://img.shields.io/badge/status-public--ready%20kit-2dba4e.svg)](#status)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-2dba4e.svg)](https://anstrays.github.io/arc-mcp-builder-assistant/)

> Independent local-first builder kit for Arc MCP, stablecoin payment intents, agent-wallet review flows, and x402-style paid-agent boundaries.

Arc MCP Builder Assistant helps developers turn Arc docs and MCP context into practical, reviewable agent-commerce prototypes. It ships a static docs site, source-grounded prompts, local playgrounds, regression tests, and a dependency-free x402-style challenge server that models `402 -> proof -> protected response` without wallets, custody, signing, settlement, or transaction broadcast.

Use this repo when you want to prototype Arc-focused payment infrastructure before a live wallet or production verifier exists. The safe default is always: Arc Testnet context, reviewable JSON first, explicit human approval, no private keys, no mainnet, and no autonomous spending.

## Table of contents

- [Why this matters](#why-this-matters)
- [Builder quickstart](#builder-quickstart)
- [Arc-focused use cases](#arc-focused-use-cases)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Current kit](#current-kit)
- [Screenshots](#screenshots)
- [Completion status](#completion-status)
- [Local development](#local-development)
- [Repository structure](#repository-structure)
- [Safety and honesty](#safety-and-honesty)
- [Contributing](#contributing)
- [Status](#status)

## Why this matters

Arc's public docs and positioning point toward stablecoin-native finance, agentic economy applications, autonomous agents, onchain identity, and developer-friendly payment infrastructure.

Many builders want to explore that direction, but the first step is often messy:

- finding the right docs;
- translating docs into implementation tasks;
- creating safe AI-coding prompts;
- scoping a realistic first demo;
- documenting what works and what fails.

This kit turns those steps into reusable guides, prompts, and examples.

## Builder quickstart

The repo is static-site first and Python-only for tests. No npm install, package manager, database, wallet, or paid SaaS dependency is required.

```bash
# 1. Run the full local regression suite.
python3 scripts/test_all.py

# 2. Preview the GitHub Pages site locally.
python3 -m http.server 8080
# open http://localhost:8080/

# 3. Run the local x402-style paid-agent boundary.
python3 examples/x402-local-challenge-server/server.py --port 8087
# in another terminal: curl -i http://127.0.0.1:8087/protected
```

Useful one-shot checks:

```bash
python3 examples/x402-local-challenge-server/server.py --print-challenge
python3 examples/x402-local-challenge-server/server.py --print-manifest
X402_DEMO_AMOUNT=0.05 python3 examples/x402-local-challenge-server/server.py --print-challenge
python3 scripts/validate_operator_evidence.py
```

On Windows, use `python` instead of `python3` if that is how Python is installed.

## Arc-focused use cases

- **Paid API agent:** model an Arc Testnet USDC x402-style `402 -> proof -> protected response` boundary before production Gateway verification exists.
- **Stablecoin payment request:** prepare reviewable payment-intent JSON with amount, recipient, memo, expiry, status, and human approval state.
- **Job escrow workflow:** simulate ERC-8183-style job posting, agent acceptance, simulated funding, work review, disputes, expiry, and payout approval.
- **Agent identity preview:** inspect ERC-8004-style agent metadata and controller/reputation notes before registration.
- **MCP-assisted coding:** connect AI tools to Arc docs/MCP, then force retrieved facts, implementation suggestions, unknowns, and safety checks into the plan.

## Configuration

Copy [`.env.example`](./.env.example) to `.env` only for local experiments. `.env` is ignored by git; keep real API keys, verifier tokens, private proofs, and deployment secrets in a private shell or secret manager.

| Variable | Used by | Default | Notes |
| --- | --- | --- | --- |
| `X402_DEMO_NETWORK` | Local x402 server | `arc-testnet` | Must stay `arc-testnet`; non-Arc networks are rejected. |
| `X402_DEMO_ASSET` | Local x402 server | `USDC` | Display/payment asset for the local challenge. |
| `X402_DEMO_AMOUNT` | Local x402 server | `0.01` | Positive decimal string, max 6 decimal places. |
| `X402_DEMO_PAY_TO` | Local x402 server | `0xA11CE00000000000000000000000000000000000` | Safe placeholder EVM address. |
| `X402_DEMO_MAINNET_ENABLED` | Local x402 server | `false` | Must remain false; true exits safely. |
| `ARC_PAID_AGENT_URL` | Live smoke script | empty | Deployed protected endpoint for challenge-only smoke checks. |
| `EXPECT_402_ONLY` | Live smoke script | `true` | Stops after validating the unpaid 402 challenge. |
| `ARC_LIVE_X_PAYMENT` | Live smoke script | empty | Optional externally created proof; never commit it. |
| `CIRCLE_GATEWAY_API_KEY` | Future verifier handoff | empty | Placeholder only. Store real values in a secret manager. |
| `X402_GATEWAY_VERIFIER_URL` | Future verifier handoff | empty | Placeholder only. |

## Troubleshooting

- **`python3` is not found:** use `python scripts/test_all.py` or install Python 3.12+. CI uses Python 3.12.
- **Port 8080 or 8087 is already in use:** choose another port, for example `python3 -m http.server 8090` or `python3 examples/x402-local-challenge-server/server.py --port 8097`.
- **`ARC_PAID_AGENT_URL` is missing:** either skip live smoke or set it to a deployed `/protected` endpoint. The local x402 demo does not need it.
- **Local x402 proof is rejected:** run `python3 examples/x402-local-challenge-server/server.py --print-challenge` and copy the exact `localDemoProof` value into the `X-Payment` header.
- **Config exits with `Invalid x402 demo configuration`:** keep `X402_DEMO_NETWORK=arc-testnet`, `X402_DEMO_MAINNET_ENABLED=false`, a positive 6-decimal-or-less amount, and a 42-character EVM `X402_DEMO_PAY_TO`.
- **A secret was pasted by mistake:** remove it from `.env` or shell history as needed, rotate the secret, and do not commit it. The repo scans common credential shapes during validation.

## Current kit

- [`docs/view.html`](./docs/view.html) — styled GitHub Pages Markdown reader so landing-page docs and community-health links open readable pages instead of raw text.
- [`docs/arc-mcp-setup.md`](./docs/arc-mcp-setup.md) — real Arc MCP setup steps for Claude Code, Claude Desktop, Cursor, VS Code, Windsurf, and HTTP MCP clients.
- [`docs/arc-docs-map.md`](./docs/arc-docs-map.md) — practical map of Arc Testnet config, contracts, agent primitives, tutorials, tools, and the recommended build path.
- [`docs/deploy-contracts-arc.md`](./docs/deploy-contracts-arc.md) — builder notes from Arc's deploy-contracts tutorial using Circle Contracts and Arc Testnet.
- [`docs/agent-identity-erc8004.md`](./docs/agent-identity-erc8004.md) — ERC-8004 agent identity notes and trust-boundary guidance.
- [`docs/agent-identity-profile-preview.md`](./docs/agent-identity-profile-preview.md) — local-only ERC-8004 profile preview before any agent registration transaction exists.
- [`docs/builder-workflows.md`](./docs/builder-workflows.md) — practical Arc + AI builder workflows.
- [`docs/payment-intent-demo.md`](./docs/payment-intent-demo.md) — first demo specification.
- [`docs/payment-intent-quickstart.md`](./docs/payment-intent-quickstart.md) — 5-minute reviewer path for showing the local payment-intent playground without wallet or transaction side effects.
- [`docs/payment-status-tutorial.md`](./docs/payment-status-tutorial.md) — step-by-step local payment status exercise for reviewers, plus the future Arc Testnet status checklist.
- [`docs/transaction-status-playground.md`](./docs/transaction-status-playground.md) — read-only Arc Testnet transaction status playground for checking hashes through public RPC without wallet or broadcast side effects.
- [`docs/contest-demo-script.md`](./docs/contest-demo-script.md) — 60-90 second demo script, recording checklist, community post copy, and contest submission bullets.
- [`docs/content-pack.md`](./docs/content-pack.md) — blog and contest content pack with Russian Telegram copy, X/Discord drafts, thumbnail prompts, video storyboard, and screenshot checklist.
- [`docs/public-launch-packet.md`](./docs/public-launch-packet.md) — human-review launch packet with safe Russian Telegram, X, Discord/Arc House copy, submission checklist, links, and forbidden claims.
- [`docs/prompt-library.md`](./docs/prompt-library.md) and [`prompts/`](./prompts/) — copy-paste prompts for AI coding tools, including the standalone Arc Testnet status prompt.
- [`docs/arc-builder-readiness-checklist.md`](./docs/arc-builder-readiness-checklist.md) — pre-submit checklist for docs grounding, payment safety, UX states, repo quality, and public proof-of-work.
- [`docs/current-readiness-report.md`](./docs/current-readiness-report.md) — concise current-scope verdict, local evidence commands, optional future extensions, and exact wording for public claims.
- [`docs/arc-testnet-integration-runbook.md`](./docs/arc-testnet-integration-runbook.md) — stepwise path from local-only demos to a reviewed Arc Testnet transfer, including no-secret and no-mainnet gates.
- [`docs/arc-wallet-integration-notes.md`](./docs/arc-wallet-integration-notes.md) — Circle Wallets vs browser-wallet decision notes for the next Phase 2 integration slice.
- [`docs/wallet-preflight-contract.md`](./docs/wallet-preflight-contract.md) — secret-free wallet preflight contract for the next Arc Testnet wallet preview/send PRs.
- [`docs/arc-testnet-send-readiness-gate.md`](./docs/arc-testnet-send-readiness-gate.md) — guard-only evidence contract for any future Arc Testnet send PR after the unsigned transaction draft and final local confirmation.
- [`docs/arc-testnet-operator-runbook.md`](./docs/arc-testnet-operator-runbook.md) — manual review checklist, stop conditions, and evidence record for any future guarded Arc Testnet live-send PR.
- [`docs/arc-testnet-operator-evidence.md`](./docs/arc-testnet-operator-evidence.md) — strict machine-readable operator evidence packet and dependency-free fail-closed validator.
- [`docs/agent-commerce-use-cases.md`](./docs/agent-commerce-use-cases.md) — practical use cases for API-call payments, creator payouts, job escrow, AI-service marketplace flows, and report agents.
- [`docs/agent-commerce-components.md`](./docs/agent-commerce-components.md) — reusable local-first agent cards, payment request cards, receipt cards, and event logs for future Arc commerce flows.
- [`docs/agent-commerce-flow-library.md`](./docs/agent-commerce-flow-library.md) — local-only paid API call, creator payout, and AI-agent commerce flow templates.
- [`docs/agent-commerce-review-packet.md`](./docs/agent-commerce-review-packet.md) — local-only final review packet schema before any live wallet, settlement, or registration handoff.
- [`docs/job-escrow-demo.md`](./docs/job-escrow-demo.md) — ERC-8183-style flow for posting jobs, funding escrow, reviewing agent output, and releasing stablecoin payouts.
- [`docs/x402-mcp-manifest.md`](./docs/x402-mcp-manifest.md) — machine-readable paid-agent manifest and JSON-RPC tool surface for the local x402 boundary.
- [`docs/x402-demo-transcript.md`](./docs/x402-demo-transcript.md) — copy-paste local `402 -> proof -> protected response` transcript with explicit no-wallet/no-settlement guardrails.
- [`docs/arc-production-deployment.md`](./docs/arc-production-deployment.md) — secret-free production deployment runbook, live-smoke checklist, and Circle Gateway/x402 verifier handoff.
- [`docs/mcp-query-examples.md`](./docs/mcp-query-examples.md) — prompts that force AI tools to separate retrieved Arc facts, implementation suggestions, and unknowns.
- [`docs/arc-house-submission.md`](./docs/arc-house-submission.md) — ready-to-edit builder update for Arc community or Arc House-style submissions.
- [`docs/build-log.md`](./docs/build-log.md) — public milestone note and community-update draft for sharing the current local-first builder kit.
- [`examples/payment-intent-playground/`](./examples/payment-intent-playground/) — local-only interactive playground for editing a payment request, inspecting live JSON, viewing Arc Testnet read-only status constants, previewing injected wallet provider/address/chain state without requesting permissions, freezing reviewed intent fields, recording final local confirmation, reviewing an unsigned ERC-20 transaction draft and local calldata consistency check, reviewing a blocked wallet handoff manifest, reviewing disabled wallet guard reasons, and copying a preflight report while transaction requests remain disabled.
- [`examples/transaction-status-playground/`](./examples/transaction-status-playground/) — read-only Arc Testnet transaction hash lookup with explicit `not_checked`, `pending`, `confirmed`, `failed`, and `unknown` states.
- [`examples/agent-commerce-components/`](./examples/agent-commerce-components/) — reusable local-only agent/payment/receipt/log cards that freeze money fields before any future wallet handoff.
- [`examples/agent-commerce-flows/`](./examples/agent-commerce-flows/) — local-only product-flow templates for paid API calls, creator payouts, and AI-agent commerce with frozen review artifacts.
- [`examples/agent-commerce-review-packet/`](./examples/agent-commerce-review-packet/) — local-only exporter that combines agent identity, commerce flow, escrow outcome, approval note, and disabled-surface controls into a review JSON packet.
- [`examples/arc-testnet-operator-evidence/`](./examples/arc-testnet-operator-evidence/) — safe example evidence packet for the Arc Testnet operator manual-review workflow.
- [`examples/agent-identity-profile-preview/`](./examples/agent-identity-profile-preview/) — local-only ERC-8004 profile preview for agent metadata, controller notes, reputation notes, and validation requirements.
- [`examples/job-escrow-simulator/`](./examples/job-escrow-simulator/) — local-only ERC-8183-style job escrow simulator for posting, accepting, simulated funding, submitting, requesting changes, resubmitting, rejection, dispute, expiry/cancellation, and payout approval.
- [`examples/x402-local-challenge-server/`](./examples/x402-local-challenge-server/) — dependency-free local HTTP 402 challenge server with MCP-style manifest, JSON-RPC stdio tool mode, JSON CLI helpers, and a swappable verifier boundary for future Circle/x402 settlement work.
- [`examples/payment-intent-demo/`](./examples/payment-intent-demo/) — tiny static mockup for the first payment-intent flow, including trust-boundary and review-state UI copy.

## Screenshots

These screenshots are committed so reviewers can quickly see the live-site UX without clicking through every page.

![Landing page screenshot](./assets/screenshots/landing.png)

![Styled security policy viewer screenshot](./assets/screenshots/security-viewer.png)

![Payment intent playground screenshot](./assets/screenshots/payment-intent-playground.png)

![Job escrow simulator screenshot](./assets/screenshots/job-escrow-simulator.png)

## Completion status

The public static kit is complete for its current safe scope: docs-grounded Arc/MCP workflows, local playgrounds, review packets, screenshots, and CI validation. It intentionally stops before wallet permissions, private keys, signing, custody, live settlement, or transaction broadcast.

For the shortest reviewer-facing checkpoint, see [`docs/current-readiness-report.md`](./docs/current-readiness-report.md).

### Shipped surfaces

- MCP setup checklist, Arc docs map, prompt library, deploy-contract notes, and agent identity notes.
- Builder readiness checklist, MCP query examples, agent-commerce use cases, job escrow demo spec, Arc House submission draft, public build log, and community copy packs.
- Styled GitHub Pages docs viewer so docs and community-health pages render like web pages instead of raw Markdown.
- Local payment-intent playground with reviewable JSON, status transitions, USDC unit preview, unsigned transaction draft preview, final local confirmation, send-readiness gate, and calldata consistency check.
- Local receipt verifier playground (`examples/receipt-verifier-playground/index.html`, `docs/receipt-verifier-playground.md`), read-only transaction-status playground (`examples/transaction-status-playground/index.html`, `docs/transaction-status-playground.md`), and local-only job escrow simulator with change-request, rejection, dispute, expiry, cancellation, and human-approved payout states.
- x402 local challenge boundary with machine-readable manifest, JSON-RPC/MCP-style stdio helpers, `.env.example`, local transcript, and production deployment runbook.
- Agent commerce starter-kit examples: components, flows, identity profile preview, and review packet exporter.
- Committed screenshots for the landing page, docs viewer, payment-intent playground, and job escrow simulator.

### Safe default

- No wallet connection.
- No private-key, seed-phrase, API-key, or token collection.
- No signing or transaction broadcast.
- No custody or real fund movement.
- Human approval stays required for any future send path.

### Optional future extensions

- Real wallet-submission tutorial after wallet integration exists and has a separate review.
- Optional Circle Wallets or Circle Contracts notes for teams that want a live integration path.
- Public community sharing of the build log as a distribution step, not a missing product feature.

## Suggested use

Use this repo with an AI coding assistant that supports MCP or can read local docs.

Example task:

```text
Use Arc MCP/docs context and this repo to design a minimal Arc payment-intent demo where an AI agent requests a USDC payment and the user approves it manually.
```

## Local development

The repo is intentionally dependency-free: only Python 3 (used by the
validator) and a web browser are required.

```bash
# Validate the repo the same way CI does.
python3 scripts/test_all.py

# Optional read-only Arc Testnet status check.
python3 scripts/check_arc_testnet_status.py

# Preview the static site locally (matches GitHub Pages behavior).
python3 -m http.server 8080
# then open http://localhost:8080/

# Run the local-only x402 challenge boundary demo.
python3 examples/x402-local-challenge-server/server.py --port 8087
# then request http://localhost:8087/protected to inspect the 402 challenge and MCP-style manifest

# Inspect the same paid-agent surface through JSON helpers / stdio.
python3 examples/x402-local-challenge-server/server.py --print-manifest
python3 examples/x402-local-challenge-server/server.py --print-challenge
printf '{"jsonrpc":"2.0","id":"tools","method":"tools/list"}\n' \
  | python3 examples/x402-local-challenge-server/server.py --mcp-stdio

# Challenge-only smoke for a deployed paid-agent endpoint.
ARC_PAID_AGENT_URL="http://127.0.0.1:8087/protected" \
  python3 scripts/live_arc_gateway_smoke.py --expect-402-only
```

For targeted debugging, run any individual `scripts/test_*.py` file directly.

The validator checks for required files, obvious credential patterns,
basic HTML safety / accessibility / SEO invariants on every public HTML page,
local links, reduced-motion CSS coverage, payment-demo safety copy, styled-viewer
coverage for public Markdown pages, the local-only x402 verifier boundary,
production deployment placeholders / live-smoke assets,
no raw Markdown links in user-facing HTML, and the integrity of `robots.txt`
and `sitemap.xml`. It runs on every push and pull request
via [`.github/workflows/validate.yml`](./.github/workflows/validate.yml).

## Repository structure

```text
.
├── index.html                       # Landing page (GitHub Pages root)
├── .env.example                     # Safe local config placeholders
├── 404.html                         # Branded GitHub Pages "Not found" page
├── robots.txt                       # Crawler directives + sitemap pointer
├── sitemap.xml                      # XML sitemap for the deployed site
├── docs/                            # Builder documentation
│   ├── view.html                    # Styled GitHub Pages Markdown docs reader
│   ├── viewer.js                    # Dependency-free local Markdown renderer
│   ├── arc-mcp-setup.md
│   ├── arc-docs-map.md
│   ├── deploy-contracts-arc.md
│   ├── builder-workflows.md
│   ├── payment-intent-demo.md
│   ├── payment-intent-quickstart.md
│   ├── payment-status-tutorial.md
│   ├── arc-discord-introduction.md
│   ├── receipt-verifier-playground.md
│   ├── transaction-status-playground.md
│   ├── x402-mcp-manifest.md
│   ├── x402-demo-transcript.md
│   ├── arc-builder-readiness-checklist.md
│   ├── arc-testnet-integration-runbook.md
│   ├── wallet-preflight-contract.md
│   ├── agent-commerce-use-cases.md
│   ├── job-escrow-demo.md
│   ├── mcp-query-examples.md
│   ├── arc-house-submission.md
│   └── build-log.md
├── prompts/                         # Copy-paste prompts for AI coding tools
├── examples/
│   ├── payment-intent-demo/         # Static UI mockup of the v0 demo flow
│   ├── payment-intent-playground/   # Local-only intent playground with Arc status constants
│   ├── receipt-verifier-playground/  # Local-only simulated receipt verifier
│   ├── transaction-status-playground/ # Read-only Arc Testnet transaction status lookup
│   ├── job-escrow-simulator/        # Local-only ERC-8183-style escrow flow simulator
│   └── x402-local-challenge-server/ # Local-only 402 challenge/verifier boundary demo
├── assets/screenshots/              # Committed preview proof for reviewers
├── scripts/
│   ├── check_arc_testnet_status.py  # Read-only Arc Testnet RPC status check
│   ├── test_all.py                  # Canonical local / CI regression suite
│   ├── test_x402_boundary.py        # Regression tests for the local x402 boundary
│   ├── test_receipt_verifier_playground.py # Regression tests for receipt verifier UI
│   ├── test_transaction_status_playground.py # Regression tests for transaction status UI
│   └── validate_repo.py             # CI / local validation script
├── .github/                         # Workflows, issue & PR templates
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md
```

## Safety and honesty

- Do not paste private keys, wallet seed phrases, access tokens, or API keys into AI tools.
- Do not imply official Arc endorsement unless confirmed.
- Treat all generated code as a draft until tested against current Arc docs.
- Keep claims honest: this is an early independent builder resource.

See [`SECURITY.md`](./SECURITY.md) for the full security policy and how
to report issues privately.

## Contributing

Contributions are welcome — corrections to MCP setup notes, verified Arc
docs links, prompt improvements, testnet integration notes, payment-intent
demo improvements, or agent-identity / ERC-8004 docs.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the contribution checklist
and [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md) for community
expectations.

## Status

Public-ready static builder kit for the current safe scope. Built in public as an independent Arc builder experiment, with wallet/signing/broadcast work kept behind separate future review gates.
