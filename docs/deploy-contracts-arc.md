# Deploy Contracts on Arc — Builder Notes

> Practical notes from Arc's official `Deploy contracts` tutorial for turning Arc docs into builder-friendly AI prompts and prototypes.

> Security boundary: this is a separate backend/custody integration path, not
> code used by the static site or guarded browser-wallet lab. Use a disposable
> Arc Testnet project, keep credentials out of frontend code and chat, and use
> a deployment secret manager for any reviewed non-local environment.

Source docs:

- https://docs.arc.network/arc/tutorials/deploy-contracts
- https://developers.circle.com/contracts/scp-templates-overview
- https://developers.circle.com/wallets/dev-controlled

## What the official tutorial covers

Arc's tutorial shows how to deploy pre-audited smart contract templates on **Arc Testnet** using **Circle Contracts** and **Circle Dev-Controlled SCA Wallets**.

Supported template categories in the tutorial:

- ERC-20 — fungible tokens / programmable money / liquidity instruments.
- ERC-721 — unique assets / certificates / identity / unique rights.
- ERC-1155 — multi-asset instruments / tiered assets / batch-style products.
- Airdrop — mass distribution / treasury distributions / stakeholder settlements.

Why this matters for this repo: these templates can become building blocks for agentic commerce demos, payment workflows, creator payout experiments, and tokenized receipts.

## Prerequisites

You need:

1. Node.js v22+
2. Circle Developer Account — https://console.circle.com/
3. Circle API Key — Console → Keys → Create a key → API key → Standard Key
4. Circle Entity Secret — required for Circle Dev-Controlled Wallets SDK

Do **not** commit Circle credentials or expose them to browser code. A local
`.env` is acceptable only for a disposable Arc Testnet experiment and must stay
ignored; use a deployment secret manager for any reviewed non-local environment.

## Project setup

```bash
mkdir hello-arc
cd hello-arc
npm init -y
npm pkg set type=module

npm pkg set scripts.create-wallet="tsx --env-file=.env create-wallet.ts"
npm pkg set scripts.deploy-erc20="tsx --env-file=.env deploy-erc20.ts"
npm pkg set scripts.deploy-erc721="tsx --env-file=.env deploy-erc721.ts"
npm pkg set scripts.deploy-erc1155="tsx --env-file=.env deploy-erc1155.ts"
npm pkg set scripts.deploy-airdrop="tsx --env-file=.env deploy-airdrop.ts"
```

Install dependencies:

```bash
npm install @circle-fin/developer-controlled-wallets @circle-fin/smart-contract-platform
npm install --save-dev tsx typescript @types/node
```

Optional TypeScript setup:

```bash
npx tsc --init
```

Recommended `tsconfig.json` from the docs:

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "types": ["node"]
  }
}
```

## Environment variables

Create `.env` locally:

```dotenv
CIRCLE_API_KEY=YOUR_API_KEY
CIRCLE_ENTITY_SECRET=YOUR_ENTITY_SECRET
CIRCLE_WEB3_API_KEY=YOUR_API_KEY
```

Optional runtime values are added later as you progress:

```dotenv
WALLET_ID=YOUR_WALLET_ID
WALLET_ADDRESS=YOUR_WALLET_ADDRESS
TRANSACTION_ID=YOUR_TRANSACTION_ID
CONTRACT_ID=YOUR_CONTRACT_ID
```

Notes:

- `CIRCLE_API_KEY` is used for Circle Wallets and Contracts API requests.
- `CIRCLE_ENTITY_SECRET` authorizes developer-controlled wallet operations.
- `CIRCLE_WEB3_API_KEY` is used for Python SDK compatibility and can mirror `CIRCLE_API_KEY`.

## Create an Arc Testnet dev-controlled wallet

Create `create-wallet.ts`:

```ts
import { initiateDeveloperControlledWalletsClient } from "@circle-fin/developer-controlled-wallets";

const client = initiateDeveloperControlledWalletsClient({
  apiKey: process.env.CIRCLE_API_KEY,
  entitySecret: process.env.CIRCLE_ENTITY_SECRET,
});

const walletSetResponse = await client.createWalletSet({
  name: "Wallet Set 1",
});

const walletsResponse = await client.createWallets({
  blockchains: ["ARC-TESTNET"],
  count: 1,
  walletSetId: walletSetResponse.data?.walletSet?.id ?? "",
  accountType: "SCA",
});

