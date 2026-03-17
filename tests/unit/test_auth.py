# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.api.auth — JWT authentication middleware."""

import time

import pytest


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


class TestCreateToken:
    """Test JWT token creation."""

    def test_create_token_returns_string(self):
        from praxis.api.auth import create_token

        token = create_token(user_id="user-1", secret="a" * 64)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_contains_user_id_claim(self):
        from praxis.api.auth import create_token, decode_token

        secret = "b" * 64
        token = create_token(user_id="user-42", secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert payload["sub"] == "user-42"

    def test_create_token_contains_iat_claim(self):
        from praxis.api.auth import create_token, decode_token

        secret = "c" * 64
        token = create_token(user_id="user-1", secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert "iat" in payload
        assert isinstance(payload["iat"], (int, float))

    def test_create_token_contains_exp_claim(self):
        from praxis.api.auth import create_token, decode_token

        secret = "d" * 64
        token = create_token(user_id="user-1", secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]

    def test_create_token_default_expiry_is_24_hours(self):
        from praxis.api.auth import create_token, decode_token

        secret = "e" * 64
        token = create_token(user_id="user-1", secret=secret)
        payload = decode_token(token=token, secret=secret)
        # Default expiry should be 24 hours (86400 seconds)
        diff = payload["exp"] - payload["iat"]
        assert diff == 86400

    def test_create_token_custom_expiry(self):
        from praxis.api.auth import create_token, decode_token

        secret = "f" * 64
        token = create_token(user_id="user-1", secret=secret, expires_in_seconds=3600)
        payload = decode_token(token=token, secret=secret)
        diff = payload["exp"] - payload["iat"]
        assert diff == 3600

    def test_create_token_contains_issuer(self):
        from praxis.api.auth import create_token, decode_token

        secret = "g" * 64
        token = create_token(user_id="user-1", secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert payload["iss"] == "praxis"

    def test_create_token_empty_user_id_raises(self):
        from praxis.api.auth import create_token

        with pytest.raises(ValueError, match="user_id"):
            create_token(user_id="", secret="h" * 64)

    def test_create_token_empty_secret_raises(self):
        from praxis.api.auth import create_token

        with pytest.raises(ValueError, match="secret"):
            create_token(user_id="user-1", secret="")


# ---------------------------------------------------------------------------
# Token decoding / verification
# ---------------------------------------------------------------------------


class TestDecodeToken:
    """Test JWT token decoding and verification."""

    def test_decode_valid_token(self):
        from praxis.api.auth import create_token, decode_token

        secret = "i" * 64
        token = create_token(user_id="user-1", secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert payload["sub"] == "user-1"

    def test_decode_with_wrong_secret_raises(self):
        from praxis.api.auth import create_token, decode_token, AuthenticationError

        token = create_token(user_id="user-1", secret="j" * 64)
        with pytest.raises(AuthenticationError):
            decode_token(token=token, secret="k" * 64)

    def test_decode_malformed_token_raises(self):
        from praxis.api.auth import decode_token, AuthenticationError

        with pytest.raises(AuthenticationError):
            decode_token(token="not.a.jwt", secret="l" * 64)

    def test_decode_empty_token_raises(self):
        from praxis.api.auth import decode_token, AuthenticationError

        with pytest.raises(AuthenticationError):
            decode_token(token="", secret="m" * 64)


# ---------------------------------------------------------------------------
# Dev mode bypass
# ---------------------------------------------------------------------------


class TestDevModeAuth:
    """Test that dev mode allows relaxed authentication."""

    def test_dev_mode_allows_no_token(self):
        from praxis.api.auth import check_auth_dev_mode

        # In dev mode, should return a default identity even without token
        result = check_auth_dev_mode(token=None)
        assert result is not None
        assert "sub" in result
        assert result["sub"] == "dev-user"

    def test_dev_mode_accepts_any_token(self):
        from praxis.api.auth import check_auth_dev_mode

        result = check_auth_dev_mode(token="garbage-token")
        assert result is not None
        assert result["sub"] == "dev-user"


# ---------------------------------------------------------------------------
# AuthenticationError
# ---------------------------------------------------------------------------


class TestAuthenticationError:
    """Test custom authentication error."""

    def test_authentication_error_exists(self):
        from praxis.api.auth import AuthenticationError

        err = AuthenticationError("Token expired")
        assert "Token expired" in str(err)

    def test_authentication_error_is_exception(self):
        from praxis.api.auth import AuthenticationError

        assert issubclass(AuthenticationError, Exception)
