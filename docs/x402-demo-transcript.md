# x402 local demo transcript

This page is a copy-paste walkthrough for the local paid-agent boundary. It shows the full `402 -> local proof -> protected response` loop without a wallet, private key, backend settlement, or transaction broadcast.

Use it after reading the [x402 MCP manifest](./x402-mcp-manifest.md) and before attempting any real Circle Gateway or x402 verifier integration.

## Safety scope

- **Local only:** run the dependency-free demo server on `127.0.0.1`.
- **No funds move:** the proof is a deterministic `local-demo:` string, not a signature or payment.
- **No private keys:** never paste wallet seeds, private keys, API keys, entity secrets, or production verifier credentials into this repo or an AI tool.
- **No transaction broadcast:** accepted responses keep `settled: false` and `transactionBroadcast: false`.
- **Human approval stays required:** this transcript models the review boundary before any future signing step.

## 1. Start the local 402 challenge server

```bash
python3 examples/x402-local-challenge-server/server.py --port 8087
```

Expected console line:

```text
local x402 challenge server listening on http://127.0.0.1:8087
GET /protected returns a 402 challenge. No funds move in this demo.
```

## 2. Inspect the challenge

In another shell:

```bash
curl -i http://127.0.0.1:8087/protected
```

Expected properties:

- HTTP status: `402 Payment Required`.
- `error`: `payment_required`.
- `x402Version`: `demo-boundary-v1`.
- `accepts[0].network`: `arc-testnet`.
- `accepts[0].asset`: `USDC`.
- `humanApprovalRequired`: `true`.
- `transactionBroadcast`: `false`.
- `mcpManifest.safety.localDemoProofOnly`: `true`.

## 3. Generate the local demo proof

The CLI helper prints the same challenge plus a proof hint:

```bash
python3 examples/x402-local-challenge-server/server.py --print-challenge
```

Look for:

```json
{
  "localDemoProof": "local-demo:arc-mcp-builder-assistant.local-report.v1:arc-testnet:USDC:0.01:0.01"
}
```

That string is intentionally only a local switch. It does not prove settlement, ownership, or signature validity.

## 4. Request the protected resource with the local proof

```bash
PROOF="local-demo:arc-mcp-builder-assistant.local-report.v1:arc-testnet:USDC:0.01:0.01"
curl -s \
  -H "X-Payment: ${PROOF}" \
  http://127.0.0.1:8087/protected
```

Expected properties:

- HTTP status: `200 OK`.
- `ok`: `true`.
- `data.message`: `Protected Arc builder resource unlocked.`
- `receipt.verifierMode`: `local-simulation`.
- `receipt.settled`: `false`.
- `receipt.transactionBroadcast`: `false`.
- `unitEconomics.priceMicroUsd`: `10000`.

## 5. Verify the JSON-RPC / MCP-style tool path

List tools:

```bash
printf '{"jsonrpc":"2.0","id":"tools","method":"tools/list"}\n' \
  | python3 examples/x402-local-challenge-server/server.py --mcp-stdio
```

Inspect a challenge through the tool surface:

```bash
printf '{"jsonrpc":"2.0","id":"inspect","method":"tools/call","params":{"name":"inspect_payment_challenge","arguments":{}}}\n' \
  | python3 examples/x402-local-challenge-server/server.py --mcp-stdio
```

Call the paid resource tool with the local proof:

```bash
printf '{"jsonrpc":"2.0","id":"paid","method":"tools/call","params":{"name":"get_paid_resource","arguments":{"xPayment":"local-demo:arc-mcp-builder-assistant.local-report.v1:arc-testnet:USDC:0.01:0.01"}}}\n' \
  | python3 examples/x402-local-challenge-server/server.py --mcp-stdio
```

Expected property:

- `result.structuredContent.status`: `200`.
- `result.structuredContent.body.receipt.transactionBroadcast`: `false`.

## 6. Production handoff notes

Do not replace `LocalDemoVerifier` until these are solved and reviewed:

1. Verifier endpoint and Circle Gateway/x402 contract are chosen.
2. Pay-to address ownership is verified.
3. Nonce, expiry, replay protection, and idempotency are implemented.
4. Asset decimals and network IDs are validated from trusted config, not user input.
5. Logs redact payment headers and never store secrets.
6. Rollback returns to challenge-only mode if verifier calls fail or settle ambiguously.

See [Arc production deployment](./arc-production-deployment.md) for the secret-free deployment runbook and live smoke checklist.

## Honest status

Real today:

- local 402 challenge response;
- local deterministic proof path;
- safe MCP-style manifest and JSON-RPC tool surface;
- unit-economics metadata for a tiny paid-report demo.

Intentionally not real yet:

- wallet connection;
- payment signature validation;
- Circle Gateway or production x402 verifier calls;
- settlement finality;
- transaction broadcast;
- autonomous agent spending.
