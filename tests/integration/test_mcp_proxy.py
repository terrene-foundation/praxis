# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""M14-03: MCP proxy integration tests.

Tests PraxisProxy.handle_tool_call() with real ConstraintEnforcer,
real AuditChain, real DeliberationEngine, and a real SQLite database.
Verifies that constraint verdicts, held actions, audit anchors, and
deliberation records are created and persisted correctly during proxy
interception.
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sid() -> str:
    return str(uuid.uuid4())


def _make_proxy(
    session_id,
    constraints,
    key_manager=None,
    key_id="test-key",
    with_audit=False,
    with_deliberation=False,
    use_db_held=True,
):
    """Create a PraxisProxy wired to real services."""
    from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
    from praxis.mcp.proxy import PraxisProxy

    enforcer = ConstraintEnforcer(constraints, session_id=session_id)
    held_mgr = HeldActionManager(use_db=use_db_held)

    audit_chain = None
    if with_audit and key_manager:
        from praxis.trust.audit import AuditChain

        audit_chain = AuditChain(session_id=session_id, key_id=key_id, key_manager=key_manager)

    delib_engine = None
    if with_deliberation and key_manager:
        from praxis.core.deliberation import DeliberationEngine

        delib_engine = DeliberationEngine(
            session_id=session_id, key_manager=key_manager, key_id=key_id
        )

    proxy = PraxisProxy(
        session_id=session_id,
        downstream_servers=[],
        constraint_enforcer=enforcer,
        held_action_manager=held_mgr,
        audit_chain=audit_chain,
        deliberation_engine=delib_engine,
        key_manager=key_manager,
        key_id=key_id,
    )

    # Register a standard set of test tools
    proxy.register_tools(
        "fs",
        [
            {"name": "read_file", "description": "Read a file", "inputSchema": {}},
            {"name": "write_file", "description": "Write a file", "inputSchema": {}},
            {"name": "delete_file", "description": "Delete a file", "inputSchema": {}},
        ],
    )
    proxy.register_tools(
        "shell",
        [
            {"name": "bash", "description": "Run bash command", "inputSchema": {}},
        ],
    )

    return proxy, enforcer, held_mgr, audit_chain, delib_engine


PERMISSIVE_CONSTRAINTS = {
    "financial": {"max_spend": 10000.0, "current_spend": 0.0},
    "operational": {
        "allowed_actions": ["read", "write", "execute"],
        "blocked_actions": ["delete"],
    },
    "temporal": {"max_duration_minutes": 480, "elapsed_minutes": 0},
    "data_access": {
        "allowed_paths": ["/src/", "/tests/"],
        "blocked_paths": ["/secrets/"],
    },
    "communication": {"allowed_channels": [], "blocked_channels": []},
}


# ---------------------------------------------------------------------------
# 1. BLOCKED action -> verify rejection
# ---------------------------------------------------------------------------


class TestProxyBlocked:
    """Proxy rejects BLOCKED actions without forwarding."""

    @pytest.mark.asyncio
    async def test_blocked_path_rejected(self, key_manager):
        """Reading a blocked path is rejected and persists a constraint event."""
        sid = _sid()
        proxy, enforcer, _, _, _ = _make_proxy(sid, PERMISSIVE_CONSTRAINTS, key_manager=key_manager)

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/secrets/key.pem"})

        assert result.verdict.level.value == "blocked"
        assert result.forwarded is False
        assert result.error is not None
        assert "BLOCKED" in result.error

        # Verify constraint event was persisted
        events = enforcer.get_events()
        assert len(events) == 1
        assert events[0]["verdict"] == "blocked"

    @pytest.mark.asyncio
    async def test_blocked_action_type_rejected(self, key_manager):
        """Blocked action types (delete) are rejected."""
        sid = _sid()
        proxy, enforcer, _, _, _ = _make_proxy(sid, PERMISSIVE_CONSTRAINTS, key_manager=key_manager)

        result = await proxy.handle_tool_call("fs__delete_file", {"path": "/src/old.py"})

        assert result.verdict.level.value == "blocked"
        assert result.forwarded is False


