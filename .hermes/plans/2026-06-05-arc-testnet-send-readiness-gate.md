# Arc Testnet Send Readiness Gate Implementation Plan

> **For Hermes:** Use the validator-first static-docs continuation pattern. This is a guard-only Arc docs increment after the unsigned transaction draft guard.

**Goal:** Add one public Arc-only reviewer page that defines the exact evidence required before any future Arc Testnet send PR can be considered.

**Architecture:** Keep the current static kit public-ready and do not add wallet, RPC, signer, backend, or payment side effects. The new Markdown page becomes a docs-viewer page, a README current-kit entry, a landing-page docs card, and a validator-enforced public contract.

**Tech Stack:** Static Markdown, dependency-free docs viewer (`docs/viewer.js`), Python validator (`scripts/validate_repo.py`), GitHub Pages.

---

## Increment choice

The repo is already public-ready for its current local-only scope, including payment intent, final local confirmation, unsigned ERC-20 draft preview, local calldata consistency check, receipt/status helpers, job escrow simulator, content/public launch packets, and green CI on `main`.

The next safe Arc-only increment is **not** live sending. It is a guard-only public page: `docs/arc-testnet-send-readiness-gate.md`.

Why this is the safest next step:

- It follows the unsigned draft guard with a reviewer handoff contract instead of enabling `eth_sendTransaction`.
- It makes future live-wallet/testnet-send scope harder to misrepresent in public copy.
- It remains Arc-only: Arc Testnet chain ID `5042002`, hex `0x4cef52`, Arc Testnet RPC status, USDC decimals, reviewed recipient, amount, expiry, and rollback evidence.
- It introduces no private keys, wallet permission prompts, backend calls, custody, signing, or transaction broadcast.

## Task 1: RED — register the missing public page contract

**Objective:** Make `python3 scripts/validate_repo.py` fail before the page exists.

**Files:**
- Modify: `scripts/validate_repo.py`

**Steps:**
1. Add `docs/arc-testnet-send-readiness-gate.md` to `REQUIRED_FILES` near other Arc wallet/runbook docs.
2. Add `validate_arc_testnet_send_readiness_gate()` that reads README, `index.html`, `docs/viewer.js`, and the new doc.
3. Require markers for:
   - `Arc Testnet Send Readiness Gate`
   - `5042002`
   - `0x4cef52`
   - `unsigned transaction draft`
   - `final local confirmation`
   - `No wallet connection in this increment`
   - `No private keys`
   - `No signing`
   - `No transaction broadcast`
   - `eth_sendTransaction remains forbidden`
   - `rollback criteria`
4. Wire the function into `main()`.
5. Run `python3 scripts/validate_repo.py`.
6. Expected: FAIL only because `docs/arc-testnet-send-readiness-gate.md` is missing.

## Task 2: GREEN — add the reviewer-facing send readiness page

**Objective:** Add the minimal Markdown content needed for the validator contract and public usefulness.

**Files:**
- Create: `docs/arc-testnet-send-readiness-gate.md`

**Content requirements:**
- Clear verdict: not a send feature, not a wallet feature, no broadcast.
- Real today / intentionally not real yet split.
- Required pre-send evidence checklist.
- Frozen intent fields and unsigned draft comparison checklist.
- Human approval and rollback criteria.
- Forbidden claims/surfaces.
- Future PR acceptance criteria.

**Verification:** Run `python3 scripts/validate_repo.py`; expected failure should move to missing wiring markers until README/index/viewer are updated.

## Task 3: GREEN — wire the page through public navigation

**Objective:** Make the page discoverable everywhere public docs are discovered.

**Files:**
- Modify: `README.md`
- Modify: `index.html`
- Modify: `docs/viewer.js`

**Steps:**
1. Add README current-kit bullet after `wallet-preflight-contract.md`.
2. Add README completion/safe-default wording that names the send readiness gate as a future-send checkpoint.
3. Add one landing-page docs card for the readiness gate.
4. Add the page to `PAGES` in `docs/viewer.js` under `Playbooks` near `wallet-preflight-contract.md`.
5. Update homepage doc metric from `30` to `31` if needed.

**Verification:** Run `python3 scripts/validate_repo.py`; expected: `validation passed`.

## Task 4: Full local verification

**Objective:** Prove the docs-only guard did not regress the static kit.

**Commands:**
- `git diff --check`
- `python3 scripts/validate_repo.py`
- `python3 scripts/test_all.py`
- risk scan for live wallet/send/private-key surfaces in changed files.

## Task 5: Browser smoke

**Objective:** Verify the new page renders in the docs viewer and homepage has no console errors.

**Commands:**
1. Start local server: `python3 -m http.server 8080`.
2. Open `http://127.0.0.1:8080/docs/view.html#arc-testnet-send-readiness-gate.md`.
3. Assert title/heading contains `Arc Testnet Send Readiness Gate` and body contains `eth_sendTransaction remains forbidden`.
4. Open `http://127.0.0.1:8080/` and assert no console errors.
5. Kill the server.

## Task 6: PR, CI, merge, Pages verification

**Objective:** Land the narrow guard-only PR.

**Commands:**
- `git add ... && git commit -m "docs: add Arc Testnet send readiness gate"`
- `git push -u origin HEAD`
- Create PR with Safety section: docs-only, Arc-only, no wallet connection, no backend call, no private-key handling, no signing, no broadcast.
- Wait for checks.
- Merge only after CI is green.
- Pull `main`, run local validation, and smoke the deployed Pages URL for the new docs-viewer hash.
