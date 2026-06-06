# Local x402 challenge server demo

This example is a production-shaped boundary for a future Arc/Circle/x402 payment verifier. It is intentionally local-only:

- returns an HTTP `402 Payment Required` challenge for `/protected`;
- accepts only an explicit local demo proof shape;
- never opens a wallet, broadcasts transactions, or claims settlement;
- keeps human approval and mainnet disabled by default.
- refuses non-loopback HTTP bind hosts and invalid ports.

## Run locally

```bash
python3 examples/x402-local-challenge-server/server.py --port 8087
```

HTTP mode accepts only `127.0.0.1` or `localhost`. Use a separately reviewed
deployment implementation for remote or staging access; do not expose the
deterministic local proof verifier on a network interface.

The server reads safe local overrides from environment variables documented in
[`../../.env.example`](../../.env.example). Defaults stay Arc Testnet only:

```bash
X402_DEMO_AMOUNT=0.05 \
  python3 examples/x402-local-challenge-server/server.py --print-challenge
```

Unsafe overrides are rejected with clear errors: non-Arc network,
`X402_DEMO_MAINNET_ENABLED=true`, non-positive or over-precision amounts, and
malformed `X402_DEMO_PAY_TO` addresses.

In another terminal:

```bash
curl -i http://127.0.0.1:8087/protected
```

The response includes a challenge id plus an `mcpManifest` object with safe paid-agent tool metadata. To simulate approval, send:

```bash
curl -i \
  -H 'X-Payment: local-demo:<challenge-id>:0.01' \
  http://127.0.0.1:8087/protected
```

## MCP-style manifest

The unpaid `402` response includes `mcpManifest`, a machine-readable discovery contract for future agents. It lists the local tool surface, Arc Testnet constants, integer microUSD unit economics, safety flags, and the Circle Gateway/x402 production replacement boundary.

The same local tool surface is available through a dependency-free JSON-RPC/MCP-style stdio mode:

```bash
printf '{"jsonrpc":"2.0","id":"tools","method":"tools/list"}\n' \
  | python3 examples/x402-local-challenge-server/server.py --mcp-stdio
```

Quick JSON helpers:

```bash
python3 examples/x402-local-challenge-server/server.py --print-manifest
python3 examples/x402-local-challenge-server/server.py --print-challenge
python3 examples/x402-local-challenge-server/server.py --verify-payment 'local-demo:<challenge-id>:0.01'
```

These helpers never open wallets, accept private keys, broadcast transactions, or claim settlement.

See [x402 MCP manifest](../../docs/x402-mcp-manifest.md) for the field-by-field walkthrough.

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
