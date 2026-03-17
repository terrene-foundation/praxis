# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Bainbridge's Irony detection — approval fatigue and practitioner capability tracking.

Bainbridge's Irony of Automation (1983): the more reliable an automated system,
the less attention its human supervisors pay to it. In CO, this manifests as
approval fatigue — practitioners rubber-stamping held actions without genuine
review — and skill atrophy — practitioners losing the ability to make good
decisions because the system handles everything.

This module provides two classes:

- FatigueDetector: detects approval fatigue patterns from HeldAction metrics
- CapabilityTracker: tracks practitioner skill indicators from deliberation data
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Risk levels for fatigue assessment
# ---------------------------------------------------------------------------


class FatigueRisk(str, Enum):
    """Risk levels for approval fatigue.

    HIGH: practitioner is almost certainly rubber-stamping approvals.
    MEDIUM: warning signs of reduced attention.
    LOW: practitioner appears to be reviewing held actions carefully.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Threshold for "fast" approvals (seconds).
# An approval resolved in under this many seconds likely was not reviewed.
FAST_APPROVAL_THRESHOLD_SECONDS = 5.0

# High risk: >95% approval rate AND <5s avg review time
HIGH_RISK_APPROVAL_RATE = 0.95
HIGH_RISK_AVG_REVIEW_SECONDS = 5.0

# Medium risk: >90% approval rate OR <10s avg review time
MEDIUM_RISK_APPROVAL_RATE = 0.90
MEDIUM_RISK_AVG_REVIEW_SECONDS = 10.0


# ---------------------------------------------------------------------------
# FatigueDetector
# ---------------------------------------------------------------------------


class FatigueDetector:
    """Detects approval fatigue patterns from HeldAction resolution data.

    Tracks per-practitioner metrics:
    - approval_rate: fraction of held actions approved (vs denied)
    - average_review_time_seconds: mean time between creation and resolution
    - fast_approval_rate: fraction of approvals resolved in < 5 seconds

    Risk levels:
    - HIGH: approval_rate > 95% AND average_review_time < 5s
    - MEDIUM: approval_rate > 90% OR average_review_time < 10s
    - LOW: otherwise
    """

    def assess(self, session_id: str) -> dict[str, Any]:
        """Assess approval fatigue risk for a session.

        Reads all resolved HeldAction records for the session from the
        database and computes fatigue metrics.

        Args:
            session_id: The session to assess.

        Returns:
            Dict with keys:
                - risk_level: "high", "medium", or "low"
                - approval_rate: float (0.0-1.0)
                - average_review_time_seconds: float
                - fast_approval_rate: float (0.0-1.0)
                - total_resolved: int
                - total_approved: int
                - total_denied: int
                - details: human-readable explanation
        """
        from praxis.persistence.db_ops import db_list

        # Fetch all resolved held actions for this session
        records = db_list(
            "HeldAction",
            filter={"session_id": session_id, "resolved": True},
            limit=10000,
        )

        total_resolved = len(records)

        if total_resolved == 0:
            return {
                "risk_level": FatigueRisk.LOW.value,
                "approval_rate": 0.0,
                "average_review_time_seconds": 0.0,
                "fast_approval_rate": 0.0,
                "total_resolved": 0,
                "total_approved": 0,
                "total_denied": 0,
                "details": "No resolved held actions to assess.",
            }

        total_approved = sum(1 for r in records if r.get("resolution") == "approved")
        total_denied = total_resolved - total_approved

        approval_rate = total_approved / total_resolved if total_resolved > 0 else 0.0

        # Calculate review times
        review_times = self._compute_review_times(records)
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0.0

        # Fast approval rate: approvals resolved in < 5 seconds
        fast_approvals = sum(
            1
            for r, t in zip(records, review_times)
            if r.get("resolution") == "approved" and t < FAST_APPROVAL_THRESHOLD_SECONDS
        )
        fast_approval_rate = fast_approvals / total_approved if total_approved > 0 else 0.0

        # Determine risk level
        risk_level = self._classify_risk(approval_rate, avg_review_time, fast_approval_rate)

        details = self._build_details(
            risk_level, approval_rate, avg_review_time, fast_approval_rate
        )

        return {
            "risk_level": risk_level.value,
            "approval_rate": round(approval_rate, 4),
            "average_review_time_seconds": round(avg_review_time, 2),
            "fast_approval_rate": round(fast_approval_rate, 4),
            "total_resolved": total_resolved,
            "total_approved": total_approved,
            "total_denied": total_denied,
            "details": details,
        }

    def _compute_review_times(self, records: list[dict]) -> list[float]:
        """Compute review duration in seconds for each resolved record.

        Falls back to 0.0 for records with unparseable timestamps.
        """
        times: list[float] = []
        for r in records:
            created = r.get("created_at", "")
            resolved = r.get("resolved_at", "")
            if created and resolved:
                try:
                    t_created = _parse_iso(created)
                    t_resolved = _parse_iso(resolved)
                    delta = (t_resolved - t_created).total_seconds()
                    times.append(max(delta, 0.0))
                except (ValueError, TypeError):
                    times.append(0.0)
            else:
                times.append(0.0)
        return times

    def _classify_risk(
        self,
        approval_rate: float,
        avg_review_time: float,
        fast_approval_rate: float,
    ) -> FatigueRisk:
        """Classify fatigue risk based on metrics.

        HIGH: approval_rate > 95% AND avg_review_time < 5s
        MEDIUM: approval_rate > 90% OR avg_review_time < 10s
        LOW: otherwise
        """
        if (
            approval_rate > HIGH_RISK_APPROVAL_RATE
            and avg_review_time < HIGH_RISK_AVG_REVIEW_SECONDS
        ):
            return FatigueRisk.HIGH

        if (
            approval_rate > MEDIUM_RISK_APPROVAL_RATE
            or avg_review_time < MEDIUM_RISK_AVG_REVIEW_SECONDS
        ):
            return FatigueRisk.MEDIUM

        return FatigueRisk.LOW

    def _build_details(
        self,
        risk: FatigueRisk,
        approval_rate: float,
        avg_review_time: float,
        fast_approval_rate: float,
    ) -> str:
        """Build a human-readable explanation of the fatigue assessment."""
        if risk == FatigueRisk.HIGH:
            return (
                f"High approval fatigue risk: {approval_rate:.0%} approval rate "
                f"with {avg_review_time:.1f}s average review time. "
                f"{fast_approval_rate:.0%} of approvals were under "
                f"{FAST_APPROVAL_THRESHOLD_SECONDS}s. "
                f"Practitioner may be rubber-stamping held actions."
            )
        if risk == FatigueRisk.MEDIUM:
            parts = []
            if approval_rate > MEDIUM_RISK_APPROVAL_RATE:
                parts.append(f"approval rate is {approval_rate:.0%} (>90%)")
            if avg_review_time < MEDIUM_RISK_AVG_REVIEW_SECONDS:
                parts.append(f"average review time is {avg_review_time:.1f}s (<10s)")
            return (
                f"Medium approval fatigue risk: {'; '.join(parts)}. "
                f"Consider reviewing constraint calibration."
            )
        return (
            f"Low approval fatigue risk: {approval_rate:.0%} approval rate "
            f"with {avg_review_time:.1f}s average review time. "
            f"Practitioner appears to be reviewing held actions carefully."
        )


# ---------------------------------------------------------------------------
# CapabilityTracker
# ---------------------------------------------------------------------------


class CapabilityTracker:
    """Tracks practitioner capability indicators from deliberation and constraint data.

    Monitors five metrics:
    1. reasoning_depth: average word count in decision rationales
    2. alternatives_considered: fraction of decisions with alternatives listed
    3. confidence_calibration: how accurately self-assessed confidence matches outcomes
    4. escalation_appropriateness: ratio of escalations to total decisions
    5. temporal_engagement: average time between decisions (seconds)
    """

    def assess_capability(
        self,
        practitioner_id: str,
        domain: str,
    ) -> dict[str, Any]:
        """Assess a practitioner's capability across five metrics.

        Args:
            practitioner_id: The actor identifier (e.g. "human", "alice").
            domain: CO domain to scope the assessment.

        Returns:
            Dict with keys:
                - practitioner_id: str
                - domain: str
                - reasoning_depth: float (avg word count)
                - alternatives_considered: float (0.0-1.0 fraction)
                - confidence_calibration: float (0.0-1.0)
                - escalation_appropriateness: float (ratio)
                - temporal_engagement: float (avg seconds between decisions)
                - overall_score: float (0.0-1.0 composite)
                - details: human-readable summary
        """
        from praxis.persistence.db_ops import db_list

        # Get all deliberation records for this practitioner in sessions of this domain
        # First, find session IDs for the domain
        sessions = db_list("Session", filter={"domain": domain}, limit=10000)
        session_ids = {s["id"] for s in sessions}

        if not session_ids:
            return self._empty_result(practitioner_id, domain)

        # Get all deliberation records by this actor across domain sessions
        all_records: list[dict] = []
        for sid in session_ids:
            records = db_list(
                "DeliberationRecord",
                filter={"session_id": sid, "actor": practitioner_id},
                limit=10000,
                order_asc=True,
            )
            all_records.extend(records)

        if not all_records:
            return self._empty_result(practitioner_id, domain)

        # Separate by type
        decisions = [r for r in all_records if r.get("record_type") == "decision"]
        escalations = [r for r in all_records if r.get("record_type") == "escalation"]

        # 1. Reasoning depth: average word count in rationales
        reasoning_depth = self._compute_reasoning_depth(decisions)

        # 2. Alternatives considered: fraction of decisions with alternatives
        alternatives_considered = self._compute_alternatives_rate(decisions)

        # 3. Confidence calibration
        confidence_calibration = self._compute_confidence_calibration(decisions)

        # 4. Escalation appropriateness
        total_decisions = len(decisions)
        total_escalations = len(escalations)
        escalation_appropriateness = (
            total_escalations / (total_decisions + total_escalations)
            if (total_decisions + total_escalations) > 0
            else 0.0
        )

        # 5. Temporal engagement: average seconds between decisions
        temporal_engagement = self._compute_temporal_engagement(decisions)

        # Composite score (simple normalized average)
        overall_score = self._compute_overall_score(
            reasoning_depth,
            alternatives_considered,
            confidence_calibration,
            escalation_appropriateness,
            temporal_engagement,
        )

        return {
            "practitioner_id": practitioner_id,
            "domain": domain,
            "reasoning_depth": round(reasoning_depth, 2),
            "alternatives_considered": round(alternatives_considered, 4),
            "confidence_calibration": round(confidence_calibration, 4),
            "escalation_appropriateness": round(escalation_appropriateness, 4),
            "temporal_engagement": round(temporal_engagement, 2),
            "overall_score": round(overall_score, 4),
            "total_decisions": total_decisions,
            "total_escalations": total_escalations,
            "details": self._build_capability_details(
                reasoning_depth,
                alternatives_considered,
                confidence_calibration,
                escalation_appropriateness,
                temporal_engagement,
                overall_score,
            ),
        }

    def _compute_reasoning_depth(self, decisions: list[dict]) -> float:
        """Average word count of rationales across decisions."""
        word_counts: list[int] = []
        for d in decisions:
            trace = d.get("reasoning_trace") or {}
            if isinstance(trace, str):
                import json

                try:
                    trace = json.loads(trace)
                except (json.JSONDecodeError, TypeError):
                    trace = {}
            rationale = trace.get("rationale", "")
            if rationale:
                word_counts.append(len(rationale.split()))

        return sum(word_counts) / len(word_counts) if word_counts else 0.0

    def _compute_alternatives_rate(self, decisions: list[dict]) -> float:
        """Fraction of decisions that include alternatives."""
        if not decisions:
            return 0.0
        with_alts = 0
        for d in decisions:
            content = d.get("content") or {}
            if isinstance(content, str):
                import json

                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    content = {}
            alternatives = content.get("alternatives", [])
            if alternatives:
                with_alts += 1
        return with_alts / len(decisions)

    def _compute_confidence_calibration(self, decisions: list[dict]) -> float:
        """How well self-assessed confidence distributes.

        Good calibration means the practitioner uses a range of confidence
        values. If every decision is confidence=1.0, that suggests poor
        self-awareness. We measure the standard deviation of confidence
        values and normalize it.

        Returns a value between 0.0 and 1.0, where higher is better.
        """
        confidences: list[float] = []
        for d in decisions:
            conf = d.get("confidence")
            if conf is not None:
                try:
                    confidences.append(float(conf))
                except (ValueError, TypeError):
                    pass

        if len(confidences) < 2:
            # Not enough data to assess calibration
            return 0.5

        mean = sum(confidences) / len(confidences)
        variance = sum((c - mean) ** 2 for c in confidences) / len(confidences)
        std_dev = variance**0.5

        # Max possible std_dev for values in [0, 1] is 0.5
        # Higher spread indicates better calibration (not always saying 1.0)
        calibration = min(std_dev / 0.5, 1.0)
        return calibration

    def _compute_temporal_engagement(self, decisions: list[dict]) -> float:
        """Average seconds between consecutive decisions."""
        if len(decisions) < 2:
            return 0.0

        timestamps: list[datetime] = []
        for d in decisions:
            created = d.get("created_at", "")
            if created:
                try:
                    timestamps.append(_parse_iso(created))
                except (ValueError, TypeError):
                    pass

        if len(timestamps) < 2:
            return 0.0

        timestamps.sort()
        gaps = [
            (timestamps[i + 1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)
        ]
        return sum(gaps) / len(gaps) if gaps else 0.0

    def _compute_overall_score(
        self,
        reasoning_depth: float,
        alternatives_considered: float,
        confidence_calibration: float,
        escalation_appropriateness: float,
        temporal_engagement: float,
    ) -> float:
        """Compute a composite capability score (0.0-1.0).

        Normalizes each metric to [0, 1] then averages.
        """
        # reasoning_depth: normalize assuming 50 words is excellent
        rd_score = min(reasoning_depth / 50.0, 1.0)

        # alternatives_considered: already 0-1
        ac_score = alternatives_considered

        # confidence_calibration: already 0-1
        cc_score = confidence_calibration

        # escalation_appropriateness: ideal is some but not too many
        # 5-15% is ideal range; we score highest at ~10%
        if escalation_appropriateness <= 0:
            ea_score = 0.3  # Never escalating is not great
        elif escalation_appropriateness <= 0.15:
            ea_score = min(escalation_appropriateness / 0.10, 1.0)
        else:
            # Too many escalations — diminishing returns
            ea_score = max(0.0, 1.0 - (escalation_appropriateness - 0.15) * 5)

        # temporal_engagement: 30-300 seconds between decisions is ideal
        if temporal_engagement <= 0:
            te_score = 0.0
        elif temporal_engagement < 30:
            te_score = temporal_engagement / 30.0  # Too fast
        elif temporal_engagement <= 300:
            te_score = 1.0  # Sweet spot
        else:
            # Diminishing but still okay up to 1800s (30 min)
            te_score = max(0.0, 1.0 - (temporal_engagement - 300) / 1500)

        return (rd_score + ac_score + cc_score + ea_score + te_score) / 5.0

    def _build_capability_details(
        self,
        reasoning_depth: float,
        alternatives_considered: float,
        confidence_calibration: float,
        escalation_appropriateness: float,
        temporal_engagement: float,
        overall_score: float,
    ) -> str:
        """Build a human-readable capability summary."""
        parts = [
            f"Reasoning depth: {reasoning_depth:.1f} words/rationale",
            f"Alternatives considered: {alternatives_considered:.0%} of decisions",
            f"Confidence calibration: {confidence_calibration:.0%}",
            f"Escalation rate: {escalation_appropriateness:.0%}",
            f"Avg time between decisions: {temporal_engagement:.0f}s",
        ]
        return f"Overall capability score: {overall_score:.0%}. " + "; ".join(parts)

    def _empty_result(self, practitioner_id: str, domain: str) -> dict[str, Any]:
        """Return a zero-data capability result."""
        return {
            "practitioner_id": practitioner_id,
            "domain": domain,
            "reasoning_depth": 0.0,
            "alternatives_considered": 0.0,
            "confidence_calibration": 0.5,
            "escalation_appropriateness": 0.0,
            "temporal_engagement": 0.0,
            "overall_score": 0.0,
            "total_decisions": 0,
            "total_escalations": 0,
            "details": "No deliberation data available for this practitioner in this domain.",
        }


# ---------------------------------------------------------------------------
# Constraint review reminders (M11-03)
# ---------------------------------------------------------------------------


class ConstraintReviewTracker:
    """Tracks when constraint dimensions were last reviewed and flags review-due dimensions.

    Each constraint dimension has a ``last_reviewed`` timestamp and a
    ``sessions_since_review`` counter stored in session_metadata.

    Default review interval: 30 sessions.
    Unused constraint detection: dimensions never triggered in N sessions
    are flagged as "potentially unnecessary".
    """

    DEFAULT_REVIEW_INTERVAL_SESSIONS = 30
    UNUSED_THRESHOLD_SESSIONS = 30

    def __init__(self, review_interval: int | None = None) -> None:
        self.review_interval = (
            review_interval
            if review_interval is not None
            else self.DEFAULT_REVIEW_INTERVAL_SESSIONS
        )

    def get_review_status(self, session_id: str) -> dict[str, Any]:
        """Get constraint review status for a session.

        Returns which dimensions need review and which may be unnecessary.

        Args:
            session_id: The session to check.

        Returns:
            Dict with keys:
                - review_due: list of dimension names needing review
                - potentially_unnecessary: list of dimensions never triggered
                - dimension_status: per-dimension detail dict
        """
        from praxis.persistence.db_ops import db_list, db_read

        # Load session metadata to get review tracking
        session = db_read("Session", session_id)
        if session is None:
            return {
                "review_due": [],
                "potentially_unnecessary": [],
                "dimension_status": {},
            }

        metadata = session.get("session_metadata") or {}
        if isinstance(metadata, str):
            import json

            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        constraint_reviews = metadata.get("constraint_reviews", {})

        # Count total sessions for this workspace/domain to determine staleness
        domain = session.get("domain", "coc")
        workspace_id = session.get("workspace_id", "")
        all_sessions = db_list(
            "Session",
            filter={"workspace_id": workspace_id, "domain": domain},
            limit=10000,
        )
        total_sessions = len(all_sessions)

        # Get constraint events for this session to find triggered dimensions
        events = db_list(
            "ConstraintEvent",
            filter={"session_id": session_id},
            limit=10000,
        )
        triggered_dimensions = {e.get("dimension") for e in events if e.get("dimension")}

        dimensions = [
            "financial",
            "operational",
            "temporal",
            "data_access",
            "communication",
        ]

        review_due: list[str] = []
        potentially_unnecessary: list[str] = []
        dimension_status: dict[str, dict] = {}

        for dim in dimensions:
            dim_review = constraint_reviews.get(dim, {})
            last_reviewed_session = dim_review.get("last_reviewed_session", 0)
            sessions_since = total_sessions - last_reviewed_session

            needs_review = sessions_since >= self.review_interval
            never_triggered = dim not in triggered_dimensions

            if needs_review:
                review_due.append(dim)

            if never_triggered and total_sessions >= self.UNUSED_THRESHOLD_SESSIONS:
                potentially_unnecessary.append(dim)

            dimension_status[dim] = {
                "last_reviewed_session": last_reviewed_session,
                "sessions_since_review": sessions_since,
                "needs_review": needs_review,
                "triggered_in_session": dim in triggered_dimensions,
                "potentially_unnecessary": (
                    never_triggered and total_sessions >= self.UNUSED_THRESHOLD_SESSIONS
                ),
            }

        return {
            "review_due": review_due,
            "potentially_unnecessary": potentially_unnecessary,
            "dimension_status": dimension_status,
            "total_sessions": total_sessions,
        }

    def mark_reviewed(self, session_id: str, dimension: str) -> None:
        """Mark a constraint dimension as reviewed.

        Updates session_metadata with the current session count as the
        last reviewed marker.

        Args:
            session_id: The session.
            dimension: The constraint dimension that was reviewed.
        """
        from praxis.persistence.db_ops import db_list, db_read, db_update

        session = db_read("Session", session_id)
        if session is None:
            return

        metadata = session.get("session_metadata") or {}
        if isinstance(metadata, str):
            import json

            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        constraint_reviews = metadata.get("constraint_reviews", {})

        # Count total sessions for the domain/workspace
        domain = session.get("domain", "coc")
        workspace_id = session.get("workspace_id", "")
        all_sessions = db_list(
            "Session",
            filter={"workspace_id": workspace_id, "domain": domain},
            limit=10000,
        )

        constraint_reviews[dimension] = {
            "last_reviewed_session": len(all_sessions),
            "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        metadata["constraint_reviews"] = constraint_reviews
        db_update("Session", session_id, {"session_metadata": metadata})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp string to a timezone-aware datetime.

    Handles the Z-suffix format used throughout Praxis.
    """
    # Replace Z with +00:00 for Python's fromisoformat
    normalized = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)
