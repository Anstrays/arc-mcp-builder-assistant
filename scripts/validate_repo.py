#!/usr/bin/env python3
"""Lightweight repository validation for the Arc MCP Builder Assistant.

This script enforces a few cheap, deterministic invariants so that the
GitHub Pages site cannot accidentally regress on:

- presence of the documents required by the project
- absence of obvious credential patterns
- safe HTML (no executable scripts, no inline event handlers, no broken
  anchors, external links carry rel=noopener noreferrer, images carry
  alt text)

- presence of the SEO/meta basics (lang, viewport, description, charset)

It is intentionally dependency-free so it can run in CI without setup.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILES = (
    ".github/workflows/validate.yml",
    ".github/workflows/pages.yml",
    ".github/workflows/readiness-monitor.yml",
)
REQUIRED_FILES = [
    "README.md",
    "index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".env.example",
    "pyproject.toml",
    "MANIFEST.in",
    "setup.py",
    "build_support.py",
    "arc_builder_kit/__init__.py",
    "arc_builder_kit/_paths.py",
    "arc_builder_kit/cli.py",
    "arc_builder_kit/mcp_server.py",
    "config/arc_testnet.facts.json",
    ".github/workflows/validate.yml",
    ".github/workflows/pages.yml",
    ".github/workflows/publish-pypi.yml",
    ".github/dependabot.yml",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    "docs/arc-mcp-setup.md",
    "docs/arc-docs-map.md",
    "docs/deploy-contracts-arc.md",
    "docs/agent-identity-erc8004.md",
    "docs/agent-identity-profile-preview.md",
    "docs/builder-workflows.md",
    "docs/payment-intent-demo.md",
    "docs/payment-intent-quickstart.md",
    "docs/payment-status-tutorial.md",
    "docs/contest-demo-script.md",
    "docs/content-pack.md",
    "docs/public-launch-packet.md",
    "docs/arc-discord-introduction.md",
    "docs/receipt-verifier-playground.md",
    "docs/receipt-viewer.md",
    "docs/payment-intent-receipt-matcher.md",
    "docs/transaction-status-playground.md",
    "docs/x402-mcp-manifest.md",
    "docs/x402-demo-transcript.md",
    "docs/arc-paid-api-endpoint.md",
    "docs/arc-production-deployment.md",
    "docs/prompt-library.md",
    "docs/arc-builder-readiness-checklist.md",
    "docs/completion-contract.md",
    "docs/current-readiness-report.md",
    "docs/arc-testnet-integration-runbook.md",
    "docs/arc-wallet-integration-notes.md",
    "docs/wallet-preflight-contract.md",
    "docs/arc-testnet-send-readiness-gate.md",
    "docs/guarded-wallet-send-runbook.md",
    "docs/custody-and-mainnet-gates.md",
    "docs/arc-testnet-operator-runbook.md",
    "docs/arc-testnet-operator-evidence.md",
    "docs/agent-commerce-use-cases.md",
    "docs/agent-commerce-components.md",
    "docs/agent-commerce-flow-library.md",
    "docs/agent-commerce-review-packet.md",
    "docs/job-escrow-demo.md",
    "docs/arc-agent-treasury-lab.md",
    "docs/circle-wallet-integration.md",
    "docs/agent-commerce-live-evidence.md",
    "docs/agentic-maintainer-loop.md",
    "docs/mcp-query-examples.md",
    "docs/arc-house-submission.md",
    "docs/builder-tooling.md",
    "docs/build-log.md",
    "docs/view.html",
    "docs/viewer.js",
    "prompts/explain-arc-docs.md",
    "prompts/build-payment-intent-demo.md",
    "prompts/register-agent-notes.md",
    "prompts/deploy-contracts-on-arc.md",
    "prompts/wire-arc-testnet-status.md",
    "prompts/agentic-maintainer-loop.md",
    "examples/payment-intent-demo/index.html",
    "examples/payment-intent-playground/index.html",
    "examples/payment-intent-playground/playground.js",
    "examples/receipt-verifier-playground/index.html",
    "examples/receipt-verifier-playground/verifier.js",
    "examples/receipt-viewer/index.html",
    "examples/receipt-viewer/receipt-viewer.js",
    "examples/payment-intent-receipt-matcher/index.html",
    "examples/payment-intent-receipt-matcher/matcher.js",
    "examples/transaction-status-playground/index.html",
    "examples/transaction-status-playground/status.js",
    "examples/arc-testnet-wallet-send-gate/index.html",
    "examples/arc-testnet-wallet-send-gate/wallet-send-gate.js",
    "examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json",
    "examples/agent-commerce-components/index.html",
    "examples/agent-commerce-components/components.js",
    "examples/agent-commerce-flows/index.html",
    "examples/agent-commerce-flows/flows.js",
    "examples/agent-commerce-review-packet/index.html",
    "examples/agent-commerce-review-packet/packet.js",
    "examples/agent-identity-profile-preview/index.html",
    "examples/agent-identity-profile-preview/identity.js",
    "examples/job-escrow-simulator/index.html",
    "examples/job-escrow-simulator/simulator.js",
    "examples/arc-agent-treasury-lab/index.html",
    "examples/arc-agent-treasury-lab/treasury.js",
    "examples/circle-wallet-integration/index.html",
    "examples/circle-wallet-integration/wallet-lab.js",
    "examples/agent-commerce-live/index.html",
    "examples/agent-commerce-live/commerce-live.js",
    "examples/arc-testnet-operator-evidence/evidence.example.json",
    "examples/x402-local-challenge-server/README.md",
    "examples/x402-local-challenge-server/.env.example",
    "examples/arc-paid-api-endpoint/README.md",
    "examples/arc-paid-api-endpoint/server.py",
    "scripts/validate_arc_testnet_facts.py",
    "scripts/test_arc_testnet_facts.py",
    "examples/x402-local-challenge-server/server.py",
    "scripts/check_arc_testnet_status.py",
    "scripts/check_completion.py",
    "scripts/live_arc_gateway_smoke.py",
    "scripts/test_all.py",
    "scripts/scan_for_secrets.py",
    "scripts/serve_local.py",
    "scripts/test_arc_production_deployment.py",
    "scripts/test_arc_testnet_status_helper.py",
    "scripts/test_completion_contract.py",
    "scripts/test_public_claims.py",
    "scripts/test_docs_viewer_security.py",
    "scripts/test_docs_viewer_behavior.py",
    "scripts/docs_viewer_behavior_harness.mjs",
    "scripts/test_workflow_security.py",
    "scripts/generate_arc_release_packet.py",
    "scripts/test_arc_release_packet.py",
    "scripts/test_payment_intent_playground.py",
    "scripts/test_x402_boundary.py",
    "scripts/test_x402_client.py",
    "scripts/test_arc_paid_api_endpoint.py",
    "scripts/test_transaction_status_playground.py",
    "scripts/test_transaction_status_behavior.py",
    "scripts/transaction_status_behavior_harness.mjs",
    "scripts/test_receipt_viewer.py",
    "scripts/receipt_viewer_behavior_harness.mjs",
    "scripts/test_payment_intent_receipt_matcher.py",
    "scripts/payment_intent_receipt_matcher_behavior_harness.mjs",
    "scripts/test_arc_testnet_wallet_send_gate.py",
    "scripts/test_arc_testnet_wallet_send_behavior.py",
    "scripts/wallet_send_behavior_harness.mjs",
    "scripts/validate_live_infrastructure_policy.py",
    "scripts/test_live_infrastructure_policy.py",
    "scripts/test_agent_commerce_components.py",
    "scripts/test_agent_commerce_flows.py",
    "scripts/test_agent_commerce_review_packet.py",
    "scripts/test_agent_identity_profile_preview.py",
    "scripts/test_job_escrow_simulator.py",
    "scripts/test_arc_agent_treasury_lab.py",
    "scripts/arc_agent_treasury_behavior_harness.mjs",
    "scripts/validate_operator_evidence.py",
    "scripts/test_operator_evidence.py",
    "scripts/generate_operator_evidence_draft.py",
    "scripts/test_operator_evidence_draft.py",
    "scripts/report_operator_evidence.py",
    "scripts/test_operator_evidence_report.py",
    "scripts/arc_builder_cli.py",
    "scripts/test_arc_builder_cli.py",
    "scripts/arc_builder_mcp_server.py",
    "scripts/test_arc_builder_mcp_server.py",
    "scripts/test_templates.py",
    "scripts/test_package_distribution.py",
    "scripts/pre_commit_guard.py",
    "scripts/install_repo_hooks.py",
    "scripts/hooks/pre-commit",
    "scripts/test_pre_commit_guard.py",
    "scripts/check_release_version.py",
    "scripts/test_release_version.py",
    "templates/README.md",
    "templates/payment-intent-starter/README.md",
    "templates/payment-intent-starter/index.html",
    "templates/payment-intent-starter/index.js",
    "templates/x402-agent-starter/README.md",
    "templates/x402-agent-starter/server.py",
    "templates/job-escrow-starter/README.md",
    "templates/job-escrow-starter/index.html",
    "templates/job-escrow-starter/index.js",
    "assets/screenshots/landing.png",
    "assets/screenshots/security-viewer.png",
    "assets/screenshots/payment-intent-playground.png",
    "assets/screenshots/job-escrow-simulator.png",
]

# Every HTML file in the repo is checked with these full invariants.
HTML_FILES_TO_VALIDATE = [
    "index.html",
    "404.html",
    "docs/view.html",
    "examples/payment-intent-demo/index.html",
    "examples/payment-intent-playground/index.html",
    "examples/receipt-verifier-playground/index.html",
    "examples/receipt-viewer/index.html",
    "examples/payment-intent-receipt-matcher/index.html",
    "examples/transaction-status-playground/index.html",
    "examples/arc-testnet-wallet-send-gate/index.html",
    "examples/agent-commerce-components/index.html",
    "examples/agent-commerce-flows/index.html",
    "examples/agent-commerce-review-packet/index.html",
    "examples/agent-identity-profile-preview/index.html",
    "examples/job-escrow-simulator/index.html",
    "examples/arc-agent-treasury-lab/index.html",
    "templates/payment-intent-starter/index.html",
    "templates/job-escrow-starter/index.html",
]

CANONICAL_BASE_URL = "https://anstrays.github.io/arc-mcp-builder-assistant/"
SITE_BASE_PATH = "/arc-mcp-builder-assistant/"
SITEMAP_REQUIRED_LOCATIONS = (
    CANONICAL_BASE_URL,
    CANONICAL_BASE_URL + "docs/view.html",
    CANONICAL_BASE_URL + "examples/payment-intent-demo/",
    CANONICAL_BASE_URL + "examples/payment-intent-playground/",
    CANONICAL_BASE_URL + "examples/receipt-verifier-playground/",
    CANONICAL_BASE_URL + "examples/receipt-viewer/",
    CANONICAL_BASE_URL + "examples/payment-intent-receipt-matcher/",
    CANONICAL_BASE_URL + "examples/transaction-status-playground/",
    CANONICAL_BASE_URL + "examples/arc-testnet-wallet-send-gate/",
    CANONICAL_BASE_URL + "examples/agent-commerce-components/",
    CANONICAL_BASE_URL + "examples/agent-commerce-flows/",
    CANONICAL_BASE_URL + "examples/agent-commerce-review-packet/",
    CANONICAL_BASE_URL + "examples/agent-identity-profile-preview/",
    CANONICAL_BASE_URL + "examples/job-escrow-simulator/",
    CANONICAL_BASE_URL + "examples/arc-agent-treasury-lab/",
    CANONICAL_BASE_URL + "examples/circle-wallet-integration/",
    CANONICAL_BASE_URL + "examples/agent-commerce-live/",
)
REDUCED_MOTION_MEDIA_RE = re.compile(
    r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)",
    re.IGNORECASE,
)
DEMO_SAFETY_MARKERS = (
    "does not connect to a wallet",
    "broadcast transactions",
    "talk to any backend",
    "human keeps approval control",
    "controls are intentionally disabled",
)

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}"),  # Telegram bot token shape
    re.compile(
        r"(?i)(?:export\s+)?[A-Z0-9_]*(?:api[_-]?key|secret|password|private[_-]?key|"
        r"entity[_-]?secret|bot[_-]?token)[A-Z0-9_]*[ \t]*[:=][ \t]*['\"]?"
        r"(?![ \t]*(?:process\.env\.|os\.environ|placeholder|example|changeme|todo|your[_-]?|\*+|<|\[|$))[^'\"\s#]{8,}"
    ),
    re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
]

TEXT_SUFFIXES_TO_SECRET_SCAN = {
    "",
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

MOJIBAKE_MARKERS = (
    "\u00c3",
    "\u00c2",
    "\u00e2\u20ac",
    "\u0432\u0402",
    "\u0420\u00b0",
)

# Files we never want to scan for secrets — they only describe patterns,
# not real credentials.
SECRET_SCAN_SKIP = {
    Path("scripts/validate_repo.py"),
    Path("scripts/scan_for_secrets.py"),
}

# script type values that are inert (no JavaScript execution).
INERT_SCRIPT_TYPES = {
    "application/ld+json",
    "application/json",
    "text/plain",
}


class HtmlInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.html_lang: str | None = None
        self.has_charset = False
        self.has_viewport = False
        self.has_description = False
        self.has_csp = False

        self.script_type_stack: list[str] = []
        self.script_text_segments: list[str] = []
        self._in_inert_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "") for key, value in attrs}
        self.elements.append((tag, attr))
        if "id" in attr:
            self.ids.add(attr["id"])
        if tag == "html":
            self.html_lang = attr.get("lang")
        if tag == "meta":
            if attr.get("charset"):
                self.has_charset = True
            name = attr.get("name", "").lower()
            if name == "viewport":
                self.has_viewport = True
            if name == "description" and attr.get("content"):
                self.has_description = True
            if attr.get("http-equiv", "").lower() == "content-security-policy" and attr.get("content"):
                self.has_csp = True

        if tag == "script":
            script_type = attr.get("type", "").lower()
            self.script_type_stack.append(script_type)
            self._in_inert_script = script_type in INERT_SCRIPT_TYPES

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.script_type_stack:
            self.script_type_stack.pop()
            self._in_inert_script = bool(
                self.script_type_stack
                and self.script_type_stack[-1] in INERT_SCRIPT_TYPES
            )

    def handle_data(self, data: str) -> None:
        if self.script_type_stack and not self._in_inert_script and data.strip():
            self.script_text_segments.append(data)


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def validate_required_files() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required file: {relative}")


def validate_workflow_security() -> None:
    """Keep CI reproducible, least-privilege, and aligned with local tests."""
    action_pin = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
    permission_grant = re.compile(
        r"^\s*([a-z][a-z0-9-]*):\s*(read|write)\s*(?:#.*)?$",
        re.IGNORECASE,
    )

    def parsed_permissions(relative: str, text: str) -> set[tuple[str, str]]:
        lines = text.splitlines()
        permission_lines = [
            index
            for index, line in enumerate(lines)
            if line.lstrip().startswith("permissions:")
            and not line.lstrip().startswith("#")
        ]
        if len(permission_lines) != 1:
            fail(f"{relative}: workflow must contain exactly one permissions block")
        start = permission_lines[0]
        if lines[start] != "permissions:":
            fail(f"{relative}: permissions must be one explicit top-level map")

        observed: set[tuple[str, str]] = set()
        for line in lines[start + 1:]:
            if line and not line[0].isspace():
                break
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = permission_grant.fullmatch(line)
            if not match:
                fail(f"{relative}: invalid permissions entry: {line.strip()}")
            observed.add((match.group(1).lower(), match.group(2).lower()))
        return observed

    for relative in WORKFLOW_FILES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        active_lines = [
            line.strip().removeprefix("- ").lstrip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        for forbidden in ("pull_request_target:", "workflow_run:"):
            if forbidden in text:
                fail(f"{relative}: forbidden privileged workflow trigger: {forbidden}")
        active_actions: set[str] = set()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                stripped = stripped[2:].lstrip()
            if not stripped.startswith("uses:"):
                continue
            action = stripped.removeprefix("uses:").split("#", 1)[0].strip()
            if action.startswith("./"):
                continue
            if not action_pin.fullmatch(action):
                fail(f"{relative}: action must use a full commit SHA: {action}")
            active_actions.add(action.split("@", 1)[0])
        for action in ("actions/setup-python", "actions/setup-node"):
            if action not in active_actions:
                fail(f"{relative}: missing active runtime setup action: {action}")
        for marker in (
            'python-version: "3.12"',
            'node-version: "22"',
            "run: python scripts/test_all.py",
        ):
            if marker not in active_lines:
                fail(f"{relative}: missing active runtime/test contract marker: {marker}")

    expected_permissions = {
        WORKFLOW_FILES[0]: {("contents", "read")},
        WORKFLOW_FILES[1]: {
            ("contents", "read"),
            ("pages", "write"),
            ("id-token", "write"),
        },
        WORKFLOW_FILES[2]: {("contents", "read")},
    }
    for relative, expected in expected_permissions.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        observed = parsed_permissions(relative, text)
        if observed != expected:
            fail(
                f"{relative}: workflow permissions must be exactly "
                f"{sorted(expected)}; observed {sorted(observed)}"
            )

    validate = (ROOT / WORKFLOW_FILES[0]).read_text(encoding="utf-8")
    validate_active_lines = [
        line.strip().removeprefix("- ").lstrip()
        for line in validate.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for marker in (
        "python3 scripts/arc_builder_doctor.py --markdown",
        '>> "$GITHUB_STEP_SUMMARY"',
    ):
        if not any(marker in line for line in validate_active_lines):
            fail(f"{WORKFLOW_FILES[0]}: missing active Doctor summary marker: {marker}")

    monitor = (ROOT / WORKFLOW_FILES[2]).read_text(encoding="utf-8")
    monitor_active_lines = [
        line.strip().removeprefix("- ").lstrip()
        for line in monitor.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for marker in (
        "schedule:",
        "workflow_dispatch:",
        "timeout-minutes: 10",
        "set +e",
        "--include-arc-rpc",
        "--include-public-site",
        "--strict",
        "--markdown",
        '"$RUNNER_TEMP/arc-builder-doctor.md"',
        '"$GITHUB_STEP_SUMMARY"',
        "doctor_status=$?",
        "set -e",
        'exit "$doctor_status"',
    ):
        if not any(marker in line for line in monitor_active_lines):
            fail(f"{WORKFLOW_FILES[2]}: missing active readiness-monitor safety marker: {marker}")

    validate_pypi_publish_workflow()


def validate_pypi_publish_workflow() -> None:
    """Keep package publication release-only, keyless, and least-privilege."""
    relative = ".github/workflows/publish-pypi.yml"
    text = (ROOT / relative).read_text(encoding="utf-8")
    active_lines = [
        line.strip().removeprefix("- ").lstrip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if "pull_request_target:" in text or "workflow_run:" in text or "workflow_dispatch:" in text:
        fail(f"{relative}: publishing must only be triggered by a published GitHub release")
    for marker in (
        "release:",
        "types: [published]",
        "if: github.event.release.prerelease == false",
        "name: pypi",
        'python scripts/check_release_version.py --tag "${GITHUB_REF_NAME}"',
        "python scripts/test_all.py",
        "build==1.5.0",
        "twine==6.2.0",
        "python -m build",
        "python -m twine check dist/*",
        "pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b",
    ):
        if not any(marker in line for line in active_lines):
            fail(f"{relative}: missing active trusted-publishing marker: {marker}")

    action_pin = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            stripped = stripped[2:].lstrip()
        if stripped.startswith("uses:"):
            ref = stripped.split(":", 1)[1].strip().split()[0]
            if not action_pin.fullmatch(ref):
                fail(f"{relative}: action must be pinned to a full commit SHA: {ref}")

    permission_headers = [line for line in text.splitlines() if line.strip() == "permissions:"]
    if len(permission_headers) != 2:
        fail(f"{relative}: expected top-level and publish-job permissions only")
    top_permissions = re.search(r"(?m)^permissions:\n((?:  [a-z][a-z0-9-]*: (?:read|write)\n)+)", text)
    job_permissions = re.search(r"(?m)^    permissions:\n((?:      [a-z][a-z0-9-]*: (?:read|write)\n)+)", text)
    if top_permissions is None or set(top_permissions.group(1).splitlines()) != {"  contents: read"}:
        fail(f"{relative}: top-level permissions must be exactly contents: read")
    if job_permissions is None or set(job_permissions.group(1).splitlines()) != {
        "      contents: read",
        "      id-token: write",
    }:
        fail(f"{relative}: publish job permissions must be exactly contents: read and id-token: write")

    lowered = text.lower()
    for forbidden in ("secrets.", "pypi_api_token", "password:", "username: __token__", "skip-existing"):
        if forbidden in lowered:
            fail(f"{relative}: forbidden token-based or fail-open publishing marker: {forbidden}")


def validate_no_secrets() -> None:
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative in SECRET_SCAN_SKIP:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES_TO_SECRET_SCAN:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(f"non-UTF-8 text file blocks secret scan: {relative}")
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"potential secret pattern in {relative}")


def validate_public_text_integrity() -> None:
    """Reject common UTF-8/Windows-1252 decoding damage in public text files."""
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or ".hermes" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES_TO_SECRET_SCAN:
            continue
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                fail(f"possible mojibake marker in {relative}: {marker!r}")


def validate_repository_line_ending_policy() -> None:
    """Keep Windows, WSL, and CI diffs deterministic without bulk churn."""
    relative = ".gitattributes"
    attributes = (ROOT / relative).read_text(encoding="utf-8")
    for marker in (
        "* text=auto eol=lf",
        "*.png binary",
        "*.jpg binary",
        "*.jpeg binary",
        "*.gif binary",
        "*.webp binary",
    ):
        if marker not in attributes:
            fail(f"{relative}: missing line-ending/binary marker: {marker}")


def validate_documented_secret_handling() -> None:
    """Keep builder tutorials from normalizing raw-key or frontend-secret use."""
    docs_map = (ROOT / "docs/arc-docs-map.md").read_text(encoding="utf-8")
    for forbidden in ("--private-key", "$PRIVATE_KEY"):
        if forbidden in docs_map:
            fail(f"docs/arc-docs-map.md: forbidden raw private-key deploy marker: {forbidden}")
    for marker in (
        "cast wallet import arc-testnet-review",
        "--account arc-testnet-review",
        "Never put a raw private key in",
    ):
        if marker not in docs_map:
            fail(f"docs/arc-docs-map.md: missing encrypted-keystore guidance: {marker}")

    deploy_notes = (ROOT / "docs/deploy-contracts-arc.md").read_text(encoding="utf-8")
    for marker in (
        "separate backend/custody integration path",
        "keep credentials out of frontend code and chat",
        "use a deployment secret manager",
    ):
        if marker not in deploy_notes:
            fail(f"docs/deploy-contracts-arc.md: missing custody/secret boundary: {marker}")


def validate_html_file(relative: str) -> None:
    html_path = ROOT / relative
    html = html_path.read_text(encoding="utf-8")
    if "<!doctype html>" not in html.lower():
        fail(f"{relative} is missing doctype")

    inspector = HtmlInspector()
    inspector.feed(html)

    if inspector.script_text_segments:
        fail(
            f"{relative} should not contain executable scripts; "
            "only inert types (e.g. application/ld+json) are allowed"
        )

    for tag, attrs in inspector.elements:
        if tag == "script":
            script_type = attrs.get("type", "").lower()
            if script_type and script_type not in INERT_SCRIPT_TYPES:
                fail(f"{relative}: executable script type is not allowed: {script_type}")
            if attrs.get("src"):
                src = attrs.get("src", "").strip()
                if src.startswith(("http://", "https://", "//")):
                    fail(f"{relative}: remote scripts are not allowed: {src}")
                target = _resolved_local_link_target(relative, src)
                if target is None or not target.is_file():
                    fail(f"{relative}: local script is missing: {src}")
        for key in attrs:
            if key.lower().startswith("on"):
                fail(f"{relative}: inline event handler is not allowed on <{tag}>: {key}")
        if tag == "img":
            if "alt" not in attrs:
                fail(f"{relative}: <img> missing alt attribute (src={attrs.get('src','?')})")
        if tag == "a":
            href = attrs.get("href", "")
            normalized_href = href.strip().lower()
            if normalized_href.startswith("javascript:"):
                fail(f"{relative}: unsafe javascript URL: {href}")
            if href.startswith("#") and len(href) > 1 and href[1:] not in inspector.ids:
                fail(f"{relative}: broken anchor link: {href}")
            if attrs.get("target", "").strip().lower() == "_blank":
                rel = {value.lower() for value in attrs.get("rel", "").split()}
                if not {"noopener", "noreferrer"}.issubset(rel):
                    fail(f"{relative}: external link missing rel noopener noreferrer: {href}")

    if not inspector.html_lang:
        fail(f"{relative}: <html> tag must declare a lang attribute")
    if not inspector.has_charset:
        fail(f"{relative}: missing <meta charset>")
    if not inspector.has_viewport:
        fail(f"{relative}: missing <meta name=\"viewport\">")
    if not inspector.has_description:
        fail(f"{relative}: missing a non-empty <meta name=\"description\">")
    if not inspector.has_csp:
        fail(f"{relative}: missing Content-Security-Policy meta tag")

def validate_html() -> None:
    for relative in HTML_FILES_TO_VALIDATE:
        validate_html_file(relative)


def validate_reduced_motion_css() -> None:
    for relative in HTML_FILES_TO_VALIDATE:
        html = (ROOT / relative).read_text(encoding="utf-8")
        if not REDUCED_MOTION_MEDIA_RE.search(html):
            fail(f"{relative}: missing prefers-reduced-motion CSS rule")
        if "transition: none" not in html:
            fail(f"{relative}: reduced-motion rule must disable transitions")
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    if "scroll-behavior: auto" not in index_html:
        fail("index.html: reduced-motion rule must disable smooth scrolling")


def validate_responsive_layout_guards() -> None:
    """Keep narrow layouts from expanding beyond the mobile viewport."""
    required = {
        "index.html": (
            ".hero-grid > *, .split > *, .playground-grid > * { min-width: 0; }",
            "grid-template-columns: minmax(0, 1fr)",
            "overflow-wrap: anywhere",
        ),
        "docs/view.html": (
            "grid-template-columns: minmax(0, 1fr) minmax(0, 300px)",
            ".panel, aside { min-width: 0; }",
            "overflow-wrap: anywhere",
        ),
        "examples/payment-intent-playground/index.html": (
            "main > *, .grid > * { min-width: 0; }",
        ),
        "examples/receipt-verifier-playground/index.html": (
            "main > *, .grid > * { min-width:0; }",
        ),
        "examples/transaction-status-playground/index.html": (
            "main > *, .grid > * { min-width:0; }",
        ),
        "examples/receipt-viewer/index.html": (
            "main > *, .grid > * { min-width:0; }",
            "overflow-wrap:anywhere",
        ),
        "examples/agent-commerce-components/index.html": (
            ".wrap > *, .grid > *, .cards > * { min-width: 0; }",
            ".actions { flex-wrap: wrap; }",
        ),
        "examples/arc-agent-treasury-lab/index.html": (
            "grid-template-columns: minmax(320px, .78fr) minmax(420px, 1.22fr)",
            "@media (max-width: 980px) { .layout { grid-template-columns: 1fr; }",
            "overflow-wrap: anywhere",
        ),
    }
    for relative, markers in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                fail(f"{relative}: missing responsive layout guard: {marker}")


def validate_public_inventory_counts() -> None:
    """Keep the landing-page repository counts tied to committed surfaces."""
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    counts = {
        "Docs": len(list((ROOT / "docs").glob("*.md"))),
        "Examples": len([path for path in (ROOT / "examples").iterdir() if path.is_dir()]),
        "Prompt packs": len([path for path in (ROOT / "prompts").iterdir() if path.is_file()]),
    }
    for label, count in counts.items():
        marker = f'<div class="metric"><span>{label}</span><strong>{count}</strong></div>'
        if marker not in index:
            fail(f"index.html: stale public inventory count for {label}: expected {count}")


def _resolved_local_link_target(source_relative: str, href: str) -> Path | None:
    href = href.strip()
    if (
        not href
        or href.startswith("#")
        or href.startswith(("http://", "https://", "mailto:", "tel:", "data:"))
    ):
        return None

    href_without_fragment = href.split("#", 1)[0]
    if href_without_fragment.startswith(SITE_BASE_PATH):
        href_without_fragment = href_without_fragment[len(SITE_BASE_PATH):]
        target = ROOT / href_without_fragment
    elif href_without_fragment.startswith("/"):
        target = ROOT / href_without_fragment.lstrip("/")
    else:
        target = ROOT / source_relative
        target = target.parent / href_without_fragment

    if href.endswith("/"):
        target = target / "index.html"
    return target.resolve()


def validate_local_links() -> None:
    root_resolved = ROOT.resolve()
    for relative in HTML_FILES_TO_VALIDATE:
        html = (ROOT / relative).read_text(encoding="utf-8")
        inspector = HtmlInspector()
        inspector.feed(html)
        for tag, attrs in inspector.elements:
            if tag != "a":
                continue
            href = attrs.get("href", "")
            target = _resolved_local_link_target(relative, href)
            if target is None:
                continue
            if root_resolved not in (target, *target.parents):
                fail(f"{relative}: local link escapes repository root: {href}")
            if not target.is_file():
                fail(f"{relative}: broken local link: {href}")


def validate_markdown_local_links() -> None:
    """Ensure committed relative links in public Markdown resolve locally."""
    root_resolved = ROOT.resolve()
    link_re = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts or ".hermes" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for href in link_re.findall(text):
            href = href.strip("<>")
            target = _resolved_local_link_target(relative, href)
            if target is None:
                continue
            if href.split("#", 1)[0].endswith("/") and target.name == "index.html":
                target = target.parent
            if root_resolved not in (target, *target.parents):
                fail(f"{relative}: Markdown link escapes repository root: {href}")
            if not target.exists():
                fail(f"{relative}: broken Markdown link: {href}")


def validate_no_raw_markdown_links() -> None:
    """Keep user-facing HTML Markdown links on the styled viewer, not raw files."""
    raw_markdown_link_re = re.compile(r"href=[\"']([^\"']+\.md(?:#[^\"']*)?)[\"']", re.IGNORECASE)
    for relative in HTML_FILES_TO_VALIDATE:
        html = (ROOT / relative).read_text(encoding="utf-8")
        for href in raw_markdown_link_re.findall(html):
            if "docs/view.html#" not in href:
                fail(f"{relative}: link to raw Markdown should use docs/view.html: {href}")


def validate_docs_viewer_registry() -> None:
    """Ensure every public Markdown page is reachable through the styled viewer."""
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")
    expected_page_ids = [
        path.replace("docs/", "")
        for path in REQUIRED_FILES
        if path.startswith("docs/") and path.endswith(".md")
    ] + ["security.md", "contributing.md", "code-of-conduct.md"]
    for page_id in expected_page_ids:
        if f"id: '{page_id}'" not in viewer:
            fail(f"docs/viewer.js: missing styled viewer page id: {page_id}")
    for source_path in ("../SECURITY.md", "../CONTRIBUTING.md", "../CODE_OF_CONDUCT.md"):
        if f"path: '{source_path}'" not in viewer:
            fail(f"docs/viewer.js: missing community source path: {source_path}")
    for marker in (
        "const DOC_TIMEOUT_MS = 8_000;",
        "const MAX_DOC_BYTES = 1_000_000;",
        "async function fetchDocText(path)",
        "new AbortController()",
        "new TextEncoder().encode(markdown).byteLength",
        "window.clearTimeout(timeout)",
        "const markdown = await fetchDocText(page.path);",
    ):
        if marker not in viewer:
            fail(f"docs/viewer.js: missing bounded document fetch marker: {marker}")


def validate_completion_contract() -> None:
    """Keep the public completion claim measurable and discoverable."""
    contract_relative = "docs/completion-contract.md"
    checker_relative = "scripts/check_completion.py"
    contract = (ROOT / contract_relative).read_text(encoding="utf-8")
    checker = (ROOT / checker_relative).read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")

    for marker in (
        "# Safe-scope completion contract",
        "## Definition of complete",
        "## Acceptance criteria",
        "## Explicit non-goals",
        "## Canonical verification",
        "no private keys",
        "no transaction broadcast on page load",
    ):
        if marker.lower() not in contract.lower():
            fail(f"{contract_relative}: missing completion marker: {marker}")
    for marker in (
        "def check_required_surfaces",
        "def check_canonical_suite",
        "def check_safety_boundary",
        "def main",
    ):
        if marker not in checker:
            fail(f"{checker_relative}: missing completion check marker: {marker}")
    for surface, text in (
        ("README.md", readme),
        ("index.html", index),
        ("docs/viewer.js", viewer),
    ):
        if "completion-contract.md" not in text:
            fail(f"{surface}: missing completion contract link")


def validate_demo_safety_copy() -> None:
    relative = "examples/payment-intent-demo/index.html"
    html = (ROOT / relative).read_text(encoding="utf-8").lower()
    for marker in DEMO_SAFETY_MARKERS:
        if marker not in html:
            fail(f"{relative}: missing safety copy marker: {marker}")


def validate_public_launch_packet() -> None:
    """Keep public distribution copy discoverable and non-overclaiming."""
    doc_relative = "docs/public-launch-packet.md"
    viewer_relative = "docs/viewer.js"
    index_relative = "index.html"

    doc = (ROOT / doc_relative).read_text(encoding="utf-8")
    doc_lower = doc.lower()
    viewer = (ROOT / viewer_relative).read_text(encoding="utf-8")
    index = (ROOT / index_relative).read_text(encoding="utf-8")

    for marker in (
        "# Public launch packet",
        "## Launch verdict",
        "## Do not post automatically",
        "## Russian Telegram draft",
        "## X draft under 280 chars",
        "## Discord / Arc House update",
        "## Submission checklist",
        "## Claims to avoid",
    ):
        if marker not in doc:
            fail(f"{doc_relative}: missing launch packet marker: {marker}")
    for marker in (
        "do not post automatically",
        "no wallet",
        "no private keys",
        "no custody",
        "no transaction broadcast",
        "not an official arc product",
        "local-only",
        "public-ready arc builder kit",
    ):
        if marker not in doc_lower:
            fail(f"{doc_relative}: missing safety wording marker: {marker}")
    if "public-launch-packet.md" not in viewer:
        fail(f"{viewer_relative}: missing public launch packet route")
    if "./docs/view.html#public-launch-packet.md" not in index:
        fail(f"{index_relative}: missing public launch packet link")


def validate_arc_release_packet() -> None:
    """Keep the local release packet generator and its test discoverable."""
    for relative in (
        "scripts/generate_arc_release_packet.py",
        "scripts/test_arc_release_packet.py",
    ):
        if not (ROOT / relative).is_file():
            fail(f"{relative}: missing release packet surface")

    test_all = (ROOT / "scripts/test_all.py").read_text(encoding="utf-8")
    if "scripts/test_arc_release_packet.py" not in test_all:
        fail("scripts/test_all.py: missing release packet regression entry for scripts/test_arc_release_packet.py")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if ".arc-release-packet/" not in gitignore:
        fail(".gitignore: missing ignored output directory for release packet")


def validate_x402_boundary_demo() -> None:
    """Keep the x402 example explicitly local-only and verifier-shaped."""
    server = (ROOT / "examples/x402-local-challenge-server/server.py").read_text(encoding="utf-8")
    readme = (ROOT / "examples/x402-local-challenge-server/README.md").read_text(encoding="utf-8").lower()
    required_server_markers = (
        "class PaymentVerifier(Protocol)",
        "class LocalDemoVerifier",
        "HTTPStatus.PAYMENT_REQUIRED",
        '"transactionBroadcast": False',
        '"mainnetEnabled": config.mainnet_enabled',
        'DEFAULT_NETWORK = "arc-testnet"',
        'DEFAULT_ASSET = "USDC"',
        "def from_env",
        "validate_payment_config",
        "human approval must remain required in this demo",
        "verifier mode must stay local-simulation in this demo",
        "request jsonrpc must be exactly 2.0",
        "request id must be a string, integer, or null",
        "request method must be a string",
        "validate_bind_target",
        "LOCAL_BIND_HOSTS",
        "X402_DEMO_MAINNET_ENABLED",
        "PaymentConfig.from_env()",
        "MAX_MCP_LINE_BYTES = 1_000_000",
        "MAX_PAYMENT_PROOF_BYTES = 4_096",
        "def require_exact_keys",
        "def validate_payment_proof",
        "def extract_payment_proof",
        "exactly one X-Payment header is required",
        "X-Payment proof exceeds the 4 KB safety limit",
        '"error": "payment_verifier_unavailable"',
        '"error": "invalid_verifier_result"',
        '"error": "unsafe_verifier_result"',
        "object_pairs_hook=reject_duplicate_json_keys",
    )
    for marker in required_server_markers:
        if marker not in server:
            fail(f"examples/x402-local-challenge-server/server.py: missing marker: {marker}")
    for marker in ("local-only", "never opens a wallet", "transactionbroadcast", "mainnetenabled"):
        if marker not in readme:
            fail(f"examples/x402-local-challenge-server/README.md: missing safety marker: {marker}")


def validate_arc_production_deployment_assets() -> None:
    """Keep production-facing Arc/x402 docs secret-free and smoke-testable."""
    runbook_relative = "docs/arc-production-deployment.md"
    env_relative = "examples/x402-local-challenge-server/.env.example"
    smoke_relative = "scripts/live_arc_gateway_smoke.py"
    test_relative = "scripts/test_arc_production_deployment.py"

    runbook = (ROOT / runbook_relative).read_text(encoding="utf-8").lower()
    env_example = (ROOT / env_relative).read_text(encoding="utf-8")
    smoke = (ROOT / smoke_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")

    for marker in (
        "arc_paid_agent_url",
        "arc_live_x_payment",
        "--expect-402-only",
        "circle gateway",
        "x402",
        "rollback",
        "human approval",
        "no private keys",
        "no seed phrases",
        "does not create payments",
    ):
        if marker not in runbook:
            fail(f"{runbook_relative}: missing production runbook marker: {marker}")
    for marker in (
        "ARC_PAID_AGENT_URL=",
        "ARC_LIVE_X_PAYMENT=",
        "CIRCLE_GATEWAY_API_KEY=",
        "X402_GATEWAY_VERIFIER_URL=",
        "EXPECT_402_ONLY=true",
        "Placeholder only",
    ):
        if marker not in env_example:
            fail(f"{env_relative}: missing placeholder env marker: {marker}")
    for marker in (
        "ARC_PAID_AGENT_URL",
        "ARC_LIVE_X_PAYMENT",
        "X-Payment",
        "NoRedirectHandler",
        "redirects are disabled for live smoke requests",
        "MAX_RESPONSE_BYTES",
        'first.get("asset") != "USDC"',
        'payload.get("mainnetEnabled") is not False',
        "--expect-402-only",
        "No payments were created",
        "transactionBroadcast",
        "humanApprovalRequired",
        "arc-testnet",
    ):
        if marker not in smoke:
            fail(f"{smoke_relative}: missing safe smoke marker: {marker}")
    for marker in (
        "test_live_smoke_fails_safely_without_target_url",
        "test_live_smoke_accepts_local_402_only_mode",
        "test_live_smoke_rejects_unsupported_url_scheme_without_proof",
        "test_live_smoke_rejects_url_credentials_and_invalid_timeout",
        "test_production_runbook_documents_safe_gateway_handoff",
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing regression test marker: {marker}")
    for forbidden in ("local-demo:", "-----BEGIN", "sk-"):
        if forbidden in env_example:
            fail(f"{env_relative}: forbidden placeholder content: {forbidden}")


def validate_arc_testnet_status_helper() -> None:
    """Keep the first Arc Testnet helper read-only and source-fact grounded."""
    relative = "scripts/check_arc_testnet_status.py"
    helper = (ROOT / relative).read_text(encoding="utf-8")
    required_markers = (
        "EXPECTED_CHAIN_ID_DECIMAL = 5042002",
        "EXPECTED_CHAIN_ID_HEX = hex(EXPECTED_CHAIN_ID_DECIMAL)",
        'DEFAULT_RPC_URL = "https://rpc.testnet.arc.network"',
        'DEFAULT_EXPLORER_URL = "https://testnet.arcscan.app"',
        '"nativeGasAsset": "USDC"',
        '"nativeGasDecimals": 18',
        '"erc20UsdcAddress": "0x3600000000000000000000000000000000000000"',
        '"erc20UsdcDecimals": 6',
        '"rpcChainIdMatchesArcTestnet": expected',
        '"signingRequiresWalletChainGateAndHumanApproval": True',
        "validate_endpoint",
        "validate_timeout",
        "MAX_RESPONSE_BYTES",
        "decode_json_object",
    )
    for marker in required_markers:
        if marker not in helper:
            fail(f"{relative}: missing Arc Testnet status marker: {marker}")
    forbidden_markers = ("PRIVATE_KEY", "seed phrase", "safeToUseForSigning")
    for marker in forbidden_markers:
        if marker in helper:
            fail(f"{relative}: forbidden wallet/signing marker: {marker}")


def validate_payment_intent_playground_status_panel() -> None:
    """Keep the interactive playground status panel local-only and Arc-grounded."""
    html_relative = "examples/payment-intent-playground/index.html"
    js_relative = "examples/payment-intent-playground/playground.js"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    for marker in (
        'id="arc-status-panel"',
        'id="arc-chain-id"',
        'id="arc-rpc-url"',
        'id="arc-readonly-state"',
        "Arc Testnet status",
        "Read-only RPC probe",
    ):
        if marker not in html:
            fail(f"{html_relative}: missing Arc status panel marker: {marker}")
    for marker in (
        "const ARC_TESTNET_STATUS",
        "expectedChainIdDecimal: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "walletConnected: false",
        "transactionBroadcast: false",
        "signingRequiresWalletChainGateAndHumanApproval: true",
        "!/^0x0{40}$/.test(normalized)",
        "normalized !== ARC_TESTNET_STATUS.erc20UsdcAddress.toLowerCase()",
        "renderArcStatusPanel()",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing Arc status panel marker: {marker}")
    for marker in ("fetch(", "XMLHttpRequest", "WebSocket", "ethereum.request", "sendTransaction", "signTransaction", "PRIVATE_KEY"):
        if marker in js:
            fail(f"{js_relative}: forbidden network/wallet marker: {marker}")


def validate_receipt_verifier_playground() -> None:
    """Keep the receipt verifier playground static, local-only, and Arc-grounded."""
    html_relative = "examples/receipt-verifier-playground/index.html"
    js_relative = "examples/receipt-verifier-playground/verifier.js"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    for marker in (
        'id="receipt-json"',
        'id="verify-receipt"',
        'id="verdict-pill"',
        'id="receipt-check-list"',
        'id="normalized-receipt"',
        "Receipt Verifier Playground",
        "No wallet connection",
        "No transaction broadcast",
    ):
        if marker not in html:
            fail(f"{html_relative}: missing receipt verifier marker: {marker}")
    for marker in (
        "const ARC_RECEIPT_EXPECTATIONS",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "asset: 'USDC'",
        "assetDecimals: 6",
        "function normalizeReceipt(rawReceipt)",
        "function verifyReceipt(receipt)",
        "function isValidAddress(value)",
        "!/^0x0{40}$/.test(normalized)",
        "normalized !== '0x3600000000000000000000000000000000000000'",
        "walletConnected: false",
        "backendCalls: false",
        "transactionBroadcast: false",
        "signingEnabled: false",
        "localOnly: true",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing receipt verifier marker: {marker}")
    for marker in ("fetch(", "XMLHttpRequest", "WebSocket", "ethereum.request", "sendTransaction", "signTransaction", "PRIVATE_KEY", "seed phrase"):
        if marker in js:
            fail(f"{js_relative}: forbidden network/wallet marker: {marker}")


def validate_payment_intent_receipt_matcher() -> None:
    """Keep the payment-intent receipt matcher pinned to Arc Testnet USDC and read-only."""
    html_relative = "examples/payment-intent-receipt-matcher/index.html"
    js_relative = "examples/payment-intent-receipt-matcher/matcher.js"
    test_relative = "scripts/test_payment_intent_receipt_matcher.py"
    harness_relative = "scripts/payment_intent_receipt_matcher_behavior_harness.mjs"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")
    harness = (ROOT / harness_relative).read_text(encoding="utf-8")

    # HTML structure and policy
    for marker in (
        "Payment Intent Receipt Matcher",
        'id="payment-intent"',
        'id="transaction-hash"',
        'id="match-receipt"',
        'id="reset-matcher"',
        'id="status-pill"',
        'id="match-summary-list"',
        'id="transfer-log-list"',
        'id="match-json"',
        "Read-only Arc Testnet RPC",
        "USDC Transfer logs",
        "No wallet connection",
        "No signing",
        "No transaction broadcast",
        "connect-src 'self' https://rpc.testnet.arc.network",
        'crossorigin="anonymous"',
    ):
        if marker not in html:
            fail(f"{html_relative}: missing payment-intent receipt matcher marker: {marker}")

    # JS pinning and read-only scope
    for marker in (
        "const ARC_MATCHER = Object.freeze",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "usdcDecimals: 6",
        "const ZERO_ADDRESS",
        "function isNonZeroAddress",
        "function parseAmountBaseUnits",
        "function usdcBaseUnitsFromDecimal",
        "network !== 'Arc Testnet'",
        "'arc-testnet'",
        "chainId !== ARC_MATCHER.expectedChainId",
        "asset !== 'USDC'",
        "token !== ARC_MATCHER.usdcAddress.toLowerCase()",
        "decimals !== ARC_MATCHER.usdcDecimals",
        "recipient must include a valid non-zero 20-byte recipient address",
        "recipient must not be the USDC token contract",
        "amount and amountBaseUnits do not match",
        "fractionPart.length > ARC_MATCHER.usdcDecimals",
        "const RPC_TIMEOUT_MS = 15_000",
        "const MAX_RPC_RESPONSE_BYTES = 1_000_000",
        "const RPC_REQUEST_ID = 'arc-payment-intent-receipt-matcher-read-only'",
        "const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'",
        "method: 'eth_chainId'",
        "method: 'eth_getTransactionReceipt'",
        "new AbortController()",
        "new TextEncoder().encode(responseText).byteLength",
        "window.clearTimeout(timeout)",
        "Request timed out after 15 seconds.",
        "RPC response must be a JSON object",
        "RPC response envelope did not match the request",
        "RPC response must contain exactly one result or error field",
        "function decodeUsdcTransferLog(log)",
        "function extractUsdcTransferLogs(receipt)",
        "function classifyMatch",
        "function parseIntent",
        "invalid_local_input",
        "intent_receipt_match_observed",
        "intent_receipt_mismatch",
        "reverted_receipt_observed",
        "receipt_not_found",
        "unknown_wrong_chain",
        "unknown_hash_mismatch",
        "settlementProven: false",
        "businessAcceptanceProven: false",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing payment-intent receipt matcher marker: {marker}")

    if "eth_getTransactionByHash" in js:
        fail(f"{js_relative}: matcher must not fetch full transactions")

    for marker in (
        "window.ethereum",
        "ethereum.request",
        "personal_sign",
        "eth_sendTransaction",
        "eth_sendRawTransaction",
        "wallet_switchEthereumChain",
        "sendTransaction",
        "signTransaction",
        "PRIVATE_KEY",
        "localStorage",
        "sessionStorage",
    ):
        if marker in html or marker in js:
            fail(f"{html_relative}/{js_relative}: forbidden payment-intent receipt matcher marker: {marker}")

    # Regression tests cover the hardening
    for marker in (
        "test_payment_intent_receipt_matcher_script_tag_has_matching_sri",
        "test_payment_intent_receipt_matcher_js_pins_arc_testnet_chain",
        "test_payment_intent_receipt_matcher_js_pins_usdc_token",
        "test_payment_intent_receipt_matcher_js_enforces_six_decimals",
        "test_payment_intent_receipt_matcher_js_rejects_amount_precision_errors",
        "test_payment_intent_receipt_matcher_js_rejects_zero_address",
        "test_payment_intent_receipt_matcher_js_rejects_mismatched_amount_fields",
        "test_payment_intent_receipt_matcher_js_rejects_recipient_equal_to_usdc_contract",
        "test_payment_intent_receipt_matcher_harness_tests_invalid_intent_cases",
        "payment_intent_receipt_matcher_behavior_harness.mjs",
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing payment-intent matcher regression marker: {marker}")

    # Behavior harness exercises invalid local intent cases without RPC
    for marker in (
        "testInvalidLocalIntentAvoidsRpc",
        "wrong chainId",
        "wrong network",
        "wrong asset",
        "non-USDC token",
        "wrong decimals",
        "zero recipient",
        "recipient is USDC contract",
        "too many fractional digits",
        "zero amount",
        "negative amount",
        "hex amountBaseUnits",
        "mismatched amount/baseUnits",
        "invalid_local_input",
    ):
        if marker not in harness:
            fail(f"{harness_relative}: missing payment-intent matcher behavior marker: {marker}")



def validate_receipt_viewer() -> None:
    """Keep the receipt viewer read-only, receipt-scoped, and wallet-free."""
    html_relative = "examples/receipt-viewer/index.html"
    js_relative = "examples/receipt-viewer/receipt-viewer.js"
    test_relative = "scripts/test_receipt_viewer.py"
    harness_relative = "scripts/receipt_viewer_behavior_harness.mjs"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")
    harness = (ROOT / harness_relative).read_text(encoding="utf-8")
    for marker in (
        "Agent Payment Receipt Viewer",
        'id="transaction-hash"',
        'id="load-receipt"',
        'id="reset-receipt"',
        'id="status-pill"',
        'id="receipt-summary-list"',
        'id="transfer-log-list"',
        'id="receipt-json"',
        "Read-only Arc Testnet RPC",
        "USDC Transfer logs",
        "No wallet connection",
        "No transaction broadcast",
        "connect-src 'self' https://rpc.testnet.arc.network",
        'crossorigin="anonymous"',
    ):
        if marker not in html:
            fail(f"{html_relative}: missing receipt viewer marker: {marker}")
    for marker in (
        "const ARC_RECEIPT_VIEWER = Object.freeze",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "usdcDecimals: 6",
        "const RPC_TIMEOUT_MS = 15_000",
        "const MAX_RPC_RESPONSE_BYTES = 1_000_000",
        "const RPC_REQUEST_ID = 'arc-receipt-viewer-read-only'",
        "const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'",
        "method: 'eth_chainId'",
        "method: 'eth_getTransactionReceipt'",
        "new AbortController()",
        "new TextEncoder().encode(responseText).byteLength",
        "window.clearTimeout(timeout)",
        "Request timed out after 15 seconds.",
        "RPC response must be a JSON object",
        "RPC response envelope did not match the request",
        "RPC response must contain exactly one result or error field",
        "function decodeUsdcTransferLog(log)",
        "function extractUsdcTransferLogs(receipt)",
        "function classifyReceiptStatus(chainIdHex, receipt, expectedTransactionHash)",
        "success_receipt_observed",
        "reverted_receipt_observed",
        "receipt_not_found",
        "unknown_wrong_chain",
        "unknown_hash_mismatch",
        "settlementProven: false",
        "businessAcceptanceProven: false",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing receipt viewer marker: {marker}")
    if "eth_getTransactionByHash" in js:
        fail(f"{js_relative}: receipt viewer must not fetch full transactions")
    for marker in (
        "window.ethereum",
        "ethereum.request",
        "personal_sign",
        "eth_sendTransaction",
        "eth_sendRawTransaction",
        "wallet_switchEthereumChain",
        "sendTransaction",
        "signTransaction",
        "PRIVATE_KEY",
        "localStorage",
        "sessionStorage",
    ):
        if marker in html or marker in js:
            fail(f"{html_relative}/{js_relative}: forbidden receipt viewer marker: {marker}")
    for marker in (
        "test_receipt_viewer_page_has_read_only_receipt_ui",
        "test_receipt_viewer_script_tag_has_matching_sri",
        "test_receipt_viewer_js_uses_receipt_only_read_only_rpc",
        "test_receipt_viewer_forbids_wallet_signing_storage_or_broadcast_surface",
        "test_actual_receipt_viewer_javascript_behavior",
        "receipt_viewer_behavior_harness.mjs",
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing receipt viewer regression marker: {marker}")
    for marker in (
        "testSuccessfulReceiptHighlightsUsdcTransfer",
        "testRevertedReceiptAndNullReceipt",
        "testWrongChainStopsBeforeReceipt",
        "testInvalidHashAvoidsRpc",
        "testRpcEnvelopeAndHashBindingFailClosed",
        "testTimeoutFailsClosed",
        "success_receipt_observed",
        "reverted_receipt_observed",
        "unknown_wrong_chain",
        "unknown_hash_mismatch",
    ):
        if marker not in harness:
            fail(f"{harness_relative}: missing receipt viewer behavior marker: {marker}")



def validate_transaction_status_playground() -> None:
    """Keep the transaction status playground read-only and wallet-free."""
    html_relative = "examples/transaction-status-playground/index.html"
    js_relative = "examples/transaction-status-playground/status.js"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    for marker in (
        'id="transaction-hash"',
        'id="expected-recipient"',
        'id="expected-amount"',
        'id="check-transaction"',
        'id="status-pill"',
        'id="status-check-list"',
        'id="transaction-status-json"',
        "Transaction Status Playground",
        "Read-only Arc Testnet RPC",
        "No wallet connection",
        "No transaction broadcast",
        "connect-src 'self' https://rpc.testnet.arc.network",
    ):
        if marker not in html:
            fail(f"{html_relative}: missing transaction status marker: {marker}")
    for marker in (
        "const ARC_TRANSACTION_STATUS = Object.freeze",
        "expectedChainId: 5042002",
        "expectedChainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "usdcDecimals: 6",
        "const TRANSFER_SELECTOR = 'a9059cbb'",
        "method: 'eth_chainId'",
        "method: 'eth_getTransactionByHash'",
        "method: 'eth_getTransactionReceipt'",
        "const RPC_TIMEOUT_MS = 10_000",
        "const MAX_RPC_RESPONSE_BYTES = 1_000_000",
        "const RPC_REQUEST_ID = 'arc-transaction-status-read-only'",
        "new AbortController()",
        "new TextEncoder().encode(responseText).byteLength",
        "window.clearTimeout(timeout)",
        "RPC response must be a JSON object",
        "RPC response envelope did not match the request",
        "RPC response must contain exactly one result or error field",
        "function hashMatchesExpected(value, expectedHash)",
        "rpcObjectHashesMatch",
        "unknown_hash_mismatch",
        "readOnlyRpcCheckOnly: true",
        "transactionBroadcast: false",
        "autonomousSpending: false",
        "humanApprovalRequired: true",
        "signingRequiresWalletChainGateAndHumanApproval: true",
        "function buildExpectedTransfer()",
        "function decodeTransferCalldata(data)",
        "function reviewExpectedTransfer(transaction, expectedTransfer)",
        "function withTransferEvidence(result, transaction, expectedTransfer)",
        "function classifyTransactionStatus(chainIdHex, transaction, receipt, expectedTransfer, expectedTransactionHash)",
        "evidenceVerdict",
        "settlementProven: false",
        "businessAcceptanceProven: false",
        "state: 'not_checked'",
        "state: 'pending'",
        "state: 'confirmed'",
        "state: 'failed'",
        "state: 'unknown'",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing transaction status marker: {marker}")
    for marker in ("window.ethereum", "personal_sign", "eth_sendTransaction", "wallet_switchEthereumChain", "signTransaction", "PRIVATE_KEY", "localStorage"):
        if marker in js:
            fail(f"{js_relative}: forbidden wallet/signing marker: {marker}")
    behavior_test = (ROOT / "scripts/test_transaction_status_behavior.py").read_text(encoding="utf-8")
    behavior_harness = (ROOT / "scripts/transaction_status_behavior_harness.mjs").read_text(encoding="utf-8")
    for marker in ("shutil.which(\"node\")", "transaction_status_behavior_harness.mjs", "timeout=30"):
        if marker not in behavior_test:
            fail(f"scripts/test_transaction_status_behavior.py: missing behavior test marker: {marker}")
    for marker in (
        "testConfirmedExpectedTransferShape",
        "testMismatchAndWrongChainFailClosed",
        "testInvalidExpectedFieldsAvoidRpc",
        "testRpcEnvelopeAndHashBindingFailClosed",
        "confirmed_expected_transfer_shape",
        "mismatch_expected_transfer",
        "unknown_wrong_chain",
        "unknown_hash_mismatch",
    ):
        if marker not in behavior_harness:
            fail(f"scripts/transaction_status_behavior_harness.mjs: missing behavior marker: {marker}")


def validate_guarded_wallet_send_gate() -> None:
    """Keep the only write-capable browser surface narrow and fail-closed."""
    html_relative = "examples/arc-testnet-wallet-send-gate/index.html"
    js_relative = "examples/arc-testnet-wallet-send-gate/wallet-send-gate.js"
    runbook_relative = "docs/guarded-wallet-send-runbook.md"
    gates_relative = "docs/custody-and-mainnet-gates.md"
    policy_relative = "examples/arc-testnet-wallet-send-gate/live-infrastructure-policy.example.json"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    runbook = (ROOT / runbook_relative).read_text(encoding="utf-8").lower()
    gates = (ROOT / gates_relative).read_text(encoding="utf-8").lower()
    policy = (ROOT / policy_relative).read_text(encoding="utf-8")

    for marker in (
        "Arc Testnet Wallet Send Gate",
        'id="risk-acknowledgement"',
        'id="connect-wallet"',
        'id="switch-network"',
        'id="freeze-intent"',
        'id="send-transaction"',
        'id="confirmation-phrase"',
        'id="final-send-confirmation"',
        "Disabled by default",
        "Arc Testnet only",
        "One attempt per page load",
        "No custody",
        "No private keys",
    ):
        if marker not in html:
            fail(f"{html_relative}: missing guarded send marker: {marker}")
    for marker in (
        "const ARC_TESTNET = Object.freeze",
        "chainId: 5042002",
        "chainIdHex: '0x4cef52'",
        "rpcUrl: 'https://rpc.testnet.arc.network'",
        "explorerUrl: 'https://testnet.arcscan.app'",
        "usdcAddress: '0x3600000000000000000000000000000000000000'",
        "usdcDecimals: 6",
        "maxAmountBaseUnits: 1000000n",
        "enableArcTestnetSend",
        "reviewed-testnet-only",
        "function parseUsdcAmount",
        "function encodeTransferCalldata",
        "function decodeTransferCalldata",
        "function buildGuardReport",
        "function canAttemptSend",
        "const ALLOWED_WALLET_METHODS = new Set",
        "if (!ALLOWED_WALLET_METHODS.has(request.method))",
        "topLevelContext: window.top === window.self",
        "['top-level-context', state.topLevelContext",
        "function isNonZeroAddress",
        "Recipient cannot be the pinned USDC token contract address.",
        "const failedPrerequisite = report.checks.find",
        "throw new Error(failedPrerequisite.detail",
        "Risk acknowledgement cleared. Freeze and review the intent again.",
        "sendAttempted = true",
        "method: 'eth_requestAccounts'",
        "method: 'wallet_switchEthereumChain'",
        "method: 'wallet_addEthereumChain'",
        "method: 'eth_sendTransaction'",
        "No automatic retry",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing guarded send marker: {marker}")
    for forbidden in (
        "personal_sign",
        "eth_sign",
        "signTransaction",
        "eth_sendRawTransaction",
        "PRIVATE_KEY",
        "seed phrase",
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "mainnet",
    ):
        if forbidden in js:
            fail(f"{js_relative}: forbidden guarded send marker: {forbidden}")
    for marker in (
        "injected user-controlled browser wallet",
        "wallet confirmation dialog is the only signing path",
        "no automatic retry",
        "one attempt per page load",
        "arc testnet only",
        "rollback",
    ):
        if marker not in runbook:
            fail(f"{runbook_relative}: missing guarded runbook marker: {marker}")
    for marker in (
        "non-custodial",
        "static site",
        "secret manager",
        "mainnet remains blocked",
        "upcoming",
        "separate security review",
        "no fake mainnet constants",
    ):
        if marker not in gates:
            fail(f"{gates_relative}: missing custody/mainnet gate marker: {marker}")
    for marker in (
        '"activeProfile": "arc-testnet-injected-wallet"',
        '"enabled": false',
        '"status": "blocked_official_configuration_upcoming"',
        '"implemented": false',
        '"mode": "non-custodial"',
        '"staticSiteMayHoldSecrets": false',
        '"maxAttemptsPerPageLoad": 1',
        '"transactionChainIdRequired": "0x4cef52"',
        '"topLevelBrowsingContextRequired": true',
        '"zeroAddressAllowed": false',
        '"tokenContractRecipientAllowed": false',
        '"automaticRetry": false',
    ):
        if marker not in policy:
            fail(f"{policy_relative}: missing fail-closed policy marker: {marker}")
    policy_validator = (ROOT / "scripts/validate_live_infrastructure_policy.py").read_text(encoding="utf-8")
    for marker in ("require_exact_keys", "reject_duplicate_keys", "object_pairs_hook=reject_duplicate_keys"):
        if marker not in policy_validator:
            fail(f"scripts/validate_live_infrastructure_policy.py: missing strict policy marker: {marker}")
    behavior_test = (ROOT / "scripts/test_arc_testnet_wallet_send_behavior.py").read_text(encoding="utf-8")
    behavior_harness = (ROOT / "scripts/wallet_send_behavior_harness.mjs").read_text(encoding="utf-8")
    for marker in ("shutil.which(\"node\")", "wallet_send_behavior_harness.mjs", "timeout=30"):
        if marker not in behavior_test:
            fail(f"scripts/test_arc_testnet_wallet_send_behavior.py: missing behavior test marker: {marker}")
    for marker in (
        "vm.runInContext(SOURCE",
        "testDefaultDisabled",
        "testExactOneShotSend",
        "testWrongChainAndAccountChangeBlock",
        "testRejectionKeepsOneShotLock",
        "eth_sendTransaction",
        "EXPECTED_DATA",
    ):
        if marker not in behavior_harness:
            fail(f"scripts/wallet_send_behavior_harness.mjs: missing fake-provider marker: {marker}")


def validate_job_escrow_simulator() -> None:
    """Keep the job escrow simulator local-only and review-gated."""
    html_relative = "examples/job-escrow-simulator/index.html"
    js_relative = "examples/job-escrow-simulator/simulator.js"
    test_relative = "scripts/test_job_escrow_simulator.py"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")
    for marker in (
        'id="request-changes"',
        'id="revise-work"',
        'id="reject-work"',
        'id="open-dispute"',
        'id="expire-job"',
        'id="cancel-job"',
        'id="revision-note"',
        'id="dispute-note"',
        "Request changes",
        "Revise work",
        "Reject no payout",
        "Open dispute",
        "Expire job",
        "Cancel job",
        "changes and disputes are simulated review notes",
        "terminal local review states with no payout release",
    ):
        if marker not in html:
            fail(f"{html_relative}: missing job escrow review marker: {marker}")
    for marker in (
        "changes_requested",
        "changesRequestedCount",
        "latestRevisionNote",
        "latestCloseNote",
        "terminalNoPayoutStates",
        "rejected_no_payout",
        "disputed_manual_review",
        "expired_no_payout",
        "cancelled_no_payout",
        "payoutReleased: status === 'payout_approved_simulation' ? 'simulated_only' : false",
        "contactsArbitrator: false",
        "contactsValidator: false",
        "payoutRelease: 'simulated_only_after_human_approval'",
        "arcTestnetChainId: 5042002",
        "arcTestnetChainIdHex: '0x4cef52'",
        "walletActionEnabled: false",
        "signingEnabled: false",
        "transactionBroadcast: false",
        "localOnly: true",
        "realEscrowContract: false",
        "buttons.requestChanges.disabled = status !== 'work_submitted'",
        "buttons.revise.disabled = status !== 'changes_requested'",
        "buttons.reject.disabled = status !== 'work_submitted'",
        "buttons.dispute.disabled = !['work_submitted', 'changes_requested'].includes(status)",
        "buttons.expire.disabled = !['posted', 'accepted_by_agent', 'escrow_funded_simulation', 'changes_requested'].includes(status)",
        "buttons.cancel.disabled = !['draft', 'posted', 'accepted_by_agent'].includes(status)",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing job escrow safety marker: {marker}")
    for marker in (
        "test_job_escrow_review_loop_controls_are_present",
        "test_job_escrow_json_exposes_review_and_arc_safety_flags",
        "test_job_escrow_state_machine_allows_revisions_before_payout",
        "test_job_escrow_state_machine_allows_terminal_no_payout_paths",
        "test_job_escrow_simulator_forbids_wallet_network_and_secret_surface",
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing job escrow regression marker: {marker}")
    for marker in ("fetch(", "XMLHttpRequest", "WebSocket", "window.ethereum", "ethereum.request", "eth_sendTransaction", "wallet_switchEthereumChain", "sendTransaction", "signTransaction", "PRIVATE_KEY", "localStorage"):
        if marker in html or marker in js:
            fail(f"{html_relative}/{js_relative}: forbidden network/wallet marker: {marker}")


def validate_arc_agent_treasury_lab() -> None:
    """Keep the local self-funding-agent product exact, bounded, and wallet-free."""
    html_relative = "examples/arc-agent-treasury-lab/index.html"
    js_relative = "examples/arc-agent-treasury-lab/treasury.js"
    test_relative = "scripts/test_arc_agent_treasury_lab.py"
    harness_relative = "scripts/arc_agent_treasury_behavior_harness.mjs"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")
    harness = (ROOT / harness_relative).read_text(encoding="utf-8")
    for marker in (
        "Arc Agent Treasury Lab",
        'id="review-task"',
        'id="run-loop"',
        'id="ledger"',
        'id="snapshot"',
        "No wallet, custody, mainnet, backend, signing, settlement, or transaction broadcast.",
    ):
        if marker not in html:
            fail(f"{html_relative}: missing treasury product marker: {marker}")
    for marker in (
        "const MICRO_USDC = 1_000_000",
        "request_replay_detected",
        "receipt_replay_detected",
        "single_task_cap_exceeded",
        "daily_spend_cap_exceeded",
        "protected_reserve_would_be_breached",
        "minimum_profit_not_met",
        "Runtime spend preflight failed closed",
        "settled: false",
        "transactionBroadcast: false",
        "autonomousSpendingEnabled: false",
        "mainnetEnabled: false",
        "custodyEnabled: false",
    ):
        if marker not in js:
            fail(f"{js_relative}: missing treasury safety marker: {marker}")
    for marker in (
        "test_product_surface_is_complete",
        "test_domain_exposes_fail_closed_policy_and_loop",
        "test_local_lab_forbids_wallet_network_storage_and_secrets",
        "test_actual_javascript_behavior",
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing treasury regression marker: {marker}")
    for marker in (
        "exact micro-USDC",
        "request replay reason missing",
        "single-task cap must fail closed",
        "reserve breach must fail closed",
        "runtime policy drift must fail closed before spend",
    ):
        if marker not in harness:
            fail(f"{harness_relative}: missing treasury behavior marker: {marker}")
    for marker in ("fetch(", "XMLHttpRequest", "WebSocket", "window.ethereum", "ethereum.request", "eth_sendTransaction", "eth_sendRawTransaction", "personal_sign", "signTypedData", "PRIVATE_KEY", "localStorage", "sessionStorage"):
        if marker in html or marker in js:
            fail(f"{html_relative}/{js_relative}: forbidden treasury network/wallet marker: {marker}")


def validate_agentic_maintainer_loop() -> None:
    """Keep the maintainer-agent loop discoverable and safety-anchored."""
    doc_relative = "docs/agentic-maintainer-loop.md"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")
    doc = (ROOT / doc_relative).read_text(encoding="utf-8")

    for marker in (
        "Loop 1: task execution",
        "Loop 2: verification",
        "Loop 3: event-driven maintenance",
        "Loop 4: improvement",
        "Human approval gates",
        "no custody",
        "no mainnet",
        "no private keys",
        "no signing",
        "no broadcast",
    ):
        if marker not in doc:
            fail(f"{doc_relative}: missing maintainer loop marker: {marker}")
    for surface, text in (
        ("README.md", readme),
        ("index.html", index),
        ("docs/viewer.js", viewer),
    ):
        if "agentic-maintainer-loop.md" not in text:
            fail(f"{surface}: missing agentic maintainer loop link")
    for marker in ("ethereum.request", "eth_sendTransaction", "wallet_switchEthereumChain", "sendTransaction", "signTransaction", "PRIVATE_KEY"):
        if marker in index:
            fail(f"index.html: forbidden maintainer loop live-wallet marker: {marker}")


def validate_arc_testnet_send_readiness_gate() -> None:
    """Keep the Arc Testnet send handoff narrow, explicit, and guard-first."""
    doc_relative = "docs/arc-testnet-send-readiness-gate.md"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")
    doc = (ROOT / doc_relative).read_text(encoding="utf-8")

    for marker in (
        "Arc Testnet Send Readiness Gate",
        "5042002",
        "0x4cef52",
        "unsigned transaction draft",
        "disabled by default",
        "eth_sendTransaction",
        "external wallet confirmation dialog is the only signing path",
        "top-level browsing context",
        "Zero addresses",
        "pinned USDC token contract",
        "one-attempt lock",
        "No private keys",
        "No mainnet profile",
        "Rollback criteria",
    ):
        if marker not in doc:
            fail(f"{doc_relative}: missing send readiness marker: {marker}")
    for surface, text in (
        ("README.md", readme),
        ("index.html", index),
        ("docs/viewer.js", viewer),
    ):
        if "arc-testnet-send-readiness-gate.md" not in text:
            fail(f"{surface}: missing Arc Testnet send readiness gate link")
    for marker in ("ethereum.request", "eth_sendTransaction", "wallet_switchEthereumChain", "sendTransaction", "signTransaction", "PRIVATE_KEY"):
        if marker in index:
            fail(f"index.html: forbidden send readiness live-wallet marker: {marker}")


def validate_arc_testnet_operator_runbook() -> None:
    """Keep the operator handoff manual, Arc-only, and fail-closed."""
    doc_relative = "docs/arc-testnet-operator-runbook.md"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")
    doc = (ROOT / doc_relative).read_text(encoding="utf-8")

    for marker in (
        "Arc Testnet Operator Runbook",
        "5042002",
        "0x4cef52",
        "manual review",
        "separate guarded Arc Testnet send lab",
        "no private keys",
        "no custody",
        "no mainnet",
        "no automatic retry",
        "no transaction request on page load",
        "top-level tab",
        "pinned-token-contract recipients fail closed",
    ):
        if marker not in doc:
            fail(f"{doc_relative}: missing operator runbook marker: {marker}")
    for surface, text in (
        ("README.md", readme),
        ("index.html", index),
        ("docs/viewer.js", viewer),
    ):
        if "arc-testnet-operator-runbook.md" not in text:
            fail(f"{surface}: missing Arc Testnet operator runbook link")
    for marker in ("ethereum.request", "eth_sendTransaction", "wallet_switchEthereumChain", "sendTransaction", "signTransaction", "PRIVATE_KEY"):
        if marker in index:
            fail(f"index.html: forbidden operator runbook live-wallet marker: {marker}")


def validate_arc_testnet_operator_evidence() -> None:
    """Keep the operator evidence packet strict, discoverable, and fail-closed."""
    doc_relative = "docs/arc-testnet-operator-evidence.md"
    example_relative = "examples/arc-testnet-operator-evidence/evidence.example.json"
    validator_relative = "scripts/validate_operator_evidence.py"
    test_relative = "scripts/test_operator_evidence.py"
    generator_relative = "scripts/generate_operator_evidence_draft.py"
    draft_test_relative = "scripts/test_operator_evidence_draft.py"
    reporter_relative = "scripts/report_operator_evidence.py"
    report_test_relative = "scripts/test_operator_evidence_report.py"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")
    doc = (ROOT / doc_relative).read_text(encoding="utf-8")
    example = (ROOT / example_relative).read_text(encoding="utf-8")
    validator = (ROOT / validator_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")
    generator = (ROOT / generator_relative).read_text(encoding="utf-8")
    draft_tests = (ROOT / draft_test_relative).read_text(encoding="utf-8")
    reporter = (ROOT / reporter_relative).read_text(encoding="utf-8")
    report_tests = (ROOT / report_test_relative).read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    test_all = (ROOT / "scripts/test_all.py").read_text(encoding="utf-8")

    for marker in (
        "Arc Testnet Operator Evidence Packet",
        "arc-mcp-builder-assistant.arcTestnet.operatorEvidence.v1",
        "5042002",
        "0x4cef52",
        "blocked_pending_separate_guarded_pr",
        "pre_send_readiness_baseline",
        "eth_sendTransaction",
        "separate guarded PR",
        "python scripts/validate_operator_evidence.py",
        "--expect-commit",
        "generate_operator_evidence_draft.py",
        "report_operator_evidence.py",
    ):
        if marker not in doc:
            fail(f"{doc_relative}: missing operator evidence marker: {marker}")
    for marker in (
        '"schema": "arc-mcp-builder-assistant.arcTestnet.operatorEvidence.v1"',
        '"chainId": 5042002',
        '"chainIdHex": "0x4cef52"',
        '"reviewedSurface": "pre_send_readiness_baseline"',
        '"transactionBroadcast": false',
        '"ethSendTransactionForbidden": true',
        '"separateGuardedPrRequired": true',
        '"status": "blocked_pending_separate_guarded_pr"',
    ):
        if marker not in example:
            fail(f"{example_relative}: missing safe evidence marker: {marker}")
    for marker in (
        "require_exact_keys",
        "validate_references",
        "validate_expected_commit",
        "SECRET_VALUE_PATTERNS",
        "MAX_PACKET_BYTES",
        "reject_duplicate_keys",
        "controls.{field} must be false",
        "decision.status must be blocked_pending_separate_guarded_pr",
    ):
        if marker not in validator:
            fail(f"{validator_relative}: missing fail-closed validator marker: {marker}")
    for marker in (
        "test_wrong_chain_fails_closed",
        "test_placeholder_commit_fails_closed",
        "test_non_string_commit_fails_closed",
        "test_broadcast_enabled_fails_closed",
        "test_unknown_field_fails_closed",
        "test_missing_evidence_fails_closed",
        "test_decision_cannot_approve_live_send",
        "test_non_repository_reference_fails_closed",
        "test_duplicate_reference_fails_closed",
        "test_credential_like_value_fails_closed",
        "test_cli_missing_packet_has_clear_error",
        "test_cli_accepts_matching_expected_commit",
        "test_cli_rejects_mismatched_expected_commit",
        "test_cli_rejects_malformed_expected_commit",
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing evidence regression marker: {marker}")
    for marker in (
        'resolved.open("x"',
        "resolved_relative",
        "strictValidationReady",
        "existingFileOverwritten",
        "transactionBroadcast",
        "draft_operator_evidence",
        "manualSecretReviewComplete",
        "blocked_pending_separate_guarded_pr",
        "LOCAL_DRAFT_SUFFIX",
    ):
        if marker not in generator:
            fail(f"{generator_relative}: missing safe draft generator marker: {marker}")
    for marker in (
        "test_draft_intentionally_fails_strict_validation",
        "test_cli_creates_ignored_local_draft",
        "test_cli_refuses_to_overwrite_existing_file",
        "test_cli_rejects_output_outside_repository",
        "test_cli_requires_local_draft_suffix",
        "test_cli_rejects_git_metadata_output",
        "test_cli_rejects_malformed_reviewed_commit",
    ):
        if marker not in draft_tests:
            fail(f"{draft_test_relative}: missing draft generator regression marker: {marker}")
    for marker in (
        "strict_validation_ready",
        "incomplete_or_unsafe",
        "credentialLikeValueDetected",
        '"liveSendApproved": False',
        "validate_packet",
        "validate_commit_sha",
    ):
        if marker not in reporter:
            fail(f"{reporter_relative}: missing read-only readiness report marker: {marker}")
    for marker in (
        "test_complete_example_is_strictly_ready",
        "test_draft_lists_all_incomplete_gates",
        "test_expected_commit_mismatch_is_reported",
        "test_malformed_expected_commit_exits_two",
        "test_malformed_json_exits_two",
        "test_credential_like_value_is_reported_without_echoing_it",
        "test_credential_like_key_is_reported_without_echoing_it",
        "test_report_does_not_expose_absolute_workspace_path",
        "test_report_redacts_credential_like_filename",
    ):
        if marker not in report_tests:
            fail(f"{report_test_relative}: missing readiness report regression marker: {marker}")
    if "*.operator-evidence.local.json" not in gitignore:
        fail(".gitignore: missing local operator evidence draft rule")
    if "scripts/test_operator_evidence.py" not in test_all:
        fail("scripts/test_all.py: missing operator evidence regression command")
    if "scripts/test_operator_evidence_draft.py" not in test_all:
        fail("scripts/test_all.py: missing operator evidence draft regression command")
    if "scripts/test_operator_evidence_report.py" not in test_all:
        fail("scripts/test_all.py: missing operator evidence report regression command")
    for forbidden in (
        "write_text(",
        "write_bytes(",
        '.open("w',
        ".open('w",
        "subprocess",
        "urllib",
        "socket",
        "requests",
    ):
        if forbidden in reporter:
            fail(f"{reporter_relative}: forbidden non-read-only marker: {forbidden}")
    for surface, text in (
        ("README.md", readme),
        ("index.html", index),
        ("docs/viewer.js", viewer),
    ):
        if "arc-testnet-operator-evidence.md" not in text:
            fail(f"{surface}: missing Arc Testnet operator evidence link")


def validate_robots_txt() -> None:
    relative = "robots.txt"
    text = (ROOT / relative).read_text(encoding="utf-8")
    lowered = text.lower()
    if "user-agent:" not in lowered:
        fail(f"{relative}: missing User-agent directive")
    if "sitemap:" not in lowered:
        fail(f"{relative}: missing Sitemap directive")
    if CANONICAL_BASE_URL + "sitemap.xml" not in text:
        fail(
            f"{relative}: Sitemap directive must point at "
            f"{CANONICAL_BASE_URL}sitemap.xml"
        )


def validate_sitemap_xml() -> None:
    relative = "sitemap.xml"
    text = (ROOT / relative).read_text(encoding="utf-8")
    if "<urlset" not in text or "sitemaps.org/schemas/sitemap" not in text:
        fail(f"{relative}: must be a sitemap 0.9 urlset document")
    for location in SITEMAP_REQUIRED_LOCATIONS:
        if f"<loc>{location}</loc>" not in text:
            fail(f"{relative}: missing <loc>{location}</loc>")


def main() -> None:
    validate_required_files()
    validate_workflow_security()
    validate_no_secrets()
    validate_public_text_integrity()
    validate_repository_line_ending_policy()
    validate_documented_secret_handling()
    validate_html()
    validate_reduced_motion_css()
    validate_responsive_layout_guards()
    validate_public_inventory_counts()
    validate_local_links()
    validate_markdown_local_links()
    validate_no_raw_markdown_links()
    validate_docs_viewer_registry()
    validate_completion_contract()
    validate_demo_safety_copy()
    validate_public_launch_packet()
    validate_arc_release_packet()
    validate_x402_boundary_demo()
    validate_arc_production_deployment_assets()
    validate_arc_testnet_status_helper()
    validate_payment_intent_playground_status_panel()
    validate_receipt_verifier_playground()
    validate_receipt_viewer()
    validate_payment_intent_receipt_matcher()
    validate_transaction_status_playground()
    validate_guarded_wallet_send_gate()
    validate_job_escrow_simulator()
    validate_arc_agent_treasury_lab()
    validate_agentic_maintainer_loop()
    validate_arc_testnet_send_readiness_gate()
    validate_arc_testnet_operator_runbook()
    validate_arc_testnet_operator_evidence()
    validate_robots_txt()
    validate_sitemap_xml()
    print("validation passed", file=sys.stdout)


if __name__ == "__main__":
    main()
