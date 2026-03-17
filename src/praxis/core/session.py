# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Session lifecycle state machine for CO collaboration sessions.

Sessions progress through a strict state machine:
    CREATING -> ACTIVE -> PAUSED -> ACTIVE -> ARCHIVED
                       -> ARCHIVED

ARCHIVED is terminal — no transitions out.
Constraints can only be tightened, never loosened.
"""

from __future__ import annotations

import copy
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State machine definitions
# ---------------------------------------------------------------------------


class SessionState(str, Enum):
    """Valid states for a CO collaboration session."""

    CREATING = "creating"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


VALID_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.CREATING: {SessionState.ACTIVE},
    SessionState.ACTIVE: {SessionState.PAUSED, SessionState.ARCHIVED},
    SessionState.PAUSED: {SessionState.ACTIVE, SessionState.ARCHIVED},
    SessionState.ARCHIVED: set(),  # Terminal state — no transitions out
}


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class InvalidStateTransitionError(Exception):
    """Raised when a session state transition violates the state machine."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SessionNotActiveError(Exception):
    """Raised when an operation requires an active or paused session but it is archived."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PhaseGateError(Exception):
    """Raised when attempting to advance past a phase that has an approval gate.

    The caller must approve the held action before the phase can advance.
    """

    def __init__(self, message: str, held_action_id: str | None = None) -> None:
        super().__init__(message)
        self.held_action_id = held_action_id


class SessionPreconditionError(Exception):
    """Raised when session preconditions fail during creation.

    Defense-in-depth: validates genesis record, constraint envelope
    completeness, and domain config after initial creation. Failing
    this check means the session was created in an inconsistent state.
    """

    def __init__(self, message: str, checks_failed: list[str] | None = None) -> None:
        super().__init__(message)
        self.checks_failed = checks_failed or []


# ---------------------------------------------------------------------------
# Constraint templates
# ---------------------------------------------------------------------------

CONSTRAINT_TEMPLATES: dict[str, dict] = {
    "strict": {
        "financial": {"max_spend": 10.0, "current_spend": 0.0},
        "operational": {"allowed_actions": ["read"], "blocked_actions": ["delete", "deploy"]},
        "temporal": {"max_duration_minutes": 30, "elapsed_minutes": 0},
        "data_access": {
            "allowed_paths": ["/src/"],
            "blocked_paths": ["/secrets/", "/credentials/"],
        },
        "communication": {"allowed_channels": ["internal"], "blocked_channels": ["external"]},
    },
    "moderate": {
        "financial": {"max_spend": 100.0, "current_spend": 0.0},
        "operational": {
            "allowed_actions": ["read", "write", "execute"],
            "blocked_actions": ["delete"],
        },
        "temporal": {"max_duration_minutes": 120, "elapsed_minutes": 0},
        "data_access": {
            "allowed_paths": ["/src/", "/tests/", "/docs/"],
            "blocked_paths": ["/secrets/"],
        },
        "communication": {
            "allowed_channels": ["internal", "email"],
            "blocked_channels": ["external"],
        },
    },
    "permissive": {
        "financial": {"max_spend": 1000.0, "current_spend": 0.0},
        "operational": {
            "allowed_actions": ["read", "write", "execute", "delete", "deploy"],
            "blocked_actions": [],
        },
        "temporal": {"max_duration_minutes": 480, "elapsed_minutes": 0},
        "data_access": {
            "allowed_paths": ["/"],
            "blocked_paths": [],
        },
        "communication": {
            "allowed_channels": ["internal", "email", "external"],
            "blocked_channels": [],
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _validate_transition(current: SessionState, target: SessionState) -> None:
    """Validate that a state transition is allowed.

    Raises:
        InvalidStateTransitionError: If the transition is not in VALID_TRANSITIONS.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Cannot transition from '{current.value}' to '{target.value}'. "
            f"Valid transitions from '{current.value}': "
            f"{sorted(s.value for s in allowed) if allowed else 'none (terminal state)'}"
        )


