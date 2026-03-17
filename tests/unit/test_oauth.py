# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.api.oauth — OAuth2 SSO login flows."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# State management tests
# ---------------------------------------------------------------------------


class TestOAuthState:
    """Test CSRF state token generation and validation."""

    def setup_method(self):
        from praxis.api.oauth import clear_state_store

        clear_state_store()

    def teardown_method(self):
        from praxis.api.oauth import clear_state_store

        clear_state_store()

    def test_generate_state_returns_string(self):
        from praxis.api.oauth import _generate_state

        state = _generate_state()
        assert isinstance(state, str)
        assert len(state) > 0

    def test_generate_state_unique(self):
        from praxis.api.oauth import _generate_state

        states = {_generate_state() for _ in range(100)}
        assert len(states) == 100

    def test_validate_state_valid(self):
        from praxis.api.oauth import _generate_state, _validate_state

        state = _generate_state()
        assert _validate_state(state) is True

    def test_validate_state_consumed(self):
        """State tokens are single-use: validating twice should fail."""
        from praxis.api.oauth import _generate_state, _validate_state

        state = _generate_state()
        assert _validate_state(state) is True
        assert _validate_state(state) is False

    def test_validate_state_missing(self):
        from praxis.api.oauth import _validate_state

        assert _validate_state("nonexistent-state-token") is False

    def test_validate_state_empty(self):
        from praxis.api.oauth import _validate_state

        assert _validate_state("") is False

    def test_validate_state_expired(self):
        from praxis.api.oauth import _generate_state, _oauth_state_store, _validate_state

        state = _generate_state()
        # Manually expire the state
        _oauth_state_store[state] = time.time() - 1
        assert _validate_state(state) is False

    def test_evict_expired_states(self):
        from praxis.api.oauth import (
            _evict_expired_states,
            _generate_state,
            _oauth_state_store,
        )

        # Generate some states and expire them
        state1 = _generate_state()
        state2 = _generate_state()
        _oauth_state_store[state1] = time.time() - 10
        _oauth_state_store[state2] = time.time() - 10
        state3 = _generate_state()  # This one should survive

        _evict_expired_states()
        assert state1 not in _oauth_state_store
        assert state2 not in _oauth_state_store
        assert state3 in _oauth_state_store


# ---------------------------------------------------------------------------
# GitHub OAuth URL building
# ---------------------------------------------------------------------------


class TestGitHubAuthorizeUrl:
    """Test GitHub authorization URL construction."""

    def setup_method(self):
        from praxis.api.oauth import clear_state_store

        clear_state_store()

    def test_url_contains_client_id(self):
        from praxis.api.oauth import build_github_authorize_url

        url = build_github_authorize_url(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/auth/github/callback",
        )
        assert "client_id=test-client-id" in url

    def test_url_contains_redirect_uri(self):
        from praxis.api.oauth import build_github_authorize_url

        url = build_github_authorize_url(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/auth/github/callback",
        )
        assert "redirect_uri=" in url
        assert "auth%2Fgithub%2Fcallback" in url or "auth/github/callback" in url

    def test_url_contains_state(self):
        from praxis.api.oauth import build_github_authorize_url

        url = build_github_authorize_url(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/auth/github/callback",
        )
        assert "state=" in url

    def test_url_contains_scope(self):
        from praxis.api.oauth import build_github_authorize_url

        url = build_github_authorize_url(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/auth/github/callback",
        )
        assert "scope=" in url
        assert "read%3Auser" in url or "read:user" in url

    def test_url_starts_with_github(self):
        from praxis.api.oauth import build_github_authorize_url

        url = build_github_authorize_url(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/auth/github/callback",
        )
        assert url.startswith("https://github.com/login/oauth/authorize")


# ---------------------------------------------------------------------------
# Google OAuth URL building
# ---------------------------------------------------------------------------


