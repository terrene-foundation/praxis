# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Shared cryptographic utilities for the trust layer.

All trust modules use these functions for canonical hashing, signing,
and signature verification. JCS (RFC 8785) canonicalization ensures
deterministic JSON serialization across platforms.
"""

from __future__ import annotations

import base64
import hashlib

import jcs


def canonical_hash(payload: dict) -> str:
    """SHA-256 hash of JCS-canonical JSON representation.

    Args:
        payload: The dictionary to canonicalize and hash.

    Returns:
        Hex-encoded SHA-256 digest of the canonicalized payload.

    Raises:
        TypeError: If payload is not a dict.
        ValueError: If payload cannot be serialized to JSON.
    """
    if not isinstance(payload, dict):
        raise TypeError(f"payload must be a dict, got {type(payload).__name__}")
    canonical = jcs.canonicalize(payload)
    return hashlib.sha256(canonical).hexdigest()


def sign_hash(hash_hex: str, key_id: str, key_manager) -> str:
    """Sign a hex-encoded hash and return a base64url-encoded signature.

    Args:
        hash_hex: The hex-encoded hash to sign.
        key_id: Identifier of the signing key in the key manager.
        key_manager: A KeyManager instance with sign(key_id, data) method.

    Returns:
        Base64url-encoded signature string (no padding).

    Raises:
        KeyError: If key_id is not found in the key manager.
        ValueError: If hash_hex is not valid hex.
    """
    hash_bytes = bytes.fromhex(hash_hex)
    sig_bytes = key_manager.sign(key_id, hash_bytes)
    return base64.urlsafe_b64encode(sig_bytes).decode()


def verify_signature(hash_hex: str, signature_b64: str, key_id: str, key_manager) -> bool:
    """Verify a base64url signature against a hex-encoded hash.

    Args:
        hash_hex: The hex-encoded hash that was signed.
        signature_b64: Base64url-encoded signature to verify.
        key_id: Identifier of the signing key in the key manager.
        key_manager: A KeyManager instance with verify(key_id, data, signature) method.

    Returns:
        True if the signature is valid, False otherwise.

    Raises:
        KeyError: If key_id is not found in the key manager.
    """
    hash_bytes = bytes.fromhex(hash_hex)
    sig_bytes = base64.urlsafe_b64decode(signature_b64)
    return key_manager.verify(key_id, hash_bytes, sig_bytes)
