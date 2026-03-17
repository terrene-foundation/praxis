# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Integration tests for complete session lifecycle.

Tests the full pipeline: create workspace context -> start session ->
record decisions -> evaluate constraints -> end session -> export archive.
These tests use real components (no mocking) to verify module interactions.
"""

import pytest


class TestFullSessionLifecycle:
    """Test complete session lifecycle without HTTP."""

    def test_create_session_record_decisions_evaluate_constraints_end_export(
        self, key_manager, sample_constraints
    ):
        """Create workspace -> start session -> record decisions ->
        evaluate constraints -> end -> export archive."""
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session
        from praxis.persistence.queries import (
            get_constraint_events,
            get_deliberation_timeline,
            get_session,
            get_session_stats,
            list_sessions,
        )

        # Step 1: Create session manager and session
        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-integration",
            domain="coc",
            constraints=sample_constraints,
        )
        session_id = session["session_id"]
        assert session["state"] == "active"

        # Step 2: Verify session is queryable
        retrieved = get_session(session_id, session_manager=mgr)
        assert retrieved is not None
        assert retrieved["session_id"] == session_id

        sessions, count = list_sessions(workspace_id="ws-integration", session_manager=mgr)
        assert count == 1

        # Step 3: Record deliberation
        engine = DeliberationEngine(
            session_id=session_id, key_manager=key_manager, key_id="test-key"
        )
        d1 = engine.record_decision(
            decision="Use PostgreSQL for production",
            rationale="Proven reliability at scale",
            actor="human",
            alternatives=["SQLite", "MySQL"],
            confidence=0.9,
        )
        engine.record_observation(
            observation="Connection pooling works with asyncpg",
            actor="ai",
            confidence=0.85,
        )
        engine.record_decision(
            decision="Add connection pool size of 20",
            rationale="Based on load testing results",
            actor="human",
            confidence=0.95,
        )

        # Verify hash chain integrity
        timeline, total = get_deliberation_timeline(
            session_id=session_id, deliberation_engine=engine
        )
        assert total == 3
        assert timeline[0]["parent_record_id"] is None
        assert timeline[1]["parent_record_id"] == timeline[0]["reasoning_hash"]
        assert timeline[2]["parent_record_id"] == timeline[1]["reasoning_hash"]

        # Step 4: Evaluate constraints
        enforcer = ConstraintEnforcer(sample_constraints)
        v1 = enforcer.evaluate("read", resource="/src/main.py")
        assert v1.level.value == "auto_approved"

        v2 = enforcer.evaluate("write", resource="/src/config.py")
        assert v2.level.value == "auto_approved"

        events = get_constraint_events(session_id=session_id, constraint_enforcer=enforcer)
        assert len(events) == 2

        # Step 5: Get session stats
        stats = get_session_stats(
            session_id=session_id,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert stats["decision_count"] == 2
        assert stats["observation_count"] == 1
        assert stats["escalation_count"] == 0

        # Step 6: End session
        ended = mgr.end_session(session_id, summary="Integration test complete")
        assert ended["state"] == "archived"
        assert ended["ended_at"] is not None

        # Step 7: Export archive
        archive = export_session(
            session_id=session_id,
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert archive["session"]["state"] == "archived"
        assert len(archive["deliberation"]) == 3
        assert len(archive["constraint_events"]) == 2

    def test_session_pause_resume_lifecycle(self, key_manager, sample_constraints):
        """Test pause -> resume -> continue working -> end lifecycle."""
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-pause-test",
            constraints=sample_constraints,
        )
        session_id = session["session_id"]

        # Record decision before pause
        engine = DeliberationEngine(
            session_id=session_id, key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(
            decision="Start feature implementation",
            rationale="Approved by team lead",
        )

        # Pause
        paused = mgr.pause_session(session_id, reason="lunch break")
        assert paused["state"] == "paused"

        # Resume
        resumed = mgr.resume_session(session_id)
        assert resumed["state"] == "active"

        # Record more decisions after resume
        engine.record_decision(
            decision="Complete feature",
            rationale="All tests pass",
        )

        # End
        ended = mgr.end_session(session_id, summary="Feature completed")
        assert ended["state"] == "archived"

        # Verify the complete timeline
        timeline, total = engine.get_timeline()
        assert total == 2
        # Chain should still be intact across pause/resume
        assert timeline[1]["parent_record_id"] == timeline[0]["reasoning_hash"]

    def test_constraint_tightening_through_session(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        """Test constraint tightening during a session lifecycle."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-tighten-test",
            constraints=sample_constraints,
        )
        session_id = session["session_id"]

        # Initial constraints allow write
        enforcer = ConstraintEnforcer(sample_constraints)
        v1 = enforcer.evaluate("write", resource="/src/file.py")
        assert v1.level.value == "auto_approved"

        # Tighten constraints
        updated = mgr.update_constraints(session_id, tighter_constraints)
        assert updated["constraint_envelope"]["financial"]["max_spend"] == 500.0

        # Verify constraints were actually tightened
        tightened_enforcer = ConstraintEnforcer(updated["constraint_envelope"])
        # execute is no longer in allowed_actions (was in sample, not in tighter)
        v2 = tightened_enforcer.evaluate("execute", resource="/src/file.py")
        assert v2.level.value == "blocked"

    def test_held_action_workflow(self, key_manager, sample_constraints):
        """Test held action creation and approval workflow."""
        from praxis.core.constraint import (
            ConstraintEnforcer,
            GradientLevel,
            HeldActionManager,
        )
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import get_pending_held_actions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-held-test",
            constraints=sample_constraints,
        )
        session_id = session["session_id"]

        # Create a constraint envelope where financial is near limit
        high_util_constraints = dict(sample_constraints)
        high_util_constraints["financial"] = {
            "max_spend": 100.0,
            "current_spend": 92.0,
        }
        enforcer = ConstraintEnforcer(high_util_constraints)

        # Evaluate -- should be HELD due to 92% financial utilization
        verdict = enforcer.evaluate("write")
        assert verdict.level == GradientLevel.HELD

        # Create held action
        held_mgr = HeldActionManager()
        held = held_mgr.hold(
            session_id=session_id,
            action="write",
            resource=None,
            verdict=verdict,
        )

        # Verify pending
        pending = get_pending_held_actions(session_id=session_id, held_action_manager=held_mgr)
        assert len(pending) == 1

        # Approve
        held_mgr.approve(held.held_id, approved_by="supervisor-1")

        # Verify no longer pending
        pending_after = get_pending_held_actions(
            session_id=session_id, held_action_manager=held_mgr
        )
        assert len(pending_after) == 0

    def test_multi_session_workspace(self, key_manager, sample_constraints):
        """Test multiple sessions in the same workspace."""
        from praxis.core.session import SessionManager
        from praxis.persistence.queries import list_sessions

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        # Create multiple sessions
        s1 = mgr.create_session(workspace_id="ws-multi", domain="coc")
        s2 = mgr.create_session(workspace_id="ws-multi", domain="coe")
        s3 = mgr.create_session(workspace_id="ws-other", domain="coc")

        # List all in workspace
        sessions, total = list_sessions(workspace_id="ws-multi", session_manager=mgr)
        assert total == 2

        # Filter by domain within workspace
        coc_sessions, coc_total = list_sessions(
            workspace_id="ws-multi", domain="coc", session_manager=mgr
        )
        assert coc_total == 1
        assert coc_sessions[0]["domain"] == "coc"

        # End one session, verify filtering by state
        mgr.end_session(s1["session_id"])
        active_sessions, active_total = list_sessions(
            workspace_id="ws-multi", state="active", session_manager=mgr
        )
        assert active_total == 1
