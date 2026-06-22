# Builder Tooling

Phase 4 of the Arc MCP Builder Assistant ships unified command-line and MCP interfaces over the existing dependency-free kit. The goal is to let builders and AI agents scaffold, validate, and inspect Arc Testnet projects without touching wallets, secrets, or mainnet.

## What is included

- `scripts/arc_builder_cli.py` — human-facing CLI.
- `scripts/arc_builder_mcp_server.py` — stdio MCP server for AI agents.
- `templates/` — dependency-free project starters.
- Tests and validation for all of the above.

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
| `mcp` | Start the Arc Builder MCP server. |

Examples:

```bash
python3 scripts/arc_builder_cli.py templates
python3 scripts/arc_builder_cli.py scaffold payment-intent-starter ./my-demo
python3 scripts/arc_builder_cli.py doctor --full
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
```

These are also included in the canonical suite:

```bash
python3 scripts/test_all.py
```
