# Arc MCP Setup Notes

> Goal: help builders connect AI tools to Arc documentation through Arc's official MCP server, then use that context to prototype Arc apps faster.

Source docs:

- https://docs.arc.network/ai/mcp
- https://docs.arc.network/llms.txt

## Official Arc MCP facts

Arc's Model Context Protocol server is hosted at:

```text
https://docs.arc.network/mcp
```

It requires **no authentication**.

The server exposes two documentation tools:

1. **Search** — finds relevant documentation snippets based on a query.
2. **Get page** — retrieves the full content of a specific documentation page.

Arc also publishes a machine-readable documentation index:

```text
https://docs.arc.network/llms.txt
```

Use `llms.txt` to discover available pages before drilling into specific docs.

## Claude Code

```bash
claude mcp add --transport http arc-docs https://docs.arc.network/mcp
```

Claude Code automatically discovers the server's tools in the next conversation.

## Claude Desktop

1. Open **Settings**.
2. Go to **Connectors**.
3. Select **Add custom connector**.
4. Name: `Arc Docs`.
5. URL: `https://docs.arc.network/mcp`.
6. During a chat, use the attachments button to select the Arc Docs connector.

## Cursor

Add this to your Cursor `mcp.json` file via **Cursor Settings > MCP**:

```json
{
  "mcpServers": {
    "arc-docs": {
      "url": "https://docs.arc.network/mcp"
    }
  }
}
```

## VS Code / Copilot

Create or update `.vscode/mcp.json` in your project root:

```json
{
  "servers": {
    "arc-docs": {
      "type": "http",
      "url": "https://docs.arc.network/mcp"
    }
  }
}
```

## Windsurf

Add this to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "arc-docs": {
      "serverUrl": "https://docs.arc.network/mcp"
    }
  }
}
```

## Other MCP clients

Any MCP-compatible client can connect using HTTP transport:

```text
URL: https://docs.arc.network/mcp
Transport: http
Auth: none
```

Follow your client-specific configuration format.

## Hermes-style MCP configuration

For Hermes/OpenClaw-style YAML configuration, use HTTP transport like this:

```yaml
mcp_servers:
  arc-docs:
    url: "https://docs.arc.network/mcp"
    timeout: 120
    connect_timeout: 60
```

Then restart the agent runtime so MCP tools are discovered at startup.

Expected tool naming depends on the client. In Hermes-style clients, tools are usually prefixed with the server name, for example:

```text
mcp_arc_docs_<tool_name>
```

## Verify the connection

Ask your AI tool:

```text
What smart contract standards does Arc support? Use Arc docs as the source.
```

Or:

```text
Search Arc docs for deploy contracts, MCP server, agentic economy, and ERC-8004 agent registration. Return the relevant page URLs first.
```

If the tool does not return Arc-sourced content:

- Check the URL exactly: `https://docs.arc.network/mcp`
- Check that HTTPS network access is available.
- Restart the client or start a new session.
- Confirm the MCP client supports HTTP transport.

## Good builder prompts

```text
Use Arc MCP docs to identify the minimum steps required to deploy a contract on Arc Testnet using Circle Contracts. Return prerequisites, commands, required environment variables, and safe handling notes.
```

```text
Use Arc MCP docs to design a payment-intent demo that stays human-approved. Include only primitives that appear in Arc docs and mark unknowns explicitly.
```

## Security checklist

- Never paste private keys, seed phrases, Circle API keys, or Entity Secrets into AI chat.
- Keep `.env` out of git.
- Use testnet credentials and testnet wallets for demos.
- Treat MCP output as documentation context, not permission to run unreviewed commands.
- Mark unknowns instead of inventing contract addresses, chain IDs, or API details.
