---
name: arc-builder-kit
description: Use when building, testing, or deploying Arc Testnet agent-commerce prototypes with the arc-builder-kit CLI, MCP server, Circle wallet SDK, x402 verifier, or payment-intent tooling.
version: 1.0.0
author: Anstrays
license: MIT
metadata:
  hermes:
    tags: [arc, circle, usdc, agent-commerce, mcp, x402, payment, testnet]
    related_skills: [circle-use-circle-cli, circle-use-agent-wallet]
---

# Arc Builder Kit

## Overview

Use `arc-builder-kit` to build and review Arc Testnet agent-commerce prototypes without turning the agent into an autonomous spender. The kit combines an installable Python CLI, a stdio MCP server, reviewed Arc Testnet facts, local x402-style payment boundaries, Circle wallet guard helpers, starter templates, browser demos, and a dependency-free regression suite.

Keep every workflow Arc-focused and testnet-first. Prefer structured payment intents, read-only evidence, deterministic validation, and explicit human approval. Treat generated plans and receipt checks as review aids, not as proof of settlement or authorization to spend.

The package requires Python 3.10 or newer. Core tooling uses the Python standard library. Repository behavior tests also use Node.js built-ins and require no `npm install`.

## Quickstart

Install the published package in an isolated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install "arc-builder-kit>=0.4.1"
arc-builder --version
```

On Windows, activate with `.venv\Scripts\activate` and use `python` when `python3` is unavailable.

Inspect the local, zero-network surfaces first:

```bash
arc-builder facts --json
arc-builder templates
arc-builder wallet status --json
arc-builder doctor
```

When working from a repository clone, run the canonical suite before and after changes:

```bash
python3 scripts/check_completion.py
python3 scripts/test_all.py
python3 scripts/arc_builder_doctor.py --full
```

Use network checks only when the user explicitly requests them. `doctor` is local-only by default; `--include-arc-rpc`, `--include-public-site`, and `--include-circle-wallet` opt in to read-only external checks.

## CLI Reference

### `arc-builder doctor`

Run the health orchestrator to verify package or repository integrity, safety markers, Arc Testnet facts, workflow policy, and optional external surfaces.

```bash
arc-builder doctor
arc-builder doctor --full
arc-builder doctor --include-arc-rpc
arc-builder doctor --include-public-site
arc-builder doctor --include-circle-wallet
```

Use the default mode for normal agent work. It makes zero network calls. Use `--full` to run the canonical regression suite once. Treat optional Circle checks as operator-invoked diagnostics; do not use them to initiate wallet actions.

### `arc-builder x402 challenge` and `verify`

Fetch an HTTP 402 challenge for inspection:

```bash
arc-builder x402 challenge http://127.0.0.1:8087/protected
```

Verify a supplied Arc Testnet transaction hash against receipt evidence, then retry the protected resource when the verifier accepts it:

```bash
arc-builder x402 verify http://127.0.0.1:8087/protected 0xTRANSACTION_HASH
```

These commands never create a payment, accept a private key, sign, or broadcast. `verify` is read-only evidence checking. Preserve the distinction between a submitted transaction, a successful receipt, an expected USDC transfer log, and final business settlement.

Run the dependency-free local challenge server when a reproducible fixture is enough:

```bash
python3 examples/x402-local-challenge-server/server.py --port 8087
```

The local demo defaults to `127.0.0.1`, Arc Testnet, USDC, and mainnet disabled. Do not weaken those defaults.

### `arc-builder scaffold`

List and copy reviewed starter templates:

```bash
arc-builder templates
arc-builder scaffold payment-intent-starter ./my-arc-demo
arc-builder scaffold x402-verified-api ./my-paid-api
```

Available templates include payment-intent, x402 agent/API, job escrow, marketplace, treasury, and verified x402 starters. After scaffolding, inspect the generated files, keep Arc Testnet facts pinned, and run the template's local command. Scaffolding copies files; it does not deploy contracts, configure custody, or fund a wallet.

Other useful commands are:

- `arc-builder validate` to validate a source checkout or installed distribution.
- `arc-builder facts` to print reviewed Arc Testnet constants.
- `arc-builder manifest` to print the local x402 manifest.
- `arc-builder release-packet` to generate a local maintainer review packet.
- `arc-builder mcp` to start the stdio MCP server.

## MCP Server

Start the server with either installed entry point:

```bash
arc-builder-mcp-server
# or
arc-builder mcp
```

The transport is newline-delimited JSON-RPC over stdio. Configure Claude Desktop, Cursor, or another stdio MCP client to launch the command directly:

```json
{
  "mcpServers": {
    "arc-builder": {
      "command": "arc-builder-mcp-server",
      "args": []
    }
  }
}
```

For Claude Code, Hermes, or OpenClaw, use the runtime's stdio MCP registration mechanism with the same command. Keep stdout reserved for JSON-RPC; send operator diagnostics to stderr. Restart the client after configuration so it can discover tools.

The current server exposes 14 tools:

- `arc_builder_doctor`, `validate_repo`, and `get_arc_testnet_facts` for health and facts.
- `list_templates`, `scaffold_project`, `list_examples`, and `generate_release_packet` for builder workflows.
- `x402_manifest`, `x402_paid_request`, `x402_fetch_challenge`, and `x402_verify_receipt` for local challenges and read-only payment evidence.
- `wallet_status`, `wallet_balance`, and `wallet_prepare_send` for guard status, read-only USDC balance, and non-broadcast send-intent preparation.

Tool results contain human-readable `content`, machine-readable `structuredContent`, and duration metadata. Long-running read-only tools can emit progress notifications on stderr. Do not treat MCP tool discovery as permission to invoke network checks or wallet-related operations without user intent.

## Circle Wallet SDK

Use the wallet surface in three layers:

1. Inspect guard and environment readiness with `wallet_status` or `arc-builder wallet status --json`. This makes no network call and redacts secret values.
2. Read an Arc Testnet USDC balance with `wallet_balance` or `arc-builder wallet balance ADDRESS --json`. This performs `eth_chainId` proof followed by read-only `eth_call` against the configured USDC interface.
3. Prepare a review object with `wallet_prepare_send` or `arc-builder wallet send ADDRESS AMOUNT --json`. Despite the CLI name, this returns `pending_human_approval`; it does not execute, sign, or broadcast.

Use `arc-builder wallet env-check --json` to check only whether required Circle environment variables are present. Never print their values. Use `wallet sdk-plan` or `wallet sdk-snippet` only to create a human-reviewed integration plan or manual snippet.

For any actual testnet transfer outside the guard-only CLI:

- Require a user-controlled Circle or injected wallet session.
- Re-check `ARC-TESTNET` and chain ID `5042002` / `0x4cef52` immediately before handoff.
- Freeze recipient, USDC amount, token address, calldata or transfer request, and expiry before approval.
- Display the exact request to the human.
- Require an explicit final confirmation.
- Never accept private keys or seed phrases.
- Never retry a rejected or failed send automatically.

The separate browser wallet-send lab and Payment Intent Demo implement narrow testnet-only examples. They are not authorization for an agent to spend autonomously.

## RPC Fallback

Use `arc_builder_kit.circle_wallet_sdk.rpc_call()` for bounded read-only JSON-RPC requests with sequential endpoint fallback. With no explicit endpoint list, the helper tries the primary Arc Testnet RPC and then reviewed operator-provided fallbacks from `ARC_RPC_FALLBACKS`. Pass `rpc_urls=[...]` when the caller must define the complete ordered chain.

```python
from arc_builder_kit.circle_wallet_sdk import check_arc_rpc_health, rpc_call

