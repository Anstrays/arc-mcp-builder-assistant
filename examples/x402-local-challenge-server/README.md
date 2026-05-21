# Local x402 challenge server demo

This example is a production-shaped boundary for a future Arc/Circle/x402 payment verifier. It is intentionally local-only:

- returns an HTTP `402 Payment Required` challenge for `/protected`;
- accepts only an explicit local demo proof shape;
- never opens a wallet, broadcasts transactions, or claims settlement;
- keeps human approval and mainnet disabled by default.

## Run locally

```bash
python3 examples/x402-local-challenge-server/server.py --port 8087
```

In another terminal:

```bash
curl -i http://127.0.0.1:8087/protected
```

The response includes a challenge id. To simulate approval, send:

```bash
curl -i \
  -H 'X-Payment: local-demo:<challenge-id>:0.01' \
  http://127.0.0.1:8087/protected
```

## Boundary contract

The swappable production boundary is the `PaymentVerifier` protocol in `server.py`:

```python
class PaymentVerifier(Protocol):
    def verify(self, proof: str, challenge: Mapping[str, object], config: PaymentConfig) -> VerificationResult:
        ...
```

A real verifier should replace `LocalDemoVerifier` only after these rules are explicit:

- exact supported network and asset, e.g. Arc Testnet USDC;
- recipient address ownership and rotation policy;
- proof format, expiry, replay protection, and nonce storage;
- settlement finality requirements;
- logging and privacy policy for payment proofs;
- failure behavior when the verifier is unavailable.

## Safety posture

This demo is not a mainnet payment processor. `mainnetEnabled` and `transactionBroadcast` remain `false` in both the challenge and receipt. The local proof is only a deterministic UI/API switch for demonstrating the 402 -> proof -> 200 flow.
