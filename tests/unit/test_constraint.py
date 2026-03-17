# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.core.constraint — 5-dimensional constraint enforcer."""

import pytest


# ---------------------------------------------------------------------------
# GradientLevel enum
# ---------------------------------------------------------------------------


class TestGradientLevel:
    """Test GradientLevel enum values."""

    def test_all_levels_exist(self):
        from praxis.core.constraint import GradientLevel

        assert GradientLevel.AUTO_APPROVED == "auto_approved"
        assert GradientLevel.FLAGGED == "flagged"
        assert GradientLevel.HELD == "held"
        assert GradientLevel.BLOCKED == "blocked"

    def test_gradient_level_is_str_enum(self):
        from praxis.core.constraint import GradientLevel

        assert isinstance(GradientLevel.BLOCKED, str)


# ---------------------------------------------------------------------------
# CONSTRAINT_DIMENSIONS
# ---------------------------------------------------------------------------


class TestConstraintDimensions:
    """Test the five constraint dimensions are properly defined."""

    def test_five_dimensions(self):
        from praxis.core.constraint import CONSTRAINT_DIMENSIONS

        assert len(CONSTRAINT_DIMENSIONS) == 5

    def test_exact_dimension_names(self):
        from praxis.core.constraint import CONSTRAINT_DIMENSIONS

        assert "financial" in CONSTRAINT_DIMENSIONS
        assert "operational" in CONSTRAINT_DIMENSIONS
        assert "temporal" in CONSTRAINT_DIMENSIONS
        assert "data_access" in CONSTRAINT_DIMENSIONS
        assert "communication" in CONSTRAINT_DIMENSIONS


# ---------------------------------------------------------------------------
# ConstraintVerdict dataclass
# ---------------------------------------------------------------------------


class TestConstraintVerdict:
    """Test the ConstraintVerdict dataclass."""

    def test_verdict_has_required_fields(self):
        from praxis.core.constraint import ConstraintVerdict, GradientLevel

        verdict = ConstraintVerdict(
            level=GradientLevel.AUTO_APPROVED,
            dimension="financial",
            utilization=0.3,
            reason="Within limits",
            action="read",
            resource="/src/main.py",
        )
        assert verdict.level == GradientLevel.AUTO_APPROVED
        assert verdict.dimension == "financial"
        assert verdict.utilization == 0.3
        assert verdict.reason == "Within limits"
        assert verdict.action == "read"
        assert verdict.resource == "/src/main.py"

    def test_verdict_resource_defaults_to_none(self):
        from praxis.core.constraint import ConstraintVerdict, GradientLevel

        verdict = ConstraintVerdict(
            level=GradientLevel.FLAGGED,
            dimension="temporal",
            utilization=0.75,
            reason="Approaching time limit",
            action="write",
        )
        assert verdict.resource is None


# ---------------------------------------------------------------------------
# ConstraintEnforcer — Financial dimension
# ---------------------------------------------------------------------------


def _make_full_constraints(**overrides):
    """Build a full 5-dimension constraint envelope with optional overrides."""
    base = {
        "financial": {"max_spend": 100.0, "current_spend": 0.0},
        "operational": {
            "allowed_actions": ["read", "write", "execute", "send"],
            "blocked_actions": [],
        },
        "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
        "data_access": {"allowed_paths": ["/src/", "/tests/"], "blocked_paths": ["/secrets/"]},
        "communication": {
            "allowed_channels": ["internal"],
            "blocked_channels": ["external"],
        },
    }
    base.update(overrides)
    return base


