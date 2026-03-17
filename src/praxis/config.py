# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Praxis configuration — single source of truth for all runtime settings.

All configuration comes from .env via environment variables.
No other module in the codebase should access os.environ directly.
"""

from __future__ import annotations

import logging
import os
import secrets
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env ONCE at import time — before any os.environ reads
load_dotenv(override=False)

logger = logging.getLogger(__name__)

_config_cache: Optional[PraxisConfig] = None


class PraxisConfigError(Exception):
    """Raised when a required configuration value is missing or invalid."""

    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        super().__init__(f"{field_name}: {message}")


@dataclass(frozen=True)
class PraxisConfig:
    """Typed, validated configuration for the Praxis runtime.

    All values originate from environment variables (loaded from .env).
    Frozen dataclass ensures immutability after creation.
    """

    # Database
    database_url: str

    # Keys
    key_dir: Path
    key_id: str

    # API
    api_host: str
    api_port: int
    api_secret: str
    cors_origins: list[str] = field(default_factory=list)

    # Trust / EATP
    eatp_namespace: str = "praxis"
    eatp_strict_mode: bool = True

    # AI models
    default_model: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "text"

    # Admin credentials (production login)
    admin_user: str = ""
    admin_password: str = ""

    # OAuth2 SSO providers
    github_client_id: str = ""
    github_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_base: str = ""  # e.g., https://api.praxis.terrene.foundation

    # Feature flags
    dev_mode: bool = False


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """Read an environment variable with validation."""
    value = os.environ.get(name, "")
    if value:
        return value
    if default is not None:
        return default
    if required:
        raise PraxisConfigError(name, "is required but not set")
    return ""


def _parse_bool(name: str, value: str) -> bool:
    """Parse a boolean environment variable."""
    lower = value.lower().strip()
    if lower in ("true", "1", "yes", "on"):
        return True
    if lower in ("false", "0", "no", "off", ""):
        return False
    raise PraxisConfigError(name, f"must be a boolean, got '{value}'")


def _parse_int(name: str, value: str) -> int:
    """Parse an integer environment variable."""
    try:
        return int(value)
    except ValueError:
        raise PraxisConfigError(name, f"must be an integer, got '{value}'")


def _parse_list(value: str) -> list[str]:
    """Parse a comma-separated list."""
    if not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _setup_logging(level: str, fmt: str) -> None:
    """Configure root logger based on config values."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise PraxisConfigError("LOG_LEVEL", f"invalid log level '{level}'")

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates on reset
    root.handlers.clear()

    if fmt == "json":
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler()
            handler.setFormatter(
                jsonlogger.JsonFormatter(
                    "%(asctime)s %(name)s %(levelname)s %(message)s",
                    timestamp=True,
                )
            )
            root.addHandler(handler)
        except ImportError:
            # Fall back to text if python-json-logger not installed
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            root.addHandler(handler)
            logger.warning("python-json-logger not installed, falling back to text format")
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        root.addHandler(handler)


def _build_config() -> PraxisConfig:
    """Build and validate configuration from environment variables."""
    dev_mode = _parse_bool("PRAXIS_DEV_MODE", _get_env("PRAXIS_DEV_MODE", "false"))

    # Database URL — required (defaults to SQLite in dev mode)
    if dev_mode:
        database_url = _get_env("DATABASE_URL", "sqlite:///./praxis.db")
    else:
        database_url = _get_env("DATABASE_URL", required=True)

    # Key directory — create if not exists
    key_dir_str = _get_env("PRAXIS_KEY_DIR", str(Path.home() / ".praxis" / "keys"))
    key_dir = Path(key_dir_str).expanduser()
    key_dir.mkdir(parents=True, exist_ok=True)

    key_id = _get_env("PRAXIS_KEY_ID", "default")

    # API settings
    api_host = _get_env("PRAXIS_API_HOST", "0.0.0.0")
    api_port = _parse_int("PRAXIS_API_PORT", _get_env("PRAXIS_API_PORT", "8000"))

    # API secret — required in production, defaulted in dev
    api_secret_raw = _get_env("PRAXIS_API_SECRET", "")
    if not api_secret_raw:
        if dev_mode:
            api_secret_raw = secrets.token_urlsafe(32)
            warnings.warn(
                "PRAXIS_API_SECRET not set — using random ephemeral secret. "
                "Tokens will not survive process restarts. "
                "Set PRAXIS_API_SECRET in .env for persistent tokens.",
                stacklevel=2,
            )
        else:
            raise PraxisConfigError(
                "PRAXIS_API_SECRET",
                "is required in production mode (PRAXIS_DEV_MODE=false)",
            )

    cors_origins = _parse_list(_get_env("PRAXIS_CORS_ORIGINS", "http://localhost:3000"))

    # EATP
    eatp_namespace = _get_env("EATP_NAMESPACE", "praxis")
    eatp_strict_mode = _parse_bool("EATP_STRICT_MODE", _get_env("EATP_STRICT_MODE", "true"))

    # AI models
    default_model = _get_env("PRAXIS_DEFAULT_MODEL", "")
    anthropic_api_key = _get_env("ANTHROPIC_API_KEY", "")
    openai_api_key = _get_env("OPENAI_API_KEY", "")

    # Logging
    log_level = _get_env("LOG_LEVEL", "INFO").upper()
    log_format = _get_env("LOG_FORMAT", "text").lower()
    if log_format not in ("json", "text"):
        raise PraxisConfigError("LOG_FORMAT", f"must be 'json' or 'text', got '{log_format}'")

    # Admin credentials for login endpoint
    admin_user = _get_env("PRAXIS_ADMIN_USER", "")
    admin_password = _get_env("PRAXIS_ADMIN_PASSWORD", "")

    # OAuth2 SSO providers
    github_client_id = _get_env("GITHUB_CLIENT_ID", "")
    github_client_secret = _get_env("GITHUB_CLIENT_SECRET", "")
    google_client_id = _get_env("GOOGLE_CLIENT_ID", "")
    google_client_secret = _get_env("GOOGLE_CLIENT_SECRET", "")
    oauth_redirect_base = _get_env(
        "OAUTH_REDIRECT_BASE",
        f"http://{api_host}:{api_port}" if api_host != "0.0.0.0" else f"http://localhost:{api_port}",
    )

    # Set up logging before returning
    _setup_logging(log_level, log_format)

    return PraxisConfig(
        database_url=database_url,
        key_dir=key_dir,
        key_id=key_id,
        api_host=api_host,
        api_port=api_port,
        api_secret=api_secret_raw,
        cors_origins=cors_origins,
        eatp_namespace=eatp_namespace,
        eatp_strict_mode=eatp_strict_mode,
        default_model=default_model,
        anthropic_api_key=anthropic_api_key,
        openai_api_key=openai_api_key,
        log_level=log_level,
        log_format=log_format,
        admin_user=admin_user,
        admin_password=admin_password,
        github_client_id=github_client_id,
        github_client_secret=github_client_secret,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        oauth_redirect_base=oauth_redirect_base,
        dev_mode=dev_mode,
    )


def get_config() -> PraxisConfig:
    """Get the singleton PraxisConfig instance.

    On first call, loads and validates configuration from environment.
    Subsequent calls return the cached instance.
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = _build_config()
    return _config_cache


def reset_config() -> None:
    """Clear the cached config. Used in tests to reload with different env vars."""
    global _config_cache
    _config_cache = None
