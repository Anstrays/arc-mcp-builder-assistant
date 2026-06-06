# Arc Builder Readiness Checklist

Use this checklist before sharing an Arc demo, opening a PR, or submitting the project to an Arc builder program. It keeps the project docs-grounded, safe, and easy for another builder to reproduce.

## 1. Context grounding

- [ ] Arc MCP server or current Arc docs were checked before implementation.
- [ ] The prompt or issue asks the AI tool to cite the Arc docs it used.
- [ ] Chain IDs, RPC URLs, explorers, contract addresses, and token assumptions are copied from current docs, not memory.
- [ ] For Arc Testnet work, [`arc-testnet-integration-runbook.md`](./arc-testnet-integration-runbook.md) was checked and any stale constants were re-verified.
- [ ] Open questions are listed instead of guessed.

## 2. Payment safety

- [ ] No private keys, seed phrases, entity secrets, API keys, or wallet credentials are committed.
- [ ] The demo is testnet-first unless a human explicitly chooses otherwise.
- [ ] Wallet signing is blocked unless the connected chain is Arc Testnet (`5042002`).
- [ ] The agent can prepare intent data, but a human approves every wallet action.
- [ ] Spending limits and recipient details are visible before approval.
- [ ] The UI says whether it is a mockup, local simulation, testnet transaction, or production flow.

## 3. Agent-commerce UX

- [ ] Every payment intent has an agent, recipient, asset, amount, memo, expiry, and status.
- [ ] Users can inspect the raw JSON before any signing step.
- [ ] Status is observable through logs, ArcScan, or an app event timeline.
- [ ] The UI distinguishes native USDC gas precision from ERC-20 USDC transfer precision.
- [ ] Failure states are documented: rejected, expired, insufficient funds, wrong chain, and unknown transaction.

## 4. Repository quality

- [ ] `python3 scripts/check_completion.py` passes locally.
- [ ] `python3 scripts/test_all.py` passes locally.
- [ ] README explains the purpose, current MVP, local preview, and safety boundaries.
- [ ] GitHub Pages links resolve and the sitemap includes public demo pages.
- [ ] Docs link to specific files instead of vague folders when used from GitHub Pages.
- [ ] Security policy tells contributors how to report sensitive issues privately.
- [ ] The [safe-scope completion contract](./completion-contract.md) still matches public claims and explicit non-goals.

## 5. Operator evidence

- [ ] Any local operator evidence draft remains ignored and intentionally fails strict validation until reviewed.
- [ ] `scripts/report_operator_evidence.py` reports gaps without mutating the packet or exposing credential-like values.
- [ ] Strict evidence validation remains Arc Testnet only, commit-bound, fail-closed, and blocked from live send.

## 6. Builder proof-of-work

- [ ] There is a screenshot, mockup, or live playground that a reviewer can open in under 30 seconds.
- [ ] There is a short build log or submission page describing what changed and what comes next.
- [ ] The project states clearly that it is independent and not an official Arc product.
- [ ] Next steps are small enough to ship in one sitting.
