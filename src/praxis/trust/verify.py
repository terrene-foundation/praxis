# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Trust chain verification — validates integrity of entire trust chains.

Verifies the complete trust chain for a session: genesis, delegations,
audit anchors, and attestations. For each entry, it recomputes the
content hash, verifies the signature, and checks the parent hash link.

The verifier distinguishes between:
    - "bad_hash": content_hash doesn't match recomputed hash
    - "bad_signature": signature doesn't verify with the public key
    - "broken_parent_link": parent_hash doesn't match previous entry
    - "unknown_key": signer's public key not available (not a signature failure)
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

import jcs
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


@dataclass(frozen=True)
class VerificationResult:
    """Result of trust chain verification.

    Attributes:
        valid: True if the entire chain verified successfully.
        total_entries: Number of entries in the chain.
        verified_entries: Number of entries that passed all checks.
        breaks: List of dicts describing each break found. Each dict has:
                position (int), reason (str), entry_id (str or None).
    """

    valid: bool
    total_entries: int
    verified_entries: int
    breaks: list[dict]


def _load_public_key(pem_str: str) -> Ed25519PublicKey:
    """Load an Ed25519 public key from PEM string.

    Args:
        pem_str: PEM-encoded public key string.

    Returns:
        Ed25519PublicKey instance.

    Raises:
        ValueError: If the PEM string is invalid or not an Ed25519 key.
    """
    pem_bytes = pem_str.encode("utf-8") if isinstance(pem_str, str) else pem_str
    key = serialization.load_pem_public_key(pem_bytes)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError(f"Expected Ed25519 public key, got {type(key).__name__}")
    return key


def verify_chain(entries: list[dict], public_keys: dict[str, str]) -> VerificationResult:
    """Verify an entire trust chain from exported data.

    For each entry:
        1. Recompute content_hash from payload using JCS + SHA-256
        2. Verify content_hash matches stored value
        3. Verify signature using the signer's public key
        4. Verify parent_hash matches the previous entry's content_hash
        5. Verify first entry (genesis) has no parent_hash

    Does not stop at the first break -- enumerates all breaks for forensics.

    Args:
        entries: Ordered list of chain entry dicts. Each must have:
                 payload, content_hash, signature, signer_key_id, parent_hash.
        public_keys: Mapping of key_id -> PEM-encoded public key string.

    Returns:
        VerificationResult with validity status and any breaks found.
    """
    if not entries:
        return VerificationResult(valid=True, total_entries=0, verified_entries=0, breaks=[])

    breaks: list[dict] = []
    verified_count = 0
    previous_hash: str | None = None

    for i, entry in enumerate(entries):
        entry_id = (
            entry.get("payload", {}).get("anchor_id")
            or entry.get("payload", {}).get("delegation_id")
            or entry.get("payload", {}).get("session_id")
            or f"entry-{i}"
        )
        entry_valid = True

        # Step 1: Recompute content_hash from payload
        payload = entry.get("payload", {})
        canonical = jcs.canonicalize(payload)
        expected_hash = hashlib.sha256(canonical).hexdigest()

        stored_hash = entry.get("content_hash", "")
        if expected_hash != stored_hash:
            breaks.append(
                {
                    "position": i,
                    "reason": "bad_hash",
                    "entry_id": entry_id,
                }
            )
            entry_valid = False

        # Step 2: Verify signature with public key
        signer_key_id = entry.get("signer_key_id", "")
        signature_b64 = entry.get("signature", "")

        if signer_key_id not in public_keys:
            breaks.append(
                {
                    "position": i,
                    "reason": "unknown_key",
                    "entry_id": entry_id,
                }
            )
            entry_valid = False
        elif entry_valid:
            # Only verify signature if hash matched (otherwise signature check is meaningless)
            try:
                pub_key = _load_public_key(public_keys[signer_key_id])
                hash_bytes = bytes.fromhex(stored_hash)
                sig_bytes = base64.urlsafe_b64decode(signature_b64)
                pub_key.verify(sig_bytes, hash_bytes)
            except Exception:
                breaks.append(
                    {
                        "position": i,
                        "reason": "bad_signature",
                        "entry_id": entry_id,
                    }
                )
                entry_valid = False

        # Step 3: Verify parent hash chain link
        stored_parent_hash = entry.get("parent_hash")

        if i == 0:
            # First entry (genesis) must have no parent_hash
            if stored_parent_hash is not None:
                breaks.append(
                    {
                        "position": i,
                        "reason": "broken_parent_link",
                        "entry_id": entry_id,
                    }
                )
                entry_valid = False
        else:
            # Subsequent entries must link to previous entry's content_hash
            if stored_parent_hash != previous_hash:
                breaks.append(
                    {
                        "position": i,
                        "reason": "broken_parent_link",
                        "entry_id": entry_id,
                    }
                )
                entry_valid = False

        if entry_valid:
            verified_count += 1

        previous_hash = stored_hash

    valid = len(breaks) == 0
    return VerificationResult(
        valid=valid,
        total_entries=len(entries),
        verified_entries=verified_count,
        breaks=breaks,
    )
