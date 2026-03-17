# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Automated session audit reviewer.

Runs after a session ends (or on demand) to evaluate the quality of the
session's deliberation trail. Checks for temporal consistency, decision
density, approval review time, and chain integrity. Produces a quality
score from 0 to 100 that can be stored in session metadata.

This is a defense-in-depth mechanism: even if individual records pass
validation, the aggregate session patterns may reveal quality concerns.

Checks:
    temporal_consistency  - No unexplained timestamp gaps
    decision_density      - Plausible number of decisions for session length
    approval_review_time  - Flag very fast approvals (rubber-stamping)
    chain_integrity       - Deliberation hash chain is unbroken
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Default thresholds
DEFAULT_MAX_GAP_MINUTES = 60  # Flag gaps > 60 minutes
DEFAULT_MIN_REVIEW_SECONDS = 5  # Approvals faster than 5s are suspicious
DEFAULT_MAX_DECISIONS_PER_HOUR = 60  # More than 60 decisions/hour is suspicious
DEFAULT_MIN_DECISIONS_PER_HOUR = 0.1  # Less than ~1 decision per 10h is unusual


@dataclass
class AuditFinding:
    """A single finding from the audit review.

    Attributes:
        check: Name of the check that produced this finding.
        severity: "critical", "warning", or "info".
        message: Human-readable description of the finding.
        details: Optional dict with additional structured data.
    """

    check: str
    severity: str
    message: str
    details: dict[str, Any] | None = None


