# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.trust.delegation — delegation chain management."""

import base64
import hashlib

import jcs
import pytest


class TestDelegationRecordDataclass:
    """Test that DelegationRecord has all required fields."""

    def test_delegation_record_has_required_fields(self):
        from praxis.trust.delegation import DelegationRecord

        record = DelegationRecord(
            delegation_id="del-001",
            session_id="sess-001",
            parent_id="genesis-001",
            delegate_id="ai-assistant",
            constraints={"financial": {"max_spend": 500}},
            payload={"type": "delegation"},
            content_hash="a" * 64,
            signature="sig",
            signer_key_id="key-1",
            parent_hash="b" * 64,
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert record.delegation_id == "del-001"
        assert record.session_id == "sess-001"
        assert record.parent_id == "genesis-001"
        assert record.delegate_id == "ai-assistant"
        assert record.parent_hash == "b" * 64


class TestConstraintTightening:
    """Test the constraint tightening validation rules."""

    def test_equal_constraints_are_valid(self, sample_constraints):
        from praxis.trust.delegation import validate_constraint_tightening

        assert validate_constraint_tightening(sample_constraints, sample_constraints) is True

    def test_tighter_financial_is_valid(self, sample_constraints, tighter_constraints):
        from praxis.trust.delegation import validate_constraint_tightening

        assert validate_constraint_tightening(sample_constraints, tighter_constraints) is True

    def test_looser_financial_is_invalid(self, sample_constraints, looser_constraints):
        from praxis.trust.delegation import validate_constraint_tightening

        assert validate_constraint_tightening(sample_constraints, looser_constraints) is False

    def test_tighter_operational_subset_is_valid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read", "write", "execute"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src", "/tests"]},
            "communication": {"allowed_channels": ["internal", "email"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src", "/tests"]},
            "communication": {"allowed_channels": ["internal", "email"]},
        }
        assert validate_constraint_tightening(parent, child) is True

    def test_looser_operational_superset_is_invalid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read", "write", "deploy"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert validate_constraint_tightening(parent, child) is False

    def test_tighter_temporal_is_valid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert validate_constraint_tightening(parent, child) is True

    def test_looser_temporal_is_invalid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert validate_constraint_tightening(parent, child) is False

    def test_tighter_data_access_subset_is_valid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src", "/tests", "/docs"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert validate_constraint_tightening(parent, child) is True

    def test_looser_data_access_superset_is_invalid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src", "/secrets"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert validate_constraint_tightening(parent, child) is False

    def test_tighter_communication_subset_is_valid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal", "email"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        assert validate_constraint_tightening(parent, child) is True

    def test_looser_communication_superset_is_invalid(self):
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        child = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal", "external"]},
        }
        assert validate_constraint_tightening(parent, child) is False

    def test_single_dimension_looser_makes_entire_tightening_fail(self):
        """Even if 4 of 5 dimensions are tighter, one looser dimension fails."""
        from praxis.trust.delegation import validate_constraint_tightening

        parent = {
            "financial": {"max_spend": 1000},
            "operational": {"allowed_actions": ["read", "write", "execute"]},
            "temporal": {"max_duration_minutes": 120},
            "data_access": {"allowed_paths": ["/src", "/tests"]},
            "communication": {"allowed_channels": ["internal", "email"]},
        }
        child = {
            "financial": {"max_spend": 500},  # tighter
            "operational": {"allowed_actions": ["read"]},  # tighter
            "temporal": {"max_duration_minutes": 60},  # tighter
            "data_access": {"allowed_paths": ["/src"]},  # tighter
            "communication": {"allowed_channels": ["internal", "email", "slack"]},  # LOOSER
        }
        assert validate_constraint_tightening(parent, child) is False


