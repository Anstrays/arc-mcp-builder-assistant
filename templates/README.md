# Arc Builder Starter Templates

Dependency-free project scaffolds for the Arc MCP Builder Assistant.

| Template | Files | Use |
| --- | --- | --- |
| `payment-intent-starter` | `index.html`, `index.js` | Static payment-intent UI. |
| `x402-agent-starter` | `server.py` | Local x402 paid-agent boundary. |
| `marketplace` | `server.py` | Agent-to-agent marketplace with buyer/seller intent flow. |
| `treasury` | `index.html` | Treasury management UI with balance and send intents. |
| `x402-verified-api` | `server.py` | Paid API endpoint with on-chain x402 payment verification. |
| `job-escrow-starter` | `index.html`, `index.js` | Static ERC-8183-style escrow UI. |

## Scaffold a new project

```bash
python3 scripts/arc_builder_cli.py scaffold payment-intent-starter ./my-payment-demo
```

Or via the Arc Builder MCP server with the `scaffold_project` tool.

## Safety

All templates are:
- Arc Testnet only.
- Wallet-free and secret-free.
- Human-approved at every spending-related step.
- Not production-ready without a separate reviewed integration.
