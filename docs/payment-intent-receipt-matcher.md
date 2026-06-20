# Payment Intent Receipt Matcher

A read-only, browser-only tool that compares an offchain **payment intent** with an onchain **Arc Testnet transaction receipt**. It answers the question:

> "Did this transaction actually transfer the expected USDC amount to the expected recipient?"

It is part of the [Arc MCP Builder Assistant](https://anstrays.github.io/arc-mcp-builder-assistant/) static demo suite.

## Where to use it

Open `examples/payment-intent-receipt-matcher/index.html` locally or via the GitHub Pages site.

## What it does

1. Parses a payment intent JSON (recipient, token, amount / amountBaseUnits, decimals).
2. Validates the transaction hash shape locally.
3. Calls `eth_chainId` on the public Arc Testnet RPC to confirm the right chain.
4. Calls `eth_getTransactionReceipt` for the supplied hash.
5. Decodes only the pinned Arc Testnet USDC `Transfer` logs (`0x3600000000000000000000000000000000000000`).
6. Reports `match`, `mismatch`, `revert`, `not_found`, or `unknown`.
7. Emits a machine-readable evidence JSON object.
8. Lets you download the review evidence as local JSON or Markdown after a match run.

## Input format

The matcher accepts a JSON payment intent with the following fields. All fields are validated before any RPC call is made.

```json
{
  "version": "2025-06-arc-payment-intent-v1",
  "network": "Arc Testnet",
  "chainId": 5042002,
  "asset": "USDC",
  "token": "0x3600000000000000000000000000000000000000",
  "recipient": "0x1111111111111111111111111111111111111111",
  "amount": "0.01",
  "amountBaseUnits": "10000",
  "decimals": 6,
  "memo": "Optional note"
}
```

Either `amount` (decimal string) or `amountBaseUnits` (integer string) is required. `recipient` and a valid 20-byte token address are required.

## Safety boundaries

- No wallet connection.
- No private keys, seed phrases, or credentials.
- No transaction signing or broadcast.
- Only `eth_chainId` and `eth_getTransactionReceipt` RPC calls.
- Read-only, Arc Testnet only.
- A `match` verdict does **not** prove settlement, business acceptance, or offchain fulfillment.

## Evidence export

After you run a match, two read-only export buttons become active:

- **Download JSON evidence** — machine-readable packet with matcher version, export timestamp, Arc Testnet chain constants, normalized intent/receipt fields, matched USDC Transfer log summary, verdict, mismatch reasons, and a disclaimer.
- **Download Markdown evidence** — human-readable version of the same packet.

The export is local-only: it uses a browser `Blob` and `URL.createObjectURL`, so no file leaves your machine. There is no wallet, signing, broadcast, telemetry, `localStorage`, `sessionStorage`, or auto-upload. The exported evidence is an observed receipt/log summary, not a settlement proof, custody proof, or mainnet readiness claim.

## Verdicts

| Verdict | Meaning |
|---|---|
| `match` | Receipt status `0x1` and at least one USDC Transfer log matches recipient, token, and amount. |
| `mismatch` | Receipt status `0x1` but no Transfer log matched the intent. |
| `revert` | Receipt exists with status `0x0`. |
| `not_found` | RPC returned `null` for the receipt. |
| `unknown` | Wrong chain, RPC error, malformed envelope, hash mismatch, or invalid local input. |

## Files

- `examples/payment-intent-receipt-matcher/index.html` — static UI.
- `examples/payment-intent-receipt-matcher/matcher.js` — read-only matcher logic.
- `scripts/test_payment_intent_receipt_matcher.py` — Python smoke tests.
- `scripts/payment_intent_receipt_matcher_behavior_harness.mjs` — Node.js behavior harness.

## Related
- [Payment Intent Playground](payment-intent-demo.md)
- [Receipt Viewer](receipt-viewer.md)
- [Transaction Status Playground](transaction-status-playground.md)
