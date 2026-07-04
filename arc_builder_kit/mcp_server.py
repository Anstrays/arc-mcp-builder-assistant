"""
Arc Builder MCP Server (dependency-free)
-----------------------------------------
Self-contained JSON-RPC over stdio — no external MCP library needed.

14 tools:
  1. search_arc_docs       – search Arc documentation
  2. get_arc_page          – get full doc page
  3. list_arc_tools        – list Arc MCP tools
  4. fetch_llms_txt        – fetch llms.txt index
  5. wallet_status         – get wallet details
  6. wallet_balance        – get wallet balances
  7. wallet_list           – list all wallets
  8. wallet_send           – send tokens
  9. get_transaction       – check transaction status
  10. create_wallet_set    – create a wallet set
  11. arc_docs_overview    – get the full Arc docs map from local repo
  12. quickstart_prompt    – get a tailored prompt for a task
  13. template_info        – get Circle contract template info
  14. estimate_fee         – estimate transaction fee on Arc
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from arc_builder_kit import ArcDocsClient, CircleWalletClient, __version__

# ── constants ───────────────────────────────────────────────────

CONTRACT_TEMPLATES = {
    "erc20": {
        "id": "a1b74add-23e0-4712-88d1-6b3009e85a86",
        "name": "ERC-20",
        "description": "Fungible tokens — programmable money, demo credits, settlement tokens.",
    },
    "erc721": {
        "id": "76b83278-50e2-4006-8b63-5b1a2a814533",
        "name": "ERC-721",
        "description": "Unique assets — identity, certificates, agent receipts.",
    },
    "erc1155": {
        "id": "aea21da6-0aa2-4971-9a1a-5098842b1248",
        "name": "ERC-1155",
        "description": "Multi-asset instruments — tiers, batch products.",
    },
    "airdrop": {
        "id": "13e322f2-18dc-4f57-8eed-4bddfc50f85e",
        "name": "Airdrop",
        "description": "Mass distribution — payouts, treasury distributions.",
    },
}

ARC_TESTNET_INFO = {
    "network": "Arc Testnet",
    "rpc_url": "https://rpc.testnet.arc.network",
    "chain_id": 5042002,
    "currency": "USDC",
    "explorer": "https://testnet.arcscan.app",
    "gas_estimate": {"base_fee_gwei": 20, "notes": "USDC as native gas, 18 decimals for gas accounting"},
}

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "arc-builder-kit"
SERVER_VERSION = __version__


# ── helpers ─────────────────────────────────────────────────────


def _text(content: str) -> list[dict]:
    return [{"type": "text", "text": content}]


def _rpc_error(code: int, message: str, req_id: int | str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _rpc_result(data: Any, req_id: int | str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": data}


# ── tool implementations ────────────────────────────────────────


async def _search_arc_docs(query: str, limit: int = 5) -> str:
    client = ArcDocsClient()
    try:
        results = await client.search(query, limit=limit)
        if not results:
            return "No results found."
        parts = [f"--- Result {i+1} ---\n{r.content[:1500]}" for i, r in enumerate(results)]
        return "\n\n".join(parts)
    finally:
        await client.close()


async def _get_arc_page(path: str) -> str:
    client = ArcDocsClient()
    try:
        result = await client.get_page(path)
        if not result:
            return f"No content found at path: {path}"
        return result.content
    finally:
        await client.close()


async def _list_arc_tools() -> str:
    client = ArcDocsClient()
    try:
        tools = await client.list_tools()
        return json.dumps(tools, indent=2)
    finally:
        await client.close()


async def _fetch_llms_txt() -> str:
    client = ArcDocsClient()
    try:
        return await client.fetch_llms_txt()
    finally:
        await client.close()


async def _wallet_status(wallet_id: str) -> str:
    client = CircleWalletClient()
    try:
        w = await client.get_wallet(wallet_id)
        return json.dumps(
            {
                "id": w.id,
                "address": w.address,
                "blockchain": w.blockchain,
                "account_type": w.account_type,
                "custody_type": w.custody_type,
                "state": w.state,
            },
            indent=2,
        )
    finally:
        await client.close()


async def _wallet_balance(wallet_id: str) -> str:
    client = CircleWalletClient()
    try:
        balances = await client.get_balance(wallet_id)
        return json.dumps(
            [{"currency": b.currency, "amount": b.amount, "blockchain": b.blockchain} for b in balances],
            indent=2,
        )
    finally:
        await client.close()


async def _wallet_list() -> str:
    client = CircleWalletClient()
    try:
        wallets = await client.list_wallets()
        return json.dumps(
            [
                {
                    "id": w.id,
                    "address": w.address,
                    "blockchain": w.blockchain,
                    "account_type": w.account_type,
                    "state": w.state,
                }
                for w in wallets
            ],
            indent=2,
        )
    finally:
        await client.close()


async def _wallet_send(wallet_id: str, to: str, amount: str, currency: str = "USDC", memo: str = "") -> str:
    client = CircleWalletClient()
    try:
        tx = await client.create_transaction(
            wallet_id=wallet_id,
            destination=to,
            amount=amount,
            currency=currency,
            memo=memo,
        )
        return json.dumps(
            {
                "id": tx.id,
                "state": tx.state,
                "amount": tx.amount,
                "currency": tx.currency,
                "tx_hash": tx.tx_hash,
            },
            indent=2,
        )
    finally:
        await client.close()


async def _get_transaction(tx_id: str) -> str:
    client = CircleWalletClient()
    try:
        tx = await client.get_transaction(tx_id)
        return json.dumps(
            {
                "id": tx.id,
                "state": tx.state,
                "blockchain": tx.blockchain,
                "tx_hash": tx.tx_hash,
                "amount": tx.amount,
                "currency": tx.currency,
            },
            indent=2,
        )
    finally:
        await client.close()


async def _create_wallet_set(name: str) -> str:
    client = CircleWalletClient()
    try:
        result = await client.create_wallet_set(name=name)
        return json.dumps(result, indent=2)
    finally:
        await client.close()


async def _arc_docs_overview(section: str = "all") -> str:
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "arc-docs-map.md"
    if not doc_path.exists():
        return "Local docs map not found. Run `git pull` to fetch the latest docs."
    text = doc_path.read_text()
    if section != "all":
        lines = text.splitlines()
        filtered: list[str] = []
        in_section = False
        for line in lines:
            if line.startswith("## ") and section.lower() in line.lower():
                in_section = True
                filtered.append(line)
            elif line.startswith("## ") and in_section:
                break
            elif in_section:
                filtered.append(line)
        if filtered:
            return "\n".join(filtered)
        return f"Section '{section}' not found. Available sections are marked with ## in arc-docs-map.md."
    return text


async def _quickstart_prompt(task: str) -> str:
    prompts: dict[str, str] = {
        "payment-intent": (
            "Design a minimal payment-intent demo on Arc Testnet:\n"
            "1. AI agent creates a USDC payment request (recipient, amount, memo, expiry)\n"
            "2. Human reviews and approves manually\n"
            "3. App submits transaction and displays receipt\n"
            "Use Circle Dev-Controlled SCA wallets. No autonomous spending."
        ),
        "deploy-contract": (
            "Create a checklist for deploying a pre-audited contract template on Arc Testnet with Circle Contracts.\n"
            "Include: prerequisites, env vars, wallet creation, ERC-20 deployment, status verification."
        ),
        "agent-identity": (
            "Summarize Arc's ERC-8004 agent identity flow:\n"
            "1. Register an AI agent onchain\n"
            "2. Record reputation events\n"
            "3. Connect identity to payment requests\n"
            "Use Arc Testnet only."
        ),
        "job-escrow": (
            "Explain the ERC-8183 job escrow flow on Arc:\n"
            "1. Create a job\n"
            "2. Fund escrow with USDC\n"
            "3. Submit deliverable hash\n"
            "4. Complete job as evaluator\n"
            "5. Settle funds"
        ),
    }
    task_lower = task.lower()
    for key, prompt in prompts.items():
        if key in task_lower:
            return prompt
    return (
        f"Task: {task}\n\n"
        "Use Arc MCP/docs context to design a safe implementation plan for Arc Testnet. "
        "No mainnet funds, no private keys in code, no autonomous spending without human approval."
    )


async def _template_info(name: str = "") -> str:
    if name:
        t = CONTRACT_TEMPLATES.get(name.lower())
        if t:
            return json.dumps(t, indent=2)
        available = ", ".join(CONTRACT_TEMPLATES.keys())
        return f"Unknown template '{name}'. Available: {available}"
    return json.dumps(CONTRACT_TEMPLATES, indent=2)


async def _estimate_fee(chain: str = "ARC-TESTNET") -> str:
    info = dict(ARC_TESTNET_INFO)
    info["note"] = "Fees are paid in USDC at ~20 Gwei base fee. Actual fee depends on gas used."
    return json.dumps(info, indent=2)


# ── tool registry ───────────────────────────────────────────────

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "search_arc_docs": {
        "fn": _search_arc_docs,
        "description": "Search Arc documentation for relevant snippets",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "number", "description": "Max results (1-10)", "default": 5},
            },
            "required": ["query"],
        },
    },
    "get_arc_page": {
        "fn": _get_arc_page,
        "description": "Retrieve full content of a specific Arc documentation page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Page path e.g. '/arc/tutorials/deploy-contracts'"},
            },
            "required": ["path"],
        },
    },
    "list_arc_tools": {
        "fn": _list_arc_tools,
        "description": "List available Arc MCP tools",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "fetch_llms_txt": {
        "fn": _fetch_llms_txt,
        "description": "Fetch Arc's machine-readable documentation index (llms.txt)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "wallet_status": {
        "fn": _wallet_status,
        "description": "Get Circle wallet details by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wallet_id": {"type": "string", "description": "Circle wallet ID"},
            },
            "required": ["wallet_id"],
        },
    },
    "wallet_balance": {
        "fn": _wallet_balance,
        "description": "Get token balances for a Circle wallet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wallet_id": {"type": "string", "description": "Circle wallet ID"},
            },
            "required": ["wallet_id"],
        },
    },
    "wallet_list": {
        "fn": _wallet_list,
        "description": "List all Circle wallets",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "wallet_send": {
        "fn": _wallet_send,
        "description": "Send tokens from a Circle wallet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wallet_id": {"type": "string", "description": "Source wallet ID"},
                "to": {"type": "string", "description": "Destination address"},
                "amount": {"type": "string", "description": "Amount to send"},
                "currency": {"type": "string", "description": "Token (default: USDC)"},
                "memo": {"type": "string", "description": "Optional transaction memo"},
            },
            "required": ["wallet_id", "to", "amount"],
        },
    },
    "get_transaction": {
        "fn": _get_transaction,
        "description": "Check Circle transaction status by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string", "description": "Transaction ID"},
            },
            "required": ["tx_id"],
        },
    },
    "create_wallet_set": {
        "fn": _create_wallet_set,
        "description": "Create a new Circle wallet set",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Wallet set name"},
            },
            "required": [],
        },
    },
    "arc_docs_overview": {
        "fn": _arc_docs_overview,
        "description": "Get Arc docs overview from the local knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "description": "Section to filter (e.g. 'ai agent', 'deploy', or 'all')"},
            },
            "required": [],
        },
    },
    "quickstart_prompt": {
        "fn": _quickstart_prompt,
        "description": "Get a tailored AI prompt for common Arc builder tasks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task type: payment-intent, deploy-contract, agent-identity, job-escrow"},
            },
            "required": ["task"],
        },
    },
    "template_info": {
        "fn": _template_info,
        "description": "Get Circle contract template IDs and descriptions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Template name (erc20, erc721, erc1155, airdrop) or empty for all"},
            },
            "required": [],
        },
    },
    "estimate_fee": {
        "fn": _estimate_fee,
        "description": "Get estimated gas/fee info for Arc Testnet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chain": {"type": "string", "description": "Chain name (default: ARC-TESTNET)"},
            },
            "required": [],
        },
    },
}


# ── JSON-RPC handler ────────────────────────────────────────────


async def _handle_initialize(req: dict) -> dict:
    req_id = req.get("id", 0)
    return _rpc_result(
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {},
                "resources": {},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
        req_id,
    )


async def _handle_list_tools(req: dict) -> dict:
    req_id = req.get("id", 0)
    tools = []
    for name, meta in TOOL_REGISTRY.items():
        tools.append(
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": meta["inputSchema"],
            }
        )
    return _rpc_result({"tools": tools}, req_id)


async def _handle_call_tool(req: dict) -> dict:
    req_id = req.get("id", 0)
    params = req.get("params", {})
    name = params.get("name", "")
    args = params.get("arguments", {})

    if name not in TOOL_REGISTRY:
        return _rpc_error(-32601, f"Unknown tool: {name}", req_id)

    try:
        result = await TOOL_REGISTRY[name]["fn"](**args)
        return _rpc_result({"content": _text(result)}, req_id)
    except ValueError as e:
        return _rpc_error(-32000, str(e), req_id)
    except Exception as e:
        return _rpc_error(-32603, f"Internal error: {e}", req_id)


async def _handle_ping(req: dict) -> dict:
    return _rpc_result({"status": "ok"}, req.get("id", 0))


HANDLERS: dict[str, Callable] = {
    "initialize": _handle_initialize,
    "tools/list": _handle_list_tools,
    "tools/call": _handle_call_tool,
    "ping": _handle_ping,
}


# ── stdio server loop ───────────────────────────────────────────


async def serve_stdio() -> None:
    """Read JSON-RPC requests from stdin, write responses to stdout."""
    import asyncio

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    # signal readiness
    sys.stderr.write(f"[arc-builder-kit] MCP server v{__version__} ready\n")
    sys.stderr.flush()

    while True:
        try:
            line = await reader.readline()
        except (EOFError, ConnectionError):
            break
        if not line:
            break  # stdin closed

        raw = line.strip()
        if not raw:
            continue

        try:
            req = json.loads(raw)
        except json.JSONDecodeError as e:
            resp = _rpc_error(-32700, f"Parse error: {e}", 0)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        method = req.get("method", "")
        handler = HANDLERS.get(method)
        if handler is None:
            resp = _rpc_error(-32601, f"Method not found: {method}", req.get("id", 0))
        else:
            try:
                resp = await handler(req)
            except Exception as e:
                resp = _rpc_error(-32603, f"Handler error: {e}", req.get("id", 0))

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


def serve() -> None:
    """Synchronous entry point."""
    import asyncio

    asyncio.run(serve_stdio())
