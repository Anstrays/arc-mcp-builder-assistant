# Arc x402 Verified API Starter

A paid API endpoint that returns `402 Payment Required` and verifies on-chain USDC payments on Arc Testnet before serving the protected resource.

This is a starter template from the Arc MCP Builder Assistant. It verifies real Arc Testnet transactions via read-only RPC. No wallet or signing is required.

## Files

- `server.py` — dependency-free Python HTTP server with x402-style payment verification.

## Use

```bash
python3 server.py --port 8094
```

In another terminal:

```bash
# Without payment — returns 402 challenge
curl -sv http://127.0.0.1:8094/protected 2>&1 | grep -E "HTTP/|{"

# With a real Arc Testnet USDC tx hash
curl -sv -H "X-Payment: 0x<txhash>" http://127.0.0.1:8094/protected 2>&1
```

The protected endpoint only returns content after verifying a valid USDC Transfer event on-chain.

## Safety notes

- Only accepts `arc-testnet` network (chain ID 5042002).
- `PAY_TO` address must be an honest statement — verify it against your own records before each run.
- Mainnet is fail-closed: passing a mainnet chain ID or payment proof rejects immediately.
- Asset is pinned to `USDC` on Arc Testnet.
- The server makes read-only RPC calls (`eth_getTransactionReceipt`) — no private keys, no broadcast.
