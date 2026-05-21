# Arc Testnet Integration Runbook

This runbook is the next step after the local payment-intent, job-escrow, and x402 demos. It turns the project from a local-only builder kit into a safe testnet prototype without jumping directly into production credentials or autonomous spending.

## Goal

Ship one minimal Arc Testnet flow where an AI agent prepares payment/job context, a human reviews it, and the app records observable testnet status.

The first real integration should be **payment intent → manual wallet approval → tx hash/status**. Job escrow and x402 settlement can reuse the same verified network, wallet, and status primitives afterward.

## Source-grounded Arc facts checked for this runbook

Checked docs:

- Arc docs index: `https://docs.arc.io/llms.txt`
- Connect to Arc: `https://docs.arc.io/arc/references/connect-to-arc.md`
- Contract addresses: `https://docs.arc.io/arc/references/contract-addresses.md`

Current facts from those docs:

- Network: Arc Testnet.
- Chain ID: `5042002`.
- Primary RPC: `https://rpc.testnet.arc.network`.
- Explorer: `https://testnet.arcscan.app`.
- Faucet: `https://faucet.circle.com`.
- Currency symbol: `USDC`.
- Arc uses USDC as the native gas token.
- Native gas precision is 18 decimals.
- The optional ERC-20 USDC interface is `0x3600000000000000000000000000000000000000` and uses 6 decimals.
- Arc docs say all listed contract addresses are for Arc Testnet; mainnet addresses are not yet available.

Re-check these before writing transaction code. Treat this file as a snapshot, not a permanent source of truth.

## Non-negotiable safety rules

- No private keys, seed phrases, Entity Secrets, API keys, or wallet credentials in the repo.
- No server-side custody.
- No autonomous spending.
- No mainnet claims or mainnet configuration.
- The user must manually approve every wallet transaction.
- The UI must display chain ID, recipient, asset, amount, memo, expiry, and status before approval.
- The app must block signing unless the wallet is connected to Arc Testnet chain ID `5042002`.
- The app must distinguish native USDC gas precision from ERC-20 USDC transfer precision.
- Every transaction status must be observable through tx hash, explorer link, and app timeline.

## Recommended implementation sequence

### 1. Add read-only network status

Create a tiny status helper before adding signing:

- request `eth_chainId` from the configured RPC;
- request latest block number;
- show explorer base URL;
- fail closed if the chain ID is not `0x4cef52` / `5042002`.

This can be implemented without secrets and without wallet access.

### 2. Add wallet-gated payment intent preview

Extend the existing payment-intent playground so it can show:

- expected network: Arc Testnet;
- connected chain ID;
- connected address;
- recipient address;
- USDC amount as a decimal string;
- parsed ERC-20 USDC base units with 6 decimals;
- human-readable warning that gas uses native USDC with 18 decimals.

No transaction is prepared yet in this step.

### 3. Add manual send path

Only after the preview is correct:

- require connected chain ID `5042002`;
- build a standard ERC-20 `transfer` call to the USDC interface;
- require explicit user wallet confirmation;
- capture tx hash;
- link to `https://testnet.arcscan.app/tx/<hash>`;
- mark status as `submitted`.

### 4. Add confirmation/status polling

Poll receipt by tx hash:

- `pending` while receipt is absent;
- `confirmed` when status is success;
- `failed` when receipt status is failure;
- include block number and explorer link.

Arc docs describe sub-second finality, but the UI should still handle RPC delay, wallet rejection, wrong-chain, and unknown-transaction states.

### 5. Reuse the primitive

Once payment-intent status is verified, reuse the same primitives for:

- job escrow simulator status labels;
- x402 local challenge verifier replacement boundary;
- future ERC-8183 job escrow contract interaction.

## Acceptance criteria for the first real testnet PR

- A user can open the app and see Arc Testnet readiness without secrets.
- Wrong-chain wallets are blocked before signing.
- A payment intent is visible as JSON before wallet confirmation.
- The app never hides recipient, amount, asset, memo, expiry, or chain ID.
- Wallet signing happens only through a human-initiated button.
- A submitted tx hash renders as an ArcScan link.
- The code contains no private keys, API keys, or production credentials.
- Local validator and CI pass.

## Suggested PR split

1. **Read-only Arc Testnet status kit**: docs, optional status checker, UI status panel. No wallet signing.
2. **Wallet preview**: connect wallet, show chain/account/intent, wrong-chain guard. No send.
3. **Manual testnet send**: user-approved ERC-20 USDC transfer and tx status.
4. **Job/x402 follow-up**: reuse verified status primitives.

## Copy-paste implementation prompt

```txt
Use current Arc docs/MCP context and this repository's docs. Implement the next smallest Arc Testnet step without secrets or autonomous spending.

Scope:
- Add read-only Arc Testnet status first.
- Do not add private-key handling.
- Do not add production credentials.
- Do not add mainnet config.
- Do not submit transactions unless a human clicks an explicit approval button in a later PR.

Required source facts to verify before coding:
- Arc Testnet chain ID
- RPC endpoint
- explorer URL
- USDC native gas behavior
- ERC-20 USDC interface address and decimals

Return:
1. retrieved Arc facts with URLs;
2. files to change;
3. safety invariants;
4. tests/validator updates;
5. exact manual smoke test steps.
```
