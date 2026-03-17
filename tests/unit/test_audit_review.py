# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.core.audit_review — session audit quality reviewer."""

import pytest
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso(dt: datetime) -> str:
    """Format a datetime as ISO 8601 with Z suffix."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _make_record(
    index: int,
    record_type: str = "decision",
    created_at: datetime | None = None,
    reasoning_hash: str | None = None,
    parent_record_id: str | None = None,
) -> dict:
    """Create a minimal deliberation record dict for testing."""
    base_time = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
    if created_at is None:
        created_at = base_time + timedelta(minutes=index * 5)
    return {
        "record_id": f"rec-{index}",
        "session_id": "test-session",
        "record_type": record_type,
        "content": {"decision": f"Decision {index}"},
        "reasoning_trace": {"rationale": "Some reasoning here"},
        "reasoning_hash": reasoning_hash or f"hash-{index}",
        "parent_record_id": parent_record_id,
        "created_at": _iso(created_at),
    }


def _make_session(
    created_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> dict:
    """Create a minimal session dict for testing."""
    base_time = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
    return {
        "session_id": "test-session",
        "workspace_id": "ws-1",
        "domain": "coc",
        "state": "archived",
        "created_at": _iso(created_at or base_time),
        "ended_at": _iso(ended_at) if ended_at else None,
    }


# ---------------------------------------------------------------------------
# QualityReport
# ---------------------------------------------------------------------------


class TestQualityReport:
    """Test the QualityReport dataclass and serialisation."""

    def test_to_dict(self):
        from praxis.core.audit_review import AuditFinding, QualityReport

        report = QualityReport(
            session_id="s-1",
            score=85,
            findings=[
                AuditFinding(
                    check="temporal_consistency",
                    severity="warning",
                    message="Gap detected",
                )
            ],
            summary="One warning",
            checked_at="2026-03-16T10:00:00.000000Z",
        )
        d = report.to_dict()
        assert d["session_id"] == "s-1"
        assert d["score"] == 85
        assert len(d["findings"]) == 1
        assert d["findings"][0]["check"] == "temporal_consistency"

    def test_empty_report(self):
        from praxis.core.audit_review import QualityReport

        report = QualityReport(session_id="s-1", score=100)
        d = report.to_dict()
        assert d["score"] == 100
        assert d["findings"] == []


# ---------------------------------------------------------------------------
# Temporal consistency
# ---------------------------------------------------------------------------


class TestTemporalConsistency:
    """Test the temporal consistency check."""

    def test_no_gaps(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [_make_record(i, created_at=base + timedelta(minutes=i * 10)) for i in range(5)]
        session = _make_session(
            created_at=base,
            ended_at=base + timedelta(hours=1),
        )
        report = reviewer.review_session(session, records)
        temporal_findings = [f for f in report.findings if f.check == "temporal_consistency"]
        assert len(temporal_findings) == 0

    def test_large_gap_flagged(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(max_gap_minutes=30)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [
            _make_record(0, created_at=base),
            _make_record(1, created_at=base + timedelta(minutes=45)),  # 45 min gap
            _make_record(2, created_at=base + timedelta(minutes=50)),
        ]
        session = _make_session(created_at=base, ended_at=base + timedelta(hours=1))
        report = reviewer.review_session(session, records)
        temporal_findings = [f for f in report.findings if f.check == "temporal_consistency"]
        assert len(temporal_findings) == 1
        assert temporal_findings[0].severity == "warning"

    def test_timestamp_ordering_violation(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [
            _make_record(0, created_at=base + timedelta(minutes=10)),
            _make_record(1, created_at=base),  # Earlier than previous!
        ]
        session = _make_session(created_at=base)
        report = reviewer.review_session(session, records)
        temporal_findings = [f for f in report.findings if f.check == "temporal_consistency"]
        critical = [f for f in temporal_findings if f.severity == "critical"]
        assert len(critical) == 1

    def test_single_record_no_findings(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        records = [_make_record(0)]
        session = _make_session()
        report = reviewer.review_session(session, records)
        temporal_findings = [f for f in report.findings if f.check == "temporal_consistency"]
        assert len(temporal_findings) == 0


# ---------------------------------------------------------------------------
# Decision density
# ---------------------------------------------------------------------------


class TestDecisionDensity:
    """Test the decision density check."""

    def test_normal_density(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [_make_record(i, created_at=base + timedelta(minutes=i * 15)) for i in range(4)]
        session = _make_session(
            created_at=base,
            ended_at=base + timedelta(hours=1),
        )
        report = reviewer.review_session(session, records)
        density_findings = [f for f in report.findings if f.check == "decision_density"]
        # 4 decisions in 1 hour = 4/hr, which is normal
        assert all(f.severity != "warning" for f in density_findings)

    def test_high_density_flagged(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(max_decisions_per_hour=10)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [_make_record(i, created_at=base + timedelta(seconds=i * 30)) for i in range(20)]
        session = _make_session(
            created_at=base,
            ended_at=base + timedelta(minutes=10),
        )
        report = reviewer.review_session(session, records)
        density_findings = [
            f for f in report.findings if f.check == "decision_density" and f.severity == "warning"
        ]
        assert len(density_findings) >= 1

    def test_no_decisions_info(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        records = [_make_record(0, record_type="observation")]
        session = _make_session()
        report = reviewer.review_session(session, records)
        density_findings = [f for f in report.findings if f.check == "decision_density"]
        assert len(density_findings) == 1
        assert density_findings[0].severity == "info"


# ---------------------------------------------------------------------------
# Approval review time
# ---------------------------------------------------------------------------


class TestApprovalReviewTime:
    """Test the approval review time check."""

    def test_fast_approval_flagged(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(min_review_seconds=5)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        held_actions = [
            {
                "held_id": "h-1",
                "resolved": True,
                "resolution": "approved",
                "created_at": _iso(base),
                "resolved_at": _iso(base + timedelta(seconds=2)),
                "action": "write",
            }
        ]
        session = _make_session()
        report = reviewer.review_session(session, [], held_actions=held_actions)
        approval_findings = [f for f in report.findings if f.check == "approval_review_time"]
        assert len(approval_findings) >= 1

    def test_normal_approval_passes(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(min_review_seconds=5)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        held_actions = [
            {
                "held_id": "h-1",
                "resolved": True,
                "resolution": "approved",
                "created_at": _iso(base),
                "resolved_at": _iso(base + timedelta(seconds=30)),
                "action": "write",
            }
        ]
        session = _make_session()
        report = reviewer.review_session(session, [], held_actions=held_actions)
        approval_findings = [f for f in report.findings if f.check == "approval_review_time"]
        assert len(approval_findings) == 0

    def test_denied_actions_not_flagged(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(min_review_seconds=5)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        held_actions = [
            {
                "held_id": "h-1",
                "resolved": True,
                "resolution": "denied",
                "created_at": _iso(base),
                "resolved_at": _iso(base + timedelta(seconds=1)),
                "action": "delete",
            }
        ]
        session = _make_session()
        report = reviewer.review_session(session, [], held_actions=held_actions)
        approval_findings = [f for f in report.findings if f.check == "approval_review_time"]
        assert len(approval_findings) == 0

    def test_majority_fast_approvals_critical(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(min_review_seconds=5)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        held_actions = [
            {
                "held_id": f"h-{i}",
                "resolved": True,
                "resolution": "approved",
                "created_at": _iso(base + timedelta(minutes=i)),
                "resolved_at": _iso(base + timedelta(minutes=i, seconds=1)),
                "action": "write",
            }
            for i in range(4)
        ]
        session = _make_session()
        report = reviewer.review_session(session, [], held_actions=held_actions)
        critical = [
            f
            for f in report.findings
            if f.check == "approval_review_time" and f.severity == "critical"
        ]
        assert len(critical) >= 1


# ---------------------------------------------------------------------------
# Chain integrity
# ---------------------------------------------------------------------------


class TestChainIntegrity:
    """Test the deliberation chain integrity check."""

    def test_valid_chain(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id=None),
            _make_record(1, reasoning_hash="h1", parent_record_id="h0"),
            _make_record(2, reasoning_hash="h2", parent_record_id="h1"),
        ]
        session = _make_session()
        report = reviewer.review_session(session, records)
        chain_findings = [f for f in report.findings if f.check == "chain_integrity"]
        assert len(chain_findings) == 0

    def test_broken_chain(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id=None),
            _make_record(1, reasoning_hash="h1", parent_record_id="wrong"),
            _make_record(2, reasoning_hash="h2", parent_record_id="h1"),
        ]
        session = _make_session()
        report = reviewer.review_session(session, records)
        chain_findings = [f for f in report.findings if f.check == "chain_integrity"]
        assert len(chain_findings) == 1
        assert chain_findings[0].severity == "critical"

    def test_first_record_with_parent(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id="orphan"),
        ]
        session = _make_session()
        report = reviewer.review_session(session, records)
        chain_findings = [f for f in report.findings if f.check == "chain_integrity"]
        assert len(chain_findings) == 1
        assert chain_findings[0].severity == "critical"

    def test_empty_records(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        session = _make_session()
        report = reviewer.review_session(session, [])
        chain_findings = [f for f in report.findings if f.check == "chain_integrity"]
        assert len(chain_findings) == 0


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


class TestScoring:
    """Test the quality score calculation."""

    def test_perfect_score(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id=None, created_at=base),
            _make_record(
                1,
                reasoning_hash="h1",
                parent_record_id="h0",
                created_at=base + timedelta(minutes=15),
            ),
            _make_record(
                2,
                reasoning_hash="h2",
                parent_record_id="h1",
                created_at=base + timedelta(minutes=30),
            ),
        ]
        session = _make_session(
            created_at=base,
            ended_at=base + timedelta(hours=1),
        )
        report = reviewer.review_session(session, records)
        assert report.score >= 90  # Near-perfect

    def test_low_score_with_critical(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id="orphan"),
            _make_record(1, reasoning_hash="h1", parent_record_id="wrong"),
        ]
        session = _make_session()
        report = reviewer.review_session(session, records)
        assert report.score < 80  # Multiple critical findings

    def test_score_never_below_zero(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer(max_gap_minutes=1, min_review_seconds=100)
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        # Many issues
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id="orphan", created_at=base),
            _make_record(
                1,
                reasoning_hash="h1",
                parent_record_id="wrong",
                created_at=base + timedelta(minutes=5),
            ),
            _make_record(
                2,
                reasoning_hash="h2",
                parent_record_id="wrong2",
                created_at=base + timedelta(minutes=10),
            ),
            _make_record(
                3,
                reasoning_hash="h3",
                parent_record_id="wrong3",
                created_at=base + timedelta(minutes=15),
            ),
            _make_record(
                4,
                reasoning_hash="h4",
                parent_record_id="wrong4",
                created_at=base + timedelta(minutes=20),
            ),
            _make_record(
                5,
                reasoning_hash="h5",
                parent_record_id="wrong5",
                created_at=base + timedelta(minutes=25),
            ),
        ]
        session = _make_session(
            created_at=base,
            ended_at=base + timedelta(minutes=25),
        )
        report = reviewer.review_session(session, records)
        assert report.score >= 0

    def test_summary_reflects_findings(self):
        from praxis.core.audit_review import SessionAuditReviewer

        reviewer = SessionAuditReviewer()
        base = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        records = [
            _make_record(0, reasoning_hash="h0", parent_record_id=None, created_at=base),
            _make_record(
                1,
                reasoning_hash="h1",
                parent_record_id="h0",
                created_at=base + timedelta(minutes=10),
            ),
        ]
        session = _make_session(
            created_at=base,
            ended_at=base + timedelta(hours=1),
        )
        report = reviewer.review_session(session, records)
        assert "Score:" in report.summary or "score:" in report.summary.lower()
