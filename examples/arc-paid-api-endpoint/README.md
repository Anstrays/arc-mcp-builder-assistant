# Arc paid API endpoint prototype

Local Arc Testnet paid API boundary that models a production paid endpoint without custody or signing.

## Run

```bash
python3 examples/arc-paid-api-endpoint/server.py --port 8098
curl -i http://127.0.0.1:8098/protected
```

The first request returns `402 Payment Required` with an x402-shaped challenge. A human operator must review the challenge, send the Arc Testnet USDC payment themselves, and retry with the transaction hash:

```bash
curl -i \
  -H 'X-Payment: 0x<arc-testnet-transaction-hash>' \
  http://127.0.0.1:8098/protected
```

The server then performs read-only receipt verification through Arc Testnet RPC. It never accepts private keys, signs, broadcasts, switches chains, or touches mainnet.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `ARC_PAID_API_AMOUNT` | `0.01` | USDC amount, max 6 decimals. |
| `ARC_PAID_API_PAY_TO` | `0xA11CE00000000000000000000000000000000000` | Non-zero EVM recipient. |
| `ARC_PAID_API_RPC_URL` | `https://rpc.testnet.arc.network` | Read-only receipt lookup. |
| `ARC_PAID_API_NETWORK` | `arc-testnet` | Must stay Arc Testnet. |
| `ARC_PAID_API_MAINNET_ENABLED` | `false` | Must remain false. |

Forbidden inputs include `ARC_PAID_API_PRIVATE_KEY`, `PRIVATE_KEY`, `WALLET_PRIVATE_KEY`, `MNEMONIC`, and `SEED_PHRASE`.

## Safe scope

- testnet-only
- human approval required
- read-only receipt verification
- no private keys
- no signing
- no transaction broadcast
- no autonomous spending
- localhost-only HTTP bind by default