@dataclass
class QualityReport:
    """Aggregate quality report for a session.

    Attributes:
        session_id: The session this report covers.
        score: Quality score from 0 to 100.
        findings: List of AuditFinding instances.
        summary: Brief human-readable summary.
        checked_at: ISO 8601 timestamp of when the review was run.
    """

    session_id: str
    score: int
    findings: list[AuditFinding] = field(default_factory=list)
    summary: str = ""
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict suitable for storage in session_metadata."""
        return {
            "session_id": self.session_id,
            "score": self.score,
            "findings": [
                {
                    "check": f.check,
                    "severity": f.severity,
                    "message": f.message,
                    "details": f.details,
                }
                for f in self.findings
            ],
            "summary": self.summary,
            "checked_at": self.checked_at,
        }


class SessionAuditReviewer:
    """Automated quality reviewer for completed CO sessions.

    Evaluates the session's deliberation records for quality indicators
    and produces a QualityReport with a score and findings.

    Args:
        max_gap_minutes: Maximum acceptable gap between records (minutes).
        min_review_seconds: Minimum acceptable approval review time (seconds).
        max_decisions_per_hour: Maximum plausible decisions per hour.
        min_decisions_per_hour: Minimum expected decisions per hour.
    """

    def __init__(
        self,
        max_gap_minutes: float = DEFAULT_MAX_GAP_MINUTES,
        min_review_seconds: float = DEFAULT_MIN_REVIEW_SECONDS,
        max_decisions_per_hour: float = DEFAULT_MAX_DECISIONS_PER_HOUR,
        min_decisions_per_hour: float = DEFAULT_MIN_DECISIONS_PER_HOUR,
    ) -> None:
        self.max_gap_minutes = max_gap_minutes
        self.min_review_seconds = min_review_seconds
        self.max_decisions_per_hour = max_decisions_per_hour
        self.min_decisions_per_hour = min_decisions_per_hour

    def review_session(
        self,
        session: dict,
        records: list[dict],
        held_actions: list[dict] | None = None,
    ) -> QualityReport:
        """Run all audit checks on a session and produce a quality report.

        Args:
            session: The session dict (from SessionManager.get_session).
            records: List of deliberation record dicts (chronological order).
            held_actions: Optional list of held action dicts for approval
                review time analysis.

        Returns:
            A QualityReport with score and findings.
        """
        findings: list[AuditFinding] = []

        # Run all checks
        findings.extend(self._check_temporal_consistency(records))
        findings.extend(self._check_decision_density(session, records))
        findings.extend(self._check_approval_review_time(held_actions or []))
        findings.extend(self._check_chain_integrity(records))

        # Calculate score
        score = self._calculate_score(findings)

        # Build summary
        critical_count = sum(1 for f in findings if f.severity == "critical")
        warning_count = sum(1 for f in findings if f.severity == "warning")
        info_count = sum(1 for f in findings if f.severity == "info")

        if critical_count > 0:
            summary = (
                f"Session has {critical_count} critical finding(s). " f"Quality score: {score}/100."
            )
        elif warning_count > 0:
            summary = f"Session has {warning_count} warning(s). " f"Quality score: {score}/100."
        elif info_count > 0:
            summary = f"Session passed with {info_count} informational note(s). Score: {score}/100."
        else:
            summary = f"Session passed all audit checks. Score: {score}/100."

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        report = QualityReport(
            session_id=session.get("session_id", "unknown"),
            score=score,
            findings=findings,
            summary=summary,
            checked_at=now,
        )

        logger.info(
            "Audit review for session %s: score=%d, findings=%d",
            session.get("session_id", "unknown"),
            score,
            len(findings),
        )

        return report

    def _check_temporal_consistency(self, records: list[dict]) -> list[AuditFinding]:
        """Check for unexplained timestamp gaps between consecutive records.

        Large gaps may indicate the session was left running without
        activity, or that records were inserted out of order.
        """
        findings: list[AuditFinding] = []

        if len(records) < 2:
            return findings

        timestamps = []
        for r in records:
            ts_str = r.get("created_at", "")
            if not ts_str:
                continue
            try:
                ts = _parse_iso(ts_str)
                timestamps.append(ts)
            except (ValueError, TypeError):
                findings.append(
                    AuditFinding(
                        check="temporal_consistency",
                        severity="warning",
                        message=f"Record has unparseable timestamp: {ts_str}",
                    )
                )

        for i in range(1, len(timestamps)):
            gap_seconds = (timestamps[i] - timestamps[i - 1]).total_seconds()
            gap_minutes = gap_seconds / 60.0

            if gap_minutes > self.max_gap_minutes:
                findings.append(
                    AuditFinding(
                        check="temporal_consistency",
                        severity="warning",
                        message=(
                            f"Gap of {gap_minutes:.1f} minutes between "
                            f"records {i - 1} and {i} "
                            f"(threshold: {self.max_gap_minutes} minutes)"
                        ),
                        details={
                            "gap_minutes": round(gap_minutes, 1),
                            "record_index_before": i - 1,
                            "record_index_after": i,
                        },
                    )
                )

            if gap_seconds < 0:
                findings.append(
                    AuditFinding(
                        check="temporal_consistency",
                        severity="critical",
                        message=(
                            f"Timestamp ordering violation: record {i} is "
                            f"{abs(gap_seconds):.1f}s before record {i - 1}"
                        ),
                        details={
                            "gap_seconds": round(gap_seconds, 1),
                            "record_index_before": i - 1,
                            "record_index_after": i,
                        },
                    )
                )

        return findings

    def _check_decision_density(self, session: dict, records: list[dict]) -> list[AuditFinding]:
        """Check that the number of decisions is plausible for session duration.

        Too many decisions per hour suggests automated rubber-stamping.
        Too few may indicate the session was not productive.
        """
        findings: list[AuditFinding] = []

        decision_records = [r for r in records if r.get("record_type") == "decision"]
        decision_count = len(decision_records)

        if decision_count == 0:
            findings.append(
                AuditFinding(
                    check="decision_density",
                    severity="info",
                    message="Session has no decision records.",
                )
            )
            return findings

        # Estimate session duration
        duration_hours = self._estimate_duration_hours(session, records)

        if duration_hours <= 0:
            return findings

        decisions_per_hour = decision_count / duration_hours

        if decisions_per_hour > self.max_decisions_per_hour:
            findings.append(
                AuditFinding(
                    check="decision_density",
                    severity="warning",
                    message=(
                        f"High decision density: {decisions_per_hour:.1f} "
                        f"decisions/hour (threshold: {self.max_decisions_per_hour}). "
                        f"This may indicate insufficient deliberation time."
                    ),
                    details={
                        "decisions_per_hour": round(decisions_per_hour, 1),
                        "total_decisions": decision_count,
                        "duration_hours": round(duration_hours, 2),
                    },
                )
            )

        if decisions_per_hour < self.min_decisions_per_hour and duration_hours > 1:
            findings.append(
                AuditFinding(
                    check="decision_density",
                    severity="info",
                    message=(
                        f"Low decision density: {decisions_per_hour:.2f} "
                        f"decisions/hour over {duration_hours:.1f} hours."
                    ),
                    details={
                        "decisions_per_hour": round(decisions_per_hour, 2),
                        "total_decisions": decision_count,
                        "duration_hours": round(duration_hours, 2),
                    },
                )
            )

        return findings

    def _check_approval_review_time(self, held_actions: list[dict]) -> list[AuditFinding]:
        """Flag held actions that were approved very quickly (rubber-stamping).

        If a held action was approved in less than the minimum review time,
        it suggests the approver did not actually review the action.
        """
        findings: list[AuditFinding] = []

        resolved_actions = [h for h in held_actions if h.get("resolved")]
        fast_approvals = 0

        for action in resolved_actions:
            if action.get("resolution") != "approved":
                continue

            created_str = action.get("created_at", "")
            resolved_str = action.get("resolved_at", "")

            if not created_str or not resolved_str:
                continue

            try:
                created_ts = _parse_iso(created_str)
                resolved_ts = _parse_iso(resolved_str)
                review_seconds = (resolved_ts - created_ts).total_seconds()

                if review_seconds < self.min_review_seconds:
                    fast_approvals += 1
                    findings.append(
                        AuditFinding(
                            check="approval_review_time",
                            severity="warning",
                            message=(
                                f"Held action approved in {review_seconds:.1f}s "
                                f"(minimum: {self.min_review_seconds}s). "
                                f"Fast approvals may indicate rubber-stamping."
                            ),
                            details={
                                "held_id": action.get("held_id", action.get("id", "")),
                                "review_seconds": round(review_seconds, 1),
                                "action": action.get("action", ""),
                            },
                        )
                    )
            except (ValueError, TypeError):
                continue

        if fast_approvals > 0 and len(resolved_actions) > 0:
            ratio = fast_approvals / len(resolved_actions)
            if ratio > 0.5:
                findings.append(
                    AuditFinding(
                        check="approval_review_time",
                        severity="critical",
                        message=(
                            f"{fast_approvals}/{len(resolved_actions)} "
                            f"approvals ({ratio:.0%}) were faster than "
                            f"{self.min_review_seconds}s. "
                            f"This pattern suggests systematic rubber-stamping."
                        ),
                        details={
                            "fast_approvals": fast_approvals,
                            "total_resolved": len(resolved_actions),
                            "ratio": round(ratio, 2),
                        },
                    )
                )

        return findings

    def _check_chain_integrity(self, records: list[dict]) -> list[AuditFinding]:
        """Check that the deliberation hash chain is unbroken.

        Each record's parent_record_id should match the previous
        record's reasoning_hash. The first record should have no parent.
        """
        findings: list[AuditFinding] = []

        if len(records) == 0:
            return findings

        # First record should have no parent
        first = records[0]
        if first.get("parent_record_id") is not None:
            findings.append(
                AuditFinding(
                    check="chain_integrity",
                    severity="critical",
                    message=(
                        "First deliberation record has a parent_record_id. "
                        "The chain root should have no parent."
                    ),
                    details={"record_id": first.get("record_id", "")},
                )
            )

        # Check chain links
        for i in range(1, len(records)):
            prev_hash = records[i - 1].get("reasoning_hash")
            parent_id = records[i].get("parent_record_id")

            if prev_hash is not None and parent_id is not None:
                if parent_id != prev_hash:
                    findings.append(
                        AuditFinding(
                            check="chain_integrity",
                            severity="critical",
                            message=(
                                f"Chain break at record {i}: "
                                f"parent_record_id does not match "
                                f"previous record's reasoning_hash"
                            ),
                            details={
                                "record_index": i,
                                "record_id": records[i].get("record_id", ""),
                                "expected_parent": prev_hash,
                                "actual_parent": parent_id,
                            },
                        )
                    )

        return findings

    def _estimate_duration_hours(self, session: dict, records: list[dict]) -> float:
        """Estimate session duration in hours from timestamps.

        Uses session created_at and ended_at if available, otherwise
        falls back to the first and last record timestamps.
        """
        start_str = session.get("created_at", "")
        end_str = session.get("ended_at", "")

        # Try session timestamps first
        if start_str and end_str:
            try:
                start = _parse_iso(start_str)
                end = _parse_iso(end_str)
                return max(0, (end - start).total_seconds() / 3600.0)
            except (ValueError, TypeError):
                pass

        # Fall back to record timestamps
        if len(records) >= 2:
            first_ts = records[0].get("created_at", "")
            last_ts = records[-1].get("created_at", "")
            if first_ts and last_ts:
                try:
                    start = _parse_iso(first_ts)
                    end = _parse_iso(last_ts)
                    return max(0, (end - start).total_seconds() / 3600.0)
                except (ValueError, TypeError):
                    pass

        return 0.0

    def _calculate_score(self, findings: list[AuditFinding]) -> int:
        """Calculate a quality score from 0 to 100 based on findings.

        Scoring:
            Start at 100.
            Critical findings: -20 each
            Warning findings: -10 each
            Info findings: -2 each
            Minimum score: 0
        """
        score = 100

        for f in findings:
            if f.severity == "critical":
                score -= 20
            elif f.severity == "warning":
                score -= 10
            elif f.severity == "info":
                score -= 2

        return max(0, score)


def _parse_iso(ts_str: str) -> datetime:
    """Parse an ISO 8601 timestamp string to a datetime.

    Handles both 'Z' suffix and '+00:00' timezone formats.
    """
    # Normalize Z suffix
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"

    return datetime.fromisoformat(ts_str)
