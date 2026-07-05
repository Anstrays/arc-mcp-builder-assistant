# Changelog

All notable changes to the Arc MCP Builder Assistant are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- **Feature:** Added `RpcVerifier` to x402 challenge server — verifies X-Payment
  tx hashes on-chain via `eth_getTransactionReceipt` on Arc Testnet.
- **CLI:** `x402-local-challenge-server` gained `--verifier-mode rpc` flag.
- **Doctor:** Added `--include-circle-wallet` flag to `arc-builder doctor` — checks Circle CLI
  presence, agent session (email + expiry), wallet on Arc Testnet, and USDC balance via Circle CLI.
- **Feature:** Payment Intent Demo now integrates a **live Circle wallet** via Circle CLI:
  - Real USDC balance display on Arc Testnet (`circle wallet balance`)
  - Recent transaction history (`circle transaction list`)
  - On-chain gas estimates for every intent (`circle wallet transfer --estimate`)
  - Optional real USDC transfers (`REAL_TRANSFER=1` env var, double opt-in)
  - New REST endpoints: `GET /api/wallet`, `GET /api/transactions`, `GET /api/estimate`
- **Docs:** Updated `docs/payment-intent-demo.md` with Circle wallet spec, added `examples/payment-intent-demo/README.md`.

## [0.3.0] — 2026-07-04

### Added
- **MCP Server v2:** structured error classes (`ValidationError`,
  `ToolNotFoundError`, `TimeoutError`, `RpcError`, `PaymentError`) with
  standard JSON-RPC codes, retry hints, and user-facing messages.
- **Progress streaming:** long-running tools emit progress notifications
  on stderr.
- **Wallet MCP tools:** `wallet_status`, `wallet_balance`,
  `wallet_prepare_send` — guard-only, no signing/broadcasting.
- **Result metadata:** every tool response includes `meta.durationMs`.
- **Zero-amount guard:** `circle_wallet_sdk.prepare_send_intent` now rejects
  zero/negative USDC amounts.
- **Templates:** `marketplace/`, `treasury/`, `x402-verified-api/` starter
  projects added to `templates/`.

### Changed
- `scripts/arc_builder_mcp_server.py` reduced to thin wrapper over package
  (500 → 34 lines).
- README: updated pip version references, wallet subcommands, new templates.
- 14 MCP tools total (was 11).

### Fixed
- Audited zero-amount edge case in `prepare_send_intent`.
- Replaced `getattr(args, "network")` with direct `args.network` in CLI.

## [0.2.2] — 2026-07-02

### Added
- **Agent Commerce Kit docs** — ERC-8004 + ERC-8183 flow documentation.
- **Payment Intent Demo** — interactive Web UI with `server.py` + `index.html`.
- **CI/CD** — `.github/workflows/ci.yml` (test + build + Pages).

### Fixed
- `scripts/validate_repo.py` — fixed false positives in HTML/meta validation.

## [0.2.1] — 2026-06-30

### Fixed
- PyPI metadata: project URLs, classifiers, version bump.
- Package resources and trusted publishing configuration.

## [0.2.0] — 2026-06-29

### Added
- **Python package** (`arc-builder-kit`): CLI (`arc-builder`) + stdio MCP server.
- **`arc_builder_kit` modules:**
  - `arc_client.py` — read-only Arc docs client.
  - `circle_wallet_sdk.py` — guard-only Circle SDK plan builder.
  - `cli.py` — unified CLI (templates, validate, facts, wallet).
  - `doctor.py` — Arc Builder Doctor readiness checks.
  - `mcp_server.py` — stdio MCP server (8 tools).
  - `release_packet.py` — release packet generator.
  - `validate_repo.py` — repo validation script.
  - `x402_client.py` — read-only x402 challenge/response client.
- **Web UI** — static site redesign (light theme, Docs viewer, playgrounds).
- **MCP setup guide** (`docs/arc-mcp-setup.md`) — Claude Code, Claude Desktop,
  Cursor, VS Code, Windsurf, HTTP MCP clients.
- **Prompt library** (`docs/prompt-library.md`).
- **Agent Commerce Kit** — interactive examples (components, flows, live
  evidence, identity profile, treasury lab).
- **x402 challenge server** — local demo with MCP-style stdio and HTTP modes.
- **Templates:** `payment-intent-starter/`, `x402-agent-starter/`,
  `job-escrow-starter/`.
- **Examples:** wallet-send gate, receipt viewer, receipt verifier playground,
  transaction status playground, Circle wallet integration lab, job escrow
  simulator, Arc paid API endpoint.
- **CI/CD workflows:**
  - `validate.yml` — repo validation on push/PR.
  - `pages.yml` — GitHub Pages deployment.
  - `publish-pypi.yml` — trusted publishing to PyPI.
  - `readiness-monitor.yml` — scheduled Arc readiness check.
- **Arc Builder Doctor** — readiness checks, Markdown reports, Testnet facts
  contract, operator evidence (validator, draft generator, readiness report,
  commit binding).
- **Operator evidence** — full pipeline (validator → draft → commit-binding →
  readiness report).
- **Receipt matcher** — payment-intent receipt verification with security
  hardening (DoS protection, strict amount parsing, fail-closed validation,
  agentic maintainer loop).
- **Wallet send gate** — guarded Arc Testnet wallet-send readiness kit.

### Changed
- Static site: light theme, unified palette, mobile breakpoints, SEO/a11y.
- `README.md`: comprehensive restructuring with TOC, quickstart, safety docs.

### Security
- Secret scanner (`scripts/scan_for_secrets.py`).
- CSP, CORS, X-Content-Type-Options headers on all served pages.
- Dependabot configuration for GitHub Actions and Python deps.
- Codeowners file.

## [0.1.0] — 2026-05-15

### Added
- Initial static site with dark theme.
- Arc docs map (`docs/arc-docs-map.md`).
- Basic payment intent playground.
- Job escrow simulator.
- 3 prompts: explain Arc docs, build payment intent, deploy contracts.

[Unreleased]: https://github.com/Anstrays/arc-mcp-builder-assistant/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Anstrays/arc-mcp-builder-assistant/releases/tag/v0.3.0
[0.2.2]: https://github.com/Anstrays/arc-mcp-builder-assistant/releases/tag/v0.2.2
[0.2.1]: https://github.com/Anstrays/arc-mcp-builder-assistant/releases/tag/v0.2.1
[0.2.0]: https://github.com/Anstrays/arc-mcp-builder-assistant/releases/tag/v0.2.0
[0.1.0]: https://github.com/Anstrays/arc-mcp-builder-assistant/releases/tag/v0.1.0
