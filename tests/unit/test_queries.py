# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.persistence.queries — query patterns for the persistence layer.

These tests validate the query interface that the API and CLI use to
retrieve data from the in-memory stores in SessionManager, DeliberationEngine,
ConstraintEnforcer, and trust chain components.
"""

import pytest


# ---------------------------------------------------------------------------
# get_session
# ---------------------------------------------------------------------------


class TestGetSession:
    """Test get_session query function."""

    def test_get_session_returns_dict(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import get_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        result = get_session(session["session_id"], session_manager=mgr)
        assert isinstance(result, dict)
        assert result["session_id"] == session["session_id"]

    def test_get_session_not_found_returns_none(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import get_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        result = get_session("nonexistent", session_manager=mgr)
        assert result is None

    def test_get_session_includes_all_fields(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import get_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001", domain="coe")
        result = get_session(session["session_id"], session_manager=mgr)
        assert result["workspace_id"] == "ws-001"
        assert result["domain"] == "coe"
        assert result["state"] == "active"
        assert "constraint_envelope" in result
        assert "created_at" in result
        assert "updated_at" in result


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    """Test list_sessions query function."""

    def test_list_sessions_returns_tuple(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-001")
        sessions, total = list_sessions(session_manager=mgr)
        assert isinstance(sessions, list)
        assert isinstance(total, int)
        assert total == 1
        assert len(sessions) == 1

    def test_list_sessions_filter_by_workspace(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-001")
        mgr.create_session(workspace_id="ws-002")
        mgr.create_session(workspace_id="ws-001")
        sessions, total = list_sessions(workspace_id="ws-001", session_manager=mgr)
        assert total == 2
        assert all(s["workspace_id"] == "ws-001" for s in sessions)

    def test_list_sessions_filter_by_state(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        s1 = mgr.create_session(workspace_id="ws-001")
        mgr.create_session(workspace_id="ws-001")
        mgr.pause_session(s1["session_id"])
        sessions, total = list_sessions(state="paused", session_manager=mgr)
        assert total == 1
        assert sessions[0]["state"] == "paused"

    def test_list_sessions_filter_by_domain(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-001", domain="coc")
        mgr.create_session(workspace_id="ws-001", domain="coe")
        sessions, total = list_sessions(domain="coe", session_manager=mgr)
        assert total == 1
        assert sessions[0]["domain"] == "coe"

    def test_list_sessions_with_limit(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        for _ in range(5):
            mgr.create_session(workspace_id="ws-001")
        sessions, total = list_sessions(limit=2, session_manager=mgr)
        assert len(sessions) == 2
        assert total == 5

    def test_list_sessions_with_offset(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        for _ in range(5):
            mgr.create_session(workspace_id="ws-001")
        sessions, total = list_sessions(offset=3, session_manager=mgr)
        assert len(sessions) == 2
        assert total == 5

    def test_list_sessions_empty(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        sessions, total = list_sessions(session_manager=mgr)
        assert sessions == []
        assert total == 0


# ---------------------------------------------------------------------------
# get_deliberation_timeline
# ---------------------------------------------------------------------------


class TestGetDeliberationTimeline:
    """Test get_deliberation_timeline query function."""

    def test_get_timeline_returns_records_and_count(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.persistence.queries import get_deliberation_timeline

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_observation(observation="o1")
        records, total = get_deliberation_timeline(
            session_id="sess-001", deliberation_engine=engine
        )
        assert len(records) == 2
        assert total == 2

    def test_get_timeline_filter_by_type(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.persistence.queries import get_deliberation_timeline

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_observation(observation="o1")
        engine.record_decision(decision="d2", rationale="r2")
        records, total = get_deliberation_timeline(
            session_id="sess-001", record_type="decision", deliberation_engine=engine
        )
        assert total == 2
        assert all(r["record_type"] == "decision" for r in records)

    def test_get_timeline_with_limit_and_offset(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.persistence.queries import get_deliberation_timeline

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        for i in range(10):
            engine.record_decision(decision=f"d{i}", rationale=f"r{i}")
        records, total = get_deliberation_timeline(
            session_id="sess-001", limit=3, offset=2, deliberation_engine=engine
        )
        assert len(records) == 3
        assert total == 10

    def test_get_timeline_chronological_order(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.persistence.queries import get_deliberation_timeline

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="first", rationale="r1")
        engine.record_observation(observation="second")
        engine.record_escalation(issue="third", context="c1")
        records, _ = get_deliberation_timeline(session_id="sess-001", deliberation_engine=engine)
        assert records[0]["content"]["decision"] == "first"
        assert records[1]["content"]["observation"] == "second"
        assert records[2]["content"]["issue"] == "third"


# ---------------------------------------------------------------------------
# get_trust_chain
# ---------------------------------------------------------------------------


class TestGetTrustChain:
    """Test get_trust_chain query function."""

    def test_get_trust_chain_returns_list(self, key_manager, sample_constraints):
        from praxis.trust.audit import AuditChain
        from praxis.trust.genesis import create_genesis
        from praxis.persistence.queries import get_trust_chain

        genesis = create_genesis(
            session_id="sess-001",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        audit = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        audit.append(action="read", actor="ai", result="auto_approved")

        chain = get_trust_chain(session_id="sess-001", genesis_record=genesis, audit_chain=audit)
        assert isinstance(chain, list)
        assert len(chain) >= 2  # genesis + at least one anchor

    def test_get_trust_chain_first_entry_is_genesis(self, key_manager, sample_constraints):
        from praxis.trust.audit import AuditChain
        from praxis.trust.genesis import create_genesis
        from praxis.persistence.queries import get_trust_chain

        genesis = create_genesis(
            session_id="sess-001",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        audit = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        chain = get_trust_chain(session_id="sess-001", genesis_record=genesis, audit_chain=audit)
        assert chain[0]["payload"]["type"] == "genesis"

    def test_get_trust_chain_empty_when_no_genesis(self):
        from praxis.persistence.queries import get_trust_chain

        chain = get_trust_chain(session_id="sess-001", genesis_record=None, audit_chain=None)
        assert chain == []


# ---------------------------------------------------------------------------
# get_constraint_events
# ---------------------------------------------------------------------------


class TestGetConstraintEvents:
    """Test get_constraint_events query function."""

    def test_get_constraint_events_returns_list(self):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.queries import get_constraint_events

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 10.0},
            "operational": {"allowed_actions": ["read", "write"], "blocked_actions": []},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)
        enforcer.evaluate("read", resource="/src/file.py")
        enforcer.evaluate("write", resource="/src/file.py")
        events = get_constraint_events(session_id="sess-001", constraint_enforcer=enforcer)
        assert isinstance(events, list)
        assert len(events) == 2

    def test_get_constraint_events_filter_by_dimension(self):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.queries import get_constraint_events

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 95.0},
            "operational": {
                "allowed_actions": ["read", "write", "delete"],
                "blocked_actions": ["deploy"],
            },
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": ["/secrets/"]},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)
        # This should be blocked by financial (95 + 10 > 100)
        enforcer.evaluate("read", context={"cost": 10.0})
        # This should be blocked by operational (deploy is blocked)
        enforcer.evaluate("deploy")
        events = get_constraint_events(
            session_id="sess-001",
            dimension="financial",
            constraint_enforcer=enforcer,
        )
        assert all(e["dimension"] == "financial" for e in events)

    def test_get_constraint_events_filter_by_gradient_result(self):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.queries import get_constraint_events

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 5.0},
            "operational": {"allowed_actions": ["read", "write"], "blocked_actions": ["delete"]},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)
        enforcer.evaluate("read", resource="/src/file.py")  # auto_approved
        enforcer.evaluate("delete", resource="/src/file.py")  # blocked
        events = get_constraint_events(
            session_id="sess-001",
            gradient_result="blocked",
            constraint_enforcer=enforcer,
        )
        assert all(e["verdict"] == "blocked" for e in events)


# ---------------------------------------------------------------------------
# get_pending_held_actions
# ---------------------------------------------------------------------------


class TestGetPendingHeldActions:
    """Test get_pending_held_actions query function."""

    def test_get_pending_returns_list(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )
        from praxis.persistence.queries import get_pending_held_actions

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        manager.hold(session_id="sess-001", action="write", resource=None, verdict=verdict)
        pending = get_pending_held_actions(held_action_manager=manager)
        assert isinstance(pending, list)
        assert len(pending) == 1

    def test_get_pending_filter_by_session(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )
        from praxis.persistence.queries import get_pending_held_actions

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        manager.hold(session_id="sess-001", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-002", action="read", resource=None, verdict=verdict)
        pending = get_pending_held_actions(session_id="sess-001", held_action_manager=manager)
        assert len(pending) == 1
        assert pending[0]["session_id"] == "sess-001"

    def test_get_pending_excludes_resolved(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )
        from praxis.persistence.queries import get_pending_held_actions

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        h1 = manager.hold(session_id="sess-001", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-001", action="read", resource=None, verdict=verdict)
        manager.approve(h1.held_id, approved_by="supervisor")
        pending = get_pending_held_actions(held_action_manager=manager)
        assert len(pending) == 1

    def test_get_pending_without_manager_queries_db(self):
        """When no manager is passed, get_pending_held_actions queries DataFlow directly."""
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )
        from praxis.persistence.queries import get_pending_held_actions

        # Create held actions via a manager (which persists to DB)
        manager = HeldActionManager(use_db=True)
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        manager.hold(session_id="sess-direct-001", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-direct-002", action="read", resource=None, verdict=verdict)

        # Query without passing a manager — should query DB directly
        pending = get_pending_held_actions(session_id="sess-direct-001")
        assert len(pending) == 1
        assert pending[0]["session_id"] == "sess-direct-001"

    def test_get_pending_without_manager_all_sessions(self):
        """get_pending_held_actions without manager and no session filter returns all."""
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )
        from praxis.persistence.queries import get_pending_held_actions

        manager = HeldActionManager(use_db=True)
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="temporal",
            utilization=0.91,
            reason="Near time limit",
            action="execute",
        )
        manager.hold(session_id="sess-all-a", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-all-b", action="read", resource=None, verdict=verdict)

        # Query all without manager
        pending = get_pending_held_actions()
        assert len(pending) == 2


# ---------------------------------------------------------------------------
# get_session_stats
# ---------------------------------------------------------------------------


class TestGetSessionStats:
    """Test get_session_stats query function."""

    def test_get_session_stats_returns_dict(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.queries import get_session_stats

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_observation(observation="o1")

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 50.0},
            "operational": {"allowed_actions": ["read"], "blocked_actions": []},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 60},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)

        stats = get_session_stats(
            session_id="sess-001",
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert isinstance(stats, dict)
        assert "decision_count" in stats
        assert "observation_count" in stats
        assert "escalation_count" in stats
        assert "anchor_count" in stats
        assert "constraint_status" in stats

    def test_get_session_stats_counts_decisions(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.queries import get_session_stats

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_decision(decision="d2", rationale="r2")
        engine.record_observation(observation="o1")

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {"allowed_actions": ["read"], "blocked_actions": []},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)

        stats = get_session_stats(
            session_id="sess-001",
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert stats["decision_count"] == 2
        assert stats["observation_count"] == 1
        assert stats["escalation_count"] == 0

    def test_get_session_stats_constraint_utilization(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.queries import get_session_stats

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 80.0},
            "operational": {"allowed_actions": ["read"], "blocked_actions": []},
            "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 30},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }
        enforcer = ConstraintEnforcer(constraints)
        stats = get_session_stats(
            session_id="sess-001",
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert "financial" in stats["constraint_status"]
        assert stats["constraint_status"]["financial"]["utilization"] == pytest.approx(0.8)
