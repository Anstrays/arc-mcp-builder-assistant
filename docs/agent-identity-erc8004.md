# ERC-8004 Agent Identity Notes on Arc

> Builder notes for connecting Arc's ERC-8004 agent registration tutorial to payment-intent and agentic commerce prototypes.

Source docs:

- https://docs.arc.network/arc/tutorials/register-your-first-ai-agent
- https://docs.arc.network/build/agentic-economy
- https://docs.arc.network/arc/tutorials/create-your-first-erc-8183-job

This page is an independent summary. Verify contract addresses and API behavior against official Arc docs before deploying or funding anything.

## Why ERC-8004 matters here

The payment-intent demo is intentionally local and human-approved. ERC-8004 is the next layer for identity: it gives an AI agent a discoverable onchain identity and a place to attach reputation or validation records.

A useful progression is:

1. **Local payment intent** — agent prepares amount, asset, recipient, memo, expiry, and rationale.
2. **Human approval** — user reviews and signs only when ready.
3. **Agent identity** — agent address or identity token links the request to a known agent.
4. **Reputation / validation** — external validators or counterparties can record feedback.
5. **Job escrow** — ERC-8183 can represent paid work with escrow, deliverables, and settlement.

## Arc Testnet ERC-8004 registries

| Registry | Arc Testnet address | Purpose |
| --- | --- | --- |
| IdentityRegistry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` | Registers an AI agent with onchain identity. |
| ReputationRegistry | `0x8004B663056A597Dffe9eCcC1965A193B7388713` | Records reputation feedback. |
| ValidationRegistry | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` | Requests and verifies validation responses. |

Arc's tutorial summary says the flow creates or prepares two Arc Testnet wallets, registers an AI agent with a unique onchain identity, records reputation feedback from an external validator, and requests validation that is verified onchain.

## What should be onchain vs offchain

### Good onchain candidates

- Agent identity registration.
- Agent owner/controller address.
- Reputation events or validation references.
- Job IDs and escrow settlement state.
- Hashes of deliverables or signed artifacts.

### Better kept offchain

- Private prompts, raw user data, API keys, Entity Secrets, seed phrases, OTPs, and private keys.
- Full deliverable content unless the user explicitly wants it public.
- Sensitive customer, counterparty, or compliance data.
- Unreviewed agent reasoning traces.

## Mapping to this repo

| Repo piece | ERC-8004 connection |
| --- | --- |
| `docs/payment-intent-demo.md` | Add optional `agentIdentity` field once identity details are confirmed. |
| `examples/payment-intent-demo/` | Show a non-signing identity preview before wallet connection exists. |
| `docs/arc-docs-map.md` | Keep registry addresses discoverable with official source links. |
| `docs/prompt-library.md` | Include prompts that force the agent to cite docs and mark unknowns. |

## Suggested payment-intent identity fields

```json
{
  "agent": {
    "displayName": "Example Research Agent",
    "identityRegistry": "0x8004A818BFB912233c491871b3d84c89A494BD9e",
    "agentId": "unknown-until-registered",
    "controllerAddress": "unknown-until-wallet-confirmed",
    "reputationRegistry": "0x8004B663056A597Dffe9eCcC1965A193B7388713",
    "validationRegistry": "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
  }
}
```

Keep these fields informational in the static/local prototype. Do not imply that an identity is registered until a transaction has been signed, broadcast, and confirmed on Arc Testnet.

## Trust boundaries

- The agent may prepare identity metadata and explain the registration flow.
- The user chooses whether to create wallets, register identity, or publish reputation events.
- No private key, seed phrase, Circle Entity Secret, API key, or OTP should be pasted into prompts.
- Any future implementation should show the exact transaction, contract address, chain ID, and expected fee before signing.
- Mainnet behavior should be disabled until policy, funding, and spending limits are explicit.

## Open implementation questions

Before turning this into a live flow, confirm:

1. Which wallet model to use: browser wallet, Circle Wallets, local script, or another account abstraction provider.
2. Whether the identity registration should happen inside this app or in a separate setup script.
3. How to display agent identity without implying trust or endorsement.
4. How reputation/validation events map to payment-intent outcomes.
5. Whether ERC-8183 job escrow is required for the first working demo or should remain a later phase.

## Builder prompt

```text
Use Arc MCP/docs to design a safe ERC-8004 extension for the payment-intent demo.

Return:
1. confirmed Arc Testnet registry addresses;
2. wallet/signing prerequisites;
3. proposed payment-intent JSON fields;
4. user approval steps;
5. what remains local/offchain;
6. tests and validation checks.

Do not submit transactions or handle secrets.
```
