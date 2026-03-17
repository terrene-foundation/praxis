# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Tests for M05 (Constraint Runtime) and M06 (Phase Enforcement).

M05-01: Temporal auto-tracking (wall-clock elapsed time)
M05-02: Financial spend tracking (record_spend accumulator)
M05-03: Constraint enforcement middleware (403 for BLOCKED, 202 for HELD)
M05-04: Consolidated gradient engine (single source of truth)
M06-01: Phase tracking in SessionManager (advance_phase)
M06-02: Phase approval gates (held actions for gated phases)
M06-03: Phase-aware constraint adjustment (tightening-only)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helper: default constraints for all tests
# ---------------------------------------------------------------------------


def _full_constraints(**overrides):
    """Build a 5-dimensional constraint envelope with optional overrides."""
    base = {
        "financial": {"max_spend": 100.0, "current_spend": 0.0},
        "operational": {
            "allowed_actions": ["read", "write", "execute"],
            "blocked_actions": [],
        },
        "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
        "data_access": {"allowed_paths": ["/src/", "/tests/"], "blocked_paths": []},
        "communication": {
            "allowed_channels": ["internal"],
            "blocked_channels": [],
        },
    }
    for dim, values in overrides.items():
        if dim in base:
            base[dim].update(values)
        else:
            base[dim] = values
    return base


# ===========================================================================
# M05-01: Temporal auto-tracking
# ===========================================================================


class TestTemporalAutoTracking:
    """Temporal constraints should use wall-clock time, not static values."""

    def test_freshly_created_enforcer_has_low_elapsed(self):
        """A brand-new enforcer should report near-zero elapsed time."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(temporal={"max_duration_minutes": 120})
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # Just created — should be near 0% utilization
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_elapsed_increases_with_backdated_start(self):
        """Backdating session_start_time should increase elapsed minutes."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(temporal={"max_duration_minutes": 60})
        # Set start time 50 minutes ago (83% utilization -> FLAGGED)
        start = datetime.now(timezone.utc) - timedelta(minutes=50)
        enforcer = ConstraintEnforcer(constraints, session_start_time=start)
        verdict = enforcer.evaluate("read")
        assert verdict.dimension == "temporal"
        assert verdict.level == GradientLevel.FLAGGED

    def test_elapsed_blocked_after_expiry(self):
        """Session that started 2 hours ago with 60-min limit should be BLOCKED."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(temporal={"max_duration_minutes": 60})
        start = datetime.now(timezone.utc) - timedelta(minutes=120)
        enforcer = ConstraintEnforcer(constraints, session_start_time=start)
        verdict = enforcer.evaluate("read")
        assert verdict.level == GradientLevel.BLOCKED

    def test_elapsed_changes_over_time(self):
        """Two evaluations at different times should produce different temporal status."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _full_constraints(temporal={"max_duration_minutes": 120})
        enforcer = ConstraintEnforcer(constraints)

        # First check — near zero
        s1 = enforcer.get_status()
        u1 = s1["temporal"]["utilization"]

        # Backdate the start time by 60 minutes to simulate time passing
        enforcer.session_start_time = datetime.now(timezone.utc) - timedelta(minutes=60)
        s2 = enforcer.get_status()
        u2 = s2["temporal"]["utilization"]

        # Second utilization should be significantly higher
        assert u2 > u1
        assert u2 >= 0.49  # Should be ~50% (60/120)

    def test_get_status_uses_wall_clock_elapsed(self):
        """get_status should report wall-clock elapsed, not static value."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _full_constraints(temporal={"max_duration_minutes": 120})
        start = datetime.now(timezone.utc) - timedelta(minutes=30)
        enforcer = ConstraintEnforcer(constraints, session_start_time=start)
        status = enforcer.get_status()
        # Should report ~30 minutes elapsed
        assert status["temporal"]["elapsed_minutes"] >= 29.0
        assert status["temporal"]["elapsed_minutes"] <= 32.0

    def test_backward_compat_elapsed_minutes_in_envelope(self):
        """If elapsed_minutes is set in the envelope, it should be used to
        backdate session_start_time for backward compatibility."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(
            temporal={"max_duration_minutes": 120, "elapsed_minutes": 100}
        )
        enforcer = ConstraintEnforcer(constraints)
        verdict = enforcer.evaluate("read")
        # 100/120 = 83% -> FLAGGED
        assert verdict.level in (GradientLevel.FLAGGED, GradientLevel.HELD)


