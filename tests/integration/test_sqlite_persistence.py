# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Integration tests for SQLite persistence — verifies that get_db() creates
all 5 tables on disk and that the singleton/reset lifecycle works correctly.

Tests use tmp_path fixtures for full filesystem isolation.
"""

import sqlite3

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_db_env(monkeypatch, tmp_path):
    """Provide a clean, isolated environment for each test.

    Sets DATABASE_URL to a temp SQLite path and resets all persistence
    module state so each test starts fresh.
    """
    from praxis.config import reset_config

    reset_config()

    # Clear Praxis env vars for isolation
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

    db_path = tmp_path / "praxis_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PRAXIS_API_SECRET", "test-secret-key")
    monkeypatch.setenv("PRAXIS_KEY_DIR", str(tmp_path / "keys"))

    yield db_path

    # Reset persistence and config state after each test
    import praxis.persistence as persistence_mod

    persistence_mod._db = None
    persistence_mod._models_registered = False
    persistence_mod._tables_created = False

    reset_config()


# ---------------------------------------------------------------------------
# Table Creation Tests
# ---------------------------------------------------------------------------


class TestSQLiteTableCreation:
    """Verify that get_db() creates all 5 Praxis tables in SQLite."""

    def test_creates_all_five_tables(self, isolated_db_env):
        """get_db() should create tables for all 5 models."""
        from praxis.persistence import get_db

        get_db()

        # Query SQLite directly to verify tables exist
        db_path = isolated_db_env
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        # DataFlow pluralizes table names from class names
        expected_tables = {
            "sessions",
            "deliberation_records",
            "constraint_events",
            "trust_chain_entries",
            "workspaces",
        }
        for table in expected_tables:
            assert table in tables, (
                f"Expected table '{table}' not found. " f"Actual tables: {sorted(tables)}"
            )

    def test_sqlite_file_created_on_disk(self, isolated_db_env):
        """The SQLite database file should physically exist after get_db()."""
        from praxis.persistence import get_db

        db_path = isolated_db_env
        assert not db_path.exists(), "DB file should not exist before get_db()"

        get_db()

        assert db_path.exists(), "DB file should exist after get_db()"
        assert db_path.stat().st_size > 0, "DB file should not be empty"

    def test_tables_have_columns(self, isolated_db_env):
        """Each table should have the columns defined in the model."""
        from praxis.persistence import get_db

        get_db()

        db_path = isolated_db_env
        conn = sqlite3.connect(str(db_path))

        # Check sessions table has key columns
        cursor = conn.execute("PRAGMA table_info(sessions)")
        session_cols = {row[1] for row in cursor.fetchall()}
        assert "id" in session_cols
        assert "workspace_id" in session_cols
        assert "domain" in session_cols
        assert "state" in session_cols

        # Check deliberation_records table
        cursor = conn.execute("PRAGMA table_info(deliberation_records)")
        delib_cols = {row[1] for row in cursor.fetchall()}
        assert "id" in delib_cols
        assert "session_id" in delib_cols
        assert "record_type" in delib_cols

        # Check constraint_events table
        cursor = conn.execute("PRAGMA table_info(constraint_events)")
        constraint_cols = {row[1] for row in cursor.fetchall()}
        assert "id" in constraint_cols
        assert "session_id" in constraint_cols
        assert "action" in constraint_cols
        assert "dimension" in constraint_cols

        # Check trust_chain_entries table
        cursor = conn.execute("PRAGMA table_info(trust_chain_entries)")
        trust_cols = {row[1] for row in cursor.fetchall()}
        assert "id" in trust_cols
        assert "session_id" in trust_cols
        assert "entry_type" in trust_cols

        # Check workspaces table
        cursor = conn.execute("PRAGMA table_info(workspaces)")
        workspace_cols = {row[1] for row in cursor.fetchall()}
        assert "id" in workspace_cols
        assert "name" in workspace_cols
        assert "domain" in workspace_cols

        conn.close()


# ---------------------------------------------------------------------------
# Singleton Behavior Tests
# ---------------------------------------------------------------------------


class TestSingletonBehavior:
    """Verify that get_db() returns the same instance and reset_db() clears it."""

    def test_get_db_returns_same_instance(self):
        """Calling get_db() twice should return the exact same object."""
        from praxis.persistence import get_db

        db1 = get_db()
        db2 = get_db()
        assert db1 is db2

    def test_reset_db_clears_all_state(self):
        """reset_db() should clear the singleton, model registration, and table creation flags."""
        import praxis.persistence as persistence_mod
        from praxis.persistence import get_db, reset_db

        get_db()
        assert persistence_mod._db is not None
        assert persistence_mod._models_registered is True
        assert persistence_mod._tables_created is True

        reset_db()
        assert persistence_mod._db is None
        assert persistence_mod._models_registered is False
        assert persistence_mod._tables_created is False

    def test_get_db_after_reset_creates_new_instance(self):
        """After reset_db(), get_db() should create a fresh DataFlow instance."""
        from praxis.persistence import get_db, reset_db

        db1 = get_db()
        reset_db()
        db2 = get_db()

        # New instance, not the same object
        assert db2 is not db1

    def test_tables_created_flag_prevents_repeated_creation(self):
        """The _tables_created flag should prevent redundant create_tables_sync() calls."""
        import praxis.persistence as persistence_mod
        from praxis.persistence import get_db

        get_db()
        assert persistence_mod._tables_created is True

        # Second call should not re-trigger table creation (flag is already True)
        db = get_db()
        assert persistence_mod._tables_created is True
        assert db is not None


# ---------------------------------------------------------------------------
# Raw SQLite Verification
# ---------------------------------------------------------------------------


class TestRawSQLiteVerification:
    """Verify tables via raw sqlite3 module, independent of DataFlow."""

    def test_can_insert_and_read_via_raw_sqlite(self, isolated_db_env):
        """Tables created by DataFlow should be usable via raw sqlite3."""
        from praxis.persistence import get_db

        get_db()

        db_path = isolated_db_env
        conn = sqlite3.connect(str(db_path))

        # Insert a workspace row directly (include timestamps since DataFlow makes them NOT NULL)
        conn.execute(
            "INSERT INTO workspaces (id, name, domain, constraint_template, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "ws-001",
                "Test Workspace",
                "coc",
                "moderate",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
        conn.commit()

        # Read it back
        cursor = conn.execute("SELECT id, name, domain FROM workspaces WHERE id = ?", ("ws-001",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "ws-001"
        assert row[1] == "Test Workspace"
        assert row[2] == "coc"

        conn.close()

    def test_table_count_is_at_least_five(self, isolated_db_env):
        """There should be at least 5 user tables (DataFlow may add internal tables)."""
        from praxis.persistence import get_db

        get_db()

        db_path = isolated_db_env
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' " "AND name NOT LIKE 'sqlite_%'"
        )
        table_count = cursor.fetchone()[0]
        conn.close()

        assert table_count >= 5, f"Expected at least 5 tables, found {table_count}"
