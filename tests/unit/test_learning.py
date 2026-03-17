# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Comprehensive tests for CO Layer 5: Learning Pipeline (M09).

Tests cover:
- M09-01: Observation recording
- M09-02: Observation target consumers
- M09-03: Pattern analysis engine (all 5 pattern types)
- M09-04: Evolution proposal generation
- M09-05: Human approval/rejection flow
- M09-06: Persistence round-trip
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session_id() -> str:
    return str(uuid.uuid4())


def _seed_constraint_observations(
    pipeline,
    session_id: str,
    *,
    count: int = 10,
    dimension: str = "financial",
    utilization: float = 0.0,
    action: str = "read",
    verdict: str = "auto_approved",
):
    """Seed the pipeline with constraint_evaluation observations."""
    for _ in range(count):
        pipeline.observe(
            target="constraint_evaluation",
            content={
                "session_id": session_id,
                "action": action,
                "resource": "/src/file.py",
                "verdict": verdict,
                "dimension": dimension,
                "utilization": utilization,
            },
        )


def _seed_held_action_observations(
    pipeline,
    session_id: str,
    *,
    count: int = 10,
    resolution: str = "approved",
    review_time_seconds: float = 2.0,
):
    """Seed the pipeline with held_action_resolution observations."""
    for _ in range(count):
        pipeline.observe(
            target="held_action_resolution",
            content={
                "session_id": session_id,
                "held_id": str(uuid.uuid4()),
                "action": "write",
                "resolution": resolution,
                "resolved_by": "test-user",
                "review_time_seconds": review_time_seconds,
            },
        )


def _seed_session_lifecycle_observations(
    pipeline,
    session_id: str,
    *,
    count: int = 5,
    constraint_template: str = "moderate",
):
    """Seed the pipeline with session_lifecycle observations."""
    for _ in range(count):
        pipeline.observe(
            target="session_lifecycle",
            content={
                "session_id": session_id,
                "event": "created",
                "constraint_template": constraint_template,
            },
        )


# ---------------------------------------------------------------------------
# M09-01: Observation recording
# ---------------------------------------------------------------------------


