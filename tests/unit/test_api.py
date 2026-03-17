# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.api.handlers — API handler functions.

These tests validate handler logic by calling handlers directly
(not through HTTP). Each handler returns a dict response.
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session_manager(key_manager):
    """Provide a SessionManager with a key manager."""
    from praxis.core.session import SessionManager

    return SessionManager(key_manager=key_manager, key_id="test-key")


@pytest.fixture
def active_session(session_manager):
    """Create and return an active session."""
    return session_manager.create_session(workspace_id="ws-test", domain="coc")


@pytest.fixture
def deliberation_engine(active_session, key_manager):
    """Provide a DeliberationEngine for the active session."""
    from praxis.core.deliberation import DeliberationEngine

    return DeliberationEngine(
        session_id=active_session["session_id"],
        key_manager=key_manager,
        key_id="test-key",
    )


@pytest.fixture
def constraint_enforcer(active_session):
    """Provide a ConstraintEnforcer for the active session."""
    from praxis.core.constraint import ConstraintEnforcer

    return ConstraintEnforcer(active_session["constraint_envelope"])


@pytest.fixture
def held_action_manager():
    """Provide a HeldActionManager."""
    from praxis.core.constraint import HeldActionManager

    return HeldActionManager()


# ---------------------------------------------------------------------------
# Session handlers
# ---------------------------------------------------------------------------


class TestCreateSessionHandler:
    """Test the create_session_handler function."""

    def test_create_session_returns_session_dict(self, session_manager):
        from praxis.api.handlers import create_session_handler

        result = create_session_handler(
            session_manager=session_manager,
            workspace_id="ws-test",
            domain="coc",
            constraint_template="moderate",
        )
        assert "session_id" in result
        assert result["state"] == "active"
        assert result["workspace_id"] == "ws-test"

    def test_create_session_with_custom_constraints(self, session_manager, sample_constraints):
        from praxis.api.handlers import create_session_handler

        result = create_session_handler(
            session_manager=session_manager,
            workspace_id="ws-test",
            constraints=sample_constraints,
        )
        assert result["constraint_envelope"] == sample_constraints

    def test_create_session_empty_workspace_id_returns_error(self, session_manager):
        from praxis.api.handlers import create_session_handler

        result = create_session_handler(
            session_manager=session_manager,
            workspace_id="",
        )
        assert "error" in result

    def test_create_session_invalid_template_returns_error(self, session_manager):
        from praxis.api.handlers import create_session_handler

        result = create_session_handler(
            session_manager=session_manager,
            workspace_id="ws-test",
            constraint_template="nonexistent",
        )
        assert "error" in result


class TestListSessionsHandler:
    """Test the list_sessions_handler function."""

    def test_list_sessions_returns_list(self, session_manager):
        from praxis.api.handlers import list_sessions_handler

        session_manager.create_session(workspace_id="ws-test")
        result = list_sessions_handler(session_manager=session_manager)
        assert "sessions" in result
        assert isinstance(result["sessions"], list)
        assert len(result["sessions"]) == 1

    def test_list_sessions_filter_by_workspace(self, session_manager):
        from praxis.api.handlers import list_sessions_handler

        session_manager.create_session(workspace_id="ws-a")
        session_manager.create_session(workspace_id="ws-b")
        result = list_sessions_handler(
            session_manager=session_manager,
            workspace_id="ws-a",
        )
        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["workspace_id"] == "ws-a"

    def test_list_sessions_empty(self, session_manager):
        from praxis.api.handlers import list_sessions_handler

        result = list_sessions_handler(session_manager=session_manager)
        assert result["sessions"] == []


class TestGetSessionHandler:
    """Test the get_session_handler function."""

    def test_get_session_returns_session(self, session_manager, active_session):
        from praxis.api.handlers import get_session_handler

        result = get_session_handler(
            session_manager=session_manager,
            session_id=active_session["session_id"],
        )
        assert result["session_id"] == active_session["session_id"]

    def test_get_session_not_found_returns_error(self, session_manager):
        from praxis.api.handlers import get_session_handler

        result = get_session_handler(
            session_manager=session_manager,
            session_id="nonexistent",
        )
        assert "error" in result


class TestPauseSessionHandler:
    """Test the pause_session_handler function."""

    def test_pause_session_succeeds(self, session_manager, active_session):
        from praxis.api.handlers import pause_session_handler

        result = pause_session_handler(
            session_manager=session_manager,
            session_id=active_session["session_id"],
            reason="break",
        )
        assert result["state"] == "paused"

    def test_pause_archived_session_returns_error(self, session_manager, active_session):
        from praxis.api.handlers import pause_session_handler

        session_manager.end_session(active_session["session_id"])
        result = pause_session_handler(
            session_manager=session_manager,
            session_id=active_session["session_id"],
        )
        assert "error" in result


