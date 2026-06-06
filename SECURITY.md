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
