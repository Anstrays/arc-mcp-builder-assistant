# Current readiness report

This report is the short checkpoint for deciding whether the Arc MCP Builder Assistant is finished for the current scope, and what remains outside that scope.

## Verdict

The repository is **complete for the current public-ready static builder-kit scope**.

That scope includes docs-grounded Arc/MCP workflows, local-only playgrounds, review packets, screenshots, CI validation, read-only Arc Testnet status checks, and explicit wallet/send guardrails. It intentionally stops before private keys, wallet permission requests, signing, custody, live settlement, real paid-agent verification, or transaction broadcast.

## Latest local evidence

Run these commands from the repository root before publishing a new checkpoint:

```bash
python3 scripts/test_all.py
python3 scripts/check_arc_testnet_status.py
```

Expected safe result:

- `scripts/test_all.py` finishes with `all checks passed` for the full local regression suite.
- `scripts/check_arc_testnet_status.py` returns `ok: true`, confirms Arc Testnet chain ID `5042002 / 0x4cef52`, and reports the latest block through the read-only RPC.
- Neither command requests wallet permissions, collects secrets, signs, estimates gas, simulates a transaction, or broadcasts.

## Shipped working surfaces

- GitHub Pages landing page and styled docs viewer.
- Arc MCP setup, docs map, prompt library, builder workflows, and deployment/runbook docs.
- Local payment-intent playground with reviewable JSON, frozen intent fields, explicit local approval states, USDC unit preview, unsigned ERC-20 transaction draft, calldata consistency check, final local confirmation, and blocked wallet handoff manifest.
- Read-only transaction-status playground for Arc Testnet transaction hashes.
- Local receipt verifier playground.
- Local x402 challenge boundary with machine-readable manifest and MCP-style JSON-RPC helpers.
- Agent-commerce components, flow library, review packet, agent identity profile preview, and job escrow simulator.
- Static validation for required files, safe HTML, SEO/meta basics, local links, viewer coverage, and obvious credential patterns.

## Remaining work is optional extension work

These are not blockers for the current public kit. They are separate future PRs because each adds higher-risk integration surface:

1. **Testnet-only wallet send path**
   - Requires a separate reviewed PR.
   - Must keep chain ID, token decimals, frozen intent fields, fresh human confirmation, and rollback criteria enforced immediately before any wallet prompt.
   - Must not add mainnet fallback or autonomous spending.

2. **Live x402 / Circle verifier handoff**
   - Requires real verifier credentials and deployed endpoint configuration outside the committed repo.
   - Must keep `.env.example` placeholders only and avoid committing secrets.
   - Should begin with challenge-only smoke before any paid resource unlock claim.

3. **Public distribution**
   - Sharing the build log, content pack, or Arc House submission copy is a distribution step, not a missing product feature.

## Safe next increment

The next safe code/documentation increment is to keep this report wired into the README, landing page, docs viewer, and validator so reviewers can quickly see the current status without reading every roadmap page.

## Do not claim yet

Do not describe this repo as a production wallet app, custodian, live settlement service, or real payment processor. The accurate wording is:

```text
Public-ready Arc builder kit with local-only payment and agent-commerce prototypes, read-only Arc Testnet checks, and review-first guardrails for future wallet or verifier integrations.
```
