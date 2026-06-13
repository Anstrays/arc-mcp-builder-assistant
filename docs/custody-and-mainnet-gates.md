# Custody and mainnet gates

> Current implementation boundary: non-custodial Arc Testnet browser-wallet
> handoff only. Mainnet remains blocked and custody is not implemented.

## Current honest state

The guarded wallet send lab is a static site. It delegates approval, signing,
and transaction submission to an injected user-controlled wallet. The site
does not receive or store private keys and cannot act as a custodian.

As of June 7, 2026, official Arc network documentation lists Public Testnet
as live and private/public mainnet stages as upcoming. No fake mainnet constants,
guessed endpoints, or chain fallback belong in this repository.

## Mainnet remains blocked

Mainnet enablement requires a separate security review and must not be a flag
flip in the testnet browser page. The future review must verify official,
current Arc sources for:

- chain ID and RPC endpoints;
- explorer and finality behavior;
- native gas and token addresses;
- wallet support and transaction behavior;
- incident response, monitoring, and rollback;
- legal, compliance, and operational ownership.

Until every item exists and is independently reviewed, mainnet remains
blocked. The guarded testnet page must not contain a mainnet profile or
fallback.

## Custody requires a separate system

A custody integration cannot be safely implemented in a static site. It
requires an owned backend or reviewed custody provider, a secret manager or
HSM/MPC boundary, and explicit operator controls.

Minimum custody acceptance gates:

1. Written ownership and threat model.
2. Provider due diligence and separate security review.
3. Secrets held only in a secret manager, HSM, MPC service, or equivalent
   controlled environment.
4. Address, asset, chain, method, and amount allowlists.
5. Per-transaction and cumulative spending limits.
6. Human approval or a narrowly reviewed policy engine.
7. Idempotency, replay protection, nonce handling, and reconciliation.
8. Immutable audit logs that exclude secrets and raw authorization material.
9. Emergency kill switch, credential rotation, and incident runbook.
10. Staged testnet evidence before any production-value transaction.

## Signing boundary

The current page never calls a message-signing method and never handles a raw
private key. The only signing event is the user's decision inside the
external wallet confirmation dialog for the exact frozen transaction.

A future custodial signer or account-abstraction flow must be a separate
service and PR. It must not reuse the static page as a secret-bearing client.

## Transaction broadcast boundary

The guarded page can ask the injected wallet to submit one exact Arc Testnet
transaction after all visible guards pass. It does not call a raw-transaction
broadcast method, does not retry automatically, and does not claim
confirmation from a returned hash.

## Required future evidence

Before custody or mainnet work can be considered complete, reviewers need:

- official current network/provider references;
- architecture and data-flow diagrams;
- secret and key lifecycle;
- policy and spending-limit tests;
- adversarial and failure-path tests;
- testnet transaction evidence;
- monitoring and reconciliation evidence;
- incident, rollback, and credential-rotation drills;
- a separate approval record from the static builder-kit review.

## Machine-readable policy

The committed
[`live-infrastructure-policy.example.json`](../examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json)
captures the current fail-closed state: Arc Testnet browser-wallet handoff is
the active profile, mainnet has no guessed configuration and remains disabled,
and custody remains non-custodial and unimplemented.

Validate it with:

```bash
python scripts/validate_live_infrastructure_policy.py
```

The validator rejects unknown fields, duplicate JSON keys, duplicate custody
gates, and any change that loosens the reviewed Arc Testnet-only policy.

## Official Arc references checked

These gates were last checked on June 7, 2026:

- [Network deployment model](https://docs.arc.network/arc/concepts/deployment-model)
  lists permissionless Public Testnet as live and the mainnet stages as
  upcoming.
- [RPC endpoints](https://docs.arc.network/arc/references/rpc-endpoints)
  confirms chain ID `5042002`, the primary Testnet RPC, and the standard
  Ethereum JSON-RPC surface.
- [Contract addresses](https://docs.arc.network/arc/references/contract-addresses)
  confirms the Arc Testnet USDC ERC-20 interface address.
- [Wallets and contract accounts](https://docs.arc.network/arc/references/wallets-and-contract-accounts)
  describes standard EVM wallet support and external wallet/account providers.
- [Account abstraction](https://docs.arc.network/arc/references/account-abstraction)
  describes the separate smart-account infrastructure surface.