def _is_tightening(current: dict, proposed: dict) -> bool:
    """Check if proposed constraints are strictly tighter than or equal to current.

    Tightening rules:
    - financial.max_spend: must be <= current
    - operational.allowed_actions: must be a subset of current
    - temporal.max_duration_minutes: must be <= current
    - data_access.allowed_paths: must be a subset of current
    - communication.allowed_channels: must be a subset of current

    Returns:
        True if proposed is tighter or equal, False if any dimension is loosened.
    """
    # Reject new dimensions not in current — adding dimensions is not tightening,
    # it is expanding the constraint surface which could bypass enforcement.
    for dim in proposed:
        if dim not in current:
            return False

    # Financial: lower max_spend is tighter
    if "financial" in proposed and "financial" in current:
        proposed_max = proposed["financial"].get("max_spend", 0)
        current_max = current["financial"].get("max_spend", 0)
        if proposed_max > current_max:
            return False

    # Operational: fewer allowed_actions is tighter
    if "operational" in proposed and "operational" in current:
        proposed_actions = set(proposed["operational"].get("allowed_actions", []))
        current_actions = set(current["operational"].get("allowed_actions", []))
        if not proposed_actions.issubset(current_actions):
            return False

    # Temporal: lower max_duration is tighter
    if "temporal" in proposed and "temporal" in current:
        proposed_dur = proposed["temporal"].get("max_duration_minutes", 0)
        current_dur = current["temporal"].get("max_duration_minutes", 0)
        if proposed_dur > current_dur:
            return False

    # Data access: fewer allowed_paths is tighter
    if "data_access" in proposed and "data_access" in current:
        proposed_paths = set(proposed["data_access"].get("allowed_paths", []))
        current_paths = set(current["data_access"].get("allowed_paths", []))
        if not proposed_paths.issubset(current_paths):
            return False

    # Communication: fewer allowed_channels is tighter
    if "communication" in proposed and "communication" in current:
        proposed_channels = set(proposed["communication"].get("allowed_channels", []))
        current_channels = set(current["communication"].get("allowed_channels", []))
        if not proposed_channels.issubset(current_channels):
            return False

    return True


# ---------------------------------------------------------------------------
# Domain YAML constraint resolution
# ---------------------------------------------------------------------------


def _resolve_domain_phases(domain: str) -> tuple[str | None, list[str]]:
    """Attempt to load phase definitions from the domain YAML.

    Returns a tuple of (first_phase_name, phase_name_list).
    If the domain cannot be loaded or has no phases, returns (None, []).
    This function never raises.
    """
    try:
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        config = loader.load_domain(domain)
        if config.phases:
            phase_names = [p["name"] for p in config.phases]
            return phase_names[0], phase_names
    except Exception as exc:
        logger.debug(
            "Could not load phases from domain '%s': %s",
            domain,
            exc,
        )
    return None, []


def _resolve_domain_template(domain: str, template_name: str) -> dict[str, Any] | None:
    """Attempt to load a constraint template from the domain YAML.

    Returns the template dict (with runtime fields injected) on success,
    or None if the domain or template cannot be loaded.  This function
    never raises — all errors are logged and result in a None return so
    that callers can fall back to hardcoded templates.
    """
    try:
        from praxis.domains.loader import DomainLoader

        loader = DomainLoader()
        raw_template = loader.get_constraint_template(domain, template_name)
        return _normalize_yaml_template(raw_template)
    except Exception as exc:
        logger.debug(
            "Could not load domain YAML template '%s' for domain '%s': %s",
            template_name,
            domain,
            exc,
        )
        return None


