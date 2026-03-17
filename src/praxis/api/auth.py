# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
JWT authentication for the Praxis API.

Provides token creation, verification, and dev-mode bypass.
All secrets come from PraxisConfig (loaded from .env).
"""

from __future__ import annotations

import logging
import time
from typing import Any

import jwt as pyjwt

logger = logging.getLogger(__name__)

# Default token expiry: 24 hours
DEFAULT_EXPIRY_SECONDS = 86400

# Token issuer
ISSUER = "praxis"


class AuthenticationError(Exception):
    """Raised when authentication fails (bad token, expired, wrong secret, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def create_token(
    user_id: str,
    secret: str,
    expires_in_seconds: int = DEFAULT_EXPIRY_SECONDS,
) -> str:
    """Create a signed JWT token for a user.

    Args:
        user_id: The user identifier to encode in the 'sub' claim.
        secret: The signing secret. Must not be empty.
        expires_in_seconds: Token validity duration in seconds. Defaults to 24 hours.

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: If user_id or secret is empty.
    """
    if not user_id:
        raise ValueError(
            "user_id must not be empty. " "Provide a valid user identifier to create a token."
        )
    if not secret:
        raise ValueError(
            "secret must not be empty. " "Provide a valid signing secret to create a token."
        )

    now = int(time.time())
    payload = {
        "sub": user_id,
        "iss": ISSUER,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    token = pyjwt.encode(payload, secret, algorithm="HS256")
    logger.debug("Created JWT token for user '%s' (expires in %ds)", user_id, expires_in_seconds)
    return token


def decode_token(token: str, secret: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Args:
        token: The encoded JWT string to decode.
        secret: The secret used to sign the token.

    Returns:
        The decoded payload as a dict.

    Raises:
        AuthenticationError: If the token is invalid, expired, or signed
            with a different secret.
    """
    if not token:
        raise AuthenticationError("Token must not be empty")

    try:
        payload = pyjwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=ISSUER,
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except pyjwt.InvalidIssuerError:
        raise AuthenticationError("Token has invalid issuer")
    except pyjwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid token: {exc}")


def check_auth_dev_mode(token: str | None) -> dict[str, Any]:
    """Dev-mode authentication bypass.

    In development mode, authentication is relaxed:
    - No token? Returns a default dev-user identity.
    - Any token? Returns a default dev-user identity (no verification).

    This allows local development without configuring JWT secrets.

    Args:
        token: The token string, or None if no token provided.

    Returns:
        A dict with at minimum a 'sub' claim set to 'dev-user'.
    """
    logger.debug("Dev-mode auth bypass: token=%s", "present" if token else "absent")
    return {
        "sub": "dev-user",
        "iss": ISSUER,
        "dev_mode": True,
    }
