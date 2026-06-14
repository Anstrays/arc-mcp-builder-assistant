# Arc Builder Doctor

One safe command that tells a new builder whether their local clone, Arc
Testnet facts, examples, and public builder-kit boundaries are healthy.

The doctor is an **orchestrator and reporter**, not a second validator. It runs
the existing dependency-free checks, reads their results, and prints a single
structured verdict. It never connects a wallet, never signs, never broadcasts,
and makes **zero network calls by default**.

## Quick start

```bash
# Default: local-only, zero network calls. Exit 0 for pass/warn, non-zero for fail.
python3 scripts/arc_builder_doctor.py

# Machine-readable report (only JSON on stdout; diagnostics on stderr).
python3 scripts/arc_builder_doctor.py --json

# Markdown report for CI summaries or PR comments.
python3 scripts/arc_builder_doctor.py --markdown

# Full local verification (runs the canonical suite once, bounded).
python3 scripts/arc_builder_doctor.py --full

# Opt-in, read-only Arc Testnet RPC chain-id check.
python3 scripts/arc_builder_doctor.py --include-arc-rpc

# Opt-in, read-only public GitHub Pages health check.
python3 scripts/arc_builder_doctor.py --include-public-site

# Treat unavailable *requested* optional checks as failures.
python3 scripts/arc_builder_doctor.py --include-arc-rpc --strict
```

Optional network checks are **opt-in only** and **read-only**. The Arc Testnet
status check uses JSON-RPC `POST`; public-site checks use `GET` against reviewed
public endpoints. They never connect a wallet, never submit a transaction, and
never read `.env`, credentials, or wallet material.

`--json` and `--markdown` are mutually exclusive stdout formats. Markdown table
cells escape HTML and table delimiters before rendering child-check details or
sources. The doctor still writes no files; a caller may explicitly redirect
stdout when it wants to retain a report.

The weekly and manually dispatchable
`.github/workflows/readiness-monitor.yml` job runs the canonical suite, then
publishes a strict read-only Arc RPC and public-site Markdown report to the
GitHub Actions step summary. It has only `contents: read` permission and cannot
deploy Pages, write issues, or post PR comments.

## Report contract (schemaVersion 1)

The `--json` output is a single object with stable field names:

```json
{
  "kind": "arc_builder_doctor_report",
  "schemaVersion": 1,
  "overallStatus": "pass | warn | fail",
  "generatedAt": "ISO-8601 UTC timestamp",
  "mode": {
    "localOnly": true,
    "arcRpcIncluded": false,
    "publicSiteIncluded": false,
    "full": false,
    "strict": false
  },
  "checks": [
    {
      "id": "runtime.python",
      "label": "Python runtime",
      "status": "pass | warn | fail | skip",
      "detail": "concise, redacted explanation",
      "source": "optional reviewed source identifier",
      "durationMs": 0
    }
  ],
  "safety": {
    "walletConnected": false,
    "privateKeysAccepted": false,
    "signingEnabled": false,
    "transactionBroadcast": false,
    "custodyEnabled": false,
    "mainnetEnabled": false,
    "autonomousSpending": false,
    "networkChecksOptIn": true
  }
}
```

### Safety object

Every field is a fixed boolean asserting the doctor's hard boundaries. All are
`false` except `networkChecksOptIn`, which is always `true` because network
checks never run unless explicitly requested.

### Check object fields

- `id` — stable machine-readable identifier.
- `label` — short human-readable name.
- `status` — one of `pass`, `warn`, `fail`, `skip`.
- `detail` — concise, redacted explanation. Never an environment dump, raw
  exception, authorization value, proof, wallet address, or arbitrary child
  output.
- `source` — optional reviewed source identifier (for example the composed
  script name). Never a URL containing credentials.
- `durationMs` — non-negative integer where useful.

The report never includes environment dictionaries, secret-like values, full
credentialed URLs, or Python object reprs.

## Checks

| id | mode | status meaning |
| --- | --- | --- |
| `runtime.python` | default | `fail` if older than the supported minimum. |
| `runtime.node` | default | `warn` if Node.js is unavailable (only the behavioral harnesses need it). |
| `repo.required_files` | default | `fail` if a critical kit file is missing. |
| `repo.clean_safety_markers` | default | composes `scripts/check_completion.py`. |
| `repo.public_claims` | default | composes `scripts/test_public_claims.py`. |
| `repo.live_infrastructure_policy` | default | composes `scripts/validate_live_infrastructure_policy.py`. |
| `repo.arc_testnet_facts` | default | composes the offline `scripts/validate_arc_testnet_facts.py` consistency check. |
| `repo.workflow_security` | default | composes `scripts/test_workflow_security.py`. |
| `repo.canonical_suite` | `--full` | composes `scripts/test_all.py`. |
| `arc_testnet.read_only_status` | `--include-arc-rpc` | composes `scripts/check_arc_testnet_status.py`; requires chain id `5042002` / `0x4cef52`. |
| `public_site.root` | `--include-public-site` | `GET` the public site root. |
| `public_site.wallet_gate` | `--include-public-site` | `GET` the disabled-by-default wallet-send lab. |
| `public_site.docs_viewer` | `--include-public-site` | `GET` the styled docs viewer. |

Checks run in a deterministic, fixed order. The report lists only the checks
that the selected mode enabled.

## Status rules

- `overallStatus` is `fail` if any enabled check is `fail`, else `warn` if any
  is `warn`, else `pass`. A `skip` never changes the outcome.
- The process exits `0` for `pass`/`warn` and non-zero for `fail`.
- `runtime.node` stays a warning even under `--strict`; Node is optional for the
  static-first kit.
- A wrong Arc Testnet chain id is always a `fail`, regardless of `--strict`.
- `--strict` converts a warning into a failure only when an optional network
  check was **requested** but its endpoint was unavailable or malformed. It
  never enables a network check by itself.

## Boundaries

- Arc Testnet only. No mainnet facts, support, or fallback.
- No custody, private-key input, seed phrases, raw signing, message signing,
  autonomous spending, automatic retry, background tasks, or broadcast.
- No real wallet connection.
- No shell command-string execution; child commands run as argument lists with
  bounded timeouts and bounded captured output.
- No repository files are mutated and no servers are started.
- The default offline facts check reads `config/arc_testnet.facts.json` and
  critical repository surfaces; it does not contact Arc RPC or official docs.

See [`../scripts/arc_builder_doctor.py`](../scripts/arc_builder_doctor.py) for
the implementation and
[`../scripts/test_arc_builder_doctor.py`](../scripts/test_arc_builder_doctor.py)
for the safety-boundary tests.
