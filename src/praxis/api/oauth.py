# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
OAuth2 SSO login flows for GitHub and Google.

Implements the standard authorization code flow for both providers:
1. User clicks SSO button -> frontend redirects to /auth/{provider}
2. Backend redirects to provider's authorization URL with state param
3. Provider redirects back to /auth/{provider}/callback with code + state
4. Backend exchanges code for access token, fetches user info
5. Backend creates a Praxis JWT and redirects to frontend with token in URL fragment

Security:
- CSRF protection via random `state` parameter validated on callback
- State entries expire after 5 minutes
- All provider communication uses HTTPS
- No new dependencies -- uses httpx (available via kailash)
"""

from __future__ import annotations

import logging
import secrets
import time
import urllib.parse
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State store for CSRF protection
# ---------------------------------------------------------------------------

# In-memory state store: {state_token: expiry_timestamp}
# Short-lived (5 minutes). Resets on process restart, which is acceptable
# because OAuth state tokens are transient by design.
_oauth_state_store: dict[str, float] = {}

# State token TTL in seconds
_STATE_TTL = 300  # 5 minutes

# Maximum stored state entries (prevents memory exhaustion)
_MAX_STATE_ENTRIES = 10000


def _generate_state() -> str:
    """Generate a cryptographically random state token and store it.

    Returns:
        The state token string.
    """
    # Evict expired entries on generation to keep memory bounded
    _evict_expired_states()

    if len(_oauth_state_store) >= _MAX_STATE_ENTRIES:
        # Force eviction of oldest entries
        sorted_entries = sorted(_oauth_state_store.items(), key=lambda x: x[1])
        for key, _ in sorted_entries[: len(sorted_entries) // 2]:
            _oauth_state_store.pop(key, None)

    state = secrets.token_urlsafe(32)
    _oauth_state_store[state] = time.time() + _STATE_TTL
    return state


def _validate_state(state: str) -> bool:
    """Validate and consume a state token.

    Args:
        state: The state token from the callback.

    Returns:
        True if the state is valid and not expired, False otherwise.
    """
    if not state:
        return False

    expiry = _oauth_state_store.pop(state, None)
    if expiry is None:
        return False

    if time.time() > expiry:
        return False

    return True


def _evict_expired_states() -> None:
    """Remove expired state entries."""
    now = time.time()
    expired = [k for k, v in _oauth_state_store.items() if now > v]
    for k in expired:
        _oauth_state_store.pop(k, None)


def clear_state_store() -> None:
    """Clear all state entries. Used in tests."""
    _oauth_state_store.clear()


# ---------------------------------------------------------------------------
# GitHub OAuth2
# ---------------------------------------------------------------------------

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_USER_EMAILS_URL = "https://api.github.com/user/emails"
_GITHUB_SCOPES = "read:user,user:email"


def build_github_authorize_url(client_id: str, redirect_uri: str) -> str:
    """Build the GitHub OAuth authorization URL.

    Args:
        client_id: GitHub OAuth app client ID.
        redirect_uri: The callback URL GitHub will redirect to.

    Returns:
        Full authorization URL with state parameter.
    """
    state = _generate_state()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": _GITHUB_SCOPES,
        "state": state,
    }
    return f"{_GITHUB_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


async def exchange_github_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Exchange a GitHub authorization code for user information.

    Args:
        code: The authorization code from GitHub callback.
        client_id: GitHub OAuth app client ID.
        client_secret: GitHub OAuth app client secret.
        redirect_uri: The callback URL (must match the one used in authorization).

    Returns:
        Dict with user info: {"username": str, "email": str, "name": str}

    Raises:
        ValueError: If the code exchange or user info fetch fails.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Exchange code for access token
        token_response = await client.post(
            _GITHUB_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error("GitHub token exchange failed: %d", token_response.status_code)
            raise ValueError("Failed to exchange authorization code with GitHub")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            error_desc = token_data.get("error_description", "Unknown error")
            logger.error("GitHub token exchange returned no access_token: %s", error_desc)
            raise ValueError("GitHub did not return an access token")

        # Fetch user profile
        user_response = await client.get(
            _GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        if user_response.status_code != 200:
            logger.error("GitHub user fetch failed: %d", user_response.status_code)
            raise ValueError("Failed to fetch user profile from GitHub")

        user_data = user_response.json()
        username = user_data.get("login", "")
        name = user_data.get("name", "") or username
        email = user_data.get("email", "")

        # If email is not public, fetch from /user/emails
        if not email:
            try:
                emails_response = await client.get(
                    _GITHUB_USER_EMAILS_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    # Find primary verified email
                    for e in emails:
                        if e.get("primary") and e.get("verified"):
                            email = e.get("email", "")
                            break
                    # Fallback to first verified email
                    if not email:
                        for e in emails:
                            if e.get("verified"):
                                email = e.get("email", "")
                                break
            except Exception:
                logger.debug("Could not fetch GitHub user emails")

        return {
            "username": username,
            "email": email,
            "name": name,
        }


# ---------------------------------------------------------------------------
# Google OAuth2
# ---------------------------------------------------------------------------

_GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_GOOGLE_SCOPES = "openid email profile"


def build_google_authorize_url(client_id: str, redirect_uri: str) -> str:
    """Build the Google OAuth authorization URL.

    Args:
        client_id: Google OAuth client ID.
        redirect_uri: The callback URL Google will redirect to.

    Returns:
        Full authorization URL with state parameter.
    """
    state = _generate_state()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": _GOOGLE_SCOPES,
        "response_type": "code",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{_GOOGLE_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


async def exchange_google_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Exchange a Google authorization code for user information.

    Args:
        code: The authorization code from Google callback.
        client_id: Google OAuth client ID.
        client_secret: Google OAuth client secret.
        redirect_uri: The callback URL (must match the one used in authorization).

    Returns:
        Dict with user info: {"email": str, "name": str, "picture": str}

    Raises:
        ValueError: If the code exchange or user info fetch fails.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Exchange code for tokens
        token_response = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error("Google token exchange failed: %d", token_response.status_code)
            raise ValueError("Failed to exchange authorization code with Google")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            error_desc = token_data.get("error_description", "Unknown error")
            logger.error("Google token exchange returned no access_token: %s", error_desc)
            raise ValueError("Google did not return an access token")

        # Fetch user info from Google's userinfo endpoint
        userinfo_response = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        if userinfo_response.status_code != 200:
            logger.error("Google userinfo fetch failed: %d", userinfo_response.status_code)
            raise ValueError("Failed to fetch user profile from Google")

        userinfo = userinfo_response.json()
        email = userinfo.get("email", "")
        name = userinfo.get("name", "") or email
        picture = userinfo.get("picture", "")

        if not email:
            raise ValueError("Google did not return an email address")

        return {
            "email": email,
            "name": name,
            "picture": picture,
        }


# ---------------------------------------------------------------------------
# Starlette route handlers (registered in app.py)
# ---------------------------------------------------------------------------


def register_oauth_routes(starlette_app, config) -> None:
    """Register OAuth2 SSO routes on the Starlette app.

    Only registers routes for providers that have client IDs configured.
    If no OAuth providers are configured, no routes are registered.

    Args:
        starlette_app: The underlying Starlette app from Nexus.
        config: PraxisConfig instance with OAuth settings.
    """
    from starlette.requests import Request
    from starlette.responses import JSONResponse, RedirectResponse
    from starlette.routing import Route

    routes_added = []

    # --- OAuth provider availability endpoint ---
    async def _oauth_providers(request: Request) -> JSONResponse:
        """Return which OAuth providers are configured."""
        providers = []
        if getattr(config, "github_client_id", ""):
            providers.append("github")
        if getattr(config, "google_client_id", ""):
            providers.append("google")
        return JSONResponse({"providers": providers})

    starlette_app.routes.append(Route("/auth/providers", _oauth_providers, methods=["GET"]))
    routes_added.append("GET /auth/providers")

    # --- GitHub OAuth ---
    if getattr(config, "github_client_id", ""):
        github_redirect_uri = f"{config.oauth_redirect_base}/auth/github/callback"

        async def _github_authorize(request: Request) -> RedirectResponse:
            url = build_github_authorize_url(
                client_id=config.github_client_id,
                redirect_uri=github_redirect_uri,
            )
            return RedirectResponse(url=url, status_code=302)

        async def _github_callback(request: Request) -> RedirectResponse | JSONResponse:
            # Validate state parameter (CSRF protection)
            state = request.query_params.get("state", "")
            if not _validate_state(state):
                logger.warning("GitHub OAuth callback: invalid or expired state")
                return JSONResponse(
                    {"error": {"type": "oauth_error", "message": "Invalid or expired state"}},
                    status_code=400,
                )

            code = request.query_params.get("code", "")
            if not code:
                return JSONResponse(
                    {"error": {"type": "oauth_error", "message": "Missing authorization code"}},
                    status_code=400,
                )

            try:
                user_info = await exchange_github_code(
                    code=code,
                    client_id=config.github_client_id,
                    client_secret=config.github_client_secret,
                    redirect_uri=github_redirect_uri,
                )
            except ValueError as exc:
                logger.error("GitHub OAuth exchange failed: %s", exc)
                return JSONResponse(
                    {"error": {"type": "oauth_error", "message": "Authentication failed"}},
                    status_code=401,
                )

            # Create Praxis JWT
            from praxis.api.auth import create_token

            user_id = f"github:{user_info['username']}"
            token = create_token(user_id=user_id, secret=config.api_secret)

            logger.info(
                "OAuth: GitHub login for user '%s' (email=%s)",
                user_info["username"],
                user_info.get("email", ""),
            )

            # Redirect to frontend with token in URL fragment
            frontend_url = _build_frontend_redirect(config, token)
            return RedirectResponse(url=frontend_url, status_code=302)

        starlette_app.routes.append(
            Route("/auth/github", _github_authorize, methods=["GET"])
        )
        starlette_app.routes.append(
            Route("/auth/github/callback", _github_callback, methods=["GET"])
        )
        routes_added.extend(["GET /auth/github", "GET /auth/github/callback"])

    # --- Google OAuth ---
    if getattr(config, "google_client_id", ""):
        google_redirect_uri = f"{config.oauth_redirect_base}/auth/google/callback"

        async def _google_authorize(request: Request) -> RedirectResponse:
            url = build_google_authorize_url(
                client_id=config.google_client_id,
                redirect_uri=google_redirect_uri,
            )
            return RedirectResponse(url=url, status_code=302)

        async def _google_callback(request: Request) -> RedirectResponse | JSONResponse:
            # Validate state parameter (CSRF protection)
            state = request.query_params.get("state", "")
            if not _validate_state(state):
                logger.warning("Google OAuth callback: invalid or expired state")
                return JSONResponse(
                    {"error": {"type": "oauth_error", "message": "Invalid or expired state"}},
                    status_code=400,
                )

            code = request.query_params.get("code", "")
            if not code:
                return JSONResponse(
                    {"error": {"type": "oauth_error", "message": "Missing authorization code"}},
                    status_code=400,
                )

            try:
                user_info = await exchange_google_code(
                    code=code,
                    client_id=config.google_client_id,
                    client_secret=config.google_client_secret,
                    redirect_uri=google_redirect_uri,
                )
            except ValueError as exc:
                logger.error("Google OAuth exchange failed: %s", exc)
                return JSONResponse(
                    {"error": {"type": "oauth_error", "message": "Authentication failed"}},
                    status_code=401,
                )

            # Create Praxis JWT
            from praxis.api.auth import create_token

            user_id = f"google:{user_info['email']}"
            token = create_token(user_id=user_id, secret=config.api_secret)

            logger.info(
                "OAuth: Google login for user '%s' (name=%s)",
                user_info["email"],
                user_info.get("name", ""),
            )

            # Redirect to frontend with token in URL fragment
            frontend_url = _build_frontend_redirect(config, token)
            return RedirectResponse(url=frontend_url, status_code=302)

        starlette_app.routes.append(
            Route("/auth/google", _google_authorize, methods=["GET"])
        )
        starlette_app.routes.append(
            Route("/auth/google/callback", _google_callback, methods=["GET"])
        )
        routes_added.extend(["GET /auth/google", "GET /auth/google/callback"])

    if routes_added:
        logger.info("Registered OAuth routes: %s", ", ".join(routes_added))
    else:
        logger.debug("No OAuth providers configured, skipping OAuth route registration")


def _build_frontend_redirect(config, token: str) -> str:
    """Build the frontend redirect URL with the JWT in the URL fragment.

    Uses the first CORS origin as the frontend URL, which is the standard
    pattern for SPA OAuth flows.

    Args:
        config: PraxisConfig instance.
        token: The Praxis JWT token.

    Returns:
        Frontend URL with #token=JWT fragment.
    """
    # Use the first CORS origin as the frontend URL
    if config.cors_origins:
        frontend_base = config.cors_origins[0]
    else:
        frontend_base = "http://localhost:3000"

    return f"{frontend_base}/login#token={token}"
