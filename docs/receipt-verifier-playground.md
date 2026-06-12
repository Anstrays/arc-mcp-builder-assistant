# Receipt verifier playground

The receipt verifier playground is a local-only companion to the payment-intent playground. It lets reviewers paste a simulated Arc payment receipt JSON and inspect whether the fields are internally consistent before any real wallet, ArcScan, RPC, or backend verifier is added.

Open it locally after starting the static server:

```bash
python3 -m http.server 8080
# http://localhost:8080/examples/receipt-verifier-playground/
```

Public path after GitHub Pages deployment:

```text
https://anstrays.github.io/arc-mcp-builder-assistant/examples/receipt-verifier-playground/
```

## What this verifier checks

The page parses a JSON object and checks these local receipt fields:

- `chainId`: must match Arc Testnet `5042002` / `0x4cef52`.
- `recipient`: must be a non-zero `0x`-prefixed 20-byte address and cannot be
  the pinned USDC token contract.
- `amount`: must be a positive USDC amount with at most 6 decimal places.
- `asset`: must be `USDC`.
- `intentHash`: must be a 32-byte `0x` hash.
- `expiry`: must be an ISO-compatible future timestamp.
- `transactionHash`: may be empty for a draft or a 32-byte `0x` hash for a simulated submitted receipt.

The verifier also emits normalized JSON with the static Arc constants used by the starter kit:

- network: Arc Testnet
- chain ID: `5042002` / `0x4cef52`
- asset: USDC
- asset decimals: `6`
- explorer: `https://testnet.arcscan.app`

## What it does not prove

This is intentionally a browser-local review tool:

- local-only parsing and field checks;
- no wallet signing;
- no transaction broadcast;
- no backend calls;
- no RPC query;
- no ArcScan query;
- no proof of token transfer finality;
- no custody, private key, or seed phrase handling.

A passing local verdict means the receipt JSON is shaped correctly for review. It does **not** prove that an onchain transaction happened.

## Safe extension path

Only extend this page toward real testnet verification after the separate wallet/status PR proves these gates:

1. Re-check current Arc docs/MCP constants.
2. Keep receipt parsing separate from wallet signing.
3. Add read-only status lookup first, not transaction submission.
4. Require explicit human approval for any wallet action.
5. Keep transaction hashes and explorer links reviewable before any automated follow-up.
6. Document every network call and failure mode in the UI.

## Example receipt

```json
{
  "network": "arc-testnet",
  "chainId": 5042002,
  "recipient": "0x1111111111111111111111111111111111111111",
  "amount": "5.00",
  "asset": "USDC",
  "intentHash": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "expiry": "2030-05-30T00:00:00.000Z",
  "transactionHash": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "status": "submitted_simulated"
}
```