class TestObservationRecording:
    """Test the LearningPipeline.observe() method."""

    def test_record_observation_basic(self):
        """An observation is recorded and persisted."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        obs = pipeline.observe(
            target="constraint_evaluation",
            content={"action": "read", "dimension": "financial", "utilization": 0.5},
        )

        assert obs.observation_id
        assert obs.session_id == sid
        assert obs.domain == "coc"
        assert obs.target == "constraint_evaluation"
        assert obs.content["action"] == "read"
        assert obs.created_at

    def test_record_observation_invalid_target(self):
        """Observations for undeclared targets are rejected."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        with pytest.raises(ValueError, match="not declared"):
            pipeline.observe(
                target="nonexistent_target",
                content={"data": "test"},
            )

    def test_record_observation_without_session_id(self):
        """Observations without any session_id raise ValueError."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")

        with pytest.raises(ValueError, match="session_id"):
            pipeline.observe(
                target="constraint_evaluation",
                content={"data": "test"},
            )

    def test_record_observation_session_id_from_content(self):
        """If pipeline has no session_id, it can come from content."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")
        sid = _make_session_id()

        obs = pipeline.observe(
            target="constraint_evaluation",
            content={
                "session_id": sid,
                "action": "read",
                "dimension": "financial",
                "utilization": 0.1,
            },
        )

        assert obs.session_id == sid

    def test_get_observations_round_trip(self):
        """Observations can be retrieved after recording."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        pipeline.observe(
            target="constraint_evaluation",
            content={"action": "write", "dimension": "operational", "utilization": 0.3},
        )

        observations = pipeline.get_observations(target="constraint_evaluation")
        assert len(observations) >= 1
        assert observations[0]["target"] == "constraint_evaluation"


# ---------------------------------------------------------------------------
# M09-02: Observation target consumers
# ---------------------------------------------------------------------------


class TestObservationConsumers:
    """Test the learning_observers integration functions."""

    def test_observe_constraint_evaluation(self):
        """observe_constraint_evaluation creates an observation record."""
        from praxis.core.learning import LearningPipeline
        from praxis.core.learning_observers import observe_constraint_evaluation

        sid = _make_session_id()
        observe_constraint_evaluation(
            session_id=sid,
            domain="coc",
            action="read",
            resource="/src/file.py",
            verdict="auto_approved",
            dimension="financial",
            utilization=0.3,
        )

        pipeline = LearningPipeline(domain="coc", session_id=sid)
        obs = pipeline.get_observations(target="constraint_evaluation")
        assert len(obs) >= 1
        assert obs[0]["content"]["action"] == "read"

    def test_observe_held_action_resolution(self):
        """observe_held_action_resolution creates an observation record."""
        from praxis.core.learning import LearningPipeline
        from praxis.core.learning_observers import observe_held_action_resolution

        sid = _make_session_id()
        observe_held_action_resolution(
            session_id=sid,
            domain="coc",
            held_id="test-held-id",
            action="delete",
            resolution="approved",
            resolved_by="supervisor",
            review_time_seconds=3.5,
        )

        pipeline = LearningPipeline(domain="coc", session_id=sid)
        obs = pipeline.get_observations(target="held_action_resolution")
        assert len(obs) >= 1
        assert obs[0]["content"]["resolution"] == "approved"

    def test_observe_session_lifecycle(self):
        """observe_session_lifecycle creates an observation record."""
        from praxis.core.learning import LearningPipeline
        from praxis.core.learning_observers import observe_session_lifecycle

        sid = _make_session_id()
        observe_session_lifecycle(
            session_id=sid,
            domain="coc",
            event="created",
            constraint_template="moderate",
        )

        pipeline = LearningPipeline(domain="coc", session_id=sid)
        obs = pipeline.get_observations(target="session_lifecycle")
        assert len(obs) >= 1
        assert obs[0]["content"]["event"] == "created"

    def test_observer_silent_on_invalid_domain(self):
        """Observers do not raise on domains without matching targets."""
        from praxis.core.learning_observers import observe_constraint_evaluation

        # This should not raise — errors are silently logged
        observe_constraint_evaluation(
            session_id=_make_session_id(),
            domain="nonexistent_domain",
            action="read",
            resource=None,
            verdict="auto_approved",
            dimension="financial",
            utilization=0.0,
        )


# ---------------------------------------------------------------------------
# M09-03: Pattern analysis engine
# ---------------------------------------------------------------------------


class TestPatternDetection:
    """Test each of the 5 pattern detectors."""

    def test_detect_unused_constraint(self):
        """Detect a constraint dimension with 0% utilization across evaluations."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Seed observations where 'communication' always has 0% utilization
        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()

        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1
        assert "communication" in unused[0].description
        assert unused[0].confidence > 0.0

    def test_no_unused_constraint_when_triggered(self):
        """No unused_constraint pattern when dimension has utilization > 0."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Seed observations where 'financial' has varied utilization
        for util in [0.0, 0.1, 0.3, 0.5, 0.2]:
            pipeline.observe(
                target="constraint_evaluation",
                content={
                    "session_id": sid,
                    "action": "read",
                    "dimension": "financial",
                    "utilization": util,
                    "verdict": "auto_approved",
                },
            )

        patterns = pipeline.analyze()
        unused_financial = [
            p
            for p in patterns
            if p.pattern_type == "unused_constraint" and "'financial'" in p.description
        ]
        assert len(unused_financial) == 0

    def test_detect_rubber_stamp(self):
        """Detect rubber-stamp pattern: >95% approval, <5s review time."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_held_action_observations(
            pipeline, sid, count=10, resolution="approved", review_time_seconds=2.0
        )

        patterns = pipeline.analyze()

        rubber = [p for p in patterns if p.pattern_type == "rubber_stamp"]
        assert len(rubber) >= 1
        assert rubber[0].confidence > 0.0
        assert "approved" in rubber[0].description.lower()

    def test_no_rubber_stamp_with_slow_review(self):
        """No rubber_stamp when average review time is >= 5 seconds."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_held_action_observations(
            pipeline, sid, count=10, resolution="approved", review_time_seconds=10.0
        )

        patterns = pipeline.analyze()
        rubber = [p for p in patterns if p.pattern_type == "rubber_stamp"]
        assert len(rubber) == 0

    def test_no_rubber_stamp_with_denials(self):
        """No rubber_stamp when approval rate is <= 95%."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # 5 approved + 5 denied = 50% approval rate
        _seed_held_action_observations(
            pipeline, sid, count=5, resolution="approved", review_time_seconds=1.0
        )
        _seed_held_action_observations(
            pipeline, sid, count=5, resolution="denied", review_time_seconds=1.0
        )

        patterns = pipeline.analyze()
        rubber = [p for p in patterns if p.pattern_type == "rubber_stamp"]
        assert len(rubber) == 0

    def test_detect_boundary_pressure(self):
        """Detect actions clustering near constraint boundaries (>80% utilization)."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Seed observations where financial utilization is repeatedly >80%
        for _ in range(12):
            pipeline.observe(
                target="constraint_evaluation",
                content={
                    "session_id": sid,
                    "action": "write",
                    "dimension": "financial",
                    "utilization": 0.85,
                    "verdict": "flagged",
                },
            )

        patterns = pipeline.analyze()

        boundary = [p for p in patterns if p.pattern_type == "boundary_pressure"]
        assert len(boundary) >= 1
        assert "financial" in boundary[0].description

    def test_no_boundary_pressure_when_low_util(self):
        """No boundary_pressure when utilization is low."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=15, dimension="financial", utilization=0.3
        )

        patterns = pipeline.analyze()
        boundary = [
            p
            for p in patterns
            if p.pattern_type == "boundary_pressure" and "'financial'" in p.description
        ]
        assert len(boundary) == 0

    def test_detect_always_approved(self):
        """Detect action type that is always AUTO_APPROVED."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # All evaluations for 'read' are auto_approved
        _seed_constraint_observations(
            pipeline, sid, count=12, action="read", verdict="auto_approved", dimension="operational"
        )

        patterns = pipeline.analyze()

        always = [p for p in patterns if p.pattern_type == "always_approved"]
        assert len(always) >= 1
        assert "read" in always[0].description

    def test_no_always_approved_with_mixed_verdicts(self):
        """No always_approved when verdicts include non-auto_approved."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        for i in range(12):
            pipeline.observe(
                target="constraint_evaluation",
                content={
                    "session_id": sid,
                    "action": "write",
                    "dimension": "operational",
                    "utilization": 0.5,
                    "verdict": "auto_approved" if i % 3 != 0 else "flagged",
                },
            )

        patterns = pipeline.analyze()
        always = [
            p
            for p in patterns
            if p.pattern_type == "always_approved" and "'write'" in p.description
        ]
        assert len(always) == 0

    def test_detect_never_reached(self):
        """Detect constraint template that exists but has never been used."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Seed session_lifecycle with only "moderate" template usage
        # coc domain has strict, moderate, permissive templates
        _seed_session_lifecycle_observations(pipeline, sid, count=5, constraint_template="moderate")

        patterns = pipeline.analyze()

        never = [p for p in patterns if p.pattern_type == "never_reached"]
        # Should detect "strict" and "permissive" as unused
        assert len(never) >= 1
        template_names = [p.description for p in never]
        assert any("strict" in d or "permissive" in d for d in template_names)

    def test_no_patterns_insufficient_data(self):
        """No patterns when observation count is below minimum thresholds."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Only 2 observations — below all thresholds
        pipeline.observe(
            target="constraint_evaluation",
            content={
                "session_id": sid,
                "action": "read",
                "dimension": "financial",
                "utilization": 0.0,
                "verdict": "auto_approved",
            },
        )

        patterns = pipeline.analyze()
        assert len(patterns) == 0

    def test_analyze_empty_database(self):
        """analyze() returns empty list when there are no observations."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")
        patterns = pipeline.analyze()
        assert patterns == []


# ---------------------------------------------------------------------------
# M09-04: Evolution proposal generation
# ---------------------------------------------------------------------------


class TestEvolutionProposals:
    """Test proposal generation from detected patterns."""

    def test_propose_from_unused_constraint(self):
        """unused_constraint generates a 'remove' proposal."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1

        proposal = pipeline.propose(unused[0])
        assert proposal is not None
        assert proposal.proposal_type == "remove"
        assert "communication" in proposal.target
        assert proposal.status == "pending"

    def test_propose_from_rubber_stamp(self):
        """rubber_stamp generates a 'loosen' proposal."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_held_action_observations(
            pipeline, sid, count=10, resolution="approved", review_time_seconds=1.0
        )

        patterns = pipeline.analyze()
        rubber = [p for p in patterns if p.pattern_type == "rubber_stamp"]
        assert len(rubber) >= 1

        proposal = pipeline.propose(rubber[0])
        assert proposal is not None
        assert proposal.proposal_type == "loosen"
        assert proposal.target == "held_action_threshold"

    def test_propose_from_boundary_pressure(self):
        """boundary_pressure generates a 'loosen' proposal."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        for _ in range(12):
            pipeline.observe(
                target="constraint_evaluation",
                content={
                    "session_id": sid,
                    "action": "write",
                    "dimension": "temporal",
                    "utilization": 0.9,
                    "verdict": "held",
                },
            )

        patterns = pipeline.analyze()
        boundary = [p for p in patterns if p.pattern_type == "boundary_pressure"]
        assert len(boundary) >= 1

        proposal = pipeline.propose(boundary[0])
        assert proposal is not None
        assert proposal.proposal_type == "loosen"

    def test_propose_from_always_approved(self):
        """always_approved generates a 'tighten' proposal."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=12, action="read", verdict="auto_approved", dimension="operational"
        )

        patterns = pipeline.analyze()
        always = [p for p in patterns if p.pattern_type == "always_approved"]
        assert len(always) >= 1

        proposal = pipeline.propose(always[0])
        assert proposal is not None
        assert proposal.proposal_type == "tighten"

    def test_propose_from_never_reached(self):
        """never_reached generates a 'remove' proposal."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_session_lifecycle_observations(pipeline, sid, count=5, constraint_template="moderate")

        patterns = pipeline.analyze()
        never = [p for p in patterns if p.pattern_type == "never_reached"]
        assert len(never) >= 1

        proposal = pipeline.propose(never[0])
        assert proposal is not None
        assert proposal.proposal_type == "remove"
        assert "template:" in proposal.target

    def test_low_confidence_skipped(self):
        """Patterns with confidence < 0.3 do not generate proposals."""
        from praxis.core.learning import LearningPipeline, Pattern

        pipeline = LearningPipeline(domain="coc")

        low_confidence_pattern = Pattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type="unused_constraint",
            description="The 'financial' constraint dimension has never been triggered.",
            confidence=0.1,  # Below threshold
            evidence=["obs-1"],
            domain="coc",
            created_at="2026-01-01T00:00:00.000000Z",
        )

        proposal = pipeline.propose(low_confidence_pattern)
        assert proposal is None


