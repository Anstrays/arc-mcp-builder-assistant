# Build Log

Use this page as the public build-note version of the project status. It is written for Arc community updates, Arc House-style submissions, and reviewers who want to understand what is usable now versus what remains local-only.

## Current milestone

**Milestone:** Arc Testnet agent-commerce builder kit — CLI, MCP server, Circle wallet SDK, RPC fallback, x402 verifier, and OpenClaw skill package.

This repo ships a GitHub Pages site, docs, prompts, local demos, an installable PyPI package (`arc-builder-kit`), and a live Circle wallet payment demo with real USDC balance and gas estimates on Arc Testnet.

## What shipped

- GitHub Pages landing page with styled navigation for builder docs.
- Styled Markdown viewer so public docs open as readable site pages instead of raw Markdown.
- Arc MCP setup checklist for Claude Code, Claude Desktop, Cursor, VS Code, Windsurf, and HTTP MCP clients.
- Arc docs map covering Testnet config, stablecoin context, ERC-8004 agent identity, ERC-8183 job escrow, providers, and tutorials.
- Prompt library that asks AI tools to cite Arc docs, separate known facts from suggestions, and flag unknowns.
- Local-only payment-intent playground with editable fields, reviewable JSON, USDC unit preview, and human approval status transitions.
- Local-only ERC-8183-style job escrow simulator for posting, accepting, funding, submitting, reviewing, and approving payout state.
- Local-only x402 challenge server that demonstrates an HTTP 402 payment boundary without wallet, RPC, verifier backend, transaction broadcast, or mainnet settlement.
- Lightweight validator and GitHub Actions workflow covering required files, safety copy, static-page invariants, public links, and the x402 verifier boundary.
- Safe-scope completion contract with a dependency-free completion check and canonical-suite coverage enforcement.
- Arc Testnet operator evidence packet, fail-closed validator, create-only ignored draft generator, and read-only readiness report.
- Separate disabled-by-default Arc Testnet browser-wallet send lab with frozen USDC payload parity, explicit confirmation, and a one-attempt lock.
- Phase 4 builder tooling: unified CLI (`scripts/arc_builder_cli.py`), stdio MCP server (`scripts/arc_builder_mcp_server.py`), and dependency-free starter templates under `templates/` for payment-intent, x402-agent, and job-escrow scaffolds.
- **PyPI package `arc-builder-kit` v0.4.1** — installable CLI + MCP server with `pip install arc-builder-kit`.
- **Circle Wallet SDK** — guard manifests, read-only USDC balance via `eth_call`, guarded send intents, Circle CLI env readiness checks, and safe Python/TypeScript SDK snippets. All operations: testnet-only, no private keys, no broadcast.
- **Payment Intent Demo with live Circle wallet** — real USDC balance, on-chain gas estimates, transaction history, and optional real transfers (capped at 1.00 USDC, estimate-only by default).
- **x402 RpcVerifier** — `arc-builder x402 verify` checks Arc Testnet transaction receipts against payment proof on-chain via RPC.
- **RPC fallback chain** — automatic primary → env `ARC_RPC_FALLBACKS` → user-specified endpoint failover with `rpc_call()` and `check_arc_rpc_health()`. No single-point-of-failure for Arc Testnet connectivity.
- **MCP Server v2** — 11 tools, structured errors, streaming-ready JSON-RPC for AI coding agents.
- **New templates** — marketplace, treasury, x402-verified starter scaffolds.
- **OpenClaw/Hermes skill package** — reusable skill (`arc-builder-kit`) for AI agents to discover and use the full CLI, MCP, SDK, and validator surface.

## Safety boundaries

- Independent builder resource, not an official Arc product or endorsement.
- No private-key handling in the repo.
- No seed phrases, wallet credentials, Circle API keys, Entity Secrets, or production tokens in examples.
- No autonomous mainnet spending.
- Local-only demos do not broadcast transactions; the isolated guarded send lab can request one manual Arc Testnet transaction.
- Human approval remains required before every wallet action.
- Current chain, contract, wallet, and x402 settlement assumptions must be re-verified through Arc docs/MCP and Circle docs before real testnet integration.

## How to verify locally

```bash
python3 scripts/check_completion.py
python3 scripts/test_all.py
python3 -m http.server 8080
```

Then open:

- `http://localhost:8080/`
- `http://localhost:8080/examples/payment-intent-playground/`
- `http://localhost:8080/examples/job-escrow-simulator/`
- `http://localhost:8080/examples/arc-testnet-wallet-send-gate/` (disabled state)
- `http://localhost:8080/docs/view.html#build-log.md`

To run the Circle wallet payment intent demo:

```bash
python3 examples/payment-intent-demo/server.py
# → http://localhost:8080 — real USDC balance, estimates, tx history
```

To check RPC fallback health:

```bash
python3 -c "from arc_builder_kit.circle_wallet_sdk import check_arc_rpc_health; print(check_arc_rpc_health())"
```

To run the x402 boundary demo:

```bash
python3 examples/x402-local-challenge-server/server.py --port 8087
```

Then request `http://localhost:8087/protected` and inspect the local 402 challenge response.

## Public links

- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repository: https://github.com/Anstrays/arc-mcp-builder-assistant
- Payment-intent playground: https://anstrays.github.io/arc-mcp-builder-assistant/examples/payment-intent-playground/
- Job escrow simulator: https://anstrays.github.io/arc-mcp-builder-assistant/examples/job-escrow-simulator/
- Docs viewer: https://anstrays.github.io/arc-mcp-builder-assistant/docs/view.html

## Community update draft

Built a local-first Arc MCP Builder Assistant: docs-grounded prompts, Arc MCP setup notes, payment-intent playground, job escrow simulator, and a local x402 challenge boundary.

The goal is not an autonomous spending bot. The useful primitive is review-first agent commerce: AI prepares structured payment/job context, humans approve wallet actions, and status stays observable.

Current build is intentionally safe:

- no private keys;
- no custody;
- no mainnet spending;
- no transaction broadcast in local demos;
- Arc/Circle assumptions are documented as things to re-check before testnet integration.

Links:

- Live site: https://anstrays.github.io/arc-mcp-builder-assistant/
- Repo: https://github.com/Anstrays/arc-mcp-builder-assistant

Ask: feedback on the safest first Arc Testnet flow — direct payment intent, job escrow, or paid API/x402 request?

## Completion and future work

The current builder-kit scope is complete: PyPI package, CLI, MCP server, Circle Wallet SDK, RPC fallback, x402 verifier, payment intent demo, and OpenClaw skill. All 12 original project phases are closed. Remaining work is optional extension, not a hidden blocker:

1. RPC fallback improvements (additional public endpoints beyond user-specified).
2. A custody/account-abstraction provider integration with secrets held outside the repo.
3. Mainnet evaluation only after official Arc mainnet configuration exists and passes a separate review.

Each extension must preserve explicit human approval, Arc-only positioning, testnet-first verification, and fail-closed safety gates.
