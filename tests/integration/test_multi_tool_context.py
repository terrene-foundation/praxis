# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Test that trust context (session, constraints, audit chain) is consistent
across CLI, MCP, and API access paths.

Trust context must be identical regardless of which entry point accesses it.
A session created via SessionManager (the CLI path) must be visible and
consistent when accessed via API handlers (the REST path) or when constraint
enforcement is applied (the MCP path). This is a fundamental invariant of
Praxis: there is one source of truth, multiple access paths.
"""

from __future__ import annotations


class TestMultiToolTrustContext:
    """Verify trust context consistency across CLI, MCP, and API paths."""

    def test_session_visible_from_all_paths(self, key_manager):
        """Create session via SessionManager, verify visible via API handlers."""
        from praxis.api.handlers import get_session_handler, list_sessions_handler
        from praxis.core.session import SessionManager

        # Create session via SessionManager (CLI path)
        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-multi", domain="coc")
        session_id = session["session_id"]

        # Access via API handler (REST path)
        api_result = get_session_handler(session_manager=mgr, session_id=session_id)
        assert "error" not in api_result
        assert api_result["session_id"] == session_id
        assert api_result["domain"] == "coc"

        # Verify constraint envelope is identical
        assert api_result["constraint_envelope"] == session["constraint_envelope"]

        # Verify visible in list (another API path)
        list_result = list_sessions_handler(session_manager=mgr, workspace_id="ws-multi")
        assert "error" not in list_result
        assert any(s["session_id"] == session_id for s in list_result["sessions"])

    def test_constraints_identical_across_paths(self, key_manager):
        """Constraints must be the same whether accessed from CLI or API."""
        from praxis.api.handlers import get_constraints_handler
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-multi", domain="coc")

        api_constraints = get_constraints_handler(
            session_manager=mgr, session_id=session["session_id"]
        )
        assert "error" not in api_constraints
        assert api_constraints["constraint_envelope"] == session["constraint_envelope"]

    def test_deliberation_visible_across_paths(self, key_manager):
        """Decisions recorded via one path must be visible from another."""
        from praxis.api.handlers import timeline_handler
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-multi", domain="coc")

        # Record decision via direct engine (CLI path)
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        engine.record_decision(
            decision="Use REST API",
            rationale="Standard web protocol",
        )

        # Access timeline via handler (API path)
        timeline = timeline_handler(engine=engine, record_type=None)
        assert "error" not in timeline
        assert timeline["total"] >= 1
        assert any("Use REST API" in str(r) for r in timeline["records"])

    def test_audit_chain_consistent_across_paths(self, key_manager):
        """Audit chain length must match regardless of access path."""
        from praxis.api.handlers import get_chain_handler
        from praxis.core.session import SessionManager
        from praxis.trust.audit import AuditChain

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-multi", domain="coc")

        # Create audit chain and add anchors (trust path)
        chain = AuditChain(
            session_id=session["session_id"],
            key_id="test-key",
            key_manager=key_manager,
        )
        chain.append(action="test_action", actor="human", result="auto_approved")
        chain.append(action="test_action_2", actor="ai", result="flagged")

        # Access via handler (API path)
        chain_status = get_chain_handler(audit_chain=chain)
        assert "error" not in chain_status
        assert chain_status["chain_length"] == 2
        assert chain_status["valid"] is True
        assert chain_status["breaks"] == []

    def test_constraint_evaluation_consistent(self, key_manager):
        """Identical constraint envelopes must produce identical verdicts."""
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-multi",
            domain="coc",
            constraint_template="strict",
        )

        # Direct evaluation (CLI path)
        enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"],
        )
        direct_verdict = enforcer.evaluate(action="delete", resource="/src/main.py")

        # Create second enforcer with same envelope (simulating MCP path)
        mcp_enforcer = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session["session_id"] + "-mcp",
        )
        mcp_verdict = mcp_enforcer.evaluate(action="delete", resource="/src/main.py")

        # Same envelope must yield same verdict
        assert direct_verdict.level == mcp_verdict.level
        assert direct_verdict.dimension == mcp_verdict.dimension

    def test_multiple_operations_same_session(self, key_manager):
        """Multiple operations through different paths maintain consistency."""
        from praxis.api.handlers import (
            get_constraints_handler,
            get_session_handler,
            timeline_handler,
        )
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager

        # Setup
        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-multi-ops", domain="coc")
        sid = session["session_id"]

        engine = DeliberationEngine(
            session_id=sid, key_manager=key_manager, key_id="test-key"
        )
        enforcer = ConstraintEnforcer(
            session["constraint_envelope"], session_id=sid
        )

        # Record several decisions (CLI path)
        engine.record_decision(
            decision="Use microservices",
            rationale="Team expertise",
            actor="human",
        )
        engine.record_decision(
            decision="Deploy to Kubernetes",
            rationale="Scalability",
            actor="human",
        )
        engine.record_observation(
            observation="Load tests pass",
            actor="ai",
        )

        # Evaluate constraints (CLI path)
        enforcer.evaluate(action="read", resource="/src/app.py")
        enforcer.evaluate(action="write", resource="/src/config.py")

        # Verify session via API
        api_session = get_session_handler(session_manager=mgr, session_id=sid)
        assert api_session["session_id"] == sid
        assert api_session["state"] == "active"

        # Verify constraints via API
        api_constraints = get_constraints_handler(session_manager=mgr, session_id=sid)
        assert api_constraints["constraint_envelope"] == session["constraint_envelope"]

        # Verify timeline via API
        api_timeline = timeline_handler(engine=engine, record_type=None)
        assert api_timeline["total"] == 3

        # Verify decisions are in order (decision text is inside content dict)
        records = api_timeline["records"]
        assert "Use microservices" in str(records[0].get("content", {}))
        assert "Deploy to Kubernetes" in str(records[1].get("content", {}))

    def test_chain_integrity_after_cross_path_operations(self, key_manager):
        """Audit chain remains intact after operations from different paths."""
        from praxis.api.handlers import get_chain_handler
        from praxis.core.session import SessionManager
        from praxis.trust.audit import AuditChain

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-chain-test", domain="coc")
        sid = session["session_id"]

        # Build chain from "CLI path"
        chain = AuditChain(
            session_id=sid, key_id="test-key", key_manager=key_manager
        )
        chain.append(action="read", actor="human", result="auto_approved")
        chain.append(action="write", actor="ai", result="auto_approved")
        chain.append(action="execute", actor="human", result="flagged")

        # Verify via "API path"
        status = get_chain_handler(audit_chain=chain)
        assert status["chain_length"] == 3
        assert status["valid"] is True

        # Build a second AuditChain instance for the same session (simulates
        # a new MCP path reconnecting to the same session)
        chain2 = AuditChain(
            session_id=sid, key_id="test-key", key_manager=key_manager
        )
        # The new instance should see the same chain from the database
        assert chain2.length == 3

        # Append from the new instance and verify integrity across both
        chain2.append(action="deploy", actor="human", result="auto_approved")
        assert chain2.length == 4

        # Original chain variable should also see 4 (same DB)
        assert chain.length == 4

        # Full integrity check
        final_status = get_chain_handler(audit_chain=chain)
        assert final_status["chain_length"] == 4
        assert final_status["valid"] is True