console.log(JSON.stringify(walletsResponse.data, null, 2));
```

Run:

```bash
npm run create-wallet
```

You should receive a wallet with:

- `blockchain`: `ARC-TESTNET`
- `accountType`: `SCA`
- `custodyType`: `DEVELOPER`
- `address`: your Arc Testnet wallet address

Arc docs recommend SCA wallets because they work with Circle Gas Station for sponsored transaction fees on Arc Testnet.

## Deploy ERC-20 template

Template ID from Arc docs:

```text
a1b74add-23e0-4712-88d1-6b3009e85a86
```

Create `deploy-erc20.ts`:

```ts
import { initiateSmartContractPlatformClient } from "@circle-fin/smart-contract-platform";

const circleContractSdk = initiateSmartContractPlatformClient({
  apiKey: process.env.CIRCLE_API_KEY,
  entitySecret: process.env.CIRCLE_ENTITY_SECRET,
});

const response = await circleContractSdk.deployContractTemplate({
  id: "a1b74add-23e0-4712-88d1-6b3009e85a86",
  blockchain: "ARC-TESTNET",
  name: "MyTokenContract",
  walletId: process.env.WALLET_ID,
  templateParameters: {
    name: "MyToken",
    symbol: "MTK",
    defaultAdmin: process.env.WALLET_ADDRESS,
    primarySaleRecipient: process.env.WALLET_ADDRESS,
  },
  fee: {
    type: "level",
    config: {
      feeLevel: "MEDIUM",
    },
  },
});

console.log(JSON.stringify(response.data, null, 2));
```

Run:

```bash
npm run deploy-erc20
```

A successful response means deployment was **initiated**, not completed. It returns:

- `contractIds`
- `transactionId`

## Check transaction status

Create `check-transaction.ts`:

```ts
import { initiateDeveloperControlledWalletsClient } from "@circle-fin/developer-controlled-wallets";

const circleDeveloperSdk = initiateDeveloperControlledWalletsClient({
  apiKey: process.env.CIRCLE_API_KEY,
  entitySecret: process.env.CIRCLE_ENTITY_SECRET,
});

const transactionResponse = await circleDeveloperSdk.getTransaction({
  id: process.env.TRANSACTION_ID!,
});

console.log(JSON.stringify(transactionResponse.data, null, 2));
```

Add script and run:

```bash
npm pkg set scripts.check-transaction="tsx --env-file=.env check-transaction.ts"
npm run check-transaction
```

Status may show `PENDING` first. Wait 10-30 seconds and re-run until `COMPLETE`.

## Get deployed contract address

Create `get-contract.ts`:

```ts
import { initiateSmartContractPlatformClient } from "@circle-fin/smart-contract-platform";

const circleContractSdk = initiateSmartContractPlatformClient({
  apiKey: process.env.CIRCLE_API_KEY,
  entitySecret: process.env.CIRCLE_ENTITY_SECRET,
});

const contractResponse = await circleContractSdk.getContract({
  id: process.env.CONTRACT_ID!,
});

console.log(JSON.stringify(contractResponse.data, null, 2));
```

Add script and run:

```bash
npm pkg set scripts.get-contract="tsx --env-file=.env get-contract.ts"
npm run get-contract
```

You can view deployed contracts in:

- Circle Developer Console: https://console.circle.com/smart-contracts/contracts
- Arc Testnet Explorer: https://testnet.arcscan.app/

## Template IDs from the Arc tutorial

| Template | Template ID | Suggested builder use |
| --- | --- | --- |
| ERC-20 | `a1b74add-23e0-4712-88d1-6b3009e85a86` | programmable money, demo credits, settlement tokens |
| ERC-721 | `76b83278-50e2-4006-8b63-5b1a2a814533` | identity, certificates, unique rights, agent receipts |
| ERC-1155 | `aea21da6-0aa2-4971-9a1a-5098842b1248` | multi-asset instruments, tiers, batch-like products |
| Airdrop | `13e322f2-18dc-4f57-8eed-4bddfc50f85e` | programmatic distributions, stakeholder/creator payouts |

## How this maps to Arc MCP Builder Assistant

Good next demos:

1. **Agent receipt NFT** — ERC-721 receipt for an agent-approved task.
2. **Creator payout airdrop** — Airdrop template for contributor payouts.
3. **Agent payment credit** — ERC-20 test token representing prepaid API/agent credits.
4. **Multi-tier agent access** — ERC-1155 tiers for API or service access.

For the current repo, the lowest-risk next step is still the human-approved **payment intent** flow. Contract deployment notes are the second layer: once the payment intent flow is clear, use templates for receipts, payouts, or programmable demo assets.

## AI prompt for this page

```text
Use Arc MCP docs and the deploy-contracts tutorial to create a safe implementation checklist for deploying an ERC-20 template on Arc Testnet with Circle Contracts. Include prerequisites, env vars, scripts, verification steps, and security warnings. Do not include real credentials.
```
