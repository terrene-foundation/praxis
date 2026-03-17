# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.trust.genesis — root of trust for CO sessions."""

import hashlib
import json
from datetime import datetime, timezone

import jcs
import pytest


class TestGenesisRecordDataclass:
    """Test that GenesisRecord holds all required fields."""

    def test_genesis_record_has_required_fields(self):
        from praxis.trust.genesis import GenesisRecord

        record = GenesisRecord(
            session_id="sess-001",
            authority_id="user-1",
            namespace="praxis",
            constraints={"financial": {"max_spend": 1000}},
            domain="coc",
            payload={"type": "genesis"},
            content_hash="a" * 64,
            signature="sig_base64url",
            signer_key_id="key-1",
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert record.session_id == "sess-001"
        assert record.authority_id == "user-1"
        assert record.namespace == "praxis"
        assert record.domain == "coc"
        assert record.signer_key_id == "key-1"

    def test_genesis_record_constraints_are_dict(self):
        from praxis.trust.genesis import GenesisRecord

        constraints = {
            "financial": {"max_spend": 500},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        record = GenesisRecord(
            session_id="s",
            authority_id="a",
            namespace="praxis",
            constraints=constraints,
            domain="coc",
            payload={},
            content_hash="b" * 64,
            signature="sig",
            signer_key_id="k",
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert record.constraints == constraints


class TestCreateGenesis:
    """Test the create_genesis function produces valid signed records."""

    def test_creates_genesis_with_valid_signature(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-001",
            authority_id="human-user-1",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
            domain="coc",
            namespace="praxis",
        )
        assert record.session_id == "sess-001"
        assert record.authority_id == "human-user-1"
        assert record.domain == "coc"
        assert record.namespace == "praxis"
        assert record.signer_key_id == "test-key"

    def test_content_hash_is_sha256_of_jcs_payload(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-002",
            authority_id="user-2",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Verify the content_hash is indeed SHA-256 of JCS-canonical payload
        canonical = jcs.canonicalize(record.payload)
        expected_hash = hashlib.sha256(canonical).hexdigest()
        assert record.content_hash == expected_hash

    def test_signature_verifies_with_key_manager(self, key_manager, sample_constraints):
        import base64

        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-003",
            authority_id="user-3",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Decode the base64url signature and verify
        hash_bytes = bytes.fromhex(record.content_hash)
        sig_bytes = base64.urlsafe_b64decode(record.signature)
        assert key_manager.verify("test-key", hash_bytes, sig_bytes) is True

    def test_payload_contains_required_fields(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-004",
            authority_id="user-4",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
            domain="coc",
            namespace="praxis",
        )
        payload = record.payload
        assert payload["type"] == "genesis"
        assert payload["version"] == "1.0"
        assert payload["session_id"] == "sess-004"
        assert payload["authority_id"] == "user-4"
        assert payload["domain"] == "coc"
        assert payload["namespace"] == "praxis"
        assert "constraints" in payload
        assert "created_at" in payload

    def test_created_at_is_utc_iso8601(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-005",
            authority_id="user-5",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        # Should end with Z (UTC)
        assert record.created_at.endswith("Z")
        # Should be parseable
        dt_str = record.created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        assert dt.tzinfo is not None

    def test_default_domain_is_coc(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-006",
            authority_id="user-6",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert record.domain == "coc"

    def test_default_namespace_is_praxis(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-007",
            authority_id="user-7",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert record.namespace == "praxis"

    def test_custom_domain_and_namespace(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-008",
            authority_id="user-8",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
            domain="coe",
            namespace="custom-ns",
        )
        assert record.domain == "coe"
        assert record.namespace == "custom-ns"

    def test_constraints_stored_in_payload(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-009",
            authority_id="user-9",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert record.payload["constraints"] == sample_constraints
        assert record.constraints == sample_constraints

    def test_invalid_key_raises_error(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        with pytest.raises((KeyError, Exception)):
            create_genesis(
                session_id="sess-010",
                authority_id="user-10",
                key_id="nonexistent-key",
                key_manager=key_manager,
                constraints=sample_constraints,
            )

    def test_each_genesis_has_unique_content_hash(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        r1 = create_genesis(
            session_id="sess-a",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        r2 = create_genesis(
            session_id="sess-b",
            authority_id="user",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert r1.content_hash != r2.content_hash

    def test_genesis_payload_has_signer_key_id(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        record = create_genesis(
            session_id="sess-011",
            authority_id="user-11",
            key_id="test-key",
            key_manager=key_manager,
            constraints=sample_constraints,
        )
        assert record.payload["signer_key_id"] == "test-key"


class TestGenesisValidation:
    """Test input validation for genesis creation."""

    def test_empty_session_id_raises(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        with pytest.raises(ValueError, match="session_id"):
            create_genesis(
                session_id="",
                authority_id="user",
                key_id="test-key",
                key_manager=key_manager,
                constraints=sample_constraints,
            )

    def test_empty_authority_id_raises(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        with pytest.raises(ValueError, match="authority_id"):
            create_genesis(
                session_id="sess-001",
                authority_id="",
                key_id="test-key",
                key_manager=key_manager,
                constraints=sample_constraints,
            )

    def test_empty_key_id_raises(self, key_manager, sample_constraints):
        from praxis.trust.genesis import create_genesis

        with pytest.raises(ValueError, match="key_id"):
            create_genesis(
                session_id="sess-001",
                authority_id="user",
                key_id="",
                key_manager=key_manager,
                constraints=sample_constraints,
            )