class TestResumeSessionHandler:
    """Test the resume_session_handler function."""

    def test_resume_paused_session_succeeds(self, session_manager, active_session):
        from praxis.api.handlers import resume_session_handler

        session_manager.pause_session(active_session["session_id"])
        result = resume_session_handler(
            session_manager=session_manager,
            session_id=active_session["session_id"],
        )
        assert result["state"] == "active"


class TestEndSessionHandler:
    """Test the end_session_handler function."""

    def test_end_session_succeeds(self, session_manager, active_session):
        from praxis.api.handlers import end_session_handler

        result = end_session_handler(
            session_manager=session_manager,
            session_id=active_session["session_id"],
            summary="Done",
        )
        assert result["state"] == "archived"
        assert result["ended_at"] is not None


# ---------------------------------------------------------------------------
# Deliberation handlers
# ---------------------------------------------------------------------------


class TestDecideHandler:
    """Test the decide_handler function."""

    def test_decide_returns_record(self, deliberation_engine):
        from praxis.api.handlers import decide_handler

        result = decide_handler(
            engine=deliberation_engine,
            decision="Use PostgreSQL",
            rationale="Better for production",
            actor="human",
        )
        assert result["record_type"] == "decision"
        assert result["content"]["decision"] == "Use PostgreSQL"

    def test_decide_with_alternatives(self, deliberation_engine):
        from praxis.api.handlers import decide_handler

        result = decide_handler(
            engine=deliberation_engine,
            decision="Use Python",
            rationale="Team expertise",
            alternatives=["Go", "Rust"],
        )
        assert result["content"]["alternatives"] == ["Go", "Rust"]


class TestObserveHandler:
    """Test the observe_handler function."""

    def test_observe_returns_record(self, deliberation_engine):
        from praxis.api.handlers import observe_handler

        result = observe_handler(
            engine=deliberation_engine,
            observation="Build times are slow",
            actor="ai",
        )
        assert result["record_type"] == "observation"
        assert result["content"]["observation"] == "Build times are slow"


class TestTimelineHandler:
    """Test the timeline_handler function."""

    def test_timeline_returns_records_and_total(self, deliberation_engine):
        from praxis.api.handlers import timeline_handler

        deliberation_engine.record_decision(decision="test", rationale="test", actor="human")
        deliberation_engine.record_observation(observation="observed", actor="ai")
        result = timeline_handler(engine=deliberation_engine)
        assert "records" in result
        assert "total" in result
        assert result["total"] == 2

    def test_timeline_with_type_filter(self, deliberation_engine):
        from praxis.api.handlers import timeline_handler

        deliberation_engine.record_decision(decision="test", rationale="test", actor="human")
        deliberation_engine.record_observation(observation="observed", actor="ai")
        result = timeline_handler(engine=deliberation_engine, record_type="decision")
        assert result["total"] == 1
        assert result["records"][0]["record_type"] == "decision"


# ---------------------------------------------------------------------------
# Constraint handlers
# ---------------------------------------------------------------------------


class TestGetConstraintsHandler:
    """Test the get_constraints_handler function."""

    def test_get_constraints_returns_envelope(self, session_manager, active_session):
        from praxis.api.handlers import get_constraints_handler

        result = get_constraints_handler(
            session_manager=session_manager,
            session_id=active_session["session_id"],
        )
        assert "constraint_envelope" in result
        assert isinstance(result["constraint_envelope"], dict)


class TestUpdateConstraintsHandler:
    """Test the update_constraints_handler function."""

    def test_update_constraints_tightening_succeeds(
        self, session_manager, sample_constraints, tighter_constraints
    ):
        from praxis.api.handlers import update_constraints_handler

        session = session_manager.create_session(
            workspace_id="ws-test", constraints=sample_constraints
        )
        result = update_constraints_handler(
            session_manager=session_manager,
            session_id=session["session_id"],
            new_constraints=tighter_constraints,
            rationale="Tightening constraints for security review",
        )
        assert "constraint_envelope" in result

    def test_update_constraints_loosening_returns_error(
        self, session_manager, sample_constraints, looser_constraints
    ):
        from praxis.api.handlers import update_constraints_handler

        session = session_manager.create_session(
            workspace_id="ws-test", constraints=sample_constraints
        )
        result = update_constraints_handler(
            session_manager=session_manager,
            session_id=session["session_id"],
            new_constraints=looser_constraints,
            rationale="Attempting to loosen constraints",
        )
        assert "error" in result


