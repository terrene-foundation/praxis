# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Final adversarial and regression tests (Round 4).

Covers areas changed since the last red team round: learning pipeline
integration, session detail data flow, multi-tool context stress,
constraint enforcement correctness, and security regression.

All tests use real SQLite (via the autouse _isolated_db fixture) and
real crypto (via the conftest key_manager). NO MOCKING.
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


# ===========================================================================
# 1. Learning pipeline edge cases
# ===========================================================================


class TestLearningPipelineAdversarial:
    """Adversarial tests for the continuous learning pipeline."""

    def test_100_observations_patterns_detected(self):
        """Create 100 observations, run analyze(), verify patterns are
        detected correctly with high confidence."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # 100 observations with 0% utilization on communication
        _seed_constraint_observations(
            pipeline, sid, count=100, dimension="communication", utilization=0.0
        )

        patterns = pipeline.analyze()
        unused = [p for p in patterns if p.pattern_type == "unused_constraint"]
        assert len(unused) >= 1

        # With 100 observations, confidence should be high (capped at 1.0)
        comm_pattern = [p for p in unused if "communication" in p.description]
        assert len(comm_pattern) >= 1
        assert comm_pattern[0].confidence == 1.0  # min(1.0, 100/20)

    def test_proposal_idempotency_cannot_approve_twice(self):
        """Approve a proposal, verify it cannot be approved again."""
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

        # First approval succeeds
        result = pipeline.formalize(proposal.proposal_id, approved_by="admin-1")
        assert result["status"] == "approved"

        # Second approval must fail
        with pytest.raises(ValueError, match="not 'pending'"):
            pipeline.formalize(proposal.proposal_id, approved_by="admin-2")

    def test_domain_isolation_cross_domain_observation(self):
        """Observations recorded in COC must not appear in COE analysis."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        coc = LearningPipeline(domain="coc", session_id=sid)

        # Create 15 observations in COC
        _seed_constraint_observations(
            coc, sid, count=15, dimension="communication", utilization=0.0
        )

        # COC sees them
        coc_obs = coc.get_observations(target="constraint_evaluation")
        assert len(coc_obs) == 15

        # COE does not — even using the same session_id
        coe = LearningPipeline(domain="coe", session_id=sid)
        coe_obs = coe.get_observations(target="constraint_evaluation")
        assert len(coe_obs) == 0

        # COE analysis produces no patterns from COC data
        coe_patterns = coe.analyze()
        assert len(coe_patterns) == 0

    def test_burst_observations_all_persisted(self):
        """Create observations in rapid succession and verify all persisted."""
        from praxis.core.learning import LearningPipeline

        sid = _sid()
        pipeline = LearningPipeline(domain="coc", session_id=sid)

        # Burst: 50 observations as fast as possible
        for i in range(50):
            pipeline.observe(
                target="constraint_evaluation",
                content={
                    "session_id": sid,
                    "action": "write",
                    "dimension": "financial",
                    "utilization": i / 100.0,
                    "verdict": "auto_approved",
                },
            )

        # All 50 must be persisted
        obs = pipeline.get_observations(target="constraint_evaluation")
        assert len(obs) == 50

        # Verify via a fresh pipeline instance (different Python object, same DB)
        p2 = LearningPipeline(domain="coc", session_id=sid)
        obs2 = p2.get_observations(target="constraint_evaluation")
        assert len(obs2) == 50


# ===========================================================================
# 2. Session detail data roundtrip
# ===========================================================================


class TestSessionDetailRoundtrip:
    """Verify session data survives create -> retrieve roundtrip."""

    def test_decisions_with_varying_confidence_retrieved_via_timeline(self, key_manager):
        """Create session, record 5 decisions with confidence 0.0, 0.25, 0.5,
        0.75, 1.0, verify all retrieved via timeline."""
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-confidence", domain="coc")
        sid = session["session_id"]

        engine = DeliberationEngine(session_id=sid, key_manager=key_manager, key_id="test-key")

        confidences = [0.0, 0.25, 0.5, 0.75, 1.0]
        for c in confidences:
            engine.record_decision(
                decision=f"Decision at confidence {c}",
                rationale=f"Testing confidence={c}",
                confidence=c,
            )

        # Retrieve timeline
        timeline, total = engine.get_timeline()
        assert total == 5

        # Verify each confidence value roundtrips correctly
        retrieved_confidences = [r["confidence"] for r in timeline]
        assert retrieved_confidences == confidences

    def test_coe_session_has_coe_phases(self, key_manager):
        """Create session with COE domain, verify phase_list comes from COE YAML."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-coe-phases", domain="coe")

        # COE phases: research, draft, review, revise
        expected_phases = ["research", "draft", "review", "revise"]
        assert session["phase_list"] == expected_phases
        assert session["current_phase"] == "research"

        # Verify the same after a fresh get
        retrieved = mgr.get_session(session["session_id"])
        assert retrieved["phase_list"] == expected_phases
        assert retrieved["current_phase"] == "research"

    def test_constraint_tightening_persists_and_retrievable(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        """Update constraints (tightening), verify the updated values persist
        and are retrievable from a fresh get_session call."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-tighten-persist",
            domain="coc",
            constraints=sample_constraints,
        )
        sid = session["session_id"]

        # Confirm initial values
        assert session["constraint_envelope"]["financial"]["max_spend"] == 1000.0

        # Tighten
        updated = mgr.update_constraints(sid, tighter_constraints)
        assert updated["constraint_envelope"]["financial"]["max_spend"] == 500.0
        assert updated["constraint_envelope"]["temporal"]["max_duration_minutes"] == 60

        # Verify via a fresh get_session
        retrieved = mgr.get_session(sid)
        assert retrieved["constraint_envelope"]["financial"]["max_spend"] == 500.0
        assert retrieved["constraint_envelope"]["operational"]["allowed_actions"] == [
            "read",
            "write",
        ]
        assert retrieved["constraint_envelope"]["temporal"]["max_duration_minutes"] == 60
        assert retrieved["constraint_envelope"]["data_access"]["allowed_paths"] == [
            "/src",
            "/tests",
        ]
        assert retrieved["constraint_envelope"]["communication"]["allowed_channels"] == ["internal"]


