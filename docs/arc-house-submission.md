# Arc House / Builder Submission Draft

Use this page as a ready-to-edit submission note for Arc community posts, Arc House updates, or builder program forms.

## Project

**Arc MCP Builder Assistant** — an independent builder kit that turns Arc's MCP/docs surface into practical AI-coding prompts, safety checklists, and agentic-commerce demo flows.

## What I built

- GitHub Pages landing page for the project.
- Arc MCP setup checklist for AI coding tools.
- Arc docs map covering testnet config, stablecoin/payment context, ERC-8004 agent identity, ERC-8183/job escrow notes, providers, and tutorials.
- Prompt library for docs-grounded Arc building.
- Static payment-intent demo mockup with explicit human approval boundaries.
- Local-only interactive payment-intent playground with editable fields, reviewable JSON, and approval/submission status transitions.
- Builder readiness checklist, MCP query examples, agent-commerce use cases, and job escrow demo spec.
- Lightweight repo validator and GitHub Actions workflow for safe static-site changes.

## Why it matters

Arc's narrative around stablecoins, agents, identity, and predictable payment infrastructure is powerful, but builders still need a safe path from docs to working demos. This project makes that path repeatable:

```txt
Arc docs/MCP → grounded AI prompts → payment intent → human approval → testnet prototype → public build log
```

## Safety boundaries

- Independent project, not an official Arc product.
- No private-key handling.
- No autonomous mainnet spending.
- Human approval remains required for every payment action.
- Testnet integration comes only after current docs and wallet details are verified.

## Current links

- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repository: https://github.com/Anstrays/arc-mcp-builder-assistant
- Demo mockup: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-demo/
- Interactive playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/

## Next build task

Wire the local payment-intent playground to verified Arc Testnet wallet/status details after the chain, provider, and transaction assumptions are re-checked through Arc MCP/docs.

## Ask from the community

- Feedback on the safest first payment-intent flow.
- Pointers to the most current Arc Testnet wallet/provider details.
- Review of ERC-8004 identity and ERC-8183/job escrow assumptions.
- Suggestions for one practical agent-commerce use case worth implementing first.
