# Arc Agent Treasury Starter

Minimal agent treasury management UI on Arc Testnet. View USDC balance, prepare send intents, and track payment history.

This is a starter template from the Arc MCP Builder Assistant. No funds move; no wallet or signing is required.

## Files

- `index.html` — treasury dashboard UI with balance display and send intent form.

## Use

Open `index.html` in a browser or serve it locally:

```bash
python3 -m http.server 8093
```

Then open http://localhost:8093/ in a browser.

## Safety notes

- All amounts and intents are local mock values pinned to Arc Testnet/USDC semantics.
- No private keys, seed phrases, or API keys are stored or requested.
- The send form prepares a human-reviewable intent — it does NOT broadcast a transaction.
- Production handoff requires a separate reviewed integration with Circle Gateway or an injected wallet.
