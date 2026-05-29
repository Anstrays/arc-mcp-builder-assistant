# Agent identity profile preview

This page adds a local-only ERC-8004 identity profile preview for the Arc MCP Builder Assistant. It is meant to sit between static identity notes and a future reviewed registration flow.

## Source grounding

Official Arc docs describe ERC-8004 on Arc Testnet as a flow where a builder registers an AI agent identity, records reputation from an external validator, and requests/ verifies validation responses. The Arc Testnet registry addresses used by this repo are:

- IdentityRegistry: `0x8004A818BFB912233c491871b3d84c89A494BD9e`
- ReputationRegistry: `0x8004B663056A597Dffe9eCcC1965A193B7388713`
- ValidationRegistry: `0x8004Cb1BF31DAf7788923b405b754f57acEB4272`

## What this preview does

- Lets a reviewer draft agent display metadata, capabilities, controller notes, reputation notes, and validation requirements.
- Emits a machine-readable profile object that can be copied into docs, a future manifest, or a future registration checklist.
- Marks every identity field as `unregistered_local_preview` until a real Arc Testnet transaction is signed, broadcast, and confirmed.
- Separates profile metadata from wallet authority and payment authority.

## What this preview does not do

- It does not create wallets.
- It does not upload metadata to IPFS or any remote storage.
- It does not call Arc RPC, Circle APIs, browser wallets, or Gateway/x402 verifiers.
- It does not register ERC-8004 identities, record reputation, request validation, sign, or broadcast transactions.
- It does not imply endorsement, KYC, validation, reputation, or payment eligibility.

## Review flow

1. Draft the public-facing agent profile.
2. Review controller and validator notes separately.
3. Freeze the profile draft before future registration work.
4. Export the JSON object and compare it with official Arc docs before any live implementation.

## Minimum profile object

```json
{
  "schema": "arc-mcp-builder-assistant.agentIdentity.preview.v1",
  "status": "unregistered_local_preview",
  "network": {
    "name": "arc-testnet",
    "chainId": 5042002
  },
  "registries": {
    "identityRegistry": "0x8004A818BFB912233c491871b3d84c89A494BD9e",
    "reputationRegistry": "0x8004B663056A597Dffe9eCcC1965A193B7388713",
    "validationRegistry": "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
  },
  "profile": {
    "name": "Research Buyer Agent",
    "agentType": "research",
    "capabilities": ["quote-paid-data", "prepare-payment-intent"],
    "metadataUri": "not_uploaded"
  },
  "safety": {
    "walletConnected": false,
    "registrationTransactionPrepared": false,
    "transactionBroadcast": false,
    "humanApprovalRequired": true
  }
}
```

## Future live-registration gate

A later PR may add real registration only after it has: official docs cited in the PR, chain gating to Arc Testnet, explicit human review, no secrets in prompts or static files, transaction preview before signing, confirmation tracking after broadcast, and separate handling for owner and validator roles.
