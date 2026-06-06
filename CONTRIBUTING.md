# Contributing

Arc MCP Builder Assistant is a dependency-free, local-first builder kit.
Contributions should make Arc stablecoin and agent-infrastructure workflows
easier to understand, reproduce, review, or extend without weakening the
safety boundary.

## Local setup

```bash
git clone https://github.com/Anstrays/arc-mcp-builder-assistant.git
cd arc-mcp-builder-assistant
python scripts/test_all.py
python -m http.server 8080
```

Open `http://localhost:8080/`. No npm install, wallet, database, or secret is
required.

## Useful contributions

- corrections to Arc MCP setup notes;
- verified Arc docs links;
- prompt improvements;
- testnet integration notes;
- payment-intent demo improvements;
- docs for agent identity / ERC-8004 flows.

## Pull request checklist

- Keep the change Arc-focused and small enough to review.
- Add or update a dependency-free regression test for changed behavior.
- Update public docs when a command, config value, example, or claim changes.
- Run `python scripts/check_completion.py` and `python scripts/test_all.py`.
- Verify the affected local page or example in a browser.
- State what was verified, what remains unknown, and any safety impact.

## Rules

- Keep claims honest and sourced.
- Do not paste secrets or private wallet material.
- Do not imply official Arc endorsement.
- Mark unknowns instead of inventing details.
- Do not add mainnet, signing, custody, autonomous spending, or transaction
  broadcast as a casual extension. Those require a separately reviewed,
  guarded proposal.

See [`docs/completion-contract.md`](./docs/completion-contract.md) for the
current definition of complete and [`SECURITY.md`](./SECURITY.md) for private
reporting guidance.