# ---------------------------------------------------------------------------
# M09-05: Human approval/rejection flow
# ---------------------------------------------------------------------------


class TestApprovalRejectionFlow:
    """Test the formalize() and reject() methods."""

    def _create_pending_proposal(self, pipeline, session_id: str) -> str:
        """Helper: create and return a pending proposal ID."""
        _seed_constraint_observations(
            pipeline, session_id, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1

        proposal = pipeline.propose(unused[0])
        assert proposal is not None
        return proposal.proposal_id

    def test_approve_proposal(self):
        """Approving a proposal returns a diff and marks it as approved."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        proposal_id = self._create_pending_proposal(pipeline, sid)

        result = pipeline.formalize(proposal_id, approved_by="test-admin")

        assert result["status"] == "approved"
        assert result["reviewed_by"] == "test-admin"
        assert result["reviewed_at"]
        assert "diff" in result
        assert result["diff"]["action"]  # Has an action recommendation
        assert result["diff"]["note"]  # Has a human-readable note

    def test_reject_proposal(self):
        """Rejecting a proposal marks it as rejected with reason."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        proposal_id = self._create_pending_proposal(pipeline, sid)

        result = pipeline.reject(proposal_id, rejected_by="test-admin", reason="Not needed")

        assert result["status"] == "rejected"
        assert result["reviewed_by"] == "test-admin"
        assert result["reason"] == "Not needed"

    def test_cannot_approve_nonexistent_proposal(self):
        """Approving a nonexistent proposal raises KeyError."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")

        with pytest.raises(KeyError):
            pipeline.formalize("nonexistent-id", approved_by="admin")

    def test_cannot_reject_nonexistent_proposal(self):
        """Rejecting a nonexistent proposal raises KeyError."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")

        with pytest.raises(KeyError):
            pipeline.reject("nonexistent-id", rejected_by="admin")

    def test_cannot_approve_already_approved(self):
        """Approving an already-approved proposal raises ValueError."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        proposal_id = self._create_pending_proposal(pipeline, sid)

        # First approval succeeds
        pipeline.formalize(proposal_id, approved_by="admin")

        # Second approval fails
        with pytest.raises(ValueError, match="not 'pending'"):
            pipeline.formalize(proposal_id, approved_by="admin")

    def test_cannot_reject_already_rejected(self):
        """Rejecting an already-rejected proposal raises ValueError."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        proposal_id = self._create_pending_proposal(pipeline, sid)

        # First rejection succeeds
        pipeline.reject(proposal_id, rejected_by="admin")

        # Second rejection fails
        with pytest.raises(ValueError, match="not 'pending'"):
            pipeline.reject(proposal_id, rejected_by="admin")


