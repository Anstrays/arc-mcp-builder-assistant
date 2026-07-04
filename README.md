# Arc MCP Builder Assistant

> Independent early-stage builder resource for exploring Arc's MCP server, AI-assisted development workflows, and agentic commerce prototypes.

Arc MCP Builder Assistant is a **lightweight documentation + Python toolkit** that helps builders use Arc's official MCP/docs surface with AI coding tools to prototype faster.

## What's included

### 🐍 Python Package — `arc-builder-kit`

Installable toolkit with:

| Module | Description |
|--------|-------------|
| `ArcDocsClient` | Async HTTP client for Arc's MCP server (doc search/read) |
| `CircleWalletClient` | Async client for Circle Developer-Controlled Wallets API |
| `mcp_server` | Self-contained MCP server (14 tools, dependency-free JSON-RPC over stdio) |
| `cli` | Typer CLI — `arc-builder wallet list`, `arc-builder docs search`, etc. |

**14 MCP tools** available via the MCP server:

- `search_arc_docs` / `get_arc_page` / `list_arc_tools` / `fetch_llms_txt` — Arc documentation
- `wallet_status` / `wallet_balance` / `wallet_list` / `wallet_send` — Circle wallet operations
- `get_transaction` / `create_wallet_set` — transaction management
- `arc_docs_overview` / `quickstart_prompt` / `template_info` / `estimate_fee` — builder helpers

```bash
# Install
pip install arc-builder-kit

# Or from repo
pip install -e .

# CLI
arc-builder --version
arc-builder wallet list
arc-builder docs search "ERC-8004 agent identity"

# MCP server (stdio)
python scripts/arc_builder_mcp_server.py
```

### 📚 Documentation

- [`docs/arc-mcp-setup.md`](docs/arc-mcp-setup.md) — Arc MCP setup for Claude, Cursor, VS Code, Windsurf
- [`docs/arc-docs-map.md`](docs/arc-docs-map.md) — Practical map of Arc Testnet config, contracts, ERC-8004, ERC-8183
- [`docs/deploy-contracts-arc.md`](docs/deploy-contracts-arc.md) — Deploy contracts with Circle + Arc Testnet
- [`docs/builder-workflows.md`](docs/builder-workflows.md) — Practical Arc + AI builder workflows
- [`docs/payment-intent-demo.md`](docs/payment-intent-demo.md) — Payment intent demo specification
- [`docs/agent-commerce-kit.md`](docs/agent-commerce-kit.md) — ERC-8004 agent identity + ERC-8183 job escrow

### 🖥️ Payment Intent Demo

A working web UI prototype:

```bash
python3 examples/payment-intent-demo/server.py
# → http://localhost:8080
```

- Create payment intents (recipient, amount, asset, memo)
- Review and approve manually
- View Arc Testnet network info
- Backend API ready for real Circle wallet integration

### 🎯 Prompts

Copy-paste prompts for AI coding tools:

- [`explain-arc-docs.md`](prompts/explain-arc-docs.md)
- [`build-payment-intent-demo.md`](prompts/build-payment-intent-demo.md)
- [`deploy-contracts-on-arc.md`](prompts/deploy-contracts-on-arc.md)
- [`register-agent-notes.md`](prompts/register-agent-notes.md)

## Quick start

```bash
# 1. Install the toolkit
pip install -e .

# 2. Run the MCP server
python scripts/arc_builder_mcp_server.py

# 3. Or start the web UI
python3 examples/payment-intent-demo/server.py
```

## Roadmap

| Phase | Status |
|-------|--------|
| Phase A — Python `arc-builder-kit` package | ✅ v0.1.0 |
| Phase B — Web UI prototype with API | ✅ |
| Phase C — Agent Commerce Kit (ERC-8004/8183) | ✅ |
| Phase D — DevOps / CI | ✅ |
| Phase E — PyPI publish & GitHub Release | 🔜 |

## Development

```bash
# Install in dev mode
pip install -e .

# Run tests
python3 -m unittest discover -s tests -v

# Validate repo
python3 scripts/validate_repo.py

# Build wheel
python3 -m build --wheel --no-isolation
```
