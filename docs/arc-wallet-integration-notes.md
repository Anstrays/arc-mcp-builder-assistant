# Arc Testnet Wallet Integration Notes

> Scope: choose the safest wallet path for the next payment-intent prototype step. This is not a live payment implementation and does not require or store Circle API keys, Entity Secrets, OTP codes, seed phrases, or private keys.

## Source-grounded facts

Sources checked for this note:

- Arc docs index: `https://docs.arc.network/llms.txt`
- Arc connect reference: `https://docs.arc.io/arc/references/connect-to-arc.md`
- Arc contract addresses reference: `https://docs.arc.io/arc/references/contract-addresses.md`
- Circle docs index: `https://developers.circle.com/llms.txt`
- Circle Wallets overview / infrastructure models: `https://developers.circle.com/wallets.md`
- Circle account types: `https://developers.circle.com/wallets/account-types.md`
- Circle Dev-Controlled Wallets overview: `https://developers.circle.com/wallets/dev-controlled.md`
- Circle Dev-Controlled Wallet quickstart: `https://developers.circle.com/wallets/dev-controlled/create-your-first-wallet.md`
- Circle Wallets supported blockchains: `https://developers.circle.com/wallets/supported-blockchains.md`

Confirmed constants and compatibility:

- Arc Testnet chain ID: `5042002` / `0x4cef52`.
- Public RPC: `https://rpc.testnet.arc.network`.
- Explorer: `https://testnet.arcscan.app`.
- Faucet: `https://faucet.circle.com`.
- Native gas asset: USDC with native-gas 18-decimal accounting.
- ERC-20 USDC on Arc Testnet: `0x3600000000000000000000000000000000000000` with 6 decimals.
- Circle Wallets supported blockchains lists Arc Testnet as `ARC-TESTNET` and shows support for EOA, SCA, and MSCA.
- Circle's Dev-Controlled Wallet quickstart creates an Arc Testnet wallet with `blockchains: ["ARC-TESTNET"]` and `accountType: "EOA"`, with SCA also available.

## Wallet options for this repository

### 1. Browser wallet / external signer

Best first write path for a public static demo because the user keeps custody and explicitly approves the transaction in their wallet.

Use when:

- the app only builds and displays a payment intent;
- the user must review chain, recipient, amount, memo, and expiry before signing;
- transaction submission remains a manual wallet action.

Guardrails:

- Require Arc Testnet chain ID before enabling any signing UI.
- Never mutate the recipient or amount after the user starts review.
- Keep the current local simulator available when no wallet is connected.
- Store only public receipt fields: chain ID, sender address, recipient, token address, amount, transaction hash, explorer URL, and timestamps.

### 2. Circle Dev-Controlled Wallet — EOA

Useful for backend-run payouts, agent wallets, automation, or demos where the developer intentionally controls the wallet. Circle docs describe this as a server-side/custodial model: your application controls wallet creation, transaction execution, and signing through Circle APIs/SDKs.

Use only when:

- there is a backend service, not a static browser-only page;
- Circle API key and Entity Secret stay outside the repository and outside chat;
- the user explicitly chooses custodial/developer-controlled semantics;
- spending policies, idempotency, audit logs, and manual approval gates are defined.

Do not use it as the default for end-user payment approval in this public builder kit because it changes custody assumptions.

### 3. Circle Dev-Controlled Wallet — SCA

Useful when backend-controlled wallets need smart-account features such as gas sponsorship or batch execution. Circle docs list Arc Testnet SCA support and describe SCA as a smart-contract account with gas sponsorship/batch capabilities.

Use only after the EOA flow is understood and the project needs one of:

- sponsored gas;
- batch operations;
- policy-controlled backend automation;
- more explicit account abstraction demos.

Important caveat: SCA deployment gas may occur on the first outbound transaction. Treat this as a write path requiring manual review and testnet funding.

### 4. User-Controlled or Modular Wallets

Use for a product where users own and approve transactions through embedded auth/passkeys. This can be better for a consumer-facing app, but it is a larger integration than the current static/local builder kit.

Do not mix this into the first write-path PR unless the goal is specifically embedded user wallets.

## Recommended next implementation sequence

1. Keep `examples/payment-intent-playground/` local-first and unchanged by default.
2. Add an optional read-only network panel fed by `scripts/check_arc_testnet_status.py` or equivalent browser-side read-only RPC calls.
3. Add data-model fields for network readiness:
   - `chainId`
   - `chainIdHex`
   - `rpcUrl`
   - `explorerUrl`
   - `assetAddress`
   - `assetDecimals`
   - `nativeGasDecimals`
   - `statusSource`
4. Add disabled wallet/signing controls with exact failure reasons:
   - wrong chain;
   - RPC unavailable;
   - unverified docs/constants;
   - missing recipient;
   - invalid amount or decimals;
   - expired intent;
   - user approval required.
5. Only after review, add a separate browser-wallet signing PR. It must be feature-flagged and testnet-only.
6. Treat Circle Dev-Controlled Wallet as a separate backend track, not as the first public static-site path.

## Secret and credential boundary

Never commit or paste:

- `CIRCLE_API_KEY`;
- `CIRCLE_ENTITY_SECRET`;
- Entity Secret ciphertexts;
- OTP codes;
- wallet private keys;
- seed phrases;
- session tokens;
- funded wallet IDs if the surrounding context exposes sensitive operations.

Allowed in docs/examples:

- placeholder names such as `CIRCLE_API_KEY=[REDACTED]`;
- public Arc Testnet constants;
- public token contract addresses;
- public transaction hashes from intentionally shared testnet demos.

## Backend-only Circle Dev-Controlled Wallet checklist

Before implementing a Circle Dev-Controlled Wallet backend, confirm all of these:

- [ ] The user explicitly accepts the custodial/developer-controlled wallet model.
- [ ] API key and Entity Secret are provisioned outside the repo.
- [ ] `.env*` files are ignored and never uploaded.
- [ ] Idempotency keys are used for wallet/transaction creation.
- [ ] Transaction requests include immutable recipient, amount, asset, chain, and memo fields.
- [ ] Human approval is required before any transfer or contract execution.
- [ ] Testnet-only chain code `ARC-TESTNET` is enforced.
- [ ] Mainnet fallback is impossible.
- [ ] Logs redact API keys, Entity Secrets, OTPs, and raw request authorization headers.
- [ ] Transaction state is stored as public receipt metadata, not as secret wallet material.

## Implemented decision for the current builder kit

The current guarded slice uses a browser wallet plus separate read-only status UI:

- show Arc Testnet readiness in the local playground;
- keep the local playground transaction controls disabled;
- isolate one manually reviewed transaction request in the separate guarded Arc Testnet lab;
- do not add Circle backend credentials;
- do not add automatic retry, background broadcast, custody, or mainnet;
- add tests around chain/decimals/amount/recipient/expiry validation.

Circle Dev-Controlled Wallet notes should remain a documented backend option until the project intentionally moves beyond static GitHub Pages and local demos.
