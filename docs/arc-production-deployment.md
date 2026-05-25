# Arc production deployment runbook

This is a production-facing handoff for the local Arc/x402 paid-agent boundary. It keeps the public repository secret-free while documenting exactly what a builder must replace before a real Circle Gateway or x402 verifier is enabled.

> Safety baseline: this repository does **not** create payments, sign wallet messages, broadcast transactions, store private keys, store seed phrases, or claim production settlement. The bundled smoke checks validate HTTP response shape only.

## What is production-ready vs still a placeholder

Production-facing now:

- Local paid-agent boundary returns an x402-style `402 Payment Required` challenge.
- The challenge includes a machine-readable MCP-style manifest and safety flags.
- `scripts/live_arc_gateway_smoke.py` can check a deployed endpoint without creating payments.
- `.env.example` documents deployment and smoke-test variables without real secrets.

Still a placeholder:

- Real Circle Gateway / x402 verification.
- Wallet UX, signing, or transaction submission.
- Mainnet or autonomous spending flows.
- Any custody, balance management, or private-key handling.

## Environment contract

Use the public example as a template:

```bash
cp examples/x402-local-challenge-server/.env.example .env
```

Required for live smoke:

- `ARC_PAID_AGENT_URL`: deployed protected endpoint URL. Example shape: `https://your-service.example/protected`.

Optional for live smoke:

- `EXPECT_402_ONLY=true`: validates the unpaid challenge and stops before any paid retry.
- `ARC_LIVE_X_PAYMENT`: opaque `X-Payment` proof created outside this repo by a real x402/Circle Gateway payment flow.

Future verifier placeholders:

- `CIRCLE_GATEWAY_API_KEY`: store only in a deployment secret manager. Never commit it.
- `X402_GATEWAY_VERIFIER_URL`: URL for the production verifier boundary once implemented.

Do not add:

- no private keys;
- no seed phrases;
- no browser-held entity secrets;
- no real user payment proofs in git history;
- no logs that print `ARC_LIVE_X_PAYMENT` or gateway credentials.

## Deployment shape

A minimal deployment should expose the same protected resource contract as the local example:

1. Request without `X-Payment` returns HTTP `402`.
2. The `402` JSON includes `accepts[]` payment terms for `arc-testnet` and a `mcpManifest`.
3. `mcpManifest.safety.transactionBroadcast` is `false`.
4. `mcpManifest.safety.humanApprovalRequired` is `true`.
5. When a production verifier exists, a request with a valid externally created `X-Payment` proof may return HTTP `200` plus an accepted receipt.

The repo's local example intentionally accepts only deterministic demo proofs. Do not treat those proofs as production settlement.

## Safe live smoke

Challenge-only gate, recommended for public CI/staging before real verifier credentials exist:

```bash
export ARC_PAID_AGENT_URL="https://your-service.example/protected"
python3 scripts/live_arc_gateway_smoke.py --expect-402-only
```

Expected result:

```text
unpaid 402 challenge accepted: network=arc-testnet transactionBroadcast=false
stopped after 402-only check; no ARC_LIVE_X_PAYMENT was supplied
```

Paid retry gate, only after a separate production payment flow has produced an opaque proof:

```bash
export ARC_PAID_AGENT_URL="https://your-service.example/protected"
export ARC_LIVE_X_PAYMENT="<opaque proof from your payment flow>"
python3 scripts/live_arc_gateway_smoke.py
```

The script sends the proof as an `X-Payment` header. It redacts the proof in output and does not create payments.

## Circle Gateway / x402 verifier handoff

When replacing the local verifier with a real Circle Gateway or x402 verifier:

1. Keep the verifier behind an interface boundary like the current `PaymentVerifier` protocol.
2. Verify chain/network first: Arc Testnet chain ID is `5042002` (`0x4cef52`).
3. Verify amount, asset, recipient, expiry, and resource binding before returning paid content.
4. Keep human approval mandatory for any wallet-created payment proof.
5. Log only stable request IDs and redacted proof fingerprints.
6. Fail closed: verifier timeout, invalid proof, wrong network, wrong amount, or wrong recipient must return `402`/`403`, not paid content.
7. Add integration tests with fixture proofs before enabling paid `200` in staging.

## Rollback plan

If a deployed verifier behaves unexpectedly:

1. Disable the production verifier feature flag.
2. Revert to `--expect-402-only` challenge mode.
3. Rotate any possibly exposed gateway credentials.
4. Re-run:

```bash
python3 scripts/live_arc_gateway_smoke.py --expect-402-only
```

5. Review logs for accidental proof or credential output before re-enabling.

## Pre-release checklist

- [ ] Endpoint returns an unpaid `402` challenge with Arc Testnet payment terms.
- [ ] `mcpManifest.safety.transactionBroadcast` remains `false` unless a separate audited transaction path exists.
- [ ] Human approval is required for every payment proof.
- [ ] `.env.example` contains placeholders only.
- [ ] `scripts/live_arc_gateway_smoke.py --expect-402-only` passes against staging.
- [ ] No private keys, seed phrases, API keys, payment proofs, or wallet credentials are committed.
- [ ] Rollback path has been tested.

## Non-goals

This runbook does not create payments, does not connect wallets, does not broadcast transactions, and does not make this demo a production payments processor. It is the safe bridge from a local Arc/x402 paid-agent MVP to a future Circle Gateway verifier integration.
