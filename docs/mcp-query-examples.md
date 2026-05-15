# Arc MCP Query Examples

These examples show how to use Arc docs context with an AI coding tool without letting the model invent chain details. They are intentionally written as copy-paste prompts and expected output shapes.

## Rule for all queries

Ask the assistant to separate three things:

1. **Retrieved facts** — what the Arc docs/MCP context says.
2. **Implementation suggestion** — how to use those facts in code.
3. **Unknowns** — anything not found or not verified.

## Query 1 — Arc Testnet config

```txt
Use Arc MCP/docs context. Find the current Arc Testnet chain ID, RPC endpoint guidance, explorer link, native gas asset assumptions, and any wallet setup notes. Return only facts grounded in retrieved docs, then show a minimal viem/wagmi config draft.
```

Expected output shape:

```txt
Retrieved facts:
- Chain ID: ...
- RPC: ...
- Explorer: ...
- Gas asset: ...

Implementation draft:
...

Unknowns / verify before shipping:
...
```

## Query 2 — Payment intent data model

```txt
Use Arc MCP/docs context and this repository's payment-intent spec. Design a minimal payment intent object for a USDC request where an AI agent prepares the request and a human approves manually. Include fields, validation rules, and status transitions. Do not add autonomous spending.
```

## Query 3 — ERC-8004 agent identity

```txt
Use Arc MCP/docs context. Summarize the current ERC-8004 agent identity flow on Arc. Explain which fields a payment-intent demo should display to help a human evaluate an agent before approving a payment.
```

## Query 4 — ERC-8183 job escrow

```txt
Use Arc MCP/docs context. Map the ERC-8183/job escrow flow into a safe demo where a user funds a job, an agent submits work, and the user approves release. Include events/statuses to monitor and list unknowns that must be verified before testnet integration.
```

## Query 5 — Contract deployment notes

```txt
Use Arc MCP/docs context. Find the current deploy-contracts tutorial path and summarize how to deploy a minimal receipt, credits, or airdrop contract on Arc Testnet. Keep the output as a checklist and include security caveats.
```

## Query 6 — Security review prompt

```txt
Review this Arc payment/agent demo for safety. Flag any private-key handling, hidden spending authority, unclear recipient, missing chain checks, missing human approval, weak status labels, or claims that imply official Arc endorsement. Return blocking issues first.
```

## Query 7 — Build log prompt

```txt
Turn today's changes into a public Arc builder update. Include: what was built, which Arc primitives it touches, what is still mock/testnet-only, safety boundaries, screenshots or links, and the next 1-day task.
```

## Notes

If an answer lacks citations or says "probably", treat it as draft only. Re-run the query with more specific context or check the Arc docs directly before writing code.
