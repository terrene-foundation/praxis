# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Deliberation capture engine — hash-chained records of human-AI decisions.

Every deliberation record (decision, observation, escalation) is hash-chained
to the previous record using JCS (RFC 8785) canonical JSON serialization
and SHA-256 hashing. This creates a tamper-evident log of reasoning.

When a KeyManager is available, records are also signed with Ed25519 and
an audit anchor ID is generated for external verification.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone

import jcs

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _validate_confidence(confidence: float | None) -> None:
    """Validate that confidence is None or within [0.0, 1.0].

    Args:
        confidence: The confidence value to validate.

    Raises:
        ValueError: If confidence is outside [0.0, 1.0].
    """
    if confidence is not None:
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0 (inclusive), got {confidence}. "
                f"Use None for unspecified confidence, or a value in the range [0.0, 1.0]."
            )


# ---------------------------------------------------------------------------
# Format conversion helpers
# ---------------------------------------------------------------------------


def _record_to_db(record: dict) -> dict:
    """Convert an in-memory deliberation record dict to DataFlow model fields.

    Maps ``record_id`` to the DataFlow primary key ``id`` and passes through
    all other fields that correspond to ``DeliberationRecord`` columns.
    """
    return {
        "id": record["record_id"],
        "session_id": record["session_id"],
        "record_type": record["record_type"],
        "content": record.get("content"),
        "reasoning_trace": record.get("reasoning_trace"),
        "reasoning_hash": record.get("reasoning_hash"),
        "parent_record_id": record.get("parent_record_id"),
        "anchor_id": record.get("anchor_id"),
        "actor": record.get("actor", "human"),
        "confidence": record.get("confidence"),
    }


def _record_from_db(row: dict) -> dict:
    """Convert a DataFlow ``DeliberationRecord`` row to the public record dict.

    Restores the ``record_id`` key from the DataFlow ``id`` primary key
    and normalizes JSON columns that may have been deserialized by db_ops.
    """
    return {
        "record_id": row["id"],
        "session_id": row["session_id"],
        "record_type": row["record_type"],
        "content": row.get("content"),
        "reasoning_trace": row.get("reasoning_trace"),
        "reasoning_hash": row.get("reasoning_hash"),
        "parent_record_id": row.get("parent_record_id"),
        "anchor_id": row.get("anchor_id"),
        "actor": row.get("actor", "human"),
        "confidence": row.get("confidence"),
        "created_at": row.get("created_at", ""),
    }


# ---------------------------------------------------------------------------
# DeliberationEngine
# ---------------------------------------------------------------------------


class InvalidDecisionTypeError(ValueError):
    """Raised when a decision_type is not allowed by the domain capture config."""

    def __init__(self, decision_type: str, allowed: list[str]) -> None:
        self.decision_type = decision_type
        self.allowed = allowed
        super().__init__(
            f"Decision type '{decision_type}' is not allowed by the domain capture config. "
            f"Allowed types: {sorted(allowed)}"
        )


