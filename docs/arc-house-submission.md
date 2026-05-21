# Arc House / Builder Submission Draft

Use this page as a ready-to-edit submission note for Arc community posts, Arc House updates, or builder program forms.

## Project

**Arc MCP Builder Assistant** — an independent builder kit that turns Arc's MCP/docs surface into practical AI-coding prompts, safety checklists, and local-first agentic-commerce demo flows.

## What I built

- GitHub Pages landing page for the project.
- Styled Markdown docs viewer so builder docs open as readable site pages.
- Arc MCP setup checklist for AI coding tools.
- Arc docs map covering testnet config, stablecoin/payment context, ERC-8004 agent identity, ERC-8183/job escrow notes, providers, and tutorials.
- Prompt library for docs-grounded Arc building.
- Static payment-intent demo mockup with explicit human approval boundaries.
- Local-only interactive payment-intent playground with editable fields, reviewable JSON, and approval/submission status transitions.
- Local-only ERC-8183-style job escrow simulator for posting jobs, accepting work, simulated escrow funding, deliverable submission, human review, and payout approval state.
- Local-only x402 HTTP 402 challenge server with a swappable verifier boundary for future Circle/x402 settlement work.
- Builder readiness checklist, MCP query examples, agent-commerce use cases, build log, and public submission draft.
- Lightweight repo validator and GitHub Actions workflow for safe static-site changes.

## Why it matters

Arc's narrative around stablecoins, agents, identity, predictable fees, and agentic commerce is powerful, but builders still need a safe path from docs to working demos. This project makes that path repeatable:

```txt
Arc docs/MCP → grounded AI prompts → reviewable payment/job object → human approval → testnet prototype → public build log
```

## Safety boundaries

- Independent project, not an official Arc product.
- No private-key handling.
- No custody.
- No autonomous mainnet spending.
- Local demos do not broadcast transactions.
- Human approval remains required for every future wallet action.
- Testnet integration comes only after current docs, wallet details, contract addresses, and provider assumptions are verified.

## Current links

- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repository: https://github.com/Anstrays/arc-mcp-builder-assistant
- Payment-intent playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Job escrow simulator: https://anstrays.github.io/arc-mcp-builder-assistant/examples/job-escrow-simulator/
- Build log: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#build-log.md
- Docs viewer: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html

## Current milestone

The current milestone is a **local-first builder kit**: docs, prompts, reviewable payment/job objects, simulators, and safety checks that another builder can open and understand quickly.

## Next build task

Wire one flow to verified Arc Testnet status while keeping the same human-approved boundary:

1. Re-check Arc Testnet RPC, chain ID, explorer, wallet/provider path, USDC assumptions, and relevant contract addresses through Arc MCP/docs.
2. Pick the smallest useful integration path: payment intent first, then job escrow/x402.
3. Add manual wallet approval.
4. Show tx hash, ArcScan link, and status timeline.
5. Keep examples testnet-first and secret-free.

## Ask from the community

- Feedback on the safest first payment-intent flow.
- Pointers to the most current Arc Testnet wallet/provider details.
- Review of ERC-8004 identity and ERC-8183/job escrow assumptions.
- Suggestions for whether the first real integration should be direct payment intent, job escrow, or paid API/x402 request.
