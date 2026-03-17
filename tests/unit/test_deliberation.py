# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.core.deliberation — hash-chained deliberation capture."""

import hashlib

import jcs
import pytest


# ---------------------------------------------------------------------------
# DeliberationEngine.record_decision
# ---------------------------------------------------------------------------


class TestRecordDecision:
    """Test recording decision deliberation records."""

    def test_record_decision_returns_dict(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
        )
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Better for production workloads",
            actor="human",
        )
        assert isinstance(record, dict)

    def test_record_decision_has_record_id(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Better for production",
        )
        assert "record_id" in record
        assert len(record["record_id"]) > 0

    def test_record_decision_type_is_decision(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Reliability",
        )
        assert record["record_type"] == "decision"

    def test_record_decision_stores_session_id(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-042", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="choice",
            rationale="reason",
        )
        assert record["session_id"] == "sess-042"

    def test_record_decision_stores_content(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Better for production",
            alternatives=["SQLite", "MySQL"],
        )
        assert record["content"]["decision"] == "Use PostgreSQL"
        assert record["content"]["alternatives"] == ["SQLite", "MySQL"]

    def test_record_decision_stores_reasoning_trace(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="Use PostgreSQL",
            rationale="Production-grade reliability",
            actor="human",
            confidence=0.9,
        )
        assert record["reasoning_trace"]["rationale"] == "Production-grade reliability"
        assert record["reasoning_trace"]["actor"] == "human"
        assert record["reasoning_trace"]["confidence"] == 0.9

    def test_record_decision_actor_default_is_human(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="choice",
            rationale="reason",
        )
        assert record["actor"] == "human"

    def test_record_decision_custom_actor(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="choice",
            rationale="reason",
            actor="ai",
        )
        assert record["actor"] == "ai"

    def test_record_decision_has_created_at(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="choice",
            rationale="reason",
        )
        assert "created_at" in record
        assert record["created_at"].endswith("Z")


# ---------------------------------------------------------------------------
# DeliberationEngine.record_observation
# ---------------------------------------------------------------------------


