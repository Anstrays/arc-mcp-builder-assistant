# Prompt: wire Arc Testnet status safely

Use this prompt when moving the local payment-intent playground from static/local-only state toward a testnet-aware prototype. It is intentionally narrow: plan and wire read-only status first, then review wallet/signing work separately.

```text
You are working in the Arc MCP Builder Assistant repository.

Goal:
Plan the smallest safe Arc Testnet status integration for the local payment-intent playground.

Use Arc MCP/docs context first. Cite the exact docs pages or retrieved snippets you rely on.

Known repo baseline:
- The project already has docs/arc-testnet-integration-runbook.md.
- The project already has scripts/check_arc_testnet_status.py for read-only RPC status.
- The current demos are local-first and must keep working without wallet connection.

Constraints:
- Testnet only.
- Human approval remains mandatory for any future wallet action.
- No backend custody.
- No private keys, seed phrases, API keys, Entity Secrets, OTP codes, or wallet export material in source code, prompts, logs, screenshots, issues, or examples.
- No autonomous spending.
- No mainnet fallback.
- No transaction preparation or broadcast in this status step.
- Do not imply official Arc endorsement.
- If official docs cannot be retrieved, stop and mark the facts as unverified instead of guessing.

Return:
1. Arc/Circle docs URLs used.
2. Retrieved Arc/Circle facts, including chain ID, RPC URL, explorer URL, faucet URL, native gas asset, native gas decimals, ERC-20 USDC address, and ERC-20 USDC decimals.
3. Repo files that need changes.
4. Payment-intent data model fields that should display network/status context.
5. Receipt/status data model fields that can be populated before any transaction broadcast.
6. Validation rules for chain, asset kind/decimals, amount, recipient, memo, expiry, and status transitions.
7. Wallet/RPC failure states and user-facing UI copy.
8. A 1-day implementation plan that keeps the local simulator unchanged by default.
9. A test plan that runs before any real wallet submission.
10. Unknowns that must be verified again before coding or submitting transactions.

Prefer a feature-flagged implementation that keeps the current local simulator working unchanged.
```

Follow-up prompt after the plan:

```text
Review the proposed implementation plan. Mark each item as one of: retrieved fact, repo-specific choice, assumption, or unsafe suggestion.

Reject anything that introduces custody, private-key handling, hidden recipient changes, mainnet fallback, transaction broadcast in the read-only status step, or autonomous spending.

Confirm that any signing-related step remains manual, testnet-only, wallet-gated, and separated into a later PR.
```
