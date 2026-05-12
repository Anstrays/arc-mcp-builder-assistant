# Arc MCP Prompt Library

> Copy-paste prompts for using Arc's MCP/docs surface with AI coding agents. The goal is to keep the agent grounded in official docs, explicit about unknowns, and conservative around wallets, secrets, and transaction signing.

Source context:

- Arc MCP HTTP server: `https://docs.arc.network/mcp`
- Arc docs index: `https://docs.arc.network/llms.txt`
- Arc MCP docs page: https://docs.arc.network/ai/mcp

## How to use these prompts

1. Connect your AI coding tool to Arc MCP first. See [`arc-mcp-setup.md`](./arc-mcp-setup.md).
2. Start every build session by asking the agent to cite the Arc docs pages it used.
3. Ask for implementation plans before code changes.
4. Keep private keys, seed phrases, Circle API keys, Entity Secrets, OTP codes, and wallet credentials out of chat.
5. Treat payment and wallet actions as human-approved steps unless you have explicitly configured a scoped testnet or policy-limited environment.

## Grounding prompt

```text
Use Arc MCP/docs as the primary source for this task.

Before making recommendations, return:
1. the Arc docs pages you searched or opened;
2. the exact facts you are relying on;
3. any unknowns or assumptions;
4. a conservative implementation plan.

Do not invent contract addresses, chain IDs, RPC URLs, SDK methods, or wallet behavior. If the docs do not confirm a detail, mark it as unknown.
```

## MCP setup verification prompt

```text
Verify that my Arc MCP setup works.

Use the Arc docs MCP server to:
1. search for the Arc MCP server page;
2. search for Arc Testnet network configuration;
3. search for ERC-8004 agent registration;
4. return the docs URLs and a short summary of each page.

If the MCP tools are unavailable, tell me which client configuration to check first.
```

## Arc docs map prompt

```text
Create a builder-focused map of Arc docs for an AI agent payment prototype.

Include:
- Arc Testnet chain config;
- RPC and explorer URLs;
- USDC/EURC contract references;
- ERC-8004 agent identity registries;
- ERC-8183 job escrow reference implementation;
- node providers and infrastructure providers;
- tutorials that matter for payment intents, contracts, event monitoring, and agent identity.

Return links to official Arc docs for each section.
```

## Payment-intent demo planning prompt

```text
Use Arc MCP/docs context to design a safe payment-intent demo.

Constraints:
- local/static first;
- no private keys in the browser;
- no backend custody;
- no transaction broadcast unless a human explicitly approves;
- no autonomous mainnet spending;
- all unknown chain/wallet details must be labeled unknown.

Return:
1. data model for a payment intent;
2. UI states from draft to approved/submitted/paid/failed;
3. trust boundaries;
4. validation rules;
5. a follow-up path for Arc Testnet integration.
```

## Working local app prompt

```text
Turn the static payment-intent mockup into a local-only working app.

Build only local functionality:
- form fields for amount, asset, recipient, memo, expiry, and purpose;
- deterministic payment-intent JSON output;
- client-side validation;
- copy/export button;
- risk and trust-boundary panel;
- disabled transaction controls with clear explanatory copy.

Do not add wallet connection, backend calls, private-key handling, or transaction broadcast.
```

## Arc Testnet integration prompt

```text
Plan the first Arc Testnet integration for this payment-intent app.

Use official Arc docs and return:
- confirmed chain ID, RPC URL, explorer URL, native gas asset, and decimals caveats;
- wallet options and tradeoffs;
- whether the integration should use browser wallet, Circle Wallets, or a local script;
- exact files to add or change;
- safety gates before any signing or broadcasting;
- a test plan that avoids real mainnet funds.

Do not implement until chain and wallet details are explicitly confirmed.
```

## ERC-8004 agent identity prompt

```text
Use Arc MCP/docs to summarize the ERC-8004 agent registration tutorial.

Return:
1. Arc Testnet registry contracts;
2. what the agent identity represents;
3. what reputation and validation records represent;
4. how this identity could be linked to a payment-intent or ERC-8183 job flow;
5. what should remain offchain;
6. safe next steps for a local prototype.

Do not create wallets, submit transactions, or expose credentials.
```

## ERC-8183 job escrow prompt

```text
Use Arc MCP/docs to summarize the ERC-8183 job lifecycle for an agentic commerce demo.

Return:
- the Arc Testnet AgenticCommerce reference contract;
- job creation, budget, escrow, deliverable hash, evaluation, and settlement steps;
- which actors are involved;
- which steps require wallet signing;
- how to represent the flow in a local UI before any onchain transaction.
```

## Circle Contracts template prompt

```text
Use Arc's deploy-contracts tutorial to compare the Circle Contracts templates available on Arc Testnet.

Cover:
- ERC-20;
- ERC-721;
- ERC-1155;
- Airdrop.

For each template, explain the likely builder use case for agentic commerce, required configuration, deployment verification, and security warnings. Do not include real API keys, Entity Secrets, or wallet credentials.
```

## Security review prompt

```text
Review this Arc/MCP/agent payment prototype for safety.

Focus on:
- private-key or credential exposure;
- wallet connection assumptions;
- backend/custody assumptions;
- transaction broadcast paths;
- missing human approval gates;
- incorrect Arc Testnet addresses or chain config;
- claims that are not backed by official docs.

Return blockers first, then non-blocking polish.
```
