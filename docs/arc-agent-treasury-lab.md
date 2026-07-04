# Arc Agent Treasury Lab

The Arc Agent Treasury Lab is a local product simulator for testing whether a
paid agent can fund its own bounded compute loop without giving the browser a
wallet, custody role, signing capability, or transaction-broadcast path.

## Three product levels

### Level 1: agentic loop

The lab models the operational cycle that makes an agent useful without
constant supervision:

```text
reproduce -> execute -> verify -> repair -> verify
```

Verification failure consumes another explicitly bounded attempt. Exhausted
attempts stop with manual review instead of a success claim.

### Level 2: paid agent

Each reviewed task carries a unique local x402-style receipt ID and quoted
USDC revenue. Replay protection prevents the same request or receipt from
crediting the treasury twice.

### Level 3: self-funding treasury

The policy engine decides whether the paid task can fund its worst-case
compute loop while preserving reserve, daily cap, single-task cap, and minimum
profit. This is a local economic-policy simulation, not autonomous live
spending.

Open:

```text
examples/arc-agent-treasury-lab/index.html
```

Or serve the repository and visit:

```text
http://127.0.0.1:8080/examples/arc-agent-treasury-lab/
```

## Product flow

1. Configure the treasury policy:
   - opening USDC balance;
   - protected reserve;
   - daily compute-spend cap;
   - single-task compute cap;
   - minimum worst-case profit;
   - maximum verification attempts.
2. Enter a paid request with a unique request ID and local x402 receipt ID.
3. Review the request.
4. The policy engine calculates the worst-case compute cost and denies the
   request if any reserve, cap, replay, or profitability rule fails.
5. An approved local receipt credits simulated USDC revenue exactly once.
6. Run the deterministic agentic loop:
   `reproduce -> execute -> verify -> repair`.
7. Inspect the ledger and machine-readable treasury snapshot.

## Why it matters for Arc builders

Arc is designed for stablecoin-native applications and agentic commerce. A
useful paid agent needs more than a payment button: it needs deterministic
unit economics, bounded resource spending, replay protection, verification,
and clear evidence when work fails.

This lab connects those concerns into one reviewable local surface:

```text
x402-style paid request
-> treasury policy
-> bounded compute attempts
-> verification or manual review
-> auditable local receipt and ledger
```

## Policy decisions

The request is denied when any of these conditions applies:

- the request ID was already processed;
- the receipt ID was already accepted;
- worst-case compute exceeds the single-task cap;
- worst-case compute exceeds the remaining daily cap;
- worst-case compute would breach the protected reserve;
- worst-case task profit is below the configured minimum;
- inputs are malformed or exceed the local simulation limits.

All USDC arithmetic uses integer micro-USDC values. JavaScript floating-point
money arithmetic is not used.

## Verification outcomes

- `pass_first`: the first attempt verifies successfully.
- `fail_then_pass`: the first verification fails, a repair stage runs, and the
  second attempt verifies successfully.
- `exhaust_retries`: every allowed attempt fails; the lab emits no success
  claim and marks the paid task for manual refund review.

The runtime performs a fresh spend preflight before every attempt. If policy
state changes after review, the next attempt fails closed before compute spend.

## Safety boundary

- Local simulation only.
- Arc Testnet constants are descriptive policy context only.
- No wallet connection.
- No private keys or seed phrases.
- No custody.
- No mainnet.
- No autonomous live spending.
- No signing.
- No backend or network request.
- No settlement claim.
- No transaction broadcast.

The accepted receipt intentionally keeps `settled=false` and
`transactionBroadcast=false`. A real x402 verifier, wallet, compute provider,
refund path, custody design, or mainnet deployment requires a separate
security-reviewed backend project.

## Verification

Run the focused test:

```bash
python scripts/test_arc_agent_treasury_lab.py
```

Run the full repository suite:

```bash
python scripts/test_all.py
```

The focused test executes the actual treasury domain JavaScript in a
dependency-free Node harness and covers exact micro-USDC arithmetic, profitable
repair loops, replay denial, spend caps, reserve protection, minimum profit,
retry exhaustion, and runtime fail-closed behavior.
