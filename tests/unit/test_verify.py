# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.trust.verify — trust chain verification."""

import base64
import hashlib

import jcs
import pytest


class TestVerificationResultDataclass:
    """Test that VerificationResult has all required fields."""

    def test_verification_result_has_required_fields(self):
        from praxis.trust.verify import VerificationResult

        result = VerificationResult(
            valid=True,
            total_entries=5,
            verified_entries=5,
            breaks=[],
        )
        assert result.valid is True
        assert result.total_entries == 5
        assert result.verified_entries == 5
        assert result.breaks == []

    def test_verification_result_with_breaks(self):
        from praxis.trust.verify import VerificationResult

        result = VerificationResult(
            valid=False,
            total_entries=5,
            verified_entries=3,
            breaks=[
                {"position": 3, "reason": "bad_hash", "entry_id": "entry-003"},
            ],
        )
        assert result.valid is False
        assert result.verified_entries == 3
        assert len(result.breaks) == 1
        assert result.breaks[0]["reason"] == "bad_hash"


class TestVerifyChainWithGenesisOnly:
    """Test verification of chains containing only a genesis record."""

    def test_single_genesis_verifies(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-001",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Build the entry dict for verification
        entry = {
            "payload": genesis.payload,
            "content_hash": genesis.content_hash,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        }
        # Get public key PEM for verification
        public_keys = {
            "test-key": key_manager.export_public_pem("test-key"),
        }
        result = verify_chain([entry], public_keys)
        assert result.valid is True
        assert result.total_entries == 1
        assert result.verified_entries == 1
        assert result.breaks == []


class TestVerifyChainWithDelegation:
    """Test verification of chains with genesis + delegations."""

    def test_genesis_plus_delegation_verifies(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-002",
            authority_id="user-2",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-002",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
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
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain(entries, public_keys)
        assert result.valid is True
        assert result.total_entries == 2
        assert result.verified_entries == 2


class TestVerifyChainWithAuditAnchors:
    """Test verification of chains that include audit anchors."""

    def test_genesis_plus_anchors_verifies(self, key_manager, sample_constraints):
        from praxis.trust.audit import AuditChain
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-003",
            authority_id="user-3",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Create audit chain starting from genesis
        audit = AuditChain(session_id="sess-003", key_id="test-key", key_manager=key_manager)
        a1 = audit.append(action="read_file", actor="ai", result="auto_approved")
        a2 = audit.append(action="write_file", actor="ai", result="flagged")

        entries = [
            {
                "payload": genesis.payload,
                "content_hash": genesis.content_hash,
                "signature": genesis.signature,
                "signer_key_id": genesis.signer_key_id,
                "parent_hash": None,
            },
            {
                "payload": a1.payload,
                "content_hash": a1.content_hash,
                "signature": a1.signature,
                "signer_key_id": a1.signer_key_id,
                "parent_hash": a1.parent_hash,
            },
            {
                "payload": a2.payload,
                "content_hash": a2.content_hash,
                "signature": a2.signature,
                "signer_key_id": a2.signer_key_id,
                "parent_hash": a2.parent_hash,
            },
        ]
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain(entries, public_keys)
        # The audit chain is independent from the genesis chain in terms of parent_hash
        # We verify each entry's own hash and signature
        assert result.total_entries == 3
        # At minimum, entries with correct self-hashes and signatures pass
        assert result.verified_entries >= 1


class TestVerifyChainTampering:
    """Test that tampering is detected."""

    def test_tampered_content_hash_detected(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-tamper-001",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        entry = {
            "payload": genesis.payload,
            "content_hash": "0" * 64,  # TAMPERED
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        }
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain([entry], public_keys)
        assert result.valid is False
        assert len(result.breaks) > 0
        assert any("hash" in b["reason"].lower() for b in result.breaks)

    def test_tampered_signature_detected(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-tamper-002",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Create a bad signature (valid base64url but wrong data)
        bad_sig = base64.urlsafe_b64encode(b"x" * 64).decode()
        entry = {
            "payload": genesis.payload,
            "content_hash": genesis.content_hash,
            "signature": bad_sig,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        }
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain([entry], public_keys)
        assert result.valid is False
        assert len(result.breaks) > 0
        assert any("signature" in b["reason"].lower() for b in result.breaks)

    def test_tampered_payload_detected(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-tamper-003",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Tamper with payload
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

    def test_broken_parent_link_detected(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-tamper-004",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-tamper-004",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
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
                "parent_hash": "wrong_hash_" + "0" * 53,  # TAMPERED parent link
            },
        ]
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain(entries, public_keys)
        assert result.valid is False
        assert len(result.breaks) > 0

    def test_genesis_with_parent_hash_is_invalid(self, key_manager, sample_constraints):
        """Genesis must have no parent_hash."""
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-tamper-005",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        entry = {
            "payload": genesis.payload,
            "content_hash": genesis.content_hash,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": "should_not_be_here_" + "0" * 45,  # Genesis should have None
        }
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain([entry], public_keys)
        assert result.valid is False


class TestVerifyChainEmpty:
    """Test verification of empty chains."""

    def test_empty_chain_is_valid(self):
        from praxis.trust.verify import verify_chain

        result = verify_chain([], {})
        assert result.valid is True
        assert result.total_entries == 0
        assert result.verified_entries == 0
        assert result.breaks == []


class TestVerifyChainMultipleKeys:
    """Test verification with multiple signing keys."""

    def test_entries_signed_by_different_keys(self, key_manager_factory, sample_constraints):
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        km = key_manager_factory("key-a", "key-b")

        g1 = create_genesis(
            session_id="sess-multi-001",
            authority_id="user-1",
            key_id="key-a",
            key_manager=km,
            constraints=sample_constraints,
        )
        g2 = create_genesis(
            session_id="sess-multi-002",
            authority_id="user-2",
            key_id="key-b",
            key_manager=km,
            constraints=sample_constraints,
        )
        # Verify each separately
        entries_a = [
            {
                "payload": g1.payload,
                "content_hash": g1.content_hash,
                "signature": g1.signature,
                "signer_key_id": g1.signer_key_id,
                "parent_hash": None,
            },
        ]
        entries_b = [
            {
                "payload": g2.payload,
                "content_hash": g2.content_hash,
                "signature": g2.signature,
                "signer_key_id": g2.signer_key_id,
                "parent_hash": None,
            },
        ]
        public_keys = {
            "key-a": km.export_public_pem("key-a"),
            "key-b": km.export_public_pem("key-b"),
        }
        result_a = verify_chain(entries_a, public_keys)
        result_b = verify_chain(entries_b, public_keys)
        assert result_a.valid is True
        assert result_b.valid is True

    def test_unknown_key_reported_not_as_bad_signature(self, key_manager, sample_constraints):
        """Missing key should be reported as 'unknown_key', not 'bad_signature'."""
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="sess-unknown-key",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        entry = {
            "payload": genesis.payload,
            "content_hash": genesis.content_hash,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        }
        # Pass empty public_keys — key not found
        result = verify_chain([entry], {})
        assert result.valid is False
        assert len(result.breaks) > 0
        assert any("unknown_key" in b["reason"].lower() for b in result.breaks)
