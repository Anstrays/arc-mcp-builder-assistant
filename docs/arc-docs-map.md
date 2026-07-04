# Arc Docs Map for Builders

> Practical map of the official `docs.arc.network/arc/` surface for Arc builders exploring stablecoin payments, AI agents, and agentic commerce prototypes.

This is an independent builder note. Always verify against the latest official Arc docs before deploying or funding anything.

## Source pages reviewed

The `/arc/` docs surface currently covers four main buckets:

- **Concepts** — architecture, consensus, execution, finality, fees, privacy roadmap, post-quantum security, and running nodes.
- **References** — connect to Arc, contract addresses, EVM compatibility, gas/fees, node requirements, sample applications.
- **Tools** — account abstraction, compliance vendors, indexers, node providers, oracles.
- **Tutorials / quickstarts** — deploy contracts, interact with contracts, monitor events, transfer stablecoins, access crosschain USDC, register AI agents, create ERC-8183 jobs, and run/monitor nodes.

## Arc Testnet essentials

| Item | Value |
| --- | --- |
| Network name | Arc Testnet |
| RPC URL | `https://rpc.testnet.arc.network` |
| WebSocket | `wss://rpc.testnet.arc.network` |
| Chain ID | `5042002` |
| Currency symbol | `USDC` |
| Explorer | `https://testnet.arcscan.app` |
| Gas tracker | `https://testnet.arcscan.app/gas-tracker` |
| Testnet base fee guidance | minimum `20 Gwei` |
| Public native gas asset | USDC |

Arc uses USDC as the native gas token. Native gas accounting uses 18 decimals, while the optional ERC-20 USDC interface uses 6 decimals.

## Why Arc is interesting for payment and agent apps

### Stablecoin-native UX

Arc is designed around stablecoin finance rather than volatile native gas. For builders, this makes payment UX easier to explain:

- fees are denominated in USDC;
- apps can estimate cost in dollar terms;
- payment receipts can show asset, amount, fee, and final settlement status in one familiar unit.

### Deterministic finality

Arc docs position finality as deterministic and sub-second. Once a block is committed, included transactions are final. This matters for:

- checkout/payment confirmation UX;
- escrow release flows;
- agent job settlement;
- treasury movements;
- event-driven backends that should not wait for probabilistic confirmations.

### EVM compatibility

Arc is EVM-compatible and built around familiar Ethereum tooling such as Solidity, Foundry, Hardhat, `cast`, `viem`, and wallet/RPC patterns. The main differences to remember:

- gas and balances are denominated in USDC, not ETH;
- finality is deterministic;
- gas pricing is smoothed for predictable costs;
- native USDC has 18-decimal gas accounting while ERC-20 interfaces can expose 6 decimals.

## Core contract addresses

### Stablecoins

| Asset | Address | Notes |
| --- | --- | --- |
| USDC | `0x3600000000000000000000000000000000000000` | Native USDC optional ERC-20 interface; 6 decimals for ERC-20 interface. |
| EURC | `0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a` | Euro-denominated stablecoin on Arc. |
| USYC | `0xe9185F0c5F296Ed1797AaE4238D26CCaBEadb86C` | Yield-bearing token for institutional use; allowlisting may apply. |

### CCTP / crosschain components

| Component | Address |
| --- | --- |
| TokenMessengerV2 | `0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA` |
| MessageTransmitterV2 | `0xE737e5cEBEEBa77EFE34D4aa090756590b1CE275` |
| TokenMinterV2 | `0xb43db544E2c27092c107639Ad201b3dEfAbcF192` |
| MessageV2 | `0xbaC0179bB358A8936169a63408C8481D582390C4` |

### Gateway

| Component | Address |
| --- | --- |
| GatewayWallet | `0x0077777d7EBA4688BDeF3E311b846F25870A19B9` |
| GatewayMinter | `0x0022222ABE238Cc2C7Bb1f21003F0a260052475B` |

### Useful infra contracts

