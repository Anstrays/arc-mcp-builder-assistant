# Agentic maintainer loop

This document defines a practical operating loop for using AI agents on this
repository without weakening the Arc-only, non-custodial, dependency-free
scope.

It is inspired by the loop-engineering framing in
[Проектирование циклов для AI-агентов](https://telegra.ph/Proektirovanie-ciklov-dlya-AI-agentov-06-17),
but adapts it to this repository instead of adding LangChain, LangSmith, a
backend service, or a new runtime dependency.

## Purpose

The goal is to make agent work repeatable:

1. Give the agent a narrow Arc builder task.
2. Let it inspect the repository and make a minimal change.
3. Force deterministic verification before it reports success.
4. Convert every bug, failed check, or review finding into a regression test.
5. Keep sensitive actions behind human approval.

The loop is for maintainers and coding agents. It is not a payment runtime,
wallet service, custody layer, or autonomous spender.

## Loop 1: task execution

The agent loop is the normal coding pass:

```text
task -> inspect repo -> identify root cause -> edit -> run checks -> report
```

Required behavior:

- read the relevant files before editing;
- keep changes scoped to the requested Arc builder surface;
- prefer existing project patterns over new abstractions;
- never stage unrelated files blindly;
- never request, store, print, or invent secrets;
- never connect a real wallet, sign, or broadcast transactions.

Useful agent roles:

| Role | Allowed work | Stop condition |
| --- | --- | --- |
| Builder | Implement docs, examples, tests, local validators. | Needs credentials, real wallet, production endpoint, or destructive action. |
| Reviewer | Inspect diff for bugs, security gaps, and missing tests. | Needs external maintainer decision. |
| CI fixer | Read failing logs, reproduce locally, patch narrowly. | Failure needs a secret, service outage, or unrelated branch change. |
| Release checker | Run readiness commands and summarize merge risk. | Arc facts changed or public claims are no longer true. |

## Loop 2: verification

No agent pass is complete until verification runs. The canonical local command
is:

```bash
python scripts/test_all.py
```

For higher-risk payment, wallet, docs-viewer, or public-readiness changes, add:

```bash
python scripts/validate_repo.py
python scripts/scan_for_secrets.py
python scripts/validate_arc_testnet_facts.py
python scripts/validate_live_infrastructure_policy.py
python scripts/arc_builder_doctor.py --include-arc-rpc --strict
git diff --check
```

For JavaScript changes, run syntax checks across tracked JavaScript files:

```bash
node --check examples/payment-intent-playground/playground.js
node --check examples/transaction-status-playground/status.js
node --check examples/receipt-viewer/receipt-viewer.js
node --check examples/payment-intent-receipt-matcher/matcher.js
```

If a page script uses Subresource Integrity, recompute the SRI hash after every
script change and keep the matching test in place.

## Loop 3: event-driven maintenance

Events can trigger agents, but they must not bypass review.

Safe triggers:

- pull request opened or updated;
- CI failure;
- scheduled readiness monitor warning;
- public GitHub Pages drift;
- official Arc Testnet facts changed;
- maintainer asks for a focused improvement pass.

Recommended response map:

| Event | Agent action | Human gate |
| --- | --- | --- |
| CI red | Read logs, reproduce locally, patch narrowly, push. | Merge remains human-approved. |
| Review comment | Address only actionable comments, add tests when possible. | Reviewer resolves or approves. |
| Arc facts drift | Update pinned facts and affected docs/tests. | Maintainer confirms official source. |
| Security finding | Stop if a secret is involved, redact output, propose rotation. | Maintainer handles secret rotation. |
| Wallet/payment request | Keep real wallet actions manual and out of automation. | Human operates wallet in a separate reviewed runbook. |

Do not create an event loop that can sign, spend, broadcast, change production
credentials, or merge to `main` without maintainer approval.

## Loop 4: improvement

The improvement loop turns repeated failures into better guardrails.

When an agent or reviewer finds a gap, prefer this sequence:

1. Write a failing regression test or validator marker.
2. Fix the smallest relevant code or docs surface.
3. Run the targeted test.
4. Run `python scripts/test_all.py`.
5. Document the new boundary if it affects public behavior.

Examples:

- If a matcher accepts malformed payment amounts, add harness cases for zero,
  negative, over-precision, hex, and scientific notation before fixing parser
  code.
- If a docs page can be removed without detection, add it to
  `scripts/validate_repo.py` and `docs/viewer.js`.
- If a public claim implies production readiness, add a public-claims
  regression check instead of relying on review memory.
- If a secret scanner false positive is a public deterministic constant, add a
  narrow allowlist entry with a comment. Do not weaken the whole scanner.

## Human approval gates

Agents may automate reading, editing, testing, reporting, and PR preparation.
They must stop before:

- real wallet connection;
- message signing;
- transaction signing;
- transaction broadcast;
- private-key or seed-phrase handling;
- custody or account-abstraction provider setup;
- production verifier credentials;
- mainnet configuration;
- destructive filesystem or Git operations;
- merge, release, or deployment without explicit maintainer approval.

For the guarded Arc Testnet wallet-send lab, automation may inspect source code
and fake-provider tests only. Real-wallet smoke remains a separate manual
runbook with a disposable test wallet.

## Standard agent prompt

Use this structure for Codex, GLM, Claude Code, or Hermes:

```text
Work as an autonomous maintainer agent for Anstrays/arc-mcp-builder-assistant.

Goal:
<one focused Arc builder task>

Constraints:
- Arc Testnet only.
- No custody, mainnet, private keys, seed phrases, autonomous spending, or real
  wallet automation.
- Keep local-only demos wallet-free.
- Keep write-capable wallet-send behavior disabled by default and human-gated.
- Add dependency-free tests for new behavior.

Cycle:
1. Inspect repo state.
2. Reproduce or identify the issue.
3. Find root cause.
4. Make the minimal change.
5. Run targeted checks.
6. Run canonical checks.
7. If checks fail, read logs, fix, and repeat.
8. Stop only for missing external access, secrets, real wallet actions, or
   maintainer approval gates.

Verification:
- python scripts/test_all.py
- python scripts/validate_repo.py
- python scripts/scan_for_secrets.py
- git diff --check

Final report:
- summary
- files changed
- commands and PASS/FAIL
- security boundary
- remaining risks
- merge recommendation
```

## Repository fit

This repository should remain static-site-first and dependency-free. The loop is
implemented through prompts, tests, validators, CI, and review discipline, not
through a new framework dependency.

The correct long-term direction is:

```text
agent work -> deterministic checks -> CI -> PR review -> regression tests
      ^                                                |
      |                                                v
      +--------- failed check or review finding --------+
```

That keeps the project useful for Arc builders while preserving the current
safety boundary: no custody, no mainnet, no secrets, no autonomous spending,
and no real wallet automation.