class TestCreateDelegation:
    """Test delegation creation with signing and validation."""

    def test_creates_delegation_with_valid_signature(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-001",
            authority_id="user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-001",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-assistant",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        assert delegation.session_id == "sess-001"
        assert delegation.delegate_id == "ai-assistant"
        assert delegation.parent_hash == genesis.content_hash

    def test_content_hash_matches_jcs_payload(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

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
            delegate_id="ai-assistant",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        canonical = jcs.canonicalize(delegation.payload)
        expected_hash = hashlib.sha256(canonical).hexdigest()
        assert delegation.content_hash == expected_hash

    def test_signature_verifies(self, key_manager, sample_constraints, tighter_constraints):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-003",
            authority_id="user-3",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-003",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-assistant",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        hash_bytes = bytes.fromhex(delegation.content_hash)
        sig_bytes = base64.urlsafe_b64decode(delegation.signature)
        assert key_manager.verify("test-key", hash_bytes, sig_bytes) is True

    def test_rejects_looser_constraints(self, key_manager, sample_constraints, looser_constraints):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-004",
            authority_id="user-4",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        with pytest.raises(ValueError, match="[Cc]onstraint|[Tt]ighten"):
            create_delegation(
                session_id="sess-004",
                parent_id=genesis.content_hash,
                parent_constraints=sample_constraints,
                delegate_id="ai-assistant",
                delegate_constraints=looser_constraints,
                key_id="test-key",
                key_manager=key_manager,
                parent_hash=genesis.content_hash,
            )

    def test_delegation_payload_has_required_fields(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-005",
            authority_id="user-5",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-005",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-assistant",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        payload = delegation.payload
        assert payload["type"] == "delegation"
        assert payload["version"] == "1.0"
        assert payload["session_id"] == "sess-005"
        assert payload["delegate_id"] == "ai-assistant"
        assert payload["parent_hash"] == genesis.content_hash
        assert "constraints" in payload
        assert "created_at" in payload

    def test_delegation_chain_links_hashes(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        """A delegation's parent_hash must match the genesis content_hash."""
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-006",
            authority_id="user-6",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-006",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        # The delegation's parent_hash should point back to the genesis
        assert delegation.parent_hash == genesis.content_hash


class TestRevokeDelegation:
    """Test delegation revocation."""

    def test_revoke_returns_revocation_entry(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation, revoke_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-revoke-001",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-revoke-001",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        revocation = revoke_delegation(
            delegation_id=delegation.delegation_id,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=delegation.content_hash,
        )
        assert "revocation" in revocation.get("type", "") or "revoked_delegation_id" in revocation

    def test_revocation_is_signed(self, key_manager, sample_constraints, tighter_constraints):
        from praxis.trust.delegation import create_delegation, revoke_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-revoke-002",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-revoke-002",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        revocation = revoke_delegation(
            delegation_id=delegation.delegation_id,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=delegation.content_hash,
        )
        assert "signature" in revocation
        assert "content_hash" in revocation

    def test_revocation_references_original_delegation(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        from praxis.trust.delegation import create_delegation, revoke_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="sess-revoke-003",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        delegation = create_delegation(
            session_id="sess-revoke-003",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="ai-agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        revocation = revoke_delegation(
            delegation_id=delegation.delegation_id,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=delegation.content_hash,
        )
        assert revocation["revoked_delegation_id"] == delegation.delegation_id


class TestDelegationValidation:
    """Test input validation for delegation creation."""

    def test_empty_session_id_raises(self, key_manager, sample_constraints, tighter_constraints):
        from praxis.trust.delegation import create_delegation

        with pytest.raises(ValueError, match="session_id"):
            create_delegation(
                session_id="",
                parent_id="parent",
                parent_constraints=sample_constraints,
                delegate_id="ai",
                delegate_constraints=tighter_constraints,
                key_id="test-key",
                key_manager=key_manager,
                parent_hash="hash",
            )

    def test_empty_delegate_id_raises(self, key_manager, sample_constraints, tighter_constraints):
        from praxis.trust.delegation import create_delegation

        with pytest.raises(ValueError, match="delegate_id"):
            create_delegation(
                session_id="sess",
                parent_id="parent",
                parent_constraints=sample_constraints,
                delegate_id="",
                delegate_constraints=tighter_constraints,
                key_id="test-key",
                key_manager=key_manager,
                parent_hash="hash",
            )
