# Arc paid API endpoint prototype

`examples/arc-paid-api-endpoint/server.py` is the first production-shaped paid API endpoint prototype for the Arc Builder Kit. It keeps the repo safe while moving beyond local demo proof strings: clients receive a `402 Payment Required` challenge, a human performs the Arc Testnet USDC payment, and the server verifies the supplied transaction hash with read-only receipt checks before returning the protected resource.

## What it proves

- A real API endpoint can advertise Arc Testnet USDC payment terms in an x402-shaped challenge.
- The protected resource stays locked until a human supplies an Arc Testnet transaction hash in `X-Payment`.
- Verification uses read-only RPC receipt evidence, not a local magic proof.
- The endpoint remains testnet-only and fail-closed for mainnet, private-key, signing, and broadcast paths.

## Run locally

```bash
python3 examples/arc-paid-api-endpoint/server.py --port 8098
curl -i http://127.0.0.1:8098/protected
```

Inspect the machine-readable manifest without starting HTTP:

```bash
python3 examples/arc-paid-api-endpoint/server.py --print-manifest
python3 examples/arc-paid-api-endpoint/server.py --print-challenge
```

The challenge response tells the operator exactly what to review: network, asset, amount, `payTo`, resource, and safety flags. After a human sends the Arc Testnet USDC payment from their own wallet, retry with the transaction hash:

```bash
curl -i \
  -H 'X-Payment: 0x<arc-testnet-transaction-hash>' \
  http://127.0.0.1:8098/protected
```

If the receipt contains a matching pinned-USDC `Transfer` to the reviewed recipient on Arc Testnet, the endpoint returns the protected JSON. If the transaction is missing, wrong-chain, wrong-recipient, reverted, malformed, or unverified, it returns another `402` and keeps `settled: false`.

## Safety contract

| Property | Value |
| --- | --- |
| Network | Arc Testnet only (`5042002 / 0x4cef52`) |
| Payment asset | USDC, 6 decimals |
| Approval | Human-reviewed transaction hash only |
| RPC | Read-only `eth_getTransactionReceipt` / `eth_getTransactionByHash` via `arc_builder_kit.x402_client` |
| Private keys | Forbidden |
| Signing | Not implemented |
| Broadcast | Not implemented |
| Mainnet | Disabled and fail-closed |
| HTTP bind | `127.0.0.1` / `localhost` only by default |

Forbidden environment inputs include `ARC_PAID_API_PRIVATE_KEY`, `PRIVATE_KEY`, `WALLET_PRIVATE_KEY`, `MNEMONIC`, and `SEED_PHRASE`. The endpoint exits instead of accepting those values.

## Configuration

| Variable | Default | Constraint |
| --- | --- | --- |
| `ARC_PAID_API_AMOUNT` | `0.01` | Positive USDC amount, max 6 decimals |
| `ARC_PAID_API_PAY_TO` | `0xA11CE00000000000000000000000000000000000` | Non-zero EVM address |
| `ARC_PAID_API_RPC_URL` | `https://rpc.testnet.arc.network` | HTTPS or localhost for tests |
| `ARC_PAID_API_NETWORK` | `arc-testnet` | Must not change |
| `ARC_PAID_API_ASSET` | `USDC` | Must not change |
| `ARC_PAID_API_MAINNET_ENABLED` | `false` | Must remain false |

## What it does not prove yet

- It does not submit payments.
- It does not prove wallet UX or signing flows.
- It does not include nonce/replay storage or production rate limits.
- It does not integrate Circle Gateway or a production x402 verifier.

Those belong in later phases after this local read-only paid API boundary is reviewed.