| Component | Address | Notes |
| --- | --- | --- |
| FxEscrow | `0x867650F5eAe8df91445971f14d89fd84F0C9a9f8` | Escrow used for stablecoin swaps. |
| Memo | `0x9702466268ccF55eAB64cdf484d272Ac08d3b75b` | Attach memo metadata to calls. |
| Multicall3From | `0xEb7cc06E3D3b5F9F9a5fA2B31B477ff72bB9c8b6` | Batches calls while preserving original `msg.sender`. |
| CREATE2 Factory | `0x4e59b44847b379578588920cA78FbF26c0B4956C` | Deterministic deployment. |
| Multicall3 | `0xcA11bde05977b3631167028862bE2a173976CA11` | Aggregate read calls. |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | Required for StableFX flows. |

## AI agent and agentic commerce primitives

### ERC-8004 agent identity

Arc docs include a quickstart for registering an AI agent using ERC-8004 on Arc Testnet.

| Registry | Address |
| --- | --- |
| IdentityRegistry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| ReputationRegistry | `0x8004B663056A597Dffe9eCcC1965A193B7388713` |
| ValidationRegistry | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` |

Builder use cases:

- register an AI agent with an onchain identity;
- record reputation events;
- verify credentials;
- connect identity to payment requests and job settlement.

### ERC-8183 job / escrow flow

Arc docs include an ERC-8183 job quickstart for agentic commerce flows.

| Component | Address |
| --- | --- |
| AgenticCommerce reference implementation | `0x0747EEf0706327138c69792bF28Cd525089e4583` |

Documented flow:

1. Create developer-controlled smart contract account wallets.
2. Create a job.
3. Fund escrow with USDC.
4. Submit a deliverable hash.
5. Complete the job as evaluator.
6. Settle funds.

Builder use cases:

- agent-to-agent paid tasks;
- freelance / microservice escrow;
- verifiable deliverable hash;
- reputation-based agent marketplace.

## Practical tutorials to build from

### Deploy on Arc with Foundry

Core setup:

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
forge init hello-arc && cd hello-arc
```

Environment:

```bash
ARC_TESTNET_RPC_URL="https://rpc.testnet.arc.network"
```

Create or import a disposable Arc Testnet account into Foundry's encrypted
keystore using its interactive hidden prompts. Never put a raw private key in
an environment variable, command history, repository file, issue, or AI chat.

```bash
cast wallet import arc-testnet-review
```

Deploy example:

```bash
forge create src/HelloArchitect.sol:HelloArchitect \
  --rpc-url $ARC_TESTNET_RPC_URL \
  --account arc-testnet-review \
  --broadcast
```

Read example:

```bash
cast call $HELLOARCHITECT_ADDRESS "getGreeting()(string)" \
  --rpc-url $ARC_TESTNET_RPC_URL
```

Use this path for a minimal custom contract such as `HelloArcPaymentIntent`.

### Deploy contracts with Circle Contracts

Prerequisites:

- Node.js v22+
- Circle Developer account
- Circle API key
- Entity Secret
- Arc Testnet wallet

Packages:

```bash
npm install @circle-fin/developer-controlled-wallets @circle-fin/smart-contract-platform
```

Useful scripts from the Arc tutorial path:

```bash
npm run create-wallet
npm run deploy-erc20
npm run check-transaction
```

Contract templates:

| Template | ID |
| --- | --- |
| ERC-20 | `a1b74add-23e0-4712-88d1-6b3009e85a86` |
| ERC-721 | `76b83278-50e2-4006-8b63-5b1a2a814533` |
| ERC-1155 | `aea21da6-0aa2-4971-9a1a-5098842b1248` |
| Airdrop | `13e322f2-18dc-4f57-8eed-4bddfc50f85e` |

Use this path for receipt NFTs, access tokens, credits, or payout distribution demos.

### Transfer USDC or EURC

The stablecoin transfer quickstart uses Circle App Kit and Viem.

Packages:

```bash
npm install @circle-fin/app-kit @circle-fin/adapter-viem-v2 viem typescript tsx
```

Run pattern:

```bash
npx tsx --env-file=.env index.ts
```

Use this as the first real transaction flow for a payment-intent demo.

### Monitor contract events

Arc docs include a flow for monitoring onchain contract events and receiving webhook updates.

Tools mentioned:

- webhook.site
- ngrok
- Circle monitoring
- `ARC-TESTNET`

Script patterns:

```bash
npm pkg set scripts.webhook="tsx webhook-receiver.ts"
npm pkg set scripts.import-contract="tsx --env-file=.env import-contract.ts"
npm pkg set scripts.create-monitor="tsx --env-file=.env create-monitor.ts"
npm pkg set scripts.get-event-logs="tsx --env-file=.env get-event-logs.ts"
```

Use this for real-time payment status updates: `draft -> pending approval -> submitted -> paid -> failed`.

### Access USDC crosschain / Unified Balance

The crosschain docs show Gateway/App Kit style flows across Base Sepolia, Arc Testnet, and Solana Devnet.

Packages:

```bash
npm install @circle-fin/app-kit @circle-fin/adapter-viem-v2 @circle-fin/adapter-solana viem @solana/web3.js
```

Run patterns:

```bash
npx tsx --env-file=.env deposit-base.ts
npx tsx --env-file=.env deposit-solana.ts
npx tsx --env-file=.env check-balance.ts
npx tsx --env-file=.env spend.ts
```

This is a later-stage feature for multichain funding and Arc-first spending.

## Tools and providers mentioned in Arc docs

### Account abstraction

- Biconomy
- Blockradar
- Circle Wallets
- Crossmint
- Dynamic
- Para
- Pimlico
- Privy
- Thirdweb
- Turnkey
- Zerodev

### Compliance

- Elliptic
- TRM Labs

### Indexers

- Goldsky
- Ponder
- Subsquid
- The Graph
- Thirdweb

### Node providers

| Provider / endpoint | URL |
| --- | --- |
| Arc public RPC | `https://rpc.testnet.arc.network` |
| Arc public WebSocket | `wss://rpc.testnet.arc.network` |
| dRPC | `https://rpc.drpc.testnet.arc.network` |
| QuickNode | `https://rpc.quicknode.testnet.arc.network` |
| Blockdaemon | `https://rpc.blockdaemon.testnet.arc.network` |

### Oracles

- Chainlink
- Pyth
- RedStone
- Stork

## Node operations notes

Running a node is useful for independent verification and low-latency access, but it is not required for the first MVP.

Minimum-style requirements surfaced in docs:

- Linux: Ubuntu 22.04+ or Debian 12+
- 64 GB+ memory
- 1 TB+ NVMe SSD
- 24 Mbps+ stable bandwidth

Local node RPC:

```text
http://localhost:8545
```

Metrics endpoints:

```text
Execution Layer: http://localhost:9001/metrics
Consensus Layer: http://localhost:29000/metrics
```

## Recommended builder roadmap for this repo

### Phase A — Docs map and prompt kit

- Keep `docs/arc-mcp-setup.md` as the MCP entrypoint.
- Use this map as the high-level Arc builder surface.
- Maintain prompt files for payments, deploys, and agent flows.

### Phase B — Payment Intent Demo v1

Implement a local app that can:

- create a payment intent;
- set recipient, amount, asset, memo, and expiration;
- show estimated USDC fee;
- keep human approval explicit;
- record tx hash manually or from wallet flow;
- display final status.

### Phase C — Arc Testnet stablecoin transfer

Connect the demo to Arc Testnet with a safe transfer flow:

- use testnet wallets only;
- use testnet USDC/EURC only;
- keep private keys out of frontend code;
- store no secrets in repo;
- verify tx status on ArcScan.

### Phase D — Event monitoring

Add event/webhook monitoring for real payment status updates.

### Phase E — Agent identity

Add ERC-8004 agent registration notes and a minimal agent profile card.

### Phase F — ERC-8183 job escrow

Add an agent job escrow demo:

- create job;
- fund USDC escrow;
- submit deliverable hash;
- evaluator completes job;
- show settlement.

## Best public positioning

Short version:

```text
Independent Arc builder resource mapping Arc MCP/docs into practical AI-assisted workflows for stablecoin payments, agent identity, and agentic commerce prototypes.
```

Arc House / community version:

```text
I mapped the Arc docs surface around stablecoin payments, USDC-native gas, deterministic finality, Circle tooling, ERC-8004 agent identity, ERC-8183 job escrow, and contract event monitoring. The goal is to turn this into a practical payment-intent and agent-commerce prototype while keeping the docs/prompt layer reusable for other builders.
```