# ---------------------------------------------------------------------------
# M09-06: Persistence round-trip
# ---------------------------------------------------------------------------


class TestPersistenceRoundTrip:
    """Test that all learning data persists correctly through the database."""

    def test_observation_persistence(self):
        """Observations persist and can be retrieved by domain and target."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        pipeline.observe(
            target="constraint_evaluation",
            content={"action": "read", "dimension": "financial", "utilization": 0.5},
        )

        # Retrieve from a fresh pipeline (no in-memory cache)
        pipeline2 = LearningPipeline(domain="coc", session_id=sid)
        obs = pipeline2.get_observations(target="constraint_evaluation")
        assert len(obs) >= 1
        content = obs[0].get("content", {})
        assert content.get("action") == "read"
        assert content.get("utilization") == 0.5

    def test_pattern_persistence(self):
        """Patterns persist and can be retrieved by domain and type."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        assert len(patterns) >= 1

        # Retrieve from a fresh pipeline
        pipeline2 = LearningPipeline(domain="coc")
        db_patterns = pipeline2.get_patterns(pattern_type="unused_constraint")
        assert len(db_patterns) >= 1
        assert db_patterns[0]["pattern_type"] == "unused_constraint"

    def test_proposal_persistence(self):
        """Proposals persist and can be retrieved by domain and status."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1

        proposal = pipeline.propose(unused[0])
        assert proposal is not None

        # Retrieve from a fresh pipeline
        pipeline2 = LearningPipeline(domain="coc")
        proposals = pipeline2.get_proposals(status="pending")
        assert len(proposals) >= 1
        assert proposals[0]["status"] == "pending"

    def test_approved_proposal_status_persists(self):
        """Approved proposal status persists correctly."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = pipeline.propose(unused[0])
        assert proposal is not None

        pipeline.formalize(proposal.proposal_id, approved_by="test-admin")

        # Verify in DB
        pipeline2 = LearningPipeline(domain="coc")
        proposals = pipeline2.get_proposals(status="approved")
        assert len(proposals) >= 1
        assert proposals[0]["status"] == "approved"
        assert proposals[0]["reviewed_by"] == "test-admin"

    def test_rejected_proposal_status_persists(self):
        """Rejected proposal status persists correctly."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = pipeline.propose(unused[0])
        assert proposal is not None

        pipeline.reject(proposal.proposal_id, rejected_by="test-admin", reason="Not now")

        # Verify in DB
        pipeline2 = LearningPipeline(domain="coc")
        proposals = pipeline2.get_proposals(status="rejected")
        assert len(proposals) >= 1
        assert proposals[0]["status"] == "rejected"

    def test_cross_session_analysis(self):
        """Analysis works across observations from multiple sessions."""
        from praxis.core.learning import LearningPipeline

        sid1 = _make_session_id()
        sid2 = _make_session_id()

        # Create observations in session 1
        p1 = LearningPipeline(domain="coc", session_id=sid1)
        _seed_constraint_observations(p1, sid1, count=5, dimension="communication", utilization=0.0)

        # Create observations in session 2
        p2 = LearningPipeline(domain="coc", session_id=sid2)
        _seed_constraint_observations(p2, sid2, count=5, dimension="communication", utilization=0.0)

        # Analyze across all sessions (no session_id filter)
        pipeline_all = LearningPipeline(domain="coc")
        patterns = pipeline_all.analyze()

        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1

    def test_domain_isolation(self):
        """Observations from different domains do not interfere."""
        from praxis.core.learning import LearningPipeline

        sid = _make_session_id()

        # Record observations for coc domain
        p_coc = LearningPipeline(domain="coc", session_id=sid)
        _seed_constraint_observations(p_coc, sid, count=10, dimension="financial", utilization=0.0)

        # Analyzing coe domain should find nothing (different domain)
        p_coe = LearningPipeline(domain="coe")
        observations = p_coe.get_observations()
        assert len(observations) == 0
