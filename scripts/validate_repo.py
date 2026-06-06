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
    ".env.example",
    ".github/workflows/validate.yml",
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
    "docs/transaction-status-playground.md",
    "docs/x402-mcp-manifest.md",
    "docs/x402-demo-transcript.md",
    "docs/arc-production-deployment.md",
    "docs/prompt-library.md",
    "docs/arc-builder-readiness-checklist.md",
    "docs/current-readiness-report.md",
    "docs/arc-testnet-integration-runbook.md",
    "docs/arc-wallet-integration-notes.md",
    "docs/wallet-preflight-contract.md",
    "docs/arc-testnet-send-readiness-gate.md",
    "docs/arc-testnet-operator-runbook.md",
    "docs/arc-testnet-operator-evidence.md",
    "docs/agent-commerce-use-cases.md",
    "docs/agent-commerce-components.md",
    "docs/agent-commerce-flow-library.md",
    "docs/agent-commerce-review-packet.md",
    "docs/job-escrow-demo.md",
    "docs/mcp-query-examples.md",
    "docs/arc-house-submission.md",
    "docs/build-log.md",
    "docs/view.html",
    "docs/viewer.js",
    "prompts/explain-arc-docs.md",
    "prompts/build-payment-intent-demo.md",
    "prompts/register-agent-notes.md",
    "prompts/deploy-contracts-on-arc.md",
    "prompts/wire-arc-testnet-status.md",
    "examples/payment-intent-demo/index.html",
    "examples/payment-intent-playground/index.html",
    "examples/payment-intent-playground/playground.js",
    "examples/receipt-verifier-playground/index.html",
    "examples/receipt-verifier-playground/verifier.js",
    "examples/transaction-status-playground/index.html",
    "examples/transaction-status-playground/status.js",
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
    "examples/arc-testnet-operator-evidence/evidence.example.json",
    "examples/x402-local-challenge-server/README.md",
    "examples/x402-local-challenge-server/.env.example",
    "examples/x402-local-challenge-server/server.py",
    "scripts/check_arc_testnet_status.py",
    "scripts/live_arc_gateway_smoke.py",
    "scripts/test_all.py",
    "scripts/test_arc_production_deployment.py",
    "scripts/test_payment_intent_playground.py",
    "scripts/test_x402_boundary.py",
    "scripts/test_transaction_status_playground.py",
    "scripts/test_agent_commerce_components.py",
    "scripts/test_agent_commerce_flows.py",
    "scripts/test_agent_commerce_review_packet.py",
    "scripts/test_agent_identity_profile_preview.py",
    "scripts/test_job_escrow_simulator.py",
    "scripts/validate_operator_evidence.py",
    "scripts/test_operator_evidence.py",
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
    "examples/transaction-status-playground/index.html",
    "examples/agent-commerce-components/index.html",
    "examples/agent-commerce-flows/index.html",
    "examples/agent-commerce-review-packet/index.html",
    "examples/agent-identity-profile-preview/index.html",
    "examples/job-escrow-simulator/index.html",
]

CANONICAL_BASE_URL = "https://anstrays.github.io/arc-mcp-builder-assistant/"
SITE_BASE_PATH = "/arc-mcp-builder-assistant/"
SITEMAP_REQUIRED_LOCATIONS = (
    CANONICAL_BASE_URL,
    CANONICAL_BASE_URL + "docs/view.html",
    CANONICAL_BASE_URL + "examples/payment-intent-demo/",
    CANONICAL_BASE_URL + "examples/payment-intent-playground/",
    CANONICAL_BASE_URL + "examples/receipt-verifier-playground/",
    CANONICAL_BASE_URL + "examples/transaction-status-playground/",
    CANONICAL_BASE_URL + "examples/agent-commerce-components/",
    CANONICAL_BASE_URL + "examples/agent-commerce-flows/",
    CANONICAL_BASE_URL + "examples/agent-commerce-review-packet/",
    CANONICAL_BASE_URL + "examples/agent-identity-profile-preview/",
    CANONICAL_BASE_URL + "examples/job-escrow-simulator/",
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

# Files we never want to scan for secrets — they only describe patterns,
# not real credentials.
SECRET_SCAN_SKIP = {
    Path("scripts/validate_repo.py"),
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
        "X402_DEMO_MAINNET_ENABLED",
        "PaymentConfig.from_env()",
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



def validate_transaction_status_playground() -> None:
    """Keep the transaction status playground read-only and wallet-free."""
    html_relative = "examples/transaction-status-playground/index.html"
    js_relative = "examples/transaction-status-playground/status.js"
    html = (ROOT / html_relative).read_text(encoding="utf-8")
    js = (ROOT / js_relative).read_text(encoding="utf-8")
    for marker in (
        'id="transaction-hash"',
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
        "method: 'eth_chainId'",
        "method: 'eth_getTransactionByHash'",
        "method: 'eth_getTransactionReceipt'",
        "readOnlyRpcCheckOnly: true",
        "transactionBroadcast: false",
        "autonomousSpending: false",
        "humanApprovalRequired: true",
        "signingRequiresWalletChainGateAndHumanApproval: true",
        "function classifyTransactionStatus(chainIdHex, transaction, receipt)",
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


def validate_arc_testnet_send_readiness_gate() -> None:
    """Keep the future Arc Testnet send handoff docs-only and guard-first."""
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
        "final local confirmation",
        "No wallet connection in this increment",
        "No private keys",
        "No signing",
        "No transaction broadcast",
        "eth_sendTransaction remains forbidden",
        "rollback criteria",
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
    """Keep the operator handoff manual, Arc-only, and docs-only."""
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
        "eth_sendTransaction remains forbidden",
        "no private keys",
        "no signing",
        "no transaction broadcast",
        "separate guarded PR",
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
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    viewer = (ROOT / "docs/viewer.js").read_text(encoding="utf-8")
    doc = (ROOT / doc_relative).read_text(encoding="utf-8")
    example = (ROOT / example_relative).read_text(encoding="utf-8")
    validator = (ROOT / validator_relative).read_text(encoding="utf-8")
    tests = (ROOT / test_relative).read_text(encoding="utf-8")
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
        "SECRET_VALUE_PATTERNS",
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
    ):
        if marker not in tests:
            fail(f"{test_relative}: missing evidence regression marker: {marker}")
    if "scripts/test_operator_evidence.py" not in test_all:
        fail("scripts/test_all.py: missing operator evidence regression command")
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
    validate_no_secrets()
    validate_html()
    validate_reduced_motion_css()
    validate_local_links()
    validate_no_raw_markdown_links()
    validate_docs_viewer_registry()
    validate_demo_safety_copy()
    validate_public_launch_packet()
    validate_x402_boundary_demo()
    validate_arc_production_deployment_assets()
    validate_arc_testnet_status_helper()
    validate_payment_intent_playground_status_panel()
    validate_receipt_verifier_playground()
    validate_transaction_status_playground()
    validate_job_escrow_simulator()
    validate_arc_testnet_send_readiness_gate()
    validate_arc_testnet_operator_runbook()
    validate_arc_testnet_operator_evidence()
    validate_robots_txt()
    validate_sitemap_xml()
    print("validation passed", file=sys.stdout)


if __name__ == "__main__":
    main()
