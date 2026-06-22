# Arc Payment Intent Starter

Minimal static demo: an AI agent prepares a USDC payment intent on Arc Testnet and a human reviews/approves it.

This is a starter template from the Arc MCP Builder Assistant. It is wallet-free and does not sign or broadcast anything.

## Files

- `index.html` — reviewable payment-intent UI.

## Use

Open `index.html` in a browser or serve it locally:

```bash
python3 -m http.server 8090
```

Then open http://localhost:8090/.

## Safety notes

- No private keys, seed phrases, or API keys are stored or requested.
- Amounts are local mock values pinned to Arc Testnet/USDC semantics.
- Production handoff requires a separate reviewed integration with Circle Gateway or an injected wallet.
