# Prompt: wire Arc Testnet status safely

Use this prompt when moving the local payment-intent playground toward a testnet-aware prototype.

```text
You are working in the Arc MCP Builder Assistant repository.

Goal:
Plan the smallest safe Arc Testnet integration for the local payment-intent playground.

Use Arc MCP/docs context first. Cite the exact docs pages or retrieved snippets you rely on.

Constraints:
- Testnet only.
- Human approval remains mandatory.
- No backend custody.
- No private keys, seed phrases, API keys, or wallet export material in source code, prompts, logs, screenshots, or issues.
- No autonomous spending.
- No mainnet fallback.
- Do not imply official Arc endorsement.

Return:
1. Retrieved Arc/Circle facts.
2. Repo files that need changes.
3. Payment-intent data model changes.
4. Receipt/status data model changes.
5. Validation rules for chain, asset, amount, recipient, memo, expiry, and status transitions.
6. Wallet/RPC failure states and UI copy.
7. A 1-day implementation plan.
8. A test plan that can run before real wallet submission.
9. Unknowns that must be verified again before coding.

Prefer a feature-flagged implementation that keeps the current local simulator working unchanged.
```

Follow-up prompt after the plan:

```text
Review the proposed implementation plan. Mark each item as one of: retrieved fact, repo-specific choice, assumption, or unsafe suggestion. Reject anything that introduces custody, private-key handling, hidden recipient changes, mainnet fallback, or autonomous spending.
```