health = check_arc_rpc_health()
if not health["ok"]:
    raise RuntimeError(health["error"])

block = rpc_call("eth_blockNumber")
```

`check_arc_rpc_health()` calls `eth_chainId` and fails unless the endpoint reports Arc Testnet `0x4cef52`. A configured USDC balance read binds the chain proof and `eth_call` to the same selected endpoint. RPC helpers reject unsafe URL forms, cap response size, and return structured failures after all candidates fail.

Do not add guessed public RPC endpoints. Add a fallback only after operator review, and keep mainnet or unrelated-chain endpoints forbidden. RPC fallback is availability logic, not a chain-selection feature.

## Payment Intent Demo

Run the local Circle-backed demo from a source checkout:

```bash
python3 examples/payment-intent-demo/server.py
```

Open `http://127.0.0.1:8080`. The stdlib server binds to loopback, shows Circle wallet data when the Circle CLI session is available, creates local payment intents, and requests gas estimates.

Real transfer mode is disabled by default. Keep `REAL_TRANSFER=0` for normal demos and automated checks. When a maintainer separately approves a disposable Arc Testnet transfer, the guarded path additionally requires `REAL_TRANSFER=1`, `real=true`, the exact phrase `SEND ARC TESTNET USDC`, an explicit click, an amount no greater than `1.00 USDC`, and one attempt per intent. Never use that path in unattended tests.

