# Arc Testnet Send Readiness Gate

> Guard-only reviewer contract after the unsigned transaction draft preview. This page does **not** enable wallet connection, signing, custody, settlement, or transaction broadcast.

## Verdict

The current repo is still a public-ready static builder kit, not a live send product. This page defines the minimum evidence required before a separate future PR can even propose an Arc Testnet send path.

No wallet connection in this increment. No private keys. No signing. No transaction broadcast. `eth_sendTransaction` remains forbidden in the shipped public kit. Plain-language gate: eth_sendTransaction remains forbidden until a separate reviewed send PR changes that boundary.

## Real today

- Arc Testnet constants are documented and used by local-only surfaces: decimal chain ID `5042002`, hex chain ID `0x4cef52`, and the public Arc Testnet RPC status helper.
- The payment-intent playground can freeze reviewed money fields, record final local confirmation, and produce an unsigned transaction draft for reviewer comparison.
- The local calldata consistency check compares the unsigned transaction draft against the reviewed recipient, token target, USDC amount, zero native value, and Arc Testnet chain metadata.
- Receipt and transaction-status playgrounds are available for local/read-only review paths.
- CI validates that current demos do not collect keys, connect wallets, sign, or broadcast.

## Intentionally not real yet

- No wallet permission prompt.
- No injected-wallet account request.
- No chain switching request.
- No transaction signing.
- No `eth_sendTransaction` call.
- No custody, relayer, backend signer, or autonomous spending path.
- No claim that a real Arc Testnet transfer is shipped in this repo today.

## Required evidence before a future send PR

A future send PR must include all of the following evidence before reviewers should consider it:

1. **Frozen intent evidence**
   - recipient address;
   - token contract target;
   - USDC amount with 6-decimal conversion;
   - memo or intent hash;
   - expiry;
   - Arc Testnet chain ID `5042002` and `0x4cef52`.
2. **Unsigned draft evidence**
   - calldata decodes back to the reviewed recipient and amount;
   - transaction `to` equals the reviewed token target;
   - transaction `value` is zero for ERC-20 USDC transfer drafts;
   - unsigned transaction draft is visibly separate from any wallet handoff.
3. **Final local confirmation evidence**
   - final local confirmation was recorded after the frozen intent and unsigned draft were visible;
   - the confirmation copy names the exact recipient, amount, chain, and token;
   - reviewers can reproduce the same preflight report from a clean browser session.
4. **Arc Testnet status evidence**
   - chain ID probe succeeds against the Arc Testnet RPC when a live network check is in scope;
   - failures stay non-destructive and block send readiness;
   - RPC downtime is treated as a stop condition, not a reason to bypass checks.
5. **Safety evidence**
   - No wallet connection in this increment remains true until the send PR explicitly changes it;
   - No private keys are accepted, pasted, logged, or committed;
   - No signing is possible before the future PR's new tests pass;
   - No transaction broadcast is possible from current pages;
   - `eth_sendTransaction` remains forbidden outside the future, reviewed send implementation.

## Human approval checkpoint

A future send PR must require a human to review, in one visible screen or report:

- chain: Arc Testnet only;
- chain ID: `5042002` / `0x4cef52`;
- asset: USDC;
- recipient: exact address;
- amount: exact decimal value and base-unit value;
- token target: exact contract address used by the draft;
- expiry and memo/intent hash;
- the unsigned transaction draft and decoded fields;
- explicit warning that signing and broadcast can move real testnet assets.

The approval state must not be inferred from earlier actions such as opening the playground, editing the intent, generating calldata, or copying a report. It has to be a distinct final local confirmation step before any future live wallet handoff.

## Rollback criteria

The future send PR must document rollback criteria before it is merged. At minimum, the implementation should be stopped, reverted, or disabled when any of these happen:

- Arc Testnet chain ID is not `5042002` or `0x4cef52`.
- The wallet is on a non-Arc chain or cannot prove the selected chain.
- The decoded calldata differs from the reviewed recipient, amount, token target, or zero native value.
- The recipient, amount, token target, or expiry changes after final local confirmation.
- Any private key, seed phrase, verifier token, API key, or secret appears in browser state, logs, commits, screenshots, CI output, or public docs.
- A test, validator, browser smoke, or reviewer report shows an unexpected wallet call, signing call, backend call, or broadcast attempt.

## Future PR acceptance criteria

The first real send PR should be narrow and reversible:

- It must be Arc Testnet only.
- It must add tests before production code for wallet-request behavior.
- It must keep private keys out of the repo and browser UI.
- It must preserve a disabled or dry-run path for reviewers.
- It must verify the exact wallet request payload before any transaction can be submitted.
- It must update public copy so the site distinguishes local-only pages from live testnet behavior.
- It must include a browser smoke test that spies on wallet requests and proves no extra wallet methods fire.

## Public wording to use

Safe wording:

> The project has a reviewed local payment-intent flow, unsigned Arc Testnet transaction draft preview, final local confirmation, and a public send-readiness gate. A real Arc Testnet send path is intentionally deferred to a separate PR.

Unsafe wording:

> The app already sends Arc payments.

> The agent can autonomously pay.

> The wallet integration is complete.

> Production settlement is live.

## Reviewer shortcut

Before approving any future live-send work, ask one question: can a reviewer independently compare the frozen intent, final local confirmation, unsigned transaction draft, wallet request payload, Arc Testnet chain proof, and rollback criteria without trusting hidden state?

If the answer is no, the send path is not ready.
