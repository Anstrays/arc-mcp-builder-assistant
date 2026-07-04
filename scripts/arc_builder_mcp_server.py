#!/usr/bin/env python3
"""Arc Builder MCP server (stdio) — standalone entry point.

Thin wrapper that delegates to the installable ``arc_builder_kit.mcp_server``
module. Use this file when running directly from the repo checkout without
installing the package.

Supported JSON-RPC methods:
- initialize
- tools/list
- tools/call

For the full tool list and v2 features (structured errors, progress streaming,
wallet tools) see ``arc_builder_kit/mcp_server.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "0.3.0"

# Ensure the repo root is on sys.path so the package is importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from arc_builder_kit.mcp_server import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
