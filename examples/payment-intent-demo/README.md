# Arc Payment Intent Demo — Circle Wallet Integration

Интерактивная демка где AI-агент создаёт USDC payment request, а backend показывает **реальный баланс Circle wallet**, **оценку газа** и **историю транзакций** на Arc Testnet.

## Quick Start

```bash
# 1. Убедись что Circle CLI установлен и залогинен
circle wallet status --testnet

# 2. Запусти сервер
python3 server.py

# 3. Открой http://localhost:8080
```

## Что видно на странице

1. **👛 Wallet Card** — реальный адрес кошелька, баланс USDC (native + ERC-20), последние 5 транзакций
2. **📝 Create Intent** — форма создания payment request
3. **📋 Payment Intents** — список интентов с кнопками "Estimate Fee" (газ) и (опционально) "Send Real USDC"
4. **📡 Live Data** — Arc Testnet информация

## Режимы работы

| Режим | Описание | Включение |
|-------|----------|-----------|
| 🟡 **Estimate only** (default) | Оценка газа через `--estimate`, никаких реальных транзакций | `REAL_TRANSFER=0` |
| 🔴 **Real transfers** | Реальные USDC transfers на Arc Testnet | `REAL_TRANSFER=1` |

## API

Сервер предоставляет REST API на stdlib (без зависимостей):

- `GET /api/wallet` — баланс + транзакции из Circle CLI
- `POST /api/intent` — создать intent (авто-эстимейт)
- `POST /api/approve` — эстимейт или реальный transfer
- `GET /api/estimate?to=0x...&amount=1` — dry-run эстимейт

## Env vars

| Variable | Default | |
|----------|---------|-|
| `CIRCLE_WALLET_ADDR` | `0x0cd9...ea401` | Адрес кошелька |
| `CIRCLE_CHAIN` | `ARC-TESTNET` | Blockchain |
| `CIRCLE_RPC_URL` | `https://rpc.testnet.arc.network` | RPC |
| `REAL_TRANSFER` | `0` | `1` = разрешить реальные переводы |

## Prerequisites

- Python 3.10+
- Circle CLI: `npm install -g @circle-fin/cli`
- Agent wallet на Arc Testnet с USDC
