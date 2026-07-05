# Payment Intent Demo Spec

## Thesis

A safe first version of agentic commerce is not a fully autonomous spending bot. It is an AI agent that can create a structured payment request, while a human user stays in control of approval — backed by a **real Circle agent wallet on Arc Testnet**.

## What's new (v2 — Circle Wallet Integration)

The demo now connects to a **real Circle agent wallet** via the Circle CLI:

| Что было (v1) | Что стало (v2) |
|---------------|----------------|
| Mock-баланс: "12.80 USDC" хардкодом | **Реальный баланс** через `circle wallet balance` |
| Аппров — заглушка "set CIRCLE_API_KEY" | **Реальная оценка газа** через `--estimate` |
| Нет tx history | **Реальные транзакции** из `circle transaction list` |
| Нет информации о кошельке | Адрес, chain, USDC token — live с CLI |
| — | Опционально: реальный USDC transfer при `REAL_TRANSFER=1` |

## User story

As a user, I want an AI agent to prepare a clear USDC payment request, see **the real balance and gas estimate** on my Circle wallet, and review before approving.

## MVP flow (v2)

1. User opens demo app.
2. Page loads **live wallet data** from Circle CLI:
   - Wallet address
   - USDC balance (native + ERC-20)
   - Recent transaction history
3. User creates a payment intent:
   - recipient, amount, asset, memo
   - **Auto-estimate**: backend calls `circle wallet transfer --estimate` — shows gas fee, base fee, priority fee
4. User reviews estimate in the intent card.
5. User clicks "Estimate Fee" → **real** gas quote from Circle.
6. (optional, `REAL_TRANSFER=1`) Click "Send Arc Testnet USDC" and type `SEND ARC TESTNET USDC` before the backend can request one transfer.

## Architecture

```
┌────────────┐     HTTP/JSON     ┌──────────────┐     subprocess     ┌────────────┐
│  index.html │ ◄──────────────► │  server.py   │ ◄────────────────► │ circle CLI │
│  (vanilla)  │                  │  (stdlib)    │                    │  (agent)   │
└────────────┘                  └──────────────┘                    └────────────┘
                                                                          │
                                                                    ┌──────┴──────┐
                                                                    │ Arc Testnet │
                                                                    │  (RPC)      │
                                                                    └─────────────┘
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/wallet` | Wallet address, USDC balance, recent transactions |
| `GET` | `/api/transactions` | Last 20 transactions from Circle |
| `GET` | `/api/estimate?to=ADDR&amount=N` | Dry-run gas estimate |
| `POST` | `/api/intent` | Create payment intent (auto-estimates) |
| `POST` | `/api/approve` | Estimate or execute transfer |
| `GET` | `/api/intents` | List all intents |
| `GET` | `/api/status/<id>` | Single intent status |
| `GET` | `/api/network` | Arc Testnet info |

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `CIRCLE_WALLET_ADDR` | `0x0cd9...ea401` | Circle agent wallet address |
| `CIRCLE_CHAIN` | `ARC-TESTNET` | Blockchain name |
| `CIRCLE_RPC_URL` | `https://rpc.testnet.arc.network` | RPC endpoint |
| `CIRCLE_USDC_TOKEN` | `0x3600...0000` | USDC ERC-20 token address |
| `REAL_TRANSFER` | `0` | Set to `1` to enable real USDC sends |
| `HOST`, `PORT` | `127.0.0.1:8080` | Local-only server bind; external binds are rejected |

## Prerequisites

1. **Circle CLI** installed: `npm install -g @circle-fin/cli`
2. **Logged in** as agent: `circle wallet login <email> --type agent`
3. **Wallet on Arc Testnet**: `circle wallet create --output json`
4. **Funded**: Use faucet or Gateway deposit

## Running

```bash
cd examples/payment-intent-demo/
python3 server.py
# → http://localhost:8080
```

## Non-goals for v2

- No autonomous spending without human approval.
- No mainnet funds (Arc Testnet only by default).
- No private key exposure (all via Circle CLI agent session).
- Real USDC transfer disabled by default (`REAL_TRANSFER=0`).

## Safety

- All transfers go through `--estimate` first (no cost).
- Real transfer requires `REAL_TRANSFER=1`, `real=true`, the exact `SEND ARC TESTNET USDC` confirmation phrase, an explicit click, a maximum amount of `1.00 USDC`, and one send attempt per intent.
- The backend rejects external bind addresses, wildcard CORS, oversized JSON bodies, non-USDC assets, invalid recipients, and non-Arc chain configuration.
- Circle agent wallet session expires after ~28 days; re-login with OTP.
- `circle wallet transfer` sends USDC via Circle's infrastructure — not raw private key signing.
