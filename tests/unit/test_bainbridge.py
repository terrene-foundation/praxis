# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Tests for Bainbridge's Irony detection — approval fatigue, capability tracking,
constraint review reminders, and mandatory constraint rationale.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso(offset_seconds: float = 0.0) -> str:
    """Return an ISO 8601 timestamp with an optional offset."""
    ts = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


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


def _create_held_action(
    session_id: str,
    resolution: str = "approved",
    review_seconds: float = 2.0,
) -> str:
    """Create a resolved held action with specified review time."""
    from praxis.persistence.db_ops import db_create

    held_id = str(uuid.uuid4())
    created = _now_iso(-review_seconds)
    resolved = _now_iso()

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
            "resolved": True,
            "resolution": resolution,
            "resolved_by": "test-user",
            "resolved_at": resolved,
            "created_at": created,
        },
    )
    return held_id


# ---------------------------------------------------------------------------
# M11-01: FatigueDetector tests
# ---------------------------------------------------------------------------


class TestFatigueDetector:
    """Tests for the FatigueDetector class."""

    def test_no_held_actions_returns_low_risk(self):
        """With no resolved held actions, risk should be LOW."""
        from praxis.core.bainbridge import FatigueDetector

        sid = _create_session()
        detector = FatigueDetector()
        result = detector.assess(sid)

        assert result["risk_level"] == "low"
        assert result["total_resolved"] == 0

    def test_high_risk_rubber_stamping(self):
        """High approval rate with fast reviews = HIGH risk."""
        from praxis.core.bainbridge import FatigueDetector

        sid = _create_session()

        # Create 20 fast approvals (< 5s review time)
        for _ in range(20):
            _create_held_action(sid, resolution="approved", review_seconds=2.0)

        detector = FatigueDetector()
        result = detector.assess(sid)

        assert result["risk_level"] == "high"
        assert result["approval_rate"] == 1.0
        assert result["total_approved"] == 20
        assert result["total_denied"] == 0
        assert result["fast_approval_rate"] == 1.0

    def test_medium_risk_high_approval_rate(self):
        """>90% approval rate but slow reviews = MEDIUM risk."""
        from praxis.core.bainbridge import FatigueDetector

        sid = _create_session()

        # 19 approvals, 1 denial, all with >10s review time
        for _ in range(19):
            _create_held_action(sid, resolution="approved", review_seconds=30.0)
        _create_held_action(sid, resolution="denied", review_seconds=30.0)

        detector = FatigueDetector()
        result = detector.assess(sid)

        assert result["risk_level"] == "medium"
        assert result["approval_rate"] == 0.95
        assert result["total_resolved"] == 20

    def test_medium_risk_fast_reviews(self):
        """Fast review time with moderate approval rate = MEDIUM risk."""
        from praxis.core.bainbridge import FatigueDetector

        sid = _create_session()

        # 8 approvals, 4 denials, all with <10s review time
        for _ in range(8):
            _create_held_action(sid, resolution="approved", review_seconds=5.0)
        for _ in range(4):
            _create_held_action(sid, resolution="denied", review_seconds=5.0)

        detector = FatigueDetector()
        result = detector.assess(sid)

        # 66% approval rate, <10s avg review -> medium due to fast reviews
        assert result["risk_level"] == "medium"

    def test_low_risk_careful_reviews(self):
        """Moderate approval rate with slow reviews = LOW risk."""
        from praxis.core.bainbridge import FatigueDetector

        sid = _create_session()

        # 6 approvals, 4 denials, all with >10s review time
        for _ in range(6):
            _create_held_action(sid, resolution="approved", review_seconds=30.0)
        for _ in range(4):
            _create_held_action(sid, resolution="denied", review_seconds=30.0)

        detector = FatigueDetector()
        result = detector.assess(sid)

        assert result["risk_level"] == "low"
        assert result["approval_rate"] == 0.6
        assert result["total_resolved"] == 10

    def test_assess_returns_expected_keys(self):
        """Assessment result should have all documented keys."""
        from praxis.core.bainbridge import FatigueDetector

        sid = _create_session()
        _create_held_action(sid, resolution="approved", review_seconds=10.0)

        detector = FatigueDetector()
        result = detector.assess(sid)

        expected_keys = {
            "risk_level",
            "approval_rate",
            "average_review_time_seconds",
            "fast_approval_rate",
            "total_resolved",
            "total_approved",
            "total_denied",
            "details",
        }
        assert expected_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# M11-02: Mandatory constraint rationale tests
