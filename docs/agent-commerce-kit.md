# Agent Commerce Kit — ERC-8004 & ERC-8183

> Reusable components, notes, and flows for agent identity and job escrow on Arc.

---

## ERC-8004 — Agent Identity

### Overview

Arc implements ERC-8004 for onchain AI agent identity. Three registries on Arc Testnet:

| Registry | Address |
| --- | --- |
| IdentityRegistry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| ReputationRegistry | `0x8004B663056A597Dffe9eCcC1965A193B7388713` |
| ValidationRegistry | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` |

### Flow

1. **Register agent** — call `IdentityRegistry.register()` with agent metadata (name, description, endpoint)
2. **Record reputation** — `ReputationRegistry.recordReputation()` for completed jobs
3. **Verify credentials** — `ValidationRegistry.verify()` for agent credentials

### Integration with Payment Intents

Agent identity can be embedded in payment intents:

```ts
type PaymentIntent = {
  id: string;
  agentId?: string;       // ERC-8004 agent ID
  agentName?: string;     // Human-readable name
  recipient: string;      // Agent's wallet address
  amount: string;
  asset: 'USDC' | string;
  memo: string;
  status: 'draft' | 'pending_user_approval' | 'submitted' | 'confirmed' | 'failed' | 'cancelled';
  txHash?: string;
}
```

### CLI Usage

```bash
# Quick reference (requires Circle API credentials)
arc-builder docs search "ERC-8004 agent identity"
arc-builder docs search "register AI agent"
```

---

## ERC-8183 — Job Escrow

### Overview

Arc's ERC-8183 enables agent-to-agent job escrows. The reference implementation is deployed at:

| Component | Address |
| --- | --- |
| AgenticCommerce | `0x0747EEf0706327138c69792bF28Cd525089e4583` |

### Flow

```
1. Create developer-controlled SCA wallets
2. Create a job (specify task, deliverables, payment)
3. Fund escrow with USDC
4. Agent submits deliverable hash
5. Evaluator verifies and completes the job
6. Funds are settled to the agent
```

### Minimal Example

```python
# Pseudocode for ERC-8183 job flow
job_steps = [
    ("Create Wallets", "Use CircleWalletClient.create_wallets()"),
    ("Create Job", "call AgenticCommerce.createJob(taskDescription, deliverableHash)"),
    ("Fund Escrow", "Send USDC to escrow contract"),
    ("Submit Work", "Agent submits deliverableHash onchain"),
    ("Complete Job", "Evaluator calls completeJob()"),
    ("Settle Funds", "Escrow releases USDC to agent"),
]
```

### Builder Use Cases

- Agent-to-agent paid tasks
- Freelance / microservice escrow
- Verifiable deliverable hash
- Reputation-based agent marketplace

---

## Agent Profile Card (HTML component)

A minimal agent profile card that can be embedded in any UI:

```html
<div class="agent-card">
  <div class="agent-avatar">🤖</div>
  <div class="agent-name">Research Agent</div>
  <div class="agent-id">ID: 0x8004...A494BD9e</div>
  <div class="agent-status">Verified ✓</div>
  <div class="agent-reputation">⭐ 4.8 (23 jobs)</div>
</div>
```

---

## Quick Prompts

### Agent Identity Prompt

```text
Use Arc MCP/docs context to design a minimal agent registration flow on Arc Testnet:
1. Register agent using ERC-8004 IdentityRegistry
2. Record reputation for completed jobs
3. Connect identity to payment intents
Use Arc Testnet only. No mainnet.
```

### Job Escrow Prompt

```text
Design a minimal agent-to-agent job escrow flow on Arc using ERC-8183:
1. Job creation with deliverables
2. USDC escrow funding
3. Deliverable submission and verification
4. Settlement
Arc Testnet only.
```
