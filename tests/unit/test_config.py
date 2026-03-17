# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.config — the single source of truth for all settings."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Reset config cache and provide a clean environment for each test."""
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

    # Set minimal required vars for most tests
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("PRAXIS_API_SECRET", "test-secret-key")
    monkeypatch.setenv("PRAXIS_KEY_DIR", str(tmp_path / "keys"))

    yield

    reset_config()


class TestGetConfig:
    """Test get_config() returns a valid PraxisConfig."""

    def test_returns_config_with_defaults(self):
        from praxis.config import get_config

        config = get_config()
        assert config.database_url == "sqlite:///./test.db"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.api_secret == "test-secret-key"
        assert config.eatp_namespace == "praxis"
        assert config.eatp_strict_mode is True
        assert config.log_level == "INFO"
        assert config.log_format == "text"
        assert config.dev_mode is False

    def test_singleton_returns_same_instance(self):
        from praxis.config import get_config

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_clears_cache(self):
        from praxis.config import get_config, reset_config

        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2
        # But values should be the same since env hasn't changed
        assert config1.database_url == config2.database_url

    def test_config_is_frozen(self):
        from praxis.config import get_config

        config = get_config()
        with pytest.raises(AttributeError):
            config.database_url = "changed"


class TestDatabaseUrl:
    """Test DATABASE_URL handling."""

    def test_required_in_production(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("PRAXIS_DEV_MODE", "false")
        reset_config()
        with pytest.raises(PraxisConfigError, match="DATABASE_URL"):
            get_config()

    def test_defaults_to_sqlite_in_dev_mode(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("PRAXIS_DEV_MODE", "true")
        reset_config()
        config = get_config()
        assert config.database_url == "sqlite:///./praxis.db"

    def test_custom_value_used(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/praxis")
        reset_config()
        config = get_config()
        assert config.database_url == "postgresql://user:pass@localhost/praxis"


class TestApiSecret:
    """Test PRAXIS_API_SECRET handling."""

    def test_required_in_production(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.delenv("PRAXIS_API_SECRET", raising=False)
        monkeypatch.setenv("PRAXIS_DEV_MODE", "false")
        reset_config()
        with pytest.raises(PraxisConfigError, match="PRAXIS_API_SECRET"):
            get_config()

    def test_defaults_in_dev_mode(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.delenv("PRAXIS_API_SECRET", raising=False)
        monkeypatch.setenv("PRAXIS_DEV_MODE", "true")
        reset_config()
        with pytest.warns(UserWarning, match="random ephemeral secret"):
            config = get_config()
        # Secret should be a random token, not a hardcoded value
        assert config.api_secret != ""
        assert config.api_secret != "dev-secret-not-for-production"
        assert len(config.api_secret) > 16


class TestKeyDir:
    """Test PRAXIS_KEY_DIR handling."""

    def test_creates_directory_if_not_exists(self, tmp_path, monkeypatch):
        from praxis.config import get_config, reset_config

        key_dir = tmp_path / "new" / "keys"
        assert not key_dir.exists()
        monkeypatch.setenv("PRAXIS_KEY_DIR", str(key_dir))
        reset_config()
        config = get_config()
        assert config.key_dir == key_dir
        assert key_dir.exists()

    def test_default_path(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.delenv("PRAXIS_KEY_DIR", raising=False)
        reset_config()
        config = get_config()
        expected = Path.home() / ".praxis" / "keys"
        assert config.key_dir == expected


class TestTypeParsing:
    """Test type validation for non-string fields."""

    def test_port_must_be_integer(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.setenv("PRAXIS_API_PORT", "not-a-number")
        reset_config()
        with pytest.raises(PraxisConfigError, match="PRAXIS_API_PORT"):
            get_config()

    def test_port_parses_valid_integer(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.setenv("PRAXIS_API_PORT", "9090")
        reset_config()
        config = get_config()
        assert config.api_port == 9090

    def test_boolean_parsing_true_values(self, monkeypatch):
        from praxis.config import get_config, reset_config

        for val in ("true", "True", "TRUE", "1", "yes", "on"):
            monkeypatch.setenv("PRAXIS_DEV_MODE", val)
            reset_config()
            config = get_config()
            assert config.dev_mode is True, f"Failed for '{val}'"

    def test_boolean_parsing_false_values(self, monkeypatch):
        from praxis.config import get_config, reset_config

        for val in ("false", "False", "FALSE", "0", "no", "off"):
            monkeypatch.setenv("PRAXIS_DEV_MODE", val)
            reset_config()
            config = get_config()
            assert config.dev_mode is False, f"Failed for '{val}'"

    def test_invalid_boolean_raises(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.setenv("EATP_STRICT_MODE", "maybe")
        reset_config()
        with pytest.raises(PraxisConfigError, match="EATP_STRICT_MODE"):
            get_config()


class TestCorsOrigins:
    """Test PRAXIS_CORS_ORIGINS parsing."""

    def test_default_origins(self):
        from praxis.config import get_config

        config = get_config()
        assert config.cors_origins == ["http://localhost:3000"]

    def test_multiple_origins(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.setenv(
            "PRAXIS_CORS_ORIGINS",
            "http://localhost:3000, http://localhost:3001, https://app.example.com",
        )
        reset_config()
        config = get_config()
        assert config.cors_origins == [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://app.example.com",
        ]

    def test_empty_origins_uses_default(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.setenv("PRAXIS_CORS_ORIGINS", "")
        reset_config()
        config = get_config()
        # Empty string falls back to the default value
        assert config.cors_origins == ["http://localhost:3000"]


class TestLogConfig:
    """Test logging configuration."""

    def test_invalid_log_level_raises(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
        reset_config()
        with pytest.raises(PraxisConfigError, match="LOG_LEVEL"):
            get_config()

    def test_invalid_log_format_raises(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.setenv("LOG_FORMAT", "xml")
        reset_config()
        with pytest.raises(PraxisConfigError, match="LOG_FORMAT"):
            get_config()

    def test_log_level_case_insensitive(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.setenv("LOG_LEVEL", "debug")
        reset_config()
        config = get_config()
        assert config.log_level == "DEBUG"


class TestDevMode:
    """Test PRAXIS_DEV_MODE behavior."""

    def test_dev_mode_relaxes_requirements(self, monkeypatch):
        from praxis.config import get_config, reset_config

        monkeypatch.setenv("PRAXIS_DEV_MODE", "true")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("PRAXIS_API_SECRET", raising=False)
        reset_config()
        with pytest.warns(UserWarning, match="random ephemeral secret"):
            config = get_config()
        assert config.dev_mode is True
        assert config.database_url == "sqlite:///./praxis.db"

    def test_production_mode_enforces_requirements(self, monkeypatch):
        from praxis.config import PraxisConfigError, get_config, reset_config

        monkeypatch.setenv("PRAXIS_DEV_MODE", "false")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("PRAXIS_API_SECRET", raising=False)
        reset_config()
        with pytest.raises(PraxisConfigError):
            get_config()
