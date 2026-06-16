# Agent payment receipt viewer

The agent payment receipt viewer is a read-only Arc Testnet evidence page for
reviewers who already have a transaction hash from a wallet, ArcScan, or an
operator handoff. It fetches the receipt through public RPC, shows the receipt
status, and highlights pinned Arc Testnet USDC `Transfer` logs.

Open it locally after starting the static server:

```bash
python3 -m http.server 8080
# http://localhost:8080/examples/receipt-viewer/
```

Public path after GitHub Pages deployment:

```text
https://anstrays.github.io/arc-mcp-builder-assistant/examples/receipt-viewer/
```

## What it checks

The page performs a chain-first, read-only lookup using only:

- `eth_chainId`
- `eth_getTransactionReceipt`

It requires the RPC endpoint to report Arc Testnet `5042002 / 0x4cef52` before
it asks for the receipt. If the chain ID does not match, the viewer stops after
`eth_chainId` and reports `unknown_wrong_chain`.

For a receipt on the expected chain, the viewer reports:

- `success` when `status` is `0x1`;
- `revert` when `status` is `0x0`;
- `not_found` when the RPC returns no receipt;
- `unknown` for RPC errors, ambiguous status, malformed JSON-RPC envelopes, or
  a returned receipt whose `transactionHash` does not match the reviewer input.

It also scans receipt logs for the ERC-20 `Transfer` topic emitted by the
pinned Arc Testnet USDC interface:

```text
0x3600000000000000000000000000000000000000
```

Decoded USDC Transfer logs show `from`, `to`, 6-decimal base units, and a human
USDC amount. Logs from other contracts are ignored.

## Safety limits

Every RPC request has a 15-second timeout and a 1 MB safety limit. Invalid
JSON, non-object JSON, mismatched JSON-RPC request IDs, replies with both
`result` and `error`, and oversized responses fail closed.

The canonical suite executes the real page JavaScript against a dependency-free
Node fake-RPC harness:

```bash
python scripts/test_receipt_viewer.py
```

The harness covers success, revert, missing receipt, wrong-chain stop,
invalid-input no-RPC, JSON-RPC envelope failure, transaction-hash binding, USDC
Transfer log decoding, and timeout handling.

## What it does not prove

This is evidence for receipt shape only. It does not prove business acceptance,
offchain fulfillment, product settlement, customer entitlement, payment-intent
review, or final reconciliation.

Safety boundaries:

- no wallet signing;
- no transaction broadcast;
- no private-key handling;
- no gas estimation or simulation;
- no automatic retry;
- no autonomous spending;
- human approval remains mandatory for any future write path.

## Reviewer flow

1. Produce or receive a reviewed Arc Testnet transaction hash.
2. Paste the hash into the receipt viewer.
3. Confirm the page reports Arc Testnet `5042002 / 0x4cef52`.
4. Inspect `success`, `revert`, `not_found`, or `unknown`.
5. If USDC Transfer logs are present, compare the decoded `from`, `to`, and
   amount with the frozen payment intent or operator evidence packet.
6. Store the JSON output as review evidence, not as a settlement receipt.

Use the transaction-status playground when you also need to compare expected
recipient and amount against transaction calldata. Keep this receipt viewer as
the narrow, receipt-only path for agent payment evidence.
