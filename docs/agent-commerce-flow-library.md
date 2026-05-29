# Agent commerce flow library

Local-only flow templates for the Arc agent-commerce starter kit. These flows reuse the component contract from `docs/agent-commerce-components.md` and stay intentionally short of wallet signing, transaction broadcast, or production Gateway/x402 verification.

## Shared safety boundary

- Arc Testnet only: chain ID `5042002`, chain hex `0x4cef52`, native gas asset `USDC`.
- ERC-20 USDC accounting uses 6 decimals; native gas accounting uses 18 decimals.
- Human approval remains mandatory for every money-moving intent.
- Flow output is a review artifact, not a transaction instruction.
- No private keys, seed phrases, browser wallet requests, remote RPC calls, or backend calls.
- Future live settlement must be a separate PR with wallet chain gating, frozen money fields, and explicit reviewer approval.

## Flow 1: Paid API call

**Goal:** A research agent asks to buy one paid data response.

- Agent proposes the data source, endpoint purpose, cost, and freshness need.
- User reviews the recipient, amount, asset, chain, memo, and spending cap.
- Local flow freezes the payment request and records `payment_required_local`.
- Simulated receipt records whether the API payload would be released after a verified payment.

Good for: market data, token intelligence, legal/company lookups, report enrichment, private search APIs.

## Flow 2: Creator payout

**Goal:** A project lead reviews a payout line item for a contributor.

- Agent converts work evidence into a proposed payout memo.
- User checks recipient, role, deliverable URL, amount, and payout reason.
- Local flow freezes the payout request and records `approved_local_no_broadcast`.
- Simulated receipt becomes an auditable payout note without pretending funds moved.

Good for: editors, designers, translators, bounty contributors, community moderators.

## Flow 3: AI-agent commerce

**Goal:** One agent asks to call another specialist agent under a human-approved spend cap.

- Initiating agent describes the specialist action and budget.
- User checks the specialist identity, trust notes, quote, and cap.
- Local flow freezes the request before any future x402/Gateway proof path.
- Simulated receipt records specialist output metadata and cost basis.

Good for: code review agents, summarizers, data labelers, research workers, enrichment services.

## Review object fields

Each flow emits this minimum shape:

```json
{
  "schema": "arc-mcp-builder-assistant.agentCommerce.flow.v1",
  "flowId": "paid-api-call",
  "network": {
    "name": "arc-testnet",
    "chainId": 5042002,
    "erc20UsdcDecimals": 6
  },
  "agent": {
    "displayName": "Research Agent",
    "role": "paid-api-gateway"
  },
  "request": {
    "purpose": "Buy one market-data response",
    "recipient": "0x0000000000000000000000000000000000000000",
    "amount": "1.25",
    "asset": "USDC",
    "humanApprovalRequired": true,
    "frozenBeforeWallet": true
  },
  "receipt": {
    "status": "simulated",
    "transactionBroadcast": false
  }
}
```

## Add-vs-skip tradeoff

Add these flows when the repo needs demoable product direction beyond generic components. Skip live settlement until Circle Gateway/x402 credentials, wallet chain gating, transaction verification, and user approval UX are in scope.
