# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.trust.audit — audit anchor chain management."""

import base64
import hashlib

import jcs
import pytest


class TestAuditAnchorDataclass:
    """Test that AuditAnchor holds all required fields."""

    def test_audit_anchor_has_required_fields(self):
        from praxis.trust.audit import AuditAnchor

        anchor = AuditAnchor(
            anchor_id="anchor-001",
            session_id="sess-001",
            action="read_file",
            resource="src/main.py",
            actor="ai",
            result="auto_approved",
            reasoning_hash=None,
            payload={"type": "anchor"},
            content_hash="a" * 64,
            signature="sig",
            signer_key_id="key-1",
            parent_hash=None,
            sequence=0,
            created_at="2026-03-15T10:00:00.000000Z",
        )
        assert anchor.anchor_id == "anchor-001"
        assert anchor.session_id == "sess-001"
        assert anchor.sequence == 0
        assert anchor.parent_hash is None

    def test_audit_anchor_with_parent_hash(self):
        from praxis.trust.audit import AuditAnchor

        anchor = AuditAnchor(
            anchor_id="anchor-002",
            session_id="sess-001",
            action="write_file",
            resource="src/new.py",
            actor="ai",
            result="flagged",
            reasoning_hash="r" * 64,
            payload={"type": "anchor"},
            content_hash="c" * 64,
            signature="sig2",
            signer_key_id="key-1",
            parent_hash="a" * 64,
            sequence=1,
            created_at="2026-03-15T10:01:00.000000Z",
        )
        assert anchor.parent_hash == "a" * 64
        assert anchor.sequence == 1


class TestAuditChainCreation:
    """Test AuditChain creation and anchor appending."""

    def test_new_chain_is_empty(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        assert chain.length == 0
        assert chain.head_hash is None

    def test_append_first_anchor_has_no_parent(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(
            action="read_file",
            actor="ai",
            result="auto_approved",
            resource="src/main.py",
        )
        assert anchor.parent_hash is None
        assert anchor.sequence == 0
        assert chain.length == 1

    def test_second_anchor_chains_to_first(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        a1 = chain.append(action="read_file", actor="ai", result="auto_approved")
        a2 = chain.append(action="write_file", actor="ai", result="flagged")
        assert a2.parent_hash == a1.content_hash
        assert a2.sequence == 1
        assert chain.length == 2

    def test_head_hash_updates_after_append(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        assert chain.head_hash is None
        a1 = chain.append(action="read_file", actor="ai", result="auto_approved")
        assert chain.head_hash == a1.content_hash
        a2 = chain.append(action="write_file", actor="ai", result="flagged")
        assert chain.head_hash == a2.content_hash

    def test_content_hash_is_sha256_of_jcs_payload(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(action="read_file", actor="ai", result="auto_approved")
        canonical = jcs.canonicalize(anchor.payload)
        expected_hash = hashlib.sha256(canonical).hexdigest()
        assert anchor.content_hash == expected_hash

    def test_signature_verifies(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(action="read_file", actor="ai", result="auto_approved")
        hash_bytes = bytes.fromhex(anchor.content_hash)
        sig_bytes = base64.urlsafe_b64decode(anchor.signature)
        assert key_manager.verify("test-key", hash_bytes, sig_bytes) is True

    def test_anchor_stores_session_id(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="my-session", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(action="read_file", actor="ai", result="auto_approved")
        assert anchor.session_id == "my-session"

    def test_anchor_stores_action_and_actor(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(
            action="deploy_service",
            actor="human",
            result="held",
            resource="production",
        )
        assert anchor.action == "deploy_service"
        assert anchor.actor == "human"
        assert anchor.result == "held"
        assert anchor.resource == "production"

    def test_anchor_accepts_reasoning_hash(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(
            action="read_file",
            actor="ai",
            result="auto_approved",
            reasoning_hash="abc123" * 10 + "abcd",
        )
        assert anchor.reasoning_hash == "abc123" * 10 + "abcd"


class TestAuditChainLongChain:
    """Test building chains with multiple entries."""

    def test_ten_entry_chain_maintains_sequence(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        for i in range(10):
            anchor = chain.append(
                action=f"action_{i}",
                actor="ai",
                result="auto_approved",
            )
            assert anchor.sequence == i
        assert chain.length == 10

    def test_chain_parent_hashes_form_linked_list(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchors = []
        for i in range(5):
            a = chain.append(action=f"action_{i}", actor="ai", result="auto_approved")
            anchors.append(a)

        # First has no parent
        assert anchors[0].parent_hash is None
        # Each subsequent links to previous
        for i in range(1, 5):
            assert anchors[i].parent_hash == anchors[i - 1].content_hash


class TestAuditChainVerification:
    """Test chain integrity verification."""

    def test_empty_chain_is_valid(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        valid, breaks = chain.verify_integrity()
        assert valid is True
        assert breaks == []

    def test_single_entry_chain_is_valid(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        chain.append(action="read_file", actor="ai", result="auto_approved")
        valid, breaks = chain.verify_integrity()
        assert valid is True
        assert breaks == []

    def test_multi_entry_chain_is_valid(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        for i in range(5):
            chain.append(action=f"action_{i}", actor="ai", result="auto_approved")
        valid, breaks = chain.verify_integrity()
        assert valid is True
        assert breaks == []

    def test_tampered_content_hash_detected(self, key_manager):
        from praxis.persistence.db_ops import db_update
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        a1 = chain.append(action="read_file", actor="ai", result="auto_approved")
        chain.append(action="write_file", actor="ai", result="flagged")

        # Tamper with the first anchor's content hash directly in the DB
        db_update("TrustChainEntry", a1.anchor_id, {"content_hash": "tampered" + "0" * 56})

        valid, breaks = chain.verify_integrity()
        assert valid is False
        assert len(breaks) > 0

    def test_tampered_parent_hash_detected(self, key_manager):
        from praxis.persistence.db_ops import db_update
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        chain.append(action="read_file", actor="ai", result="auto_approved")
        a2 = chain.append(action="write_file", actor="ai", result="flagged")

        # Tamper with the second anchor's parent hash directly in the DB
        db_update("TrustChainEntry", a2.anchor_id, {"parent_hash": "wrong_hash" + "0" * 54})

        valid, breaks = chain.verify_integrity()
        assert valid is False
        assert len(breaks) > 0


class TestAuditChainPayload:
    """Test that anchor payloads contain required information."""

    def test_payload_has_type_and_version(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(action="read_file", actor="ai", result="auto_approved")
        assert anchor.payload["type"] == "audit_anchor"
        assert anchor.payload["version"] == "1.0"

    def test_payload_has_session_and_action(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-002", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(
            action="write_file",
            actor="human",
            result="approved",
            resource="/src/main.py",
        )
        assert anchor.payload["session_id"] == "sess-002"
        assert anchor.payload["action"] == "write_file"
        assert anchor.payload["actor"] == "human"
        assert anchor.payload["result"] == "approved"
        assert anchor.payload["resource"] == "/src/main.py"

    def test_payload_has_sequence_and_created_at(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(action="read_file", actor="ai", result="auto_approved")
        assert anchor.payload["sequence"] == 0
        assert "created_at" in anchor.payload

    def test_extra_payload_is_merged(self, key_manager):
        from praxis.trust.audit import AuditChain

        chain = AuditChain(session_id="sess-001", key_id="test-key", key_manager=key_manager)
        anchor = chain.append(
            action="read_file",
            actor="ai",
            result="auto_approved",
            extra_payload={"custom_field": "custom_value"},
        )
        assert anchor.payload["custom_field"] == "custom_value"
