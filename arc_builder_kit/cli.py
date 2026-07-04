"""
arc-builder CLI
---------------
Typer-based CLI for wallet management, doc search, and utility commands.

Usage:
    arc-builder wallet status
    arc-builder wallet balance <wallet_id>
    arc-builder wallet send <wallet_id> <to> <amount>
    arc-builder docs search <query>
    arc-builder docs list
"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from arc_builder_kit import ArcDocsClient, CircleWalletClient, __version__

app = typer.Typer(
    name="arc-builder",
    help="Arc Builder Kit — tools for Arc MCP, Circle wallets, and agentic commerce.",
    no_args_is_help=True,
)
wallet_app = typer.Typer(help="Circle wallet operations.")
docs_app = typer.Typer(help="Arc documentation lookups.")
app.add_typer(wallet_app, name="wallet")
app.add_typer(docs_app, name="docs")

console = Console()


# ── shared runner ───────────────────────────────────────────────


def _run_async(coro):
    return asyncio.run(coro)


# ── version ─────────────────────────────────────────────────────


@app.callback()
def version_callback(*, version: bool = typer.Option(False, "--version", "-v", help="Show version")) -> None:
    if version:
        console.print(f"arc-builder-kit v{__version__}")
        raise typer.Exit()


# ════════════════════════════════════════════════════════════════
# Wallet commands
# ════════════════════════════════════════════════════════════════


def _get_wallet_client() -> CircleWalletClient:
    try:
        return CircleWalletClient()
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@wallet_app.command("list")
def wallet_list():
    """List all Circle wallets."""
    client = _get_wallet_client()
    wallets = _run_async(client.list_wallets())
    if not wallets:
        console.print("No wallets found.")
        return
    table = Table(title="Wallets")
    table.add_column("ID", style="cyan")
    table.add_column("Address", style="green")
    table.add_column("Blockchain")
    table.add_column("Type")
    for w in wallets:
        table.add_row(w.id, w.address[:20] + "...", w.blockchain, w.account_type)
    console.print(table)


@wallet_app.command("status")
def wallet_status(wallet_id: str = typer.Argument(..., help="Wallet ID")):
    """Show wallet details."""
    client = _get_wallet_client()
    w = _run_async(client.get_wallet(wallet_id))
    table = Table(title=f"Wallet {wallet_id}")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("ID", w.id)
    table.add_row("Address", w.address)
    table.add_row("Blockchain", w.blockchain)
    table.add_row("Account Type", w.account_type)
    table.add_row("Custody Type", w.custody_type)
    table.add_row("State", w.state)
    console.print(table)


@wallet_app.command("balance")
def wallet_balance(wallet_id: str = typer.Argument(..., help="Wallet ID")):
    """Show wallet token balances."""
    client = _get_wallet_client()
    balances = _run_async(client.get_balance(wallet_id))
    if not balances:
        console.print("No balances found.")
        return
    table = Table(title=f"Balances — {wallet_id}")
    table.add_column("Currency")
    table.add_column("Amount", justify="right")
    table.add_column("Blockchain")
    for b in balances:
        table.add_row(b.currency, b.amount, b.blockchain)
    console.print(table)


@wallet_app.command("send")
def wallet_send(
    wallet_id: str = typer.Argument(..., help="Source wallet ID"),
    to: str = typer.Argument(..., help="Destination address"),
    amount: str = typer.Argument(..., help="Amount to send"),
    currency: str = typer.Option("USDC", "--currency", "-c", help="Token currency"),
    memo: str = typer.Option("", "--memo", "-m", help="Transaction memo"),
):
    """Send tokens from a wallet."""
    client = _get_wallet_client()
    tx = _run_async(
        client.create_transaction(
            wallet_id=wallet_id,
            destination=to,
            amount=amount,
            currency=currency,
            memo=memo,
        )
    )
    console.print(f"[green]Transaction created:[/green] {tx.id}")
    console.print(f"  State:    {tx.state}")
    console.print(f"  Amount:   {tx.amount} {tx.currency}")
    if tx.tx_hash:
        console.print(f"  Tx Hash:  {tx.tx_hash}")


# ════════════════════════════════════════════════════════════════
# Docs commands
# ════════════════════════════════════════════════════════════════


@docs_app.command("search")
def docs_search(query: str = typer.Argument(..., help="Search query")):
    """Search Arc documentation."""
    client = ArcDocsClient()
    results = _run_async(client.search(query))
    if not results:
        console.print("No results found.")
        return
    table = Table(title=f"Arc Docs — {query}")
    table.add_column("#")
    table.add_column("Content (truncated)")
    for i, r in enumerate(results, 1):
        content = r.content[:200].replace("\n", " ") + ("..." if len(r.content) > 200 else "")
        table.add_row(str(i), content)
    console.print(table)


@docs_app.command("list-tools")
def docs_list_tools():
    """List available Arc MCP tools."""
    client = ArcDocsClient()
    tools = _run_async(client.list_tools())
    if not tools:
        console.print("No tools found.")
        return
    table = Table(title="Arc MCP Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    for t in tools:
        table.add_row(t.get("name", ""), t.get("description", ""))
    console.print(table)


if __name__ == "__main__":
    app()
