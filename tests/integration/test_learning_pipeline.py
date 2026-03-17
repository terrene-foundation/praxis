# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""M14-04: Learning pipeline integration tests.

Tests the full observe -> analyze -> propose -> approve cycle with
a real SQLite database. Verifies persistence across pipeline re-init,
pattern detection with seeded data, proposal approval diffs, domain
isolation, and rejected proposal recording.
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sid() -> str:
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
# 1. Full observe -> analyze -> propose -> approve cycle
# ---------------------------------------------------------------------------


class TestFullLearningCycle:
    """Test the complete learning pipeline lifecycle."""

    def test_observe_analyze_propose_approve(self):
        """Full cycle: observe -> analyze -> propose -> approve -> diff."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Step 1: Observe enough data to trigger unused_constraint
        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        # Step 2: Analyze
        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1
        assert "communication" in unused[0].description

        # Step 3: Propose
        proposal = pipeline.propose(unused[0])
        assert proposal is not None
        assert proposal.status == "pending"
        assert proposal.proposal_type == "remove"

        # Step 4: Approve and get diff
        result = pipeline.formalize(proposal.proposal_id, approved_by="test-admin")
        assert result["status"] == "approved"
        assert result["reviewed_by"] == "test-admin"
        assert result["reviewed_at"] is not None
        assert "diff" in result
        assert result["diff"]["action"] == "remove"
        assert result["diff"]["target"] == "communication"

    def test_observe_analyze_propose_reject(self):
        """Full cycle ending in rejection."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1

        proposal = pipeline.propose(unused[0])
        assert proposal is not None

        result = pipeline.reject(
            proposal.proposal_id,
            rejected_by="test-admin",
            reason="Communication dimension is needed for future use",
        )
        assert result["status"] == "rejected"
        assert result["reason"] == "Communication dimension is needed for future use"

    def test_rubber_stamp_full_cycle(self):
        """Full cycle for rubber_stamp pattern type."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_held_action_observations(
            pipeline, sid, count=10, resolution="approved", review_time_seconds=1.5
        )

        patterns = pipeline.analyze()
        rubber = [p for p in patterns if p.pattern_type == "rubber_stamp"]
        assert len(rubber) >= 1

        proposal = pipeline.propose(rubber[0])
        assert proposal is not None
        assert proposal.proposal_type == "loosen"
        assert proposal.target == "held_action_threshold"

        result = pipeline.formalize(proposal.proposal_id, approved_by="lead")
        assert result["status"] == "approved"
        assert result["diff"]["action"] == "loosen"


# ---------------------------------------------------------------------------
# 2. Observations persist across pipeline reinit
# ---------------------------------------------------------------------------


class TestPersistenceAcrossReinit:
    """Observations survive pipeline re-initialization."""

    def test_observations_survive_pipeline_reinit(self):
        """Data written by one pipeline instance is readable from another."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        p1 = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(p1, sid, count=7, dimension="financial", utilization=0.5)

        # Create a completely new pipeline instance
        p2 = LearningPipeline(domain="coc", session_id=sid)
        obs = p2.get_observations(target="constraint_evaluation")
        assert len(obs) == 7

        # And a domain-wide pipeline can also see them
        p3 = LearningPipeline(domain="coc")
        all_obs = p3.get_observations(target="constraint_evaluation")
        assert len(all_obs) >= 7

    def test_patterns_survive_pipeline_reinit(self):
        """Detected patterns persist and are readable from a new instance."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        p1 = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(p1, sid, count=10, dimension="communication", utilization=0.0)
        patterns = p1.analyze()
        assert len(patterns) >= 1

        p2 = LearningPipeline(domain="coc")
        db_patterns = p2.get_patterns(pattern_type="unused_constraint")
        assert len(db_patterns) >= 1

    def test_proposals_survive_pipeline_reinit(self):
        """Proposals persist across pipeline re-initialization."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        p1 = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(p1, sid, count=10, dimension="communication", utilization=0.0)
        patterns = p1.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = p1.propose(unused[0])
        assert proposal is not None

        # Read from new pipeline instance
        p2 = LearningPipeline(domain="coc")
        proposals = p2.get_proposals(status="pending")
        found = [p for p in proposals if p["id"] == proposal.proposal_id]
        assert len(found) == 1
        assert found[0]["status"] == "pending"


# ---------------------------------------------------------------------------
# 3. Pattern detection with seeded data
# ---------------------------------------------------------------------------


class TestPatternDetectionWithSeededData:
    """Test that each pattern type is correctly detected from seeded observations."""

    def test_boundary_pressure_detected(self):
        """High-utilization observations trigger boundary_pressure pattern."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # 12 observations with 85% utilization on financial dimension
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

    def test_always_approved_detected(self):
        """Uniform auto_approved verdicts trigger always_approved pattern."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline,
            sid,
            count=12,
            action="read",
            verdict="auto_approved",
            dimension="operational",
        )

        patterns = pipeline.analyze()
        always = [p for p in patterns if p.pattern_type == "always_approved"]
        assert len(always) >= 1
        assert "read" in always[0].description

    def test_never_reached_detected(self):
        """Unused constraint templates trigger never_reached pattern."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_session_lifecycle_observations(pipeline, sid, count=5, constraint_template="moderate")

        patterns = pipeline.analyze()
        never = [p for p in patterns if p.pattern_type == "never_reached"]
        assert len(never) >= 1
        # Should detect at least 'strict' or 'permissive' as unused
        descriptions = " ".join(p.description for p in never)
        assert "strict" in descriptions or "permissive" in descriptions

    def test_insufficient_data_no_patterns(self):
        """Below-threshold data produces no patterns."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Only 2 observations — below all minimum thresholds
        for _ in range(2):
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


