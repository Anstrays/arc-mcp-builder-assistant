# Transaction status playground

The transaction status playground is the next safe step after the local receipt verifier. It lets a reviewer paste an Arc Testnet transaction hash and run a **read-only** public RPC lookup from the browser.

Open it here:

- [examples/transaction-status-playground/index.html](../examples/transaction-status-playground/index.html)

## What it can verify

The playground uses the Arc Testnet public RPC endpoint and only these JSON-RPC methods:

- `eth_chainId`
- `eth_getTransactionByHash`
- `eth_getTransactionReceipt`

It can show whether the RPC reports the expected Arc Testnet chain ID (`5042002 / 0x4cef52`) and whether the transaction is currently found, pending, confirmed, failed, or unknown.

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
- human approval remains mandatory for any future write path.

## Reviewer flow

1. Create or inspect a local payment intent.
2. Verify simulated receipt shape in the receipt verifier playground.
3. If a real Arc Testnet transaction already exists, paste its transaction hash into the transaction status playground.
4. Save the JSON output as evidence in a PR, issue, or build log.
5. Do not treat `confirmed` as product settlement unless a later PR also verifies the expected recipient, amount, asset, and user approval path.

## Future wallet PR gate

A future signing PR should not replace this page. It should use this read-only status page as a guardrail and add a separate, reviewed, testnet-only wallet adapter with:

- chain ID gate: `5042002 / 0x4cef52`;
- exact recipient and amount review;
- explicit human confirmation;
- disabled mainnet path;
- separate tests proving no signing happens before approval;
- clear ArcScan links after submission.
