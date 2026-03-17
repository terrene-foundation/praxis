# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Genesis record creation — root of trust for CO sessions.

The genesis record is the first entry in every trust chain. It establishes
who has authority, defines the initial constraint envelope across all five
dimensions (Financial, Operational, Temporal, Data Access, Communication),
and anchors the chain origin with a cryptographic signature.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from praxis.trust.crypto import canonical_hash, sign_hash


@dataclass(frozen=True)
class GenesisRecord:
    """Root of trust for a CO session.

    Every session begins with exactly one genesis record. It establishes
    the authority identity, constraint envelope, CO domain, and EATP namespace.
    The record is signed with Ed25519 and its content hash forms the root
    of the hash chain.
    """

    session_id: str
    authority_id: str
    namespace: str
    constraints: dict
    domain: str
    payload: dict
    content_hash: str
    signature: str
    signer_key_id: str
    created_at: str


def create_genesis(
    session_id: str,
    authority_id: str,
    key_id: str,
    key_manager,
    constraints: dict,
    domain: str = "coc",
    namespace: str = "praxis",
) -> GenesisRecord:
    """Create a signed genesis record for a new session.

    Steps:
        1. Validate all inputs
        2. Build the genesis payload
        3. Canonicalize with JCS (RFC 8785)
        4. Hash with SHA-256
        5. Sign the hash with Ed25519
        6. Return a GenesisRecord with all fields populated

    Args:
        session_id: Unique session identifier.
        authority_id: Identity of the human creating this genesis.
        key_id: Identifier of the signing key in the key manager.
        key_manager: KeyManager instance for signing.
        constraints: Initial 5-dimensional constraint envelope.
        domain: CO domain (coc, coe, cog, etc.). Defaults to "coc".
        namespace: EATP namespace. Defaults to "praxis".

    Returns:
        A signed GenesisRecord.

    Raises:
        ValueError: If any required field is empty.
        KeyError: If key_id is not found in the key manager.
    """
    # Validate inputs explicitly — never silently proceed with empty values
    if not session_id:
        raise ValueError("session_id must not be empty")
    if not authority_id:
        raise ValueError("authority_id must not be empty")
    if not key_id:
        raise ValueError("key_id must not be empty")

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Build the genesis payload with all required fields
    payload = {
        "type": "genesis",
        "version": "1.0",
        "session_id": session_id,
        "authority_id": authority_id,
        "namespace": namespace,
        "domain": domain,
        "constraints": constraints,
        "signer_key_id": key_id,
        "created_at": created_at,
    }

    # Canonicalize and hash
    content_hash = canonical_hash(payload)

    # Sign the hash
    signature = sign_hash(content_hash, key_id, key_manager)

    return GenesisRecord(
        session_id=session_id,
        authority_id=authority_id,
        namespace=namespace,
        constraints=constraints,
        domain=domain,
        payload=payload,
        content_hash=content_hash,
        signature=signature,
        signer_key_id=key_id,
        created_at=created_at,
    )
