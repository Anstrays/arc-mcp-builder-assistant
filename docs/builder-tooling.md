# Builder Tooling

Phase 4 of the Arc MCP Builder Assistant ships unified command-line and MCP interfaces over the existing dependency-free kit. The goal is to let builders and AI agents scaffold, validate, and inspect Arc Testnet projects without touching wallets, secrets, or mainnet.

## What is included

- `scripts/arc_builder_cli.py` — human-facing CLI.
- `scripts/arc_builder_mcp_server.py` — stdio MCP server for AI agents.
- `templates/` — dependency-free project starters.
- Tests and validation for all of the above.

## Install from PyPI

Release `0.2.0` requires Python 3.10+ and packages the CLI, MCP server, reviewed Arc Testnet facts,
starter templates, and local examples into one self-contained wheel:

```bash
python3 -m pip install arc-builder-kit==0.2.0
arc-builder --version
arc-builder templates
arc-builder validate
arc-builder x402 challenge http://127.0.0.1:8087/protected
```

The installed integrity check is intentionally narrower than the clone-level
repository validator. It verifies package resources, pinned Arc Testnet facts,
and fail-closed mainnet/custody policy without requiring git, docs, CI files, or
network access.

The installable `arc-builder` entry point also includes a read-only x402 helper:

```bash
# Fetch a 402 challenge for human review.
arc-builder x402 challenge http://127.0.0.1:8087/protected

# Verify an Arc Testnet transaction hash against receipt evidence before retrying
# the protected resource. No private keys, signing, or broadcast are accepted.
arc-builder x402 verify http://127.0.0.1:8087/protected 0x...
```

### Maintainer release flow

PyPI publication uses Trusted Publishing, not a stored API token. Before the
first release, configure a pending GitHub publisher in the PyPI account:

- PyPI project: `arc-builder-kit`
- GitHub owner: `Anstrays`
- Repository: `arc-mcp-builder-assistant`
- Workflow: `publish-pypi.yml`
- Environment: `pypi`

Create the GitHub environment `pypi` and require maintainer approval before
deployment. After the release-fix PR is merged, publish a non-prerelease GitHub
Release from the exact `v0.2.0` tag on `main`. The release event runs the full
suite, verifies all version surfaces, builds wheel/sdist, runs `twine check`,
and publishes through a short-lived OIDC credential.

The workflow deliberately has no manual publish trigger, no token secret, and
no `skip-existing` fallback. PyPI versions are immutable; a failed or partially
published release must be diagnosed, not silently overwritten.

## CLI

```bash
python3 scripts/arc_builder_cli.py <command>
```

Commands:

| Command | Purpose |
| --- | --- |
| `doctor` | Run Arc Builder Doctor. |
| `validate` | Run repository validation. |
| `templates` | List available starter templates. |
| `scaffold <template> <output>` | Copy a template to a new directory. |
| `facts` | Print reviewed Arc Testnet facts. |
| `manifest` | Print the local x402 paid-agent manifest. |
| `release-packet [--output <dir>] [--force]` | Generate a maintainer release packet. |
| `mcp` | Start the Arc Builder MCP server. |

Examples:

```bash
python3 scripts/arc_builder_cli.py templates
python3 scripts/arc_builder_cli.py scaffold payment-intent-starter ./my-demo
python3 scripts/arc_builder_cli.py doctor --full
python3 scripts/arc_builder_cli.py release-packet --force
```

## MCP server

The MCP server speaks JSON-RPC over stdio. It exposes the kit as MCP tools so an AI coding agent can query Arc Testnet facts, scaffold projects, run validation, and inspect the local x402 boundary.

Add it to an MCP client that supports stdio transport:

```json
{
  "mcpServers": {
    "arc-builder": {
      "command": "python3",
      "args": ["/path/to/repo/scripts/arc_builder_mcp_server.py"]
    }
  }
}
```

For a PyPI installation, the MCP entry point is shorter:

```json
{
  "mcpServers": {
    "arc-builder": {
      "command": "arc-builder-mcp-server",
      "args": []
    }
  }
}
```

Or run via the CLI:

```bash
python3 scripts/arc_builder_cli.py mcp
```

### Tools

| Tool | Description |
| --- | --- |
| `arc_builder_doctor` | Run doctor and return a structured report. |
| `list_templates` | List starter templates. |
| `scaffold_project` | Copy a template to a new directory. |
| `validate_repo` | Run repository validation. |
| `get_arc_testnet_facts` | Return reviewed Arc Testnet facts. |
| `x402_manifest` | Return the local x402 paid-agent manifest. |
| `x402_paid_request` | Fetch a 402 challenge or verify an Arc Testnet transaction hash proof read-only. |
| `generate_release_packet` | Generate a local maintainer release packet. |
| `list_examples` | List available browser-facing examples. |

All tools return `content` (human-readable) and `structuredContent` (JSON). The server advertises safety flags at initialization: local-only default, no wallet, no signing, no broadcast, testnet-only, no secrets.

## Starter templates

| Template | Files | Use |
| --- | --- | --- |
| `payment-intent-starter` | `index.html`, `index.js` | Static payment-intent UI. |
| `x402-agent-starter` | `server.py` | Local x402 paid-agent boundary. |
| `job-escrow-starter` | `index.html`, `index.js` | Static ERC-8183-style escrow UI. |

Scaffold a template:

```bash
python3 scripts/arc_builder_cli.py scaffold x402-agent-starter ./my-agent
```

Each template is intentionally minimal and dependency-free. They are not production-ready without a separate reviewed integration.

## Safety boundaries

- All tools default to local-only operation.
- No wallet connection, signing, or transaction broadcast.
- No private keys, seed phrases, or API keys are handled.
- The x402 template rejects `X402_DEMO_MAINNET_ENABLED=true`.
- Network calls are opt-in only (e.g., `doctor --include-arc-rpc`).

## Tests

```bash
python3 scripts/test_arc_builder_cli.py
python3 scripts/test_arc_builder_mcp_server.py
python3 scripts/test_templates.py
python3 scripts/test_package_distribution.py
```

These are also included in the canonical suite:

```bash
python3 scripts/test_all.py
```

## Graphify and repository hooks

Graphify is optional and is not a runtime or build dependency. Its official
PyPI package is `graphifyy`; the command remains `graphify`. This repository
does not auto-install or execute third-party hooks.

For local AST indexing, install it in an isolated tool environment and keep the
generated graph local:

```bash
uv tool install graphifyy
graphify . --no-viz
```

`graphify hook install` installs Graphify's official `post-commit` and
`post-checkout` refresh hooks. It is not a pre-commit security control. Before
using it, review the installed package and generated hook files. Do not enable
remote LLM backends or URL ingestion with repository credentials present.

The repository-owned pre-commit hook only checks staged path policy and runs
the existing local secret scanner. It makes no network calls and never invokes
Graphify:

```bash
python3 scripts/install_repo_hooks.py
```

The installer refuses to overwrite an unknown existing pre-commit hook.
Generated `graphify-out/` data is intentionally ignored for this project to
avoid committing machine-local indexes or large review-noise artifacts.
