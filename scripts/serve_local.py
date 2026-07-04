#!/usr/bin/env python3
"""Safer local development server for the Arc MCP Builder Assistant static site.

This is a thin, dependency-free wrapper around http.server that adds the
security headers the static HTML already declares, while refusing to:
- bind anything other than 127.0.0.1
- serve files outside the repository root
- serve .env, .git, or other sensitive paths

Usage:
    python scripts/serve_local.py
    python scripts/serve_local.py --port 8080

The server prints the local URL on startup and logs every request.
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Same-origin, fail-closed headers that mirror the CSP declared in index.html.
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "connect-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

BLOCKED_SEGMENTS = {
    ".env",
    ".git",
    ".gitattributes",
    ".gitignore",
    ".github",
    ".hermes",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}

BLOCKED_SUFFIXES = (
    ".env",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
)


class SafeRequestHandler(SimpleHTTPRequestHandler):
    """Request handler bound to the repo root with added security headers."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:  # type: ignore[no-untyped-def]
        print(f"[serve_local] {self.address_string()} - {format % args}")

    def end_headers(self) -> None:
        for header, value in SECURITY_HEADERS.items():
            self.send_header(header, value)
        super().end_headers()

    def translate_path(self, path: str) -> str:
        translated = super().translate_path(path)
        try:
            resolved = Path(translated).resolve()
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            self.log_message("blocked traversal attempt: %s", path)
            return str(ROOT / "404.html")
        return translated

    def _is_blocked(self, path: Path) -> bool:
        parts = set(path.parts)
        if parts & BLOCKED_SEGMENTS:
            return True
        if any(part.startswith(".") and part in BLOCKED_SEGMENTS for part in path.parts):
            return True
        if path.suffix.lower().endswith(BLOCKED_SUFFIXES):
            return True
        return False

    def send_head(self) -> os.PathLike | None:  # type: ignore[override]
        path = Path(self.translate_path(self.path)).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            self.send_error(403, "Forbidden")
            return None
        if self._is_blocked(path):
            self.send_error(403, "Forbidden")
            return None
        # Serve index.html for directory requests.
        if path.is_dir():
            index = path / "index.html"
            if index.is_file():
                self.path = str(index.relative_to(ROOT.resolve()))
                return super().send_head()  # type: ignore[no-any-return]
            self.send_error(403, "Directory listing disabled")
            return None
        return super().send_head()  # type: ignore[no-any-return]

    def do_GET(self) -> None:  # type: ignore[override]
        # Reject any request that smells like path traversal before serving.
        if ".." in self.path:
            self.send_error(403, "Forbidden")
            return
        super().do_GET()


class LocalOnlyServer(ThreadingHTTPServer):
    """Refuse to bind anything other than loopback."""

    def server_bind(self) -> None:
        host, _ = self.server_address
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise SystemExit(
                f"Refusing to bind to {host}: this server is only allowed on loopback. "
                "Use --host 127.0.0.1"
            )
        super().server_bind()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the Arc MCP Builder Assistant static site locally."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1; only loopback allowed).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind (default: 8080).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"error: refusing to bind to {args.host}; only loopback is allowed", file=sys.stderr)
        return 1

    # Ensure common types are registered for static assets.
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("application/javascript", ".mjs")

    server = LocalOnlyServer((args.host, args.port), SafeRequestHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"[serve_local] serving {ROOT} at {url}")
    print(f"[serve_local] wallet gate: {url}/examples/arc-testnet-wallet-send-gate/?enableArcTestnetSend=reviewed-testnet-only")
    print("[serve_local] press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve_local] stopping")
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