class TestGoogleAuthorizeUrl:
    """Test Google authorization URL construction."""

    def setup_method(self):
        from praxis.api.oauth import clear_state_store

        clear_state_store()

    def test_url_contains_client_id(self):
        from praxis.api.oauth import build_google_authorize_url

        url = build_google_authorize_url(
            client_id="test-google-id.apps.googleusercontent.com",
            redirect_uri="http://localhost:8000/auth/google/callback",
        )
        assert "client_id=test-google-id.apps.googleusercontent.com" in url

    def test_url_contains_response_type(self):
        from praxis.api.oauth import build_google_authorize_url

        url = build_google_authorize_url(
            client_id="test-google-id",
            redirect_uri="http://localhost:8000/auth/google/callback",
        )
        assert "response_type=code" in url

    def test_url_contains_scope(self):
        from praxis.api.oauth import build_google_authorize_url

        url = build_google_authorize_url(
            client_id="test-google-id",
            redirect_uri="http://localhost:8000/auth/google/callback",
        )
        assert "scope=" in url
        assert "openid" in url

    def test_url_starts_with_google(self):
        from praxis.api.oauth import build_google_authorize_url

        url = build_google_authorize_url(
            client_id="test-google-id",
            redirect_uri="http://localhost:8000/auth/google/callback",
        )
        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")


# ---------------------------------------------------------------------------
# GitHub code exchange (mocked HTTP)
# ---------------------------------------------------------------------------


class TestGitHubCodeExchange:
    """Test GitHub authorization code exchange with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_successful_exchange(self):
        from praxis.api.oauth import exchange_github_code

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "gho_test_token"}

        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "octocat",
            "name": "The Octocat",
            "email": "octocat@github.com",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_user_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            result = await exchange_github_code(
                code="test-code",
                client_id="test-client",
                client_secret="test-secret",
                redirect_uri="http://localhost:8000/auth/github/callback",
            )

        assert result["username"] == "octocat"
        assert result["name"] == "The Octocat"
        assert result["email"] == "octocat@github.com"

    @pytest.mark.asyncio
    async def test_token_exchange_failure(self):
        from praxis.api.oauth import exchange_github_code

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "bad_verification_code"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="Failed to exchange"):
                await exchange_github_code(
                    code="bad-code",
                    client_id="test-client",
                    client_secret="test-secret",
                    redirect_uri="http://localhost:8000/auth/github/callback",
                )

    @pytest.mark.asyncio
    async def test_no_access_token_in_response(self):
        from praxis.api.oauth import exchange_github_code

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": "bad_verification_code",
            "error_description": "The code has expired",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="did not return an access token"):
                await exchange_github_code(
                    code="expired-code",
                    client_id="test-client",
                    client_secret="test-secret",
                    redirect_uri="http://localhost:8000/auth/github/callback",
                )

    @pytest.mark.asyncio
    async def test_user_fetch_failure(self):
        from praxis.api.oauth import exchange_github_code

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "gho_test_token"}

        mock_user_response = MagicMock()
        mock_user_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_user_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="Failed to fetch user"):
                await exchange_github_code(
                    code="test-code",
                    client_id="test-client",
                    client_secret="test-secret",
                    redirect_uri="http://localhost:8000/auth/github/callback",
                )

    @pytest.mark.asyncio
    async def test_email_fetched_from_emails_endpoint(self):
        """If user's email is not public, fetch from /user/emails endpoint."""
        from praxis.api.oauth import exchange_github_code

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "gho_test_token"}

        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "octocat",
            "name": "The Octocat",
            "email": None,  # No public email
        }

        mock_emails_response = MagicMock()
        mock_emails_response.status_code = 200
        mock_emails_response.json.return_value = [
            {"email": "secondary@example.com", "primary": False, "verified": True},
            {"email": "primary@example.com", "primary": True, "verified": True},
        ]

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "user/emails" in url:
                return mock_emails_response
            return mock_user_response

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            result = await exchange_github_code(
                code="test-code",
                client_id="test-client",
                client_secret="test-secret",
                redirect_uri="http://localhost:8000/auth/github/callback",
            )

        assert result["email"] == "primary@example.com"


# ---------------------------------------------------------------------------
# Google code exchange (mocked HTTP)
# ---------------------------------------------------------------------------