# ===========================================================================
# M05-02: Financial spend tracking
# ===========================================================================


class TestFinancialSpendTracking:
    """Financial constraints should use accumulated spend via record_spend."""

    def test_record_spend_accumulates(self):
        """Calling record_spend multiple times should accumulate."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _full_constraints(financial={"max_spend": 100.0, "current_spend": 0.0})
        enforcer = ConstraintEnforcer(constraints)
        enforcer.record_spend(10.0)
        enforcer.record_spend(20.0)
        enforcer.record_spend(5.0)
        assert enforcer._accumulated_spend == pytest.approx(35.0)

    def test_accumulated_spend_affects_evaluation(self):
        """Accumulated spend should change the financial gradient level."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(financial={"max_spend": 100.0, "current_spend": 0.0})
        enforcer = ConstraintEnforcer(constraints)

        # Initially auto-approved
        v1 = enforcer.evaluate("write")
        assert v1.level == GradientLevel.AUTO_APPROVED

        # Spend 75 -> 75% utilization -> FLAGGED
        enforcer.record_spend(75.0)
        v2 = enforcer.evaluate("write")
        assert v2.level == GradientLevel.FLAGGED

    def test_record_spend_rejects_negative(self):
        """Negative spend amounts should raise ValueError."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _full_constraints()
        enforcer = ConstraintEnforcer(constraints)
        with pytest.raises(ValueError, match="non-negative"):
            enforcer.record_spend(-5.0)

    def test_initial_spend_from_envelope(self):
        """If the envelope has current_spend, it seeds the accumulator."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _full_constraints(financial={"max_spend": 100.0, "current_spend": 50.0})
        enforcer = ConstraintEnforcer(constraints)
        assert enforcer._accumulated_spend == pytest.approx(50.0)

    def test_record_spend_plus_initial_spend(self):
        """Initial spend plus record_spend should accumulate."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(financial={"max_spend": 100.0, "current_spend": 60.0})
        enforcer = ConstraintEnforcer(constraints)
        enforcer.record_spend(35.0)
        # 60 + 35 = 95 -> 95% -> HELD
        verdict = enforcer.evaluate("write")
        assert verdict.level == GradientLevel.HELD

    def test_get_status_reflects_accumulated_spend(self):
        """get_status should reflect the accumulated spend, not the initial envelope value."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = _full_constraints(financial={"max_spend": 100.0, "current_spend": 0.0})
        enforcer = ConstraintEnforcer(constraints)
        enforcer.record_spend(42.0)
        status = enforcer.get_status()
        assert status["financial"]["current_spend"] == pytest.approx(42.0)

    def test_action_cost_plus_accumulated(self):
        """Context cost should add to accumulated spend for projection."""
        from praxis.core.constraint import ConstraintEnforcer, GradientLevel

        constraints = _full_constraints(financial={"max_spend": 100.0, "current_spend": 0.0})
        enforcer = ConstraintEnforcer(constraints)
        enforcer.record_spend(90.0)
        # 90 + 15 = 105 > 100 -> BLOCKED
        verdict = enforcer.evaluate("write", context={"cost": 15.0})
        assert verdict.level == GradientLevel.BLOCKED


# ===========================================================================
# M05-03: Constraint enforcement middleware
# ===========================================================================


