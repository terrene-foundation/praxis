# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Tests for Firebase Authentication integration.

Tests cover:
- Firebase ID token verification (mocked Google certs)
- User auto-creation on first login
- User retrieval and update on subsequent login
- Role assignment and persistence
- Invalid/expired token rejection
- Certificate caching behavior
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from praxis.api.firebase import (
    FIREBASE_PROJECT_ID,
    clear_cert_cache,
    extract_user_info,
    verify_firebase_token,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_certs():
    """Clear the certificate cache before each test."""
    clear_cert_cache()
    yield
    clear_cert_cache()


@pytest.fixture
def decoded_github_token() -> dict[str, Any]:
    """Sample decoded Firebase token for a GitHub user."""
    now = int(time.time())
    return {
        "sub": "firebase-uid-github-123",
        "email": "octocat@github.com",
        "name": "Octocat",
        "picture": "https://avatars.githubusercontent.com/u/123",
        "iss": f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}",
        "aud": FIREBASE_PROJECT_ID,
        "iat": now,
        "exp": now + 3600,
        "auth_time": now,
        "firebase": {
            "sign_in_provider": "github.com",
            "identities": {
                "github.com": ["123"],
                "email": ["octocat@github.com"],
            },
        },
    }


@pytest.fixture
def decoded_google_token() -> dict[str, Any]:
    """Sample decoded Firebase token for a Google user."""
    now = int(time.time())
    return {
        "sub": "firebase-uid-google-456",
        "email": "user@gmail.com",
        "name": "Test User",
        "picture": "https://lh3.googleusercontent.com/photo",
        "iss": f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}",
        "aud": FIREBASE_PROJECT_ID,
        "iat": now,
        "exp": now + 3600,
        "auth_time": now,
        "firebase": {
            "sign_in_provider": "google.com",
            "identities": {
                "google.com": ["456"],
                "email": ["user@gmail.com"],
            },
        },
    }


@dataclass
class MockConfig:
    """Minimal config for handler tests."""

    api_secret: str = "test-secret-key-for-jwt-signing"
    dev_mode: bool = True


# ---------------------------------------------------------------------------
# extract_user_info tests
# ---------------------------------------------------------------------------


class TestExtractUserInfo:
    """Tests for extracting user info from decoded Firebase tokens."""

    def test_github_user(self, decoded_github_token):
        info = extract_user_info(decoded_github_token)
        assert info["uid"] == "firebase-uid-github-123"
        assert info["email"] == "octocat@github.com"
        assert info["display_name"] == "Octocat"
        assert info["photo_url"] == "https://avatars.githubusercontent.com/u/123"
        assert info["provider"] == "github.com"

    def test_google_user(self, decoded_google_token):
        info = extract_user_info(decoded_google_token)
        assert info["uid"] == "firebase-uid-google-456"
        assert info["email"] == "user@gmail.com"
        assert info["display_name"] == "Test User"
        assert info["photo_url"] == "https://lh3.googleusercontent.com/photo"
        assert info["provider"] == "google.com"

    def test_missing_name_falls_back_to_email_prefix(self):
        decoded = {
            "sub": "uid-789",
            "email": "hello@example.com",
            "firebase": {"sign_in_provider": "google.com"},
        }
        info = extract_user_info(decoded)
        assert info["display_name"] == "hello"

    def test_missing_picture(self):
        decoded = {
            "sub": "uid-789",
            "email": "hello@example.com",
            "name": "Hello",
            "firebase": {"sign_in_provider": "google.com"},
        }
        info = extract_user_info(decoded)
        assert info["photo_url"] is None

    def test_missing_provider(self):
        decoded = {
            "sub": "uid-789",
            "email": "hello@example.com",
            "name": "Hello",
            "firebase": {},
        }
        info = extract_user_info(decoded)
        assert info["provider"] == ""


# ---------------------------------------------------------------------------
# verify_firebase_token tests
# ---------------------------------------------------------------------------


