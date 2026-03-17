# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.persistence.archive — session export/import."""

import pytest


# ---------------------------------------------------------------------------
# export_session
# ---------------------------------------------------------------------------


class TestExportSession:
    """Test exporting sessions as portable archive dicts."""

    def test_export_session_returns_dict(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            domain="coc",
            constraints=sample_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        enforcer = ConstraintEnforcer(sample_constraints)

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert isinstance(archive, dict)

    def test_export_session_contains_session_data(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            domain="coe",
            constraints=sample_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        enforcer = ConstraintEnforcer(sample_constraints)

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert "session" in archive
        assert archive["session"]["session_id"] == session["session_id"]
        assert archive["session"]["domain"] == "coe"

    def test_export_session_contains_deliberation(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        engine.record_decision(decision="d1", rationale="r1")
        engine.record_observation(observation="o1")
        enforcer = ConstraintEnforcer(sample_constraints)

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert "deliberation" in archive
        assert len(archive["deliberation"]) == 2

    def test_export_session_contains_constraint_events(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        enforcer = ConstraintEnforcer(sample_constraints)
        enforcer.evaluate("read", resource="/src/file.py")

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert "constraint_events" in archive
        assert len(archive["constraint_events"]) == 1

    def test_export_session_has_version_and_timestamp(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001", constraints=sample_constraints)
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        enforcer = ConstraintEnforcer(sample_constraints)

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )
        assert "version" in archive
        assert "exported_at" in archive

    def test_export_session_not_found_raises(self, key_manager):
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        with pytest.raises(KeyError, match="nonexistent"):
            export_session(
                session_id="nonexistent",
                session_manager=mgr,
                deliberation_engine=None,
                constraint_enforcer=None,
            )


# ---------------------------------------------------------------------------
# import_session
# ---------------------------------------------------------------------------


class TestImportSession:
    """Test importing sessions from archive dicts."""

    def test_import_session_returns_session_id(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session, import_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001", constraints=sample_constraints)
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        engine.record_decision(decision="d1", rationale="r1")
        enforcer = ConstraintEnforcer(sample_constraints)

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )

        new_mgr = SessionManager(key_manager=None)
        new_session_id = import_session(archive, session_manager=new_mgr)
        assert isinstance(new_session_id, str)
        assert len(new_session_id) > 0

    def test_import_session_creates_session_in_manager(self, key_manager, sample_constraints):
        from praxis.core.constraint import ConstraintEnforcer
        from praxis.core.deliberation import DeliberationEngine
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import export_session, import_session

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            domain="coe",
            constraints=sample_constraints,
        )
        engine = DeliberationEngine(
            session_id=session["session_id"],
            key_manager=key_manager,
            key_id="test-key",
        )
        enforcer = ConstraintEnforcer(sample_constraints)

        archive = export_session(
            session_id=session["session_id"],
            session_manager=mgr,
            deliberation_engine=engine,
            constraint_enforcer=enforcer,
        )

        new_mgr = SessionManager(key_manager=None)
        new_session_id = import_session(archive, session_manager=new_mgr)
        imported = new_mgr.get_session(new_session_id)
        assert imported["workspace_id"] == "ws-001"
        assert imported["domain"] == "coe"

    def test_import_session_invalid_archive_raises(self):
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import import_session

        mgr = SessionManager(key_manager=None)
        with pytest.raises(ValueError, match="[Ii]nvalid|[Mm]issing"):
            import_session({}, session_manager=mgr)

    def test_import_session_missing_session_key_raises(self):
        from praxis.core.session import SessionManager
        from praxis.persistence.archive import import_session

        mgr = SessionManager(key_manager=None)
        with pytest.raises(ValueError, match="session"):
            import_session(
                {"version": "1.0", "exported_at": "2026-01-01T00:00:00Z"},
                session_manager=mgr,
            )
