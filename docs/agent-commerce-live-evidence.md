# Agent commerce live evidence

This page documents the first real agent-commerce transactions on Arc Testnet using a Circle agent wallet. All transactions are testnet-only, human-approved, and use faucet-funded USDC with no real value.

## Wallet

| Field | Value |
|---|---|
| Address | `0x0cd9b933302d90bfe295471deac7f4eafd9ea401` |
| Type | Circle agent wallet (SCA) |
| Chain | Arc Testnet (chain ID 5042002 / 0x4cef52) |
| Session | Testnet (OTP-authenticated) |
| Funding | Circle faucet (20 USDC native + 20 USDC ERC-20) |

## Transaction log

All transactions are verifiable on [Arc Testnet Explorer](https://testnet.arcscan.app).

### 1. Faucet funding

| Field | Value |
|---|---|
| Operation | TRANSFER |
| Amount | 20 USDC (native + ERC-20) |
| Block | 48020204 |
| Status | COMPLETE |

### 2. Self-transfer (wallet deployment test)

| Field | Value |
|---|---|
| Tx hash | `0xb570a204eb4d81d3610694cce5e33d647312924ef7e1448e01ce8f42fa733dd1` |
| Operation | TRANSFER |
| Amount | 1 USDC |
| Block | 48020319 |
| Network fee | 0.0076 USDC (native) |
| Status | COMPLETE |

### 3. CCTP bridge — Arc Testnet → Base Sepolia

| Field | Value |
|---|---|
| Approve tx | `0x044184a5ce5760a27693a6b2d48a1d21c2272a9174b913e630dd1aaa6c4b273b` |
| Burn tx | `0x7855802e76412ee50a7f7ffe445ae291fade450914103154277960974b623f15` |
| Forward tx | `0xd704d32f0c903f4d62dec509cb3e50aa9af43e49de3b10ac129b8b9c9b94297e` |
| Amount | 1 USDC |
| Route | Arc Testnet → Base Sepolia (CCTP domain 26 → domain 6) |
| Status | COMPLETE |

### 4. Agent payment — paid API simulation

| Field | Value |
|---|---|
| Tx hash | `0x490df63904f7722c369a76bc656f8d59f2223846274b52e41b626e187ee13aa8` |
| Operation | TRANSFER |
| From | `0x0cd9b933302d90bfe295471deac7f4eafd9ea401` |
| To | `0x000000000000000000000000000000000000dEaD` (burn address) |
| Amount | 0.5 USDC |
| Block | 48027390 |
| Network fee | 0.0036 USDC (native) |
| Status | COMPLETE |
| Simulation | Agent pays 0.5 USDC for a paid API call response |

### 5. Agent payment — micro-payment simulation

| Field | Value |
|---|---|
| Tx hash | `0xda2ed5d09c781cbf5c475e4d9fc697e479c35b6e5cef866ab4dd78d86f247fca` |
| Operation | TRANSFER |
| From | `0x0cd9b933302d90bfe295471deac7f4eafd9ea401` |
| To | `0x000000000000000000000000000000000000dEaD` (burn address) |
| Amount | 0.25 USDC |
| Block | 48027419 |
| Network fee | 0.0039 USDC (native) |
| Status | COMPLETE |
| Simulation | Agent pays 0.25 USDC for a micro-service call |

## On-chain verification

The USDC ERC-20 balance can be verified directly from the contract:

```bash
# Query USDC balance on-chain (read-only)
circle contract query "balanceOf(address)" 0x0cd9b933302d90bfe295471deac7f4eafd9ea401 \
  --contract 0x3600000000000000000000000000000000000000 \
  --chain "Arc Testnet" --output json
```

The USDC contract on Arc Testnet:
- Address: `0x3600000000000000000000000000000000000000`
- Decimals: 6 (ERC-20) / 18 (native gas)
- Name: USDC
- Symbol: USDC

## Gateway interaction

Arc is Gateway domain 26. The Gateway supports sub-500ms batched payments for x402 services.

```bash
# Check Gateway balance
circle gateway balance --address 0x0cd9b933302d90bfe295471deac7f4eafd9ea401 --chain "Arc Testnet"

# Deposit USDC into Gateway (direct, same-chain)
circle gateway deposit --amount 5 --address 0x0cd9b933302d90bfe295471deac7f4eafd9ea401 --chain "Arc Testnet" --method direct
```

## Unit economics

| Metric | Value |
|---|---|
| Starting balance | 20.00 USDC (ERC-20) |
| Total payments sent | 1.75 USDC (1 self + 0.5 API + 0.25 micro) |
| Total network fees | ~0.06 USDC (native) |
| Bridge amount | 1.00 USDC (to Base Sepolia) |
| Current balance | ~18.04 USDC (ERC-20) |
| Cost per payment | ~0.004 USDC network fee |
| Payments possible | ~4500+ (at current fee rate) |

## Safety boundaries

- **Testnet only** — faucet USDC has no real value
- **No private keys in repo** — Circle CLI manages keys internally
- **No custody** — Circle agent wallet is non-custodial SCA
- **No mainnet** — all transactions on Arc Testnet (chain ID 5042002)
- **No autonomous spending** — every transaction was human-approved
- **No secrets committed** — wallet address is public, no keys/tokens/OTP stored
- **Burn address** — payments sent to `0xdEaD` simulate service provider without funding a real counterparty
