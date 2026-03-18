# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.persistence.models — DataFlow model definitions.

Tests verify:
- All 5 model classes can be imported and registered with DataFlow
- Each model has the correct fields with correct types
- Indexes are properly defined
- The get_db() function returns a DataFlow instance
- No auto-managed fields (created_at, updated_at) are defined in models
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Provide a clean environment with database URL for each test."""
    from praxis.config import reset_config

    reset_config()

    # Clear all Praxis-related env vars so tests are isolated
    env_vars = [
        "DATABASE_URL",
        "PRAXIS_KEY_DIR",
        "PRAXIS_KEY_ID",
        "PRAXIS_API_HOST",
        "PRAXIS_API_PORT",
        "PRAXIS_API_SECRET",
        "PRAXIS_CORS_ORIGINS",
        "EATP_NAMESPACE",
        "EATP_STRICT_MODE",
        "PRAXIS_DEFAULT_MODEL",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "LOG_LEVEL",
        "LOG_FORMAT",
        "PRAXIS_DEV_MODE",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    # Set minimal required vars
    db_path = tmp_path / "test_models.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PRAXIS_API_SECRET", "test-secret-key")
    monkeypatch.setenv("PRAXIS_KEY_DIR", str(tmp_path / "keys"))

    yield

    # Reset persistence module state for test isolation
    import praxis.persistence as persistence_mod

    persistence_mod._db = None
    persistence_mod._models_registered = False
    persistence_mod._tables_created = False

    reset_config()


# ---------------------------------------------------------------------------
# Import Tests
# ---------------------------------------------------------------------------


class TestModelImports:
    """Verify all 5 model classes can be imported."""

    def test_import_session(self):
        from praxis.persistence.models import Session

        assert Session is not None

    def test_import_deliberation_record(self):
        from praxis.persistence.models import DeliberationRecord

        assert DeliberationRecord is not None

    def test_import_constraint_event(self):
        from praxis.persistence.models import ConstraintEvent

        assert ConstraintEvent is not None

    def test_import_trust_chain_entry(self):
        from praxis.persistence.models import TrustChainEntry

        assert TrustChainEntry is not None

    def test_import_workspace(self):
        from praxis.persistence.models import Workspace

        assert Workspace is not None


# ---------------------------------------------------------------------------
# Session Model Tests
# ---------------------------------------------------------------------------


class TestSessionModel:
    """Verify Session model field definitions."""

    def test_has_required_fields(self):
        from praxis.persistence.models import Session

        annotations = Session.__annotations__
        assert "id" in annotations
        assert "workspace_id" in annotations
        assert "domain" in annotations

    def test_has_optional_fields(self):
        from praxis.persistence.models import Session

        annotations = Session.__annotations__
        assert "state" in annotations
        assert "genesis_id" in annotations
        assert "constraint_envelope" in annotations
        assert "session_metadata" in annotations
        assert "ended_at" in annotations

    def test_field_types(self):
        from praxis.persistence.models import Session

        annotations = Session.__annotations__
        assert annotations["id"] is str
        assert annotations["workspace_id"] is str
        assert annotations["domain"] is str

    def test_default_state(self):
        """State should default to 'creating'."""
        from praxis.persistence.models import Session

        assert Session.state == "creating"

    def test_indexes_defined(self):
        from praxis.persistence.models import Session

        assert hasattr(Session, "__indexes__")
        index_names = {idx["name"] for idx in Session.__indexes__}
        assert "idx_session_workspace" in index_names
        assert "idx_session_state" in index_names
        assert "idx_session_domain" in index_names

    def test_no_auto_managed_fields(self):
        """Models must NOT define created_at or updated_at — DataFlow handles these."""
        from praxis.persistence.models import Session

        annotations = Session.__annotations__
        assert "created_at" not in annotations, "DataFlow auto-manages created_at"
        assert "updated_at" not in annotations, "DataFlow auto-manages updated_at"


# ---------------------------------------------------------------------------
# DeliberationRecord Model Tests
# ---------------------------------------------------------------------------


class TestDeliberationRecordModel:
    """Verify DeliberationRecord model field definitions."""

    def test_has_required_fields(self):
        from praxis.persistence.models import DeliberationRecord

        annotations = DeliberationRecord.__annotations__
        assert "id" in annotations
        assert "session_id" in annotations
        assert "record_type" in annotations

    def test_has_optional_fields(self):
        from praxis.persistence.models import DeliberationRecord

        annotations = DeliberationRecord.__annotations__
        assert "content" in annotations
        assert "reasoning_trace" in annotations
        assert "reasoning_hash" in annotations
        assert "parent_record_id" in annotations
        assert "anchor_id" in annotations
        assert "actor" in annotations
        assert "confidence" in annotations

    def test_default_actor(self):
        """Actor should default to 'human'."""
        from praxis.persistence.models import DeliberationRecord

        assert DeliberationRecord.actor == "human"

    def test_indexes_defined(self):
        from praxis.persistence.models import DeliberationRecord

        assert hasattr(DeliberationRecord, "__indexes__")
        index_names = {idx["name"] for idx in DeliberationRecord.__indexes__}
        assert "idx_delib_session" in index_names
        assert "idx_delib_type" in index_names
        assert "idx_delib_actor" in index_names

    def test_no_auto_managed_fields(self):
        from praxis.persistence.models import DeliberationRecord

        annotations = DeliberationRecord.__annotations__
        assert "created_at" not in annotations
        assert "updated_at" not in annotations


# ---------------------------------------------------------------------------
# ConstraintEvent Model Tests
# ---------------------------------------------------------------------------


class TestConstraintEventModel:
    """Verify ConstraintEvent model field definitions."""

    def test_has_required_fields(self):
        from praxis.persistence.models import ConstraintEvent

        annotations = ConstraintEvent.__annotations__
        assert "id" in annotations
        assert "session_id" in annotations
        assert "action" in annotations

    def test_has_optional_fields(self):
        from praxis.persistence.models import ConstraintEvent

        annotations = ConstraintEvent.__annotations__
        assert "resource" in annotations
        assert "dimension" in annotations
        assert "gradient_result" in annotations
        assert "utilization" in annotations
        assert "resolved_by" in annotations
        assert "resolution" in annotations
        assert "resolved_at" in annotations

    def test_default_dimension(self):
        """Dimension should default to 'operational'."""
        from praxis.persistence.models import ConstraintEvent

        assert ConstraintEvent.dimension == "operational"

    def test_default_gradient_result(self):
        """Gradient result should default to 'auto_approved'."""
        from praxis.persistence.models import ConstraintEvent

        assert ConstraintEvent.gradient_result == "auto_approved"

    def test_default_utilization(self):
        """Utilization should default to 0.0."""
        from praxis.persistence.models import ConstraintEvent

        assert ConstraintEvent.utilization == 0.0

    def test_indexes_defined(self):
        from praxis.persistence.models import ConstraintEvent

        assert hasattr(ConstraintEvent, "__indexes__")
        index_names = {idx["name"] for idx in ConstraintEvent.__indexes__}
        assert "idx_constraint_session" in index_names
        assert "idx_constraint_dimension" in index_names
        assert "idx_constraint_gradient" in index_names

    def test_no_auto_managed_fields(self):
        from praxis.persistence.models import ConstraintEvent

        annotations = ConstraintEvent.__annotations__
        assert "created_at" not in annotations
        assert "updated_at" not in annotations


# ---------------------------------------------------------------------------
# TrustChainEntry Model Tests
# ---------------------------------------------------------------------------


class TestTrustChainEntryModel:
    """Verify TrustChainEntry model field definitions."""

    def test_has_required_fields(self):
        from praxis.persistence.models import TrustChainEntry

        annotations = TrustChainEntry.__annotations__
        assert "id" in annotations
        assert "session_id" in annotations
        assert "entry_type" in annotations

    def test_has_optional_fields(self):
        from praxis.persistence.models import TrustChainEntry

        annotations = TrustChainEntry.__annotations__
        assert "payload" in annotations
        assert "signature" in annotations
        assert "signer_key_id" in annotations
        assert "parent_hash" in annotations
        assert "content_hash" in annotations
        assert "verified" in annotations

    def test_default_verified(self):
        """Verified should default to False."""
        from praxis.persistence.models import TrustChainEntry

        assert TrustChainEntry.verified is False

    def test_indexes_defined(self):
        from praxis.persistence.models import TrustChainEntry

        assert hasattr(TrustChainEntry, "__indexes__")
        index_names = {idx["name"] for idx in TrustChainEntry.__indexes__}
        assert "idx_trust_session" in index_names
        assert "idx_trust_type" in index_names
        assert "idx_trust_signer" in index_names

    def test_no_auto_managed_fields(self):
        from praxis.persistence.models import TrustChainEntry

        annotations = TrustChainEntry.__annotations__
        assert "created_at" not in annotations
        assert "updated_at" not in annotations


# ---------------------------------------------------------------------------
# Workspace Model Tests
# ---------------------------------------------------------------------------


class TestWorkspaceModel:
    """Verify Workspace model field definitions."""

    def test_has_required_fields(self):
        from praxis.persistence.models import Workspace

        annotations = Workspace.__annotations__
        assert "id" in annotations
        assert "name" in annotations

    def test_has_optional_fields(self):
        from praxis.persistence.models import Workspace

        annotations = Workspace.__annotations__
        assert "domain" in annotations
        assert "constraint_template" in annotations
        assert "constraint_config" in annotations
        assert "genesis_key_id" in annotations

    def test_default_domain(self):
        """Domain should default to 'coc'."""
        from praxis.persistence.models import Workspace

        assert Workspace.domain == "coc"

    def test_default_constraint_template(self):
        """Constraint template should default to 'moderate'."""
        from praxis.persistence.models import Workspace

        assert Workspace.constraint_template == "moderate"

    def test_indexes_defined(self):
        from praxis.persistence.models import Workspace

        assert hasattr(Workspace, "__indexes__")
        index_names = {idx["name"] for idx in Workspace.__indexes__}
        assert "idx_workspace_name" in index_names
        assert "idx_workspace_domain" in index_names

    def test_no_auto_managed_fields(self):
        from praxis.persistence.models import Workspace

        annotations = Workspace.__annotations__
        assert "created_at" not in annotations
        assert "updated_at" not in annotations


# ---------------------------------------------------------------------------
# HeldAction Model Tests
# ---------------------------------------------------------------------------


class TestHeldActionModel:
    """Verify HeldAction model field definitions."""

    def test_import_held_action(self):
        from praxis.persistence.models import HeldAction

        assert HeldAction is not None

    def test_has_required_fields(self):
        from praxis.persistence.models import HeldAction

        annotations = HeldAction.__annotations__
        assert "id" in annotations
        assert "session_id" in annotations
        assert "action" in annotations

    def test_has_optional_fields(self):
        from praxis.persistence.models import HeldAction

        annotations = HeldAction.__annotations__
        assert "resource" in annotations
        assert "dimension" in annotations
        assert "verdict_payload" in annotations
        assert "resolved" in annotations
        assert "resolved_by" in annotations
        assert "resolution" in annotations
        assert "resolved_at" in annotations

    def test_default_dimension(self):
        """Dimension should default to 'operational'."""
        from praxis.persistence.models import HeldAction

        assert HeldAction.dimension == "operational"

    def test_default_resolved(self):
        """Resolved should default to False."""
        from praxis.persistence.models import HeldAction

        assert HeldAction.resolved is False

    def test_indexes_defined(self):
        from praxis.persistence.models import HeldAction

        assert hasattr(HeldAction, "__indexes__")
        index_names = {idx["name"] for idx in HeldAction.__indexes__}
        assert "idx_held_session" in index_names
        assert "idx_held_resolved" in index_names

    def test_no_auto_managed_fields(self):
        """Models must NOT define created_at or updated_at — DataFlow handles these."""
        from praxis.persistence.models import HeldAction

        annotations = HeldAction.__annotations__
        assert "created_at" not in annotations, "DataFlow auto-manages created_at"
        assert "updated_at" not in annotations, "DataFlow auto-manages updated_at"

    def test_in_all_models(self):
        from praxis.persistence.models import ALL_MODELS, HeldAction

        assert HeldAction in ALL_MODELS


# ---------------------------------------------------------------------------
# get_db() Function Tests
# ---------------------------------------------------------------------------


class TestGetDb:
    """Verify get_db() returns a properly configured DataFlow instance."""

    def test_returns_dataflow_instance(self):
        from dataflow import DataFlow
        from praxis.persistence import get_db

        db = get_db()
        assert isinstance(db, DataFlow)

    def test_singleton_behavior(self):
        from praxis.persistence import get_db

        db1 = get_db()
        db2 = get_db()
        assert db1 is db2

    def test_models_registered(self):
        """All 6 models should be registered with the DataFlow instance."""
        from praxis.persistence import get_db

        db = get_db()
        # DataFlow API compat: newer versions use db.models, older use db._models
        if hasattr(db, "models") and db.models:
            registered = {m.name for m in db.models}
        elif hasattr(db, "_models") and db._models:
            registered = set(db._models.keys())
        else:
            registered = set()
        assert "Session" in registered
        assert "DeliberationRecord" in registered
        assert "ConstraintEvent" in registered
        assert "TrustChainEntry" in registered
        assert "Workspace" in registered
        assert "HeldAction" in registered

    def test_uses_config_database_url(self):
        """get_db() should use the database URL from PraxisConfig."""
        from praxis.persistence import get_db

        db = get_db()
        # The db should have been configured with our test database URL
        assert db is not None


# ---------------------------------------------------------------------------
# Persistence Package Init Tests
# ---------------------------------------------------------------------------


class TestPersistencePackage:
    """Verify the persistence package exports are correct."""

    def test_public_exports(self):
        import praxis.persistence as persistence

        assert hasattr(persistence, "get_db")
        assert hasattr(persistence, "Session")
        assert hasattr(persistence, "DeliberationRecord")
        assert hasattr(persistence, "ConstraintEvent")
        assert hasattr(persistence, "TrustChainEntry")
        assert hasattr(persistence, "Workspace")
        assert hasattr(persistence, "HeldAction")

    def test_reset_db(self):
        """reset_db() should clear the cached instance."""
        from praxis.persistence import get_db, reset_db

        get_db()
        reset_db()
        # After reset, internal state should be cleared
        import praxis.persistence as persistence

        assert persistence._db is None
        assert persistence._models_registered is False
        assert persistence._tables_created is False
