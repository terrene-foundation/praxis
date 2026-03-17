# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""EATP specification conformance tests.

These tests verify that Praxis's trust chain implementation
conforms to the EATP specification published by the Terrene Foundation.

EATP (Enterprise Agent Trust Protocol) defines:
    1. Genesis records: root of trust for sessions
    2. Delegation chains: authority delegation with constraint tightening
    3. Audit anchors: tamper-evident action records
    4. Revocation: cascade invalidation of delegations
    5. Verification: cryptographic chain validation

Each test maps to a specific EATP specification requirement.
"""

import pytest


class TestEATPGenesisConformance:
    """EATP Spec: Genesis record requirements."""

    def test_genesis_must_have_authority_id(self, key_manager, sample_constraints):
        """EATP: Genesis record MUST identify the authority."""
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-genesis-001",
            authority_id="authority-user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert genesis.authority_id == "authority-user"

    def test_genesis_must_have_constraints(self, key_manager, sample_constraints):
        """EATP: Genesis record MUST define the constraint envelope."""
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-genesis-002",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert genesis.constraints == sample_constraints

    def test_genesis_must_be_signed(self, key_manager, sample_constraints):
        """EATP: Genesis record MUST be cryptographically signed."""
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-genesis-003",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert genesis.signature is not None
        assert len(genesis.signature) > 0

    def test_genesis_must_have_content_hash(self, key_manager, sample_constraints):
        """EATP: Genesis record MUST have a deterministic content hash."""
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-genesis-004",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert genesis.content_hash is not None
        assert len(genesis.content_hash) == 64  # SHA-256 hex digest

    def test_genesis_empty_authority_raises(self, key_manager, sample_constraints):
        """EATP: Genesis with empty authority_id MUST be rejected."""
        from praxis.trust.genesis import create_genesis

        with pytest.raises(ValueError, match="authority_id"):
            create_genesis(
                session_id="eatp-genesis-005",
                authority_id="",
                key_id="test-key",
                key_manager=key_manager,
                constraints=sample_constraints,
            )


class TestEATPDelegationConformance:
    """EATP Spec: Delegation chain requirements."""

    def test_delegation_constraint_tightening_is_mandatory(
        self, key_manager, sample_constraints, looser_constraints
    ):
        """EATP: Delegation MUST enforce constraint tightening."""
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-deleg-001",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )

        with pytest.raises(ValueError, match="[Cc]onstraint|[Tt]ighten"):
            create_delegation(
                session_id="eatp-deleg-001",
                parent_id=genesis.content_hash,
                parent_constraints=sample_constraints,
                delegate_id="agent",
                delegate_constraints=looser_constraints,
                key_id="test-key",
                key_manager=key_manager,
                parent_hash=genesis.content_hash,
            )

    def test_delegation_must_reference_parent(
        self, key_manager, sample_constraints, tighter_constraints
    ):
        """EATP: Delegation MUST reference parent via parent_hash."""
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-deleg-002",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )

        delegation = create_delegation(
            session_id="eatp-deleg-002",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        assert delegation.parent_hash == genesis.content_hash

    def test_delegation_must_be_signed(self, key_manager, sample_constraints, tighter_constraints):
        """EATP: Delegation MUST be cryptographically signed."""
        from praxis.trust.delegation import create_delegation
        from praxis.trust.genesis import create_genesis

        genesis = create_genesis(
            session_id="eatp-deleg-003",
            authority_id="admin",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )

        delegation = create_delegation(
            session_id="eatp-deleg-003",
            parent_id=genesis.content_hash,
            parent_constraints=sample_constraints,
            delegate_id="agent",
            delegate_constraints=tighter_constraints,
            key_id="test-key",
            key_manager=key_manager,
            parent_hash=genesis.content_hash,
        )
        assert delegation.signature is not None
        assert len(delegation.signature) > 0


class TestEATPVerificationConformance:
    """EATP Spec: Chain verification requirements."""

    def test_tampered_hash_must_be_detected(self, key_manager, sample_constraints):
        """EATP: Tampered content_hash MUST be detected as 'bad_hash'."""
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="eatp-verify-001",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        entry = {
            "payload": genesis.payload,
            "content_hash": "0" * 64,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        }
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain([entry], public_keys)
        assert result.valid is False
        assert any(b["reason"] == "bad_hash" for b in result.breaks)

    def test_unknown_key_must_be_reported(self, key_manager, sample_constraints):
        """EATP: Unknown signer key MUST be reported as 'unknown_key'."""
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="eatp-verify-002",
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
        result = verify_chain([entry], {})  # No keys provided
        assert result.valid is False
        assert any(b["reason"] == "unknown_key" for b in result.breaks)

    def test_genesis_with_parent_hash_must_fail(self, key_manager, sample_constraints):
        """EATP: Genesis record MUST NOT have a parent_hash."""
        from praxis.trust.genesis import create_genesis
        from praxis.trust.verify import verify_chain

        genesis = create_genesis(
            session_id="eatp-verify-003",
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
            "parent_hash": "should_not_exist_" + "0" * 48,
        }
        public_keys = {"test-key": key_manager.export_public_pem("test-key")}
        result = verify_chain([entry], public_keys)
        assert result.valid is False

    def test_empty_chain_is_valid(self):
        """EATP: Empty chain MUST be considered valid."""
        from praxis.trust.verify import verify_chain

        result = verify_chain([], {})
        assert result.valid is True
        assert result.total_entries == 0


class TestEATPConstraintDimensions:
    """EATP Spec: Five constraint dimensions conformance."""

    def test_five_constraint_dimensions_exist(self):
        """EATP: All five constraint dimensions MUST be supported."""
        from praxis.core.constraint import CONSTRAINT_DIMENSIONS

        assert len(CONSTRAINT_DIMENSIONS) == 5
        assert "financial" in CONSTRAINT_DIMENSIONS
        assert "operational" in CONSTRAINT_DIMENSIONS
        assert "temporal" in CONSTRAINT_DIMENSIONS
        assert "data_access" in CONSTRAINT_DIMENSIONS
        assert "communication" in CONSTRAINT_DIMENSIONS

    def test_gradient_levels_match_specification(self):
        """EATP: Four gradient levels MUST be: auto_approved, flagged, held, blocked."""
        from praxis.trust.gradient import GradientLevel

        assert GradientLevel.AUTO_APPROVED == "auto_approved"
        assert GradientLevel.FLAGGED == "flagged"
        assert GradientLevel.HELD == "held"
        assert GradientLevel.BLOCKED == "blocked"

    def test_gradient_thresholds_are_normative(self):
        """EATP: Gradient thresholds (70%, 90%, 100%) are normative and not configurable."""
        from praxis.trust.gradient import _utilization_to_level, GradientLevel

        # Below 70% -> AUTO_APPROVED
        assert _utilization_to_level(0.69) == GradientLevel.AUTO_APPROVED
        # At 70% -> FLAGGED
        assert _utilization_to_level(0.70) == GradientLevel.FLAGGED
        # At 89% -> still FLAGGED
        assert _utilization_to_level(0.89) == GradientLevel.FLAGGED
        # At 90% -> HELD
        assert _utilization_to_level(0.90) == GradientLevel.HELD
        # At 99% -> still HELD
        assert _utilization_to_level(0.99) == GradientLevel.HELD
        # At 100% -> BLOCKED
        assert _utilization_to_level(1.0) == GradientLevel.BLOCKED
