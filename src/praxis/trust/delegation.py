# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Delegation chain management — authority delegation with constraint tightening.

Delegation records grant authority from a parent to a child within the trust
chain. The fundamental invariant is constraint tightening: a child delegation
can only have constraints that are equal to or tighter than its parent's
constraints across all five dimensions (Financial, Operational, Temporal,
Data Access, Communication).

Revocation cascades — revoking a delegation invalidates all child delegations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from praxis.trust.crypto import canonical_hash, sign_hash


@dataclass(frozen=True)
class DelegationRecord:
    """Authority delegation from parent to child.

    Each delegation references its parent via parent_hash, forming a
    cryptographic chain. Constraints must be equal or tighter than
    the parent's constraints.
    """

    delegation_id: str
    session_id: str
    parent_id: str
    delegate_id: str
    constraints: dict
    payload: dict
    content_hash: str
    signature: str
    signer_key_id: str
    parent_hash: str
    created_at: str


def validate_constraint_tightening(parent: dict, child: dict) -> bool:
    """Verify that child constraints are equal or tighter than parent.

    Checks all five constraint dimensions:
        - financial: child max_spend <= parent max_spend
        - operational: child allowed_actions is subset of parent
        - temporal: child max_duration_minutes <= parent max_duration_minutes
        - data_access: child allowed_paths is subset of parent
        - communication: child allowed_channels is subset of parent

    Args:
        parent: The parent constraint envelope (5-dimensional dict).
        child: The child constraint envelope to validate against parent.

    Returns:
        True if child constraints are equal or tighter across all dimensions.
        False if any dimension is looser.
    """
    # Financial: child max_spend must be <= parent max_spend
    parent_financial = parent.get("financial", {})
    child_financial = child.get("financial", {})
    parent_max_spend = parent_financial.get("max_spend", 0)
    child_max_spend = child_financial.get("max_spend", 0)
    if child_max_spend > parent_max_spend:
        return False

    # Operational: child allowed_actions must be a subset of parent
    parent_ops = parent.get("operational", {})
    child_ops = child.get("operational", {})
    parent_actions = set(parent_ops.get("allowed_actions", []))
    child_actions = set(child_ops.get("allowed_actions", []))
    if not child_actions.issubset(parent_actions):
        return False

    # Temporal: child max_duration_minutes must be <= parent
    parent_temporal = parent.get("temporal", {})
    child_temporal = child.get("temporal", {})
    parent_duration = parent_temporal.get("max_duration_minutes", 0)
    child_duration = child_temporal.get("max_duration_minutes", 0)
    if child_duration > parent_duration:
        return False

    # Data Access: child allowed_paths must be a subset of parent
    parent_data = parent.get("data_access", {})
    child_data = child.get("data_access", {})
    parent_paths = set(parent_data.get("allowed_paths", []))
    child_paths = set(child_data.get("allowed_paths", []))
    if not child_paths.issubset(parent_paths):
        return False

    # Communication: child allowed_channels must be a subset of parent
    parent_comm = parent.get("communication", {})
    child_comm = child.get("communication", {})
    parent_channels = set(parent_comm.get("allowed_channels", []))
    child_channels = set(child_comm.get("allowed_channels", []))
    if not child_channels.issubset(parent_channels):
        return False

    return True


def create_delegation(
    session_id: str,
    parent_id: str,
    parent_constraints: dict,
    delegate_id: str,
    delegate_constraints: dict,
    key_id: str,
    key_manager,
    parent_hash: str,
) -> DelegationRecord:
    """Create a signed delegation record. Validates constraint tightening.

    Args:
        session_id: Session this delegation belongs to.
        parent_id: ID of the parent record (genesis content_hash or delegation_id).
        parent_constraints: The parent's constraint envelope.
        delegate_id: Identity of the delegate receiving authority.
        delegate_constraints: The delegate's constraint envelope (must be tighter).
        key_id: Signing key identifier.
        key_manager: KeyManager instance for signing.
        parent_hash: Content hash of the parent record (chain link).

    Returns:
        A signed DelegationRecord.

    Raises:
        ValueError: If inputs are empty or constraint tightening fails.
        KeyError: If key_id is not found in the key manager.
    """
    # Validate inputs
    if not session_id:
        raise ValueError("session_id must not be empty")
    if not delegate_id:
        raise ValueError("delegate_id must not be empty")
    if not key_id:
        raise ValueError("key_id must not be empty")

    # Enforce the constraint tightening invariant
    if not validate_constraint_tightening(parent_constraints, delegate_constraints):
        raise ValueError(
            "Constraint tightening violation: delegate constraints must be "
            "equal or tighter than parent constraints across all five dimensions "
            "(Financial, Operational, Temporal, Data Access, Communication)"
        )

    delegation_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    payload = {
        "type": "delegation",
        "version": "1.0",
        "delegation_id": delegation_id,
        "session_id": session_id,
        "parent_id": parent_id,
        "delegate_id": delegate_id,
        "constraints": delegate_constraints,
        "signer_key_id": key_id,
        "parent_hash": parent_hash,
        "created_at": created_at,
    }

    content_hash = canonical_hash(payload)
    signature = sign_hash(content_hash, key_id, key_manager)

    return DelegationRecord(
        delegation_id=delegation_id,
        session_id=session_id,
        parent_id=parent_id,
        delegate_id=delegate_id,
        constraints=delegate_constraints,
        payload=payload,
        content_hash=content_hash,
        signature=signature,
        signer_key_id=key_id,
        parent_hash=parent_hash,
        created_at=created_at,
    )


def revoke_delegation(
    delegation_id: str,
    key_id: str,
    key_manager,
    parent_hash: str,
) -> dict:
    """Create a revocation entry that invalidates a delegation and all its children.

    The revocation is itself a signed record in the trust chain, ensuring that
    revocations are also tamper-evident. Cascade revocation of child delegations
    is computed at read time by walking the chain.

    Args:
        delegation_id: ID of the delegation to revoke.
        key_id: Signing key identifier.
        key_manager: KeyManager instance for signing.
        parent_hash: Content hash of the delegation being revoked (chain link).

    Returns:
        A dict containing the signed revocation entry with fields:
        type, revoked_delegation_id, content_hash, signature, signer_key_id,
        parent_hash, created_at.
    """
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    payload = {
        "type": "revocation",
        "version": "1.0",
        "revoked_delegation_id": delegation_id,
        "signer_key_id": key_id,
        "parent_hash": parent_hash,
        "created_at": created_at,
    }

    content_hash = canonical_hash(payload)
    signature = sign_hash(content_hash, key_id, key_manager)

    return {
        "type": "revocation",
        "revoked_delegation_id": delegation_id,
        "payload": payload,
        "content_hash": content_hash,
        "signature": signature,
        "signer_key_id": key_id,
        "parent_hash": parent_hash,
        "created_at": created_at,
    }
