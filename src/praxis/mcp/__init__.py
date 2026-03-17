# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis MCP proxy — trust-mediated tool call interception.

The MCP proxy sits between an AI assistant and downstream MCP tool servers,
intercepting every tool call and enforcing constraints before forwarding.
This implements the "trust as medium" architecture: trust infrastructure
is the medium through which AI operates, not a camera watching from the side.

Usage:
    from praxis.mcp.proxy import PraxisProxy
    proxy = PraxisProxy(session_id="...", downstream_servers=[...])
    await proxy.start()
"""

from praxis.mcp.proxy import PraxisProxy

__all__ = ["PraxisProxy"]
