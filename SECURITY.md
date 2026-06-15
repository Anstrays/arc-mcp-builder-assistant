# Security Policy

This repository is an early independent builder resource.

## Do not commit

- private keys
- seed phrases
- wallet files
- API keys
- access tokens
- real user data
- `.env` files

## Demo rules

- Use testnet wallets only.
- Keep human approval in all payment flows.
- Do not build or publish autonomous spending flows without clear safety constraints.
- Do not handle custody or user private keys.
- Keep the guarded wallet lab Arc Testnet only, disabled by default, and limited
  to one manually confirmed transaction attempt per page load.
- Require a top-level browsing context and reject zero-address or pinned-token
  recipients before freezing a guarded transaction.
- Never add a mainnet fallback, raw-key input, automatic retry, or unattended
  signing path to the static site.

## Real-wallet automation refusal

This repository deliberately does **not** support automated real-wallet
transactions. Any tool, script, agent, or CI step must refuse to:

- read, request, inject, or store private keys, seed phrases, keystore files,
  or wallet passwords
- call `personal_sign`, `eth_sign`, typed-data signing, or any signing method
  other than the human-approved `eth_sendTransaction` path in the guarded
  wallet-send gate
- confirm, retry, or submit a transaction on behalf of a user
- add custody, mainnet support, automatic retry, or unattended signing paths
- proceed when chain ID, recipient, amount, calldata, or wallet method does not
  match the reviewed testnet-only intent

Real-wallet smoke tests (even on testnet) must be performed manually by the
wallet owner using a disposable test wallet. The only allowed automation is
read-only validation, static-site serving, and evidence recording after a human
has already submitted a transaction.

## Reporting

Do not open a public issue containing a secret, payment proof, wallet material,
private endpoint, or exploitable vulnerability detail.

Use GitHub's private vulnerability reporting for this repository when it is
available. Otherwise, contact the maintainer privately through the repository
owner's GitHub profile and share only the minimum reproduction needed.

If a credential was exposed, revoke or rotate it before reporting. A git
history edit does not make an already exposed credential safe again.

Public issues are appropriate for non-sensitive hardening ideas after all
secret values and exploit details have been removed.

## Verification

Run the dependency-free local safety and regression checks before opening a
pull request:

```bash
python scripts/check_completion.py
python scripts/test_all.py
```
