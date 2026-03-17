# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""M14-02: API integration tests.

Tests handler functions with real core services and a real SQLite database.
Handlers are called directly (not via HTTP) — verifying that the handler
layer correctly wires to core services and that error contracts hold.
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sid() -> str:
    return str(uuid.uuid4())


def _make_session(key_manager, constraints=None):
    """Create a real session and return (mgr, session_dict)."""
    from praxis.core.session import SessionManager

    constraints = constraints or {
        "financial": {"max_spend": 1000.0},
        "operational": {"allowed_actions": ["read", "write", "execute"]},
        "temporal": {"max_duration_minutes": 120},
        "data_access": {"allowed_paths": ["/src", "/tests", "/docs"]},
        "communication": {"allowed_channels": ["internal", "email"]},
    }
    mgr = SessionManager(key_manager=key_manager, key_id="test-key")
    session = mgr.create_session(
        workspace_id="ws-handler-test",
        domain="coc",
        constraints=constraints,
    )
    return mgr, session


# ---------------------------------------------------------------------------
# 1. create_session_handler with real SessionManager + real DB
# ---------------------------------------------------------------------------


class TestCreateSessionHandler:
    """Test create_session_handler with real services."""

    def test_creates_session_successfully(self, key_manager, sample_constraints):
        from praxis.api.handlers import create_session_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        result = create_session_handler(
            session_manager=mgr,
            workspace_id="ws-api-create",
            domain="coc",
            constraints=sample_constraints,
        )

        assert "error" not in result
        assert result["session_id"] is not None
        assert result["state"] == "active"
        assert result["workspace_id"] == "ws-api-create"

    def test_returns_error_on_empty_workspace_id(self, key_manager):
        from praxis.api.handlers import create_session_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        result = create_session_handler(
            session_manager=mgr,
            workspace_id="",
            domain="coc",
        )

        assert "error" in result
        assert result["error"]["type"] == "validation_error"

    def test_returns_error_on_invalid_template(self, key_manager):
        from praxis.api.handlers import create_session_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        result = create_session_handler(
            session_manager=mgr,
            workspace_id="ws-bad-template",
            domain="coc",
            constraint_template="nonexistent",
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# 2. decide_handler with real DeliberationEngine + real DB
# ---------------------------------------------------------------------------


class TestDecideHandler:
    """Test decide_handler with real engine."""

    def test_records_decision_successfully(self, key_manager):
        from praxis.api.handlers import decide_handler
        from praxis.core.deliberation import DeliberationEngine

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        result = decide_handler(
            engine=engine,
            decision="Use Redis for caching",
            rationale="Low latency required",
            actor="human",
            confidence=0.85,
        )

        assert "error" not in result
        assert result["record_type"] == "decision"
        assert result["content"]["decision"] == "Use Redis for caching"
        assert result["confidence"] == 0.85

    def test_returns_error_on_invalid_confidence(self, key_manager):
        from praxis.api.handlers import decide_handler
        from praxis.core.deliberation import DeliberationEngine

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        result = decide_handler(
            engine=engine,
            decision="Bad confidence",
            rationale="Testing error path",
            confidence=1.5,
        )

        assert "error" in result
        assert result["error"]["type"] == "validation_error"

    def test_multiple_decisions_build_hash_chain(self, key_manager):
        from praxis.api.handlers import decide_handler, timeline_handler
        from praxis.core.deliberation import DeliberationEngine

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        decide_handler(engine=engine, decision="First", rationale="Reason 1")
        decide_handler(engine=engine, decision="Second", rationale="Reason 2")
        decide_handler(engine=engine, decision="Third", rationale="Reason 3")

        result = timeline_handler(engine=engine)

        assert "error" not in result
        assert result["total"] == 3
        records = result["records"]
        assert records[0]["parent_record_id"] is None
        assert records[1]["parent_record_id"] == records[0]["reasoning_hash"]
        assert records[2]["parent_record_id"] == records[1]["reasoning_hash"]


# ---------------------------------------------------------------------------
# 3. get_constraints_handler with real session
# ---------------------------------------------------------------------------


class TestGetConstraintsHandler:
    """Test get_constraints_handler with real session."""

    def test_returns_constraint_envelope(self, key_manager, sample_constraints):
        from praxis.api.handlers import get_constraints_handler

        mgr, session = _make_session(key_manager, sample_constraints)

        result = get_constraints_handler(
            session_manager=mgr,
            session_id=session["session_id"],
        )

        assert "error" not in result
        assert "constraint_envelope" in result
        envelope = result["constraint_envelope"]
        assert "financial" in envelope
        assert "operational" in envelope
        assert "temporal" in envelope
        assert "data_access" in envelope
        assert "communication" in envelope

    def test_returns_error_for_nonexistent_session(self, key_manager):
        from praxis.api.handlers import get_constraints_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        result = get_constraints_handler(
            session_manager=mgr,
            session_id="nonexistent-id",
        )

        assert "error" in result
        assert result["error"]["type"] == "not_found"


# ---------------------------------------------------------------------------
# 4. trust_check (constraint evaluation as MCP-style check)
# ---------------------------------------------------------------------------


class TestTrustCheckEnforcement:
    """Test constraint evaluation with a real enforcer backed by a real session."""

    def test_auto_approved_action(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer

        mgr, session = _make_session(key_manager, sample_constraints)
        enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"],
        )

        verdict = enforcer.evaluate("read", resource="/src/main.py")
        assert verdict.level.value == "auto_approved"

    def test_blocked_action(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer

        mgr, session = _make_session(key_manager, sample_constraints)
        enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"],
        )

        verdict = enforcer.evaluate("delete")
        assert verdict.level.value == "blocked"


# ---------------------------------------------------------------------------
# 5. approve/deny handlers with real HeldActionManager
# ---------------------------------------------------------------------------


class TestApproveAndDenyHandlers:
    """Test approve_handler and deny_handler with real DB-backed manager."""

    def _create_held(self, session_id):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        mgr = HeldActionManager(use_db=True)
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        held = mgr.hold(session_id=session_id, action="write", resource=None, verdict=verdict)
        return mgr, held

    def test_approve_handler_resolves_action(self, key_manager, sample_constraints):
        from praxis.api.handlers import approve_handler

        _, session = _make_session(key_manager, sample_constraints)
        held_mgr, held = self._create_held(session["session_id"])

        result = approve_handler(
            held_action_manager=held_mgr,
            held_id=held.held_id,
            approved_by="supervisor",
        )

        assert "error" not in result
        assert result["resolution"] == "approved"
        assert result["resolved_by"] == "supervisor"

    def test_deny_handler_resolves_action(self, key_manager, sample_constraints):
        from praxis.api.handlers import deny_handler

        _, session = _make_session(key_manager, sample_constraints)
        held_mgr, held = self._create_held(session["session_id"])

        result = deny_handler(
            held_action_manager=held_mgr,
            held_id=held.held_id,
            denied_by="admin",
        )

        assert "error" not in result
        assert result["resolution"] == "denied"
        assert result["resolved_by"] == "admin"

    def test_approve_nonexistent_returns_error(self):
        from praxis.api.handlers import approve_handler
        from praxis.core.constraint import HeldActionManager

        mgr = HeldActionManager(use_db=True)

        result = approve_handler(
            held_action_manager=mgr,
            held_id="nonexistent",
            approved_by="user",
        )

        assert "error" in result
        assert result["error"]["type"] == "not_found"

    def test_double_approve_returns_error(self, key_manager, sample_constraints):
        from praxis.api.handlers import approve_handler

        _, session = _make_session(key_manager, sample_constraints)
        held_mgr, held = self._create_held(session["session_id"])

        # First approval succeeds
        approve_handler(
            held_action_manager=held_mgr,
            held_id=held.held_id,
            approved_by="user1",
        )

        # Second approval returns error
        result = approve_handler(
            held_action_manager=held_mgr,
            held_id=held.held_id,
            approved_by="user2",
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# 6. login_handler in dev mode and production mode
# ---------------------------------------------------------------------------


class TestLoginHandler:
    """Test login_handler with real config."""

    def test_dev_mode_accepts_any_credentials(self, monkeypatch):
        from praxis.api.handlers import login_handler
        from praxis.config import get_config, reset_config

        reset_config()
        monkeypatch.setenv("PRAXIS_DEV_MODE", "true")
        monkeypatch.setenv("PRAXIS_API_SECRET", "test-secret")
        reset_config()

        config = get_config()

        result = login_handler(
            username="anyuser",
            password="anypass",
            config=config,
        )

        assert "error" not in result
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_production_rejects_wrong_password(self, monkeypatch):
        from praxis.api.handlers import login_handler
        from praxis.config import get_config, reset_config

        reset_config()
        monkeypatch.setenv("PRAXIS_DEV_MODE", "false")
        monkeypatch.setenv("PRAXIS_API_SECRET", "prod-secret")
        monkeypatch.setenv("PRAXIS_ADMIN_USER", "admin")
        monkeypatch.setenv("PRAXIS_ADMIN_PASSWORD", "secure-password")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_prod.db")
        reset_config()

        config = get_config()

        result = login_handler(
            username="admin",
            password="wrong-password",
            config=config,
        )

        assert "error" in result
        assert result["error"]["type"] == "unauthorized"

    def test_production_accepts_correct_credentials(self, monkeypatch):
        from praxis.api.handlers import login_handler
        from praxis.config import get_config, reset_config

        reset_config()
        monkeypatch.setenv("PRAXIS_DEV_MODE", "false")
        monkeypatch.setenv("PRAXIS_API_SECRET", "prod-secret")
        monkeypatch.setenv("PRAXIS_ADMIN_USER", "admin")
        monkeypatch.setenv("PRAXIS_ADMIN_PASSWORD", "secure-password")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_prod.db")
        reset_config()

        config = get_config()

        result = login_handler(
            username="admin",
            password="secure-password",
            config=config,
        )

        assert "error" not in result
        assert "access_token" in result

    def test_empty_credentials_returns_error(self, monkeypatch):
        from praxis.api.handlers import login_handler
        from praxis.config import get_config, reset_config

        reset_config()
        monkeypatch.setenv("PRAXIS_DEV_MODE", "true")
        monkeypatch.setenv("PRAXIS_API_SECRET", "test-secret")
        reset_config()

        config = get_config()

        result = login_handler(username="", password="", config=config)

        assert "error" in result


# ---------------------------------------------------------------------------
# 7. list_sessions with filters
# ---------------------------------------------------------------------------


class TestListSessionsHandler:
    """Test list_sessions_handler with real DB."""

    def test_list_all_sessions(self, key_manager, sample_constraints):
        from praxis.api.handlers import list_sessions_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-list", domain="coc", constraints=sample_constraints)
        mgr.create_session(workspace_id="ws-list", domain="coe", constraints=sample_constraints)

        result = list_sessions_handler(session_manager=mgr, workspace_id="ws-list")

        assert "error" not in result
        assert len(result["sessions"]) == 2

    def test_list_with_state_filter(self, key_manager, sample_constraints):
        from praxis.api.handlers import list_sessions_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        s1 = mgr.create_session(
            workspace_id="ws-filter", domain="coc", constraints=sample_constraints
        )
        mgr.create_session(workspace_id="ws-filter", domain="coc", constraints=sample_constraints)

        mgr.end_session(s1["session_id"])

        result = list_sessions_handler(
            session_manager=mgr, workspace_id="ws-filter", state="active"
        )

        assert "error" not in result
        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["state"] == "active"

    def test_list_empty_workspace_returns_empty(self, key_manager):
        from praxis.api.handlers import list_sessions_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        result = list_sessions_handler(session_manager=mgr, workspace_id="ws-empty")

        assert "error" not in result
        assert len(result["sessions"]) == 0
