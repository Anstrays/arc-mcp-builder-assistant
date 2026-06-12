# Arc Testnet Operator Evidence Packet

> A machine-readable, local-only record for the manual review described in the Arc Testnet Operator Runbook. It records evidence; it does not authorize signing or transaction broadcast.

## Builder quickstart

Validate the committed safe example:

```bash
python scripts/validate_operator_evidence.py
```

Generate a create-only local draft bound to a commit:

```bash
# Bash
python scripts/generate_operator_evidence_draft.py --reviewed-commit "$(git rev-parse HEAD)"

# PowerShell
python scripts/generate_operator_evidence_draft.py --reviewed-commit (git rev-parse HEAD)
```

The default output is `arc.operator-evidence.local.json`. Generated `*.operator-evidence.local.json` files are gitignored, never overwrite an existing file, keep all live surfaces disabled, use `packetStatus: draft_operator_evidence`, keep `noSecretsObserved: false`, and intentionally fail strict validation until real evidence is reviewed.

List every known readiness gap without changing the draft:

```bash
python scripts/report_operator_evidence.py arc.operator-evidence.local.json --expect-commit FULL_LOWERCASE_COMMIT_SHA
```

The read-only report exits `0` only for a strictly valid packet, `1` for readable but incomplete or unsafe evidence, and `2` for malformed input. It redacts credential-like values and always reports `liveSendApproved: false`.

Validate a copied packet:

```bash
python scripts/validate_operator_evidence.py path/to/operator-evidence.json
```

Bind the result to the exact commit under review:

```bash
# Bash
python scripts/validate_operator_evidence.py path/to/operator-evidence.json --expect-commit "$(git rev-parse HEAD)"

# PowerShell
python scripts/validate_operator_evidence.py path/to/operator-evidence.json --expect-commit (git rev-parse HEAD)
```

A valid packet exits `0` and prints a concise JSON summary. Invalid JSON,
duplicate JSON keys, packets above the 1 MB safety limit, missing evidence,
unsafe controls, unknown fields, non-Arc chain values, credential-like values,
or unsafe references exit `2` with a clear error.

## Why this exists

The operator runbook defines a manual review process. This packet makes the current pre-send readiness baseline reproducible for a future PR reviewer without adding a wallet, signer, backend, or live-send path.

Use it to record:

- the exact reviewed commit;
- Arc Testnet scope: `5042002` / `0x4cef52`;
- required preflight, test, status, and browser evidence;
- repo-relative references that another reviewer can inspect;
- disabled wallet, signing, mainnet, backend-signer, autonomous-spending, and transaction-broadcast controls;
- the blocked decision and rollback responsibility.

## Safety contract

The validator fails closed unless all of these remain true:

- the schema is `arc-mcp-builder-assistant.arcTestnet.operatorEvidence.v1`;
- the packet is Arc Testnet only;
- the reviewed surface is `pre_send_readiness_baseline`;
- `--expect-commit`, when provided, exactly matches `review.reviewedCommit`;
- manual review and all required evidence gates are complete;
- `walletRequestSpyResult` is `not_applicable_no_wallet_surface`;
- no wallet connection, signing, backend signer, mainnet, autonomous spending, or transaction broadcast is enabled;
- no credential-like value is present;
- every evidence reference is a repository-relative path to an existing file;
- unknown fields are rejected;
- `eth_sendTransaction` remains forbidden;
- the decision is `blocked_pending_separate_guarded_pr`.

This pre-send baseline evidence packet cannot approve or fully validate the guarded send lab or any other live-send implementation. Every wallet/send extension requires its own wallet-request evidence and security review.

## Packet shape

The committed example lives at [`examples/arc-testnet-operator-evidence/evidence.example.json`](../examples/arc-testnet-operator-evidence/evidence.example.json).

```json
{
  "schema": "arc-mcp-builder-assistant.arcTestnet.operatorEvidence.v1",
  "packetStatus": "local_operator_evidence",
  "network": {
    "name": "arc-testnet",
    "chainId": 5042002,
    "chainIdHex": "0x4cef52"
  },
  "review": {
    "reviewedCommit": "6540eb3cc56a8d3ee3824f8de7995316754a36bf",
    "reviewedSurface": "pre_send_readiness_baseline",
    "manualReviewRequired": true
  },
  "controls": {
    "walletConnected": false,
    "signingEnabled": false,
    "transactionBroadcast": false,
    "ethSendTransactionForbidden": true,
    "separateGuardedPrRequired": true
  },
  "decision": {
    "status": "blocked_pending_separate_guarded_pr"
  }
}
```

The abbreviated shape above is explanatory only. Start from the committed example because the validator requires every field and rejects unknown fields.

## Operator workflow

1. Copy `evidence.example.json` outside the committed example path.
2. Prefer the create-only draft generator, or replace `review.reviewedCommit` with the full lowercase SHA under review.
3. Confirm every referenced repository file exists and represents evidence for that commit.
4. Complete the manual secret review before changing `noSecretsObserved` to `true`.
5. Change `packetStatus` from `draft_operator_evidence` to `local_operator_evidence` only after every required evidence gate is complete.
6. Keep all live-surface controls false and all required safety controls true.
7. Run the read-only readiness report until it lists no gaps.
8. Run the strict validator with `--expect-commit` set to the full SHA under review.
9. Attach the validated baseline packet and command output to the separate guarded PR as starting evidence, not final approval.

Do not add secrets, private proofs, wallet data, authorization headers, or production user data to an evidence packet.
