#!/usr/bin/env python3
"""Arc Builder Doctor: one safe local health command for the builder kit.

This script is an orchestrator and reporter, not a second validator. It runs the
existing dependency-free checks, reads their results, and prints a single
structured verdict. It is Python-standard-library only.

Hard boundaries (see docs/arc-builder-doctor.md):
- Arc Testnet only; no mainnet facts, support, or fallback.
- No wallet connection, private-key input, signing, or transaction broadcast.
- Zero network calls by default; network checks are opt-in and read-only.
- No shell command-string execution; children run as argument lists.
- No repository files are mutated and no servers are started.
"""

from __future__ import annotations

import argparse
import http.client as http_client
import html
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

KIND = "arc_builder_doctor_report"
SCHEMA_VERSION = 1

STATUS_PASS = "pass"
STATUS_WARN = "warn"
STATUS_FAIL = "fail"
STATUS_SKIP = "skip"
VALID_STATUSES = (STATUS_PASS, STATUS_WARN, STATUS_FAIL, STATUS_SKIP)

MIN_PYTHON = (3, 9)
MIN_NODE_MAJOR = 18

EXPECTED_CHAIN_ID_DECIMAL = 5042002
EXPECTED_CHAIN_ID_HEX = "0x4cef52"

CANONICAL_BASE_URL = "https://anstrays.github.io/arc-mcp-builder-assistant/"
ALLOWED_PUBLIC_HOST = "anstrays.github.io"

# Bounds. Children run as argument lists with explicit timeouts and the captured
# output is truncated so a noisy or hostile child cannot flood the report.
QUICK_CHILD_TIMEOUT = 60
FULL_CHILD_TIMEOUT = 300
NODE_VERSION_TIMEOUT = 15
DEFAULT_NETWORK_TIMEOUT = 10
MAX_NETWORK_TIMEOUT = 30
MAX_CHILD_CAPTURE = 4000
MAX_NETWORK_BYTES = 1_000_000
DETAIL_LIMIT = 240

# Critical builder-kit files the doctor itself depends on. This is an
# orchestrator-level sanity list, not a copy of the full completion contract.
CRITICAL_FILES = (
    "README.md",
    "SECURITY.md",
    "scripts/arc_builder_doctor.py",
    "scripts/test_arc_builder_doctor.py",
    "docs/arc-builder-doctor.md",
    "scripts/test_all.py",
    "scripts/check_completion.py",
    "scripts/validate_repo.py",
    "scripts/check_arc_testnet_status.py",
    "config/arc_testnet.facts.json",
    "scripts/validate_arc_testnet_facts.py",
    "scripts/test_arc_testnet_facts.py",
    "scripts/test_public_claims.py",
    "scripts/validate_live_infrastructure_policy.py",
    "scripts/test_workflow_security.py",
    "examples/arc-testnet-wallet-send-gate/index.html",
    "examples/arc-testnet-wallet-send-gate/wallet-send-gate.js",
    "examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json",
)

_REDACTED = "[redacted]"

# Patterns for credential-like material that must never reach the report. These
# are detection rules, not real credentials; they are written so they do not
# themselves match the repository secret scanner.
_REDACTION_RULES = (
    re.compile(r"gh[oprsu]_[A-Za-z0-9_]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b0x[0-9a-fA-F]{40,}\b"),
    re.compile(r"\b[0-9a-fA-F]{64,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?i)\bauthorization\b\s*[:=]\s*\S+"),
    re.compile(
        r"(?i)(?:api[_-]?key|secret|token|password|private[_-]?key|entity[_-]?secret)"
        r"\s*[:=]\s*\S{6,}"
    ),
)


class ForeignRedirectError(Exception):
    """Raised when a public-site request is redirected to an unreviewed host."""


class OversizedResponseError(Exception):
    """Raised when a public-site response exceeds the reviewed size bound."""