def _normalize_yaml_template(raw: dict[str, Any]) -> dict[str, Any]:
    """Inject runtime fields that domain YAML files do not carry.

    Domain YAMLs define declarative constraints (max_spend, allowed_paths, etc.)
    but not runtime state (current_spend, elapsed_minutes, etc.).  This function
    deep-copies the template and fills in the runtime defaults so the resulting
    envelope matches the structure that ConstraintEnforcer and _is_tightening
    expect.
    """
    template = copy.deepcopy(raw)

    # Financial: inject current_spend = 0.0
    if "financial" in template:
        template["financial"].setdefault("current_spend", 0.0)

    # Operational: inject empty blocked_actions list
    if "operational" in template:
        template["operational"].setdefault("blocked_actions", [])

    # Temporal: inject elapsed_minutes = 0
    if "temporal" in template:
        template["temporal"].setdefault("elapsed_minutes", 0)

    # Data access: inject empty blocked_paths list
    if "data_access" in template:
        template["data_access"].setdefault("blocked_paths", [])

    # Communication: inject empty blocked_channels list
    if "communication" in template:
        template["communication"].setdefault("blocked_channels", [])

    return template


# ---------------------------------------------------------------------------
# Format conversion helpers
# ---------------------------------------------------------------------------


def _session_to_db(session_dict: dict) -> dict:
    """Convert an in-memory session dict to DataFlow ``Session`` model fields.

    The DataFlow model uses ``id`` as primary key and stores several
    session-level values inside ``session_metadata`` because they are not
    first-class columns:

    * ``genesis_chain_entry`` — full genesis record for export
    * ``created_at`` / ``updated_at`` — ISO 8601 timestamps with Z suffix

    DataFlow auto-manages its own ``created_at`` / ``updated_at`` columns
    but those are not returned by the ReadNode and use a different format.
    Storing our own timestamps inside ``session_metadata`` keeps the
    round-trip lossless.
    """
    metadata = dict(session_dict.get("metadata") or {})
    genesis_chain_entry = session_dict.get("genesis_chain_entry")
    if genesis_chain_entry is not None:
        metadata["genesis_chain_entry"] = genesis_chain_entry

    # Persist our ISO timestamps inside session_metadata
    if session_dict.get("created_at"):
        metadata["created_at"] = session_dict["created_at"]
    if session_dict.get("updated_at"):
        metadata["updated_at"] = session_dict["updated_at"]

    # Persist phase tracking inside session_metadata
    if session_dict.get("current_phase") is not None:
        metadata["current_phase"] = session_dict["current_phase"]
    if session_dict.get("phase_list"):
        metadata["phase_list"] = session_dict["phase_list"]

    return {
        "id": session_dict["session_id"],
        "workspace_id": session_dict["workspace_id"],
        "domain": session_dict["domain"],
        "state": session_dict["state"],
        "genesis_id": session_dict.get("genesis_id"),
        "constraint_envelope": session_dict.get("constraint_envelope"),
        "session_metadata": metadata if metadata else None,
        "ended_at": session_dict.get("ended_at"),
    }


