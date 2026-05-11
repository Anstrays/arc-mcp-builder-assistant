# Arc MCP Builder Assistant

[![Validate static site](https://github.com/Anstrays/arc-mcp-builder-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/Anstrays/arc-mcp-builder-assistant/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Status: early MVP](https://img.shields.io/badge/status-early%20MVP-orange.svg)](#status)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-2dba4e.svg)](https://anstrays.github.io/arc-mcp-builder-assistant/)

> Independent early-stage builder resource for exploring Arc's MCP server, AI-assisted development workflows, and agentic commerce prototypes.

Arc MCP Builder Assistant is a lightweight documentation + prompt kit that helps builders use Arc's official MCP/docs surface with AI coding tools to prototype faster.

The first version focuses on three practical workflows:

1. **Connect AI tools to Arc docs through MCP** — so builders can ask targeted questions and retrieve relevant docs while coding.
2. **Generate better Arc app plans** — prompts for payment flows, agent registration, stablecoin FX, and agentic commerce.
3. **Prototype Arc agent payment concepts** — a minimal payment-intent demo spec that can evolve into a working testnet app.

This repository is intentionally scoped as a builder enablement kit, not an official Arc product.

## Table of contents

- [Why this matters](#why-this-matters)
- [Current MVP](#current-mvp)
- [Roadmap](#roadmap)
- [Suggested use](#suggested-use)
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

## Current MVP

- [`docs/arc-mcp-setup.md`](./docs/arc-mcp-setup.md) — real Arc MCP setup steps for Claude Code, Claude Desktop, Cursor, VS Code, Windsurf, and HTTP MCP clients.
- [`docs/arc-docs-map.md`](./docs/arc-docs-map.md) — practical map of Arc Testnet config, contracts, agent primitives, tutorials, tools, and the recommended build path.
- [`docs/deploy-contracts-arc.md`](./docs/deploy-contracts-arc.md) — builder notes from Arc's deploy-contracts tutorial using Circle Contracts and Arc Testnet.
- [`docs/builder-workflows.md`](./docs/builder-workflows.md) — practical Arc + AI builder workflows.
- [`docs/payment-intent-demo.md`](./docs/payment-intent-demo.md) — first demo specification.
- [`prompts/`](./prompts/) — copy-paste prompts for AI coding tools.
- [`examples/payment-intent-demo/`](./examples/payment-intent-demo/) — tiny static mockup for the first payment-intent flow.

## Roadmap

### Phase 1 — Documentation kit

- Publish MCP setup checklist.
- Publish Arc builder prompt library.
- Publish payment-intent demo spec.
- Publish Arc docs map with network config, core contracts, ERC-8004, ERC-8183, and event-monitoring roadmap.
- Share build log in Arc community.

### Phase 2 — Working prototype

- Build a small web UI for agent payment intents.
- Use Arc Testnet config from the docs map: RPC, chain ID, USDC gas, and ArcScan.
- Use Arc MCP docs to verify current testnet and wallet details.
- Add Circle Dev-Controlled SCA Wallet notes for Arc Testnet.
- Add optional Circle Contracts template deployment notes for receipts, credits, or payout demos.
- Track transaction/payment status.
- Add a short tutorial.

### Phase 3 — Agent commerce starter kit

- Add agent identity notes around Arc's ERC-8004 tutorial.
- Add ERC-8183 job escrow notes for agentic commerce flows.
- Add reusable components for agent cards, payment requests, receipts, and logs.
- Add example flows for creator payouts, API payments, and AI-agent commerce.

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
python3 scripts/validate_repo.py

# Preview the static site locally (matches GitHub Pages behavior).
python3 -m http.server 8080
# then open http://localhost:8080/
```

The validator checks for required files, obvious credential patterns,
basic HTML safety / accessibility / SEO invariants on every page in the
site (`index.html`, `404.html`, and
`examples/payment-intent-demo/index.html`), and the integrity of
`robots.txt` and `sitemap.xml`. It runs on every push and pull request
via [`.github/workflows/validate.yml`](./.github/workflows/validate.yml).

## Repository structure

```text
.
├── index.html                       # Landing page (GitHub Pages root)
├── 404.html                         # Branded GitHub Pages "Not found" page
├── robots.txt                       # Crawler directives + sitemap pointer
├── sitemap.xml                      # XML sitemap for the deployed site
├── docs/                            # Builder documentation
│   ├── arc-mcp-setup.md
│   ├── arc-docs-map.md
│   ├── deploy-contracts-arc.md
│   ├── builder-workflows.md
│   └── payment-intent-demo.md
├── prompts/                         # Copy-paste prompts for AI coding tools
├── examples/
│   └── payment-intent-demo/         # Static UI mockup of the v0 demo flow
├── scripts/
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

Early MVP scaffold. Built in public as an Arc builder experiment.
