# Payment Intent Demo Spec

## Thesis

A safe first version of agentic commerce is not a fully autonomous spending bot. It is an AI agent that can create a structured payment request, while a human user stays in control of approval.

## User story

As a user, I want an AI agent to prepare a clear USDC payment request so I can review and approve it manually on Arc.

## MVP flow

1. User opens demo app.
2. Agent card explains its purpose.
3. Agent creates a payment intent:
   - recipient
   - amount
   - asset, e.g. USDC
   - memo
   - reason
   - expiry
4. User reviews the payment intent and the Arc Testnet read-only status panel:
   - expected chain ID `5042002` / `0x4cef52`
   - RPC URL
   - no wallet connection
   - no transaction broadcast
5. User clicks approve.
6. Future wallet/testnet transaction path is submitted only after chain gating and manual wallet confirmation.
7. App displays status and receipt.

## Data model draft

```ts
type PaymentIntent = {
  id: string;
  agentId?: string;
  recipient: string;
  amount: string;
  asset: 'USDC' | string;
  memo: string;
  reason: string;
  status: 'draft' | 'pending_user_approval' | 'submitted' | 'confirmed' | 'failed' | 'cancelled';
  txHash?: string;
  createdAt: string;
  expiresAt?: string;
};
```

## Non-goals for v0

- No autonomous spending without human approval.
- No mainnet funds.
- No custody.
- No private key handling.
- No claim of official Arc endorsement.

## Open questions to verify in Arc docs

- Current Arc Testnet RPC / chain ID.
- Recommended wallet setup.
- Recommended USDC/token contract assumptions.
- Current ERC-8004 agent registration flow.
- Whether Arc has official SDK examples for payment/agent flows.

## First prototype options

### Option A: static UI mockup

Fastest. Shows the workflow and helps get feedback.

### Option B: local app with mocked transaction

Useful before exact testnet details are verified.

### Option C: testnet-connected app

Best builder signal once current docs are confirmed.
