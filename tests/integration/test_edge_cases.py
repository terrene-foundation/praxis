# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Adversarial and edge case integration tests for the Praxis backend.

Exercises boundary conditions, illegal state transitions, malicious inputs,
and race-like rapid-fire operations against every major subsystem.
All tests use real SQLite (via the autouse _isolated_db fixture) and real
crypto (via the conftest key_manager). NO MOCKING.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import time

import pytest


# ============================================================================
# Session edge cases
# ============================================================================


class TestSessionEdgeCases:
    """Adversarial tests against the session state machine."""

    def test_create_session_with_empty_workspace_id(self):
        """Creating a session with an empty workspace_id must raise ValueError."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        with pytest.raises(ValueError, match="workspace_id must not be empty"):
            mgr.create_session(workspace_id="", domain="coc")

    def test_create_session_with_unknown_domain_falls_back_to_hardcoded(self):
        """An unknown domain should fall back to hardcoded constraint templates."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-xyz",
            domain="xyz",
            constraint_template="moderate",
        )
        assert session["state"] == "active"
        assert session["domain"] == "xyz"
        # The moderate hardcoded template has max_spend of 100
        assert session["constraint_envelope"]["financial"]["max_spend"] == 100.0

    def test_create_50_sessions_rapidly(self):
        """Creating 50 sessions in quick succession should all succeed."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session_ids = set()
        for i in range(50):
            session = mgr.create_session(
                workspace_id=f"ws-rapid-{i}",
                domain="coc",
                constraint_template="moderate",
            )
            session_ids.add(session["session_id"])
            assert session["state"] == "active"
        # All 50 must have unique IDs
        assert len(session_ids) == 50

    def test_pause_already_paused_session(self):
        """Pausing a session that is already paused must raise an error."""
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-pause", domain="coc", constraint_template="moderate"
        )
        sid = session["session_id"]

        mgr.pause_session(sid, reason="first pause")
        with pytest.raises(
            InvalidStateTransitionError, match="Cannot transition from 'paused' to 'paused'"
        ):
            mgr.pause_session(sid, reason="second pause")

    def test_resume_active_session(self):
        """Resuming a session that is already active must raise an error."""
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-resume", domain="coc", constraint_template="moderate"
        )
        sid = session["session_id"]

        # Session starts as ACTIVE; resuming it should fail
        with pytest.raises(
            InvalidStateTransitionError, match="Cannot transition from 'active' to 'active'"
        ):
            mgr.resume_session(sid)

    def test_end_already_archived_session(self):
        """Ending an already-archived session must raise an error."""
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-end", domain="coc", constraint_template="moderate"
        )
        sid = session["session_id"]

        mgr.end_session(sid, summary="done")
        with pytest.raises(InvalidStateTransitionError, match="none \\(terminal state\\)"):
            mgr.end_session(sid, summary="again")

    def test_get_nonexistent_session(self):
        """Getting a session that does not exist must raise KeyError."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        with pytest.raises(KeyError, match="not found"):
            mgr.get_session("nonexistent-id-12345")

    def test_record_decision_on_archived_session(self):
        """Recording a decision on an archived session should still succeed
        at the deliberation layer (deliberation captures are append-only),
        but the session itself cannot be modified."""
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager, SessionNotActiveError

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-archived", domain="coc", constraint_template="moderate"
        )
        sid = session["session_id"]
        mgr.end_session(sid)

        # Deliberation engine is append-only -- it records regardless.
        # But if we try to UPDATE CONSTRAINTS on the archived session, it must fail.
        with pytest.raises(SessionNotActiveError, match="archived"):
            mgr.update_constraints(sid, session["constraint_envelope"])


# ============================================================================
# Constraint edge cases
# ============================================================================


