# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.mcp.proxy — MCP trust-mediated proxy.

Tests the constraint interception logic, tool dimension mapping,
audit anchor creation, and held action management. No actual MCP
connections or downstream servers are needed.
"""

import pytest


# ---------------------------------------------------------------------------
# Tool dimension classification
# ---------------------------------------------------------------------------


class TestClassifyToolDimension:
    """Test tool name -> constraint dimension mapping."""

    def test_file_tools_map_to_data_access(self):
        from praxis.mcp.proxy import classify_tool_dimension

        assert classify_tool_dimension("read_file") == "data_access"
        assert classify_tool_dimension("write_file") == "data_access"
        assert classify_tool_dimension("edit_file") == "data_access"
        assert classify_tool_dimension("list_directory") == "data_access"
        assert classify_tool_dimension("search_files") == "data_access"
        assert classify_tool_dimension("glob_pattern") == "data_access"

    def test_shell_tools_map_to_operational(self):
        from praxis.mcp.proxy import classify_tool_dimension

        assert classify_tool_dimension("bash_exec") == "operational"
        assert classify_tool_dimension("run_command") == "operational"
        assert classify_tool_dimension("shell_execute") == "operational"
        assert classify_tool_dimension("deploy_service") == "operational"
        assert classify_tool_dimension("install_package") == "operational"
        assert classify_tool_dimension("delete_resource") == "operational"

    def test_http_tools_map_to_communication(self):
        from praxis.mcp.proxy import classify_tool_dimension

        assert classify_tool_dimension("http_get") == "communication"
        assert classify_tool_dimension("fetch_url") == "communication"
        assert classify_tool_dimension("api_request") == "communication"
        assert classify_tool_dimension("send_email") == "communication"
        assert classify_tool_dimension("post_data") == "communication"

    def test_financial_tools_map_to_financial(self):
        from praxis.mcp.proxy import classify_tool_dimension

        assert classify_tool_dimension("check_token_usage") == "financial"
        assert classify_tool_dimension("billing_status") == "financial"
        assert classify_tool_dimension("cost_estimate") == "financial"

    def test_unknown_tools_default_to_operational(self):
        from praxis.mcp.proxy import classify_tool_dimension

        assert classify_tool_dimension("custom_tool") == "operational"
        assert classify_tool_dimension("foobar") == "operational"
        assert classify_tool_dimension("") == "operational"


# ---------------------------------------------------------------------------
# Resource extraction
# ---------------------------------------------------------------------------


class TestResourceExtraction:
    """Test resource identifier extraction from tool arguments."""

    def test_data_access_extracts_file_path(self):
        from praxis.mcp.proxy import _resource_for_call

        assert (
            _resource_for_call("data_access", "read_file", {"path": "/src/main.py"})
            == "/src/main.py"
        )
        assert (
            _resource_for_call("data_access", "read_file", {"file_path": "/tmp/data.json"})
            == "/tmp/data.json"
        )

    def test_communication_extracts_url(self):
        from praxis.mcp.proxy import _resource_for_call

        assert (
            _resource_for_call("communication", "fetch", {"url": "https://api.example.com"})
            == "https://api.example.com"
        )

    def test_no_resource_returns_none(self):
        from praxis.mcp.proxy import _resource_for_call

        assert _resource_for_call("data_access", "read_file", {}) is None
        assert _resource_for_call("operational", "bash", {"command": "ls"}) is None


# ---------------------------------------------------------------------------
# ProxyResult dataclass
# ---------------------------------------------------------------------------


class TestProxyResult:
    """Test ProxyResult construction."""

    def test_basic_construction(self):
        from praxis.core.constraint import ConstraintVerdict, GradientLevel
        from praxis.mcp.proxy import ProxyResult

        verdict = ConstraintVerdict(
            level=GradientLevel.AUTO_APPROVED,
            dimension="operational",
            utilization=0.0,
            reason="Allowed",
            action="execute",
        )
        result = ProxyResult(
            tool_name="server__tool",
            server_name="server",
            original_tool="tool",
            verdict=verdict,
        )
        assert result.tool_name == "server__tool"
        assert result.forwarded is False
        assert result.held_action_id is None
        assert result.error is None


# ---------------------------------------------------------------------------
# PraxisProxy constraint enforcement (M04-02)
# ---------------------------------------------------------------------------


class TestProxyConstraintEnforcement:
    """Test that the proxy correctly enforces constraints on tool calls."""

    def _make_proxy(self, constraints, downstream_tools=None):
        """Helper to create a proxy with a pre-configured enforcer."""
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
        from praxis.mcp.proxy import PraxisProxy

        enforcer = ConstraintEnforcer(constraints)
        held_manager = HeldActionManager(use_db=False)

        proxy = PraxisProxy(
            session_id="test-session-001",
            downstream_servers=[],
            constraint_enforcer=enforcer,
            held_action_manager=held_manager,
        )

        # Register some test tools in the catalog
        if downstream_tools is None:
            downstream_tools = [
                {"name": "read_file", "description": "Read a file", "inputSchema": {}},
                {"name": "write_file", "description": "Write a file", "inputSchema": {}},
                {"name": "bash", "description": "Run bash", "inputSchema": {}},
                {"name": "http_get", "description": "HTTP GET", "inputSchema": {}},
            ]
        proxy.register_tools("test_server", downstream_tools)
        return proxy

    @pytest.mark.asyncio
    async def test_blocked_actions_rejected_without_forwarding(self):
        """BLOCKED actions must return an error and NOT forward to downstream."""
        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read"],
                "blocked_actions": ["delete"],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {
                "allowed_paths": ["/src/"],
                "blocked_paths": ["/secrets/"],
            },
            "communication": {
                "allowed_channels": [],
                "blocked_channels": [],
            },
        }
        proxy = self._make_proxy(constraints)

        # Try to read a blocked path
        result = await proxy.handle_tool_call(
            "test_server__read_file",
            {"path": "/secrets/keys.pem"},
        )

        assert result.verdict.level.value == "blocked"
        assert result.forwarded is False
        assert result.error is not None
        assert "BLOCKED" in result.error

    @pytest.mark.asyncio
    async def test_blocked_action_type(self):
        """Explicitly blocked action types must be rejected."""
        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write"],
                "blocked_actions": ["delete"],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {
                "allowed_paths": ["/"],
                "blocked_paths": [],
            },
            "communication": {
                "allowed_channels": [],
                "blocked_channels": [],
            },
        }
        proxy = self._make_proxy(constraints)

        # A delete tool maps to "delete" action via operational dimension
        delete_tools = [
            {"name": "delete_file", "description": "Delete a file", "inputSchema": {}},
        ]
        proxy.register_tools("ops_server", delete_tools)

        result = await proxy.handle_tool_call(
            "ops_server__delete_file",
            {"path": "/src/old.py"},
        )

        assert result.verdict.level.value == "blocked"
        assert result.forwarded is False

    @pytest.mark.asyncio
    async def test_held_actions_return_held_action_id(self):
        """HELD actions must return a held_action_id and NOT forward."""
        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write", "execute"],
                "blocked_actions": [],
            },
            "temporal": {
                "max_duration_minutes": 100,
                "elapsed_minutes": 92,  # 92% utilization -> HELD
            },
            "data_access": {
                "allowed_paths": ["/"],
                "blocked_paths": [],
            },
            "communication": {
                "allowed_channels": [],
                "blocked_channels": [],
            },
        }
        proxy = self._make_proxy(constraints)

        result = await proxy.handle_tool_call(
            "test_server__read_file",
            {"path": "/src/main.py"},
        )

        assert result.verdict.level.value == "held"
        assert result.held_action_id is not None
        assert len(result.held_action_id) > 0
        assert result.forwarded is False
        assert "HELD" in result.error

    @pytest.mark.asyncio
    async def test_auto_approved_actions_pass_through(self):
        """AUTO_APPROVED actions must be forwarded (even if downstream not connected)."""
        constraints = {
            "financial": {"max_spend": 1000.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write", "execute"],
                "blocked_actions": [],
            },
            "temporal": {
                "max_duration_minutes": 120,
                "elapsed_minutes": 10,  # 8% utilization -> AUTO_APPROVED
            },
            "data_access": {
                "allowed_paths": ["/src/"],
                "blocked_paths": [],
            },
            "communication": {
                "allowed_channels": [],
                "blocked_channels": [],
            },
        }
        proxy = self._make_proxy(constraints)

        result = await proxy.handle_tool_call(
            "test_server__read_file",
            {"path": "/src/main.py"},
        )

        assert result.verdict.level.value == "auto_approved"
        assert result.forwarded is True
        # No downstream connected, so response is an error dict (expected)
        assert result.response is not None

    @pytest.mark.asyncio
    async def test_flagged_actions_forward_with_warning(self):
        """FLAGGED actions must be forwarded but the verdict level should be flagged."""
        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write", "execute"],
                "blocked_actions": [],
            },
            "temporal": {
                "max_duration_minutes": 100,
                "elapsed_minutes": 75,  # 75% utilization -> FLAGGED
            },
            "data_access": {
                "allowed_paths": ["/src/"],
                "blocked_paths": [],
            },
            "communication": {
                "allowed_channels": [],
                "blocked_channels": [],
            },
        }
        proxy = self._make_proxy(constraints)

        result = await proxy.handle_tool_call(
            "test_server__read_file",
            {"path": "/src/main.py"},
        )

        assert result.verdict.level.value == "flagged"
        assert result.forwarded is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_unknown_tool_blocked(self):
        """Unknown tool names (not in catalog, can't parse) should be blocked."""
        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {"allowed_actions": [], "blocked_actions": []},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/"], "blocked_paths": []},
            "communication": {"allowed_channels": [], "blocked_channels": []},
        }
        proxy = self._make_proxy(constraints)

        result = await proxy.handle_tool_call("nonexistent_tool", {})

        assert result.verdict.level.value == "blocked"
        assert result.forwarded is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# Audit anchor creation (M04-03)
