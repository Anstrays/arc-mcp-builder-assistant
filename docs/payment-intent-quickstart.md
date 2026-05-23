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
- USDC unit preview, including 6-decimal ERC-20 base units versus 18-decimal native gas accounting;
- wallet guard reasons;
- local validation summary;
- signing preflight report.

### 5. Confirm local approval state

Click the local approval control and confirm the JSON changes. This only changes browser-local demo state.

### 6. Copy the preflight report

Copy the signing preflight report and paste it into an AI coding tool or review note. The report is useful because it separates facts that are ready from facts that still require a wallet and human approval.

### 7. Stop the preview server

Stop the local server when finished.

## Expected reviewer takeaway

The current project is a safe builder kit, not a live payment app. A reviewer should be able to see:

- a clear payment-intent data model;
- a human approval gate;
- explicit disabled wallet controls;
- a preflight report that explains what still blocks signing;
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
2. add wallet-chain detection without signing;
3. keep submit controls disabled until chain ID, recipient, amount, expiry, and human approval all pass;
4. add regression tests that prove the UI cannot call signing or broadcast code while guards are failing;
5. only then consider a separate testnet signing PR.

## Useful links

- [Payment-intent demo spec](./payment-intent-demo.md)
- [Arc Testnet integration runbook](./arc-testnet-integration-runbook.md)
- [Arc wallet integration notes](./arc-wallet-integration-notes.md)
- [Builder readiness checklist](./arc-builder-readiness-checklist.md)