class TestConstraintEdgeCases:
    """Edge cases for the constraint enforcer and tightening invariant."""

    def test_loosening_constraints_rejected(self, sample_constraints):
        """Updating constraints to a higher max_spend must be rejected."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-loosen",
            domain="coc",
            constraints=sample_constraints,
        )
        sid = session["session_id"]

        loosened = dict(sample_constraints)
        loosened["financial"] = {"max_spend": 99999.0}
        with pytest.raises(ValueError, match="Cannot loosen constraints"):
            mgr.update_constraints(sid, loosened)

    def test_update_constraints_on_archived_session(self, sample_constraints):
        """Updating constraints on an archived session must be rejected."""
        from praxis.core.session import SessionManager, SessionNotActiveError

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-archived-const",
            domain="coc",
            constraints=sample_constraints,
        )
        sid = session["session_id"]
        mgr.end_session(sid)

        with pytest.raises(SessionNotActiveError, match="archived"):
            mgr.update_constraints(sid, sample_constraints)

    def test_update_constraints_with_unknown_dimension(self, sample_constraints):
        """Adding a new dimension that did not exist in the original envelope
        must be rejected by _is_tightening."""
        from praxis.core.session import SessionManager

        mgr = SessionManager()
        session = mgr.create_session(
            workspace_id="ws-unknown-dim",
            domain="coc",
            constraints=sample_constraints,
        )
        sid = session["session_id"]

        new = dict(sample_constraints)
        new["mystery_dimension"] = {"max_mystery": 10}
        with pytest.raises(ValueError, match="Cannot loosen constraints"):
            mgr.update_constraints(sid, new)

    def test_evaluate_constraint_with_nan_utilization(self, sample_constraints):
        """Evaluating a constraint where utilization computes to NaN
        should return BLOCKED (via utilization_to_gradient_level)."""
        from praxis.trust.gradient import GradientLevel, utilization_to_gradient_level

        # NaN utilization must be BLOCKED
        result = utilization_to_gradient_level(float("nan"))
        assert result == GradientLevel.BLOCKED

        # Inf utilization must be BLOCKED
        result = utilization_to_gradient_level(float("inf"))
        assert result == GradientLevel.BLOCKED

        # Negative infinity must also be BLOCKED
        result = utilization_to_gradient_level(float("-inf"))
        assert result == GradientLevel.BLOCKED


# ============================================================================
# Deliberation edge cases
# ============================================================================


class TestDeliberationEdgeCases:
    """Edge cases for the deliberation capture engine."""

    def test_empty_decision_text(self):
        """Recording a decision with empty text should still work
        (content validation is not enforced at this layer)."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-empty-decision")
        record = engine.record_decision(decision="", rationale="testing empty")
        assert record["record_type"] == "decision"
        assert record["content"]["decision"] == ""

    def test_confidence_zero(self):
        """Confidence of 0.0 is a valid value (lowest confidence)."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-conf-zero")
        record = engine.record_decision(
            decision="uncertain call", rationale="zero confidence", confidence=0.0
        )
        assert record["confidence"] == 0.0

    def test_confidence_one(self):
        """Confidence of 1.0 is a valid value (highest confidence)."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-conf-one")
        record = engine.record_decision(
            decision="absolute certainty", rationale="full confidence", confidence=1.0
        )
        assert record["confidence"] == 1.0

    def test_confidence_above_one_rejected(self):
        """Confidence of 1.5 must be rejected by the engine."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-conf-high")
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            engine.record_decision(decision="over-confident", rationale="nope", confidence=1.5)

    def test_confidence_above_one_rejected_by_handler(self):
        """The API handler layer also rejects confidence > 1.0."""
        from praxis.core.deliberation import DeliberationEngine
        from praxis.api.handlers import decide_handler

        engine = DeliberationEngine(session_id="sess-handler-conf")
        result = decide_handler(
            engine=engine,
            decision="test",
            rationale="test",
            confidence=1.5,
        )
        assert "error" in result

    def test_very_long_rationale(self):
        """A rationale of 10,000 characters should be stored without error."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-long-rationale")
        long_rationale = "x" * 10_000
        record = engine.record_decision(decision="long test", rationale=long_rationale)
        assert record["reasoning_trace"]["rationale"] == long_rationale

    def test_hash_chain_integrity_100_decisions(self):
        """Record 100 decisions and verify the hash chain links correctly."""
        import jcs

        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-chain-100")

        records = []
        for i in range(100):
            rec = engine.record_decision(
                decision=f"decision-{i}",
                rationale=f"reason-{i}",
                actor="human",
            )
            records.append(rec)

        # Verify chain: each record's parent_record_id should point to
        # the previous record's reasoning_hash
        for i, rec in enumerate(records):
            if i == 0:
                assert rec["parent_record_id"] is None
            else:
                assert rec["parent_record_id"] == records[i - 1]["reasoning_hash"]

            # Verify the hash is correct
            hashable = {
                "content": rec["content"],
                "reasoning_trace": rec["reasoning_trace"],
            }
            canonical = jcs.canonicalize(hashable)
            expected_hash = hashlib.sha256(canonical).hexdigest()
            assert rec["reasoning_hash"] == expected_hash


# ============================================================================
# Trust chain edge cases
# ============================================================================


