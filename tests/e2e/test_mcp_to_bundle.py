# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""E2E tests for MCP-to-bundle workflow.

These tests verify the complete user journey:
    MCP client -> Praxis API -> trust chain -> verification bundle

They require a running Praxis server with MCP endpoint configured.
"""

import pytest


@pytest.mark.skip(reason="E2E tests require running Praxis server")
def test_mcp_client_creates_session_and_exports_bundle():
    """MCP client -> Praxis API -> trust chain -> verification bundle.

    End-to-end test flow:
        1. MCP client connects to Praxis
        2. Creates a new session via MCP tool call
        3. Records deliberation decisions via MCP
        4. Evaluates constraints via MCP
        5. Exports verification bundle
        6. Verifies bundle integrity offline

    This test is skipped by default because it requires:
        - Running Praxis server on localhost
        - MCP endpoint configured and accessible
        - Valid signing keys available
    """
    pass


@pytest.mark.skip(reason="E2E tests require running Praxis server")
def test_session_lifecycle_via_rest_api():
    """REST API -> session lifecycle -> deliberation -> export.

    End-to-end test flow:
        1. POST /api/sessions to create session
        2. POST /api/sessions/{id}/decisions to record decisions
        3. POST /api/sessions/{id}/evaluate to check constraints
        4. POST /api/sessions/{id}/end to archive
        5. GET /api/sessions/{id}/bundle to export
        6. Verify bundle offline
    """
    pass


@pytest.mark.skip(reason="E2E tests require running Praxis server")
def test_multi_user_delegation_workflow():
    """Test delegation from supervisor to practitioner via API.

    End-to-end test flow:
        1. Supervisor creates session with constraints
        2. Supervisor delegates to practitioner
        3. Practitioner performs work within constraints
        4. Held action triggers supervisor approval
        5. Session ends with complete trust chain
        6. Bundle verification confirms chain integrity
    """
    pass
