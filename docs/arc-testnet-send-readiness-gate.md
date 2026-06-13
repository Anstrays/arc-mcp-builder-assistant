# Arc Testnet Send Readiness Gate

> Reviewer contract for the repository's separate guarded Arc Testnet
> browser-wallet send lab. Local-only playgrounds remain wallet-free.

## Verdict

The readiness gate is implemented for one narrow Arc Testnet transaction
shape. The guarded lab is disabled by default and can request one manually
confirmed USDC transaction only after every visible guard passes.

This is not a production wallet, custody system, autonomous agent, settlement
service, or mainnet implementation.

## Real today

- Arc Testnet is pinned to decimal chain ID `5042002` and hex chain ID
  `0x4cef52`.
- The payment-intent playground remains local-only and produces a frozen
  unsigned transaction draft for review.
- The separate guarded send lab can explicitly request an injected wallet
  account, switch or add Arc Testnet, and request one `eth_sendTransaction`.
- The token target, six-decimal USDC amount, zero native value, recipient,
  memo, expiry, and deterministic calldata are frozen and compared
  immediately before wallet handoff.
- The external wallet confirmation dialog is the only signing path.
- Embedded-frame execution is blocked; the write surface requires a top-level browsing context.
- Zero addresses and the pinned USDC token contract are rejected as
  recipients.
- A one-attempt lock prevents automatic retry or a second transaction request
  during the same page load.
- A returned transaction hash is labeled submitted/pending, never confirmed.

## Still intentionally blocked

- No private keys, seed phrases, raw signed transactions, or custody secrets.
- No backend signer, relayer, sponsor, unattended policy engine, or autonomous
  spending.
- No mainnet profile, mainnet fallback, or unrelated chain selector.
- No transaction request on page load.
- No wallet connection or transaction broadcast from local-only playgrounds,
  docs, tests, or CI.
- No claim of live settlement or production payment processing.

## Required evidence

Reviewers must be able to reproduce:

1. **Default-disabled evidence**
   - opening the page without the exact query gate keeps wallet controls
     disabled;
   - opening the page inside an embedded frame keeps wallet controls disabled;
   - no wallet method fires on page load.
2. **Frozen intent evidence**
   - exact recipient;
   - token target;
   - decimal and base-unit USDC amount;
   - memo and expiry;
   - exact Arc Testnet chain IDs.
3. **Payload parity evidence**
   - calldata decodes back to the frozen recipient and amount;
   - transaction `to` is the pinned Arc Testnet USDC target;
   - transaction `value` is `0x0`;
   - any post-freeze change blocks the request.
4. **Human approval evidence**
   - risk acknowledgement;
   - explicit wallet connection and chain proof;
   - typed confirmation phrase;
   - final confirmation checkbox;
   - external wallet dialog controlled by the human.
5. **One-shot and failure evidence**
   - the attempt lock engages before the wallet transaction request;
   - rejection and errors do not retry automatically;
   - a returned hash is not called confirmed.

## Rollback criteria

Disable or revert the guarded lab when:

- the wallet cannot prove exact Arc Testnet chain ID;
- frozen fields and calldata differ;
- token target or native value differs;
- the page can request a wallet from an embedded frame;
- a zero address or the pinned USDC token contract can be frozen as recipient;
- a request fires on page load or retries automatically;
- more than one transaction request can occur per page load;
- an unexpected wallet method fires;
- any key, seed phrase, opaque proof, credential, or secret appears;
- tests, validation, or browser smoke fail.

The fastest rollback is to remove or revert the separate guarded page while
leaving every local-only example available.

## Public wording to use

Safe wording:

> The project includes a separate disabled-by-default Arc Testnet
> browser-wallet send lab for one capped, manually confirmed USDC transaction
> request. It has no custody, private-key handling, mainnet, or autonomous
> spending.

Unsafe wording:

> The agent can autonomously pay.

> The wallet integration is production-ready.

> Mainnet settlement is live.

## Reviewer shortcut

Ask one question: can a reviewer independently compare the frozen intent,
decoded calldata, exact wallet request, Arc Testnet chain proof, human
confirmation, one-attempt lock, and rollback path without trusting hidden
state?

If the answer is no, the guarded send path is not ready.
