#!/usr/bin/env python3
"""
Standalone Arc Builder MCP Server
--------------------------------
Thin entry point that runs the MCP server over stdio.

Usage:
    python scripts/arc_builder_mcp_server.py

Or configure your MCP client to run this script.
"""

from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])

from arc_builder_kit.mcp_server import serve

if __name__ == "__main__":
    serve()
