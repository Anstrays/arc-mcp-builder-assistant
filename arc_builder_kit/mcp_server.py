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
- generate_release_packet
- list_examples

Each tool result contains both human-readable `content` and `structuredContent`
so MCP clients can render text or consume JSON.
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


class McpError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def _json_response(id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _json_error(id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": id, "error": error}


def _run_script(
    script: Path,
    args: list[str],
    *,
    timeout: float = 120,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    if not script.exists():
        raise McpError(-32603, f"script not found: {script}")
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
    try:
        result = fetch_challenge(url)
        payload = result.to_dict()
        has_challenge = payload.get("challenge") is not None
        return _tool_text(
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
    try:
        verification = verify_receipt(
            tx_hash,
            expected_pay_to=expected_pay_to or None,
        )
        payload = verification.to_dict()
        return _tool_text(
            f"Receipt verified: {verification.verified} — {verification.reason}",
            payload,
        )
    except Exception as exc:
        return _tool_error(f"x402 verify receipt failed: {exc}")


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
        return _json_error(id, -32602, "invalid params: expected object")
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not isinstance(name, str) or not name:
        return _json_error(id, -32602, "missing or invalid tool name")
    if not isinstance(arguments, dict):
        return _json_error(id, -32602, "invalid arguments: expected object")
    if name not in TOOL_HANDLERS:
        return _json_error(id, -32601, f"unknown tool: {name}")
    try:
        result = TOOL_HANDLERS[name](arguments)
    except McpError as exc:
        return _json_error(id, exc.code, exc.message, exc.data)
    except subprocess.TimeoutExpired:
        return _json_error(id, -32000, f"tool '{name}' timed out")
    except Exception as exc:  # noqa: BLE001 - catch-all for tool safety
        return _json_error(id, -32603, f"tool '{name}' failed: {exc}")
    return _json_response(id, result)


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    if request.get("jsonrpc") != "2.0":
        return _json_error(request.get("id"), -32600, "invalid JSON-RPC version")
    id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})
    if not isinstance(method, str):
        return _json_error(id, -32600, "invalid method")
    if method == "initialize":
        return handle_initialize(id, params)
    if method == "tools/list":
        return handle_tools_list(id, params)
    if method == "tools/call":
        return handle_tools_call(id, params)
    return _json_error(id, -32601, f"method not found: {method}")


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
                response = _json_error(None, -32700, "request too large")
                print(json.dumps(response), flush=True)
                continue
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _json_error(None, -32700, f"parse error: {exc}")
            print(json.dumps(response), flush=True)
            continue
        if not isinstance(request, dict):
            response = _json_error(None, -32600, "invalid request")
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
