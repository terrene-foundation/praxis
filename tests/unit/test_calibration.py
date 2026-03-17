# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Tests for constraint calibration analysis (M11-04).
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_session(domain: str = "coc") -> str:
    """Create a test session and return its ID."""
    from praxis.core.session import SessionManager

    mgr = SessionManager()
    session = mgr.create_session(
        workspace_id="test-ws",
        domain=domain,
        constraint_template="moderate",
    )
    return session["session_id"]


def _create_constraint_event(
    session_id: str,
    dimension: str = "financial",
    gradient_result: str = "auto_approved",
    utilization: float = 0.5,
) -> str:
    """Create a constraint event in the database."""
    from praxis.persistence.db_ops import db_create

    event_id = str(uuid.uuid4())
    db_create(
        "ConstraintEvent",
        {
            "id": event_id,
            "session_id": session_id,
            "action": "test_action",
            "resource": "/test",
            "dimension": dimension,
            "gradient_result": gradient_result,
            "utilization": utilization,
        },
    )
    return event_id


def _create_held_action(
    session_id: str,
    resolution: str = "approved",
    resolved: bool = True,
) -> str:
    """Create a held action in the database."""
    from praxis.persistence.db_ops import db_create

    held_id = str(uuid.uuid4())
    db_create(
        "HeldAction",
        {
            "id": held_id,
            "session_id": session_id,
            "action": "test_action",
            "resource": "/test",
            "dimension": "operational",
            "verdict_payload": {
                "level": "held",
                "dimension": "operational",
                "utilization": 0.95,
                "reason": "test",
                "action": "test_action",
            },
            "resolved": resolved,
            "resolution": resolution if resolved else None,
            "resolved_by": "test-user" if resolved else None,
        },
    )
    return held_id


# ---------------------------------------------------------------------------
# CalibrationAnalyzer tests
# ---------------------------------------------------------------------------


class TestCalibrationAnalyzer:
    """Tests for the CalibrationAnalyzer class."""

    def test_no_data_returns_empty(self):
        """With no sessions for the domain, returns empty result."""
        from praxis.core.calibration import CalibrationAnalyzer

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("nonexistent-domain")

        assert result["domain"] == "nonexistent-domain"
        assert result["total_evaluations"] == 0
        assert result["total_sessions"] == 0
        assert len(result["recommendations"]) > 0

    def test_basic_calibration_analysis(self):
        """With some events, returns per-dimension analysis."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")

        # Create events across dimensions
        for _ in range(5):
            _create_constraint_event(sid, "financial", "auto_approved", 0.3)
        for _ in range(3):
            _create_constraint_event(sid, "operational", "flagged", 0.75)
        for _ in range(2):
            _create_constraint_event(sid, "temporal", "held", 0.95)

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        assert result["total_evaluations"] == 10
        assert result["total_sessions"] == 1

        # Check dimension data
        dims = result["dimensions"]
        assert dims["financial"]["total_evaluations"] == 5
        assert dims["financial"]["auto_approved"] == 5
        assert dims["operational"]["flagged"] == 3
        assert dims["temporal"]["held"] == 2

    def test_boundary_pressure_detection(self):
        """High utilization events should show up as boundary pressure."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")

        # Create many high-utilization events in financial dimension
        for _ in range(8):
            _create_constraint_event(sid, "financial", "flagged", 0.85)
        for _ in range(2):
            _create_constraint_event(sid, "financial", "auto_approved", 0.50)

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        pressure = result["boundary_pressure"]
        # 8 out of 10 events have utilization > 80%
        assert pressure["financial"] == 0.8

    def test_false_positive_rate(self):
        """Held actions that are all approved should show high false positive rate."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")
        _create_constraint_event(sid, "financial", "auto_approved", 0.5)

        # All held actions approved -> high false positive rate
        for _ in range(5):
            _create_held_action(sid, resolution="approved")

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        assert result["false_positive_rate"] == 1.0

    def test_mixed_resolutions_lower_false_positive(self):
        """Mix of approved and denied should lower false positive rate."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")
        _create_constraint_event(sid, "financial", "auto_approved", 0.5)

        # 3 approved, 2 denied
        for _ in range(3):
            _create_held_action(sid, resolution="approved")
        for _ in range(2):
            _create_held_action(sid, resolution="denied")

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        assert result["false_positive_rate"] == 0.6

    def test_false_negative_estimate(self):
        """Events near the threshold should be flagged as potential false negatives."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")

        # Create many events near the 70% threshold (60-69%)
        for _ in range(25):
            _create_constraint_event(sid, "financial", "auto_approved", 0.65)
        # Some well below threshold
        for _ in range(5):
            _create_constraint_event(sid, "financial", "auto_approved", 0.20)

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        fn = result["false_negative_estimate"]
        assert fn["near_threshold_count"] == 25
        assert fn["total_auto_approved"] == 30
        assert fn["concern"] is True  # > 20% near threshold

    def test_recommendations_for_high_false_positives(self):
        """High false positive rate should generate a recommendation."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")
        _create_constraint_event(sid, "financial", "auto_approved", 0.5)

        for _ in range(10):
            _create_held_action(sid, resolution="approved")

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        recs = result["recommendations"]
        assert any("false positive" in r.lower() for r in recs)

    def test_recommendations_for_boundary_pressure(self):
        """High boundary pressure should generate dimension-specific recommendations."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")

        # Create high-pressure events
        for _ in range(20):
            _create_constraint_event(sid, "temporal", "held", 0.95)

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        recs = result["recommendations"]
        assert any("temporal" in r.lower() and "pressure" in r.lower() for r in recs)

    def test_healthy_calibration_no_issues(self):
        """Well-calibrated constraints should get a healthy recommendation."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")

        # Well-distributed events across dimensions
        for _ in range(15):
            _create_constraint_event(sid, "financial", "auto_approved", 0.3)
        for _ in range(10):
            _create_constraint_event(sid, "operational", "auto_approved", 0.2)
        for _ in range(5):
            _create_constraint_event(sid, "temporal", "flagged", 0.75)

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        recs = result["recommendations"]
        assert any("healthy" in r.lower() for r in recs)

    def test_result_structure(self):
        """Calibration result should have all documented keys."""
        from praxis.core.calibration import CalibrationAnalyzer

        sid = _create_session("coc")
        _create_constraint_event(sid, "financial", "auto_approved", 0.5)

        analyzer = CalibrationAnalyzer()
        result = analyzer.analyze("coc")

        expected_keys = {
            "domain",
            "total_evaluations",
            "total_sessions",
            "dimensions",
            "boundary_pressure",
            "false_positive_rate",
            "false_negative_estimate",
            "recommendations",
        }
        assert expected_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# Handler test
# ---------------------------------------------------------------------------


class TestCalibrationHandler:
    """Tests for the calibration_handler function."""

    def test_calibration_handler_returns_report(self):
        """calibration_handler should return a valid calibration report."""
        from praxis.api.handlers import calibration_handler

        _create_session("coc")
        result = calibration_handler(domain="coc")

        assert "error" not in result
        assert result["domain"] == "coc"
        assert "recommendations" in result

    def test_calibration_handler_nonexistent_domain(self):
        """calibration_handler for unknown domain returns empty results."""
        from praxis.api.handlers import calibration_handler

        result = calibration_handler(domain="nonexistent")

        assert "error" not in result
        assert result["total_evaluations"] == 0