# ---------------------------------------------------------------------------
# 2. HELD action -> verify held_action_id returned
# ---------------------------------------------------------------------------


class TestProxyHeld:
    """Proxy holds actions near constraint boundaries."""

    @pytest.mark.asyncio
    async def test_temporal_held_returns_held_id(self, key_manager):
        """Actions near temporal limit produce a held action with an ID."""
        constraints = dict(PERMISSIVE_CONSTRAINTS)
        constraints["temporal"] = {
            "max_duration_minutes": 100,
            "elapsed_minutes": 92,  # 92% -> HELD
        }

        sid = _sid()
        proxy, _, held_mgr, _, _ = _make_proxy(sid, constraints, key_manager=key_manager)

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        assert result.verdict.level.value == "held"
        assert result.held_action_id is not None
        assert result.forwarded is False
        assert "HELD" in result.error

        # Verify held action was created in DB
        pending = held_mgr.get_pending(session_id=sid)
        assert len(pending) == 1
        assert pending[0].held_id == result.held_action_id

    @pytest.mark.asyncio
    async def test_financial_held_returns_held_id(self, key_manager):
        """Actions near financial limit produce a held action."""
        constraints = dict(PERMISSIVE_CONSTRAINTS)
        constraints["financial"] = {
            "max_spend": 100.0,
            "current_spend": 92.0,  # 92% -> HELD
        }

        sid = _sid()
        proxy, _, held_mgr, _, _ = _make_proxy(sid, constraints, key_manager=key_manager)

        result = await proxy.handle_tool_call("fs__write_file", {"path": "/src/output.py"})

        assert result.verdict.level.value == "held"
        assert result.held_action_id is not None


# ---------------------------------------------------------------------------
# 3. AUTO_APPROVED -> verify pass-through
# ---------------------------------------------------------------------------


class TestProxyAutoApproved:
    """Proxy forwards AUTO_APPROVED actions."""

    @pytest.mark.asyncio
    async def test_auto_approved_forwards(self, key_manager):
        """Low-utilization actions are forwarded (response comes from downstream stub)."""
        sid = _sid()
        proxy, _, _, _, _ = _make_proxy(sid, PERMISSIVE_CONSTRAINTS, key_manager=key_manager)

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        assert result.verdict.level.value == "auto_approved"
        assert result.forwarded is True
        # No downstream connected, so response is a stub dict
        assert result.response is not None
        assert result.error is None


# ---------------------------------------------------------------------------
# 4. FLAGGED -> verify forwarded with warning
# ---------------------------------------------------------------------------


class TestProxyFlagged:
    """Proxy forwards FLAGGED actions with a warning."""

    @pytest.mark.asyncio
    async def test_flagged_forwards_with_warning(self, key_manager):
        """Actions at 75% temporal utilization are FLAGGED and forwarded."""
        constraints = dict(PERMISSIVE_CONSTRAINTS)
        constraints["temporal"] = {
            "max_duration_minutes": 100,
            "elapsed_minutes": 75,  # 75% -> FLAGGED
        }

        sid = _sid()
        proxy, _, _, _, _ = _make_proxy(sid, constraints, key_manager=key_manager)

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        assert result.verdict.level.value == "flagged"
        assert result.forwarded is True
        assert result.error is None


# ---------------------------------------------------------------------------
# 5. Audit chain creation during proxy flow
# ---------------------------------------------------------------------------