class TestVerifyFirebaseToken:
    """Tests for Firebase ID token verification."""

    @pytest.mark.asyncio
    async def test_empty_token_rejected(self):
        with pytest.raises(ValueError, match="non-empty string"):
            await verify_firebase_token("")

    @pytest.mark.asyncio
    async def test_none_token_rejected(self):
        with pytest.raises(ValueError, match="non-empty string"):
            await verify_firebase_token(None)

    @pytest.mark.asyncio
    async def test_invalid_format_rejected(self):
        with pytest.raises(ValueError, match="cannot decode header"):
            await verify_firebase_token("not-a-jwt-token")

    @pytest.mark.asyncio
    async def test_missing_kid_rejected(self):
        """Token without kid in header is rejected."""
        # Create a minimal JWT-shaped string with no kid
        import base64

        header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).rstrip(b"=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "test"}).encode()).rstrip(b"=")
        token = f"{header.decode()}.{payload.decode()}.fake-sig"

        with pytest.raises(ValueError, match="missing key ID"):
            await verify_firebase_token(token)

    @pytest.mark.asyncio
    async def test_unknown_kid_rejected(self):
        """Token with kid not in Google's certificates is rejected."""
        import base64

        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "RS256", "kid": "unknown-kid"}).encode()
        ).rstrip(b"=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "test"}).encode()).rstrip(b"=")
        token = f"{header.decode()}.{payload.decode()}.fake-sig"

        # Mock the cert fetch to return known certs without the kid
        mock_response = MagicMock()
        mock_response.json.return_value = {"known-kid-1": "cert-pem-1"}
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"cache-control": "max-age=300"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("praxis.api.firebase.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="unknown key ID"):
                await verify_firebase_token(token)

    @pytest.mark.asyncio
    async def test_valid_token_with_mocked_verification(self, decoded_github_token):
        """End-to-end test with mocked JWT decode and cert fetch."""
        import base64

        # Create a token-shaped string that passes header parsing
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "RS256", "kid": "test-kid-1"}).encode()
        ).rstrip(b"=")
        payload = base64.urlsafe_b64encode(
            json.dumps(decoded_github_token).encode()
        ).rstrip(b"=")
        token = f"{header.decode()}.{payload.decode()}.fake-signature"

        # Mock cert fetch
        mock_response = MagicMock()
        mock_response.json.return_value = {"test-kid-1": "fake-cert-pem"}
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"cache-control": "max-age=300"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        # Mock the entire verification chain:
        # 1. Cert fetch returns our fake cert
        # 2. X.509 load returns a mock public key
        # 3. pyjwt.decode returns the decoded token
        mock_cert = MagicMock()
        mock_cert.public_key.return_value = "mock-public-key"

        with (
            patch("praxis.api.firebase.httpx.AsyncClient", return_value=mock_client),
            patch(
                "praxis.api.firebase.load_pem_x509_certificate",
                return_value=mock_cert,
            ),
            patch("praxis.api.firebase.pyjwt.decode", return_value=decoded_github_token),
        ):
            result = await verify_firebase_token(token)

        assert result["sub"] == "firebase-uid-github-123"
        assert result["email"] == "octocat@github.com"
        assert result["firebase"]["sign_in_provider"] == "github.com"


# ---------------------------------------------------------------------------
# firebase_login_handler tests
# ---------------------------------------------------------------------------


