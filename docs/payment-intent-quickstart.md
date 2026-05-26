# Payment-intent quickstart

Use this 5-minute path when you want to show the project to an Arc builder, reviewer, or contest judge without connecting a wallet or sending a transaction.

## What this proves

- The site can turn an agent payment request into reviewable JSON.
- The user, not the agent, keeps approval control.
- Arc Testnet details are visible as preflight context before wallet work.
- ERC-20 USDC base units are previewed separately from native gas decimals.
- The demo has guardrails for recipient, amount, expiry, and human approval.
- The current build is local-first: no wallet connection, no backend call, no RPC write, no signing, and no broadcast.

## Before you start

Run the same dependency-free checks that CI uses:

```bash
python3 scripts/test_payment_intent_playground.py
python3 scripts/test_x402_boundary.py
python3 scripts/validate_repo.py
```

Optional read-only Arc status probe:

```bash
python3 scripts/check_arc_testnet_status.py
```

This helper only checks read-only JSON-RPC facts such as chain ID and block number. It does not validate a wallet, account, recipient approval, balance, signature, or transaction safety.

## Demo path

### 1. Start the static preview server

```bash
python3 -m http.server 8080
```

### 2. Open the playground

```text
http://localhost:8080/examples/payment-intent-playground/
```

### 3. Review the sample payment intent fields

- recipient address;
- USDC amount;
- memo / purpose;
- expiry;
- local status.

### 4. Check the readiness panels before touching wallet work

- Arc Testnet status constants;
- read-only wallet preview state: provider detected/not detected, selected address if exposed by the wallet, and chain gate status without account requests;
- USDC unit preview, including 6-decimal ERC-20 base units versus 18-decimal native gas accounting;
- wallet guard reasons;
- local validation summary;
- signing preflight report;
- final local confirmation gate that records review intent without enabling any transaction request;
- unsigned ERC-20 transaction draft preview for the future wallet PR, with wallet requests still disabled;
- local transaction draft consistency check that decodes calldata back to recipient and USDC base units;
- wallet handoff readiness manifest that keeps the future send PR blocked until every guard is satisfied.

### 5. Confirm local approval state

Click the local approval control and confirm the JSON changes. This only changes browser-local demo state.

### 6. Record final local confirmation

After preparing and manually approving the frozen intent, check the final review box and click the local confirmation button. This only records that a human reviewed the exact frozen fields. It still does not request wallet permissions, sign, or submit anything.

### 7. Inspect the unsigned transaction draft

Review the generated ERC-20 transfer payload preview. It shows the future wallet request shape (`chainId`, token `to`, `value`, encoded `data`, recipient, and USDC base units) while keeping `walletRequestEnabled: false` and `unsignedOnly: true`.

### 8. Check draft consistency

Review the local consistency checklist. The playground decodes the unsigned ERC-20 calldata and verifies that token target, native value, chain ID, recipient, and 6-decimal USDC base units match the current intent before any future wallet handoff.

### 9. Review the wallet handoff manifest

Confirm that the send PR blocker manifest still says `walletRequestEnabled: false`, `canRequestWallet: false`, and `sendPrRequired: true`. Its checklist shows which guards are already locally satisfied and which ones must remain blocked until a separate wallet/send PR.

### 10. Copy the preflight report

Copy the signing preflight report and paste it into an AI coding tool or review note. The report is useful because it separates facts that are ready from facts that still require a wallet confirmation and a separate send PR.

### 11. Stop the preview server

Stop the local server when finished.

## Expected reviewer takeaway

The current project is a safe builder kit, not a live payment app. A reviewer should be able to see:

- a clear payment-intent data model;
- a human approval gate;
- explicit disabled wallet controls;
- a preflight report that explains what still blocks signing;
- frozen recipient, amount, memo, expiry, chain, token, and base-unit fields after review starts;
- a final local confirmation gate that remains separate from wallet consent;
- an unsigned ERC-20 transfer payload preview that stays separate from wallet requests;
- a local consistency check that decodes the unsigned calldata back to the reviewed recipient and USDC base units;
- a wallet handoff manifest that remains blocked until validation, frozen intent, human approval, final confirmation, draft consistency, and live chain proof are satisfied;
- a read-only wallet preview that never calls account-request, signing, switching, or broadcast APIs;
- a USDC unit preview that keeps 6-decimal ERC-20 transfer math separate from 18-decimal native gas accounting;
- test commands that prove the local-only boundary stays intact.

## What is intentionally not included yet

- No browser wallet connection.
- No Circle wallet session.
- No private key or seed handling.
- No live x402 / Gateway verifier.
- No transaction signing.
- No transaction broadcast.
- No mainnet path.

## Next safe implementation slice

The next code slice should stay guard-first:

1. verify current Arc docs and Circle wallet details through MCP or official docs;
2. keep transaction request controls disabled until chain ID, recipient, amount, expiry, frozen intent, unsigned transaction draft, draft consistency check, wallet handoff manifest, human approval, and final confirmation all pass;
3. add regression tests that prove the UI cannot call signing, chain-switching, account-request, or broadcast code while guards are failing;
4. only then consider a separate testnet signing PR.

## Useful links

- [Payment-intent demo spec](./payment-intent-demo.md)
- [Arc Testnet integration runbook](./arc-testnet-integration-runbook.md)
- [Arc wallet integration notes](./arc-wallet-integration-notes.md)
- [Builder readiness checklist](./arc-builder-readiness-checklist.md)
