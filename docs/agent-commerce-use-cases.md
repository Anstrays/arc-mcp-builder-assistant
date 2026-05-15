# Agent Commerce Use Cases on Arc

This page turns the Arc MCP Builder Assistant from a docs kit into a practical map of stablecoin-native agent workflows. Each use case keeps the same safety posture: the agent prepares context, while the human keeps approval control.

## 1. Research agent pays for API calls

**Scenario:** A research agent needs a paid data endpoint for token, market, or company intelligence.

- Payer: user-controlled wallet or app budget
- Receiver: API provider
- Asset: USDC
- Amount: $0.01-$5 per call or report
- Agent role: prepare request, quote cost, explain source, create payment intent
- Human role: approve, reject, or set a spending cap
- Arc primitive fit: predictable stablecoin payment plus observable transaction status

## 2. Creator payout assistant

**Scenario:** A content lead asks an agent to prepare payouts for editors, translators, designers, or bounty contributors.

- Payer: project treasury or contributor budget
- Receiver: creator wallet
- Asset: USDC or supported stablecoin
- Amount: $10-$500 per payout
- Agent role: convert work logs into payout intents
- Human role: review recipients and approve batch items manually
- Arc primitive fit: low-friction stablecoin settlement and transparent payout records

## 3. Agent job escrow

**Scenario:** A user posts a task for an agent. Funds are escrowed, the agent submits output, and the user approves release.

- Payer: task requester
- Receiver: agent operator or agent wallet
- Asset: USDC
- Amount: task-dependent
- Agent role: accept job, submit result, provide evidence
- Human role: define acceptance criteria and approve payout
- Arc primitive fit: ERC-8183-style job escrow plus event monitoring

## 4. AI service marketplace

**Scenario:** One agent calls another agent for a specialist task such as summarization, enrichment, code review, or data labeling.

- Payer: initiating agent under user-approved limit
- Receiver: specialist agent/service
- Asset: USDC micro-payment
- Amount: cents to dollars
- Agent role: quote, execute, return receipt
- Human role: configure budgets and review exceptions
- Arc primitive fit: agent identity, payments, receipts, and trust signals

## 5. Newsletter or report agent

**Scenario:** A content agent pays for data, builds a report, and logs exactly what sources and costs were used.

- Payer: newsletter operator
- Receiver: data/API providers or researchers
- Asset: USDC
- Amount: per issue or per source
- Agent role: source, purchase, summarize, cite
- Human role: approve spend and publish
- Arc primitive fit: stablecoin-native content operations with auditable spend

## Implementation pattern

All five use cases can start with the same minimal object:

```json
{
  "agent": "Research Agent",
  "recipient": "0xRecipient",
  "asset": "USDC",
  "amount": "5.00",
  "memo": "Paid API call for market report",
  "expiry": "2026-05-30T00:00:00Z",
  "status": "pending_human_approval"
}
```

The first production-quality improvement is not autonomy. It is better review: clear intent data, clear recipient, clear amount, clear status, and clear logs.
