# Arc House / Builder Submission Draft

Use this page as a ready-to-edit submission note for Arc community posts, Arc House updates, or builder program forms.

## Project

**Arc MCP Builder Assistant** — an independent builder kit that turns Arc's MCP/docs surface into practical AI-coding prompts, safety checklists, and local-first agentic-commerce demo flows.

## What I built

- **Installable PyPI package** `arc-builder-kit` (`pip install arc-builder-kit`): CLI (`arc-builder`), MCP server (`arc-builder-mcp-server`), 3 starter templates, doctor, validate, release-packet commands. Trusted PyPI Publishing via OIDC.
- GitHub Pages landing page and styled docs viewer.
- Arc MCP setup checklist, docs map, and prompt library for AI coding tools.
- Local-only payment-intent playground with editable fields, reviewable JSON, frozen money fields, and approval/submission status transitions.
- Read-only receipt viewer for Arc Testnet transaction evidence with chain-first stopping, JSON-RPC envelope checks, and pinned USDC Transfer log decoding.
- Read-only payment-intent receipt matcher comparing local intent JSON with Arc Testnet receipt Transfer logs, emitting match/mismatch/revert/not-found/unknown verdicts with machine-readable evidence export (JSON + Markdown).
- Read-only transaction-status playground with expected-transfer evidence comparison, exact-hash binding, and settlement claims always false.
- Local-only ERC-8183-style job escrow simulator for posting jobs, accepting work, simulated escrow funding, deliverable submission, human review, and payout approval state.
- Local-only x402 HTTP 402 challenge server with strict JSON-RPC envelope checks, fail-closed verifier boundary, and loopback-only HTTP binding.
- Separate disabled-by-default Arc Testnet browser-wallet lab: exact query gate, injected-wallet handoff, frozen USDC payload parity, 1.00 USDC cap, typed confirmation, one attempt per page load.
- Agent commerce components, flow library, review packet exporter, agent identity profile preview (ERC-8004).
- Arc Agent Treasury Lab with exact micro-USDC accounting, local x402 receipt replay protection, reserve and spend-cap policy, deterministic verify/repair loops, and fail-closed manual-review outcomes.
- Arc Builder Doctor: one dependency-free command that orchestrates all local checks into a structured pass/warn/fail report, with Markdown output for CI summaries.
- Release packet generator: one command that builds a local maintainer-facing packet (doctor report, testnet facts, readiness checklist, examples index, release JSON).
- Arc Testnet facts contract with offline consistency proof for critical constants, policy, and demo surfaces.
- Agentic maintainer loop documentation for coding agents tied to deterministic checks and human approval gates.
- CI validation: least-privilege workflow permissions, pinned Actions, failure-path tests, and dependency-free Node behavior harnesses for actual JavaScript.
- Builder readiness checklist, MCP query examples, agent-commerce use cases, build log, and public submission draft.

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
- Human approval remains required for every wallet action.
- Testnet integration comes only after current docs, wallet details, contract addresses, and provider assumptions are verified.

## Current links

- **PyPI package:** https://pypi.org/project/arc-builder-kit/
- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repository: https://github.com/Anstrays/arc-mcp-builder-assistant
- Install: `pip install arc-builder-kit`
- Payment-intent playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Job escrow simulator: https://anstrays.github.io/arc-mcp-builder-assistant/examples/job-escrow-simulator/
- Build log: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html#build-log.md
- Docs viewer: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html

## Current milestone

The current milestone is a **guarded Arc builder kit**: docs, prompts, local-only payment/job objects, simulators, read-only checks, and a separate disabled-by-default Arc Testnet wallet-send lab that another builder can inspect quickly.

## Next build task

Wire one flow to a live Circle agent wallet on Arc Testnet, keeping the same human-approved boundary:

1. Circle agent wallet bootstrap (login, create wallet, fund with testnet USDC via CCTP bridge or faucet).
2. Live x402 challenge → real USDC payment through Circle wallet on Arc Testnet.
3. Agent identity registration (ERC-8004) on Arc Testnet — read-only in repo, live tx guarded.
4. Paid API call flow: agent → x402 challenge → Circle payment → API response → receipt.
5. Job escrow with real Arc Testnet contract — guarded, human approval, no autonomous release.
6. Treasury lab with real Circle payment receipts and on-chain verification.
7. All testnet-only, human-approved, fail-closed. No mainnet, no autonomous spend, no secrets in repo.

## Ask from the community

- Feedback on the safest first payment-intent flow.
- Pointers to the most current Arc Testnet wallet/provider details.
- Review of ERC-8004 identity and ERC-8183/job escrow assumptions.
- Suggestions for whether the first real integration should be direct payment intent, job escrow, or paid API/x402 request.