def _ensure_dict(value) -> dict | None:
    """Deserialize a value that may be a JSON string or already a dict.

    DataFlow ReadNode returns ``Optional[dict]`` columns as JSON strings.
    This helper normalizes them back to Python dicts.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _session_from_db(record: dict) -> dict:
    """Convert a DataFlow ``Session`` record back to the public session dict.

    Reverses the mapping performed by :func:`_session_to_db`, extracting
    ``genesis_chain_entry`` and our ISO timestamps from ``session_metadata``
    and restoring the ``session_id`` / ``metadata`` keys expected by callers.

    DataFlow ReadNode may return dict columns as JSON strings, so we
    normalize them via :func:`_ensure_dict` before processing.
    """
    raw_meta = dict(_ensure_dict(record.get("session_metadata")) or {})
    genesis_chain_entry = raw_meta.pop("genesis_chain_entry", None)
    created_at = raw_meta.pop("created_at", "")
    updated_at = raw_meta.pop("updated_at", "")
    current_phase = raw_meta.pop("current_phase", None)
    phase_list = raw_meta.pop("phase_list", [])
    constraint_envelope = _ensure_dict(record.get("constraint_envelope"))

    return {
        "session_id": record["id"],
        "workspace_id": record["workspace_id"],
        "domain": record["domain"],
        "state": record["state"],
        "genesis_id": record.get("genesis_id"),
        "genesis_chain_entry": genesis_chain_entry,
        "constraint_envelope": constraint_envelope,
        "current_phase": current_phase,
        "phase_list": phase_list if phase_list else [],
        "metadata": raw_meta,
        "created_at": created_at,
        "updated_at": updated_at,
        "ended_at": record.get("ended_at"),
    }


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------


class SessionManager:
    """Manages CO collaboration session lifecycle.

    Provides create, get, pause, resume, end, list, and constraint update
    operations.  Sessions follow a strict state machine and constraints
    can only be tightened, never loosened.

    Sessions are persisted to the DataFlow database so they survive
    process restarts.  Every mutation is written through ``db_ops``
    helpers that execute synchronous DataFlow workflows.

    Args:
        key_manager: Optional KeyManager for signing genesis records.
            When None, sessions are created without cryptographic genesis.
        key_id: Key identifier for signing operations. Defaults to "default".
    """

    def __init__(self, key_manager=None, key_id: str = "default") -> None:
        self.key_manager = key_manager
        self.key_id = key_id

    def create_session(
        self,
        workspace_id: str,
        domain: str = "coc",
        constraint_template: str = "moderate",
        constraints: dict | None = None,
        authority_id: str = "local-user",
    ) -> dict:
        """Create and activate a new CO collaboration session.

        Steps:
            1. Validate inputs
            2. Generate session_id (UUID4)
            3. Resolve constraint envelope (explicit constraints or template)
            4. Create genesis record if key_manager is available
            5. Set state to ACTIVE
            6. Persist to DataFlow and return session dict

        Args:
            workspace_id: Workspace to create the session in. Must not be empty.
            domain: CO domain (coc, coe, cog, etc.). Defaults to "coc".
            constraint_template: Template name for default constraints. Defaults to "moderate".
            constraints: Explicit constraint envelope. Overrides template if provided.
            authority_id: Identity of the human creating this session.

        Returns:
            Session dict with all fields populated.

        Raises:
            ValueError: If workspace_id is empty.
            ValueError: If constraint_template is not recognized and no explicit constraints given.
        """
        if not workspace_id:
            raise ValueError(
                "workspace_id must not be empty. "
                "Provide a valid workspace identifier to create a session."
            )

        session_id = str(uuid.uuid4())
        now = _now_utc_iso()

        # Resolve constraint envelope
        # Priority: 1) explicit constraints, 2) domain YAML template, 3) hardcoded fallback
        if constraints is not None:
            constraint_envelope = constraints
        else:
            # Try domain YAML first
            domain_template = _resolve_domain_template(domain, constraint_template)
            if domain_template is not None:
                constraint_envelope = domain_template
            elif constraint_template in CONSTRAINT_TEMPLATES:
                constraint_envelope = dict(CONSTRAINT_TEMPLATES[constraint_template])
            else:
                raise ValueError(
                    f"Unknown constraint template '{constraint_template}'. "
                    f"No matching template found in domain '{domain}' YAML or "
                    f"hardcoded defaults. "
                    f"Available hardcoded templates: {sorted(CONSTRAINT_TEMPLATES.keys())}. "
                    f"Provide explicit constraints or use a valid template name."
                )

        # Create genesis record if key_manager is available
        genesis_id = None
        genesis_chain_entry: dict | None = None
        if self.key_manager is not None:
            try:
                from praxis.trust.genesis import create_genesis

                genesis = create_genesis(
                    session_id=session_id,
                    authority_id=authority_id,
                    key_id=self.key_id,
                    key_manager=self.key_manager,
                    constraints=constraint_envelope,
                    domain=domain,
                )
                genesis_id = genesis.content_hash
                # Persist the full chain entry so export can reconstruct a
                # verifiable trust chain without re-computing the payload.
                genesis_chain_entry = {
                    "payload": genesis.payload,
                    "content_hash": genesis.content_hash,
                    "signature": genesis.signature,
                    "signer_key_id": genesis.signer_key_id,
                    "parent_hash": None,
                }
                logger.info(
                    "Created genesis record for session %s: %s",
                    session_id,
                    genesis_id,
                )
            except Exception as exc:
                logger.error(
                    "Failed to create genesis record for session %s: %s",
                    session_id,
                    exc,
                )
                raise

        # Resolve domain phase definitions
        current_phase, phase_list = _resolve_domain_phases(domain)

        session = {
            "session_id": session_id,
            "workspace_id": workspace_id,
            "domain": domain,
            "state": SessionState.ACTIVE.value,
            "genesis_id": genesis_id,
            "genesis_chain_entry": genesis_chain_entry,
            "constraint_envelope": constraint_envelope,
            "current_phase": current_phase,
            "phase_list": phase_list,
            "metadata": {},
            "created_at": now,
            "updated_at": now,
            "ended_at": None,
        }

        # Persist to DataFlow
        from praxis.persistence.db_ops import db_create

        db_create("Session", _session_to_db(session))

        # M10-02: Defense-in-depth — verify session preconditions after creation
        self._verify_preconditions(
            session_id=session_id,
            key_manager=self.key_manager,
            constraint_envelope=constraint_envelope,
            domain=domain,
            genesis_chain_entry=genesis_chain_entry,
        )

        logger.info(
            "Created session %s in workspace %s (domain=%s, state=%s)",
            session_id,
            workspace_id,
            domain,
            session["state"],
        )
        return dict(session)

    def get_session(self, session_id: str) -> dict:
        """Get a session by its ID.

        Args:
            session_id: The session identifier to look up.

        Returns:
            A copy of the session dict.

        Raises:
            KeyError: If no session with this ID exists.
        """
        from praxis.persistence.db_ops import db_read

        record = db_read("Session", session_id)
        if record is None:
            raise KeyError(
                f"Session '{session_id}' not found. "
                f"Verify the session_id is correct and the session was created in this manager."
            )
        return _session_from_db(record)

    def pause_session(self, session_id: str, reason: str = "") -> dict:
        """Pause an active session.

        Args:
            session_id: The session to pause.
            reason: Optional reason for pausing.

        Returns:
            Updated session dict.

        Raises:
            KeyError: If session not found.
            InvalidStateTransitionError: If session is not in ACTIVE state.
        """
        session = self.get_session(session_id)
        current_state = SessionState(session["state"])
        _validate_transition(current_state, SessionState.PAUSED)

        # Build updated metadata with pause reason
        metadata = dict(session.get("metadata") or {})
        if reason:
            metadata["pause_reason"] = reason

        # Persist state change
        from praxis.persistence.db_ops import db_update

        update_fields: dict = {
            "state": SessionState.PAUSED.value,
            "session_metadata": _build_session_metadata(session, metadata),
        }
        db_update("Session", session_id, update_fields)

        logger.info("Paused session %s (reason: %s)", session_id, reason or "none")
        return self.get_session(session_id)

    def resume_session(self, session_id: str) -> dict:
        """Resume a paused session.

        Args:
            session_id: The session to resume.

        Returns:
            Updated session dict.

        Raises:
            KeyError: If session not found.
            InvalidStateTransitionError: If session is not in PAUSED state.
        """
        session = self.get_session(session_id)
        current_state = SessionState(session["state"])
        _validate_transition(current_state, SessionState.ACTIVE)

        from praxis.persistence.db_ops import db_update

        metadata = dict(session.get("metadata") or {})
        update_fields: dict = {
            "state": SessionState.ACTIVE.value,
            "session_metadata": _build_session_metadata(session, metadata),
        }
        db_update("Session", session_id, update_fields)

        logger.info("Resumed session %s", session_id)
        return self.get_session(session_id)

    def end_session(self, session_id: str, summary: str = "") -> dict:
        """End a session by archiving it.

        This is a terminal operation — archived sessions cannot be resumed.

        Args:
            session_id: The session to end.
            summary: Optional summary of the session.

        Returns:
            Updated session dict with ended_at timestamp.

        Raises:
            KeyError: If session not found.
            InvalidStateTransitionError: If session is already archived.
        """
        session = self.get_session(session_id)
        current_state = SessionState(session["state"])
        _validate_transition(current_state, SessionState.ARCHIVED)

        now = _now_utc_iso()

        metadata = dict(session.get("metadata") or {})
        if summary:
            metadata["summary"] = summary

        from praxis.persistence.db_ops import db_update

        update_fields: dict = {
            "state": SessionState.ARCHIVED.value,
            "ended_at": now,
            "session_metadata": _build_session_metadata(session, metadata, updated_at=now),
        }
        db_update("Session", session_id, update_fields)

        logger.info("Ended session %s (summary: %s)", session_id, summary or "none")
        return self.get_session(session_id)

    def list_sessions(
        self,
        workspace_id: str | None = None,
        state: str | None = None,
    ) -> list[dict]:
        """List sessions, optionally filtered by workspace and/or state.

        Args:
            workspace_id: Filter by workspace. None returns all workspaces.
            state: Filter by state string. None returns all states.

        Returns:
            List of session dicts matching the filters.
        """
        from praxis.persistence.db_ops import db_list

        db_filter: dict = {}
        if workspace_id is not None:
            db_filter["workspace_id"] = workspace_id
        if state is not None:
            db_filter["state"] = state

        records = db_list("Session", filter=db_filter if db_filter else None)
        return [_session_from_db(r) for r in records]

    def update_constraints(self, session_id: str, new_constraints: dict) -> dict:
        """Update the constraint envelope for a session.

        Constraints can only be tightened, never loosened. This enforces the
        EATP principle that trust boundaries shrink monotonically.

        Args:
            session_id: The session to update.
            new_constraints: The proposed new constraint envelope.

        Returns:
            Updated session dict.

        Raises:
            KeyError: If session not found.
            SessionNotActiveError: If session is archived.
            ValueError: If the new constraints would loosen any dimension.
        """
        session = self.get_session(session_id)

        if session["state"] == SessionState.ARCHIVED.value:
            raise SessionNotActiveError(
                f"Session '{session_id}' is archived and cannot be modified. "
                f"Archived sessions are terminal — create a new session instead."
            )

        current = session["constraint_envelope"]
        if not _is_tightening(current, new_constraints):
            raise ValueError(
                "Cannot loosen constraints — constraints can only be tightened. "
                "The proposed constraint envelope expands at least one dimension "
                "beyond the current limits. Review the proposed values against "
                "the current constraint envelope and ensure all dimensions are "
                "tighter or equal."
            )

        from praxis.persistence.db_ops import db_update

        db_update("Session", session_id, {"constraint_envelope": new_constraints})

        logger.info("Updated constraints for session %s", session_id)
        return self.get_session(session_id)

    def advance_phase(self, session_id: str) -> dict:
        """Advance a session to the next phase in its phase list.

        If the current phase has ``approval_gate: true`` in the domain YAML,
        a held action is created via HeldActionManager instead of advancing
        directly. The phase advances only when the held action is approved.

        If the domain YAML specifies per-phase constraint overrides for the
        next phase, they are applied (tightening-only) during advancement.

        Args:
            session_id: The session to advance.

        Returns:
            Updated session dict.

        Raises:
            KeyError: If session not found.
            SessionNotActiveError: If session is archived.
            PhaseGateError: If the current phase has an approval gate.
            ValueError: If there are no more phases to advance to.
        """
        session = self.get_session(session_id)

        if session["state"] == SessionState.ARCHIVED.value:
            raise SessionNotActiveError(
                f"Session '{session_id}' is archived and cannot advance phases. "
                f"Archived sessions are terminal — create a new session instead."
            )

        phase_list = session.get("phase_list", [])
        current_phase = session.get("current_phase")

        if not phase_list:
            raise ValueError(
                f"Session '{session_id}' has no phase list. "
                f"Phase advancement requires a domain with defined phases."
            )

        if current_phase is None:
            raise ValueError(
                f"Session '{session_id}' has no current phase set. " f"Cannot determine next phase."
            )

        if current_phase not in phase_list:
            raise ValueError(
                f"Current phase '{current_phase}' is not in the session's "
                f"phase list: {phase_list}"
            )

        current_idx = phase_list.index(current_phase)
        if current_idx >= len(phase_list) - 1:
            raise ValueError(
                f"Session '{session_id}' is already in the last phase "
                f"'{current_phase}'. No more phases to advance to."
            )

        next_phase = phase_list[current_idx + 1]

        # M06-02: Check if current phase has an approval gate
        gate_required = self._phase_has_approval_gate(session["domain"], current_phase)
        if gate_required:
            from praxis.core.constraint import (
                ConstraintVerdict,
                GradientLevel,
                HeldActionManager,
            )

            held_mgr = HeldActionManager(use_db=True)
            verdict = ConstraintVerdict(
                level=GradientLevel.HELD,
                dimension="operational",
                utilization=0.0,
                reason=(
                    f"Phase '{current_phase}' has an approval gate. "
                    f"Human approval required before advancing to '{next_phase}'."
                ),
                action="advance_phase",
                resource=next_phase,
            )
            held = held_mgr.hold(
                session_id=session_id,
                action="advance_phase",
                resource=next_phase,
                verdict=verdict,
            )
            raise PhaseGateError(
                f"Phase '{current_phase}' requires approval before advancing "
                f"to '{next_phase}'. Held action created: {held.held_id}",
                held_action_id=held.held_id,
            )

        # M06-03: Apply per-phase constraint overrides if defined (tightening-only)
        self._apply_phase_constraints(session_id, session, next_phase)

        # Advance the phase
        from praxis.persistence.db_ops import db_update

        metadata = dict(session.get("metadata") or {})
        metadata["current_phase"] = next_phase
        full_meta = _build_session_metadata(session, metadata)
        full_meta["current_phase"] = next_phase

        db_update("Session", session_id, {"session_metadata": full_meta})

        logger.info(
            "Advanced session %s from phase '%s' to '%s'",
            session_id,
            current_phase,
            next_phase,
        )
        return self.get_session(session_id)

    def _verify_preconditions(
        self,
        session_id: str,
        key_manager,
        constraint_envelope: dict,
        domain: str,
        genesis_chain_entry: dict | None = None,
    ) -> None:
        """Verify session preconditions after creation (defense in depth).

        Runs three checks:
            1. Genesis record validity: if key_manager was provided, verify
               the genesis chain entry has expected structure.
            2. Constraint envelope completeness: all five CO dimensions must
               be present.
            3. Domain config loadable: if a domain was specified, verify
               the domain YAML can be loaded.

        This is a second enforcement layer. The primary enforcement happens
        during creation; this catches any inconsistencies that slip through.

        Args:
            session_id: The session identifier (for error messages).
            key_manager: The KeyManager instance (or None).
            constraint_envelope: The resolved constraint envelope.
            domain: The CO domain name.
            genesis_chain_entry: The genesis chain entry dict (or None).

        Raises:
            SessionPreconditionError: If any precondition fails.
        """
        from praxis.domains.schema import CONSTRAINT_DIMENSIONS

        failed_checks: list[str] = []

        # Check 1: Genesis record validity
        if key_manager is not None:
            if genesis_chain_entry is None:
                failed_checks.append(
                    "genesis_missing: key_manager provided but no genesis record created"
                )
            elif not isinstance(genesis_chain_entry, dict):
                failed_checks.append("genesis_invalid: genesis_chain_entry is not a dict")
            else:
                required_fields = ["payload", "content_hash", "signature", "signer_key_id"]
                missing = [f for f in required_fields if f not in genesis_chain_entry]
                if missing:
                    failed_checks.append(f"genesis_incomplete: missing fields {missing}")

        # Check 2: Constraint envelope completeness
        if not isinstance(constraint_envelope, dict):
            failed_checks.append("constraints_invalid: constraint_envelope is not a dict")
        else:
            missing_dims = [dim for dim in CONSTRAINT_DIMENSIONS if dim not in constraint_envelope]
            if missing_dims:
                failed_checks.append(f"constraints_incomplete: missing dimensions {missing_dims}")

        # Check 3: Domain config loadable (advisory — non-existent domains
        # are allowed because sessions can use hardcoded fallback templates)
        if domain:
            try:
                from praxis.domains.loader import DomainLoader

                loader = DomainLoader()
                loader.load_domain(domain)
            except Exception as exc:
                logger.warning(
                    "Session %s: domain '%s' could not be loaded: %s. "
                    "Session will operate without domain-specific features "
                    "(phases, anti-amnesia, rules).",
                    session_id,
                    domain,
                    exc,
                )

        if failed_checks:
            raise SessionPreconditionError(
                f"Session '{session_id}' failed {len(failed_checks)} "
                f"precondition check(s): {'; '.join(failed_checks)}",
                checks_failed=failed_checks,
            )

        logger.debug("Session %s passed all precondition checks", session_id)

    def _phase_has_approval_gate(self, domain: str, phase_name: str) -> bool:
        """Check if a phase has approval_gate: true in the domain YAML.

        Returns False if the domain cannot be loaded or the phase is not found.
        """
        try:
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            config = loader.load_domain(domain)
            for phase in config.phases:
                if phase["name"] == phase_name:
                    return bool(phase.get("approval_gate", False))
        except Exception as exc:
            logger.debug(
                "Could not check approval gate for phase '%s' in domain '%s': %s",
                phase_name,
                domain,
                exc,
            )
        return False

    def _apply_phase_constraints(self, session_id: str, session: dict, next_phase: str) -> None:
        """Apply per-phase constraint overrides from domain YAML (tightening-only).

        If the domain YAML specifies constraint_overrides for the next phase,
        they are merged with the current constraint envelope. Only tightening
        changes are accepted.
        """
        try:
            from praxis.domains.loader import DomainLoader

            loader = DomainLoader()
            config = loader.load_domain(session["domain"])
            for phase in config.phases:
                if phase["name"] == next_phase and "constraint_overrides" in phase:
                    overrides = phase["constraint_overrides"]
                    current_envelope = session.get("constraint_envelope", {})

                    # Build merged envelope: current values with overrides applied
                    merged = copy.deepcopy(current_envelope)
                    for dim, dim_overrides in overrides.items():
                        if dim in merged and isinstance(dim_overrides, dict):
                            merged[dim].update(dim_overrides)
                        elif isinstance(dim_overrides, dict):
                            merged[dim] = dim_overrides

                    # Only apply if the merged result is tighter
                    if _is_tightening(current_envelope, merged):
                        from praxis.persistence.db_ops import db_update

                        db_update(
                            "Session",
                            session_id,
                            {"constraint_envelope": merged},
                        )
                        logger.info(
                            "Applied phase constraint overrides for phase '%s' " "in session %s",
                            next_phase,
                            session_id,
                        )
                    else:
                        logger.warning(
                            "Phase '%s' constraint overrides would loosen "
                            "constraints — skipping (tightening-only invariant)",
                            next_phase,
                        )
                    break
        except Exception as exc:
            logger.debug(
                "Could not apply phase constraints for '%s': %s",
                next_phase,
                exc,
            )


# ---------------------------------------------------------------------------
# Internal metadata merge helper
# ---------------------------------------------------------------------------


def _build_session_metadata(
    session: dict,
    metadata: dict,
    *,
    updated_at: str | None = None,
) -> dict:
    """Build the full ``session_metadata`` dict for a DB update.

    Preserves the ``genesis_chain_entry`` and ``created_at`` that live
    inside ``session_metadata``, merges in new top-level metadata keys,
    and stamps ``updated_at`` with the provided (or freshly generated)
    ISO timestamp.
    """
    full = dict(metadata)
    genesis_chain_entry = session.get("genesis_chain_entry")
    if genesis_chain_entry is not None:
        full["genesis_chain_entry"] = genesis_chain_entry

    # Always carry forward created_at
    if session.get("created_at"):
        full["created_at"] = session["created_at"]

    # Always carry forward phase tracking
    if session.get("current_phase") is not None:
        full.setdefault("current_phase", session["current_phase"])
    if session.get("phase_list"):
        full.setdefault("phase_list", session["phase_list"])

    # Stamp updated_at
    full["updated_at"] = updated_at or _now_utc_iso()

    return full
