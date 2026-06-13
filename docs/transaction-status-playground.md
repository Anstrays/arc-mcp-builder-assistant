# Transaction status playground

The transaction status playground is the next safe step after the local receipt verifier. It lets a reviewer paste an Arc Testnet transaction hash, an expected recipient and amount, and run a **read-only** public RPC lookup from the browser.

Open it here:

- [examples/transaction-status-playground/index.html](../examples/transaction-status-playground/index.html)

## What it can verify

The playground uses the Arc Testnet public RPC endpoint and only these JSON-RPC methods:

- `eth_chainId`
- `eth_getTransactionByHash`
- `eth_getTransactionReceipt`

It can show whether the RPC reports the expected Arc Testnet chain ID (`5042002 / 0x4cef52`) and whether the transaction is currently found, pending, confirmed, failed, or unknown.

The lookup verifies the JSON-RPC `2.0` response envelope and request ID. It
stops after `eth_chainId` when the endpoint does not report Arc Testnet, then
requires any returned transaction and receipt hashes to match the exact hash
entered by the reviewer.

It also compares the observed transaction with an expected Arc Testnet USDC
transfer:

- transaction target is the pinned USDC interface;
- native value is zero;
- calldata decodes as `transfer(address,uint256)`;
- decoded recipient matches the expected recipient;
- decoded 6-decimal base units match the expected amount.

The resulting `evidenceVerdict` describes transaction shape only. Even
`confirmed_expected_transfer_shape` does not prove settlement, finality, token
balance changes, or business acceptance.

Each read-only RPC request has a 10-second timeout and a 1 MB safety limit.
Timeouts, oversized replies, invalid JSON, non-object JSON, mismatched
JSON-RPC envelopes, and transaction/receipt hash mismatches fail closed; they
never become a confirmed expected-transfer result.

The canonical suite executes the real page JavaScript against a dependency-free
Node fake RPC harness:

```bash
python scripts/test_transaction_status_behavior.py
```

It proves that exact expected-transfer matches, mismatches, wrong-chain
responses, mismatched hashes, invalid JSON-RPC envelopes, and invalid local
expectations are classified without a wallet or live RPC request.

## Read-only status states

- `not_checked` — no lookup has run yet.
- `pending` — `eth_getTransactionByHash` returned a transaction, but `eth_getTransactionReceipt` returned no receipt yet.
- `confirmed` — receipt exists and `status` is `0x1`.
- `failed` — receipt exists and `status` is `0x0`.
- `unknown` — the hash is not found, Arc RPC is unavailable, the chain ID mismatched, or the response is ambiguous.

## What it cannot verify

This is not a wallet flow and not a settlement verifier. It cannot prove:

- the human reviewed the recipient, amount, memo, expiry, or payment intent;
- a wallet is connected to Arc Testnet;
- token balance changes beyond the raw receipt status;
- final business acceptance by an agent, API, escrow, or backend;
- production x402/Circle Gateway settlement.

Safety boundaries:

- no wallet signing;
- no transaction broadcast;
- no private-key handling;
- no autonomous spending;
- human approval remains mandatory for any write path.

## Reviewer flow

1. Create or inspect a local payment intent.
2. Verify simulated receipt shape in the receipt verifier playground.
3. If a real Arc Testnet transaction already exists, paste its transaction hash into the transaction status playground.
4. Enter the expected recipient and amount from the frozen reviewed intent.
5. Save the JSON output as evidence in a PR, issue, or build log.
6. Do not treat `confirmed` or `confirmed_expected_transfer_shape` as product settlement.

## Guarded wallet extension gate

Any extension of the guarded send lab should not replace this page. It should use this read-only status page as a guardrail and keep the reviewed, testnet-only wallet adapter separate with:

- chain ID gate: `5042002 / 0x4cef52`;
- exact recipient and amount review;
- explicit human confirmation;
- disabled mainnet path;
- separate tests proving no signing happens before approval;
- clear ArcScan links after submission.