class TestProxyAuditChain:
    """Audit anchors are created for every proxied tool call."""

    @pytest.mark.asyncio
    async def test_audit_anchor_created_for_auto_approved(self, key_manager):
        """Auto-approved calls produce an audit anchor."""
        sid = _sid()
        proxy, _, _, audit_chain, _ = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_audit=True,
        )

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        assert result.audit_anchor_id is not None
        assert audit_chain.length == 1

        anchors = audit_chain.anchors
        assert anchors[0].result == "auto_approved"
        assert anchors[0].payload.get("tool_name") == "fs__read_file"

    @pytest.mark.asyncio
    async def test_audit_anchor_created_for_blocked(self, key_manager):
        """Blocked calls also produce an audit anchor (evidence of attempted violation)."""
        sid = _sid()
        proxy, _, _, audit_chain, _ = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_audit=True,
        )

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/secrets/key.pem"})

        assert result.verdict.level.value == "blocked"
        assert result.audit_anchor_id is not None
        assert audit_chain.length == 1
        assert audit_chain.anchors[0].result == "blocked"

    @pytest.mark.asyncio
    async def test_multiple_calls_produce_valid_chain(self, key_manager):
        """Multiple tool calls produce a chain of anchors with valid integrity."""
        sid = _sid()
        proxy, _, _, audit_chain, _ = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_audit=True,
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/src/a.py"})
        await proxy.handle_tool_call("fs__write_file", {"path": "/src/b.py"})
        await proxy.handle_tool_call("fs__read_file", {"path": "/src/c.py"})

        assert audit_chain.length == 3

        valid, breaks = audit_chain.verify_integrity()
        assert valid is True
        assert breaks == []

    @pytest.mark.asyncio
    async def test_held_call_includes_held_action_id_in_anchor(self, key_manager):
        """Held actions store the held_action_id in the audit anchor payload."""
        constraints = dict(PERMISSIVE_CONSTRAINTS)
        constraints["temporal"] = {
            "max_duration_minutes": 100,
            "elapsed_minutes": 92,
        }

        sid = _sid()
        proxy, _, _, audit_chain, _ = _make_proxy(
            sid,
            constraints,
            key_manager=key_manager,
            with_audit=True,
        )

        result = await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        assert result.held_action_id is not None
        assert audit_chain.length == 1
        anchor = audit_chain.anchors[0]
        assert anchor.payload.get("held_action_id") == result.held_action_id


# ---------------------------------------------------------------------------
# 6. Deliberation capture during proxy flow
# ---------------------------------------------------------------------------


class TestProxyDeliberation:
    """Deliberation observations are recorded for proxied tool calls."""

    @pytest.mark.asyncio
    async def test_observation_recorded_for_auto_approved(self, key_manager):
        """Auto-approved tool calls create deliberation observations."""
        sid = _sid()
        proxy, _, _, _, delib_engine = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_deliberation=True,
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        records, total = delib_engine.get_timeline(record_type="observation")
        assert total >= 1
        assert any("fs__read_file" in r.get("content", {}).get("observation", "") for r in records)

    @pytest.mark.asyncio
    async def test_observation_recorded_for_blocked(self, key_manager):
        """Blocked tool calls also create deliberation observations."""
        sid = _sid()
        proxy, _, _, _, delib_engine = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_deliberation=True,
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/secrets/x"})

        records, total = delib_engine.get_timeline(record_type="observation")
        assert total >= 1
        assert any("blocked" in r.get("content", {}).get("observation", "") for r in records)

    @pytest.mark.asyncio
    async def test_multiple_calls_build_deliberation_chain(self, key_manager):
        """Multiple tool calls produce a hash-chained deliberation timeline."""
        sid = _sid()
        proxy, _, _, _, delib_engine = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_deliberation=True,
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/src/a.py"})
        await proxy.handle_tool_call("fs__write_file", {"path": "/src/b.py"})

        records, total = delib_engine.get_timeline()
        assert total == 2

        # Hash chain integrity
        assert records[0]["parent_record_id"] is None
        assert records[1]["parent_record_id"] == records[0]["reasoning_hash"]

    @pytest.mark.asyncio
    async def test_combined_audit_and_deliberation(self, key_manager):
        """Both audit anchors and deliberation records are created together."""
        sid = _sid()
        proxy, _, _, audit_chain, delib_engine = _make_proxy(
            sid,
            PERMISSIVE_CONSTRAINTS,
            key_manager=key_manager,
            with_audit=True,
            with_deliberation=True,
        )

        await proxy.handle_tool_call("fs__read_file", {"path": "/src/main.py"})

        # Audit chain has an anchor
        assert audit_chain.length == 1

        # Deliberation has an observation
        records, total = delib_engine.get_timeline()
        assert total >= 1

        # Both should reference the same session
        assert audit_chain.anchors[0].session_id == sid
        assert records[0]["session_id"] == sid
