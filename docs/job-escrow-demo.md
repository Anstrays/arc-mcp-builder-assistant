# Agent Job Escrow Demo

The payment-intent demo covers one direct request. The next stronger primitive is a job escrow flow: a user posts work, an agent accepts, funds are reserved, and payout happens only after review.

## Goal

Design a safe Arc Testnet demo for agentic commerce where an AI agent can earn a stablecoin payout without receiving private keys or autonomous spending authority.

## Actors

- **Requester:** human user who defines the job and funds the payment.
- **Agent:** AI or agent service that accepts the job and submits output.
- **Reviewer:** human user or configured reviewer who accepts or rejects the result.
- **Escrow/status layer:** Arc Testnet contracts, logs, or a local simulator until the contract integration is verified.

## Flow

1. Requester creates a job with title, task, budget, expiry, and acceptance criteria.
2. App shows reviewable JSON before any onchain action.
3. Requester manually approves funding the job escrow.
4. Agent accepts the job and receives the task context.
5. Agent submits output plus evidence URI or notes.
6. Reviewer approves, requests changes, or rejects.
7. On approval, payout is released to the agent recipient.
8. App records status changes and links to ArcScan when available.

## Minimal job object

```json
{
  "jobId": "job_001",
  "title": "Summarize Arc MCP docs for wallet setup",
  "requester": "0xRequester",
  "agent": "Research Agent",
  "recipient": "0xAgentRecipient",
  "asset": "USDC",
  "budget": "10.00",
  "expiry": "2026-05-30T00:00:00Z",
  "acceptanceCriteria": [
    "Cite docs used",
    "List chain and wallet assumptions",
    "Flag unknowns instead of guessing"
  ],
  "status": "draft"
}
```

## Status model

- `draft`
- `pending_funding_approval`
- `funded`
- `accepted_by_agent`
- `submitted_for_review`
- `changes_requested`
- `approved_for_release`
- `paid`
- `expired`
- `cancelled`

## Safety boundaries

- No private-key handling in the app.
- No autonomous mainnet spending in v0.
- Human approval is required for funding and release.
- Agent output is treated as untrusted until reviewed.
- Contract addresses and event names must be re-verified through Arc docs or MCP before implementation.

## Build path

1. Add a static UI card for the job object.
2. Add a local simulator for status transitions, including change requests and resubmission before payout approval.
3. Add Arc MCP query examples for ERC-8183/job escrow docs.
4. Add testnet integration only after the current contract path and wallet flow are confirmed.
5. Publish a build log with what was verified and what remains unknown.