# ---------------------------------------------------------------------------


class TestMandatoryConstraintRationale:
    """Tests for the mandatory rationale requirement on constraint updates."""

    def test_update_without_rationale_fails(self):
        """Updating constraints without a rationale should return an error."""
        from praxis.api.handlers import update_constraints_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="test-ws",
            domain="coc",
            constraint_template="moderate",
        )
        sid = session["session_id"]

        # Tighten financial
        new_constraints = dict(session["constraint_envelope"])
        new_constraints["financial"] = {"max_spend": 50.0, "current_spend": 0.0}

        result = update_constraints_handler(
            session_manager=mgr,
            session_id=sid,
            new_constraints=new_constraints,
            rationale="",
        )

        assert "error" in result

    def test_update_with_rationale_succeeds(self):
        """Updating constraints with a rationale should succeed."""
        from praxis.api.handlers import update_constraints_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="test-ws",
            domain="coc",
            constraint_template="moderate",
        )
        sid = session["session_id"]

        # Tighten financial
        new_constraints = dict(session["constraint_envelope"])
        new_constraints["financial"] = {"max_spend": 50.0, "current_spend": 0.0}

        result = update_constraints_handler(
            session_manager=mgr,
            session_id=sid,
            new_constraints=new_constraints,
            rationale="Reducing budget for prototype phase",
        )

        assert "error" not in result
        assert result["constraint_envelope"]["financial"]["max_spend"] == 50.0

    def test_rationale_stored_as_observation(self):
        """Constraint update rationale should be stored as a deliberation observation."""
        from praxis.api.handlers import update_constraints_handler
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="test-ws",
            domain="coc",
            constraint_template="moderate",
        )
        sid = session["session_id"]

        new_constraints = dict(session["constraint_envelope"])
        new_constraints["financial"] = {"max_spend": 50.0, "current_spend": 0.0}

        update_constraints_handler(
            session_manager=mgr,
            session_id=sid,
            new_constraints=new_constraints,
            rationale="Reducing budget for security audit",
        )

        # Check deliberation records for the observation
        engine = DeliberationEngine(session_id=sid)
        records, total = engine.get_timeline(record_type="observation")

        assert total >= 1
        found = any(
            "Reducing budget for security audit" in str(r.get("content", "")) for r in records
        )
        assert found, "Rationale observation not found in deliberation timeline"


# ---------------------------------------------------------------------------
# M11-03: Constraint review reminders tests
# ---------------------------------------------------------------------------


class TestConstraintReviewTracker:
    """Tests for the ConstraintReviewTracker class."""

    def test_new_session_all_review_due(self):
        """A brand new session should show all dimensions as review-due
        when there are enough sessions."""
        from praxis.core.bainbridge import ConstraintReviewTracker

        # Create many sessions to exceed the threshold
        sids = []
        for _ in range(31):
            sids.append(_create_session())

        tracker = ConstraintReviewTracker(review_interval=30)
        result = tracker.get_review_status(sids[-1])

        # With 31 sessions and no reviews, all should be due
        assert len(result["review_due"]) == 5

    def test_mark_reviewed_clears_flag(self):
        """Marking a dimension as reviewed should clear its review-due flag."""
        from praxis.core.bainbridge import ConstraintReviewTracker

        sids = []
        for _ in range(31):
            sids.append(_create_session())

        tracker = ConstraintReviewTracker(review_interval=30)

        # Mark financial as reviewed
        tracker.mark_reviewed(sids[-1], "financial")

        result = tracker.get_review_status(sids[-1])

        # Financial should NOT be in review_due, but others should be
        assert "financial" not in result["review_due"]

    def test_low_session_count_no_review_due(self):
        """With few sessions, nothing should be flagged as review due."""
        from praxis.core.bainbridge import ConstraintReviewTracker

        sid = _create_session()
        tracker = ConstraintReviewTracker(review_interval=30)
        result = tracker.get_review_status(sid)

        # Only 1 session, interval is 30 -> no reviews due
        assert len(result["review_due"]) == 0

    def test_review_status_returns_expected_keys(self):
        """Review status should have documented structure."""
        from praxis.core.bainbridge import ConstraintReviewTracker

        sid = _create_session()
        tracker = ConstraintReviewTracker()
        result = tracker.get_review_status(sid)

        assert "review_due" in result
        assert "potentially_unnecessary" in result
        assert "dimension_status" in result