# ===========================================================================
# 3. Multi-tool context stress
# ===========================================================================


class TestMultiToolContextStress:
    """Stress tests for multi-tool context consistency."""

    def test_10_sessions_in_same_workspace(self, key_manager):
        """Create 10 sessions in the same workspace, verify list_sessions
        returns all 10."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        session_ids = set()
        for i in range(10):
            session = mgr.create_session(
                workspace_id="ws-ten-sessions",
                domain="coc",
            )
            session_ids.add(session["session_id"])

        # list_sessions should return all 10
        all_sessions = mgr.list_sessions(workspace_id="ws-ten-sessions")
        assert len(all_sessions) == 10
        retrieved_ids = {s["session_id"] for s in all_sessions}
        assert retrieved_ids == session_ids

    def test_20_audit_anchors_chain_integrity_across_fresh_instance(self, key_manager):
        """Create session, add 20 audit anchors, verify chain integrity
        across a fresh AuditChain instance."""
        from praxis.core.session import SessionManager
        from praxis.trust.audit import AuditChain

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-chain-20", domain="coc")
        sid = session["session_id"]

        # Build chain with 20 anchors
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_manager)
        for i in range(20):
            chain.append(
                action=f"action-{i}",
                actor="human" if i % 2 == 0 else "ai",
                result="auto_approved",
                resource=f"/src/file-{i}.py",
            )

        assert chain.length == 20

        # Fresh instance reads from DB
        chain2 = AuditChain(session_id=sid, key_id="test-key", key_manager=key_manager)
        assert chain2.length == 20

        # Verify integrity from the fresh instance
        valid, breaks = chain2.verify_integrity()
        assert valid is True
        assert breaks == []

    def test_session_update_visible_from_fresh_get(self, key_manager, sample_constraints):
        """Create session via SessionManager, update constraints, verify
        the update is visible from a fresh get_session call."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-fresh-get",
            domain="coc",
            constraints=sample_constraints,
        )
        sid = session["session_id"]

        # Tighten financial limit
        tighter = dict(sample_constraints)
        tighter["financial"] = {"max_spend": 500.0}
        mgr.update_constraints(sid, tighter)

        # Fresh get_session (could be a different code path in a multi-tool setup)
        mgr2 = SessionManager(key_manager=key_manager, key_id="test-key")
        retrieved = mgr2.get_session(sid)
        assert retrieved["constraint_envelope"]["financial"]["max_spend"] == 500.0


# ===========================================================================
# 4. Constraint enforcement correctness
# ===========================================================================


