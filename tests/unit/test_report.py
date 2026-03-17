# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.export.report — audit report generator."""

import json

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session_data():
    """Session data for report tests."""
    return {
        "session_id": "sess-report-001",
        "workspace_id": "ws-test",
        "domain": "coc",
        "state": "archived",
        "constraint_envelope": {
            "financial": {"max_spend": 100.0},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        },
        "created_at": "2026-03-15T10:00:00.000000Z",
        "ended_at": "2026-03-15T11:00:00.000000Z",
    }


@pytest.fixture
def chain_entries(key_manager, sample_constraints):
    """Trust chain entries for report tests."""
    from praxis.trust.genesis import create_genesis

    genesis = create_genesis(
        session_id="sess-report-001",
        authority_id="user-1",
        key_id="test-key",
        key_manager=key_manager,
        constraints=sample_constraints,
    )
    return [
        {
            "payload": genesis.payload,
            "content_hash": genesis.content_hash,
            "signature": genesis.signature,
            "signer_key_id": genesis.signer_key_id,
            "parent_hash": None,
        },
    ]


@pytest.fixture
def deliberation_records():
    """Sample deliberation records for report tests."""
    return [
        {
            "record_id": "rec-r001",
            "session_id": "sess-report-001",
            "record_type": "decision",
            "content": {"decision": "Adopt TDD methodology"},
            "reasoning_trace": {
                "rationale": "Ensures quality",
                "actor": "human",
                "confidence": 0.9,
            },
            "reasoning_hash": "d" * 64,
            "parent_record_id": None,
            "actor": "human",
            "confidence": 0.9,
            "created_at": "2026-03-15T10:05:00.000000Z",
        },
    ]


@pytest.fixture
def constraint_events():
    """Sample constraint events for report tests."""
    return [
        {
            "action": "read_file",
            "resource": "/src/main.py",
            "verdict": "auto_approved",
            "dimension": "operational",
            "utilization": 0.1,
            "reason": "Action is allowed",
            "evaluated_at": "2026-03-15T10:06:00.000000Z",
        },
    ]


# ---------------------------------------------------------------------------
# AuditReportGenerator HTML tests
# ---------------------------------------------------------------------------


class TestAuditReportGeneratorHTML:
    """Test HTML report generation."""

    def test_html_report_contains_session_info(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "sess-report-001" in html

    def test_html_report_contains_deliberation_info(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        assert "Adopt TDD methodology" in html
        assert "decision" in html.lower()

    def test_html_report_contains_chain_info(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        # Should reference the chain length or entries
        assert "1" in html  # 1 chain entry
        assert "genesis" in html.lower()

    def test_html_report_contains_constraint_info(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        assert "auto_approved" in html or "auto-approved" in html.lower()

    def test_html_report_is_self_contained(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        """HTML report must have embedded styles -- no CDN links."""
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        assert "<style>" in html
        assert "cdn" not in html.lower()

    def test_html_report_references_praxis(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        assert "Praxis" in html
        assert "Terrene Foundation" in html

    def test_html_report_with_empty_deliberation(
        self, session_data, chain_entries, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=[],
            constraints=constraint_events,
        )
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_html_report_with_empty_constraints(
        self, session_data, chain_entries, deliberation_records
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        html = generator.generate_html(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=[],
        )
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# AuditReportGenerator JSON tests
# ---------------------------------------------------------------------------


class TestAuditReportGeneratorJSON:
    """Test JSON report generation."""

    def test_json_report_has_correct_structure(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        assert isinstance(report, dict)
        assert "session" in report
        assert "chain_summary" in report
        assert "deliberation_summary" in report
        assert "constraint_summary" in report
        assert "generated_at" in report

    def test_json_report_session_has_expected_fields(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        session = report["session"]
        assert session["session_id"] == "sess-report-001"
        assert session["domain"] == "coc"
        assert "duration_seconds" in session

    def test_json_report_chain_summary(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        chain_summary = report["chain_summary"]
        assert "total_entries" in chain_summary
        assert chain_summary["total_entries"] == 1

    def test_json_report_deliberation_summary(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        delib_summary = report["deliberation_summary"]
        assert "total_records" in delib_summary
        assert delib_summary["total_records"] == 1
        assert "by_type" in delib_summary
        assert delib_summary["by_type"].get("decision", 0) == 1

    def test_json_report_constraint_summary(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        constraint_summary = report["constraint_summary"]
        assert "total_evaluations" in constraint_summary
        assert constraint_summary["total_evaluations"] == 1
        assert "by_verdict" in constraint_summary

    def test_json_report_is_serializable(
        self, session_data, chain_entries, deliberation_records, constraint_events
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=deliberation_records,
            constraints=constraint_events,
        )
        # Must be valid JSON
        json_str = json.dumps(report)
        parsed = json.loads(json_str)
        assert parsed["session"]["session_id"] == "sess-report-001"

    def test_json_report_with_empty_data(
        self,
        session_data,
        chain_entries,
    ):
        from praxis.export.report import AuditReportGenerator

        generator = AuditReportGenerator()
        report = generator.generate_json(
            session_data=session_data,
            chain=chain_entries,
            deliberation=[],
            constraints=[],
        )
        assert report["deliberation_summary"]["total_records"] == 0
        assert report["constraint_summary"]["total_evaluations"] == 0
