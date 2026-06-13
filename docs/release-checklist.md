# Release readiness checklist

A concise, operational checklist for deciding whether `main` is ready to be
tagged or announced. **Creating a tag, GitHub Release, or changelog entry
requires explicit maintainer approval** — this checklist gathers evidence, it
does not authorize a release.

This kit stays in its safe scope: Arc Testnet only, non-custodial, no mainnet,
no autonomous spending, no live settlement, and no real paid-agent verification.
None of the steps below sign or broadcast a transaction.

## 1. Clean tree and branch

```bash
git status --short --branch     # expect a clean worktree on main
git log -1 --oneline
```

- `main` is the release source and the worktree is clean.
- No generated local reports, `.env`, operator-evidence drafts, or temporary
  files are staged.

## 2. Zero effective open work before a release decision

- No open issue or pull request blocks the intended release scope.
- Any deferred work is captured as a clearly-labelled follow-up, not a silent
  gap.

## 3. Canonical suite

```bash
python3 scripts/check_completion.py
python3 scripts/test_all.py
```

- Completion check and the full dependency-free regression suite both pass.

## 4. Arc Builder Doctor

```bash
python3 scripts/arc_builder_doctor.py          # default: local-only
python3 scripts/arc_builder_doctor.py --full   # also runs the canonical suite
```

- Default and `--full` runs report `overallStatus` of `pass` (a documented
  `warn`, for example missing Node.js, is acceptable only with a recorded
  reason).
- See [`arc-builder-doctor.md`](./arc-builder-doctor.md) for the report contract.

## 5. Optional read-only Arc Testnet evidence

```bash
python3 scripts/arc_builder_doctor.py --include-arc-rpc --strict
```

- When network access is available, the read-only RPC check confirms Arc Testnet
  chain id `5042002` / `0x4cef52`.
- This is read-only: no wallet, signing, gas estimation, simulation, or
  broadcast.

## 6. Public Pages health

```bash
python3 scripts/arc_builder_doctor.py --include-public-site
```

- The public site root, the disabled-by-default wallet-send lab, and the styled
  docs viewer return HTTP 200 with their expected public safety markers.

## 7. Public claims and secret hygiene

```bash
python3 scripts/test_public_claims.py
python3 scripts/validate_repo.py
```

- Public-claims scan passes: no accidental production/mainnet/custody readiness
  language.
- Repository validation passes, including its credential-pattern scan.
- Re-run a changed-file secret scan and confirm no credential, proof, or wallet
  material is committed.

## 8. Exact GitHub Actions status

- The `Validate static site` workflow is green on the release commit.
- The Pages deploy workflow is green and least-privilege permissions are
  unchanged.

## 9. Arc official facts re-check

- Re-confirm Arc Testnet chain id, RPC URL, explorer URL, and USDC token
  address against current official Arc documentation before announcing.

## 10. Release authorization (maintainer only)

- A tag, GitHub Release, or changelog release entry is created **only** after a
  maintainer explicitly approves it. This checklist never creates one.
