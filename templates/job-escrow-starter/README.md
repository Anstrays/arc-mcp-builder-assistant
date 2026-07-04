# Arc Job Escrow Starter

Minimal static ERC-8183-style job escrow UI for Arc Testnet. User posts a job, agent accepts, user funds, agent submits work, user approves release.

This is a starter template from the Arc MCP Builder Assistant. It is wallet-free and does not sign or broadcast anything.

## Files

- `index.html` — job escrow simulator UI.

## Use

Open `index.html` in a browser or serve it locally:

```bash
python3 -m http.server 8092
```

Then open http://localhost:8092/.

## Safety notes

- No private keys or funds move in this starter.
- Status transitions are local and require explicit user clicks.
- Production handoff requires a reviewed smart-contract escrow on Arc Testnet.