class TestFirebaseLoginHandler:
    """Tests for the firebase_login_handler in handlers.py."""

    @pytest.mark.asyncio
    async def test_empty_token_returns_error(self):
        from praxis.api.handlers import firebase_login_handler

        config = MockConfig()
        result = await firebase_login_handler(id_token="", config=config)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_successful_first_login_creates_user(self, decoded_github_token, tmp_path):
        """First login auto-creates a user and returns JWT + user info."""
        from praxis.api.handlers import firebase_login_handler

        config = MockConfig()

        user_info = {
            "uid": "firebase-uid-github-123",
            "email": "octocat@github.com",
            "display_name": "Octocat",
            "photo_url": "https://avatars.githubusercontent.com/u/123",
            "provider": "github.com",
        }

        with (
            patch(
                "praxis.api.firebase.verify_firebase_token",
                new_callable=AsyncMock,
                return_value=decoded_github_token,
            ),
            patch(
                "praxis.api.firebase.extract_user_info",
                return_value=user_info,
            ),
            patch("praxis.persistence.db_ops.db_read", return_value=None) as mock_read,
            patch("praxis.persistence.db_ops.db_create") as mock_create,
        ):
            result = await firebase_login_handler(
                id_token="fake-firebase-token",
                config=config,
            )

        assert "error" not in result
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"]["id"] == "firebase-uid-github-123"
        assert result["user"]["email"] == "octocat@github.com"
        assert result["user"]["display_name"] == "Octocat"
        assert result["user"]["provider"] == "github.com"
        assert result["user"]["role"] == "practitioner"

        # Verify db_create was called (user auto-creation)
        mock_read.assert_called_once_with("User", "firebase-uid-github-123")
        mock_create.assert_called_once()
        create_args = mock_create.call_args
        assert create_args[0][0] == "User"
        assert create_args[0][1]["id"] == "firebase-uid-github-123"
        assert create_args[0][1]["email"] == "octocat@github.com"

    @pytest.mark.asyncio
    async def test_subsequent_login_updates_user(self, decoded_github_token):
        """Returning user is updated (not created again)."""
        from praxis.api.handlers import firebase_login_handler

        config = MockConfig()

        user_info = {
            "uid": "firebase-uid-github-123",
            "email": "octocat@github.com",
            "display_name": "Octocat",
            "photo_url": "https://avatars.githubusercontent.com/u/123",
            "provider": "github.com",
        }

        existing_user = {
            "id": "firebase-uid-github-123",
            "email": "octocat@github.com",
            "display_name": "Octocat",
            "role": "supervisor",  # Elevated role from previous assignment
        }

        with (
            patch(
                "praxis.api.firebase.verify_firebase_token",
                new_callable=AsyncMock,
                return_value=decoded_github_token,
            ),
            patch(
                "praxis.api.firebase.extract_user_info",
                return_value=user_info,
            ),
            patch("praxis.persistence.db_ops.db_read", return_value=existing_user),
            patch("praxis.persistence.db_ops.db_create") as mock_create,
            patch("praxis.persistence.db_ops.db_update") as mock_update,
        ):
            result = await firebase_login_handler(
                id_token="fake-firebase-token",
                config=config,
            )

        assert "error" not in result
        assert result["user"]["role"] == "supervisor"  # Preserves existing role

        # db_create should NOT be called for returning user
        mock_create.assert_not_called()
        # db_update should be called to update last_login
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_role_preserved_on_returning_login(self, decoded_google_token):
        """A user's role set by an admin is preserved across logins."""
        from praxis.api.handlers import firebase_login_handler

        config = MockConfig()

        user_info = {
            "uid": "firebase-uid-google-456",
            "email": "user@gmail.com",
            "display_name": "Test User",
            "photo_url": None,
            "provider": "google.com",
        }

        existing_user = {
            "id": "firebase-uid-google-456",
            "email": "user@gmail.com",
            "role": "admin",
        }

        with (
            patch(
                "praxis.api.firebase.verify_firebase_token",
                new_callable=AsyncMock,
                return_value=decoded_google_token,
            ),
            patch(
                "praxis.api.firebase.extract_user_info",
                return_value=user_info,
            ),
            patch("praxis.persistence.db_ops.db_read", return_value=existing_user),
            patch("praxis.persistence.db_ops.db_update"),
        ):
            result = await firebase_login_handler(
                id_token="fake-firebase-token",
                config=config,
            )

        assert result["user"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_error(self):
        """An invalid Firebase token returns an error dict (never raises)."""
        from praxis.api.handlers import firebase_login_handler

        config = MockConfig()

        with patch(
            "praxis.api.firebase.verify_firebase_token",
            new_callable=AsyncMock,
            side_effect=ValueError("Invalid Firebase ID token"),
        ):
            result = await firebase_login_handler(
                id_token="bad-token",
                config=config,
            )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_google_login_creates_user(self, decoded_google_token):
        """Google SSO creates a user with google.com provider."""
        from praxis.api.handlers import firebase_login_handler

        config = MockConfig()

        user_info = {
            "uid": "firebase-uid-google-456",
            "email": "user@gmail.com",
            "display_name": "Test User",
            "photo_url": "https://lh3.googleusercontent.com/photo",
            "provider": "google.com",
        }

        with (
            patch(
                "praxis.api.firebase.verify_firebase_token",
                new_callable=AsyncMock,
                return_value=decoded_google_token,
            ),
            patch(
                "praxis.api.firebase.extract_user_info",
                return_value=user_info,
            ),
            patch("praxis.persistence.db_ops.db_read", return_value=None),
            patch("praxis.persistence.db_ops.db_create") as mock_create,
        ):
            result = await firebase_login_handler(
                id_token="fake-firebase-token",
                config=config,
            )

        assert "error" not in result
        assert result["user"]["provider"] == "google.com"
        assert result["user"]["email"] == "user@gmail.com"
        mock_create.assert_called_once()


# ---------------------------------------------------------------------------
# Certificate caching tests
# ---------------------------------------------------------------------------


class TestCertificateCaching:
    """Tests for Google certificate caching behavior."""

    @pytest.mark.asyncio
    async def test_certs_are_cached(self):
        """Subsequent calls should use cached certificates."""
        from praxis.api.firebase import _fetch_google_certs

        mock_response = MagicMock()
        mock_response.json.return_value = {"kid-1": "cert-1"}
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"cache-control": "max-age=600"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("praxis.api.firebase.httpx.AsyncClient", return_value=mock_client):
            # First call fetches
            certs1 = await _fetch_google_certs()
            # Second call should use cache (no new HTTP request)
            certs2 = await _fetch_google_certs()

        assert certs1 == certs2
        # Should only have been called once
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_cleared_works(self):
        """After clearing cache, next call fetches fresh certs."""
        from praxis.api.firebase import _fetch_google_certs

        mock_response = MagicMock()
        mock_response.json.return_value = {"kid-1": "cert-1"}
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"cache-control": "max-age=600"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("praxis.api.firebase.httpx.AsyncClient", return_value=mock_client):
            await _fetch_google_certs()
            clear_cert_cache()
            await _fetch_google_certs()

        # Should have been called twice (cache was cleared between calls)
        assert mock_client.get.call_count == 2


# ---------------------------------------------------------------------------
# User model tests
# ---------------------------------------------------------------------------


class TestUserModel:
    """Tests for the User persistence model."""

    def test_user_model_in_all_models(self):
        from praxis.persistence.models import ALL_MODELS, User

        assert User in ALL_MODELS

    def test_user_model_fields(self):
        from praxis.persistence.models import User

        annotations = User.__annotations__
        assert "id" in annotations
        assert "email" in annotations
        assert "display_name" in annotations
        assert "photo_url" in annotations
        assert "provider" in annotations
        assert "role" in annotations
        assert "last_login_at" in annotations

    def test_user_model_defaults(self):
        from praxis.persistence.models import User

        assert User.display_name == ""
        assert User.photo_url is None
        assert User.provider == ""
        assert User.role == "practitioner"
        assert User.last_login_at is None

    def test_user_model_has_indexes(self):
        from praxis.persistence.models import User

        assert hasattr(User, "__indexes__")
        index_names = {idx["name"] for idx in User.__indexes__}
        assert "idx_user_email" in index_names
        assert "idx_user_provider" in index_names
        assert "idx_user_role" in index_names