class TestGetGradientHandler:
    """Test the get_gradient_handler function."""

    def test_get_gradient_returns_status(self, constraint_enforcer):
        from praxis.api.handlers import get_gradient_handler

        result = get_gradient_handler(enforcer=constraint_enforcer)
        assert "dimensions" in result
        assert "financial" in result["dimensions"]
        assert "operational" in result["dimensions"]
        assert "temporal" in result["dimensions"]
        assert "data_access" in result["dimensions"]
        assert "communication" in result["dimensions"]


# ---------------------------------------------------------------------------
# Trust handlers
# ---------------------------------------------------------------------------


class TestDelegateHandler:
    """Test the delegate_handler function."""

    def test_delegate_returns_delegation(
        self, key_manager, active_session, sample_constraints, tighter_constraints
    ):
        from praxis.api.handlers import delegate_handler

        result = delegate_handler(
            session_id=active_session["session_id"],
            parent_id=active_session["genesis_id"],
            parent_constraints=sample_constraints,
            delegate_id="ai-agent-1",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=active_session["genesis_id"],
        )
        assert "delegation_id" in result

    def test_delegate_loosening_returns_error(
        self, key_manager, active_session, sample_constraints, looser_constraints
    ):
        from praxis.api.handlers import delegate_handler

        result = delegate_handler(
            session_id=active_session["session_id"],
            parent_id=active_session["genesis_id"],
            parent_constraints=sample_constraints,
            delegate_id="ai-agent-1",
            delegate_constraints=looser_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=active_session["genesis_id"],
        )
        assert "error" in result


class TestApproveHeldActionHandler:
    """Test the approve_handler function."""

    def test_approve_held_action_succeeds(
        self, held_action_manager, constraint_enforcer, active_session
    ):
        from praxis.api.handlers import approve_handler
        from praxis.core.constraint import GradientLevel, ConstraintVerdict

        # Create a held action first
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="deploy",
        )
        held = held_action_manager.hold(
            session_id=active_session["session_id"],
            action="deploy",
            resource=None,
            verdict=verdict,
        )

        result = approve_handler(
            held_action_manager=held_action_manager,
            held_id=held.held_id,
            approved_by="supervisor",
        )
        assert result["resolution"] == "approved"
        assert result["resolved_by"] == "supervisor"


class TestDenyHeldActionHandler:
    """Test the deny_handler function."""

    def test_deny_held_action_succeeds(self, held_action_manager, active_session):
        from praxis.api.handlers import deny_handler
        from praxis.core.constraint import GradientLevel, ConstraintVerdict

        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="temporal",
            utilization=0.95,
            reason="Near time limit",
            action="execute",
        )
        held = held_action_manager.hold(
            session_id=active_session["session_id"],
            action="execute",
            resource=None,
            verdict=verdict,
        )

        result = deny_handler(
            held_action_manager=held_action_manager,
            held_id=held.held_id,
            denied_by="supervisor",
        )
        assert result["resolution"] == "denied"
        assert result["resolved_by"] == "supervisor"


# ---------------------------------------------------------------------------
# Verification handlers
# ---------------------------------------------------------------------------


class TestVerifyHandler:
    """Test the verify_handler function."""

    def test_verify_with_valid_chain(self, key_manager):
        from praxis.api.handlers import verify_handler
        from praxis.trust.genesis import create_genesis
        from praxis.trust.crypto import canonical_hash

        genesis = create_genesis(
            session_id="sess-1",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints={"financial": {"max_spend": 100}},
            domain="coc",
        )

        entries = [
            {
                "payload": genesis.payload,
                "content_hash": genesis.content_hash,
                "signature": genesis.signature,
                "signer_key_id": genesis.signer_key_id,
                "parent_hash": None,
            }
        ]

        public_pem = key_manager.export_public_pem("test-key")
        if isinstance(public_pem, bytes):
            public_pem = public_pem.decode("utf-8")

        public_keys = {"test-key": public_pem}

        result = verify_handler(entries=entries, public_keys=public_keys)
        assert result["valid"] is True
        assert result["total_entries"] == 1
        assert result["verified_entries"] == 1


class TestExportHandler:
    """Test the export_handler function."""

    def test_export_returns_bundle_dict(self, key_manager):
        from praxis.api.handlers import export_handler
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-1", key_id="test-key", key_manager=key_manager)
        chain.append(action="read", actor="ai", result="auto_approved")

        result = export_handler(
            audit_chain=chain,
            key_manager=key_manager,
            key_id="test-key",
            session_id="sess-1",
        )
        assert "session_id" in result
        assert "entries" in result
        assert "public_keys" in result
        assert len(result["entries"]) == 1


