# Safe-scope completion contract

This contract defines what **100% complete** means for the current Arc MCP
Builder Assistant scope. It turns the readiness claim into reproducible checks
while keeping higher-risk wallet and settlement work outside the public kit.

## Definition of complete

The repository is complete for the current safe scope when a new builder can
clone it, run one dependency-free test command, preview the public site, use
the local examples, and understand exactly what is shipped, verified,
deferred, and prohibited.

Completion applies to this public builder kit only. It does not mean the repo
is a production wallet, custodian, payment processor, live verifier, or
autonomous spending agent.

## Acceptance criteria

- `python scripts/test_all.py` passes from the repository root.
- The README gives a runnable quickstart, configuration table,
  troubleshooting guidance, architecture map, and explicit safety boundary.
- Required public docs are available through the styled docs viewer.
- Public HTML has safe links, CSP metadata, reduced-motion handling, no
  executable inline scripts, and no obvious mojibake.
- Landing and docs surfaces keep narrow grid items contained and long content
  wrap-safe for mobile viewports.
- Local Markdown links resolve to committed files.
- Core local examples and their targeted regression tests pass.
- x402 demo config stays Arc Testnet only and rejects mainnet or malformed
  payment settings.
- Local x402 HTTP mode rejects non-loopback hosts, and live smoke rejects
  malformed URLs, embedded credentials, unsafe proof transport, and invalid
  timeouts.
- `.env.example` contains placeholders only; `.env` and local operator
  evidence drafts remain ignored.
- Operator evidence can be generated as an intentionally incomplete local
  draft, reported without mutation, and validated fail-closed.
- Security and contribution docs explain private reporting, canonical tests,
  and review expectations.
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
permissions, signs, settles, or broadcasts.

## Explicit non-goals

The current complete scope includes Arc-focused docs, stablecoin and
agent-commerce prototypes, a local x402-style boundary, read-only Arc Testnet
status, and operator-evidence tooling.

The current scope explicitly has:

- no private keys or seed phrases;
- no wallet connection or signing;
- no custody or autonomous spending;
- no production verifier credentials;
- no mainnet support;
- no transaction broadcast;
- no claim of live settlement or real paid-resource unlock.

Any future wallet send, live x402 verifier, Circle Gateway, or settlement path
must be proposed as a separate guarded change with current Arc facts, human
approval, rollback criteria, and new tests.

## Reviewer verdict

Use this wording only after the canonical verification passes:

> Complete for the current public-ready, local-first Arc builder-kit scope.
> Higher-risk wallet, signing, settlement, and broadcast integrations remain
> intentionally unimplemented non-goals.
