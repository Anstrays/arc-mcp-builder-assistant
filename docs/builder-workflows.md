# Arc + AI Builder Workflows

This kit focuses on practical workflows that match Arc's public narrative around stablecoin finance and agentic economy apps.

## Workflow 1: Docs-aware AI coding

**Goal:** reduce friction for new Arc builders.

Flow:

1. Connect Arc MCP to an AI coding assistant.
2. Ask targeted questions against current Arc docs.
3. Generate a small implementation plan.
4. Build only against verified docs.
5. Publish notes for other builders.

Example prompt:

```text
Use Arc MCP docs to identify the minimum steps required to build a payment-intent demo on Arc Testnet. Return a 1-day implementation plan with unknowns clearly marked.
```

## Workflow 2: Agent payment intent

**Goal:** show a safe first step toward agentic commerce.

Flow:

1. AI agent proposes a payment request.
2. User reviews the purpose, recipient, amount, and memo.
3. User manually approves the transaction.
4. App records transaction status and receipt.

This avoids unsafe autonomous spending while still showing the commerce primitive.

## Workflow 3: Agent identity notes

**Goal:** help builders understand onchain agent identity.

Flow:

1. Follow Arc's official tutorial for registering an AI agent.
2. Document exact steps and gotchas.
3. Connect identity to a demo UI.
4. Show how identity can be used in payment receipts/logs.

## Workflow 4: Builder content loop

**Goal:** turn building into useful community contribution.

Cadence:

- Day 1: publish the problem statement and repo scaffold.
- Day 2: publish MCP setup notes.
- Day 3: publish payment-intent mockup/demo.
- Day 4: publish lessons learned and open questions.
- Day 5: ask for feedback from Arc builders.

Avoid airdrop/points language in public posts. Frame it as builder feedback, docs, demos, and practical onboarding.
