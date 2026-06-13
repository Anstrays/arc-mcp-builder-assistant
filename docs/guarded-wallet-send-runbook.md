# Guarded Arc Testnet wallet send runbook

> This runbook covers the repository's only write-capable browser surface. It
> is Arc Testnet only, disabled by default, and intended for a human operating
> an injected user-controlled browser wallet.

## Scope

The guarded send lab demonstrates a narrow transaction-broadcast adapter for
one manually reviewed Arc Testnet USDC transfer. The wallet confirmation dialog is the only signing path. The page never receives a private key, seed
phrase, custody credential, or raw signed transaction.

The implementation deliberately does not change the existing local-only
payment-intent playground. Builders can continue to use that playground
without any wallet request or write capability.

## Enablement

Serve the repository locally:

```bash
python -m http.server 8080
```

Open the guarded page with the exact reviewed-testnet query gate:

```text
http://localhost:8080/examples/arc-testnet-wallet-send-gate/?enableArcTestnetSend=reviewed-testnet-only
```

The query gate alone does nothing. The operator must also acknowledge the
risk, open the page in a top-level browsing context, explicitly connect an
injected wallet, prove Arc Testnet, freeze the intent, type the exact
confirmation phrase, check the final confirmation, and click the transaction
request button.

## Enforced transaction shape

- Network: Arc Testnet only.
- Chain ID: `5042002` / `0x4cef52`.
- RPC metadata: `https://rpc.testnet.arc.network`.
- Explorer: `https://testnet.arcscan.app`.
- Token target: Arc Testnet USDC
  `0x3600000000000000000000000000000000000000`.
- Token decimals: `6`.
- Native transaction value: `0x0`.
- Method: deterministic ERC-20 `transfer(address,uint256)`.
- Amount cap: `1.00` USDC.
- Recipient must be non-zero and cannot equal the pinned USDC token contract.
- Expiry: future and within 24 hours.
- One attempt per page load.
- No automatic retry.

## Operator sequence

1. Use a dedicated test wallet with only disposable testnet assets.
2. Confirm the page is served from the expected local or reviewed Pages URL.
3. Confirm the exact query gate and risk acknowledgement are visible.
4. Connect the injected user-controlled browser wallet manually.
5. Switch or add Arc Testnet through the explicit button.
6. Verify the connected account and chain ID shown by the page.
7. Enter a non-zero recipient, an amount no greater than `1.00` USDC, a
   visible memo, and a short expiry.
8. Freeze the intent and compare the rendered transaction request with the
   entered fields.
9. Confirm the token target, zero native value, decoded recipient, and decoded
   base-unit amount.
10. Type `SEND ARC TESTNET USDC` and check the final confirmation.
11. Click the transaction request button once.
12. Re-check every field in the external wallet confirmation dialog.
13. Reject the wallet prompt if any field differs or is unclear.
14. Treat a returned transaction hash as submitted/pending until a separate
    read-only status check proves its result.

## Stop conditions

Stop and reload without sending when:

- the page is embedded in a frame instead of opened as a top-level tab;
- the connected chain is not exactly `0x4cef52`;
- the connected account changes;
- the connected account is the zero address;
- the recipient is the zero address or the pinned USDC token contract;
- recipient, amount, memo, or expiry changes after freeze;
- decoded calldata differs from the frozen intent;
- the token target or native value differs;
- any unexpected wallet method appears in the method-name log;
- any secret, opaque proof, or authorization data appears in the UI or logs;
- the page shows an error or the wallet request is rejected.

There is no retry button after a transaction attempt. This is intentional.

## Rollback

Rollback is immediate and static:

1. Remove access to the guarded URL or revert the guarded-send change.
2. Keep the local-only payment-intent playground available.
3. Preserve the one-attempt lock and default-disabled query gate.
4. Review the method-name log and transaction hash without publishing wallet
   payloads or private account data.
5. Re-run `python scripts/test_all.py` before restoring the page.

## Verification boundary

Automated tests verify the source guards and disabled-by-default browser
state. They do not connect a wallet, sign, broadcast, or spend testnet assets.
Any manual transaction remains an explicit human operation outside CI.

The canonical suite also executes the real guarded-send JavaScript inside a
dependency-free Node fake-provider harness:

```bash
python scripts/test_arc_testnet_wallet_send_behavior.py
```

It covers the default lock, zero startup requests, exact deterministic
`eth_sendTransaction` payload, double-click one-shot behavior, wrong-chain and
account-change blocks, and the rejection lock. It does not emulate wallet-vendor
UI or prove that a transaction was confirmed.

The machine-readable
[`live-infrastructure-policy.example.json`](../examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json)
keeps the current Arc Testnet, signing, broadcast, custody, and mainnet gates
reviewable by another agent or CI job.
