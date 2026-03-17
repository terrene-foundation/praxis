# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Shared fixtures for unit tests of the trust layer."""

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


# ---------------------------------------------------------------------------
# DataFlow database isolation for tests that hit persistence
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    """Provide an isolated SQLite-backed DataFlow database for every unit test.

    Sets DATABASE_URL to a temporary file so that SessionManager (which now
    persists to DataFlow) works without requiring a real database server.
    Resets persistence and config singletons before and after each test.
    """
    from praxis.config import reset_config
    from praxis.persistence import reset_db

    # Reset any cached state from a previous test
    reset_config()
    reset_db()

    db_path = tmp_path / "unit_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PRAXIS_API_SECRET", "test-secret-key")
    monkeypatch.setenv("PRAXIS_KEY_DIR", str(tmp_path / "keys"))
    monkeypatch.setenv("PRAXIS_DEV_MODE", "true")

    yield

    # Teardown: reset singletons so the next test starts clean
    reset_db()
    reset_config()


class MockKeyManager:
    """Minimal key manager for unit tests.

    If praxis.trust.keys.KeyManager is available, tests should prefer that.
    This mock provides the same interface for when the real implementation
    hasn't been created yet.
    """

    def __init__(self):
        self._keys: dict[str, Ed25519PrivateKey] = {}

    def generate_key(self, key_id: str) -> str:
        self._keys[key_id] = Ed25519PrivateKey.generate()
        return key_id

    def sign(self, key_id: str, data: bytes) -> bytes:
        if key_id not in self._keys:
            raise KeyError(f"Key not found: {key_id}")
        return self._keys[key_id].sign(data)

    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        if key_id not in self._keys:
            raise KeyError(f"Key not found: {key_id}")
        try:
            self._keys[key_id].public_key().verify(signature, data)
            return True
        except Exception:
            return False

    def get_public_key(self, key_id: str):
        if key_id not in self._keys:
            raise KeyError(f"Key not found: {key_id}")
        return self._keys[key_id].public_key()

    def export_public_pem(self, key_id: str) -> str:
        from cryptography.hazmat.primitives import serialization

        pub = self.get_public_key(key_id)
        pem_bytes = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode("utf-8")


@pytest.fixture
def key_manager():
    """Provide a key manager with a pre-generated test key."""
    try:
        from praxis.trust.keys import KeyManager
        import tempfile

        km = KeyManager(Path(tempfile.mkdtemp()))
        km.generate_key("test-key")
        return km
    except (ImportError, Exception):
        km = MockKeyManager()
        km.generate_key("test-key")
        return km


@pytest.fixture
def key_manager_factory():
    """Factory that creates fresh key managers on demand."""

    def _factory(*key_ids):
        try:
            from praxis.trust.keys import KeyManager
            import tempfile

            km = KeyManager(Path(tempfile.mkdtemp()))
            for kid in key_ids:
                km.generate_key(kid)
            return km
        except (ImportError, Exception):
            km = MockKeyManager()
            for kid in key_ids:
                km.generate_key(kid)
            return km

    return _factory


@pytest.fixture
def sample_constraints():
    """Standard 5-dimensional constraint envelope for testing."""
    return {
        "financial": {"max_spend": 1000.0},
        "operational": {"allowed_actions": ["read", "write", "execute"]},
        "temporal": {"max_duration_minutes": 120},
        "data_access": {"allowed_paths": ["/src", "/tests", "/docs"]},
        "communication": {"allowed_channels": ["internal", "email"]},
    }


@pytest.fixture
def tighter_constraints():
    """Constraints that are strictly tighter than sample_constraints."""
    return {
        "financial": {"max_spend": 500.0},
        "operational": {"allowed_actions": ["read", "write"]},
        "temporal": {"max_duration_minutes": 60},
        "data_access": {"allowed_paths": ["/src", "/tests"]},
        "communication": {"allowed_channels": ["internal"]},
    }


@pytest.fixture
def looser_constraints():
    """Constraints that are LOOSER than sample_constraints (should fail tightening)."""
    return {
        "financial": {"max_spend": 2000.0},
        "operational": {"allowed_actions": ["read", "write", "execute", "deploy"]},
        "temporal": {"max_duration_minutes": 240},
        "data_access": {"allowed_paths": ["/src", "/tests", "/docs", "/secrets"]},
        "communication": {"allowed_channels": ["internal", "email", "external"]},
    }