The static payment-intent playground remains wallet-free. Do not blur it together with the isolated browser wallet-send lab or the Circle-backed demo server.

## Safety Boundaries

Enforce all of these boundaries on every task:

- Stay on Arc Testnet. Reject mainnet, unrelated chains, and silent network fallback.
- Do not request, read, store, log, or transmit private keys, seed phrases, Circle API keys, Entity Secrets, wallet credentials, or production tokens.
- Keep local demos and default doctor runs network-free.
- Keep wallet and RPC network checks explicit and read-only unless a human separately approves the documented testnet send flow.
- Do not sign messages or transactions on behalf of the user.
- Do not broadcast automatically, retry automatically, or spend in the background.
- Keep custody, autonomous spending, production settlement, and mainnet deployment out of scope.
- Label transaction hashes as submitted or pending until receipt evidence is available.
- Label receipt matching as evidence, not guaranteed settlement.
- Preserve amount caps, chain proof, frozen intent parity, one-shot locks, and typed confirmations.
- Re-run secret scanning and the full suite before publication.

When a requested change crosses one of these boundaries, stop and produce a separate security design and review checklist instead of implementing it inside the current static or local-first surface.

## Common Pitfalls

- `python3` is not found on Windows: use `python` or the Python launcher, and verify Python 3.10+.
- `arc-builder` is not found: activate the virtual environment or run `python -m arc_builder_kit`.
- MCP client shows no tools: confirm the command starts successfully, uses stdio rather than HTTP, emits no ordinary text on stdout, and restart the client.
- Doctor unexpectedly touches the network: remove all `--include-*` flags. Default doctor mode is local-only.
- Arc RPC reports the wrong chain: stop. Expected chain ID is `5042002` / `0x4cef52`; do not continue with another chain.
- USDC balance fails: validate the EVM address, HTTPS or loopback RPC URL, Arc chain proof, and reviewed USDC token address. ERC-20 USDC uses 6 decimals.
- x402 verification says not found or mismatch: confirm the transaction hash, expected recipient, USDC Transfer log, amount, receipt status, and Arc Testnet endpoint. Do not convert an unknown verdict into success.
- Circle checks fail: verify the Circle CLI is installed, the testnet agent session is valid, and required variables exist in the private shell. Do not paste secret values into logs or prompts.
- Payment demo cannot send: this is the safe default. A send needs every documented gate and a separate human decision.
- Scaffold destination exists: choose a new directory or use `--force` only after reviewing what will be replaced.
- Port 8080 or 8087 is occupied: stop the existing local process or select another documented local port.

## Verification Checklist

Before reporting work complete:

```bash
python3 scripts/check_completion.py
python3 scripts/test_all.py
python3 scripts/validate_repo.py
python3 scripts/arc_builder_doctor.py --full
ruff check arc_builder_kit/ scripts/
git diff --check
```

Then confirm:

- The completion check reports all required surfaces and safety assertions.
- Every canonical command passes without fail-open wrappers.
- Doctor reports `overallStatus: pass` in full local mode.
- Ruff reports zero errors.
- Arc Testnet facts remain `5042002` / `0x4cef52` and no mainnet values were introduced.
- The MCP tool count and documentation match `len(arc_builder_kit.mcp_server.TOOLS)`.
- No secret-like values appear in the diff.
- Local demos remain loopback-bound and disabled for real transfer by default.
- No real wallet connection, signing, broadcast, custody operation, or mainnet action occurred during verification.

Report the exact commands and results. If an optional network check was not requested or unavailable, say so explicitly rather than claiming live proof.
