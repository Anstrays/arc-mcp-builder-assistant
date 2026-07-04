# Arc Agent Marketplace Starter

Minimal agent-to-agent marketplace demo on Arc Testnet. A buyer agent lists a payment intent, a seller agent discovers it and fulfills the order.

This is a starter template from the Arc MCP Builder Assistant. No funds move; no wallet or signing is required.

## Files

- `server.py` — dependency-free Python HTTP server with buyer/seller endpoints.

## Use

```bash
python3 server.py --port 8092
```

In another terminal:

```bash
# List open intents
curl -s http://127.0.0.1:8092/intents

# Submit a fulfillment
curl -s -X POST http://127.0.0.1:8092/fulfill \
  -H "Content-Type: application/json" \
  -d '{"intentId": "demo-1", "seller": "0x...", "proof": "local-demo"}'
```

## Safety notes

- All intents are local mock values pinned to Arc Testnet/USDC semantics.
- No private keys, seed phrases, or API keys are stored or requested.
- The `local-demo` proof is a deterministic demo switch, not a real payment credential.
- Production handoff requires a separate reviewed integration with Circle Gateway or an injected wallet.
