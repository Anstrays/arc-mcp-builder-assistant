# Arc MCP Builder Assistant

> Independent early-stage builder resource for exploring Arc's MCP server, AI-assisted development workflows, and agentic commerce prototypes.

Arc MCP Builder Assistant is a lightweight documentation + prompt kit that helps builders use Arc's official MCP/docs surface with AI coding tools to prototype faster.

The first version focuses on three practical workflows:

1. **Connect AI tools to Arc docs through MCP** — so builders can ask targeted questions and retrieve relevant docs while coding.
2. **Generate better Arc app plans** — prompts for payment flows, agent registration, stablecoin FX, and agentic commerce.
3. **Prototype Arc agent payment concepts** — a minimal payment-intent demo spec that can evolve into a working testnet app.

This repository is intentionally scoped as a builder enablement kit, not an official Arc product.

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

- `docs/arc-mcp-setup.md` — MCP setup notes and integration checklist.
- `docs/builder-workflows.md` — practical Arc + AI builder workflows.
- `docs/payment-intent-demo.md` — first demo specification.
- `prompts/` — copy-paste prompts for AI coding tools.
- `examples/payment-intent-demo/` — tiny static mockup for the first payment-intent flow.

## Roadmap

### Phase 1 — Documentation kit

- Publish MCP setup checklist.
- Publish Arc builder prompt library.
- Publish payment-intent demo spec.
- Share build log in Arc community.

### Phase 2 — Working prototype

- Build a small web UI for agent payment intents.
- Add wallet/testnet integration once confirmed against current Arc docs.
- Track transaction/payment status.
- Add a short tutorial.

### Phase 3 — Agent commerce starter kit

- Add agent identity notes around Arc's ERC-8004 tutorial.
- Add reusable components for agent cards, payment requests, receipts, and logs.
- Add example flows for creator payouts, API payments, and AI-agent commerce.

## Suggested use

Use this repo with an AI coding assistant that supports MCP or can read local docs.

Example task:

```text
Use Arc MCP/docs context and this repo to design a minimal Arc payment-intent demo where an AI agent requests a USDC payment and the user approves it manually.
```

## Safety and honesty

- Do not paste private keys, wallet seed phrases, access tokens, or API keys into AI tools.
- Do not imply official Arc endorsement unless confirmed.
- Treat all generated code as a draft until tested against current Arc docs.
- Keep claims honest: this is an early independent builder resource.

## Status

Early MVP scaffold. Built in public as an Arc builder experiment.
