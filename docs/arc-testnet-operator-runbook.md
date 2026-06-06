# Arc Testnet Operator Runbook

> A manual review checklist for operators evaluating any future guarded Arc Testnet live-send PR. This runbook does not connect a wallet, sign, hold secrets, or broadcast transactions.

## Chain scope

- Network: Arc Testnet only.
- Decimal chain ID: `5042002`.
- Hex chain ID: `0x4cef52`.
- First reviewed asset: Arc Testnet USDC.

Stop the review if the proposed implementation cannot prove this exact chain scope or can silently fall back to another network.

## Current safety boundary

The shipped public kit remains local-first and read-only. There are no private keys, no signing, no transaction broadcast, and no wallet connection in this increment. `eth_sendTransaction remains forbidden` until a separate guarded PR explicitly changes and proves that boundary.

This document is an operator checklist, not approval for a live-send implementation.

## Evidence required before manual review

Collect these artifacts from a clean checkout before reviewing any future live-send PR:

1. The frozen payment intent with exact recipient, token target, decimal amount, base-unit amount, memo, expiry, and Arc Testnet chain IDs.
2. The final local confirmation recorded after the frozen intent is visible.
3. The unsigned transaction draft and a decoded comparison against the frozen intent.
4. A wallet-request spy report proving the exact requested method and payload, plus proof that no unexpected wallet methods fired.
5. A passing validator, regression suite, Arc Testnet status helper, and browser smoke report.
6. A rollback note naming the fastest way to disable or revert the send surface.

Missing or inconsistent evidence is a stop condition, not a reason to approve with assumptions.

## Operator checklist

### 1. Confirm the proposed scope

- [ ] The PR is separate from unrelated documentation, design, or refactor work.
- [ ] The PR description says Arc Testnet only and names `5042002` / `0x4cef52`.
- [ ] Mainnet, other chains, backend signers, relayers, autonomous spending, and custody remain out of scope.
- [ ] The change is reversible and has a documented disabled or dry-run path.

### 2. Reproduce the local preflight

- [ ] Start from a clean browser session.
- [ ] Enter a known test recipient and a small test amount.
- [ ] Freeze the intent and record final local confirmation.
- [ ] Verify that the unsigned draft decodes to the same recipient and amount.
- [ ] Verify the ERC-20 token target and zero native transaction value.
- [ ] Change a frozen field and confirm the handoff becomes blocked.

### 3. Review the wallet boundary

- [ ] No page accepts or displays private keys, seed phrases, API keys, entity secrets, or authorization headers.
- [ ] No signing occurs before a visible wallet confirmation controlled by the human reviewer.
- [ ] No transaction broadcast occurs in the background or on page load.
- [ ] The wallet-request spy proves that only the reviewed request fires after the final confirmation.
- [ ] Rejection, wrong-chain, missing-wallet, expired-intent, and RPC-failure paths fail closed.

### 4. Run required checks

From the repository root:

```bash
python scripts/validate_repo.py
python scripts/test_all.py
python scripts/check_arc_testnet_status.py
git diff --check
```

The network status helper is read-only. A failed or unavailable Arc Testnet probe blocks review; it does not justify bypassing the chain check.

### 5. Record the decision

The reviewer should record:

- reviewed commit SHA;
- exact network and chain IDs;
- exact recipient, token target, decimal amount, and base-unit amount used for the smoke test;
- links or attachments for preflight, wallet-request spy, tests, and browser smoke evidence;
- approval or rejection with a short reason;
- rollback owner and rollback action.

Approval applies only to the reviewed commit and evidence. Any change to recipient handling, amount parsing, token target, chain selection, wallet method, or confirmation sequence requires another manual review.

## Immediate stop conditions

Reject or pause the future PR when any of these conditions appear:

- chain ID differs from `5042002` / `0x4cef52` or cannot be proven;
- reviewed fields differ from the unsigned draft or wallet request;
- any secret, credential, private key, or seed phrase appears in code, UI, logs, CI, screenshots, or review artifacts;
- signing or transaction broadcast can happen without the final human confirmation;
- the implementation can send on page load, retry automatically, or submit more than once;
- wallet-request spy evidence is missing or shows unexpected methods;
- tests, validation, status checks, or browser smoke fail;
- rollback is unclear or cannot be performed quickly.

## Acceptance boundary for a future PR

A future live-send implementation may be considered only in a separate guarded PR with explicit human approval, test-first wallet-request coverage, fail-closed Arc Testnet checks, and complete operator evidence.

Until that review is complete: no private keys, no signing, no transaction broadcast, and `eth_sendTransaction remains forbidden`.

## Machine-readable evidence record

After completing this checklist, record the result with the [Arc Testnet Operator Evidence Packet](./arc-testnet-operator-evidence.md) and validate it with:

```bash
python scripts/validate_operator_evidence.py path/to/operator-evidence.json
```

The packet stays blocked pending a separate guarded PR and cannot authorize signing or transaction broadcast.