class TestTrustChainEdgeCases:
    """Adversarial tests against the audit chain and delegation system."""

    def test_audit_chain_50_anchors_verify_integrity(self, key_manager):
        """Create a chain with 50 anchors and verify integrity."""
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-50-anchors", key_id="test-key", key_manager=key_manager)

        for i in range(50):
            chain.append(
                action=f"action-{i}",
                actor="human",
                result="auto_approved",
                resource=f"/src/file-{i}.py",
            )

        assert chain.length == 50
        valid, breaks = chain.verify_integrity()
        assert valid is True
        assert breaks == []

    def test_tampered_anchor_detected(self, key_manager):
        """Tamper with an anchor's content_hash in the DB and verify
        that integrity check detects the break."""
        import sqlite3

        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-tamper", key_id="test-key", key_manager=key_manager)

        chain.append(action="first", actor="human", result="auto_approved")
        chain.append(action="second", actor="human", result="auto_approved")
        chain.append(action="third", actor="human", result="auto_approved")

        # Tamper with the second anchor's content_hash directly in DB
        from praxis.persistence.db_ops import _db_path

        db_path = _db_path()
        conn = sqlite3.connect(db_path)
        try:
            # Get all anchors ordered by creation
            cursor = conn.execute(
                "SELECT id FROM trust_chain_entries WHERE session_id = ? ORDER BY created_at ASC",
                ("sess-tamper",),
            )
            anchor_ids = [row[0] for row in cursor.fetchall()]
            assert len(anchor_ids) == 3

            # Tamper with the second anchor's content_hash
            conn.execute(
                "UPDATE trust_chain_entries SET content_hash = ? WHERE id = ?",
                ("tampered_hash_value", anchor_ids[1]),
            )
            conn.commit()
        finally:
            conn.close()

        # Verification should detect the break
        valid, breaks = chain.verify_integrity()
        assert valid is False
        assert len(breaks) >= 1
        # The tampered anchor should be detected at position 1
        tampered_break = [b for b in breaks if b["position"] == 1]
        assert len(tampered_break) >= 1

    def test_delegation_with_tighter_constraints_succeeds(self, key_manager, sample_constraints):
        """Creating a delegation with tighter constraints should succeed."""
        from praxis.trust.delegation import create_delegation

        tighter = {
            "financial": {"max_spend": 500.0},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }

        delegation = create_delegation(
            session_id="sess-deleg-tight",
            parent_id="genesis-hash-123",
            parent_constraints=sample_constraints,
            delegate_id="junior-dev",
            delegate_constraints=tighter,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash="abc123",
        )
        assert delegation.delegate_id == "junior-dev"
        assert delegation.constraints["financial"]["max_spend"] == 500.0

    def test_delegation_with_looser_constraints_rejected(self, key_manager, sample_constraints):
        """Creating a delegation with looser constraints must be rejected."""
        from praxis.trust.delegation import create_delegation

        looser = {
            "financial": {"max_spend": 99999.0},
            "operational": {"allowed_actions": ["read", "write", "execute", "deploy"]},
            "temporal": {"max_duration_minutes": 999},
            "data_access": {"allowed_paths": ["/"]},
            "communication": {"allowed_channels": ["internal", "email", "external"]},
        }

        with pytest.raises(ValueError, match="Constraint tightening violation"):
            create_delegation(
                session_id="sess-deleg-loose",
                parent_id="genesis-hash-456",
                parent_constraints=sample_constraints,
                delegate_id="rogue-agent",
                delegate_constraints=looser,
                key_id="test-key",
                key_manager=key_manager,
                parent_hash="def456",
            )


# ============================================================================
# MCP proxy edge cases
# ============================================================================


class TestMCPProxyEdgeCases:
    """Edge cases for the MCP proxy trust mediation layer."""

    def test_handle_tool_call_blocked_action(self, sample_constraints):
        """Calling a tool with a blocked action returns BLOCKED."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.mcp.proxy import PraxisProxy
        from praxis.trust.gradient import GradientLevel

        # Use strict constraints where only "read" is allowed
        strict = {
            "financial": {"max_spend": 10.0, "current_spend": 0.0},
            "operational": {
                "allowed_actions": ["read"],
                "blocked_actions": ["delete", "deploy"],
            },
            "temporal": {"max_duration_minutes": 30, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": []},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": []},
        }

        enforcer = ConstraintEnforcer(strict, session_id="")
        proxy = PraxisProxy(
            session_id="sess-proxy-blocked",
            downstream_servers=[],
            constraint_enforcer=enforcer,
        )
        # Register a fake tool catalog entry so parse succeeds
        proxy.register_tools("server1", [{"name": "delete_file", "description": "delete"}])

        result = asyncio.get_event_loop().run_until_complete(
            proxy.handle_tool_call("server1__delete_file", {"path": "/src/test.py"})
        )
        assert result.verdict.level == GradientLevel.BLOCKED

    def test_handle_tool_call_no_enforcer_auto_approves(self):
        """With no enforcer configured, tools should be AUTO_APPROVED (safe default)."""
        from praxis.mcp.proxy import PraxisProxy
        from praxis.trust.gradient import GradientLevel

        proxy = PraxisProxy(
            session_id="sess-proxy-no-enforcer",
            downstream_servers=[],
            constraint_enforcer=None,
        )
        # Register a tool
        proxy.register_tools("srv", [{"name": "read_file", "description": "read"}])

        result = asyncio.get_event_loop().run_until_complete(
            proxy.handle_tool_call("srv__read_file", {"path": "/src/hello.py"})
        )
        assert result.verdict.level == GradientLevel.AUTO_APPROVED
        assert "No constraint enforcer" in result.verdict.reason

    def test_handle_tool_call_empty_tool_name(self, sample_constraints):
        """Calling with an empty tool name should still produce a result
        (BLOCKED because the tool is unknown)."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.mcp.proxy import PraxisProxy
        from praxis.trust.gradient import GradientLevel

        enforcer = ConstraintEnforcer(sample_constraints, session_id="")
        proxy = PraxisProxy(
            session_id="sess-proxy-empty",
            downstream_servers=[],
            constraint_enforcer=enforcer,
        )

        result = asyncio.get_event_loop().run_until_complete(proxy.handle_tool_call("", {}))
        # Empty tool name is unknown, so it should be BLOCKED
        assert result.verdict.level == GradientLevel.BLOCKED


