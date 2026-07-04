#!/usr/bin/env python3
"""Arc Builder MCP server (stdio).

Exposes the Arc MCP Builder Assistant kit as MCP tools over stdio JSON-RPC.
The server is dependency-free and stays local-only by default. It does not
connect wallets, sign, broadcast, or handle secrets. Network calls happen only
when a tool argument explicitly requests an opt-in read-only check.

Supported JSON-RPC methods:
- initialize
- tools/list
- tools/call

Supported tools:
- arc_builder_doctor
- list_templates
- scaffold_project
- validate_repo
- get_arc_testnet_facts
- x402_manifest
- x402_paid_request
- x402_fetch_challenge
- x402_verify_receipt
- wallet_status
- wallet_balance
- wallet_prepare_send
- generate_release_packet
- list_examples

Each tool result contains both human-readable `content` and `structuredContent`
and a `meta` block with `durationMs`. Streaming progress notifications are
emitted on stderr for long-running tools (HTTP fetch, RPC verify, balance check).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Callable

from arc_builder_kit import __version__
from arc_builder_kit._paths import (
    CONFIG_DIR,
    DEFAULT_OUTPUT_ROOT,
    EXAMPLES_DIR,
    TEMPLATES_DIR,
)
from arc_builder_kit.doctor import main as doctor_main
from arc_builder_kit.release_packet import main as release_packet_main
from arc_builder_kit.validate_repo import main as validate_main

X402_SERVER = EXAMPLES_DIR / "x402-local-challenge-server" / "server.py"

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "arc-builder-mcp"
SERVER_VERSION = __version__
MAX_REQUEST_BYTES = 1_000_000


# ---------------------------------------------------------------------------
# MCP Server v2 — structured errors, typed codes, progress notifications
# ---------------------------------------------------------------------------

# Standard JSON-RPC error codes
ERR_PARSE          = -32700
ERR_INVALID_REQ    = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_INTERNAL       = -32603
ERR_TIMEOUT        = -32000
ERR_SERVER         = -32001  # server error (transient)
ERR_SERVER_BUSY    = -32002  # server overloaded / rate-limited
ERR_PAYMENT        = -32050  # custom: x402 payment error
ERR_RPC            = -32060  # custom: upstream RPC error


class McpError(Exception):
    """Base MCP error with structured fields.

    Fields:
        code:       JSON-RPC error code (negative int)
        message:    machine-readable short label
        details:    optional structured payload (dict)
        user_message: optional human-facing explanation
        retry_hint:  optional advice: 'retry', 'backoff', 'fix_input', 'contact_support'
    """
    def __init__(
        self,
        code: int,
        message: str,
        *,
        details: Any = None,
        user_message: str | None = None,
        retry_hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.user_message = user_message
        self.retry_hint = retry_hint


class ValidationError(McpError):
    """Input validation failure (ERR_INVALID_PARAMS)."""
    def __init__(self, message: str, *, details: Any = None, user_message: str | None = None) -> None:
        super().__init__(ERR_INVALID_PARAMS, message, details=details, user_message=user_message, retry_hint="fix_input")


class ToolNotFoundError(McpError):
    """Unknown tool (ERR_METHOD_NOT_FOUND)."""
    def __init__(self, name: str) -> None:
        super().__init__(ERR_METHOD_NOT_FOUND, f"unknown tool: {name}", retry_hint="fix_input")


class TimeoutError(McpError):
    """Tool execution timed out (ERR_TIMEOUT)."""
    def __init__(self, tool_name: str, timeout: float) -> None:
        super().__init__(
            ERR_TIMEOUT,
            f"tool '{tool_name}' timed out after {timeout}s",
            retry_hint="retry",
            user_message="The operation took too long. Check network connectivity and try again.",
        )


class RpcError(McpError):
    """Upstream RPC call failure (ERR_RPC, custom)."""
    def __init__(self, message: str, *, details: Any = None, user_message: str | None = None) -> None:
        super().__init__(ERR_RPC, message, details=details, user_message=user_message, retry_hint="retry")


class PaymentError(McpError):
    """x402 payment verification failure (ERR_PAYMENT, custom)."""
    def __init__(self, message: str, *, details: Any = None, user_message: str | None = None) -> None:
        super().__init__(ERR_PAYMENT, message, details=details, user_message=user_message, retry_hint="fix_input")


def _emit_progress(progress: float, total: float, message: str | None = None) -> None:
    """Emit a progress notification on stderr (streaming)."""
    params: dict[str, Any] = {"progress": progress, "total": total}
    if message is not None:
        params["message"] = message
    notification = json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/progress",
        "params": params,
    })
    print(notification, file=sys.stderr, flush=True)


def _to_error_dict(exc: McpError) -> dict[str, Any]:
    """Convert a typed McpError to a JSON-RPC error dict."""
    error: dict[str, Any] = {"code": exc.code, "message": exc.message}
    data: dict[str, Any] = {}
    if exc.details is not None:
        data["details"] = exc.details
    if exc.user_message is not None:
        data["userMessage"] = exc.user_message
    if exc.retry_hint is not None:
        data["retryHint"] = exc.retry_hint
    if data:
        error["data"] = data
    return error


def _json_response(id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _json_error(id: Any, exc: McpError) -> dict[str, Any]:
    """Build a JSON-RPC error response from a typed McpError."""
    return {"jsonrpc": "2.0", "id": id, "error": _to_error_dict(exc)}


def _tool_result(text: str, structured: Any, *, duration: float = 0.0) -> dict[str, Any]:
    """Build a v2 tool result with metadata."""
    result: dict[str, Any] = {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
        "isError": False,
    }
    meta: dict[str, Any] = {}
    if duration:
        meta["durationMs"] = int(duration * 1000)
    if meta:
        result["meta"] = meta
    return result


def _run_script(
    script: Path,
    args: list[str],
    *,
    timeout: float = 120,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    if not script.exists():
        raise McpError(ERR_INTERNAL, f"script not found: {script}", retry_hint="fix_input", details={"script": str(script)})
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise McpError(-32603, f"file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise McpError(-32603, f"invalid JSON: {exc}") from exc


def _list_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(
        d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir() and (d / "README.md").exists()
    )


def _tool_text(text: str, structured: Any) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
        "isError": False,
    }


def _tool_error(text: str, structured: Any | None = None) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
        "isError": True,
    }


def tool_initialize(_params: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
        "capabilities": {"tools": {}},
        "safety": {
            "localOnlyDefault": True,
            "noWallet": True,
            "noSigning": True,
            "noBroadcast": True,
            "testnetOnly": True,
            "noSecrets": True,
        },
    }


def tool_list_templates(_params: dict[str, Any]) -> dict[str, Any]:
    names = _list_templates()
    titles: dict[str, str] = {}
    for name in names:
        readme = TEMPLATES_DIR / name / "README.md"
        if readme.exists():
            first = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            titles[name] = first
    return _tool_text(
        f"Available templates: {', '.join(names) if names else '(none)'}",
        {"templates": names, "titles": titles, "count": len(names)},
    )


def tool_scaffold_project(params: dict[str, Any]) -> dict[str, Any]:
    template = params.get("template")
    output = params.get("output")
    force = bool(params.get("force", False))
    if not isinstance(template, str) or not template:
        return _tool_error("missing or invalid 'template' argument")
    if not isinstance(output, str) or not output:
        return _tool_error("missing or invalid 'output' argument")
    available = _list_templates()
    if template not in available:
        return _tool_error(
            f"unknown template: {template}; available: {', '.join(available)}",
            {"available": available},
        )
    source = TEMPLATES_DIR / template
    dest = Path(output).expanduser().resolve()
    if dest.exists() and not force:
        return _tool_error(
            f"output already exists: {dest}; set force=true to overwrite",
            {"exists": str(dest)},
        )
    if dest.exists() and force:
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    return _tool_text(
        f"Scaffolded '{template}' to {dest}",
        {"template": template, "output": str(dest), "force": force},
    )


def tool_validate_repo(_params: dict[str, Any]) -> dict[str, Any]:
    try:
        validate_main()
        ok = True
        text = "Repository validation passed."
    except SystemExit as exc:
        ok = False
        text = f"Repository validation failed: {exc}"
    return _tool_text(text, {"ok": ok})


def tool_arc_builder_doctor(params: dict[str, Any]) -> dict[str, Any]:
    args = ["--json"]
    if params.get("full"):
        args.append("--full")
    if params.get("include_arc_rpc"):
        args.append("--include-arc-rpc")
    if params.get("include_public_site"):
        args.append("--include-public-site")
    old_stdout = sys.stdout
    try:
        sys.stdout = StringIO()
        rc = doctor_main(args)
        stdout = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    try:
        report = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        report = {"raw": stdout, "error": "doctor output was not valid JSON"}
    ok = rc == 0 and report.get("status") in ("pass", "warn")
    return _tool_text(
        f"Doctor report status: {report.get('status', 'unknown')}",
        {"ok": ok, "report": report},
    )


def tool_get_arc_testnet_facts(_params: dict[str, Any]) -> dict[str, Any]:
    facts = _load_json(CONFIG_DIR / "arc_testnet.facts.json")
    return _tool_text(
        f"Arc Testnet chain ID: {facts.get('chainId', 'unknown')}",
        facts,
    )


def tool_x402_manifest(_params: dict[str, Any]) -> dict[str, Any]:
    result = _run_script(X402_SERVER, ["--print-manifest"], timeout=60)
    try:
        manifest = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        manifest = {"raw": result.stdout}
    ok = result.returncode == 0
    return _tool_text(
        "x402 manifest retrieved." if ok else "x402 manifest failed.",
        {"ok": ok, "manifest": manifest, "stderr": result.stderr},
    )


def tool_x402_paid_request(params: dict[str, Any]) -> dict[str, Any]:
    """Fetch a 402 challenge or verify a paid resource on Arc Testnet."""
    from arc_builder_kit.x402_client import paid_request
    url = params.get("url", "")
    payment_proof = params.get("payment_proof", "")
    if not isinstance(url, str) or not url:
        return _tool_error("missing or invalid 'url' argument")
    if not isinstance(payment_proof, str):
        return _tool_error("'payment_proof' must be a string")
    try:
        result = paid_request(url, payment_proof or None)
        payload = result.to_dict()
        stage = "challenge" if result.receipt_verification is None else "verification"
        return _tool_text(
            f"x402 flow stage: {stage}",
            payload,
        )
    except Exception as exc:
        return _tool_error(f"x402 flow failed: {exc}")


def tool_x402_fetch_challenge(params: dict[str, Any]) -> dict[str, Any]:
    """Fetch a 402 payment challenge from an x402-enabled endpoint."""
    from arc_builder_kit.x402_client import fetch_challenge
    url = params.get("url", "")
    if not isinstance(url, str) or not url:
        return _tool_error("missing or invalid 'url' argument")
    _emit_progress(0.2, 1.0, f"Fetching challenge from {url}...")
    try:
        result = fetch_challenge(url)
        _emit_progress(1.0, 1.0, "Challenge fetched.")
        payload = result.to_dict()
        has_challenge = payload.get("challenge") is not None
        return _tool_result(
            f"x402 challenge fetched: {len(payload.get('challenge', {}).get('requirements', []))} requirement(s)"
            if has_challenge
            else f"No 402 challenge — server returned HTTP {payload.get('resourceStatus')}",
            payload,
        )
    except Exception as exc:
        return _tool_error(f"x402 fetch challenge failed: {exc}")


def tool_x402_verify_receipt(params: dict[str, Any]) -> dict[str, Any]:
    """Verify an on-chain USDC payment receipt on Arc Testnet."""
    from arc_builder_kit.x402_client import verify_receipt, validate_tx_hash
    tx_hash = params.get("tx_hash", "")
    expected_pay_to = params.get("expected_pay_to")
    if not isinstance(tx_hash, str) or not tx_hash:
        return _tool_error("missing or invalid 'tx_hash' argument")
    try:
        validate_tx_hash(tx_hash)
    except ValueError as exc:
        return _tool_error(f"invalid tx_hash: {exc}")
    if expected_pay_to is not None and (not isinstance(expected_pay_to, str) or not expected_pay_to):
        return _tool_error("'expected_pay_to' must be a non-empty string")
    _emit_progress(0.2, 1.0, "Verifying transaction receipt on Arc Testnet...")
    try:
        verification = verify_receipt(
            tx_hash,
            expected_pay_to=expected_pay_to or None,
        )
        _emit_progress(1.0, 1.0, "Verification complete.")
        payload = verification.to_dict()
        return _tool_result(
            f"Receipt verified: {verification.verified} — {verification.reason}",
            payload,
        )
    except Exception as exc:
        return _tool_error(f"x402 verify receipt failed: {exc}")


def tool_wallet_status(params: dict[str, Any]) -> dict[str, Any]:
    """Show wallet guard status summary."""
    from arc_builder_kit.circle_wallet_sdk import build_wallet_status_summary, prepare_send_intent
    payload = build_wallet_status_summary()
    env_ok = payload.get("environment", {}).get("readyForManualSdkRun", False)
    return _tool_result(
        f"Wallet guard status: {'ready' if env_ok else 'missing env vars'}",
        payload,
    )


def tool_wallet_balance(params: dict[str, Any]) -> dict[str, Any]:
    """Check USDC balance on Arc Testnet (read-only RPC)."""
    from arc_builder_kit.circle_wallet_sdk import get_usdc_balance
    address = params.get("address", "")
    if not isinstance(address, str) or not address.startswith("0x") or len(address) != 42:
        return _tool_error(f"invalid address: {address!r}; expected 0x-prefixed 42-char EVM address")
    _emit_progress(0.3, 1.0, f"Checking USDC balance for {address}...")
    try:
        payload = get_usdc_balance(address)
        _emit_progress(1.0, 1.0, "Balance retrieved.")
    except Exception as exc:
        return _tool_error(f"balance check failed: {exc}")
    if not payload.get("ok"):
        return _tool_error(payload.get("error", "unknown"))
    return _tool_result(
        f"USDC balance: {payload['balanceUSDC']} (Arc Testnet, chain {payload['chainId']})",
        payload,
    )


def tool_wallet_prepare_send(params: dict[str, Any]) -> dict[str, Any]:
    """Prepare a guarded USDC send intent for human review (no broadcast)."""
    from arc_builder_kit.circle_wallet_sdk import prepare_send_intent
    to_address = params.get("to_address", "")
    amount = params.get("amount", "")
    if not isinstance(to_address, str) or not to_address:
        return _tool_error("missing or invalid 'to_address' argument")
    if not isinstance(amount, str) or not amount:
        return _tool_error("missing or invalid 'amount' argument")
    network = params.get("network", "ARC-TESTNET")
    payload = prepare_send_intent(to_address=to_address, amount=amount, network=network)
    if not payload.get("ok"):
        return _tool_error(payload.get("error", "unknown"), payload)
    return _tool_result(
        f"Send intent prepared: {payload['intent']['amount']} USDC → {payload['intent']['toAddress'][:10]}...",
        payload,
    )


def tool_generate_release_packet(params: dict[str, Any]) -> dict[str, Any]:
    output = params.get("output")
    force = bool(params.get("force", False))
    out = (
        Path(output).expanduser().resolve()
        if isinstance(output, str) and output
        else DEFAULT_OUTPUT_ROOT / ".arc-release-packet"
    )
    argv = ["--out", str(out)]
    if force:
        argv.append("--force")
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        try:
            rc = release_packet_main(argv)
        except SystemExit as exc:
            rc = int(exc.code) if isinstance(exc.code, int) else 1
    stdout = stdout_buffer.getvalue()
    stderr = stderr_buffer.getvalue()
    ok = rc == 0
    structured: dict[str, Any] = {"ok": ok, "output": str(out), "force": force}
    if ok:
        files = sorted(p.name for p in out.iterdir()) if out.exists() else []
        structured["files"] = files
        return _tool_text(
            f"Generated release packet in {out} ({len(files)} files).",
            structured,
        )
    structured["stdout"] = stdout
    structured["stderr"] = stderr
    detail = stderr.strip() or stdout.strip() or f"exit {rc}"
    return _tool_error(f"Release packet generation failed: {detail}", structured)


def tool_list_examples(_params: dict[str, Any]) -> dict[str, Any]:
    if not EXAMPLES_DIR.exists():
        return _tool_text("No examples directory found.", {"examples": [], "count": 0})
    examples: list[dict[str, str]] = []
    for path in sorted(EXAMPLES_DIR.iterdir()):
        if path.is_dir() and (path / "index.html").exists():
            readme = path / "README.md"
            title = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip() if readme.exists() else path.name
            examples.append({"id": path.name, "title": title})
    return _tool_text(
        f"Available examples: {', '.join(e['id'] for e in examples) if examples else '(none)'}",
        {"examples": examples, "count": len(examples)},
    )


TOOLS: dict[str, dict[str, Any]] = {
    "arc_builder_doctor": {
        "description": "Run Arc Builder Doctor and return a structured report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "full": {"type": "boolean", "description": "Run full local verification."},
                "include_arc_rpc": {
                    "type": "boolean",
                    "description": "Opt-in read-only Arc Testnet RPC check.",
                },
                "include_public_site": {
                    "type": "boolean",
                    "description": "Opt-in public GitHub Pages health check.",
                },
            },
            "additionalProperties": False,
        },
    },
    "list_templates": {
        "description": "List available Arc builder starter templates.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    "scaffold_project": {
        "description": "Copy a starter template into a new project directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template": {"type": "string", "description": "Template name."},
                "output": {"type": "string", "description": "Destination directory."},
                "force": {"type": "boolean", "description": "Overwrite existing directory."},
            },
            "required": ["template", "output"],
            "additionalProperties": False,
        },
    },
    "validate_repo": {
        "description": "Run repository validation checks.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    "get_arc_testnet_facts": {
        "description": "Return the reviewed Arc Testnet facts object.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    "x402_manifest": {
        "description": "Return the local x402 paid-agent manifest.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    "generate_release_packet": {
        "description": "Generate a local maintainer release packet for PR/release review.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "description": "Output directory (default: .arc-release-packet/)."},
                "force": {"type": "boolean", "description": "Overwrite existing packet directory."},
            },
            "additionalProperties": False,
        },
    },
    "list_examples": {
        "description": "List available browser-facing examples in the kit.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    "x402_paid_request": {
        "description": "Fetch a 402 payment challenge from a URL, or verify a paid resource with a transaction hash proof on Arc Testnet. Read-only, no keys, no broadcast.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The x402-enabled endpoint URL."},
                "payment_proof": {"type": "string", "description": "Optional transaction hash proving payment. If empty, returns the 402 challenge for human review."},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    "x402_fetch_challenge": {
        "description": "Fetch a 402 payment challenge from an x402-enabled endpoint. Returns the challenge requirements, payment intent, and safety flags. Read-only, no keys, no broadcast.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The x402-enabled endpoint URL to fetch a challenge from."},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    "x402_verify_receipt": {
        "description": "Verify an on-chain USDC payment receipt on Arc Testnet. Checks the transaction receipt for USDC Transfer events from the correct sender/recipient. Read-only RPC, no keys, no broadcast.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_hash": {"type": "string", "description": "Arc Testnet transaction hash (0x-prefixed, 64 hex chars)."},
                "expected_pay_to": {"type": "string", "description": "Optional expected recipient address. If provided, the tool confirms the USDC Transfer went to this address."},
            },
            "required": ["tx_hash"],
            "additionalProperties": False,
        },
    },
    "wallet_status": {
        "description": "Show the Circle Wallet SDK guard status summary: manifest, env checks, safety flags. No network calls, no side effects.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    "wallet_balance": {
        "description": "Check USDC balance of an EVM address on Arc Testnet via read-only RPC (eth_call). No keys, no broadcast.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "EVM address to check USDC balance for (0x-prefixed, 42 chars)."},
            },
            "required": ["address"],
            "additionalProperties": False,
        },
    },
    "wallet_prepare_send": {
        "description": "Prepare a guarded USDC send intent for human review. Validates the recipient address and amount, returns a pending_human_approval intent. Does NOT broadcast or sign anything.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to_address": {"type": "string", "description": "Recipient EVM address (0x-prefixed, 42 chars)."},
                "amount": {"type": "string", "description": "USDC amount as decimal string (e.g. '1.50')."},
                "network": {"type": "string", "description": "Network identifier (default: ARC-TESTNET)."},
            },
            "required": ["to_address", "amount"],
            "additionalProperties": False,
        },
    },
}

TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "arc_builder_doctor": tool_arc_builder_doctor,
    "list_templates": tool_list_templates,
    "scaffold_project": tool_scaffold_project,
    "validate_repo": tool_validate_repo,
    "get_arc_testnet_facts": tool_get_arc_testnet_facts,
    "x402_manifest": tool_x402_manifest,
    "generate_release_packet": tool_generate_release_packet,
    "list_examples": tool_list_examples,
    "x402_paid_request": tool_x402_paid_request,
    "x402_fetch_challenge": tool_x402_fetch_challenge,
    "x402_verify_receipt": tool_x402_verify_receipt,
    "wallet_status": tool_wallet_status,
    "wallet_balance": tool_wallet_balance,
    "wallet_prepare_send": tool_wallet_prepare_send,
}


def handle_initialize(id: Any, _params: Any) -> dict[str, Any]:
    return _json_response(id, tool_initialize({}))


def handle_tools_list(id: Any, _params: Any) -> dict[str, Any]:
    tools = [
        {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
        for name, spec in TOOLS.items()
    ]
    return _json_response(id, {"tools": tools})


def handle_tools_call(id: Any, params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        return _json_error(id, ValidationError("invalid params: expected object"))
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not isinstance(name, str) or not name:
        return _json_error(id, ValidationError("missing or invalid tool name"))
    if not isinstance(arguments, dict):
        return _json_error(id, ValidationError("invalid arguments: expected object"))
    if name not in TOOL_HANDLERS:
        return _json_error(id, ToolNotFoundError(name))
    import time
    t0 = time.time()
    try:
        result = TOOL_HANDLERS[name](arguments)
    except McpError as exc:
        return _json_error(id, exc)
    except subprocess.TimeoutExpired:
        return _json_error(id, TimeoutError(name, timeout=120))
    except Exception as exc:  # noqa: BLE001 - catch-all for tool safety
        return _json_error(id, McpError(ERR_INTERNAL, f"tool '{name}' failed", details={"error": repr(exc)}, user_message=str(exc), retry_hint="retry"))
    duration = time.time() - t0
    if not result.get("meta"):
        result["meta"] = {}
    if "durationMs" not in result["meta"]:
        result["meta"]["durationMs"] = int(duration * 1000)
    return _json_response(id, result)


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    if request.get("jsonrpc") != "2.0":
        return _json_error(request.get("id"), ValidationError("invalid JSON-RPC version (must be 2.0)"))
    id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})
    if not isinstance(method, str):
        return _json_error(id, ValidationError("invalid method: must be a string"))
    if method == "initialize":
        return handle_initialize(id, params)
    if method == "tools/list":
        return handle_tools_list(id, params)
    if method == "tools/call":
        return handle_tools_call(id, params)
    return _json_error(id, McpError(ERR_METHOD_NOT_FOUND, f"method not found: {method}", retry_hint="fix_input"))


def main() -> int:
    while True:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            break
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            if len(line.encode("utf-8")) > MAX_REQUEST_BYTES:
                response = _json_error(None, McpError(ERR_PARSE, "request too large", retry_hint="fix_input", user_message=f"Request exceeds {MAX_REQUEST_BYTES} byte limit."))
                print(json.dumps(response), flush=True)
                continue
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _json_error(None, McpError(ERR_PARSE, f"parse error", details={"error": str(exc)}, retry_hint="fix_input"))
            print(json.dumps(response), flush=True)
            continue
        if not isinstance(request, dict):
            response = _json_error(None, ValidationError("invalid request: expected JSON object"))
            print(json.dumps(response), flush=True)
            continue
        if "id" not in request:
            # JSON-RPC notification: consume silently.
            continue
        response = handle_request(request)
        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
