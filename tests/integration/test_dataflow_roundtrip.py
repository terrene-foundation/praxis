# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""M14-01: DataFlow persistence integration tests.

Tests complete round-trips through the persistence layer for all core
data types: sessions, deliberation records, constraint events, trust
chain entries, and held actions.  Every test uses a real SQLite database
(via the _isolated_db autouse fixture) and real core components — no mocking.
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# 1. Session round-trip
# ---------------------------------------------------------------------------


class TestSessionRoundTrip:
    """Create via SessionManager, read back, verify all fields match."""

    def test_create_and_read_back_all_fields(self, key_manager, sample_constraints):
        """Session created through SessionManager survives a full DB round-trip."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-rt-001",
            domain="coc",
            constraints=sample_constraints,
            authority_id="admin-user",
        )
        session_id = session["session_id"]

        retrieved = mgr.get_session(session_id)

        assert retrieved["session_id"] == session_id
        assert retrieved["workspace_id"] == "ws-rt-001"
        assert retrieved["domain"] == "coc"
        assert retrieved["state"] == "active"
        assert retrieved["genesis_id"] is not None
        assert retrieved["constraint_envelope"] == sample_constraints
        assert retrieved["created_at"] != ""
        assert retrieved["ended_at"] is None

    def test_session_state_persists_through_lifecycle(self, key_manager, sample_constraints):
        """State transitions persist correctly through pause/resume/archive."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-lifecycle",
            constraints=sample_constraints,
        )
        sid = session["session_id"]

        # Pause
        mgr.pause_session(sid, reason="break")
        assert mgr.get_session(sid)["state"] == "paused"

        # Resume
        mgr.resume_session(sid)
        assert mgr.get_session(sid)["state"] == "active"

        # Archive
        mgr.end_session(sid, summary="done")
        ended = mgr.get_session(sid)
        assert ended["state"] == "archived"
        assert ended["ended_at"] is not None

    def test_list_sessions_filters_workspace_and_domain(self, key_manager, sample_constraints):
        """list_sessions correctly applies workspace_id and domain filters."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-a", domain="coc", constraints=sample_constraints)
        mgr.create_session(workspace_id="ws-a", domain="coe", constraints=sample_constraints)
        mgr.create_session(workspace_id="ws-b", domain="coc", constraints=sample_constraints)

        all_a = mgr.list_sessions(workspace_id="ws-a")
        assert len(all_a) == 2

        all_b = mgr.list_sessions(workspace_id="ws-b")
        assert len(all_b) == 1


# ---------------------------------------------------------------------------
# 2. DeliberationRecord round-trip
# ---------------------------------------------------------------------------


class TestDeliberationRecordRoundTrip:
    """Record decisions, read from DB, verify hash chain."""

    def test_decision_round_trip_with_hash_chain(self, key_manager):
        """Decisions persist and hash chain is intact after re-read."""
        from praxis.core.deliberation import DeliberationEngine

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        d1 = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Battle-tested reliability",
            actor="human",
            alternatives=["SQLite", "MySQL"],
            confidence=0.9,
        )
        d2 = engine.record_decision(
            decision="Connection pool = 20",
            rationale="Load test results",
            actor="human",
            confidence=0.95,
        )

        # Re-read from DB
        timeline, total = engine.get_timeline()
        assert total == 2

        # Chain integrity: first record has no parent, second links to first
        assert timeline[0]["parent_record_id"] is None
        assert timeline[1]["parent_record_id"] == timeline[0]["reasoning_hash"]

        # Content fidelity
        assert timeline[0]["content"]["decision"] == "Use PostgreSQL"
        assert timeline[0]["content"]["alternatives"] == ["SQLite", "MySQL"]
        assert timeline[0]["confidence"] == 0.9
        assert timeline[1]["content"]["decision"] == "Connection pool = 20"

    def test_observation_round_trip(self, key_manager):
        """Observations persist and chain to previous records."""
        from praxis.core.deliberation import DeliberationEngine

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        engine.record_decision(decision="Start", rationale="Go")
        engine.record_observation(
            observation="Connection pooling works", actor="ai", confidence=0.85
        )
        engine.record_escalation(issue="Timeout spike", context="Under load", actor="system")

        timeline, total = engine.get_timeline()
        assert total == 3
        assert timeline[0]["record_type"] == "decision"
        assert timeline[1]["record_type"] == "observation"
        assert timeline[2]["record_type"] == "escalation"

        # Chain is contiguous
        assert timeline[1]["parent_record_id"] == timeline[0]["reasoning_hash"]
        assert timeline[2]["parent_record_id"] == timeline[1]["reasoning_hash"]

    def test_anchor_ids_present_when_signed(self, key_manager):
        """Signed records get anchor IDs persisted in the DB."""
        from praxis.core.deliberation import DeliberationEngine

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        engine.record_decision(decision="Anchor test", rationale="Verify")
        timeline, _ = engine.get_timeline()
        assert timeline[0]["anchor_id"] is not None
        assert timeline[0]["anchor_id"].startswith("anchor-")


# ---------------------------------------------------------------------------
# 3. ConstraintEvent round-trip
# ---------------------------------------------------------------------------


class TestConstraintEventRoundTrip:
    """Evaluate constraint, read events from DB."""

    def test_evaluation_events_persist_with_session_id(self, sample_constraints):
        """Events written to DB when session_id is provided on enforcer."""
        from praxis.core.constraint import ConstraintEnforcer

        sid = _sid()
        enforcer = ConstraintEnforcer(sample_constraints, session_id=sid)

        enforcer.evaluate("read", resource="/src/main.py")
        enforcer.evaluate("write", resource="/src/config.py")
        enforcer.evaluate("execute")

        events = enforcer.get_events()
        assert len(events) == 3
        actions = {e["action"] for e in events}
        assert actions == {"read", "write", "execute"}

    def test_blocked_event_persists(self, sample_constraints):
        """A BLOCKED verdict is persisted with correct gradient_result."""
        from praxis.core.constraint import ConstraintEnforcer

        sid = _sid()
        enforcer = ConstraintEnforcer(sample_constraints, session_id=sid)

        # 'delete' is not in allowed_actions
        verdict = enforcer.evaluate("delete")
        assert verdict.level.value == "blocked"

        events = enforcer.get_events()
        assert len(events) == 1
        assert events[0]["verdict"] == "blocked"
        assert events[0]["dimension"] == "operational"


# ---------------------------------------------------------------------------
# 4. TrustChainEntry round-trip
# ---------------------------------------------------------------------------


class TestTrustChainEntryRoundTrip:
    """Create audit anchor, read from DB, verify signature."""

    def test_audit_anchor_persists_and_verifies(self, key_manager):
        """Audit anchors survive a round-trip and chain integrity holds."""
        from praxis.trust.audit import AuditChain

        sid = _sid()
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_manager)

        chain.append(action="read_file", actor="ai", result="auto_approved", resource="/src/a.py")
        chain.append(action="write_file", actor="ai", result="flagged", resource="/src/b.py")
        chain.append(action="deploy", actor="human", result="approved")

        assert chain.length == 3

        # Reload from DB via a new chain instance
        chain2 = AuditChain(session_id=sid, key_id="test-key", key_manager=key_manager)
        assert chain2.length == 3

        valid, breaks = chain2.verify_integrity()
        assert valid is True
        assert breaks == []

        anchors = chain2.anchors
        assert anchors[0].action == "read_file"
        assert anchors[1].action == "write_file"
        assert anchors[2].action == "deploy"

        # Parent hash chain
        assert anchors[0].parent_hash is None
        assert anchors[1].parent_hash == anchors[0].content_hash
        assert anchors[2].parent_hash == anchors[1].content_hash


# ---------------------------------------------------------------------------
# 5. HeldAction round-trip
# ---------------------------------------------------------------------------


class TestHeldActionRoundTrip:
    """Hold, read pending, approve, verify resolved."""

    def test_hold_approve_round_trip(self, sample_constraints):
        """Held action persists, appears in pending, disappears after approval."""
        from praxis.core.constraint import (
            ConstraintEnforcer,
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        sid = _sid()
        held_mgr = HeldActionManager(use_db=True)

        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near financial limit",
            action="write",
            resource="/src/expensive.py",
        )

        held = held_mgr.hold(
            session_id=sid, action="write", resource="/src/expensive.py", verdict=verdict
        )
        assert held.held_id is not None
        assert held.resolved is False

        # Pending query
        pending = held_mgr.get_pending(session_id=sid)
        assert len(pending) == 1
        assert pending[0].held_id == held.held_id

        # Approve
        held_mgr.approve(held.held_id, approved_by="supervisor")

        # No longer pending
        pending_after = held_mgr.get_pending(session_id=sid)
        assert len(pending_after) == 0

        # But still retrievable
        resolved = held_mgr.get_held(held.held_id)
        assert resolved.resolved is True
        assert resolved.resolution == "approved"
        assert resolved.resolved_by == "supervisor"

    def test_hold_deny_round_trip(self, sample_constraints):
        """Denied held action is recorded correctly."""
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        sid = _sid()
        held_mgr = HeldActionManager(use_db=True)

        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="operational",
            utilization=0.91,
            reason="High operational load",
            action="execute",
        )

        held = held_mgr.hold(session_id=sid, action="execute", resource=None, verdict=verdict)
        held_mgr.deny(held.held_id, denied_by="admin")

        resolved = held_mgr.get_held(held.held_id)
        assert resolved.resolved is True
        assert resolved.resolution == "denied"
        assert resolved.resolved_by == "admin"

    def test_multiple_held_actions_per_session(self):
        """Multiple held actions in the same session are tracked independently."""
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        sid = _sid()
        held_mgr = HeldActionManager(use_db=True)

        for i in range(3):
            verdict = ConstraintVerdict(
                level=GradientLevel.HELD,
                dimension="financial",
                utilization=0.95,
                reason=f"Action {i}",
                action="write",
            )
            held_mgr.hold(session_id=sid, action="write", resource=f"/file{i}", verdict=verdict)

        pending = held_mgr.get_pending(session_id=sid)
        assert len(pending) == 3

        # Approve just the first one
        held_mgr.approve(pending[0].held_id, approved_by="user")
        assert len(held_mgr.get_pending(session_id=sid)) == 2


# ---------------------------------------------------------------------------
# 6. Restart simulation
# ---------------------------------------------------------------------------


class TestRestartSimulation:
    """Simulate process restart: create data, reset singletons, verify survival."""

    def test_session_survives_db_reset(self, key_manager, sample_constraints):
        """Data persists across reset_db() + re-initialization."""
        from praxis.config import reset_config
        from praxis.core.session import SessionManager
        from praxis.persistence import reset_db

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-restart",
            constraints=sample_constraints,
        )
        sid = session["session_id"]

        # Simulate restart
        reset_db()
        reset_config()

        # Re-read
        mgr2 = SessionManager(key_manager=key_manager, key_id="test-key")
        retrieved = mgr2.get_session(sid)
        assert retrieved["session_id"] == sid
        assert retrieved["workspace_id"] == "ws-restart"
        assert retrieved["state"] == "active"

    def test_deliberation_chain_survives_restart(self, key_manager):
        """Deliberation hash chain is intact after reset/reinit."""
        from praxis.config import reset_config
        from praxis.core.deliberation import DeliberationEngine
        from praxis.persistence import reset_db

        sid = _sid()
        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")
        engine.record_decision(decision="First", rationale="Reason 1")
        engine.record_decision(decision="Second", rationale="Reason 2")

        # Simulate restart
        reset_db()
        reset_config()

        engine2 = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")
        timeline, total = engine2.get_timeline()
        assert total == 2
        assert timeline[0]["parent_record_id"] is None
        assert timeline[1]["parent_record_id"] == timeline[0]["reasoning_hash"]

    def test_audit_chain_survives_restart(self, key_manager):
        """Audit chain anchors and integrity survive reset/reinit."""
        from praxis.config import reset_config
        from praxis.persistence import reset_db
        from praxis.trust.audit import AuditChain

        sid = _sid()
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_manager)
        chain.append(action="read", actor="ai", result="auto_approved")
        chain.append(action="write", actor="ai", result="flagged")

        # Simulate restart
        reset_db()
        reset_config()

        chain2 = AuditChain(session_id=sid, key_id="test-key", key_manager=key_manager)
        assert chain2.length == 2

        valid, breaks = chain2.verify_integrity()
        assert valid is True
        assert breaks == []