# ---------------------------------------------------------------------------


class TestProxyAuditCapture:
    """Test that audit anchors are created for each tool call."""

    @pytest.mark.asyncio
    async def test_audit_anchor_created_on_auto_approved(self, key_manager):
        """An audit anchor should be created for every tool call."""
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
        from praxis.mcp.proxy import PraxisProxy
        from praxis.trust.audit import AuditChain

        constraints = {
            "financial": {"max_spend": 1000.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write", "execute"],
                "blocked_actions": [],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/"], "blocked_paths": []},
            "communication": {"allowed_channels": [], "blocked_channels": []},
        }

        audit_chain = AuditChain(
            session_id="test-audit-session",
            key_id="test-key",
            key_manager=key_manager,
        )

        proxy = PraxisProxy(
            session_id="test-audit-session",
            downstream_servers=[],
            constraint_enforcer=ConstraintEnforcer(constraints),
            held_action_manager=HeldActionManager(use_db=False),
            audit_chain=audit_chain,
            key_manager=key_manager,
            key_id="test-key",
        )

        proxy.register_tools(
            "fs",
            [
                {"name": "read_file", "description": "Read", "inputSchema": {}},
            ],
        )

        result = await proxy.handle_tool_call(
            "fs__read_file",
            {"path": "/src/main.py"},
        )

        # Verify an audit anchor was created
        assert result.audit_anchor_id is not None
        assert audit_chain.length == 1

        # The anchor should contain the tool call details
        anchors = audit_chain.anchors
        assert len(anchors) == 1
        assert anchors[0].action == "read"
        assert anchors[0].result == "auto_approved"
        assert anchors[0].payload.get("tool_name") == "fs__read_file"

    @pytest.mark.asyncio
    async def test_audit_anchor_created_on_blocked(self, key_manager):
        """Audit anchors should be created even for blocked calls."""
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
        from praxis.mcp.proxy import PraxisProxy
        from praxis.trust.audit import AuditChain

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read"],
                "blocked_actions": ["delete"],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": ["/secrets/"]},
            "communication": {"allowed_channels": [], "blocked_channels": []},
        }

        audit_chain = AuditChain(
            session_id="test-blocked-audit",
            key_id="test-key",
            key_manager=key_manager,
        )

        proxy = PraxisProxy(
            session_id="test-blocked-audit",
            downstream_servers=[],
            constraint_enforcer=ConstraintEnforcer(constraints),
            held_action_manager=HeldActionManager(use_db=False),
            audit_chain=audit_chain,
            key_manager=key_manager,
            key_id="test-key",
        )

        proxy.register_tools(
            "fs",
            [
                {"name": "read_file", "description": "Read", "inputSchema": {}},
            ],
        )

        result = await proxy.handle_tool_call(
            "fs__read_file",
            {"path": "/secrets/key.pem"},
        )

        assert result.verdict.level.value == "blocked"
        assert result.audit_anchor_id is not None
        assert audit_chain.length == 1
        assert audit_chain.anchors[0].result == "blocked"

    @pytest.mark.asyncio
    async def test_multiple_calls_chain_anchors(self, key_manager):
        """Multiple tool calls should produce a chain of anchors."""
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
        from praxis.mcp.proxy import PraxisProxy
        from praxis.trust.audit import AuditChain

        constraints = {
            "financial": {"max_spend": 1000.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write", "execute"],
                "blocked_actions": [],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/"], "blocked_paths": []},
            "communication": {"allowed_channels": [], "blocked_channels": []},
        }

        audit_chain = AuditChain(
            session_id="test-chain-session",
            key_id="test-key",
            key_manager=key_manager,
        )

        proxy = PraxisProxy(
            session_id="test-chain-session",
            downstream_servers=[],
            constraint_enforcer=ConstraintEnforcer(constraints),
            held_action_manager=HeldActionManager(use_db=False),
            audit_chain=audit_chain,
            key_manager=key_manager,
            key_id="test-key",
        )

        proxy.register_tools(
            "fs",
            [
                {"name": "read_file", "description": "Read", "inputSchema": {}},
                {"name": "write_file", "description": "Write", "inputSchema": {}},
            ],
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/src/a.py"})
        await proxy.handle_tool_call("fs__write_file", {"path": "/src/b.py"})
        await proxy.handle_tool_call("fs__read_file", {"path": "/src/c.py"})

        assert audit_chain.length == 3

        # Verify chain integrity
        valid, breaks = audit_chain.verify_integrity()
        assert valid is True
        assert len(breaks) == 0


# ---------------------------------------------------------------------------
# Tool catalog management
# ---------------------------------------------------------------------------


class TestToolCatalog:
    """Test tool registration and namespacing."""

    def test_register_tools(self):
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(
            session_id="test",
            downstream_servers=[],
        )

        proxy.register_tools(
            "server1",
            [
                {"name": "read_file", "description": "Read a file"},
                {"name": "write_file", "description": "Write a file"},
            ],
        )

        proxy.register_tools(
            "server2",
            [
                {"name": "bash", "description": "Run bash command"},
            ],
        )

        tools = proxy.get_tools()
        names = [t["name"] for t in tools]
        assert "server1__read_file" in names
        assert "server1__write_file" in names
        assert "server2__bash" in names
        assert len(tools) == 3

    def test_parse_tool_name_from_catalog(self):
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(session_id="test", downstream_servers=[])
        proxy.register_tools(
            "myserver",
            [
                {"name": "do_thing", "description": "Does a thing"},
            ],
        )

        server, tool = proxy._parse_tool_name("myserver__do_thing")
        assert server == "myserver"
        assert tool == "do_thing"

    def test_parse_tool_name_fallback(self):
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(session_id="test", downstream_servers=[])

        # Not in catalog but has __ separator -> fallback parsing
        server, tool = proxy._parse_tool_name("unknown__some_tool")
        assert server == "unknown"
        assert tool == "some_tool"

    def test_parse_tool_name_no_separator_raises(self):
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(session_id="test", downstream_servers=[])

        with pytest.raises(ValueError, match="Unknown tool"):
            proxy._parse_tool_name("no_separator_here")

    def test_get_tools_includes_server_prefix_in_description(self):
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(session_id="test", downstream_servers=[])
        proxy.register_tools(
            "myfs",
            [
                {"name": "read_file", "description": "Read a file"},
            ],
        )

        tools = proxy.get_tools()
        assert len(tools) == 1
        assert tools[0]["description"].startswith("[myfs]")


# ---------------------------------------------------------------------------
# No enforcer fallback
# ---------------------------------------------------------------------------


class TestNoEnforcerFallback:
    """Test behavior when no constraint enforcer is available."""

    @pytest.mark.asyncio
    async def test_no_enforcer_defaults_to_auto_approved(self):
        """Without an enforcer, all actions should default to auto_approved."""
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(
            session_id="test-no-enforcer",
            downstream_servers=[],
            constraint_enforcer=None,
        )

        proxy.register_tools(
            "srv",
            [
                {"name": "read_file", "description": "Read"},
            ],
        )

        result = await proxy.handle_tool_call("srv__read_file", {"path": "/tmp/x"})

        assert result.verdict.level.value == "auto_approved"
        assert result.forwarded is True


# ---------------------------------------------------------------------------
# Deliberation capture (M04-03)
# ---------------------------------------------------------------------------


class TestProxyDeliberationCapture:
    """Test that deliberation records are created for proxy tool calls."""

    @pytest.mark.asyncio
    async def test_observation_recorded_for_tool_call(self, key_manager):
        """A deliberation observation should be recorded for every tool call."""
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
        from praxis.core.deliberation import DeliberationEngine
        from praxis.mcp.proxy import PraxisProxy

        constraints = {
            "financial": {"max_spend": 1000.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read", "write", "execute"],
                "blocked_actions": [],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/"], "blocked_paths": []},
            "communication": {"allowed_channels": [], "blocked_channels": []},
        }

        engine = DeliberationEngine(
            session_id="test-delib-session",
            key_manager=key_manager,
            key_id="test-key",
        )

        proxy = PraxisProxy(
            session_id="test-delib-session",
            downstream_servers=[],
            constraint_enforcer=ConstraintEnforcer(constraints),
            held_action_manager=HeldActionManager(use_db=False),
            deliberation_engine=engine,
            key_manager=key_manager,
            key_id="test-key",
        )

        proxy.register_tools(
            "fs",
            [
                {"name": "read_file", "description": "Read", "inputSchema": {}},
            ],
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        # Check that an observation was recorded
        records, total = engine.get_timeline(record_type="observation")
        assert total >= 1
        assert any("fs__read_file" in r.get("content", {}).get("observation", "") for r in records)


# ---------------------------------------------------------------------------
# DownstreamServer dataclass
# ---------------------------------------------------------------------------


class TestDownstreamServer:
    """Test DownstreamServer configuration parsing."""

    def test_from_dict(self):
        from praxis.mcp.proxy import DownstreamServer

        ds = DownstreamServer(
            name="filesystem",
            command="mcp-server-filesystem",
            args=["/home/user"],
        )
        assert ds.name == "filesystem"
        assert ds.command == "mcp-server-filesystem"
        assert ds.args == ["/home/user"]
        assert ds.env is None

    def test_proxy_parses_server_dicts(self):
        from praxis.mcp.proxy import PraxisProxy

        proxy = PraxisProxy(
            session_id="test",
            downstream_servers=[
                {"name": "fs", "command": "mcp-server-fs", "args": ["/"]},
                {"name": "git", "command": "mcp-server-git"},
            ],
        )

        assert len(proxy.downstream) == 2
        assert proxy.downstream[0].name == "fs"
        assert proxy.downstream[0].command == "mcp-server-fs"
        assert proxy.downstream[0].args == ["/"]
        assert proxy.downstream[1].name == "git"
        assert proxy.downstream[1].args == []
