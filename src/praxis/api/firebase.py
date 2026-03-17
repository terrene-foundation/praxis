# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Firebase ID token verification for the Praxis API.

Verifies Firebase ID tokens using Google's public certificates and PyJWT.
Does NOT require the firebase-admin SDK -- uses lightweight certificate
verification directly.

Flow:
1. Frontend authenticates via Firebase (GitHub/Google SSO popup)
2. Frontend sends the Firebase ID token to POST /auth/firebase
3. This module verifies the token against Google's public certificates
4. Returns decoded claims (uid, email, name, picture, provider)
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import jwt as pyjwt
from cryptography.x509 import load_pem_x509_certificate

logger = logging.getLogger(__name__)

# Google's public certificate endpoint for Firebase token verification
GOOGLE_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)

# Firebase project ID -- must match the audience claim in the token
FIREBASE_PROJECT_ID = "terrene-praxis"

# Cache for Google's public certificates
# Format: {"certs": {kid: pem_string, ...}, "expires_at": unix_timestamp}
_cert_cache: dict[str, Any] = {}

# Minimum cache TTL in seconds (even if no Cache-Control header)
_MIN_CACHE_TTL = 300  # 5 minutes


async def _fetch_google_certs() -> dict[str, str]:
    """Fetch and cache Google's public certificates for token verification.

    Certificates are cached based on the Cache-Control max-age header
    from Google's response. Falls back to a 5-minute minimum cache.

    Returns:
        Dict mapping key ID (kid) to PEM-encoded certificate string.

    Raises:
        ValueError: If certificates cannot be fetched.
    """
    now = time.time()

    # Return cached certs if still valid
    if _cert_cache.get("certs") and now < _cert_cache.get("expires_at", 0):
        return _cert_cache["certs"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(GOOGLE_CERTS_URL)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Google certificates: %s", exc)
            # If we have stale certs, use them as fallback
            if _cert_cache.get("certs"):
                logger.warning("Using stale cached certificates")
                return _cert_cache["certs"]
            raise ValueError("Cannot fetch Google public certificates for token verification")

    certs = resp.json()

    # Parse Cache-Control header for max-age
    cache_control = resp.headers.get("cache-control", "")
    max_age = _MIN_CACHE_TTL
    for part in cache_control.split(","):
        part = part.strip()
        if part.startswith("max-age="):
            try:
                max_age = max(int(part[8:]), _MIN_CACHE_TTL)
            except ValueError:
                pass

    _cert_cache["certs"] = certs
    _cert_cache["expires_at"] = now + max_age

    logger.debug("Fetched %d Google certificates (cache TTL: %ds)", len(certs), max_age)
    return certs


def clear_cert_cache() -> None:
    """Clear the certificate cache. Used in tests."""
    _cert_cache.clear()


async def verify_firebase_token(id_token: str) -> dict[str, Any]:
    """Verify a Firebase ID token and return the decoded claims.

    Validates:
    - Token signature against Google's public certificates
    - Token audience matches the Firebase project ID
    - Token issuer matches the expected Firebase issuer
    - Token is not expired

    Args:
        id_token: The Firebase ID token string from the frontend.

    Returns:
        Decoded token claims dict containing at minimum:
        - sub: Firebase UID
        - email: User email
        - name: Display name (if available)
        - picture: Photo URL (if available)
        - firebase.sign_in_provider: The SSO provider used

    Raises:
        ValueError: If the token is invalid, expired, or cannot be verified.
    """
    if not id_token or not isinstance(id_token, str):
        raise ValueError("Firebase ID token must be a non-empty string")

    # Decode header to get key ID (kid)
    try:
        header = pyjwt.get_unverified_header(id_token)
    except pyjwt.exceptions.DecodeError:
        raise ValueError("Invalid token format: cannot decode header")

    kid = header.get("kid")
    if not kid:
        raise ValueError("Invalid token: missing key ID (kid) in header")

    # Fetch Google's public certificates
    certs = await _fetch_google_certs()

    if kid not in certs:
        raise ValueError(f"Invalid token: unknown key ID '{kid}'")

    # Load the X.509 certificate and extract the public key
    cert_pem = certs[kid]
    try:
        cert = load_pem_x509_certificate(cert_pem.encode("utf-8"))
        public_key = cert.public_key()
    except Exception as exc:
        raise ValueError(f"Failed to load certificate for key '{kid}': {exc}")

    # Verify and decode the token
    try:
        decoded = pyjwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=FIREBASE_PROJECT_ID,
            issuer=f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}",
        )
    except pyjwt.ExpiredSignatureError:
        raise ValueError("Firebase ID token has expired")
    except pyjwt.InvalidAudienceError:
        raise ValueError("Firebase ID token has invalid audience")
    except pyjwt.InvalidIssuerError:
        raise ValueError("Firebase ID token has invalid issuer")
    except pyjwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid Firebase ID token: {exc}")

    # Validate required claims
    if not decoded.get("sub"):
        raise ValueError("Firebase ID token missing 'sub' claim")
    if not decoded.get("email"):
        raise ValueError("Firebase ID token missing 'email' claim")

    logger.debug(
        "Verified Firebase token for uid=%s email=%s",
        decoded.get("sub"),
        decoded.get("email"),
    )

    return decoded


def extract_user_info(decoded_token: dict[str, Any]) -> dict[str, Any]:
    """Extract user information from a decoded Firebase ID token.

    Args:
        decoded_token: The decoded claims from verify_firebase_token().

    Returns:
        Dict with normalized user info:
        - uid: Firebase UID
        - email: User email
        - display_name: Display name
        - photo_url: Photo URL or None
        - provider: SSO provider (github.com, google.com)
    """
    uid = decoded_token.get("sub", "")
    email = decoded_token.get("email", "")
    display_name = decoded_token.get("name", "") or email.split("@")[0]
    photo_url = decoded_token.get("picture")

    # Extract the SSO provider from Firebase claims
    firebase_claims = decoded_token.get("firebase", {})
    provider = firebase_claims.get("sign_in_provider", "")

    return {
        "uid": uid,
        "email": email,
        "display_name": display_name,
        "photo_url": photo_url,
        "provider": provider,
    }