class TestConstraintEnforcementCorrectness:
    """Verify constraint enforcement verdicts are correct."""

    def test_strict_template_blocks_delete(self, key_manager):
        """Create session with strict template, evaluate 'delete' action,
        verify BLOCKED."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.session import SessionManager
        from praxis.trust.gradient import GradientLevel

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-strict-block",
            domain="coc",
            constraint_template="strict",
        )

        enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"],
        )
        verdict = enforcer.evaluate(action="delete", resource="/src/main.py")
        assert verdict.level == GradientLevel.BLOCKED

    def test_permissive_template_allows_delete(self, key_manager):
        """Create session with permissive template, evaluate 'delete' action,
        verify it is not BLOCKED (AUTO_APPROVED or FLAGGED)."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.session import SessionManager
        from praxis.trust.gradient import GradientLevel

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-permissive-delete",
            domain="coc",
            constraint_template="permissive",
        )

        enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"],
        )
        verdict = enforcer.evaluate(action="delete", resource="/src/main.py")

        # Permissive allows all actions including delete
        assert verdict.level in (
            GradientLevel.AUTO_APPROVED,
            GradientLevel.FLAGGED,
        )

    def test_financial_spend_flagged_then_blocked(self, key_manager):
        """Record spend of $9.50 on a $10.00 limit -> FLAGGED. Another
        $1.00 -> BLOCKED."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.session import SessionManager
        from praxis.trust.gradient import GradientLevel

        # Use the hardcoded strict template ($10.00 limit)
        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-spend-tracking",
            domain="coc",
            constraint_template="strict",
        )

        enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"],
        )

        # Record $9.50 spend (95% utilization -> HELD, per gradient thresholds)
        enforcer.record_spend(9.50)

        # Evaluate: financial utilization is 9.50/10.0 = 95% -> HELD
        verdict1 = enforcer.evaluate(action="read", resource="/src/main.py")
        # At 95%, it is at HELD level (>=90%)
        assert verdict1.level in (GradientLevel.HELD, GradientLevel.FLAGGED)

        # Record another $1.00 -> total $10.50 (exceeds $10.00 limit)
        enforcer.record_spend(1.00)
        verdict2 = enforcer.evaluate(action="read", resource="/src/main.py")
        assert verdict2.level == GradientLevel.BLOCKED

    def test_temporal_constraint_computation_correctness(self):
        """Test temporal constraint: create enforcer with 1-minute max,
        verify the math is correct. A freshly-created enforcer should have
        near-zero elapsed time -> AUTO_APPROVED."""
        from praxis.core.constraint import ConstraintEnforcer

        constraints = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 1, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"]},
            "communication": {"allowed_channels": ["internal"]},
        }

        # Fresh enforcer: elapsed ~0 seconds, utilization ~0%
        enforcer = ConstraintEnforcer(constraints)
        enforcer.evaluate(action="read", resource="/src/file.py")

        # Temporal utilization should be near zero (just created)
        status = enforcer.get_status()
        assert status["temporal"]["elapsed_minutes"] < 0.1  # Less than 6 seconds
        assert status["temporal"]["level"] == "auto_approved"

        # Now test with pre-set elapsed time at 95% of 1 minute (0.95 min)
        constraints_near_limit = {
            "financial": {"max_spend": 100.0, "current_spend": 0.0},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 1, "elapsed_minutes": 0.95},
            "data_access": {"allowed_paths": ["/src/"]},
            "communication": {"allowed_channels": ["internal"]},
        }

        enforcer2 = ConstraintEnforcer(constraints_near_limit)
        status2 = enforcer2.get_status()
        # 0.95 min elapsed out of 1 min = 95% -> HELD
        assert status2["temporal"]["level"] == "held"


# ===========================================================================
# 5. Security regression
# ===========================================================================


class TestSecurityRegression:
    """Security regression tests for the backend."""

    def test_sql_injection_in_column_name_rejected(self):
        """Attempt to create a record with SQL injection in a column name.
        db_ops._validate_columns must raise ValueError."""
        from praxis.persistence.db_ops import _validate_columns

        with pytest.raises(ValueError, match="Invalid column name"):
            _validate_columns(["id; DROP TABLE sessions"])

    def test_sql_injection_in_db_create_rejected(self):
        """Attempting db_create with an injected key should raise ValueError."""
        from praxis.persistence.db_ops import db_create

        with pytest.raises(ValueError, match="Invalid column name"):
            db_create(
                "Session",
                {"id; DROP TABLE sessions": "hack", "workspace_id": "ws-hack"},
            )

    def test_rate_limiter_blocks_after_5_attempts(self):
        """Verify that the rate limiter blocks after 5 attempts within
        the window."""
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=5, window_seconds=60)

        # 5 attempts pass
        for i in range(5):
            assert limiter.check("attacker-ip") is True, f"Attempt {i+1} should pass"

        # 6th is blocked
        assert limiter.check("attacker-ip") is False
        # 7th is also blocked
        assert limiter.check("attacker-ip") is False

        # Different key is unaffected
        assert limiter.check("legit-ip") is True

    def test_is_tightening_rejects_adding_new_dimensions(self, sample_constraints):
        """Verify that _is_tightening rejects constraints that add new
        dimensions not in the original envelope."""
        from praxis.core.session import _is_tightening

        # Adding a new dimension should fail
        with_new_dim = dict(sample_constraints)
        with_new_dim["mystery_dimension"] = {"max_mystery": 10}

        assert _is_tightening(sample_constraints, with_new_dim) is False

        # Confirm that the original vs itself is True (identity)
        assert _is_tightening(sample_constraints, sample_constraints) is True

        # Confirm that removing a dimension is still considered tightening
        # (fewer dimensions = fewer surfaces to check)
        without_comm = {k: v for k, v in sample_constraints.items() if k != "communication"}
        assert _is_tightening(sample_constraints, without_comm) is True
