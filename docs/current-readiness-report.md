# Current readiness report

This report is the short checkpoint for deciding whether the Arc MCP Builder Assistant is finished for the current scope, and what remains outside that scope.

## Verdict

The repository is **complete for the current public-ready static builder-kit scope**.

That scope includes docs-grounded Arc/MCP workflows, local-only playgrounds, review packets, screenshots, CI validation, read-only Arc Testnet status checks, and a separate disabled-by-default Arc Testnet browser-wallet send lab. It intentionally stops before private-key handling, custody, mainnet, autonomous spending, live settlement, or real paid-agent verification.

## Latest local evidence

Run these commands from the repository root before publishing a new checkpoint:

```bash
python3 scripts/check_completion.py
python3 scripts/test_all.py
python3 scripts/check_arc_testnet_status.py
```

Expected safe result:

- `scripts/check_completion.py` confirms required surfaces, canonical-suite coverage, and the current safety boundary.
- `scripts/test_all.py` finishes with `all checks passed` for the full local regression suite.
- `scripts/check_arc_testnet_status.py` returns `ok: true`, confirms Arc Testnet chain ID `5042002 / 0x4cef52`, and reports the latest block through the read-only RPC.
- Neither command requests wallet permissions, collects secrets, signs, estimates gas, simulates a transaction, or broadcasts.

## Shipped working surfaces

- GitHub Pages landing page and styled docs viewer.
- Arc MCP setup, docs map, prompt library, builder workflows, and deployment/runbook docs.
- Local payment-intent playground with reviewable JSON, frozen intent fields, explicit local approval states, USDC unit preview, unsigned ERC-20 transaction draft, calldata consistency check, final local confirmation, and blocked wallet handoff manifest.
- Read-only transaction-status playground for Arc Testnet transaction hashes.
- Expected-transfer evidence comparison for pinned Arc Testnet USDC target,
  zero native value, decoded recipient, and decoded amount, with chain-first
  stopping, JSON-RPC envelope/exact-hash binding, and settlement claims always
  false.
- Guarded Arc Testnet wallet send lab with exact query enablement, injected-wallet handoff, frozen USDC payload parity, a `1.00` USDC cap, typed confirmation, and one attempt per page load.
- Local receipt verifier playground.
- Local x402 challenge boundary with machine-readable manifest, strict
  JSON-RPC envelope checks, and fail-closed direct-helper config.
- Fail-closed live-smoke URL/timeout validation and loopback-only local x402 HTTP binding.
- Agent-commerce components, flow library, review packet, agent identity profile preview, and job escrow simulator.
- Arc Agent Treasury Lab with exact micro-USDC accounting, local x402 receipt replay protection, reserve and spend-cap policy, deterministic verify/repair loops, and fail-closed manual-review outcomes.
- Static validation for required files, safe HTML, SEO/meta basics, local links, viewer coverage, and obvious credential patterns.
- Exact least-privilege workflow permission-map enforcement and an isolated,
  automatically cleaned repository-local temp directory for canonical tests.
- A measurable [safe-scope completion contract](./completion-contract.md) and dependency-free completion check.
- Dependency-free Node behavioral harnesses for the actual guarded-send and
  transaction-status JavaScript, plus malicious-Markdown behavior checks for
  the actual docs viewer, using fake provider/RPC/document boundaries only.
- x402 proof, schema, verifier-result, and error-detail boundaries fail closed
  before a local protected response is returned.
- Fail-closed operator evidence validation, create-only ignored draft generation, and read-only readiness reporting.

## Remaining work is optional extension work

These are not blockers for the current public kit. They are separate future PRs because each adds higher-risk integration surface:

1. **Custody or account-abstraction provider integration**
   - Requires a separate backend/provider security review and secret-management boundary.
   - Must not place keys, provider secrets, or autonomous signing policy in the static site.

2. **Live x402 / Circle verifier handoff**
   - Requires real verifier credentials and deployed endpoint configuration outside the committed repo.
   - Must keep `.env.example` placeholders only and avoid committing secrets.
   - Should begin with challenge-only smoke before any paid resource unlock claim.

3. **Public distribution**
   - Sharing the build log, content pack, or Arc House submission copy is a distribution step, not a missing product feature.

## Completion basis

The [safe-scope completion contract](./completion-contract.md) defines the
acceptance criteria behind this verdict. A future extension does not make the
current kit incomplete; it changes the scope and must add its own tests,
safety evidence, and review gates.

## Do not claim yet

Do not describe this repo as a production wallet app, custodian, live settlement service, or real payment processor. The accurate wording is:

```text
Public-ready Arc builder kit with local-only payment prototypes, read-only Arc Testnet checks, and a separate disabled-by-default human-operated Arc Testnet browser-wallet send lab.
```
