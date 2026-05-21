## Summary

- Adds a production-shaped but local-only x402 challenge-server boundary with a swappable `PaymentVerifier` interface.
- Documents the dependency-free 402 challenge flow and explicit local demo proof format.
- Adds stdlib regression tests for missing, invalid, and valid `X-Payment` proofs.
- Wires the x402 boundary test into CI and extends dependency-free validation so the demo stays safe-by-default.

## Safety / scope

- No real wallet, verifier service, RPC, backend, or transaction broadcast is enabled.
- The x402 example accepts only `local-demo:<challenge-id>:<amount>` proofs and reports `transactionBroadcast: false` / `mainnetEnabled: false`.
- This is a demo boundary for future Arc/Circle/x402 integration, not production settlement code.

## Test plan

- `python3 scripts/test_x402_boundary.py`
- `python3 scripts/validate_repo.py`

## Suggested commit message

```text
feat: add local x402 payment boundary demo

- add local-only x402 challenge server with verifier interface
- document the safe demo proof flow
- add stdlib tests and validation coverage for the demo boundary
```