class TestRecordObservation:
    """Test recording observation deliberation records."""

    def test_record_observation_type(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_observation(
            observation="Code coverage is at 82%",
            actor="ai",
        )
        assert record["record_type"] == "observation"

    def test_record_observation_stores_content(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_observation(
            observation="Test suite passes",
            actor="ai",
            confidence=0.95,
        )
        assert record["content"]["observation"] == "Test suite passes"
        assert record["confidence"] == 0.95

    def test_record_observation_default_actor_is_ai(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_observation(
            observation="Something observed",
        )
        assert record["actor"] == "ai"


# ---------------------------------------------------------------------------
# DeliberationEngine.record_escalation
# ---------------------------------------------------------------------------


class TestRecordEscalation:
    """Test recording escalation deliberation records."""

    def test_record_escalation_type(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_escalation(
            issue="Security vulnerability found",
            context="CVE-2026-1234 in dependency",
        )
        assert record["record_type"] == "escalation"

    def test_record_escalation_stores_content(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_escalation(
            issue="Constraint exceeded",
            context="Financial limit approached",
            actor="system",
        )
        assert record["content"]["issue"] == "Constraint exceeded"
        assert record["content"]["context"] == "Financial limit approached"

    def test_record_escalation_default_actor_is_system(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_escalation(
            issue="issue",
            context="context",
        )
        assert record["actor"] == "system"


# ---------------------------------------------------------------------------
# Hash chain integrity
# ---------------------------------------------------------------------------


class TestHashChainIntegrity:
    """Test that deliberation records form a proper hash chain."""

    def test_first_record_has_no_parent(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(decision="first", rationale="first reason")
        assert record["parent_record_id"] is None

    def test_second_record_links_to_first(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        first = engine.record_decision(decision="first", rationale="reason")
        second = engine.record_observation(observation="second note")
        assert second["parent_record_id"] == first["reasoning_hash"]

    def test_third_record_links_to_second(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="first", rationale="reason")
        second = engine.record_observation(observation="second")
        third = engine.record_escalation(issue="third", context="ctx")
        assert third["parent_record_id"] == second["reasoning_hash"]

    def test_reasoning_hash_is_sha256_of_jcs_content_and_reasoning(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="Use Redis",
            rationale="Fast caching",
            alternatives=["Memcached"],
            confidence=0.8,
        )
        # Reconstruct the hash from content + reasoning_trace
        hashable = {
            "content": record["content"],
            "reasoning_trace": record["reasoning_trace"],
        }
        canonical = jcs.canonicalize(hashable)
        expected_hash = hashlib.sha256(canonical).hexdigest()
        assert record["reasoning_hash"] == expected_hash

    def test_chain_of_five_records(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        records = []
        for i in range(5):
            r = engine.record_decision(decision=f"decision-{i}", rationale=f"reason-{i}")
            records.append(r)

        # First has no parent
        assert records[0]["parent_record_id"] is None
        # Each subsequent links to previous
        for i in range(1, 5):
            assert records[i]["parent_record_id"] == records[i - 1]["reasoning_hash"]


# ---------------------------------------------------------------------------
# Confidence validation
# ---------------------------------------------------------------------------


class TestConfidenceValidation:
    """Test that confidence values are properly validated."""

    def test_confidence_none_is_valid(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(decision="choice", rationale="reason", confidence=None)
        assert record["confidence"] is None

    def test_confidence_zero_is_valid(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(decision="choice", rationale="reason", confidence=0.0)
        assert record["confidence"] == 0.0

    def test_confidence_one_is_valid(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(decision="choice", rationale="reason", confidence=1.0)
        assert record["confidence"] == 1.0

    def test_confidence_mid_range_is_valid(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(decision="choice", rationale="reason", confidence=0.5)
        assert record["confidence"] == 0.5

    def test_confidence_negative_raises(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        with pytest.raises(ValueError, match="[Cc]onfidence"):
            engine.record_decision(decision="choice", rationale="reason", confidence=-0.1)

    def test_confidence_above_one_raises(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        with pytest.raises(ValueError, match="[Cc]onfidence"):
            engine.record_decision(decision="choice", rationale="reason", confidence=1.1)

    def test_confidence_way_out_of_range_raises(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        with pytest.raises(ValueError, match="[Cc]onfidence"):
            engine.record_observation(observation="note", confidence=5.0)


# ---------------------------------------------------------------------------
# Signing and audit anchors
# ---------------------------------------------------------------------------


class TestSigningAndAnchors:
    """Test that records are signed when a key_manager is available."""

    def test_record_has_anchor_id_with_key_manager(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(decision="choice", rationale="reason")
        assert record["anchor_id"] is not None

    def test_record_has_no_anchor_without_key_manager(self):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(session_id="sess-001", key_manager=None)
        record = engine.record_decision(decision="choice", rationale="reason")
        assert record["anchor_id"] is None


# ---------------------------------------------------------------------------
# DeliberationEngine.get_timeline
# ---------------------------------------------------------------------------


class TestGetTimeline:
    """Test deliberation timeline retrieval."""

    def test_get_timeline_returns_all_records(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_observation(observation="o1")
        engine.record_escalation(issue="e1", context="c1")

        records, total = engine.get_timeline()
        assert len(records) == 3
        assert total == 3

    def test_get_timeline_filter_by_type(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_observation(observation="o1")
        engine.record_decision(decision="d2", rationale="r2")

        records, total = engine.get_timeline(record_type="decision")
        assert len(records) == 2
        assert total == 2
        assert all(r["record_type"] == "decision" for r in records)

    def test_get_timeline_with_limit(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        for i in range(10):
            engine.record_decision(decision=f"d{i}", rationale=f"r{i}")

        records, total = engine.get_timeline(limit=3)
        assert len(records) == 3
        assert total == 10

    def test_get_timeline_with_offset(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        for i in range(5):
            engine.record_decision(decision=f"d{i}", rationale=f"r{i}")

        records, total = engine.get_timeline(offset=2, limit=2)
        assert len(records) == 2
        assert total == 5
        # Should be the 3rd and 4th records (0-indexed: 2 and 3)
        assert records[0]["content"]["decision"] == "d2"
        assert records[1]["content"]["decision"] == "d3"

    def test_get_timeline_empty(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        records, total = engine.get_timeline()
        assert records == []
        assert total == 0

    def test_get_timeline_preserves_order(self, key_manager):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        engine.record_decision(decision="first", rationale="r")
        engine.record_observation(observation="second")
        engine.record_escalation(issue="third", context="c")

        records, _ = engine.get_timeline()
        assert records[0]["content"]["decision"] == "first"
        assert records[1]["content"]["observation"] == "second"
        assert records[2]["content"]["issue"] == "third"


# ---------------------------------------------------------------------------
# Domain capture config integration (M02-03)
# ---------------------------------------------------------------------------


class TestCaptureConfig:
    """Test that domain capture config influences DeliberationEngine behavior."""

    @pytest.fixture
    def coc_capture_config(self):
        """COC-style capture config for testing."""
        return {
            "auto_capture": ["file_changes", "tool_calls"],
            "decision_types": ["scope", "architecture", "risk", "process"],
            "observation_targets": ["workflow_patterns", "error_patterns", "tool_usage"],
        }

    @pytest.fixture
    def coe_capture_config(self):
        """COE-style capture config for testing."""
        return {
            "auto_capture": ["ai_interactions", "revision_history"],
            "decision_types": ["scope", "methodology", "sources", "interpretation"],
            "observation_targets": ["time_on_task", "revision_patterns", "source_usage"],
        }

    def test_capture_config_is_optional(self, key_manager):
        """Engine works normally when no capture_config is provided."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        assert engine.capture_config is None
        assert engine._decision_types is None
        assert engine.observation_targets is None

        # Should still record decisions without issues
        record = engine.record_decision(decision="choice", rationale="reason")
        assert record["record_type"] == "decision"

    def test_capture_config_stores_decision_types(self, key_manager, coc_capture_config):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coc_capture_config,
        )
        assert engine._decision_types == ["scope", "architecture", "risk", "process"]

    def test_capture_config_stores_observation_targets(self, key_manager, coc_capture_config):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coc_capture_config,
        )
        assert engine.observation_targets == [
            "workflow_patterns",
            "error_patterns",
            "tool_usage",
        ]

    def test_valid_decision_type_is_accepted(self, key_manager, coc_capture_config):
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coc_capture_config,
        )
        record = engine.record_decision(
            decision="Use React",
            rationale="Team expertise",
            decision_type="architecture",
        )
        assert record["content"]["decision_type"] == "architecture"

    def test_invalid_decision_type_raises(self, key_manager, coc_capture_config):
        from praxis.core.deliberation import DeliberationEngine, InvalidDecisionTypeError

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coc_capture_config,
        )
        with pytest.raises(InvalidDecisionTypeError, match="not_a_valid_type"):
            engine.record_decision(
                decision="choice",
                rationale="reason",
                decision_type="not_a_valid_type",
            )

    def test_decision_type_none_skips_validation(self, key_manager, coc_capture_config):
        """When decision_type is None, no validation is performed even with capture config."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coc_capture_config,
        )
        record = engine.record_decision(decision="choice", rationale="reason", decision_type=None)
        assert "decision_type" not in record["content"]

    def test_decision_type_without_capture_config_is_accepted(self, key_manager):
        """Without capture_config, any decision_type string is accepted."""
        from praxis.core.deliberation import DeliberationEngine

        engine = DeliberationEngine(
            session_id="sess-001", key_manager=key_manager, key_id="test-key"
        )
        record = engine.record_decision(
            decision="choice",
            rationale="reason",
            decision_type="anything_goes",
        )
        assert record["content"]["decision_type"] == "anything_goes"

    def test_coe_decision_types_validated(self, key_manager, coe_capture_config):
        from praxis.core.deliberation import DeliberationEngine, InvalidDecisionTypeError

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coe_capture_config,
        )
        # Valid for COE
        record = engine.record_decision(
            decision="Use interviews",
            rationale="Primary sources",
            decision_type="methodology",
        )
        assert record["content"]["decision_type"] == "methodology"

        # Invalid for COE (architecture is COC, not COE)
        with pytest.raises(InvalidDecisionTypeError):
            engine.record_decision(
                decision="Use React",
                rationale="Team expertise",
                decision_type="architecture",
            )

    def test_validate_decision_type_method(self, key_manager, coc_capture_config):
        from praxis.core.deliberation import DeliberationEngine, InvalidDecisionTypeError

        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=coc_capture_config,
        )
        # Valid types should not raise
        engine.validate_decision_type("scope")
        engine.validate_decision_type("architecture")
        engine.validate_decision_type("risk")
        engine.validate_decision_type("process")

        # Invalid type should raise
        with pytest.raises(InvalidDecisionTypeError):
            engine.validate_decision_type("budget")

    def test_invalid_decision_type_error_message(self, key_manager, coc_capture_config):
        from praxis.core.deliberation import InvalidDecisionTypeError

        err = InvalidDecisionTypeError("budget", ["scope", "architecture"])
        assert "budget" in str(err)
        assert "scope" in str(err)

    def test_capture_config_without_decision_types_key(self, key_manager):
        """If capture_config has no decision_types, all types are accepted."""
        from praxis.core.deliberation import DeliberationEngine

        config = {
            "auto_capture": ["file_changes"],
            "observation_targets": ["workflow_patterns"],
        }
        engine = DeliberationEngine(
            session_id="sess-001",
            key_manager=key_manager,
            key_id="test-key",
            capture_config=config,
        )
        assert engine._decision_types is None
        # Any type should be accepted
        record = engine.record_decision(
            decision="choice", rationale="reason", decision_type="anything"
        )
        assert record["content"]["decision_type"] == "anything"