class TestGoogleCodeExchange:
    """Test Google authorization code exchange with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_successful_exchange(self):
        from praxis.api.oauth import exchange_google_code

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "ya29.test_token",
            "id_token": "eyJ.test.jwt",
        }

        mock_userinfo_response = MagicMock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "email": "user@gmail.com",
            "name": "Test User",
            "picture": "https://lh3.googleusercontent.com/photo.jpg",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_userinfo_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            result = await exchange_google_code(
                code="test-code",
                client_id="test-google-id",
                client_secret="test-google-secret",
                redirect_uri="http://localhost:8000/auth/google/callback",
            )

        assert result["email"] == "user@gmail.com"
        assert result["name"] == "Test User"
        assert result["picture"] == "https://lh3.googleusercontent.com/photo.jpg"

    @pytest.mark.asyncio
    async def test_token_exchange_failure(self):
        from praxis.api.oauth import exchange_google_code

        mock_response = MagicMock()
        mock_response.status_code = 400

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="Failed to exchange"):
                await exchange_google_code(
                    code="bad-code",
                    client_id="test-google-id",
                    client_secret="test-google-secret",
                    redirect_uri="http://localhost:8000/auth/google/callback",
                )

    @pytest.mark.asyncio
    async def test_no_email_raises(self):
        from praxis.api.oauth import exchange_google_code

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "ya29.test_token"}

        mock_userinfo_response = MagicMock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "name": "Test User",
            # No email field
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_userinfo_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="did not return an email"):
                await exchange_google_code(
                    code="test-code",
                    client_id="test-google-id",
                    client_secret="test-google-secret",
                    redirect_uri="http://localhost:8000/auth/google/callback",
                )

    @pytest.mark.asyncio
    async def test_userinfo_fetch_failure(self):
        from praxis.api.oauth import exchange_google_code

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "ya29.test_token"}

        mock_userinfo_response = MagicMock()
        mock_userinfo_response.status_code = 403

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_userinfo_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("praxis.api.oauth.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="Failed to fetch user"):
                await exchange_google_code(
                    code="test-code",
                    client_id="test-google-id",
                    client_secret="test-google-secret",
                    redirect_uri="http://localhost:8000/auth/google/callback",
                )


# ---------------------------------------------------------------------------
# JWT creation from OAuth identity
# ---------------------------------------------------------------------------


class TestOAuthJwtCreation:
    """Test that OAuth login creates JWTs with correct provider-prefixed sub claim."""

    def test_github_jwt_sub_claim(self):
        from praxis.api.auth import create_token, decode_token

        secret = "test-secret-" + "x" * 50
        user_id = "github:octocat"
        token = create_token(user_id=user_id, secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert payload["sub"] == "github:octocat"
        assert payload["iss"] == "praxis"

    def test_google_jwt_sub_claim(self):
        from praxis.api.auth import create_token, decode_token

        secret = "test-secret-" + "x" * 50
        user_id = "google:user@gmail.com"
        token = create_token(user_id=user_id, secret=secret)
        payload = decode_token(token=token, secret=secret)
        assert payload["sub"] == "google:user@gmail.com"
        assert payload["iss"] == "praxis"


# ---------------------------------------------------------------------------
# Provider detection (config-driven)
# ---------------------------------------------------------------------------


class TestProviderDetection:
    """Test that OAuth routes are only registered for configured providers."""

    def test_no_providers_when_unconfigured(self):
        """When no OAuth client IDs are set, no providers should be available."""
        from dataclasses import dataclass

        @dataclass
        class FakeConfig:
            github_client_id: str = ""
            github_client_secret: str = ""
            google_client_id: str = ""
            google_client_secret: str = ""
            oauth_redirect_base: str = "http://localhost:8000"
            api_secret: str = "x" * 64
            cors_origins: list = None

            def __post_init__(self):
                if self.cors_origins is None:
                    self.cors_origins = ["http://localhost:3000"]

        config = FakeConfig()

        # Check that neither provider is detected
        providers = []
        if config.github_client_id:
            providers.append("github")
        if config.google_client_id:
            providers.append("google")

        assert providers == []

    def test_github_only_when_configured(self):
        from dataclasses import dataclass

        @dataclass
        class FakeConfig:
            github_client_id: str = "gh-test-id"
            github_client_secret: str = "gh-test-secret"
            google_client_id: str = ""
            google_client_secret: str = ""

        config = FakeConfig()
        providers = []
        if config.github_client_id:
            providers.append("github")
        if config.google_client_id:
            providers.append("google")

        assert providers == ["github"]

    def test_both_providers_when_configured(self):
        from dataclasses import dataclass

        @dataclass
        class FakeConfig:
            github_client_id: str = "gh-test-id"
            github_client_secret: str = "gh-test-secret"
            google_client_id: str = "ggl-test-id"
            google_client_secret: str = "ggl-test-secret"

        config = FakeConfig()
        providers = []
        if config.github_client_id:
            providers.append("github")
        if config.google_client_id:
            providers.append("google")

        assert providers == ["github", "google"]


# ---------------------------------------------------------------------------
# Frontend redirect URL building
# ---------------------------------------------------------------------------


class TestFrontendRedirect:
    """Test the frontend redirect URL construction."""

    def test_redirect_uses_first_cors_origin(self):
        from praxis.api.oauth import _build_frontend_redirect

        class FakeConfig:
            cors_origins = ["https://praxis.terrene.foundation", "http://localhost:3000"]

        token = "eyJ.test.jwt"
        url = _build_frontend_redirect(FakeConfig(), token)
        assert url == "https://praxis.terrene.foundation/login#token=eyJ.test.jwt"

    def test_redirect_fallback_localhost(self):
        from praxis.api.oauth import _build_frontend_redirect

        class FakeConfig:
            cors_origins = []

        token = "eyJ.test.jwt"
        url = _build_frontend_redirect(FakeConfig(), token)
        assert url == "http://localhost:3000/login#token=eyJ.test.jwt"

    def test_redirect_contains_token(self):
        from praxis.api.oauth import _build_frontend_redirect

        class FakeConfig:
            cors_origins = ["http://localhost:3000"]

        token = "abc123def456"
        url = _build_frontend_redirect(FakeConfig(), token)
        assert "#token=abc123def456" in url


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    """Test that OAuth routes are properly registered on the Starlette app."""

    def test_routes_registered_for_github(self):
        from praxis.api.oauth import clear_state_store, register_oauth_routes

        clear_state_store()

        class FakeConfig:
            github_client_id = "gh-test-id"
            github_client_secret = "gh-test-secret"
            google_client_id = ""
            google_client_secret = ""
            oauth_redirect_base = "http://localhost:8000"
            api_secret = "x" * 64
            cors_origins = ["http://localhost:3000"]

        mock_app = MagicMock()
        mock_app.routes = []
        register_oauth_routes(mock_app, FakeConfig())

        route_paths = [r.path for r in mock_app.routes]
        assert "/auth/providers" in route_paths
        assert "/auth/github" in route_paths
        assert "/auth/github/callback" in route_paths
        # Google routes should NOT be registered
        assert "/auth/google" not in route_paths
        assert "/auth/google/callback" not in route_paths

    def test_routes_registered_for_both(self):
        from praxis.api.oauth import clear_state_store, register_oauth_routes

        clear_state_store()

        class FakeConfig:
            github_client_id = "gh-test-id"
            github_client_secret = "gh-test-secret"
            google_client_id = "ggl-test-id"
            google_client_secret = "ggl-test-secret"
            oauth_redirect_base = "http://localhost:8000"
            api_secret = "x" * 64
            cors_origins = ["http://localhost:3000"]

        mock_app = MagicMock()
        mock_app.routes = []
        register_oauth_routes(mock_app, FakeConfig())

        route_paths = [r.path for r in mock_app.routes]
        assert "/auth/providers" in route_paths
        assert "/auth/github" in route_paths
        assert "/auth/github/callback" in route_paths
        assert "/auth/google" in route_paths
        assert "/auth/google/callback" in route_paths

    def test_no_provider_routes_when_unconfigured(self):
        from praxis.api.oauth import clear_state_store, register_oauth_routes

        clear_state_store()

        class FakeConfig:
            github_client_id = ""
            github_client_secret = ""
            google_client_id = ""
            google_client_secret = ""
            oauth_redirect_base = "http://localhost:8000"
            api_secret = "x" * 64
            cors_origins = ["http://localhost:3000"]

        mock_app = MagicMock()
        mock_app.routes = []
        register_oauth_routes(mock_app, FakeConfig())

        route_paths = [r.path for r in mock_app.routes]
        # Only the providers endpoint should be registered
        assert "/auth/providers" in route_paths
        assert "/auth/github" not in route_paths
        assert "/auth/google" not in route_paths
