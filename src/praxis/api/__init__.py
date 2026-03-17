# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis API layer — REST, MCP, and WebSocket interfaces.

Built on Kailash Nexus for multi-channel deployment (API + CLI + MCP).

Usage:
    from praxis.api.app import create_app

    app = create_app()
    app.start()
"""

from praxis.api.app import create_app

__all__ = ["create_app"]