# ---------------------------------------------------------------------------
# 4. Proposal approval produces correct diff
# ---------------------------------------------------------------------------


class TestProposalDiff:
    """Test that approved proposals produce correct diff structures."""

    def test_unused_constraint_diff(self):
        """unused_constraint approval produces a 'remove' diff."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = pipeline.propose(unused[0])

        result = pipeline.formalize(proposal.proposal_id, approved_by="admin")
        diff = result["diff"]

        assert diff["action"] == "remove"
        assert diff["target"] == "communication"
        assert diff["domain"] == "coc"
        assert "note" in diff

    def test_boundary_pressure_diff(self):
        """boundary_pressure approval produces a 'loosen' diff."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
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
        proposal = pipeline.propose(boundary[0])

        result = pipeline.formalize(proposal.proposal_id, approved_by="admin")
        diff = result["diff"]

        assert diff["action"] == "loosen"
        assert "temporal" in diff["target"]

    def test_rubber_stamp_diff(self):
        """rubber_stamp approval produces a 'loosen' diff for held_action_threshold."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_held_action_observations(
            pipeline, sid, count=10, resolution="approved", review_time_seconds=1.0
        )

        patterns = pipeline.analyze()
        rubber = [p for p in patterns if p.pattern_type == "rubber_stamp"]
        proposal = pipeline.propose(rubber[0])

        result = pipeline.formalize(proposal.proposal_id, approved_by="admin")
        diff = result["diff"]

        assert diff["action"] == "loosen"
        assert diff["target"] == "held_action_threshold"


# ---------------------------------------------------------------------------
# 5. Domain isolation
# ---------------------------------------------------------------------------


class TestDomainIsolation:
    """COC observations don't affect COE analysis and vice versa."""

    def test_coc_observations_invisible_to_coe(self):
        """Observations for COC domain are not visible from COE pipeline."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        coc = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(coc, sid, count=10, dimension="financial", utilization=0.0)

        # COE pipeline should see nothing
        coe = LearningPipeline(domain="coe")
        obs = coe.get_observations()
        assert len(obs) == 0

    def test_coe_patterns_independent_of_coc(self):
        """Patterns detected for COC don't appear in COE analysis."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        coc = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            coc, sid, count=10, dimension="communication", utilization=0.0
        )

        # COC analysis finds patterns
        coc_patterns = coc.analyze()
        assert len(coc_patterns) >= 1

        # COE analysis finds nothing
        coe = LearningPipeline(domain="coe")
        coe_patterns = coe.analyze()
        assert len(coe_patterns) == 0

    def test_proposals_scoped_to_domain(self):
        """Proposals created for COC are only visible in COC pipeline."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        coc = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            coc, sid, count=10, dimension="communication", utilization=0.0
        )
        patterns = coc.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        coc.propose(unused[0])

        # COC sees the proposal
        coc_proposals = coc.get_proposals(status="pending")
        assert len(coc_proposals) >= 1

        # COE does not
        coe = LearningPipeline(domain="coe")
        coe_proposals = coe.get_proposals(status="pending")
        assert len(coe_proposals) == 0


# ---------------------------------------------------------------------------
# 6. Rejected proposals are recorded
# ---------------------------------------------------------------------------


class TestRejectedProposalRecording:
    """Rejected proposals are persisted with status and reason."""

    def test_rejected_proposal_persists(self):
        """Rejected proposals have their status and reviewer stored in DB."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = pipeline.propose(unused[0])

        pipeline.reject(
            proposal.proposal_id,
            rejected_by="team-lead",
            reason="Communication constraints will be needed in Phase 2",
        )

        # Verify via a fresh pipeline
        p2 = LearningPipeline(domain="coc")
        rejected = p2.get_proposals(status="rejected")
        assert len(rejected) >= 1
        found = [p for p in rejected if p["id"] == proposal.proposal_id]
        assert len(found) == 1
        assert found[0]["status"] == "rejected"
        assert found[0]["reviewed_by"] == "team-lead"

    def test_cannot_approve_after_rejection(self):
        """Once rejected, a proposal cannot be approved."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = pipeline.propose(unused[0])

        pipeline.reject(proposal.proposal_id, rejected_by="admin")

        with pytest.raises(ValueError, match="not 'pending'"):
            pipeline.formalize(proposal.proposal_id, approved_by="admin")

    def test_cannot_reject_after_approval(self):
        """Once approved, a proposal cannot be rejected."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        _seed_constraint_observations(
            pipeline, sid, count=10, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        proposal = pipeline.propose(unused[0])

        pipeline.formalize(proposal.proposal_id, approved_by="admin")

        with pytest.raises(ValueError, match="not 'pending'"):
            pipeline.reject(proposal.proposal_id, rejected_by="admin")
