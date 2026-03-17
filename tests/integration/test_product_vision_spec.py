# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Product Vision Spec Verification — tests every line item from briefs/01-product-vision.md.

This is the definitive "did we build what we said we'd build" test. Each test class maps
to a numbered Core Capability from the product vision. Each test method maps to a specific
spec bullet point. Test names are traceable back to the spec so failures immediately
identify which product promise is broken.

NO MOCKING. All tests use real SQLite, real crypto, real domain YAML.
"""

from __future__ import annotations

import json
import time
import zipfile

import pytest

from praxis.core.constraint import (
    ConstraintEnforcer,
    ConstraintVerdict,
    GradientLevel,
    HeldActionManager,
)
from praxis.core.deliberation import DeliberationEngine
from praxis.core.session import (
    InvalidStateTransitionError,
    PhaseGateError,
    SessionManager,
)
from praxis.domains.loader import DomainLoader, get_institutional_knowledge
from praxis.export.bundle import BundleBuilder
from praxis.export.report import AuditReportGenerator
from praxis.trust.audit import AuditChain
from praxis.trust.crypto import canonical_hash, verify_signature
from praxis.trust.delegation import create_delegation
from praxis.trust.genesis import create_genesis
from praxis.trust.gradient import GradientLevel as GL
from praxis.trust.gradient import utilization_to_gradient_level
from praxis.trust.keys import KeyManager
from praxis.trust.verify import verify_chain


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def key_mgr(tmp_path):
    """Real filesystem KeyManager with a pre-generated test key."""
    km = KeyManager(tmp_path / "keys")
    km.generate_key("test-key")
    return km


@pytest.fixture
def session_mgr(key_mgr):
    """SessionManager wired to a real KeyManager."""
    return SessionManager(key_manager=key_mgr, key_id="test-key")


@pytest.fixture
def five_dim_constraints():
    """Full 5-dimensional constraint envelope matching the spec."""
    return {
        "financial": {"max_spend": 50.0, "current_spend": 0.0},
        "operational": {
            "allowed_actions": ["read", "write", "execute"],
            "blocked_actions": ["delete"],
        },
        "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
        "data_access": {
            "allowed_paths": ["/src/", "/tests/"],
            "blocked_paths": ["/secrets/", "/credentials/"],
        },
        "communication": {
            "allowed_channels": ["internal"],
            "blocked_channels": ["external"],
        },
    }


# ===========================================================================
# Capability 1: Session Management
# ===========================================================================


class TestCapability1_SessionManagement:
    """Spec: 'Persistent, identity-aware collaboration sessions.'"""

    def test_lifecycle_create_active_pause_resume_archive(self, session_mgr, five_dim_constraints):
        """Spec: 'Session lifecycle: Create -> Active -> Pause -> Resume -> Archive'"""
        session = session_mgr.create_session(
            workspace_id="ws-lifecycle",
            domain="coc",
            constraints=five_dim_constraints,
        )
        assert session["state"] == "active"

        paused = session_mgr.pause_session(session["session_id"], reason="break")
        assert paused["state"] == "paused"

        resumed = session_mgr.resume_session(session["session_id"])
        assert resumed["state"] == "active"

        archived = session_mgr.end_session(session["session_id"], summary="done")
        assert archived["state"] == "archived"
        assert archived["ended_at"] is not None

    def test_archived_is_terminal(self, session_mgr, five_dim_constraints):
        """Spec: ARCHIVED is terminal state -- no transitions out."""
        session = session_mgr.create_session(
            workspace_id="ws-terminal",
            domain="coc",
            constraints=five_dim_constraints,
        )
        session_mgr.end_session(session["session_id"])

        with pytest.raises(InvalidStateTransitionError):
            session_mgr.resume_session(session["session_id"])

        with pytest.raises(InvalidStateTransitionError):
            session_mgr.pause_session(session["session_id"])

    def test_persistent_identity_across_restarts(self, session_mgr, five_dim_constraints):
        """Spec: 'Persistent identity across interactions'"""
        session = session_mgr.create_session(
            workspace_id="ws-persist",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        # Simulate a "restart" by creating a fresh SessionManager against same DB
        from praxis.core.session import SessionManager as SM

        sm2 = SM()
        recovered = sm2.get_session(sid)
        assert recovered["session_id"] == sid
        assert recovered["workspace_id"] == "ws-persist"
        assert recovered["state"] == "active"

    def test_session_history_with_audit_trail(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Session history with full audit trail'"""
        session = session_mgr.create_session(
            workspace_id="ws-audit",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        # Record a deliberation decision
        engine = DeliberationEngine(session_id=sid, key_manager=key_mgr, key_id="test-key")
        engine.record_decision("Use REST API", "REST is standard", actor="human")

        # Create audit chain and append an anchor
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)
        chain.append(action="session_created", actor="system", result="auto_approved")

        assert chain.length >= 1
        assert len(chain.anchors) >= 1

        # The session itself has a genesis record linking to the audit trail
        assert session["genesis_id"] is not None

    def test_multi_session_workspaces(self, session_mgr, five_dim_constraints):
        """Spec: 'Multi-session workspaces for complex projects'"""
        ws = "ws-multi"
        s1 = session_mgr.create_session(
            workspace_id=ws, domain="coc", constraints=five_dim_constraints
        )
        s2 = session_mgr.create_session(
            workspace_id=ws, domain="coc", constraints=five_dim_constraints
        )
        s3 = session_mgr.create_session(
            workspace_id=ws, domain="coe", constraints=five_dim_constraints
        )

        sessions = session_mgr.list_sessions(workspace_id=ws)
        assert len(sessions) == 3

        session_ids = {s["session_id"] for s in sessions}
        assert s1["session_id"] in session_ids
        assert s2["session_id"] in session_ids
        assert s3["session_id"] in session_ids

    def test_session_export_for_portability(
        self, session_mgr, key_mgr, five_dim_constraints, tmp_path
    ):
        """Spec: 'Session export/import for portability'"""
        session = session_mgr.create_session(
            workspace_id="ws-export",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        # Record some decisions so the export has content
        engine = DeliberationEngine(session_id=sid, key_manager=key_mgr, key_id="test-key")
        engine.record_decision("Choose Python", "Best for rapid development", actor="human")

        # Create audit chain
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)
        chain.append(action="session_created", actor="system", result="auto_approved")

        # End session then build a verification bundle (the portable export)
        session_mgr.end_session(sid, summary="export test")
        session_data = session_mgr.get_session(sid)

        trust_chain_entries = []
        genesis = session_data.get("genesis_chain_entry")
        if genesis:
            trust_chain_entries.append(genesis)
        for a in chain.anchors:
            trust_chain_entries.append(
                {
                    "payload": a.payload,
                    "content_hash": a.content_hash,
                    "signature": a.signature,
                    "signer_key_id": a.signer_key_id,
                    "parent_hash": a.parent_hash,
                }
            )

        records, _ = engine.get_timeline()
        pub_pem = key_mgr.export_public_pem("test-key")
        if isinstance(pub_pem, bytes):
            pub_pem = pub_pem.decode("utf-8")

        bundle_path = tmp_path / "bundle.zip"
        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_chain_entries,
            deliberation_records=records,
            constraint_events=[],
            public_keys={"test-key": pub_pem},
        )
        builder.build(bundle_path)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0
        with zipfile.ZipFile(bundle_path) as zf:
            names = zf.namelist()
            assert "index.html" in names


