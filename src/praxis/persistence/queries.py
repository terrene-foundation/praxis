# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Query patterns for Praxis persistence layer.

These functions provide higher-level query operations on top of
the in-memory stores in SessionManager, DeliberationEngine, and
ConstraintEnforcer. They handle pagination, filtering, ordering,
and complex queries like chain walking and timeline assembly.

For now, these work with in-memory stores. The actual DataFlow
integration can be added later without changing the interface.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_session(session_id: str, *, session_manager) -> dict | None:
    """Get a session by ID.

    Args:
        session_id: The session identifier to look up.
        session_manager: SessionManager instance to query.

    Returns:
        Session dict if found, None if not found.
    """
    if not session_id:
        raise ValueError(
            "session_id must not be empty. " "Provide a valid session identifier to look up."
        )
    try:
        return session_manager.get_session(session_id)
    except KeyError:
        logger.debug("Session '%s' not found in session manager", session_id)
        return None


def list_sessions(
    workspace_id: str | None = None,
    state: str | None = None,
    domain: str | None = None,
    limit: int = 100,
    offset: int = 0,
    *,
    session_manager,
) -> tuple[list[dict], int]:
    """List sessions with optional filters. Returns (sessions, total_count).

    Args:
        workspace_id: Filter by workspace. None returns all workspaces.
        state: Filter by state string. None returns all states.
        domain: Filter by CO domain. None returns all domains.
        limit: Maximum number of sessions to return. Defaults to 100.
        offset: Number of sessions to skip from the start. Defaults to 0.
        session_manager: SessionManager instance to query.

    Returns:
        Tuple of (sessions, total_count) where total_count is the total
        matching sessions before limit/offset.
    """
    # Get all sessions matching workspace and state filters
    # SessionManager.list_sessions supports workspace_id and state
    all_sessions = session_manager.list_sessions(workspace_id=workspace_id, state=state)

    # Apply domain filter (not natively supported by SessionManager.list_sessions)
    if domain is not None:
        all_sessions = [s for s in all_sessions if s.get("domain") == domain]

    total = len(all_sessions)
    page = all_sessions[offset : offset + limit]

    return page, total


def get_deliberation_timeline(
    session_id: str,
    record_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    *,
    deliberation_engine,
) -> tuple[list[dict], int]:
    """Get deliberation records for a session in chronological order.

    Args:
        session_id: The session to get records for.
        record_type: Filter by record type. None returns all types.
        limit: Maximum number of records to return.
        offset: Number of records to skip from the start.
        deliberation_engine: DeliberationEngine instance to query.

    Returns:
        Tuple of (records, total_count) where total_count is the total
        matching records before limit/offset.
    """
    if deliberation_engine is None:
        logger.debug("No deliberation engine provided for session '%s'", session_id)
        return [], 0

    return deliberation_engine.get_timeline(record_type=record_type, limit=limit, offset=offset)


def get_trust_chain(
    session_id: str,
    *,
    genesis_record=None,
    audit_chain=None,
    delegations: list | None = None,
) -> list[dict]:
    """Get all trust chain entries for a session in order.

    Assembles the complete trust chain from genesis, delegations,
    and audit anchors. Returns an ordered list of entry dicts
    suitable for verification.

    Args:
        session_id: The session to get the chain for.
        genesis_record: GenesisRecord instance (or None if no genesis).
        audit_chain: AuditChain instance (or None if no chain).
        delegations: List of DelegationRecord instances (or None).

    Returns:
        Ordered list of trust chain entry dicts.
    """
    entries: list[dict] = []

    # Add genesis record as first entry
    if genesis_record is not None:
        entries.append(
            {
                "payload": genesis_record.payload,
                "content_hash": genesis_record.content_hash,
                "signature": genesis_record.signature,
                "signer_key_id": genesis_record.signer_key_id,
                "parent_hash": None,
            }
        )

    # Add delegation records
    if delegations:
        for delegation in delegations:
            entries.append(
                {
                    "payload": delegation.payload,
                    "content_hash": delegation.content_hash,
                    "signature": delegation.signature,
                    "signer_key_id": delegation.signer_key_id,
                    "parent_hash": delegation.parent_hash,
                }
            )

    # Add audit anchors — loaded from DB via the public .anchors property
    if audit_chain is not None:
        for anchor in audit_chain.anchors:
            entries.append(
                {
                    "payload": anchor.payload,
                    "content_hash": anchor.content_hash,
                    "signature": anchor.signature,
                    "signer_key_id": anchor.signer_key_id,
                    "parent_hash": anchor.parent_hash,
                }
            )

    return entries


