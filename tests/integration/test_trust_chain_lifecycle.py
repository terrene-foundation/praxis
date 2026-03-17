# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Integration tests for trust chain lifecycle.

Tests the complete trust chain workflow: genesis -> delegation -> audit
anchors -> chain verification. Uses real cryptographic operations (no mocking).
"""

import pytest


class TestGenesisToVerification:
    """Test complete genesis -> delegation -> audit -> verification lifecycle."""

    def test_genesis_to_delegation_to_verification(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        """Genesis -> delegation -> audit anchors -> chain verification."""
        from praxis.trust.audit import AuditChain
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain
        from praxis.persistence.queries import get_trust_chain

        # Step 1: Create genesis record
        genesis = create_genesis(
            session_id="sess-chain-001",
            authority_id="admin-user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert genesis.content_hash is not None
        assert genesis.signature is not None

        # Step 2: Create delegation with tighter constraints
        delegation = create_delegation(
            session_id="sess-chain-001",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-agent-1",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        assert delegation.content_hash is not None
        assert delegation.parent_hash == genesis.content_hash

        # Step 3: Create audit chain with anchors
        audit = AuditChain(
            session_id="sess-chain-001",
            key_id="test-key",
            key_manager=key_manager,
        )
        a1 = audit.append(
            action="read_file",
            actor="ai",
            result="auto_approved",
            resource="/src/main.py",
        )
        a2 = audit.append(
            action="write_file",
            actor="ai",
            result="flagged",
            resource="/src/config.py",
            reasoning_hash="abc123",
        )
        a3 = audit.append(
            action="deploy",
            actor="human",
            result="approved",
        )

        # Step 4: Verify audit chain integrity
        valid, breaks = audit.verify_integrity()
        assert valid is True
        assert breaks == []
        assert audit.length == 3

        # Step 5: Assemble complete trust chain via query function
        chain = get_trust_chain(
            session_id="sess-chain-001",
            genesis_record=genesis,
            audit_chain=audit,
            delegations=[delegation],
        )
        assert len(chain) == 5  # genesis + delegation + 3 anchors

        # Step 6: Verify chain entry hashes and signatures using verify_chain
        # Build entries for just genesis + delegation
        genesis_delegation_entries = [
            {
                "payload": genesis.payload,
                "content_hash": genesis.content_hash,
                "signature": genesis.signature,
                "signer_key_id": genesis.signer_key_id,
                "parent_hash": None,
            },
            {
                "payload": delegation.payload,
                "content_hash": delegation.content_hash,
                "signature": delegation.signature,
                "signer_key_id": delegation.signer_key_id,
                "parent_hash": delegation.parent_hash,
            },
        ]
        public_keys = {
            "test-key": key_manager.export_public_pem("test-key"),
        }
        result = verify_chain(genesis_delegation_entries, public_keys)
        assert result.valid is True
        assert result.total_entries == 2
        assert result.verified_entries == 2

    def test_delegation_constraint_tightening_enforcement(
        self, key_manager, sample_constraints, looser_constraints
    ):
        """Delegation with looser constraints must fail."""
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-tighten-001",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )

        with pytest.raises(ValueError, match="[Cc]onstraint|[Tt]ighten"):
            create_delegation(
                session_id="sess-tighten-001",
                parent_id=genesis.content_hash,
                parent_constraints=sample_constraints,
                delegate_id="rogue-agent",
                delegate_constraints=looser_constraints,
                key_id="test-key",
                key_manager=key_manager,
                parent_hash=genesis.content_hash,
            )

    def test_chain_tamper_detection(self, key_manager, sample_constraints):
        """Tampered chain entries must be detected during verification."""
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-tamper-int",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )

        # Tamper with the payload
        tampered_payload = dict(genesis.payload)
        tampered_payload["authority_id"] = "attacker"
        entry = {
            "payload": tampered_payload,
            "content_hash": genesis.content_hash,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        }
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain([entry], public_keys)
        assert result.valid is False
        assert len(result.breaks) > 0

    def test_revocation_in_chain(self, key_manager, sample_constraints, tighter_constraints):
        """Test delegation revocation creates proper chain entries."""
        from praxis.trust.delegation import create_delegation, revoke_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-revoke-001",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )

        delegation = create_delegation(
            session_id="sess-revoke-001",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="agent-to-revoke",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )

        # Revoke the delegation
        revocation = revoke_delegation(
            delegation_id=delegation.delegation_id,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=delegation.content_hash,
        )

        assert revocation["type"] == "revocation"
        assert revocation["revoked_delegation_id"] == delegation.delegation_id
        assert revocation["content_hash"] is not None
        assert revocation["signature"] is not None

    def test_multi_key_chain_verification(
        self, key_manager_factory, sample_constraints, tighter_constraints
    ):
        """Test chain verification with entries signed by different keys."""
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        km = key_manager_factory("admin-key", "agent-key")

        genesis = create_genesis(
            session_id="sess-multi-key",
            authority_id="admin",
            key_id="admin-key",
            key_manager=km,
            constraints=sample_constraints,
        )

        delegation = create_delegation(
            session_id="sess-multi-key",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="agent",
            delegate_constraints=tighter_constraints,
            key_id="agent-key",
            key_manager=km,
            parent_hash=genesis.content_hash,
        )

        entries = [
            {
                "payload": genesis.payload,
                "content_hash": genesis.content_hash,
                "signature": genesis.signature,
                "signer_key_id": genesis.signer_key_id,
                "parent_hash": None,
            },
            {
                "payload": delegation.payload,
                "content_hash": delegation.content_hash,
                "signature": delegation.signature,
                "signer_key_id": delegation.signer_key_id,
                "parent_hash": delegation.parent_hash,
            },
        ]

        public_keys = {
            "admin-key": km.export_public_pem("admin-key"),
            "agent-key": km.export_public_pem("agent-key"),
        }

        result = verify_chain(entries, public_keys)
        assert result.valid is True
        assert result.verified_entries == 2