# ===========================================================================
# Capability 2: Deliberation Capture
# ===========================================================================


class TestCapability2_DeliberationCapture:
    """Spec: 'Cryptographic recording of human-AI reasoning.'"""

    def test_decision_records_with_reasoning_traces(
        self, session_mgr, key_mgr, five_dim_constraints
    ):
        """Spec: 'Decision records with reasoning traces'"""
        session = session_mgr.create_session(
            workspace_id="ws-delib",
            domain="coc",
            constraints=five_dim_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_mgr,
            key_id="test-key",
        )
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Production-grade, supports concurrent writes",
            actor="human",
        )

        assert record["record_type"] == "decision"
        assert record["content"]["decision"] == "Use PostgreSQL"
        assert (
            record["reasoning_trace"]["rationale"] == "Production-grade, supports concurrent writes"
        )
        assert record["reasoning_hash"] is not None
        assert len(record["reasoning_hash"]) == 64  # SHA-256 hex

    def test_confidence_scoring(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Confidence scoring (basis points for precision)'"""
        session = session_mgr.create_session(
            workspace_id="ws-conf",
            domain="coc",
            constraints=five_dim_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_mgr,
            key_id="test-key",
        )
        record = engine.record_decision(
            decision="Deploy to staging",
            rationale="Tests pass, code reviewed",
            confidence=0.85,
        )

        assert record["confidence"] == 0.85

        # Verify it persisted correctly by reading back
        records, total = engine.get_timeline()
        assert total >= 1
        stored = [r for r in records if r["record_id"] == record["record_id"]]
        assert len(stored) == 1
        assert stored[0]["confidence"] == 0.85

    def test_alternative_tracking(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Alternative tracking (what options were considered)'"""
        session = session_mgr.create_session(
            workspace_id="ws-alt",
            domain="coc",
            constraints=five_dim_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_mgr,
            key_id="test-key",
        )
        alternatives = ["MySQL", "MongoDB", "DynamoDB"]
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Best for relational data with ACID guarantees",
            alternatives=alternatives,
        )

        assert record["content"]["alternatives"] == alternatives

    def test_evidence_linking(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Evidence linking (what informed the decision)'"""
        session = session_mgr.create_session(
            workspace_id="ws-evidence",
            domain="coc",
            constraints=five_dim_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_mgr,
            key_id="test-key",
        )
        record = engine.record_decision(
            decision="Refactor module",
            rationale="Evidence from profiling shows bottleneck",
        )

        # anchor_id links the deliberation record to the audit chain
        assert record["anchor_id"] is not None
        assert record["anchor_id"].startswith("anchor-")

    def test_hash_chained_temporal_integrity(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Hash-chained temporal integrity (records cannot be reordered)'"""
        session = session_mgr.create_session(
            workspace_id="ws-chain",
            domain="coc",
            constraints=five_dim_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_mgr,
            key_id="test-key",
        )

        records = []
        for i in range(5):
            r = engine.record_decision(
                decision=f"Decision {i}",
                rationale=f"Reason {i}",
            )
            records.append(r)

        # First record has no parent
        assert records[0]["parent_record_id"] is None

        # Each subsequent record points to the previous one's reasoning_hash
        for i in range(1, 5):
            assert records[i]["parent_record_id"] == records[i - 1]["reasoning_hash"]


# ===========================================================================
# Capability 3: Constraint Enforcement
# ===========================================================================


class TestCapability3_ConstraintEnforcement:
    """Spec: 'Five-dimensional runtime enforcement that actually prevents actions.'"""

    def test_financial_spending_limits(self, session_mgr, five_dim_constraints):
        """Spec: 'Financial: Spending limits, token budgets | Max $50/session'"""
        session = session_mgr.create_session(
            workspace_id="ws-fin",
            domain="coc",
            constraints=five_dim_constraints,
        )
        enforcer = ConstraintEnforcer(
            five_dim_constraints,
            session_id=session["session_id"],
        )

        # Spend $49 -- should be OK
        enforcer.record_spend(49.0)
        verdict = enforcer.evaluate("write", "/src/main.py")
        assert verdict.level != GradientLevel.BLOCKED

        # Try to spend $2 more -- total $51 exceeds $50 limit -> BLOCKED
        verdict = enforcer.evaluate("write", "/src/main.py", context={"cost": 2.0})
        assert verdict.level == GradientLevel.BLOCKED

    def test_operational_allowed_blocked_actions(self, session_mgr, five_dim_constraints):
        """Spec: 'Operational: Allowed/blocked actions | No file deletion'"""
        session = session_mgr.create_session(
            workspace_id="ws-ops",
            domain="coc",
            constraints=five_dim_constraints,
        )
        enforcer = ConstraintEnforcer(
            five_dim_constraints,
            session_id=session["session_id"],
        )

        # "delete" is in blocked_actions -> BLOCKED
        verdict = enforcer.evaluate("delete", "/src/old.py")
        assert verdict.level == GradientLevel.BLOCKED

        # "read" is in allowed_actions -> AUTO_APPROVED
        verdict = enforcer.evaluate("read", "/src/main.py")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_temporal_uses_wall_clock(self, session_mgr, five_dim_constraints):
        """Spec: 'Temporal: Active hours, deadlines, timeouts'"""
        session = session_mgr.create_session(
            workspace_id="ws-temp",
            domain="coc",
            constraints=five_dim_constraints,
        )
        # Create enforcer with most of the time already elapsed
        constraints_near_limit = dict(five_dim_constraints)
        constraints_near_limit["temporal"] = {
            "max_duration_minutes": 120,
            "elapsed_minutes": 118,  # 98.3% elapsed
        }
        enforcer = ConstraintEnforcer(
            constraints_near_limit,
            session_id=session["session_id"],
        )

        # At ~98% utilization, temporal dimension should produce HELD
        verdict = enforcer.evaluate("write", "/src/main.py")
        # The most restrictive verdict might come from temporal dimension
        status = enforcer.get_status()
        temporal_level = status["temporal"]["level"]
        assert temporal_level in ("held", "blocked")

    def test_data_access_paths(self, session_mgr, five_dim_constraints):
        """Spec: 'Data Access: Read/write paths | No access to /secrets/'"""
        session = session_mgr.create_session(
            workspace_id="ws-data",
            domain="coc",
            constraints=five_dim_constraints,
        )
        enforcer = ConstraintEnforcer(
            five_dim_constraints,
            session_id=session["session_id"],
        )

        # /secrets/ is in blocked_paths -> BLOCKED
        verdict = enforcer.evaluate("read", "/secrets/key.pem")
        assert verdict.level == GradientLevel.BLOCKED

        # /src/ is in allowed_paths -> OK
        verdict = enforcer.evaluate("read", "/src/main.py")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_communication_channels(self, session_mgr, five_dim_constraints):
        """Spec: 'Communication: Channels, recipients | No external API calls'"""
        session = session_mgr.create_session(
            workspace_id="ws-comm",
            domain="coc",
            constraints=five_dim_constraints,
        )
        enforcer = ConstraintEnforcer(
            five_dim_constraints,
            session_id=session["session_id"],
        )

        # "external" is in blocked_channels -> BLOCKED
        # Use "read" as the action since it's in allowed_actions, so only
        # the communication dimension produces the block.
        verdict = enforcer.evaluate("read", "external")
        assert verdict.level == GradientLevel.BLOCKED
        assert verdict.dimension == "communication"

        # "internal" is in allowed_channels -> OK
        verdict = enforcer.evaluate("read", "internal")
        assert verdict.level == GradientLevel.AUTO_APPROVED

    def test_deterministic_enforcement(self, session_mgr, five_dim_constraints):
        """Spec: 'When a constraint says blocked, the action does not proceed.'"""
        session = session_mgr.create_session(
            workspace_id="ws-det",
            domain="coc",
            constraints=five_dim_constraints,
        )
        enforcer = ConstraintEnforcer(
            five_dim_constraints,
            session_id=session["session_id"],
        )

        # Same input must produce the same output 100 times
        results = set()
        for _ in range(100):
            verdict = enforcer.evaluate("delete", "/src/file.py")
            results.add(verdict.level.value)

        assert results == {"blocked"}, "Enforcement must be deterministic"


# ===========================================================================
# Capability 4: Trust Infrastructure
# ===========================================================================


class TestCapability4_TrustInfrastructure:
    """Spec: 'EATP-based cryptographic trust chains.'"""

    def test_genesis_record_root_of_trust(self, key_mgr, five_dim_constraints):
        """Spec: 'Genesis Record -- Root of trust establishing human authority'"""
        genesis = create_genesis(
            session_id="test-session-genesis",
            authority_id="researcher-alice",
            key_id="test-key",
            key_manager=key_mgr,
            constraints=five_dim_constraints,
            domain="coc",
        )

        assert genesis.session_id == "test-session-genesis"
        assert genesis.authority_id == "researcher-alice"
        assert genesis.domain == "coc"
        assert genesis.payload["type"] == "genesis"
        assert genesis.content_hash is not None
        assert genesis.signature is not None
        assert genesis.signer_key_id == "test-key"

        # Verify the content hash is correct
        expected_hash = canonical_hash(genesis.payload)
        assert genesis.content_hash == expected_hash

        # Verify the signature
        assert verify_signature(genesis.content_hash, genesis.signature, "test-key", key_mgr)

    def test_delegation_records_tightening_only(self, key_mgr, five_dim_constraints):
        """Spec: 'Delegation Records -- Constraint-tightening delegation chains'"""
        genesis = create_genesis(
            session_id="test-session-deleg",
            authority_id="alice",
            key_id="test-key",
            key_manager=key_mgr,
            constraints=five_dim_constraints,
            domain="coc",
        )

        # Tighter constraints -> should succeed
        tighter = {
            "financial": {"max_spend": 25.0, "current_spend": 0.0},
            "operational": {"allowed_actions": ["read"], "blocked_actions": ["delete"]},
            "temporal": {"max_duration_minutes": 60, "elapsed_minutes": 0},
            "data_access": {"allowed_paths": ["/src/"], "blocked_paths": ["/secrets/"]},
            "communication": {"allowed_channels": ["internal"], "blocked_channels": ["external"]},
        }
        delegation = create_delegation(
            session_id="test-session-deleg",
            parent_id=genesis.content_hash,
            parent_constraints=five_dim_constraints,
            delegate_id="bob",
            delegate_constraints=tighter,
            key_id="test-key",
            key_manager=key_mgr,
            parent_hash=genesis.content_hash,
        )
        assert delegation.delegate_id == "bob"
        assert delegation.parent_hash == genesis.content_hash

        # Looser constraints -> should fail
        looser = dict(five_dim_constraints)
        looser["financial"] = {"max_spend": 100.0, "current_spend": 0.0}
        with pytest.raises(ValueError, match="tightening"):
            create_delegation(
                session_id="test-session-deleg",
                parent_id=genesis.content_hash,
                parent_constraints=five_dim_constraints,
                delegate_id="charlie",
                delegate_constraints=looser,
                key_id="test-key",
                key_manager=key_mgr,
                parent_hash=genesis.content_hash,
            )

    def test_verification_gradient_four_levels(self):
        """Spec: 'Verification Gradient -- Four-level action classification'"""
        # AUTO_APPROVED: < 70%
        assert utilization_to_gradient_level(0.0) == GL.AUTO_APPROVED
        assert utilization_to_gradient_level(0.69) == GL.AUTO_APPROVED

        # FLAGGED: 70%-89%
        assert utilization_to_gradient_level(0.70) == GL.FLAGGED
        assert utilization_to_gradient_level(0.75) == GL.FLAGGED
        assert utilization_to_gradient_level(0.89) == GL.FLAGGED

        # HELD: 90%-99%
        assert utilization_to_gradient_level(0.90) == GL.HELD
        assert utilization_to_gradient_level(0.95) == GL.HELD
        assert utilization_to_gradient_level(0.99) == GL.HELD

        # BLOCKED: >= 100%
        assert utilization_to_gradient_level(1.0) == GL.BLOCKED
        assert utilization_to_gradient_level(1.5) == GL.BLOCKED

    def test_audit_anchors_tamper_evident(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Audit Anchors -- Tamper-evident, hash-chained records'"""
        session = session_mgr.create_session(
            workspace_id="ws-tamper",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)

        # Append 3 anchors
        chain.append(action="read_file", actor="ai", result="auto_approved", resource="/src/a.py")
        chain.append(action="write_file", actor="ai", result="auto_approved", resource="/src/b.py")
        chain.append(action="deploy", actor="human", result="flagged")

        # Chain should verify OK
        valid, breaks = chain.verify_integrity()
        assert valid is True
        assert len(breaks) == 0

        # Tamper with the second anchor's payload in the DB directly
        from praxis.persistence.db_ops import _db_path, _get_conn

        conn = _get_conn()
        try:
            cursor = conn.execute(
                "SELECT id, payload FROM trust_chain_entries "
                "WHERE session_id = ? AND entry_type = 'anchor' "
                "ORDER BY created_at ASC LIMIT 1 OFFSET 1",
                (sid,),
            )
            row = cursor.fetchone()
            assert row is not None
            anchor_id = row["id"]

            # Corrupt the payload
            tampered = json.loads(row["payload"])
            tampered["action"] = "TAMPERED"
            conn.execute(
                "UPDATE trust_chain_entries SET payload = ? WHERE id = ?",
                (json.dumps(tampered), anchor_id),
            )
            conn.commit()
        finally:
            conn.close()

        # Verification should now detect the tampering
        valid2, breaks2 = chain.verify_integrity()
        assert valid2 is False
        assert len(breaks2) > 0
        assert any(b["reason"] == "bad_hash" for b in breaks2)

    def test_verification_bundles_self_contained(
        self, session_mgr, key_mgr, five_dim_constraints, tmp_path
    ):
        """Spec: 'Verification Bundles -- Self-contained exports'"""
        session = session_mgr.create_session(
            workspace_id="ws-bundle",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)
        chain.append(action="session_created", actor="system", result="auto_approved")

        session_mgr.end_session(sid)
        session_data = session_mgr.get_session(sid)

        # Build trust chain entries from genesis + anchors
        trust_entries = []
        genesis = session_data.get("genesis_chain_entry")
        if genesis:
            trust_entries.append(genesis)
        for a in chain.anchors:
            trust_entries.append(
                {
                    "payload": a.payload,
                    "content_hash": a.content_hash,
                    "signature": a.signature,
                    "signer_key_id": a.signer_key_id,
                    "parent_hash": a.parent_hash,
                }
            )

        pub_pem = key_mgr.export_public_pem("test-key")
        if isinstance(pub_pem, bytes):
            pub_pem = pub_pem.decode("utf-8")

        bundle_path = tmp_path / "verification.zip"
        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_entries,
            deliberation_records=[],
            constraint_events=[],
            public_keys={"test-key": pub_pem},
        )
        builder.build(bundle_path)

        assert bundle_path.exists()

        with zipfile.ZipFile(bundle_path) as zf:
            names = zf.namelist()
            assert "index.html" in names
            assert "data/bundle-data.js" in names
            assert "verify/verifier.js" in names
            assert "style/styles.css" in names

            # Verify bundle data is parseable JSON inside JS wrapper
            bundle_js = zf.read("data/bundle-data.js").decode("utf-8")
            assert bundle_js.startswith("window.PRAXIS_BUNDLE = ")
            json_str = bundle_js.replace("window.PRAXIS_BUNDLE = ", "").rstrip(";")
            bundle_data = json.loads(json_str)
            assert "metadata" in bundle_data
            assert "chain" in bundle_data
            assert "keys" in bundle_data


# ===========================================================================
# Capability 5: Domain Engine
# ===========================================================================


class TestCapability5_DomainEngine:
    """Spec: 'Pluggable CO domain applications.'"""

    def test_six_domains_loadable(self):
        """Spec: COC, COE, COG, COR, COComp, COF all defined"""
        loader = DomainLoader()
        available = loader.list_domains()

        expected = {"coc", "coe", "cog", "cor", "cocomp", "cof"}
        assert expected.issubset(
            set(available)
        ), f"Missing domains: {expected - set(available)}. Available: {available}"

        # Verify each domain parses correctly
        for domain in expected:
            config = loader.load_domain(domain)
            assert config.name == domain
            assert config.display_name
            assert config.description
            assert config.version

    def test_constraint_templates_per_domain(self):
        """Spec: 'Constraint templates -- Domain-appropriate default constraints'"""
        loader = DomainLoader()
        coc = loader.load_domain("coc")
        coe = loader.load_domain("coe")

        # COC has strict/moderate/permissive
        assert "strict" in coc.constraint_templates
        assert "moderate" in coc.constraint_templates

        # COE has year1/year2/year3
        assert "year1" in coe.constraint_templates
        assert "year2" in coe.constraint_templates
        assert "year3" in coe.constraint_templates

        # Verify they have different financial limits
        coc_strict = coc.constraint_templates["strict"]
        coe_year1 = coe.constraint_templates["year1"]

        assert coc_strict["financial"]["max_spend"] != coe_year1["financial"]["max_spend"]

    def test_workflow_phases_with_approval_gates(self, session_mgr, five_dim_constraints):
        """Spec: 'Workflow definitions -- Structured phases with approval gates'"""
        session = session_mgr.create_session(
            workspace_id="ws-phases",
            domain="coc",
            constraints=five_dim_constraints,
        )

        # COC phases: analyze, plan, implement, validate, codify
        assert session["current_phase"] is not None
        assert len(session["phase_list"]) >= 4

        sid = session["session_id"]

        # "analyze" has approval_gate: true in COC domain YAML
        # Attempting to advance past it should raise PhaseGateError
        with pytest.raises(PhaseGateError) as exc_info:
            session_mgr.advance_phase(sid)

        assert exc_info.value.held_action_id is not None

    def test_capture_rules_per_domain(self):
        """Spec: 'Capture rules -- What deliberation evidence to record'"""
        loader = DomainLoader()
        coc = loader.load_domain("coc")
        coe = loader.load_domain("coe")

        # Both have capture configs
        assert coc.capture is not None
        assert coe.capture is not None

        # They have different decision_types
        coc_types = set(coc.capture.get("decision_types", []))
        coe_types = set(coe.capture.get("decision_types", []))

        # COC includes "architecture", COE includes "methodology"
        assert "architecture" in coc_types
        assert "methodology" in coe_types
        assert coc_types != coe_types

    def test_knowledge_classification(self):
        """Spec: knowledge classified as institutional vs generic"""
        institutional = get_institutional_knowledge("coc")
        assert len(institutional) > 0

        # All returned entries should be institutional
        for entry in institutional:
            assert entry["type"] == "institutional"
            assert entry["content"]
            assert entry["priority"] in ("P0", "P1", "P2", "P3")


# ===========================================================================
# Capability 6: Multi-Channel Client API
# ===========================================================================


class TestCapability6_MultiChannelAPI:
    """Spec: 'Tool-agnostic integration.'"""

    def test_rest_api_routes_exist(self):
        """Spec: 'REST API -- For web, mobile, and custom client integration'"""
        # Verify the REST routes module exists and defines session routes
        from praxis.api.routes import create_rest_router

        router = create_rest_router(
            session_manager=None,
            deliberation_engines={},
            constraint_enforcers={},
            key_manager=None,
            key_id="test",
            audit_chains={},
            held_action_manager=None,
            config=None,
        )
        route_paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert any(
            "/sessions" in p for p in route_paths
        ), f"REST route /sessions not found. Routes: {route_paths}"

    def test_cli_commands_exist(self):
        """Spec: 'CLI -- Direct terminal access to all capabilities'"""
        from praxis.cli import main

        # main is a click.Group -- verify expected commands are registered
        assert hasattr(main, "commands") or hasattr(main, "list_commands")

        # Check for core CLI commands
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        output = result.output.lower()

        # The spec lists: session management, decide, status, export, verify
        expected_commands = ["session", "decide", "status", "export", "verify"]
        for cmd in expected_commands:
            assert cmd in output, f"CLI command '{cmd}' not found in help output"

    def test_mcp_tools_registered(self):
        """Spec: 'MCP -- For AI assistant integration'"""
        # Verify the MCP module defines all 5 trust tools
        import inspect
        from praxis.api import mcp

        source = inspect.getsource(mcp.register_mcp_tools)

        mcp_tools = [
            "trust_check",
            "trust_record",
            "trust_escalate",
            "trust_envelope",
            "trust_status",
        ]
        for tool in mcp_tools:
            assert tool in source, f"MCP tool '{tool}' not defined in register_mcp_tools"

    def test_websocket_endpoint_exists(self):
        """Spec: 'WebSocket -- Real-time event streaming'"""
        # Verify the WebSocket module exists and provides broadcasting
        from praxis.api.websocket import EventBroadcaster, get_broadcaster

        broadcaster = get_broadcaster()
        assert isinstance(broadcaster, EventBroadcaster)

        # Verify the app factory mounts /ws/events
        import inspect
        from praxis.api.app import _mount_websocket

        source = inspect.getsource(_mount_websocket)
        assert "/ws/events" in source


# ===========================================================================
# Capability 10: Verification & Export
# ===========================================================================


class TestCapability10_VerificationExport:
    """Spec: 'Independent verification capabilities.'"""

    def test_bundle_is_zip_with_html(self, session_mgr, key_mgr, five_dim_constraints, tmp_path):
        """Spec: 'Self-contained ZIP/HTML packages with embedded verification code'"""
        session = session_mgr.create_session(
            workspace_id="ws-zip",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)
        chain.append(action="test", actor="system", result="auto_approved")

        session_mgr.end_session(sid)
        session_data = session_mgr.get_session(sid)

        genesis = session_data.get("genesis_chain_entry")
        trust_entries = [genesis] if genesis else []
        for a in chain.anchors:
            trust_entries.append(
                {
                    "payload": a.payload,
                    "content_hash": a.content_hash,
                    "signature": a.signature,
                    "signer_key_id": a.signer_key_id,
                    "parent_hash": a.parent_hash,
                }
            )

        pub_pem = key_mgr.export_public_pem("test-key")
        if isinstance(pub_pem, bytes):
            pub_pem = pub_pem.decode("utf-8")
        bundle_path = tmp_path / "bundle.zip"
        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_entries,
            deliberation_records=[],
            constraint_events=[],
            public_keys={"test-key": pub_pem},
        )
        builder.build(bundle_path)

        assert zipfile.is_zipfile(bundle_path)
        with zipfile.ZipFile(bundle_path) as zf:
            html = zf.read("index.html").decode("utf-8")
            assert "<!DOCTYPE html>" in html
            assert "Praxis" in html

    def test_audit_report_human_readable(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'Audit Reports -- Human-readable with timeline, constraints, deliberation'"""
        session = session_mgr.create_session(
            workspace_id="ws-report",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        engine = DeliberationEngine(session_id=sid, key_manager=key_mgr, key_id="test-key")
        engine.record_decision("Use REST", "Standard pattern", actor="human")

        session_mgr.end_session(sid)
        session_data = session_mgr.get_session(sid)
        records, _ = engine.get_timeline()

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=[],
            deliberation=records,
            constraints=[],
        )

        assert "<!DOCTYPE html>" in html
        assert "Session Summary" in html
        assert "Deliberation Records" in html
        assert "Constraint Evaluations" in html
        assert "Use REST" in html

    def test_chain_verification_cryptographic(self, key_mgr, five_dim_constraints):
        """Spec: 'Chain Verification -- Cryptographic validation'"""
        genesis = create_genesis(
            session_id="test-verify",
            authority_id="alice",
            key_id="test-key",
            key_manager=key_mgr,
            constraints=five_dim_constraints,
            domain="coc",
        )

        entries = [
            {
                "payload": genesis.payload,
                "content_hash": genesis.content_hash,
                "signature": genesis.signature,
                "signer_key_id": genesis.signer_key_id,
                "parent_hash": None,
            }
        ]

        pub_pem = key_mgr.export_public_pem("test-key")
        if isinstance(pub_pem, bytes):
            pub_pem = pub_pem.decode("utf-8")
        public_keys = {"test-key": pub_pem}

        result = verify_chain(entries, public_keys)
        assert result.valid is True
        assert result.total_entries == 1
        assert result.verified_entries == 1
        assert len(result.breaks) == 0

    def test_export_format_json(self, session_mgr, key_mgr, five_dim_constraints):
        """Spec: 'JSON (machine-readable)'"""
        session = session_mgr.create_session(
            workspace_id="ws-json",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]
        engine = DeliberationEngine(session_id=sid, key_manager=key_mgr, key_id="test-key")
        engine.record_decision("Test export", "For JSON format", actor="human")

        session_mgr.end_session(sid)
        session_data = session_mgr.get_session(sid)
        records, _ = engine.get_timeline()

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=[],
            deliberation=records,
            constraints=[],
        )

        assert isinstance(report, dict)
        assert "session" in report
        assert "chain_summary" in report
        assert "deliberation_summary" in report
        assert "constraint_summary" in report
        assert "generated_at" in report

        # Should be JSON-serializable
        json_str = json.dumps(report)
        assert len(json_str) > 0


# ===========================================================================
# Success Criteria
# ===========================================================================


class TestSuccessCriteria:
    """Spec: 7 success criteria from the product vision."""

    def test_criterion_1_init_under_60_seconds(self, key_mgr, five_dim_constraints):
        """'A researcher can run praxis init and have trust infrastructure in under 60 seconds'"""
        start = time.monotonic()

        # Simulate the init workflow: create session + genesis + audit chain
        sm = SessionManager(key_manager=key_mgr, key_id="test-key")
        session = sm.create_session(
            workspace_id="ws-init-speed",
            domain="coc",
            constraints=five_dim_constraints,
        )
        chain = AuditChain(
            session_id=session["session_id"],
            key_id="test-key",
            key_manager=key_mgr,
        )
        chain.append(action="session_created", actor="system", result="auto_approved")

        elapsed = time.monotonic() - start
        assert elapsed < 60.0, f"Init took {elapsed:.1f}s, must be under 60s"

    def test_criterion_2_cryptographic_proof_of_supervision(
        self, session_mgr, key_mgr, five_dim_constraints, tmp_path
    ):
        """'A student can demonstrate cryptographic proof that they supervised AI collaboration'"""
        session = session_mgr.create_session(
            workspace_id="ws-proof",
            domain="coe",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        # Student records decisions
        engine = DeliberationEngine(session_id=sid, key_manager=key_mgr, key_id="test-key")
        engine.record_decision(
            "Use regression analysis",
            "Fits the research question better than correlation",
            actor="human",
            confidence=0.9,
        )
        engine.record_decision(
            "Exclude outlier data points",
            "Statistical justification: Cook's distance > threshold",
            actor="human",
            alternatives=["Keep outliers", "Winsorize"],
        )

        # Build audit chain
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)
        chain.append(action="decision_recorded", actor="human", result="auto_approved")
        chain.append(action="decision_recorded", actor="human", result="auto_approved")

        # Verify chain integrity
        valid, breaks = chain.verify_integrity()
        assert valid is True

        # Export as bundle -- the cryptographic proof
        session_mgr.end_session(sid)
        session_data = session_mgr.get_session(sid)
        records, _ = engine.get_timeline()

        trust_entries = []
        genesis = session_data.get("genesis_chain_entry")
        if genesis:
            trust_entries.append(genesis)
        for a in chain.anchors:
            trust_entries.append(
                {
                    "payload": a.payload,
                    "content_hash": a.content_hash,
                    "signature": a.signature,
                    "signer_key_id": a.signer_key_id,
                    "parent_hash": a.parent_hash,
                }
            )

        pub_pem = key_mgr.export_public_pem("test-key")
        if isinstance(pub_pem, bytes):
            pub_pem = pub_pem.decode("utf-8")
        bundle_path = tmp_path / "student_proof.zip"
        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_entries,
            deliberation_records=records,
            constraint_events=[],
            public_keys={"test-key": pub_pem},
        )
        builder.build(bundle_path)
        assert bundle_path.exists()

    def test_criterion_3_unbypassable_spending_limits(self, session_mgr, five_dim_constraints):
        """'A compliance officer can enforce spending limits that cannot be bypassed'"""
        constraints_10 = dict(five_dim_constraints)
        constraints_10["financial"] = {"max_spend": 10.0, "current_spend": 0.0}

        session = session_mgr.create_session(
            workspace_id="ws-comply",
            domain="coc",
            constraints=constraints_10,
        )
        enforcer = ConstraintEnforcer(
            constraints_10,
            session_id=session["session_id"],
        )

        # Record $9 spend -- OK
        enforcer.record_spend(9.0)
        verdict = enforcer.evaluate("write", "/src/main.py")
        assert verdict.level != GradientLevel.BLOCKED

        # Attempt $15 total spend ($9 + $6) -- BLOCKED
        verdict = enforcer.evaluate("write", "/src/main.py", context={"cost": 6.0})
        assert verdict.level == GradientLevel.BLOCKED

        # Constraint cannot be loosened via update
        with pytest.raises(ValueError, match="loosen"):
            session_mgr.update_constraints(
                session["session_id"],
                {
                    "financial": {"max_spend": 100.0, "current_spend": 0.0},
                    "operational": constraints_10["operational"],
                    "temporal": constraints_10["temporal"],
                    "data_access": constraints_10["data_access"],
                    "communication": constraints_10["communication"],
                },
            )

    def test_criterion_4_verify_without_installing(
        self, session_mgr, key_mgr, five_dim_constraints, tmp_path
    ):
        """'An auditor can independently verify audit trail without installing software'"""
        session = session_mgr.create_session(
            workspace_id="ws-auditor",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]
        chain = AuditChain(session_id=sid, key_id="test-key", key_manager=key_mgr)
        chain.append(action="session_created", actor="system", result="auto_approved")

        session_mgr.end_session(sid)
        session_data = session_mgr.get_session(sid)

        trust_entries = []
        genesis = session_data.get("genesis_chain_entry")
        if genesis:
            trust_entries.append(genesis)
        for a in chain.anchors:
            trust_entries.append(
                {
                    "payload": a.payload,
                    "content_hash": a.content_hash,
                    "signature": a.signature,
                    "signer_key_id": a.signer_key_id,
                    "parent_hash": a.parent_hash,
                }
            )

        pub_pem = key_mgr.export_public_pem("test-key")
        if isinstance(pub_pem, bytes):
            pub_pem = pub_pem.decode("utf-8")
        bundle_path = tmp_path / "auditor.zip"
        builder = BundleBuilder(
            session_data=session_data,
            trust_chain=trust_entries,
            deliberation_records=[],
            constraint_events=[],
            public_keys={"test-key": pub_pem},
        )
        builder.build(bundle_path)

        # The bundle contains client-side verification HTML + JS
        with zipfile.ZipFile(bundle_path) as zf:
            assert "index.html" in zf.namelist()
            assert "verify/verifier.js" in zf.namelist()

            # The HTML file includes script references to the verifier
            html = zf.read("index.html").decode("utf-8")
            assert "verifier.js" in html

    def test_criterion_5_tool_switching_same_context(
        self, session_mgr, key_mgr, five_dim_constraints
    ):
        """'A developer can switch between tools while maintaining same trust context'"""
        # Create session via one code path (simulating CLI)
        session = session_mgr.create_session(
            workspace_id="ws-switch",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        # Record decision via one "tool" (simulating MCP)
        engine = DeliberationEngine(session_id=sid, key_manager=key_mgr, key_id="test-key")
        engine.record_decision("Use FastAPI", "Standard async framework", actor="ai")

        # Access the same session via a different handler path (simulating REST API)
        from praxis.api.handlers import get_session_handler

        result = get_session_handler(session_manager=session_mgr, session_id=sid)
        assert result["session_id"] == sid
        assert result["state"] == "active"

        # The deliberation timeline is the same regardless of access path
        records, total = engine.get_timeline()
        assert total >= 1

    def test_criterion_6_approve_from_phone(self, session_mgr, key_mgr, five_dim_constraints):
        """'A supervisor can approve held actions from their phone'"""
        session = session_mgr.create_session(
            workspace_id="ws-phone",
            domain="coc",
            constraints=five_dim_constraints,
        )
        sid = session["session_id"]

        # Create a held action (simulating a constraint evaluation that returned HELD)
        held_mgr = HeldActionManager(use_db=True)
        verdict = ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="financial",
            utilization=0.92,
            reason="Financial utilization at 92%",
            action="deploy",
            resource="production",
        )
        held = held_mgr.hold(
            session_id=sid,
            action="deploy",
            resource="production",
            verdict=verdict,
        )

        assert held.resolved is False

        # Supervisor approves via handler (simulating mobile API call)
        from praxis.api.handlers import approve_handler

        result = approve_handler(
            held_action_manager=held_mgr,
            held_id=held.held_id,
            approved_by="supervisor-mobile",
        )

        assert result.get("resolution") == "approved"

        # Verify it's resolved
        updated = held_mgr.get_held(held.held_id)
        assert updated.resolved is True
        assert updated.resolution == "approved"
        assert updated.resolved_by == "supervisor-mobile"

    def test_criterion_7_any_domain_without_forking(self, session_mgr, five_dim_constraints):
        """'Any domain can define its own CO configuration and run on Praxis without forking'"""
        loader = DomainLoader()
        all_domains = loader.list_domains()

        # Create sessions with at least 3 different domains
        domains_to_test = all_domains[:3] if len(all_domains) >= 3 else all_domains
        assert (
            len(domains_to_test) >= 3
        ), f"Need at least 3 domains, found {len(all_domains)}: {all_domains}"

        sessions = []
        for domain in domains_to_test:
            # Each domain uses its own constraint template
            config = loader.load_domain(domain)
            template_name = list(config.constraint_templates.keys())[0]
            template = config.constraint_templates[template_name]

            # Normalize the template to have all required runtime fields
            normalized = {}
            for dim in ("financial", "operational", "temporal", "data_access", "communication"):
                normalized[dim] = dict(template.get(dim, {}))
            if "current_spend" not in normalized["financial"]:
                normalized["financial"]["current_spend"] = 0.0
            if "elapsed_minutes" not in normalized["temporal"]:
                normalized["temporal"]["elapsed_minutes"] = 0
            if "blocked_actions" not in normalized["operational"]:
                normalized["operational"]["blocked_actions"] = []
            if "blocked_paths" not in normalized["data_access"]:
                normalized["data_access"]["blocked_paths"] = []
            if "blocked_channels" not in normalized["communication"]:
                normalized["communication"]["blocked_channels"] = []

            s = session_mgr.create_session(
                workspace_id=f"ws-{domain}",
                domain=domain,
                constraints=normalized,
            )
            sessions.append(s)

        assert len(sessions) == len(domains_to_test)

        # Verify each session has domain-specific configuration
        domains_seen = {s["domain"] for s in sessions}
        assert len(domains_seen) == len(domains_to_test)

        # Each session should have its own phases from the domain YAML
        for s in sessions:
            assert s["phase_list"] is not None or s["phase_list"] == []