def redact(text: str) -> str:
    """Replace credential-like substrings with a fixed marker."""
    if not text:
        return ""
    for rule in _REDACTION_RULES:
        text = rule.sub(_REDACTED, text)
    return text


def safe_detail(text: str, limit: int = DETAIL_LIMIT) -> str:
    """Redact, collapse whitespace, and bound a human-facing detail string."""
    collapsed = " ".join(redact(text).split())
    if len(collapsed) > limit:
        collapsed = collapsed[: limit - 3].rstrip() + "..."
    return collapsed


def make_check(
    check_id: str,
    label: str,
    status: str,
    detail: str,
    *,
    source: str | None = None,
    duration_ms: int = 0,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid check status for {check_id}: {status!r}")
    check: dict[str, Any] = {
        "id": check_id,
        "label": label,
        "status": status,
        "detail": safe_detail(detail),
        "durationMs": max(0, int(duration_ms)),
    }
    if source:
        check["source"] = source
    return check


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


class ChildResult:
    __slots__ = ("returncode", "stdout", "stderr", "timed_out")

    def __init__(self, returncode: int, stdout: str, stderr: str, timed_out: bool) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out

    def summary_line(self) -> str:
        for stream in (self.stdout, self.stderr):
            for line in reversed(stream.splitlines()):
                if line.strip():
                    return line.strip()
        return ""


def run_child(argv: list[str], timeout: int) -> ChildResult:
    """Run a child process as an argument list with a bounded timeout.

    No shell is involved and captured output is truncated. A timeout produces a
    fail-closed ChildResult rather than hanging.
    """
    try:
        completed = subprocess.run(
            argv,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ChildResult(returncode=124, stdout="", stderr="", timed_out=True)
    except (OSError, ValueError) as exc:
        return ChildResult(returncode=125, stdout="", stderr=str(exc), timed_out=False)
    stdout = (completed.stdout or "")[:MAX_CHILD_CAPTURE]
    stderr = (completed.stderr or "")[:MAX_CHILD_CAPTURE]
    return ChildResult(returncode=completed.returncode, stdout=stdout, stderr=stderr, timed_out=False)


def _fetch_public(url: str, timeout: int, max_bytes: int) -> tuple[int, str]:
    """GET a reviewed public URL, rejecting redirects to unreviewed hosts."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_PUBLIC_HOST:
        raise ForeignRedirectError(f"refusing non-allowlisted URL host: {parsed.hostname}")

    handler = _HostPinnedRedirectHandler()
    opener = urllib_request.build_opener(handler)
    request = urllib_request.Request(
        url,
        method="GET",
        headers={"User-Agent": "arc-builder-doctor", "Accept": "text/html"},
    )
    with opener.open(request, timeout=timeout) as response:
        final_host = urlparse(response.geturl()).hostname
        if final_host != ALLOWED_PUBLIC_HOST:
            raise ForeignRedirectError(f"redirected to unreviewed host: {final_host}")
        status = int(getattr(response, "status", 0) or 0)
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise OversizedResponseError("public response exceeded the 1 MB safety limit")
    return status, raw.decode("utf-8", "replace")


class _HostPinnedRedirectHandler(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        if urlparse(newurl).hostname != ALLOWED_PUBLIC_HOST:
            raise ForeignRedirectError(f"redirect to unreviewed host: {urlparse(newurl).hostname}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Options:
    def __init__(
        self,
        *,
        full: bool = False,
        include_arc_rpc: bool = False,
        include_public_site: bool = False,
        strict: bool = False,
        network_timeout: int = DEFAULT_NETWORK_TIMEOUT,
    ) -> None:
        self.full = full
        self.include_arc_rpc = include_arc_rpc
        self.include_public_site = include_public_site
        self.strict = strict
        self.network_timeout = max(1, min(MAX_NETWORK_TIMEOUT, int(network_timeout)))

    def optional_unavailable_status(self) -> str:
        return STATUS_FAIL if self.strict else STATUS_WARN


# --- individual checks --------------------------------------------------------


def check_python(options: Options) -> dict[str, Any]:
    start = time.monotonic()
    version = sys.version_info
    ok = (version.major, version.minor) >= MIN_PYTHON
    detail = f"Python {version.major}.{version.minor}.{version.micro}"
    if not ok:
        detail += f"; requires >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    return make_check(
        "runtime.python",
        "Python runtime",
        STATUS_PASS if ok else STATUS_FAIL,
        detail,
        duration_ms=_elapsed_ms(start),
    )


def check_node(options: Options) -> dict[str, Any]:
    start = time.monotonic()
    node = shutil.which("node")
    if not node:
        return make_check(
            "runtime.node",
            "Node.js runtime",
            STATUS_WARN,
            "Node.js not found; behavioral harnesses are skipped (no npm install needed)",
            duration_ms=_elapsed_ms(start),
        )
    result = run_child([node, "--version"], NODE_VERSION_TIMEOUT)
    if result.timed_out or result.returncode != 0:
        return make_check(
            "runtime.node",
            "Node.js runtime",
            STATUS_WARN,
            "Node.js present but version probe failed",
            duration_ms=_elapsed_ms(start),
        )
    text = result.stdout.strip()
    match = re.match(r"v(\d+)\.", text)
    major = int(match.group(1)) if match else 0
    if major >= MIN_NODE_MAJOR:
        return make_check(
            "runtime.node",
            "Node.js runtime",
            STATUS_PASS,
            f"Node.js {text}",
            duration_ms=_elapsed_ms(start),
        )
    return make_check(
        "runtime.node",
        "Node.js runtime",
        STATUS_WARN,
        f"Node.js {text} is older than the recommended {MIN_NODE_MAJOR}+",
        duration_ms=_elapsed_ms(start),
    )


def check_required_files(options: Options) -> dict[str, Any]:
    start = time.monotonic()
    missing = [relative for relative in CRITICAL_FILES if not (ROOT / relative).is_file()]
    if missing:
        return make_check(
            "repo.required_files",
            "Required builder-kit files",
            STATUS_FAIL,
            f"missing {len(missing)} critical file(s): " + ", ".join(missing[:5]),
            duration_ms=_elapsed_ms(start),
        )
    return make_check(
        "repo.required_files",
        "Required builder-kit files",
        STATUS_PASS,
        f"{len(CRITICAL_FILES)} critical files present",
        duration_ms=_elapsed_ms(start),
    )


def _python_script_check(
    check_id: str,
    label: str,
    script_relative: str,
    *,
    timeout: int = QUICK_CHILD_TIMEOUT,
    args: Iterable[str] = (),
) -> dict[str, Any]:
    start = time.monotonic()
    argv = [sys.executable, str(ROOT / script_relative), *args]
    result = run_child(argv, timeout)
    if result.timed_out:
        return make_check(
            check_id,
            label,
            STATUS_FAIL,
            f"{script_relative} timed out after {timeout}s",
            source=script_relative,
            duration_ms=_elapsed_ms(start),
        )
    if result.returncode == 0:
        return make_check(
            check_id,
            label,
            STATUS_PASS,
            result.summary_line() or "passed",
            source=script_relative,
            duration_ms=_elapsed_ms(start),
        )
    return make_check(
        check_id,
        label,
        STATUS_FAIL,
        f"exit {result.returncode}: {result.summary_line()}",
        source=script_relative,
        duration_ms=_elapsed_ms(start),
    )


def check_clean_safety_markers(options: Options) -> dict[str, Any]:
    return _python_script_check(
        "repo.clean_safety_markers",
        "Safe-scope completion markers",
        "scripts/check_completion.py",
    )


def check_public_claims(options: Options) -> dict[str, Any]:
    return _python_script_check(
        "repo.public_claims",
        "Public claims boundaries",
        "scripts/test_public_claims.py",
    )


def check_live_infrastructure_policy(options: Options) -> dict[str, Any]:
    return _python_script_check(
        "repo.live_infrastructure_policy",
        "Live infrastructure policy",
        "scripts/validate_live_infrastructure_policy.py",
    )


def check_arc_testnet_facts(options: Options) -> dict[str, Any]:
    return _python_script_check(
        "repo.arc_testnet_facts",
        "Arc Testnet facts consistency",
        "scripts/validate_arc_testnet_facts.py",
    )


def check_workflow_security(options: Options) -> dict[str, Any]:
    return _python_script_check(
        "repo.workflow_security",
        "GitHub Actions workflow security",
        "scripts/test_workflow_security.py",
    )


def check_canonical_suite(options: Options) -> dict[str, Any]:
    return _python_script_check(
        "repo.canonical_suite",
        "Canonical regression suite",
        "scripts/test_all.py",
        timeout=FULL_CHILD_TIMEOUT,
    )


def check_arc_testnet_status(options: Options) -> dict[str, Any]:
    start = time.monotonic()
    unavailable = options.optional_unavailable_status()
    argv = [
        sys.executable,
        str(ROOT / "scripts/check_arc_testnet_status.py"),
        "--timeout",
        str(options.network_timeout),
    ]
    result = run_child(argv, options.network_timeout + 10)
    source = "scripts/check_arc_testnet_status.py"
    if result.timed_out:
        return make_check(
            "arc_testnet.read_only_status",
            "Arc Testnet read-only status",
            unavailable,
            "Arc Testnet RPC timed out",
            source=source,
            duration_ms=_elapsed_ms(start),
        )
    try:
        payload = json.loads(result.stdout)
    except (ValueError, TypeError):
        return make_check(
            "arc_testnet.read_only_status",
            "Arc Testnet read-only status",
            unavailable,
            "Arc Testnet RPC returned malformed output",
            source=source,
            duration_ms=_elapsed_ms(start),
        )
    status_obj = payload.get("status") if isinstance(payload, dict) else None
    if isinstance(status_obj, dict) and "chainIdDecimal" in status_obj:
        chain_decimal = status_obj.get("chainIdDecimal")
        chain_hex = status_obj.get("chainIdHex")
        if chain_decimal == EXPECTED_CHAIN_ID_DECIMAL and chain_hex == EXPECTED_CHAIN_ID_HEX:
            if result.returncode != 0 or payload.get("ok") is not True:
                return make_check(
                    "arc_testnet.read_only_status",
                    "Arc Testnet read-only status",
                    unavailable,
                    "Arc Testnet status helper did not confirm success",
                    source=source,
                    duration_ms=_elapsed_ms(start),
                )
            return make_check(
                "arc_testnet.read_only_status",
                "Arc Testnet read-only status",
                STATUS_PASS,
                f"Arc Testnet chain {chain_decimal} ({chain_hex})",
                source=source,
                duration_ms=_elapsed_ms(start),
            )
        return make_check(
            "arc_testnet.read_only_status",
            "Arc Testnet read-only status",
            STATUS_FAIL,
            f"unexpected chain id: {chain_decimal} ({chain_hex}); "
            f"expected {EXPECTED_CHAIN_ID_DECIMAL} ({EXPECTED_CHAIN_ID_HEX})",
            source=source,
            duration_ms=_elapsed_ms(start),
        )
    return make_check(
        "arc_testnet.read_only_status",
        "Arc Testnet read-only status",
        unavailable,
        "Arc Testnet RPC unavailable",
        source=source,
        duration_ms=_elapsed_ms(start),
    )


_PUBLIC_SITE_TARGETS = (
    ("public_site.root", "Public site root", CANONICAL_BASE_URL, ("Arc MCP Builder Assistant",)),
    (
        "public_site.wallet_gate",
        "Public wallet-send lab",
        CANONICAL_BASE_URL + "examples/arc-testnet-wallet-send-gate/",
        ("Arc Testnet", "Disabled by default"),
    ),
    (
        "public_site.docs_viewer",
        "Public docs viewer",
        CANONICAL_BASE_URL + "docs/view.html",
        ("Arc MCP Builder Assistant",),
    ),
)


def _check_public_site_target(
    options: Options,
    check_id: str,
    label: str,
    url: str,
    markers: tuple[str, ...],
) -> dict[str, Any]:
    start = time.monotonic()
    unavailable = options.optional_unavailable_status()
    try:
        status, body = _fetch_public(url, options.network_timeout, MAX_NETWORK_BYTES)
    except ForeignRedirectError:
        return make_check(
            check_id,
            label,
            STATUS_FAIL,
            "rejected redirect to unreviewed host",
            source=url,
            duration_ms=_elapsed_ms(start),
        )
    except OversizedResponseError:
        return make_check(
            check_id,
            label,
            STATUS_FAIL,
            "public response exceeded the 1 MB safety limit",
            source=url,
            duration_ms=_elapsed_ms(start),
        )
    except (urllib_error.URLError, http_client.HTTPException, TimeoutError, OSError, ValueError) as exc:
        return make_check(
            check_id,
            label,
            unavailable,
            f"public site unavailable: {exc.__class__.__name__}",
            source=url,
            duration_ms=_elapsed_ms(start),
        )
    if status != 200:
        return make_check(
            check_id,
            label,
            unavailable,
            f"unexpected HTTP status {status}",
            source=url,
            duration_ms=_elapsed_ms(start),
        )
    if any(marker not in body for marker in markers):
        return make_check(
            check_id,
            label,
            unavailable,
            "expected public safety marker missing",
            source=url,
            duration_ms=_elapsed_ms(start),
        )
    return make_check(
        check_id,
        label,
        STATUS_PASS,
        "HTTP 200 with expected public markers",
        source=url,
        duration_ms=_elapsed_ms(start),
    )


def check_public_site(options: Options) -> list[dict[str, Any]]:
    return [
        _check_public_site_target(options, check_id, label, url, markers)
        for check_id, label, url, markers in _PUBLIC_SITE_TARGETS
    ]


# --- assembly -----------------------------------------------------------------

_DEFAULT_CHECKS: tuple[Callable[[Options], dict[str, Any]], ...] = (
    check_python,
    check_node,
    check_required_files,
    check_clean_safety_markers,
    check_public_claims,
    check_live_infrastructure_policy,
    check_arc_testnet_facts,
    check_workflow_security,
)


def collect_checks(options: Options) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = [runner(options) for runner in _DEFAULT_CHECKS]
    if options.full:
        checks.append(check_canonical_suite(options))
    if options.include_arc_rpc:
        checks.append(check_arc_testnet_status(options))
    if options.include_public_site:
        checks.extend(check_public_site(options))
    for check in checks:
        if check["status"] not in VALID_STATUSES:
            raise ValueError(f"check {check.get('id')} produced invalid status")
    return checks


def overall_status(checks: list[dict[str, Any]]) -> str:
    statuses = {check["status"] for check in checks}
    if STATUS_FAIL in statuses:
        return STATUS_FAIL
    if STATUS_WARN in statuses:
        return STATUS_WARN
    return STATUS_PASS


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_report(options: Options) -> dict[str, Any]:
    checks = collect_checks(options)
    return {
        "kind": KIND,
        "schemaVersion": SCHEMA_VERSION,
        "overallStatus": overall_status(checks),
        "generatedAt": _generated_at(),
        "mode": {
            "localOnly": not (options.include_arc_rpc or options.include_public_site),
            "arcRpcIncluded": options.include_arc_rpc,
            "publicSiteIncluded": options.include_public_site,
            "full": options.full,
            "strict": options.strict,
        },
        "checks": checks,
        "safety": {
            "walletConnected": False,
            "privateKeysAccepted": False,
            "signingEnabled": False,
            "transactionBroadcast": False,
            "custodyEnabled": False,
            "mainnetEnabled": False,
            "autonomousSpending": False,
            "networkChecksOptIn": True,
        },
    }


_STATUS_GLYPH = {
    STATUS_PASS: "PASS",
    STATUS_WARN: "WARN",
    STATUS_FAIL: "FAIL",
    STATUS_SKIP: "SKIP",
}


def render_human(report: dict[str, Any]) -> str:
    lines = [
        "Arc Builder Doctor",
        f"  generatedAt : {report['generatedAt']}",
        "  mode        : "
        + ", ".join(key for key, value in report["mode"].items() if value) or "  mode        : (none)",
    ]
    lines.append("  checks:")
    for check in report["checks"]:
        source = f" [{check['source']}]" if check.get("source") else ""
        lines.append(
            f"    {_STATUS_GLYPH.get(check['status'], check['status']):4} "
            f"{check['id']}: {check['detail']}{source}"
        )
    lines.append(f"  overall     : {report['overallStatus'].upper()}")
    lines.append(
        "  safety      : non-custodial, testnet-only, no signing/broadcast, network checks opt-in"
    )
    return "\n".join(lines)


def markdown_cell(value: Any) -> str:
    """Escape a value for a single-line Markdown table cell."""
    escaped = html.escape(str(value), quote=True)
    for token in ("\\", "|", "`", "*", "_", "[", "]"):
        escaped = escaped.replace(token, "\\" + token)
    return escaped.replace("\r", " ").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    enabled_modes = [key for key, value in report["mode"].items() if value]
    lines = [
        "# Arc Builder Doctor",
        "",
        f"- **Overall:** `{markdown_cell(report['overallStatus'].upper())}`",
        f"- **Generated:** `{markdown_cell(report['generatedAt'])}`",
        f"- **Mode:** `{markdown_cell(', '.join(enabled_modes) or 'none')}`",
        "",
        "## Checks",
        "",
        "| Status | Check | Detail | Source | Duration |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for check in report["checks"]:
        lines.append(
            "| "
            + " | ".join(
                (
                    markdown_cell(_STATUS_GLYPH.get(check["status"], check["status"])),
                    markdown_cell(check["id"]),
                    markdown_cell(check["detail"]),
                    markdown_cell(check.get("source", "")),
                    markdown_cell(f"{check['durationMs']} ms"),
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "## Safety Boundaries",
            "",
            "| Boundary | Enabled |",
            "| --- | --- |",
        )
    )
    for key, value in report["safety"].items():
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(str(value).lower())} |")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="arc_builder_doctor",
        description=(
            "Arc Builder Doctor: one safe local health command for the Arc MCP "
            "builder kit. Default mode makes zero network calls. Optional Arc "
            "Testnet RPC and public-site checks are opt-in and read-only; they "
            "never connect a wallet, sign, or broadcast a transaction."
        ),
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="print only the JSON report to stdout")
    output.add_argument(
        "--markdown",
        action="store_true",
        help="print a Markdown report suitable for CI summaries or PR comments",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="also run the canonical regression suite (scripts/test_all.py)",
    )
    parser.add_argument(
        "--include-arc-rpc",
        action="store_true",
        help="opt in to a read-only Arc Testnet RPC chain-id check",
    )
    parser.add_argument(
        "--include-public-site",
        action="store_true",
        help="opt in to read-only GET checks of the public GitHub Pages site",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat an unavailable requested optional network check as a failure",
    )
    parser.add_argument(
        "--network-timeout",
        type=int,
        default=DEFAULT_NETWORK_TIMEOUT,
        help=f"per-request network timeout in seconds (1-{MAX_NETWORK_TIMEOUT})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    options = Options(
        full=args.full,
        include_arc_rpc=args.include_arc_rpc,
        include_public_site=args.include_public_site,
        strict=args.strict,
        network_timeout=args.network_timeout,
    )
    report = build_report(options)
    if args.json:
        print(json.dumps(report, indent=2))
    elif args.markdown:
        print(render_markdown(report))
    else:
        print(render_human(report))
    return 1 if report["overallStatus"] == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