def get_constraint_events(
    session_id: str,
    dimension: str | None = None,
    gradient_result: str | None = None,
    *,
    constraint_enforcer,
) -> list[dict]:
    """Get constraint events with optional filters.

    Args:
        session_id: The session to get events for.
        dimension: Filter by constraint dimension. None returns all.
        gradient_result: Filter by gradient result. None returns all.
        constraint_enforcer: ConstraintEnforcer instance to query.

    Returns:
        List of constraint event dicts.
    """
    if constraint_enforcer is None:
        logger.debug("No constraint enforcer provided for session '%s'", session_id)
        return []

    events = constraint_enforcer.get_events()

    if dimension is not None:
        events = [e for e in events if e.get("dimension") == dimension]

    if gradient_result is not None:
        events = [e for e in events if e.get("verdict") == gradient_result]

    return events


def get_pending_held_actions(
    session_id: str | None = None,
    *,
    held_action_manager=None,
) -> list[dict]:
    """Get unresolved held actions.

    Queries DataFlow directly when possible. Falls back to the
    ``held_action_manager`` instance when provided (backward compat).

    Args:
        session_id: Filter by session. None returns all sessions.
        held_action_manager: Optional HeldActionManager instance.
            When provided and using DB mode, delegates to its
            ``get_pending()`` method which queries DataFlow.
            When None, queries DataFlow directly.

    Returns:
        List of pending held action dicts.
    """
    # If a manager is provided, use its get_pending (which now hits DataFlow)
    if held_action_manager is not None:
        pending = held_action_manager.get_pending(session_id=session_id)
    else:
        # Query DataFlow directly without requiring a manager instance
        try:
            from praxis.persistence.db_ops import db_list

            db_filter: dict = {"resolved": False}
            if session_id is not None:
                db_filter["session_id"] = session_id

            from praxis.core.constraint import _held_from_db

            records = db_list("HeldAction", filter=db_filter, limit=1000)
            pending = [_held_from_db(r) for r in records]
        except Exception:
            logger.debug("Failed to query DataFlow for held actions, returning empty")
            return []

    # Convert HeldAction dataclass instances to dicts
    result = []
    for held in pending:
        result.append(
            {
                "held_id": held.held_id,
                "session_id": held.session_id,
                "action": held.action,
                "resource": held.resource,
                "dimension": held.dimension,
                "level": held.verdict.level.value,
                "utilization": held.verdict.utilization,
                "reason": held.verdict.reason,
                "created_at": held.created_at,
                "resolved": held.resolved,
            }
        )

    return result


def get_session_stats(
    session_id: str,
    *,
    deliberation_engine=None,
    constraint_enforcer=None,
    audit_chain=None,
) -> dict:
    """Get session statistics: decision count, observation count, etc.

    Args:
        session_id: The session to get stats for.
        deliberation_engine: DeliberationEngine instance (optional).
        constraint_enforcer: ConstraintEnforcer instance (optional).
        audit_chain: AuditChain instance (optional).

    Returns:
        Dict with statistics including decision_count, observation_count,
        escalation_count, anchor_count, and constraint_status.
    """
    decision_count = 0
    observation_count = 0
    escalation_count = 0

    if deliberation_engine is not None:
        decisions, _ = deliberation_engine.get_timeline(record_type="decision")
        observations, _ = deliberation_engine.get_timeline(record_type="observation")
        escalations, _ = deliberation_engine.get_timeline(record_type="escalation")
        decision_count = len(decisions)
        observation_count = len(observations)
        escalation_count = len(escalations)

    anchor_count = 0
    if audit_chain is not None:
        anchor_count = audit_chain.length

    constraint_status = {}
    if constraint_enforcer is not None:
        constraint_status = constraint_enforcer.get_status()

    return {
        "session_id": session_id,
        "decision_count": decision_count,
        "observation_count": observation_count,
        "escalation_count": escalation_count,
        "anchor_count": anchor_count,
        "constraint_status": constraint_status,
    }
