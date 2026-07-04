# Circle agent wallet integration

This page documents the Circle agent wallet integration for Arc Testnet. It covers the bootstrap flow (login, wallet creation, faucet funding), on-chain transactions (transfer, CCTP bridge), and the boundary between testnet demos and live x402 marketplace payments.

## Prerequisites

- Circle CLI (`@circle-fin/cli`) installed: `npm install -g @circle-fin/cli`
- Terms of Use accepted (one-time, interactive consent required)
- Email address for OTP login
- Arc Testnet chain ID: `5042002` / `0x4cef52`

## Bootstrap flow

### 1. Login (two-step OTP)

Circle CLI uses a two-step OTP flow designed for non-interactive agents:

```bash
# Mainnet session
circle wallet login <email> --type agent --init
# OTP sent to email
circle wallet login --type agent --request <request-id> --otp <code>

# Testnet session (separate)
circle wallet login <email> --type agent --testnet --init
circle wallet login --type agent --testnet --request <request-id> --otp <code>
```

Mainnet and testnet sessions are separate. Both require their own OTP.

### 2. Verify session

```bash
circle wallet status
circle wallet status --testnet
```

Sessions are valid for ~28 days.

### 3. Create agent wallet

```bash
circle wallet create --output json
```

Creates Circle-managed SCA (Smart Contract Account) wallets on all supported chains, including Arc Testnet.

## Developer-Controlled Wallet SDK guard

Circle's Developer-Controlled Wallet SDK can create a wallet set and then create EOA or SCA wallets on `ARC-TESTNET`. The official SDK path requires `CIRCLE_API_KEY` and `CIRCLE_ENTITY_SECRET`, so the builder kit does **not** run it automatically and does **not** store either secret. Instead, `arc-builder wallet` emits a reviewed plan, a redacted environment check, and a copy-paste SDK snippet for a human-controlled local shell.

```bash
# Review the exact Arc Testnet SDK plan. No SDK calls are made.
arc-builder wallet sdk-plan --json --account-type SCA --count 1

# Check whether required env vars are present without printing values.
arc-builder wallet env-check --json

# Print a secret-safe Python snippet for manual execution after review.
arc-builder wallet sdk-snippet --account-type EOA --count 1
```

The guarded plan pins:

- Python package: `circle-developer-controlled-wallets`
- TypeScript package: `@circle-fin/developer-controlled-wallets`
- blockchain: `ARC-TESTNET`
- supported account types: `EOA` and `SCA`
- required local env vars: `CIRCLE_API_KEY`, `CIRCLE_ENTITY_SECRET`
- safety: no live SDK execution from the repo command, no private keys, no raw signing, no transaction broadcast, no mainnet

A reviewed manual SDK run should still be treated as a sensitive external side effect: export secrets only in a private shell/secret manager, verify `blockchains` is exactly `["ARC-TESTNET"]`, and record wallet IDs/addresses without committing secrets.

### 4. Fund via faucet (testnet only)

```bash
circle wallet fund --address <addr> --chain "Arc Testnet" --token usdc
```

The Arc Testnet faucet drips both:
- **USDC native** (18 decimals) — used for gas
- **USDC ERC-20** (6 decimals, `0x3600000000000000000000000000000000000000`) — used for payments

### 5. Check balance

```bash
circle wallet balance --address <addr> --chain "Arc Testnet" --output json
```

## On-chain operations on Arc Testnet

### Transfer USDC

```bash
circle wallet transfer <to-address> --amount 1 --address <addr> --chain "Arc Testnet" --output json
```

### Bridge USDC via CCTP

```bash
# Arc Testnet -> Base Sepolia
circle bridge transfer "Base Sepolia" --amount 1 --address <addr> --chain "Arc Testnet" --output json
```

CCTP bridge burns USDC on the source chain and mints on the destination. Circle's Forwarding Service handles the destination mint — no gas needed on the destination chain.

### Transaction history

```bash
circle transaction list --address <addr> --chain "Arc Testnet" --output json
```

## Gateway (Nanopayments)

Circle Gateway supports Arc as domain 26. Gateway enables sub-500ms batched payments for x402 services.

```bash
# Check Gateway balance
circle gateway balance --address <addr> --chain "Arc Testnet" --output json

# Deposit on-chain USDC into Gateway
circle gateway deposit --amount 5 --address <addr> --chain "Arc Testnet" --method direct
```

## x402 marketplace

The Circle x402 marketplace (`circle services search`) lists paid HTTP endpoints that charge per-call USDC micropayments. Current marketplace services run on mainnet chains (Base, Ethereum, Polygon, etc.).

Arc Testnet is not yet listed as an accepted chain by marketplace sellers. To pay for a real x402 service:

1. Bridge testnet USDC to a mainnet chain (requires mainnet USDC, not testnet)
2. Or wait for marketplace sellers to accept Arc Testnet
3. Or build your own x402-compatible endpoint on Arc Testnet

## Arc Testnet contract addresses (Circle)

| Contract | Address | Category |
|---|---|---|
| USDC | `0x3600000000000000000000000000000000000000` | usdc |
| EURC | `0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a` | eurc |
| TokenMessengerV2 | `0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA` | cctp |
| MessageTransmitterV2 | `0xE737e5cEBEEBa77EFE34D4aa090756590b1CE275` | cctp |
| TokenMinterV2 | `0xb43db544E2c27092c107639Ad201b3dEfAbcF192` | cctp |
| GatewayWallet | `0x0077777d7EBA4688BDeF3E311b846F25870A19B9` | gateway |
| GatewayMinter | `0x0022222ABE238Cc2C7Bb1f21003F0a260052475B` | gateway |

## Safety boundaries

- The Circle CLI manages keys internally — no private keys in the repo
- Testnet sessions are separate from mainnet sessions
- Faucet USDC has no real value — testnet only
- x402 marketplace payments require mainnet USDC on an accepted chain
- Gateway deposits move on-chain USDC into an off-chain balance — irreversible without a withdraw
- Spending policy (limits) is mainnet-only and OTP-gated

## CLI reference

```bash
circle --help                    # top-level commands
circle wallet --help             # wallet verbs
circle bridge --help             # bridge verbs
circle services --help           # x402 marketplace
circle gateway --help            # Gateway / nanopayments
circle contract --help           # contract queries
circle blockchain list --output json  # supported chains
```
