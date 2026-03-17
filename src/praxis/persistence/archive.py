# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Session export/import — portable archive format for CO sessions.

Provides functions to export a complete session as a portable dict
and import a session from such an archive. This enables session
migration, backup, and offline analysis.

The archive format includes:
    - Session metadata (workspace, domain, state, constraints)
    - Deliberation records (hash-chained decisions, observations, escalations)
    - Constraint events (evaluation history)
    - Version and timestamp for archive format tracking
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def export_session(
    session_id: str,
    *,
    session_manager,
    deliberation_engine=None,
    constraint_enforcer=None,
) -> dict:
    """Export a complete session as a portable archive dict.

    Assembles all session data, deliberation records, and constraint
    events into a single dict suitable for serialization and import.

    Args:
        session_id: The session to export.
        session_manager: SessionManager instance containing the session.
        deliberation_engine: Optional DeliberationEngine for the session.
        constraint_enforcer: Optional ConstraintEnforcer for the session.

    Returns:
        A portable archive dict containing all session data.

    Raises:
        KeyError: If the session is not found in the session manager.
    """
    # Get session data -- let KeyError propagate if not found
    session_data = session_manager.get_session(session_id)

    # Get deliberation records
    deliberation_records = []
    if deliberation_engine is not None:
        records, _ = deliberation_engine.get_timeline()
        deliberation_records = records

    # Get constraint events
    constraint_events = []
    if constraint_enforcer is not None:
        constraint_events = constraint_enforcer.get_events()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    archive = {
        "version": "1.0",
        "exported_at": now,
        "session": session_data,
        "deliberation": deliberation_records,
        "constraint_events": constraint_events,
    }

    logger.info(
        "Exported session %s: %d deliberation records, %d constraint events",
        session_id,
        len(deliberation_records),
        len(constraint_events),
    )

    return archive


def import_session(
    archive: dict,
    *,
    session_manager,
) -> str:
    """Import a session from a portable archive. Returns new session_id.

    Creates a new session in the provided SessionManager with the data
    from the archive. The session gets a new session_id to avoid
    conflicts with existing sessions.

    Args:
        archive: A portable archive dict (as produced by export_session).
        session_manager: SessionManager to create the imported session in.

    Returns:
        The new session_id for the imported session.

    Raises:
        ValueError: If the archive is missing required fields.
    """
    if not archive:
        raise ValueError(
            "Invalid archive: archive dict must not be empty. "
            "Provide a valid archive dict as produced by export_session()."
        )

    if "session" not in archive:
        raise ValueError(
            "Invalid archive: missing 'session' key. "
            "The archive dict must contain a 'session' key with session data."
        )

    session_data = archive["session"]

    if not isinstance(session_data, dict):
        raise ValueError(
            "Invalid archive: 'session' must be a dict. "
            f"Got {type(session_data).__name__} instead."
        )

    # Extract fields from the archived session
    workspace_id = session_data.get("workspace_id", "imported")
    domain = session_data.get("domain", "coc")
    constraints = session_data.get("constraint_envelope")

    # Create a new session with the imported data
    new_session = session_manager.create_session(
        workspace_id=workspace_id,
        domain=domain,
        constraints=constraints,
    )

    new_session_id = new_session["session_id"]

    logger.info(
        "Imported session from archive: original=%s, new=%s",
        session_data.get("session_id", "unknown"),
        new_session_id,
    )

    return new_session_id
