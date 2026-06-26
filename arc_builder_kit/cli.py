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
  mcp             Start the local Arc Builder MCP server (stdio).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from arc_builder_kit._paths import CONFIG_DIR, EXAMPLES_DIR, REPO_ROOT, TEMPLATES_DIR
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
        else REPO_ROOT / ".arc-release-packet"
    )
    if args.force and out.exists():
        shutil.rmtree(out)
    argv = ["--out", str(out)]
    return release_packet_main(argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arc-builder",
        description="Unified CLI for the Arc MCP Builder Assistant kit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
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