class TestFinancialDimension:
    """Test financial constraint evaluation."""

    def test_auto_approved_low_utilization(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 10.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": 5.0})
        # 15/100 = 15% utilization => AUTO_APPROVED
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_flagged_approaching_limit(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 75.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": 0.0})
        # 75/100 = 75% => FLAGGED
        assert verdict.level in (GradientLevel.FLAGGED, GradientLevel.HELD)

    def test_held_near_limit(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 92.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": 0.0})
        # 92/100 = 92% => HELD
        assert verdict.level == GradientLevel.HELD

    def test_blocked_would_exceed_limit(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 95.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write", context={"cost": 10.0})
        # 95 + 10 = 105 > 100 => BLOCKED
        assert verdict.level == GradientLevel.BLOCKED


# ---------------------------------------------------------------------------
# ConstraintEnforcer — Operational dimension
# ---------------------------------------------------------------------------


class TestOperationalDimension:
    """Test operational constraint evaluation."""

    def test_allowed_action_auto_approved(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            operational={"allowed_actions": ["read", "write"], "blocked_actions": ["delete"]},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_blocked_action(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            operational={"allowed_actions": ["read", "write"], "blocked_actions": ["delete"]},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("delete")
        assert verdict.level == GradientLevel.BLOCKED

    def test_unknown_action_not_in_allowed_is_blocked(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            operational={
                "allowed_actions": ["read", "write"],
                "blocked_actions": [],
            },
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("deploy")
        assert verdict.level == GradientLevel.BLOCKED


# ---------------------------------------------------------------------------
# ConstraintEnforcer — Temporal dimension
# ---------------------------------------------------------------------------


class TestTemporalDimension:
    """Test temporal constraint evaluation."""

    def test_auto_approved_early_in_session(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 30},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 30/120 = 25% => AUTO_APPROVED
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_flagged_approaching_time_limit(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 90},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 90/120 = 75% => FLAGGED
        assert verdict.level in (GradientLevel.FLAGGED, GradientLevel.HELD)

    def test_held_near_time_limit(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 110},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 110/120 = 91.6% => HELD
        assert verdict.level == GradientLevel.HELD

    def test_blocked_time_exceeded(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 125},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 125/120 > 100% => BLOCKED
        assert verdict.level == GradientLevel.BLOCKED


# ---------------------------------------------------------------------------
# ConstraintEnforcer — Data Access dimension
# ---------------------------------------------------------------------------


class TestDataAccessDimension:
    """Test data access constraint evaluation."""

    def test_allowed_path_auto_approved(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            data_access={"allowed_paths": ["/src/", "/tests/"], "blocked_paths": ["/secrets/"]},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read", resource="/src/main.py")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_blocked_path(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            data_access={"allowed_paths": ["/src/"], "blocked_paths": ["/secrets/"]},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read", resource="/secrets/key.pem")
        assert verdict.level == GradientLevel.BLOCKED

    def test_path_not_in_allowed_is_blocked(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            data_access={"allowed_paths": ["/src/"], "blocked_paths": []},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read", resource="/etc/passwd")
        assert verdict.level == GradientLevel.BLOCKED


# ---------------------------------------------------------------------------
# ConstraintEnforcer — Communication dimension
# ---------------------------------------------------------------------------


class TestCommunicationDimension:
    """Test communication constraint evaluation."""

    def test_allowed_channel_auto_approved(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            communication={
                "allowed_channels": ["internal", "email"],
                "blocked_channels": ["external"],
            },
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("send", resource="internal")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_blocked_channel(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            communication={
                "allowed_channels": ["internal"],
                "blocked_channels": ["external"],
            },
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("send", resource="external")
        assert verdict.level == GradientLevel.BLOCKED

    def test_unknown_channel_not_in_allowed_is_blocked(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            communication={
                "allowed_channels": ["internal"],
                "blocked_channels": [],
            },
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("send", resource="slack")
        assert verdict.level == GradientLevel.BLOCKED


# ---------------------------------------------------------------------------
# Multi-dimension evaluation — most restrictive wins
# ---------------------------------------------------------------------------


class TestMultiDimensionEvaluation:
    """Test that evaluate returns the most restrictive verdict across all 5 dimensions."""

    def test_most_restrictive_verdict_wins(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            # Financial is fine (10%)
            financial={"max_spend": 100.0, "current_spend": 10.0},
            # But temporal is over limit (105%)
            temporal={"max_duration_minutes": 100, "elapsed_minutes": 105},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # Temporal is BLOCKED, which should dominate
        assert verdict.level == GradientLevel.BLOCKED

    def test_all_dimensions_auto_approved(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 5.0},
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 10},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read", resource="/src/file.py")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_flagged_dimension_dominates_auto_approved(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 5.0},
            # 75% temporal => FLAGGED
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 90},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read", resource="/src/file.py")
        assert verdict.level in (GradientLevel.FLAGGED, GradientLevel.HELD)

    def test_blocked_dominates_held(self):
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _make_full_constraints(
            # 92% financial => HELD
            financial={"max_spend": 100.0, "current_spend": 92.0},
            # blocked action
            operational={"allowed_actions": ["read"], "blocked_actions": ["write"]},
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("write")
        assert verdict.level == GradientLevel.BLOCKED


# ---------------------------------------------------------------------------
# ConstraintEnforcer.update_utilization
# ---------------------------------------------------------------------------


class TestUpdateUtilization:
    """Test updating utilization values."""

    def test_update_financial_spend(self):
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 10.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        enforcer.update_utilization("financial", 50.0)
        assert enforcer.constraints["financial"]["current_spend"] == 50.0

    def test_update_temporal_elapsed(self):
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 30},
        )
        enforcer = ConstraintEnforcer(constraints)
        enforcer.update_utilization("temporal", 60.0)
        assert enforcer.constraints["temporal"]["elapsed_minutes"] == 60.0

    def test_update_invalid_dimension_raises(self):
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints()
        enforcer = ConstraintEnforcer(constraints)
        with pytest.raises(ValueError, match="[Dd]imension"):
            enforcer.update_utilization("nonexistent", 10.0)


# ---------------------------------------------------------------------------
# ConstraintEnforcer.get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    """Test getting constraint status across all dimensions."""

    def test_get_status_returns_all_dimensions(self):
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints()
        enforcer = ConstraintEnforcer(constraints)
        status = enforcer.get_status()
        assert "financial" in status
        assert "operational" in status
        assert "temporal" in status
        assert "data_access" in status
        assert "communication" in status

    def test_get_status_includes_utilization(self):
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 50.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        status = enforcer.get_status()
        assert "utilization" in status["financial"]
        assert status["financial"]["utilization"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# HeldAction and HeldActionManager
# ---------------------------------------------------------------------------


class TestHeldAction:
    """Test the HeldAction dataclass."""

    def test_held_action_has_required_fields(self):
        from praxis.core.constraint import ConstraintVerdict, GradientLevel, HeldAction

        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        held = HeldAction(
            held_id="h-001",
            session_id="sess-001",
            action="write",
            resource=None,
            dimension="financial",
            verdict=verdict,
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert held.held_id == "h-001"
        assert held.resolved is False
        assert held.resolution is None


class TestHeldActionManager:
    """Test the HeldActionManager for managing held actions."""

    def test_hold_creates_held_action(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        held = manager.hold(
            session_id="sess-001",
            action="write",
            resource=None,
            verdict=verdict,
        )
        assert held.held_id is not None
        assert held.resolved is False

    def test_approve_held_action(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        held = manager.hold(
            session_id="sess-001",
            action="write",
            resource=None,
            verdict=verdict,
        )
        approved = manager.approve(held.held_id, approved_by="supervisor-1")
        assert approved.resolved is True
        assert approved.resolution == "approved"
        assert approved.resolved_by == "supervisor-1"
        assert approved.resolved_at is not None

    def test_deny_held_action(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="temporal",
            utilization=0.95,
            reason="Near time limit",
            action="execute",
        )
        held = manager.hold(
            session_id="sess-001",
            action="execute",
            resource=None,
            verdict=verdict,
        )
        denied = manager.deny(held.held_id, denied_by="supervisor-1")
        assert denied.resolved is True
        assert denied.resolution == "denied"
        assert denied.resolved_by == "supervisor-1"

    def test_get_pending_actions(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

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

        pending = manager.get_pending()
        assert len(pending) == 2

    def test_get_pending_filters_by_session(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

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

        pending = manager.get_pending(session_id="sess-001")
        assert len(pending) == 1
        assert pending[0].session_id == "sess-001"

    def test_get_pending_excludes_resolved(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

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

        pending = manager.get_pending()
        assert len(pending) == 1

    def test_get_held_by_id(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="operational",
            utilization=0.5,
            reason="Needs approval",
            action="deploy",
        )
        held = manager.hold(session_id="sess-001", action="deploy", resource=None, verdict=verdict)
        fetched = manager.get_held(held.held_id)
        assert fetched.held_id == held.held_id
        assert fetched.action == "deploy"

    def test_get_held_not_found_raises(self):
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager()
        with pytest.raises(KeyError, match="nonexistent"):
            manager.get_held("nonexistent")

    def test_approve_already_resolved_raises(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        held = manager.hold(session_id="sess-001", action="write", resource=None, verdict=verdict)
        manager.approve(held.held_id, approved_by="supervisor")
        with pytest.raises(ValueError, match="[Aa]lready resolved"):
            manager.approve(held.held_id, approved_by="supervisor-2")

    def test_deny_already_resolved_raises(self):
        from praxis.core.constraint import (
            ConstraintVerdict,
            GradientLevel,
            HeldActionManager,
        )

        manager = HeldActionManager()
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Near limit",
            action="write",
        )
        held = manager.hold(session_id="sess-001", action="write", resource=None, verdict=verdict)
        manager.deny(held.held_id, denied_by="supervisor")
        with pytest.raises(ValueError, match="[Aa]lready resolved"):
            manager.deny(held.held_id, denied_by="supervisor-2")


# ---------------------------------------------------------------------------
# ConstraintEnforcer — DataFlow persistence (session_id wired)
# ---------------------------------------------------------------------------


class TestConstraintEnforcerPersistence:
    """Test that constraint events are persisted to DataFlow when session_id is set."""

    def test_evaluate_persists_event_to_db(self):
        """When session_id is provided, evaluate() writes to the constraint_events table."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel
        from praxis.persistence.db_ops import db_list

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 10.0},
        )
        enforcer = ConstraintEnforcer(constraints, session_id="sess-db-001")
        verdict = enforcer.evaluate("read", resource="/src/main.py")

        assert verdict.level == GradientLevel.AUTO_APPROVED

        # Verify the event was written to the DB
        records = db_list("ConstraintEvent", filter={"session_id": "sess-db-001"})
        assert len(records) == 1
        assert records[0]["action"] == "read"
        assert records[0]["resource"] == "/src/main.py"
        assert records[0]["gradient_result"] == "auto_approved"
        assert records[0]["session_id"] == "sess-db-001"

    def test_evaluate_does_not_persist_without_session_id(self):
        """When session_id is empty, evaluate() uses the in-memory list only."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.db_ops import db_list

        constraints = _make_full_constraints()
        enforcer = ConstraintEnforcer(constraints)  # No session_id
        enforcer.evaluate("read")

        # In-memory list should have the event
        assert len(enforcer._events) == 1

        # DB should NOT have any events for empty session_id
        all_records = db_list("ConstraintEvent")
        assert len(all_records) == 0

    def test_get_events_reads_from_db(self):
        """get_events() returns DB records when session_id is set."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints()
        enforcer = ConstraintEnforcer(constraints, session_id="sess-db-002")
        enforcer.evaluate("read", resource="/src/file.py")
        enforcer.evaluate("write", resource="/src/other.py")

        events = enforcer.get_events()
        assert len(events) == 2
        actions = {e["action"] for e in events}
        assert "read" in actions
        assert "write" in actions

    def test_get_events_returns_in_memory_without_session_id(self):
        """get_events() returns the in-memory list when session_id is empty."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints()
        enforcer = ConstraintEnforcer(constraints)
        enforcer.evaluate("read")

        events = enforcer.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "read"

    def test_multiple_evaluations_persist_all(self):
        """Multiple evaluations are each persisted as separate DB records."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.db_ops import db_list

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 92.0},
        )
        enforcer = ConstraintEnforcer(constraints, session_id="sess-db-003")
        enforcer.evaluate("read")
        enforcer.evaluate("write")
        enforcer.evaluate("execute")

        records = db_list("ConstraintEvent", filter={"session_id": "sess-db-003"})
        assert len(records) == 3

    def test_persisted_event_has_correct_gradient(self):
        """The gradient_result column matches the evaluation verdict."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel
        from praxis.persistence.db_ops import db_list

        constraints = _make_full_constraints(
            financial={"max_spend": 100.0, "current_spend": 92.0},
        )
        enforcer = ConstraintEnforcer(constraints, session_id="sess-db-004")
        verdict = enforcer.evaluate("write", context={"cost": 0.0})
        assert verdict.level == GradientLevel.HELD

        records = db_list("ConstraintEvent", filter={"session_id": "sess-db-004"})
        assert len(records) == 1
        assert records[0]["gradient_result"] == "held"
        assert records[0]["dimension"] == "financial"

    def test_session_id_isolation(self):
        """Events from different sessions are isolated by session_id."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.persistence.db_ops import db_list

        constraints = _make_full_constraints()
        enforcer_a = ConstraintEnforcer(constraints, session_id="sess-iso-a")
        enforcer_b = ConstraintEnforcer(constraints, session_id="sess-iso-b")

        enforcer_a.evaluate("read")
        enforcer_a.evaluate("write")
        enforcer_b.evaluate("execute")

        events_a = db_list("ConstraintEvent", filter={"session_id": "sess-iso-a"})
        events_b = db_list("ConstraintEvent", filter={"session_id": "sess-iso-b"})

        assert len(events_a) == 2
        assert len(events_b) == 1

    def test_get_events_normalizes_db_records(self):
        """get_events() returns dicts with the same keys as in-memory events."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _make_full_constraints()
        enforcer = ConstraintEnforcer(constraints, session_id="sess-db-norm")
        enforcer.evaluate("read", resource="/src/file.py")

        events = enforcer.get_events()
        assert len(events) == 1
        event = events[0]

        # All expected keys should be present
        assert "action" in event
        assert "resource" in event
        assert "verdict" in event
        assert "dimension" in event
        assert "utilization" in event
        assert event["action"] == "read"
        assert event["resource"] == "/src/file.py"


# ---------------------------------------------------------------------------
# HeldActionManager — DataFlow persistence (use_db=True)
# ---------------------------------------------------------------------------


def _make_held_verdict(**overrides):
    """Build a standard HELD verdict for testing."""
    from praxis.core.constraint import ConstraintVerdict, GradientLevel

    defaults = {
        "level": GradientLevel.HELD,
        "dimension": "financial",
        "utilization": 0.92,
        "reason": "Near limit",
        "action": "write",
        "resource": None,
    }
    defaults.update(overrides)
    return ConstraintVerdict(**defaults)


class TestHeldActionManagerPersistence:
    """Test that HeldActionManager persists to DataFlow when use_db=True."""

    def test_hold_persists_to_db(self):
        """hold() should create a record in the held_actions table."""
        from praxis.core.constraint import HeldActionManager
        from praxis.persistence.db_ops import db_list

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-held-001",
            action="write",
            resource="/src/file.py",
            verdict=verdict,
        )

        # Verify the record exists in the DB
        records = db_list("HeldAction", filter={"session_id": "sess-held-001"})
        assert len(records) == 1
        assert records[0]["id"] == held.held_id
        assert records[0]["action"] == "write"
        assert records[0]["resource"] == "/src/file.py"
        assert records[0]["dimension"] == "financial"
        assert records[0]["resolved"] in (False, 0)

    def test_hold_stores_verdict_payload(self):
        """hold() should serialize the ConstraintVerdict into verdict_payload."""
        from praxis.core.constraint import HeldActionManager
        from praxis.persistence.db_ops import db_read

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict(utilization=0.95, reason="Critical level")
        held = manager.hold(
            session_id="sess-held-002",
            action="execute",
            resource=None,
            verdict=verdict,
        )

        record = db_read("HeldAction", held.held_id)
        assert record is not None
        vp = record["verdict_payload"]
        assert vp["level"] == "held"
        assert vp["dimension"] == "financial"
        assert vp["utilization"] == 0.95
        assert vp["reason"] == "Critical level"

    def test_approve_updates_db(self):
        """approve() should update the resolved fields in the DB."""
        from praxis.core.constraint import HeldActionManager
        from praxis.persistence.db_ops import db_read

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-held-003",
            action="write",
            resource=None,
            verdict=verdict,
        )

        approved = manager.approve(held.held_id, approved_by="supervisor-1")
        assert approved.resolved is True
        assert approved.resolution == "approved"

        # Verify DB was updated
        record = db_read("HeldAction", held.held_id)
        assert record is not None
        assert record["resolved"] in (True, 1)
        assert record["resolution"] == "approved"
        assert record["resolved_by"] == "supervisor-1"
        assert record["resolved_at"] is not None

    def test_deny_updates_db(self):
        """deny() should update the resolved fields in the DB."""
        from praxis.core.constraint import HeldActionManager
        from praxis.persistence.db_ops import db_read

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-held-004",
            action="execute",
            resource=None,
            verdict=verdict,
        )

        denied = manager.deny(held.held_id, denied_by="supervisor-2")
        assert denied.resolved is True
        assert denied.resolution == "denied"

        # Verify DB was updated
        record = db_read("HeldAction", held.held_id)
        assert record is not None
        assert record["resolved"] in (True, 1)
        assert record["resolution"] == "denied"
        assert record["resolved_by"] == "supervisor-2"

    def test_get_held_reads_from_db(self):
        """get_held() should read from the DB and reconstruct the HeldAction."""
        from praxis.core.constraint import GradientLevel, HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict(resource="/src/main.py")
        held = manager.hold(
            session_id="sess-held-005",
            action="write",
            resource="/src/main.py",
            verdict=verdict,
        )

        # Fetch from DB via get_held
        fetched = manager.get_held(held.held_id)
        assert fetched.held_id == held.held_id
        assert fetched.session_id == "sess-held-005"
        assert fetched.action == "write"
        assert fetched.resource == "/src/main.py"
        assert fetched.dimension == "financial"
        assert fetched.verdict.level == GradientLevel.HELD
        assert fetched.verdict.utilization == 0.92

    def test_get_held_not_found_raises(self):
        """get_held() should raise KeyError for unknown IDs."""
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=True)
        with pytest.raises(KeyError, match="nonexistent"):
            manager.get_held("nonexistent")

    def test_get_pending_reads_from_db(self):
        """get_pending() should query the DB for unresolved held actions."""
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        manager.hold(session_id="sess-held-006", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-held-006", action="read", resource=None, verdict=verdict)

        pending = manager.get_pending()
        assert len(pending) == 2

    def test_get_pending_filters_by_session(self):
        """get_pending() with session_id should only return that session's held actions."""
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        manager.hold(session_id="sess-held-007a", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-held-007b", action="read", resource=None, verdict=verdict)

        pending = manager.get_pending(session_id="sess-held-007a")
        assert len(pending) == 1
        assert pending[0].session_id == "sess-held-007a"

    def test_get_pending_excludes_resolved(self):
        """get_pending() should not return approved or denied actions."""
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        h1 = manager.hold(
            session_id="sess-held-008", action="write", resource=None, verdict=verdict
        )
        manager.hold(session_id="sess-held-008", action="read", resource=None, verdict=verdict)
        manager.approve(h1.held_id, approved_by="supervisor")

        pending = manager.get_pending()
        assert len(pending) == 1
        assert pending[0].action == "read"

    def test_approve_already_resolved_raises(self):
        """Cannot approve an already-resolved held action."""
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-held-009", action="write", resource=None, verdict=verdict
        )
        manager.approve(held.held_id, approved_by="supervisor")
        with pytest.raises(ValueError, match="[Aa]lready resolved"):
            manager.approve(held.held_id, approved_by="supervisor-2")

    def test_deny_already_resolved_raises(self):
        """Cannot deny an already-resolved held action."""
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-held-010", action="write", resource=None, verdict=verdict
        )
        manager.deny(held.held_id, denied_by="supervisor")
        with pytest.raises(ValueError, match="[Aa]lready resolved"):
            manager.deny(held.held_id, denied_by="supervisor-2")

    def test_session_id_isolation(self):
        """Held actions from different sessions should be isolated."""
        from praxis.core.constraint import HeldActionManager
        from praxis.persistence.db_ops import db_list

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict()
        manager.hold(session_id="sess-iso-x", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-iso-x", action="read", resource=None, verdict=verdict)
        manager.hold(session_id="sess-iso-y", action="execute", resource=None, verdict=verdict)

        records_x = db_list("HeldAction", filter={"session_id": "sess-iso-x"})
        records_y = db_list("HeldAction", filter={"session_id": "sess-iso-y"})
        assert len(records_x) == 2
        assert len(records_y) == 1

    def test_verdict_roundtrip(self):
        """Verdict should survive serialization to DB and deserialization back."""
        from praxis.core.constraint import GradientLevel, HeldActionManager

        manager = HeldActionManager(use_db=True)
        verdict = _make_held_verdict(
            level=GradientLevel.HELD,
            dimension="temporal",
            utilization=0.91,
            reason="Session nearing time limit",
            action="deploy",
            resource="/prod/server",
        )
        held = manager.hold(
            session_id="sess-held-rt",
            action="deploy",
            resource="/prod/server",
            verdict=verdict,
        )

        fetched = manager.get_held(held.held_id)
        assert fetched.verdict.level == GradientLevel.HELD
        assert fetched.verdict.dimension == "temporal"
        assert fetched.verdict.utilization == 0.91
        assert fetched.verdict.reason == "Session nearing time limit"
        assert fetched.verdict.action == "deploy"
        assert fetched.verdict.resource == "/prod/server"


# ---------------------------------------------------------------------------
# HeldActionManager — in-memory fallback (use_db=False)
# ---------------------------------------------------------------------------


class TestHeldActionManagerInMemory:
    """Test that HeldActionManager still works in-memory when use_db=False."""

    def test_hold_stores_in_memory(self):
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=False)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-mem-001", action="write", resource=None, verdict=verdict
        )
        assert held.held_id in manager._held

    def test_approve_in_memory(self):
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=False)
        verdict = _make_held_verdict()
        held = manager.hold(
            session_id="sess-mem-002", action="write", resource=None, verdict=verdict
        )
        approved = manager.approve(held.held_id, approved_by="supervisor")
        assert approved.resolved is True
        assert approved.resolution == "approved"

    def test_get_pending_in_memory(self):
        from praxis.core.constraint import HeldActionManager

        manager = HeldActionManager(use_db=False)
        verdict = _make_held_verdict()
        manager.hold(session_id="sess-mem-003", action="write", resource=None, verdict=verdict)
        manager.hold(session_id="sess-mem-003", action="read", resource=None, verdict=verdict)
        pending = manager.get_pending()
        assert len(pending) == 2