class TestAuditHandler:
    """Test the audit_handler function."""

    def test_audit_returns_chain_status(self, key_manager):
        from praxis.api.handlers import audit_handler
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-1", key_id="test-key", key_manager=key_manager)
        chain.append(action="read", actor="ai", result="auto_approved")
        chain.append(action="write", actor="ai", result="flagged")

        result = audit_handler(audit_chain=chain)
        assert result["chain_length"] == 2
        assert result["valid"] is True
        assert result["breaks"] == []


# ---------------------------------------------------------------------------
# Login handler
# ---------------------------------------------------------------------------


class _FakeConfig:
    """Minimal config object for testing login_handler."""

    def __init__(
        self,
        dev_mode=True,
        api_secret="test-secret",
        admin_user="",
        admin_password="",
    ):
        self.dev_mode = dev_mode
        self.api_secret = api_secret
        self.admin_user = admin_user
        self.admin_password = admin_password


class TestLoginHandler:
    """Test the login_handler function."""

    def test_dev_mode_accepts_any_credentials(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(dev_mode=True)
        result = login_handler(username="anyone", password="anything", config=config)
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_dev_mode_token_is_valid_jwt(self):
        from praxis.api.auth import decode_token
        from praxis.api.handlers import login_handler

        config = _FakeConfig(dev_mode=True, api_secret="my-secret")
        result = login_handler(username="testuser", password="pw", config=config)
        payload = decode_token(result["access_token"], "my-secret")
        assert payload["sub"] == "testuser"

    def test_empty_username_returns_error(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(dev_mode=True)
        result = login_handler(username="", password="pw", config=config)
        assert "error" in result

    def test_empty_password_returns_error(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(dev_mode=True)
        result = login_handler(username="user", password="", config=config)
        assert "error" in result

    def test_production_valid_credentials(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(
            dev_mode=False,
            api_secret="prod-secret",
            admin_user="admin",
            admin_password="s3cret",
        )
        result = login_handler(username="admin", password="s3cret", config=config)
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_production_wrong_password_returns_error(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(
            dev_mode=False,
            admin_user="admin",
            admin_password="s3cret",
        )
        result = login_handler(username="admin", password="wrong", config=config)
        assert "error" in result
        assert result["error"]["type"] == "unauthorized"

    def test_production_wrong_username_returns_error(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(
            dev_mode=False,
            admin_user="admin",
            admin_password="s3cret",
        )
        result = login_handler(username="hacker", password="s3cret", config=config)
        assert "error" in result
        assert result["error"]["type"] == "unauthorized"

    def test_production_no_admin_configured_returns_error(self):
        from praxis.api.handlers import login_handler

        config = _FakeConfig(dev_mode=False, admin_user="", admin_password="")
        result = login_handler(username="admin", password="pw", config=config)
        assert "error" in result
        assert result["error"]["type"] == "unauthorized"


# ---------------------------------------------------------------------------
# WebSocket EventBroadcaster
# ---------------------------------------------------------------------------


class TestEventBroadcaster:
    """Test the EventBroadcaster subscribe/broadcast/unsubscribe cycle."""

    @pytest.mark.asyncio
    async def test_subscribe_and_broadcast(self):
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        queue = broadcaster.subscribe()
        assert broadcaster.subscriber_count == 1

        await broadcaster.broadcast("session_created", {"session_id": "s1"})
        event = queue.get_nowait()
        assert event["type"] == "session_created"
        assert event["data"]["session_id"] == "s1"
        assert "timestamp" in event

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_listener(self):
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        queue = broadcaster.subscribe()
        broadcaster.unsubscribe(queue)
        assert broadcaster.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers_receive_events(self):
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        q1 = broadcaster.subscribe()
        q2 = broadcaster.subscribe()

        await broadcaster.broadcast("session_paused", {"session_id": "s2"})

        e1 = q1.get_nowait()
        e2 = q2.get_nowait()
        assert e1["type"] == "session_paused"
        assert e2["type"] == "session_paused"
        assert e1["data"] == e2["data"]

    @pytest.mark.asyncio
    async def test_broadcast_with_no_subscribers_does_not_error(self):
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        # Should not raise
        await broadcaster.broadcast("session_ended", {"session_id": "s3"})

    @pytest.mark.asyncio
    async def test_event_types_for_all_session_lifecycle(self):
        """Verify the broadcaster handles the expected event types."""
        from praxis.api.websocket import EventBroadcaster

        broadcaster = EventBroadcaster()
        queue = broadcaster.subscribe()

        event_types = [
            "session_state_changed",
            "constraint_updated",
            "held_action_created",
            "held_action_resolved",
            "deliberation_recorded",
        ]
        for et in event_types:
            await broadcaster.broadcast(et, {"detail": et})

        received = []
        while not queue.empty():
            received.append(queue.get_nowait()["type"])

        assert received == event_types
