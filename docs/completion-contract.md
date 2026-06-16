# Safe-scope completion contract

This contract defines what **100% complete** means for the current Arc MCP
Builder Assistant scope. It turns the readiness claim into reproducible checks
while keeping the only write-capable testnet surface narrow and fail-closed.

## Definition of complete

The repository is complete for the current safe scope when a new builder can
clone it, run one dependency-free test command, preview the public site, use
the local examples, and understand exactly what is shipped, verified,
deferred, and prohibited.

The canonical test command requires Python 3.12+ and Node.js 18+. It installs
no packages and uses Node built-ins only for actual-JavaScript behavior
harnesses.

Completion applies to this public builder kit only. It does not mean the repo
is a production wallet, custodian, payment processor, live verifier, or
autonomous spending agent.

## Acceptance criteria

- `python scripts/test_all.py` passes from the repository root.
- Each canonical child check has an explicit timeout and fails clearly instead
  of hanging indefinitely.
- The canonical runner gives child checks an isolated, automatically cleaned
  repository-local temporary directory instead of assuming system TEMP access.
- The README gives a runnable quickstart, configuration table,
  troubleshooting guidance, architecture map, and explicit safety boundary.
- Required public docs are available through the styled docs viewer.
- Public HTML has safe links, CSP metadata, reduced-motion handling, no
  executable inline scripts, and no obvious mojibake.
- Landing and docs surfaces keep narrow grid items contained and long content
  wrap-safe for mobile viewports.
- Local Markdown links resolve to committed files.
- Core local examples and their targeted regression tests pass.
- The Arc Agent Treasury Lab uses exact micro-USDC accounting, denies replay,
  reserve breaches, spend-cap breaches, and unprofitable work, then fails
  closed when verification retries or runtime spend preflight fail.
- Dependency-free Node fake-provider/fake-RPC harnesses execute the actual
  guarded-send and transaction-status JavaScript without wallets or live RPC.
- The read-only receipt viewer stops on a wrong chain, validates the JSON-RPC
  response envelope, binds the receipt hash to the reviewer input, highlights
  pinned Arc Testnet USDC Transfer logs, and keeps settlement claims false.
- A dependency-free actual-JavaScript docs-viewer harness proves malicious
  Markdown HTML and URLs stay escaped while reviewed links remain usable.
- Read-only transaction evidence stops on a wrong chain, validates the
  JSON-RPC response envelope, and binds returned transaction/receipt hashes to
  the exact reviewer-supplied hash.
- The separate guarded Arc Testnet send lab is disabled by default, requires
  an injected user-controlled wallet and explicit human gates, caps transfers
  at `1.00` USDC, and permits one attempt per page load.
- x402 demo config stays Arc Testnet only and rejects mainnet or malformed
  payment settings.
- x402 direct helpers enforce the same safe config as the CLI, and MCP stdio
  rejects malformed JSON-RPC envelopes before tool dispatch.
- x402 runtime dispatch enforces published no-extra-field schemas, bounds and
  de-duplicates proof input, and rejects malformed, unavailable, or unsafe
  verifier results without exposing internal failure details.
- Local x402 HTTP mode rejects non-loopback hosts, and live smoke rejects
  malformed URLs, embedded credentials, unsafe proof transport, and invalid
  timeouts.
- `.env.example` contains placeholders only; `.env` and local operator
  evidence drafts remain ignored.
- Operator evidence can be generated as an intentionally incomplete local
  draft, reported without mutation, and validated fail-closed.
- Security and contribution docs explain private reporting, canonical tests,
  and review expectations.
- CI actions are pinned to full commit SHAs, use explicit Python/Node
  versions, reject permission shorthands, and enforce exact least-privilege
  permission maps.
- Current readiness and build-log pages distinguish shipped behavior from
  future extension work.

## Canonical verification

Run:

```bash
python scripts/check_completion.py
python scripts/test_all.py
python examples/x402-local-challenge-server/server.py --print-challenge
python examples/x402-local-challenge-server/server.py --print-manifest
```

Optional read-only network evidence:

```bash
python scripts/check_arc_testnet_status.py
```

The completion check verifies required surfaces, canonical regression-suite
coverage, and safety-boundary markers. The full suite then exercises the
examples and repository validator. Neither command requests wallet
permissions, signs, settles, or broadcasts. There is no wallet connection on
page load and no transaction broadcast on page load.

## Explicit non-goals

The current complete scope includes Arc-focused docs, stablecoin and
agent-commerce prototypes, a local x402-style boundary, read-only Arc Testnet
status, a local policy-gated agent treasury simulator, and operator-evidence
tooling.

The current scope explicitly has:

- no private keys or seed phrases;
- no custody or autonomous spending;
- no production verifier credentials;
- no mainnet support;
- no wallet connection on page load;
- no transaction broadcast on page load, in local-only examples, or in tests;
- one attempt per page load in the separate guarded Arc Testnet send lab;
- no claim of live settlement or real paid-resource unlock.

The guarded lab delegates signing and submission to an external injected
wallet only after explicit human review. Any future custody, mainnet, live
x402 verifier, Circle Gateway, or settlement path must be proposed as a
separate guarded change with current Arc facts, human approval, rollback
criteria, and new tests.

## Reviewer verdict

Use this wording only after the canonical verification passes:

> Complete for the current public-ready, local-first Arc builder-kit scope.
> A separate disabled-by-default Arc Testnet browser-wallet send lab is
> shipped; custody, mainnet, autonomous spending, and live settlement remain
> intentionally unimplemented non-goals.
