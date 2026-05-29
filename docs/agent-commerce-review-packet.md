# Agent commerce review packet

This page defines a local-only review packet for Arc agent-commerce demos. It helps reviewers compare an agent identity preview, a proposed commerce flow, and an escrow/release decision before any wallet or network integration exists.

## Purpose

Use the packet as the final artifact before a future live PR. It should answer:

- Which agent is acting?
- What service or job is being priced?
- Which human approvals happened?
- Which safety controls stayed disabled?
- Which outcome is approved, rejected, disputed, expired, cancelled, or still pending?

## Safety boundary

The packet is not a transaction request, wallet handoff, settlement proof, reputation attestation, or validator response. It must remain:

- local-only;
- unsigned;
- unbroadcast;
- secret-free;
- detached from browser wallets, Arc RPC, Circle APIs, Gateway/x402 settlement, and backend services.

## Packet schema

```json
{
  "schema": "arc-mcp-builder-assistant.agentCommerce.reviewPacket.v1",
  "status": "local_review_packet",
  "network": {
    "name": "arc-testnet",
    "chainId": 5042002,
    "chainIdHex": "0x4cef52"
  },
  "agentIdentity": {
    "status": "unregistered_local_preview",
    "agentName": "Research Buyer Agent"
  },
  "commerceFlow": {
    "kind": "paid_api_call",
    "asset": "USDC",
    "amount": "2.50",
    "moneyFieldsFrozen": true
  },
  "escrowReview": {
    "outcome": "approved_for_local_demo",
    "payoutReleased": false
  },
  "controls": {
    "walletConnected": false,
    "signingEnabled": false,
    "transactionBroadcast": false,
    "networkCallsEnabled": false,
    "humanApprovalRequired": true
  }
}
```

## Reviewer checklist

1. Confirm the packet status says `local_review_packet`.
2. Confirm the agent identity status says `unregistered_local_preview` unless a separate registration PR has landed.
3. Confirm money fields are frozen before approval.
4. Confirm terminal no-payout outcomes keep `payoutReleased` false.
5. Confirm all wallet, signing, broadcast, backend, and network controls remain false.
6. Copy the packet into a PR description or build log; do not treat it as a spend authorization.