# ---------------------------------------------------------------------------
# M11-05: CapabilityTracker tests
# ---------------------------------------------------------------------------


class TestCapabilityTracker:
    """Tests for the CapabilityTracker class."""

    def test_no_data_returns_empty(self):
        """With no deliberation data, returns zero scores."""
        from praxis.core.bainbridge import CapabilityTracker

        _create_session()  # Ensure DB is populated
        tracker = CapabilityTracker()
        result = tracker.assess_capability("nonexistent-actor", "coc")

        assert result["practitioner_id"] == "nonexistent-actor"
        assert result["total_decisions"] == 0
        assert result["overall_score"] == 0.0

    def test_capability_with_decisions(self):
        """With deliberation data, returns meaningful scores."""
        from praxis.core.bainbridge import CapabilityTracker
        from praxis.core.deliberation import DeliberationEngine

        sid = _create_session()
        engine = DeliberationEngine(session_id=sid)

        # Record several decisions with varying rationales and confidence
        engine.record_decision(
            decision="Use React for frontend",
            rationale="React has strong community support and our team has experience with it. "
            "The component model fits our architecture well and will allow rapid iteration.",
            actor="alice",
            alternatives=["Vue.js", "Svelte"],
            confidence=0.8,
        )
        engine.record_decision(
            decision="PostgreSQL for database",
            rationale="Strong ACID compliance needed for financial data integrity.",
            actor="alice",
            alternatives=["MySQL"],
            confidence=0.9,
        )
        engine.record_decision(
            decision="Deploy to AWS",
            rationale="Existing infrastructure and team familiarity.",
            actor="alice",
            confidence=0.7,
        )

        # Record an escalation
        engine.record_escalation(
            issue="Security audit needed",
            context="Third-party library has known CVE",
            actor="alice",
        )

        tracker = CapabilityTracker()
        result = tracker.assess_capability("alice", "coc")

        assert result["practitioner_id"] == "alice"
        assert result["total_decisions"] == 3
        assert result["total_escalations"] == 1
        assert result["reasoning_depth"] > 0
        assert result["alternatives_considered"] > 0  # 2 out of 3 have alternatives
        assert 0.0 <= result["overall_score"] <= 1.0

    def test_capability_result_keys(self):
        """Capability result should have all documented keys."""
        from praxis.core.bainbridge import CapabilityTracker

        _create_session()
        tracker = CapabilityTracker()
        result = tracker.assess_capability("human", "coc")

        expected_keys = {
            "practitioner_id",
            "domain",
            "reasoning_depth",
            "alternatives_considered",
            "confidence_calibration",
            "escalation_appropriateness",
            "temporal_engagement",
            "overall_score",
            "total_decisions",
            "total_escalations",
            "details",
        }
        assert expected_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# Handler tests
# ---------------------------------------------------------------------------


class TestBainbridgeHandlers:
    """Tests for the Bainbridge handler functions."""

    def test_fatigue_handler(self):
        """fatigue_handler should return a valid assessment."""
        from praxis.api.handlers import fatigue_handler

        sid = _create_session()
        result = fatigue_handler(session_id=sid)

        assert "error" not in result
        assert result["risk_level"] == "low"

    def test_capability_handler(self):
        """capability_handler should return a valid assessment."""
        from praxis.api.handlers import capability_handler

        _create_session()
        result = capability_handler(practitioner_id="human", domain="coc")

        assert "error" not in result
        assert "practitioner_id" in result

    def test_constraint_review_handler(self):
        """constraint_review_handler should return review status."""
        from praxis.api.handlers import constraint_review_handler

        sid = _create_session()
        result = constraint_review_handler(session_id=sid)

        assert "error" not in result
        assert "review_due" in result
        assert "dimension_status" in result
