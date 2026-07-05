#!/usr/bin/env python3
"""Arc Builder CLI: unified command-line tooling for the Arc MCP Builder Assistant.

This is a dependency-free orchestrator over existing builder-kit scripts and
resources. It stays local-only by default and never connects a wallet, signs, or
broadcasts transactions. Network calls happen only through explicit opt-in flags
passed to underlying scripts.

Subcommands:
  doctor          Run Arc Builder Doctor and print a structured verdict.
  validate        Run repository validation.
  templates       List available project starter templates.
  scaffold        Copy a starter template into a new project directory.
  facts           Print the reviewed Arc Testnet facts object.
  manifest        Print the local x402 paid-agent manifest.
  release-packet  Generate a local maintainer release packet.
  wallet          Build Circle Wallet SDK guard plans for Arc Testnet.
  mcp             Start the local Arc Builder MCP server (stdio).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from arc_builder_kit import __version__, circle_wallet_sdk
from arc_builder_kit._paths import (
    CONFIG_DIR,
    DEFAULT_OUTPUT_ROOT,
    EXAMPLES_DIR,
    REPO_ROOT,
    TEMPLATES_DIR,
)
from arc_builder_kit.doctor import main as doctor_main
from arc_builder_kit.mcp_server import main as mcp_main
from arc_builder_kit.release_packet import main as release_packet_main
from arc_builder_kit.validate_repo import main as validate_main

X402_SERVER = EXAMPLES_DIR / "x402-local-challenge-server" / "server.py"


class CliError(Exception):
    """User-facing error that should exit with a clean message."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def _run_script(
    script: Path,
    args: Sequence[str] = (),
    *,
    capture: bool = True,
    timeout: float | None = 300,
) -> subprocess.CompletedProcess[str]:
    """Run a Python script as an argument list.

    Kept for the x402 manifest example, which is a standalone server file that
    remains easier to invoke as a subprocess than to import.
    """
    if not script.exists():
        raise CliError(f"script not found: {script}")
    cmd = [sys.executable, str(script), *args]
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=timeout,
        check=False,
    )


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise CliError(f"file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise CliError(f"invalid JSON in {path}: {exc}") from exc


def _list_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(
        d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir() and (d / "README.md").exists()
    )


def cmd_doctor(args: argparse.Namespace) -> int:
    flags = ["--json"]
    if args.full:
        flags.append("--full")
    if args.include_arc_rpc:
        flags.append("--include-arc-rpc")
    if args.include_public_site:
        flags.append("--include-public-site")
    if args.include_circle_wallet:
        flags.append("--include-circle-wallet")
    return doctor_main(flags)


def cmd_validate(args: argparse.Namespace) -> int:
    validate_main()
    return 0


def cmd_templates(args: argparse.Namespace) -> int:
    names = _list_templates()
    output: dict[str, Any] = {
        "templates": names,
        "templates_dir": str(TEMPLATES_DIR.relative_to(REPO_ROOT) if TEMPLATES_DIR.is_relative_to(REPO_ROOT) else TEMPLATES_DIR),
        "count": len(names),
    }
    for name in names:
        readme = TEMPLATES_DIR / name / "README.md"
        if readme.exists():
            first = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            output.setdefault("titles", {})[name] = first
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("Available Arc builder starter templates:")
        if not names:
            print("  (none)")
        for name in names:
            title = output.get("titles", {}).get(name, name)
            print(f"  - {name}: {title}")
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    available = _list_templates()
    if args.template not in available:
        raise CliError(
            f"unknown template: {args.template}\n"
            f"available: {', '.join(available) if available else '(none)'}"
        )
    source = TEMPLATES_DIR / args.template
    dest = Path(args.output).expanduser().resolve()
    if dest.exists() and not args.force:
        raise CliError(f"output already exists: {dest}; use --force to overwrite")
    if dest.exists() and args.force:
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    print(f"scaffolded '{args.template}' -> {dest}")
    print(f"next: cd {dest.relative_to(Path.cwd()) if dest.is_relative_to(Path.cwd()) else dest}")
    return 0


def cmd_facts(args: argparse.Namespace) -> int:
    facts = _load_json(CONFIG_DIR / "arc_testnet.facts.json")
    if args.json:
        print(json.dumps(facts, indent=2))
    else:
        print(json.dumps(facts, indent=2))
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    result = _run_script(X402_SERVER, ["--print-manifest"], timeout=60)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode if result.returncode else 0


def cmd_mcp(args: argparse.Namespace) -> int:
    return mcp_main()


def cmd_release_packet(args: argparse.Namespace) -> int:
    out = (
        Path(args.output).expanduser().resolve()
        if args.output
        else DEFAULT_OUTPUT_ROOT / ".arc-release-packet"
    )
    argv = ["--out", str(out)]
    if args.force:
        argv.append("--force")
    return release_packet_main(argv)


def cmd_x402(args: argparse.Namespace) -> int:
    from arc_builder_kit.x402_client import paid_request
    import json as _json

    try:
        if args.x402_command == "challenge":
            result = paid_request(args.url)
        elif args.x402_command == "verify":
            result = paid_request(args.url, payment_proof=args.txhash)
        else:
            return 1
        payload = result.to_dict()
        print(_json.dumps(payload, indent=2, sort_keys=True))
        if args.x402_command == "verify" and result.receipt_verification is not None:
            return 0 if result.receipt_verification.verified else 1
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _print_json_or_human(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_wallet(args: argparse.Namespace) -> int:
    if args.wallet_command == "sdk-plan":
        payload = {
            "manifest": circle_wallet_sdk.build_sdk_guard_manifest(),
            "plan": circle_wallet_sdk.build_wallet_creation_plan(
                account_type=args.account_type,
                count=args.count,
                wallet_set_name=args.wallet_set_name,
            ),
        }
        _print_json_or_human(payload, as_json=args.json)
        return 0
    if args.wallet_command == "env-check":
        payload = circle_wallet_sdk.summarize_environment(os.environ)
        _print_json_or_human(payload, as_json=args.json)
        return 0
    if args.wallet_command == "sdk-snippet":
        print(
            circle_wallet_sdk.generate_python_sdk_snippet(
                account_type=args.account_type,
                count=args.count,
                wallet_set_name=args.wallet_set_name,
            )
        )
        return 0
    if args.wallet_command == "status":
        payload = circle_wallet_sdk.build_wallet_status_summary()
        _print_json_or_human(payload, as_json=args.json)
        return 0
    if args.wallet_command == "balance":
        try:
            payload = circle_wallet_sdk.get_usdc_balance(args.address)
        except Exception as exc:
            print(f"error: balance check failed: {exc}", file=sys.stderr)
            return 1
        if not payload.get("ok"):
            print(f"error: {payload.get('error', 'unknown')}", file=sys.stderr)
            return 1
        print(f"Address: {payload['address']}")
        print(f"Balance: {payload['balanceUSDC']} USDC")
        print(f"Network: {payload['network']} (chain {payload['chainId']})")
        if args.json:
            print()
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.wallet_command == "send":
        payload = circle_wallet_sdk.prepare_send_intent(
            to_address=args.to_address,
            amount=args.amount,
            network=getattr(args, "network", "ARC-TESTNET"),
        )
        if not payload.get("ok"):
            print(f"error: {payload.get('error', 'unknown')}", file=sys.stderr)
            return 1
        _print_json_or_human(payload, as_json=args.json)
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arc-builder",
        description="Unified CLI for the Arc MCP Builder Assistant kit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Run Arc Builder Doctor.")
    doctor.add_argument("--full", action="store_true", help="Run full local verification.")
    doctor.add_argument(
        "--include-arc-rpc",
        action="store_true",
        help="Opt-in read-only Arc Testnet RPC chain-id check.",
    )
    doctor.add_argument(
        "--include-public-site",
        action="store_true",
        help="Opt-in public GitHub Pages health check.",
    )
    doctor.add_argument(
        "--include-circle-wallet",
        action="store_true",
        help="Opt-in live Circle CLI checks (wallet, balance, session).",
    )

    sub.add_parser("validate", help="Run repository validation.")

    templates = sub.add_parser("templates", help="List available starter templates.")
    templates.add_argument("--json", action="store_true", help="Output machine-readable JSON.")

    scaffold = sub.add_parser("scaffold", help="Copy a starter template to a new project.")
    scaffold.add_argument("template", help="Template name (see 'templates').")
    scaffold.add_argument("output", help="Destination directory.")
    scaffold.add_argument("--force", action="store_true", help="Overwrite existing directory.")

    facts = sub.add_parser("facts", help="Print reviewed Arc Testnet facts.")
    facts.add_argument("--json", action="store_true", help="Output machine-readable JSON.")

    sub.add_parser("manifest", help="Print the local x402 paid-agent manifest.")
    sub.add_parser("mcp", help="Start the local Arc Builder MCP server (stdio).")

    release_packet = sub.add_parser(
        "release-packet", help="Generate a local maintainer release packet."
    )
    release_packet.add_argument(
        "--output",
        default="",
        help="Output directory (default: .arc-release-packet/).",
    )
    release_packet.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing packet directory.",
    )

    x402 = sub.add_parser(
        "x402",
        help="Inspect x402 challenges and verify Arc Testnet payment proofs (read-only).",
    )
    x402_sub = x402.add_subparsers(dest="x402_command", required=True)
    x402_challenge = x402_sub.add_parser(
        "challenge",
        help="Fetch and print an x402 HTTP 402 challenge for human review.",
    )
    x402_challenge.add_argument("url", help="x402-enabled endpoint URL.")
    x402_verify = x402_sub.add_parser(
        "verify",
        help="Fetch the challenge and verify a transaction hash against Arc Testnet receipt evidence.",
    )
    x402_verify.add_argument("url", help="x402-enabled endpoint URL.")
    x402_verify.add_argument("txhash", help="Arc Testnet transaction hash used as the payment proof.")

    wallet = sub.add_parser(
        "wallet",
        help="Build Circle Wallet SDK guard plans for Arc Testnet (no live SDK execution).",
    )
    wallet_sub = wallet.add_subparsers(dest="wallet_command", required=True)
    sdk_plan = wallet_sub.add_parser("sdk-plan", help="Print a Circle Wallet SDK integration plan.")
    sdk_plan.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    sdk_plan.add_argument("--account-type", choices=circle_wallet_sdk.ACCOUNT_TYPES, default="SCA")
    sdk_plan.add_argument("--count", type=int, default=1)
    sdk_plan.add_argument("--wallet-set-name", default=circle_wallet_sdk.DEFAULT_WALLET_SET_NAME)
    env_check = wallet_sub.add_parser("env-check", help="Check Circle SDK env var presence with redacted values.")
    env_check.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    snippet = wallet_sub.add_parser("sdk-snippet", help="Print a secret-safe manual Python SDK snippet.")
    snippet.add_argument("--account-type", choices=circle_wallet_sdk.ACCOUNT_TYPES, default="SCA")
    snippet.add_argument("--count", type=int, default=1)
    snippet.add_argument("--wallet-set-name", default=circle_wallet_sdk.DEFAULT_WALLET_SET_NAME)

    wallet_status = wallet_sub.add_parser("status", help="Show wallet guard status summary.")
    wallet_status.add_argument("--json", action="store_true", help="Output machine-readable JSON.")

    wallet_balance = wallet_sub.add_parser("balance", help="Check USDC balance on Arc Testnet (read-only RPC).")
    wallet_balance.add_argument("address", help="EVM address to check USDC balance for.")
    wallet_balance.add_argument("--json", action="store_true", help="Show full JSON response.")

    wallet_send = wallet_sub.add_parser(
        "send",
        help="Prepare a guarded USDC send intent for human review (no broadcast).",
    )
    wallet_send.add_argument("to_address", help="Recipient EVM address.")
    wallet_send.add_argument("amount", help="USDC amount (e.g. 1.50).")
    wallet_send.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    wallet_send.add_argument("--network", default="ARC-TESTNET", help="Network (default: ARC-TESTNET).")

    return parser


COMMANDS = {
    "doctor": cmd_doctor,
    "validate": cmd_validate,
    "templates": cmd_templates,
    "scaffold": cmd_scaffold,
    "facts": cmd_facts,
    "manifest": cmd_manifest,
    "mcp": cmd_mcp,
    "release-packet": cmd_release_packet,
    "x402": cmd_x402,
    "wallet": cmd_wallet,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.error(f"unknown command: {args.command}")
    try:
        return handler(args)
    except CliError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return exc.exit_code
    except subprocess.TimeoutExpired as exc:
        print(f"error: timed out running {exc.cmd}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