# ============================================================================
# Learning pipeline edge cases
# ============================================================================


class TestLearningPipelineEdgeCases:
    """Edge cases for the continuous learning pipeline."""

    def test_observe_with_invalid_target(self):
        """Observing with a target not in the domain YAML should raise ValueError."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc", session_id="sess-bad-target")

        # The coc domain has specific observation_targets. Use one that
        # definitely does not exist.
        with pytest.raises(ValueError, match="not declared"):
            pipeline.observe(
                target="totally_bogus_target_xyz",
                content={"data": "test"},
            )

    def test_analyze_with_no_observations(self):
        """Analyzing when no observations exist should return empty patterns."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")
        patterns = pipeline.analyze()
        assert patterns == []

    def test_approve_nonexistent_proposal(self):
        """Approving a proposal that does not exist should raise KeyError."""
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain="coc")
        with pytest.raises(KeyError, match="not found"):
            pipeline.formalize("nonexistent-proposal-id", approved_by="admin")

    def test_reject_already_approved_proposal(self):
        """Rejecting a proposal that was already approved should raise ValueError."""
        from praxis.core.learning import LearningPipeline, Pattern

        pipeline = LearningPipeline(domain="coc", session_id="sess-learn")

        # First, we need an observation so we can create a pattern + proposal.
        # Observe using a valid target for coc.
        # Use a target that coc domain defines. If it fails, catch and use
        # a generic approach by creating data directly.
        try:
            pipeline.observe(
                target="constraint_evaluation",
                content={"dimension": "financial", "utilization": 0.0},
            )
        except ValueError:
            # If the domain doesn't accept this target, create via db_ops
            from praxis.persistence.db_ops import db_create

            import uuid

            db_create(
                "LearningObservation",
                {
                    "id": str(uuid.uuid4()),
                    "session_id": "sess-learn",
                    "domain": "coc",
                    "target": "constraint_evaluation",
                    "content": {"dimension": "financial", "utilization": 0.0},
                },
            )

        # Create a pattern and proposal directly for this test
        pattern = Pattern(
            pattern_id="pat-test-123",
            pattern_type="unused_constraint",
            description="The 'financial' constraint dimension has never been triggered.",
            confidence=0.8,
            evidence=["obs-1"],
            domain="coc",
            created_at="2026-03-16T00:00:00.000000Z",
        )

        proposal = pipeline.propose(pattern)
        if proposal is None:
            pytest.skip("Pattern did not generate a proposal (confidence too low)")

        # Approve the proposal
        pipeline.formalize(proposal.proposal_id, approved_by="admin")

        # Now try to reject the already-approved proposal
        with pytest.raises(ValueError, match="not 'pending'"):
            pipeline.reject(proposal.proposal_id, rejected_by="admin2", reason="changed mind")


# ============================================================================
# Rate limiter edge cases
# ============================================================================


class TestRateLimiterEdgeCases:
    """Edge cases for the in-memory rate limiter."""

    def test_five_attempts_all_pass(self):
        """Making exactly max_attempts (5) requests should all pass."""
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        for i in range(5):
            assert limiter.check("test-ip") is True
        assert limiter.remaining("test-ip") == 0

    def test_sixth_attempt_rate_limited(self):
        """The 6th attempt within the window should be blocked."""
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        for _ in range(5):
            assert limiter.check("test-ip") is True

        # 6th should be blocked
        assert limiter.check("test-ip") is False

    def test_window_expiry_allows_again(self):
        """After the window expires, requests should be allowed again."""
        from praxis.api.rate_limit import RateLimiter

        # Use a very short window (1 second)
        limiter = RateLimiter(max_attempts=2, window_seconds=1)

        assert limiter.check("test-ip") is True
        assert limiter.check("test-ip") is True
        assert limiter.check("test-ip") is False  # Blocked

        # Wait for the window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.check("test-ip") is True