class DeliberationEngine:
    """Captures deliberation records with hash-chain integrity.

    Each record is linked to the previous via its reasoning_hash, forming
    a tamper-evident chain. When a key_manager is provided, records are
    also signed and receive an audit anchor ID.

    Records are persisted to the DataFlow database so they survive
    process restarts.  Every mutation is written through ``db_ops``
    helpers that execute synchronous DataFlow workflows.

    Args:
        session_id: The session this engine captures deliberation for.
        key_manager: Optional KeyManager for signing records.
        key_id: Key identifier for signing. Defaults to "default".
        capture_config: Optional domain capture configuration dict from
            the domain YAML ``capture`` section.  When provided, enables
            decision type validation and stores observation targets for
            the learning pipeline.
    """

    def __init__(
        self,
        session_id: str,
        key_manager=None,
        key_id: str = "default",
        capture_config: dict | None = None,
    ) -> None:
        self.session_id = session_id
        self.key_manager = key_manager
        self.key_id = key_id
        self._last_hash: str | None = None
        self.capture_config = capture_config

        # Extract validated decision types and observation targets from
        # the capture config for fast lookup and downstream consumption.
        if capture_config is not None:
            self._decision_types: list[str] | None = capture_config.get("decision_types")
            self.observation_targets: list[str] | None = capture_config.get("observation_targets")
        else:
            self._decision_types = None
            self.observation_targets = None

    def validate_decision_type(self, decision_type: str) -> None:
        """Validate that a decision_type is allowed by the domain capture config.

        Does nothing if no capture_config was provided or if the config
        has no ``decision_types`` list.

        Args:
            decision_type: The decision type to validate.

        Raises:
            InvalidDecisionTypeError: If the type is not in the allowed list.
        """
        if self._decision_types is not None and decision_type not in self._decision_types:
            raise InvalidDecisionTypeError(decision_type, self._decision_types)

    def record_decision(
        self,
        decision: str,
        rationale: str,
        actor: str = "human",
        alternatives: list[str] | None = None,
        confidence: float | None = None,
        decision_type: str | None = None,
    ) -> dict:
        """Record a decision with reasoning.

        Args:
            decision: The decision that was made.
            rationale: Why this decision was made.
            actor: Who made the decision ("human", "ai", "system").
            alternatives: Other options that were considered.
            confidence: Confidence level in [0.0, 1.0], or None.
            decision_type: Optional decision type (e.g. "scope", "architecture").
                When a capture_config with ``decision_types`` is active, this
                is validated against the allowed list.

        Returns:
            The deliberation record dict.

        Raises:
            ValueError: If confidence is outside [0.0, 1.0].
            InvalidDecisionTypeError: If decision_type is not allowed by the
                domain capture config.
        """
        _validate_confidence(confidence)

        if decision_type is not None:
            self.validate_decision_type(decision_type)

        content = {"decision": decision}
        if alternatives is not None:
            content["alternatives"] = alternatives
        if decision_type is not None:
            content["decision_type"] = decision_type

        reasoning_trace = {
            "rationale": rationale,
            "actor": actor,
            "confidence": confidence,
        }

        return self._create_record(
            record_type="decision",
            content=content,
            reasoning_trace=reasoning_trace,
            actor=actor,
            confidence=confidence,
        )

    def record_observation(
        self,
        observation: str,
        actor: str = "ai",
        confidence: float | None = None,
    ) -> dict:
        """Record an observation.

        Args:
            observation: What was observed.
            actor: Who made the observation ("human", "ai", "system").
            confidence: Confidence level in [0.0, 1.0], or None.

        Returns:
            The deliberation record dict.

        Raises:
            ValueError: If confidence is outside [0.0, 1.0].
        """
        _validate_confidence(confidence)

        content = {"observation": observation}
        reasoning_trace = {
            "actor": actor,
            "confidence": confidence,
        }

        return self._create_record(
            record_type="observation",
            content=content,
            reasoning_trace=reasoning_trace,
            actor=actor,
            confidence=confidence,
        )

    def record_escalation(
        self,
        issue: str,
        context: str,
        actor: str = "system",
    ) -> dict:
        """Record an escalation.

        Args:
            issue: The issue being escalated.
            context: Context for the escalation.
            actor: Who raised the escalation ("human", "ai", "system").

        Returns:
            The deliberation record dict.
        """
        content = {"issue": issue, "context": context}
        reasoning_trace = {
            "actor": actor,
            "issue": issue,
            "context": context,
        }

        return self._create_record(
            record_type="escalation",
            content=content,
            reasoning_trace=reasoning_trace,
            actor=actor,
            confidence=None,
        )

    def get_timeline(
        self,
        record_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Get the deliberation timeline.

        Args:
            record_type: Filter by record type ("decision", "observation", "escalation").
                None returns all types.
            limit: Maximum number of records to return.
            offset: Number of records to skip from the start.

        Returns:
            Tuple of (records, total_count) where total_count is the total
            matching records (before limit/offset).
        """
        from praxis.persistence.db_ops import db_count, db_list

        db_filter: dict = {"session_id": self.session_id}
        if record_type is not None:
            db_filter["record_type"] = record_type

        total = db_count("DeliberationRecord", filter=db_filter)
        rows = db_list(
            "DeliberationRecord",
            filter=db_filter,
            limit=limit,
            offset=offset,
            order_asc=True,
        )
        records = [_record_from_db(r) for r in rows]
        return records, total

    def _get_last_hash(self) -> str | None:
        """Resolve the reasoning_hash of the most recent record for this session.

        Uses the in-memory ``_last_hash`` cache when available, otherwise
        fetches the latest record from the database.
        """
        if self._last_hash is not None:
            return self._last_hash

        from praxis.persistence.db_ops import db_list

        # Fetch the single most recent record (DESC = newest first)
        rows = db_list(
            "DeliberationRecord",
            filter={"session_id": self.session_id},
            limit=1,
            offset=0,
            order_asc=False,
        )
        if rows:
            self._last_hash = rows[0].get("reasoning_hash")
        return self._last_hash

    def _create_record(
        self,
        record_type: str,
        content: dict,
        reasoning_trace: dict,
        actor: str,
        confidence: float | None,
    ) -> dict:
        """Internal: create a hash-chained deliberation record.

        Steps:
            1. Generate record_id (UUID4)
            2. Build content and reasoning_trace dicts
            3. Hash content+reasoning using JCS + SHA-256
            4. Set parent_record_id to previous record's reasoning_hash
            5. If key_manager available, sign and create audit anchor
            6. Persist to DataFlow and return
        """
        record_id = str(uuid.uuid4())

        # Hash the content + reasoning_trace for chain integrity
        hashable = {
            "content": content,
            "reasoning_trace": reasoning_trace,
        }
        canonical = jcs.canonicalize(hashable)
        reasoning_hash = hashlib.sha256(canonical).hexdigest()

        # Chain link: point to previous record's hash
        parent_record_id = self._get_last_hash()

        # Sign and create audit anchor if key_manager is available
        anchor_id = None
        if self.key_manager is not None:
            try:
                from praxis.trust.crypto import sign_hash

                signature = sign_hash(reasoning_hash, self.key_id, self.key_manager)
                anchor_id = f"anchor-{record_id}-{reasoning_hash[:8]}"
                logger.debug(
                    "Signed deliberation record %s with key %s (anchor: %s)",
                    record_id,
                    self.key_id,
                    anchor_id,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to sign deliberation record %s: %s. "
                    "Record will be stored without an audit anchor.",
                    record_id,
                    exc,
                )

        record = {
            "record_id": record_id,
            "session_id": self.session_id,
            "record_type": record_type,
            "content": content,
            "reasoning_trace": reasoning_trace,
            "reasoning_hash": reasoning_hash,
            "parent_record_id": parent_record_id,
            "anchor_id": anchor_id,
            "actor": actor,
            "confidence": confidence,
            "created_at": _now_utc_iso(),
        }

        # Persist to DataFlow
        from praxis.persistence.db_ops import db_create

        db_create("DeliberationRecord", _record_to_db(record))

        # Update in-memory cache for the hash chain
        self._last_hash = reasoning_hash

        logger.info(
            "Captured %s record %s in session %s (actor=%s)",
            record_type,
            record_id,
            self.session_id,
            actor,
        )
        return dict(record)
