# Arc x402 Paid-Agent Starter

Minimal local x402-style paid-agent boundary for Arc Testnet. It returns a `402 Payment Required` challenge and accepts a deterministic local demo proof.

This is a starter template from the Arc MCP Builder Assistant. No funds move; no wallet or signing is required.

## Files

- `server.py` — dependency-free Python HTTP server.

## Use

```bash
python3 server.py --port 8091
```

In another terminal:

```bash
curl -s http://127.0.0.1:8091/protected
python3 server.py --print-manifest
python3 server.py --print-challenge
```

## Safety notes

- `X402_DEMO_MAINNET_ENABLED` must stay `false`; any `true` value exits safely.
- Asset is pinned to `USDC` and network to `arc-testnet`.
- The `local-demo` proof is a deterministic demo switch, not a real payment credential.