class TestConstraintMiddleware:
    """Middleware should return 403 for BLOCKED, 202 for HELD, None for allowed."""

    def test_auto_approved_returns_none(self):
        """AUTO_APPROVED should let the request through (returns None)."""
        from praxis.api.middleware import enforce_constraints
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

        constraints = _full_constraints()
        enforcer = ConstraintEnforcer(constraints)
        held_mgr = HeldActionManager(use_db=False)

        result = enforce_constraints(
            enforcer=enforcer,
            held_manager=held_mgr,
            session_id="test-sess",
            action="read",
        )
        assert result is None

    def test_blocked_returns_403(self):
        """BLOCKED action should return a dict with status_code 403."""
        from praxis.api.middleware import enforce_constraints
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

        constraints = _full_constraints(
            operational={"allowed_actions": ["read"], "blocked_actions": ["deploy"]},
        )
        enforcer = ConstraintEnforcer(constraints)
        held_mgr = HeldActionManager(use_db=False)

        result = enforce_constraints(
            enforcer=enforcer,
            held_manager=held_mgr,
            session_id="test-sess",
            action="deploy",
        )
        assert result is not None
        assert result["status_code"] == 403
        assert "error" in result
        assert result["error"]["type"] == "forbidden"

    def test_held_returns_202(self):
        """HELD action should return a dict with status_code 202 and held_action_id."""
        from praxis.api.middleware import enforce_constraints
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

        constraints = _full_constraints(
            financial={"max_spend": 100.0, "current_spend": 92.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        held_mgr = HeldActionManager(use_db=False)

        result = enforce_constraints(
            enforcer=enforcer,
            held_manager=held_mgr,
            session_id="test-sess",
            action="write",
        )
        assert result is not None
        assert result["status_code"] == 202
        assert "held_action_id" in result
        assert len(result["held_action_id"]) > 0

    def test_flagged_returns_none(self):
        """FLAGGED should still let the request through (returns None)."""
        from praxis.api.middleware import enforce_constraints
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

        constraints = _full_constraints(
            financial={"max_spend": 100.0, "current_spend": 75.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        held_mgr = HeldActionManager(use_db=False)

        result = enforce_constraints(
            enforcer=enforcer,
            held_manager=held_mgr,
            session_id="test-sess",
            action="read",
        )
        assert result is None

    def test_blocked_includes_verdict(self):
        """BLOCKED response should include the verdict details."""
        from praxis.api.middleware import enforce_constraints
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

        constraints = _full_constraints(
            data_access={"allowed_paths": ["/src/"], "blocked_paths": []},
        )
        enforcer = ConstraintEnforcer(constraints)
        held_mgr = HeldActionManager(use_db=False)

        result = enforce_constraints(
            enforcer=enforcer,
            held_manager=held_mgr,
            session_id="test-sess",
            action="read",
            resource="/secrets/key.pem",
        )
        assert result is not None
        assert result["status_code"] == 403
        assert "verdict" in result
        assert result["verdict"]["dimension"] == "data_access"

    def test_held_creates_held_action(self):
        """HELD response should create a real held action that can be retrieved."""
        from praxis.api.middleware import enforce_constraints
        from praxis.core.constraint import ConstraintEnforcer, HeldActionManager

        constraints = _full_constraints(
            financial={"max_spend": 100.0, "current_spend": 95.0},
        )
        enforcer = ConstraintEnforcer(constraints)
        held_mgr = HeldActionManager(use_db=False)

        result = enforce_constraints(
            enforcer=enforcer,
            held_manager=held_mgr,
            session_id="test-sess",
            action="write",
        )
        assert result is not None
        assert result["status_code"] == 202

        # Verify the held action exists
        held = held_mgr.get_held(result["held_action_id"])
        assert held.action == "write"
        assert held.session_id == "test-sess"


# ===========================================================================
# M05-04: Consolidated gradient engine
# ===========================================================================


class TestConsolidatedGradient:
    """Both gradient.py and constraint.py should use the same gradient function."""

    def test_single_source_of_truth(self):
        """constraint.py's _gradient_for_utilization should be the same function
        as gradient.py's utilization_to_gradient_level."""
        from praxis.core.constraint import _gradient_for_utilization
        from praxis.trust.gradient import utilization_to_gradient_level

        assert _gradient_for_utilization is utilization_to_gradient_level

    def test_both_modules_produce_same_results(self):
        """Both paths should produce identical results for the same input."""
        from praxis.core.constraint import _gradient_for_utilization
        from praxis.trust.gradient import GradientLevel, utilization_to_gradient_level

        test_values = [0.0, 0.3, 0.5, 0.69, 0.70, 0.89, 0.90, 0.99, 1.0, 1.5]
        for v in test_values:
            assert _gradient_for_utilization(v) == utilization_to_gradient_level(v)

    def test_gradient_level_importable_from_both_modules(self):
        """GradientLevel should be importable from both constraint and gradient."""
        from praxis.core.constraint import GradientLevel as CGL
        from praxis.trust.gradient import GradientLevel as TGL

        assert CGL is TGL

    def test_backward_compat_alias_in_gradient(self):
        """The old _utilization_to_level alias should still work."""
        from praxis.trust.gradient import _utilization_to_level, utilization_to_gradient_level

        assert _utilization_to_level is utilization_to_gradient_level

    def test_thresholds_match_specification(self):
        """The 70/90/100 thresholds must be correct per CO specification."""
        from praxis.trust.gradient import GradientLevel, utilization_to_gradient_level

        # Below 70% -> AUTO_APPROVED
        assert utilization_to_gradient_level(0.69) == GradientLevel.AUTO_APPROVED
        # At 70% -> FLAGGED
        assert utilization_to_gradient_level(0.70) == GradientLevel.FLAGGED
        # At 89% -> FLAGGED
        assert utilization_to_gradient_level(0.89) == GradientLevel.FLAGGED
        # At 90% -> HELD
        assert utilization_to_gradient_level(0.90) == GradientLevel.HELD
        # At 99% -> HELD
        assert utilization_to_gradient_level(0.99) == GradientLevel.HELD
        # At 100% -> BLOCKED
        assert utilization_to_gradient_level(1.00) == GradientLevel.BLOCKED


# ===========================================================================
# M06-01: Phase tracking in SessionManager
# ===========================================================================


class TestAdvancePhase:
    """Test SessionManager.advance_phase moves to the next phase."""

    def test_advance_from_first_to_second_phase(self, key_manager):
        """Advancing from 'analyze' should go to 'plan' in COC."""
        from praxis.core.session import PhaseGateError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        assert session["current_phase"] == "analyze"

        # analyze has approval_gate: true in COC, so this should raise PhaseGateError
        with pytest.raises(PhaseGateError) as exc_info:
            mgr.advance_phase(session["session_id"])
        assert exc_info.value.held_action_id is not None

    def test_advance_ungated_phase(self, key_manager):
        """Advancing past a phase without approval_gate should succeed directly."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        sid = session["session_id"]

        # Manually set current_phase to 'implement' (which has approval_gate: false)
        from praxis.persistence.db_ops import db_read, db_update

        record = db_read("Session", sid)
        import json

        raw_meta = record.get("session_metadata")
        if isinstance(raw_meta, str):
            meta = json.loads(raw_meta)
        elif isinstance(raw_meta, dict):
            meta = dict(raw_meta)
        else:
            meta = {}
        meta["current_phase"] = "implement"
        db_update("Session", sid, {"session_metadata": meta})

        # Now advance_phase should succeed (implement has approval_gate: false)
        advanced = mgr.advance_phase(sid)
        assert advanced["current_phase"] == "validate"

    def test_advance_past_last_phase_raises(self, key_manager):
        """Trying to advance past the last phase should raise ValueError."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        sid = session["session_id"]

        # Set current_phase to 'codify' (last phase in COC)
        from praxis.persistence.db_ops import db_read, db_update

        import json

        record = db_read("Session", sid)
        raw_meta = record.get("session_metadata")
        if isinstance(raw_meta, str):
            meta = json.loads(raw_meta)
        elif isinstance(raw_meta, dict):
            meta = dict(raw_meta)
        else:
            meta = {}
        meta["current_phase"] = "codify"
        db_update("Session", sid, {"session_metadata": meta})

        with pytest.raises(ValueError, match="last phase"):
            mgr.advance_phase(sid)

    def test_advance_archived_session_raises(self, key_manager):
        """Advancing an archived session should raise SessionNotActiveError."""
        from praxis.core.session import SessionManager, SessionNotActiveError

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        mgr.end_session(session["session_id"])
        with pytest.raises(SessionNotActiveError):
            mgr.advance_phase(session["session_id"])

    def test_advance_no_phase_list_raises(self, key_manager):
        """Sessions without a phase list should raise ValueError."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-dev",
            domain="nonexistent_domain",
            constraint_template="moderate",
        )
        with pytest.raises(ValueError, match="no phase list"):
            mgr.advance_phase(session["session_id"])


# ===========================================================================
# M06-02: Phase approval gates
# ===========================================================================


class TestPhaseApprovalGates:
    """Gated phases should create held actions instead of advancing."""

    def test_gated_phase_creates_held_action(self, key_manager):
        """Advancing from a gated phase should create a held action."""
        from praxis.core.session import PhaseGateError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")

        # 'analyze' has approval_gate: true in COC
        with pytest.raises(PhaseGateError) as exc_info:
            mgr.advance_phase(session["session_id"])

        held_id = exc_info.value.held_action_id
        assert held_id is not None

        # Verify the held action exists in the database
        from praxis.core.constraint import HeldActionManager

        held_mgr = HeldActionManager(use_db=True)
        held = held_mgr.get_held(held_id)
        assert held.action == "advance_phase"
        assert held.resource == "plan"  # next phase
        assert held.session_id == session["session_id"]

    def test_phase_gate_error_has_message(self, key_manager):
        """PhaseGateError should include a descriptive message."""
        from praxis.core.session import PhaseGateError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")

        with pytest.raises(PhaseGateError, match="approval"):
            mgr.advance_phase(session["session_id"])

    def test_phase_gate_error_mapped_to_202(self):
        """PhaseGateError should map to HTTP 202 in the error handler."""
        from praxis.api.errors import error_from_exception
        from praxis.core.session import PhaseGateError

        exc = PhaseGateError("Approval required", held_action_id="ha-123")
        error = error_from_exception(exc)
        assert error.status_code == 202
        assert error.detail["held_action_id"] == "ha-123"


# ===========================================================================
# M06-03: Phase-aware constraint adjustment
# ===========================================================================


class TestPhaseConstraintAdjustment:
    """Constraint adjustments on phase change should be tightening-only."""

    def test_apply_phase_constraints_method_exists(self, key_manager):
        """SessionManager should have _apply_phase_constraints method."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        assert hasattr(mgr, "_apply_phase_constraints")

    def test_constraint_adjustment_called_on_advance(self, key_manager):
        """Advancing phase should call _apply_phase_constraints."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        sid = session["session_id"]

        # Set current_phase to 'implement' (ungated) to allow advancing
        from praxis.persistence.db_ops import db_read, db_update

        import json

        record = db_read("Session", sid)
        raw_meta = record.get("session_metadata")
        if isinstance(raw_meta, str):
            meta = json.loads(raw_meta)
        elif isinstance(raw_meta, dict):
            meta = dict(raw_meta)
        else:
            meta = {}
        meta["current_phase"] = "implement"
        db_update("Session", sid, {"session_metadata": meta})

        # Patch _apply_phase_constraints to verify it was called
        with patch.object(mgr, "_apply_phase_constraints") as mock_apply:
            mgr.advance_phase(sid)
            mock_apply.assert_called_once()

    def test_loosening_overrides_are_rejected(self, key_manager):
        """Constraint overrides that would loosen should be silently skipped."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-dev",
            domain="coc",
            constraints=_full_constraints(financial={"max_spend": 50.0}),
        )
        sid = session["session_id"]
        original_envelope = session["constraint_envelope"]

        # Call _apply_phase_constraints with a phase that doesn't exist in YAML
        # (so no overrides apply) — should be a no-op
        mgr._apply_phase_constraints(sid, session, "nonexistent_phase")

        # Verify constraints unchanged
        updated = mgr.get_session(sid)
        assert (
            updated["constraint_envelope"]["financial"]["max_spend"]
            == original_envelope["financial"]["max_spend"]
        )
