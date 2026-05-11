# Arc MCP Setup Notes

> Goal: help builders connect AI tools to Arc documentation through Arc's MCP server, then use that context to prototype Arc apps faster.

## What Arc MCP appears to provide

Based on the public search snippet for `docs.arc.network/ai/mcp`, Arc's MCP server gives AI tools direct access to Arc documentation so they can search relevant content and retrieve full docs while building.

Because full docs extraction may be blocked in some environments, verify exact setup commands directly from the official docs page before publishing final instructions:

- https://docs.arc.network/ai/mcp
- https://docs.arc.network/

## Builder workflow

1. Open the official Arc MCP docs.
2. Copy the exact MCP server configuration for your AI tool.
3. Add the server to your tool config.
4. Restart the AI tool / agent runtime.
5. Ask a small verification question, e.g.:

```text
Search Arc docs for agentic economy and summarize the primitives relevant to AI-agent payment flows.
```

6. Use retrieved docs to generate a scoped implementation plan.

## Hermes-style MCP configuration pattern

If your agent runtime supports MCP servers in YAML, the shape is usually one of these:

### HTTP transport

```yaml
mcp_servers:
  arc:
    url: "https://<official-arc-mcp-url-from-docs>"
    timeout: 120
    connect_timeout: 60
```

### Stdio transport

```yaml
mcp_servers:
  arc:
    command: "npx"
    args: ["-y", "<official-arc-mcp-package-from-docs>"]
    timeout: 120
    connect_timeout: 60
```

Do not use these placeholders directly. Replace them with the official values from Arc docs.

## Verification prompts

```text
Using Arc docs through MCP, list the pages relevant to: MCP setup, agentic economy, ERC-8004 agent registration, stablecoin payments, and testnet development.
```

```text
Using Arc docs through MCP, generate a minimal implementation plan for an Arc payment-intent demo. Include only official APIs/primitives that appear in the docs.
```

```text
Using Arc docs through MCP, explain what a builder should avoid assuming before integrating wallet or testnet features.
```

## Security checklist

- Never expose private keys or seed phrases to an MCP server.
- Use testnet wallets only for demos.
- Keep `.env` out of git.
- Pin dependencies when the prototype becomes executable.
- Treat MCP output as docs context, not automatic authority to run commands.
