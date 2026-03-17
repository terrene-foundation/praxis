# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Five-dimensional constraint enforcer with gradient verdicts.

Evaluates actions against the CARE constraint envelope across all five
dimensions: Financial, Operational, Temporal, Data Access, Communication.

Returns the MOST RESTRICTIVE verdict across all dimensions using the
verification gradient: AUTO_APPROVED -> FLAGGED -> HELD -> BLOCKED.

Gradient thresholds (utilization-based):
    - AUTO_APPROVED: utilization < 70%
    - FLAGGED: utilization 70-89%
    - HELD: utilization >= 90%
    - BLOCKED: action explicitly forbidden OR would exceed hard limits
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from praxis.trust.gradient import GradientLevel, utilization_to_gradient_level

logger = logging.getLogger(__name__)


# Ordering for comparison: higher index = more restrictive
_GRADIENT_ORDER = {
    GradientLevel.AUTO_APPROVED: 0,
    GradientLevel.FLAGGED: 1,
    GradientLevel.HELD: 2,
    GradientLevel.BLOCKED: 3,
}

CONSTRAINT_DIMENSIONS = [
    "financial",
    "operational",
    "temporal",
    "data_access",
    "communication",
]


# ---------------------------------------------------------------------------
# Verdict dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConstraintVerdict:
    """Result of evaluating an action against a constraint dimension.

    Attributes:
        level: The gradient level (auto_approved, flagged, held, blocked).
        dimension: Which constraint dimension produced this verdict.
        utilization: Current utilization ratio (0.0-1.0).
        reason: Human-readable reason for the verdict.
        action: The action that was evaluated.
        resource: The resource the action targets (if applicable).
    """

    level: GradientLevel
    dimension: str
    utilization: float
    reason: str
    action: str
    resource: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# Backward-compatible alias — existing callers (including tests) use this name.
# The single source of truth is praxis.trust.gradient.utilization_to_gradient_level.
_gradient_for_utilization = utilization_to_gradient_level


def _more_restrictive(a: ConstraintVerdict, b: ConstraintVerdict) -> ConstraintVerdict:
    """Return the more restrictive of two verdicts."""
    if _GRADIENT_ORDER[a.level] >= _GRADIENT_ORDER[b.level]:
        return a
    return b


# ---------------------------------------------------------------------------
# ConstraintEnforcer
# ---------------------------------------------------------------------------


class ConstraintEnforcer:
    """Evaluates actions against the 5-dimensional constraint envelope.

    Each evaluation checks all five dimensions and returns the MOST
    RESTRICTIVE verdict. This ensures that any single dimension violation
    is sufficient to block or hold an action.

    Constraint events are persisted to the DataFlow database when a
    ``session_id`` is provided.  When ``session_id`` is empty or None
    (e.g. in unit tests that don't need persistence), events are
    accumulated in an in-memory list for backward compatibility.

    Args:
        constraints: The 5-dimensional constraint envelope dict.
        session_id: Optional session identifier for DataFlow persistence.
            Defaults to "" (in-memory only).
    """

    def __init__(
        self,
        constraints: dict,
        session_id: str = "",
        session_start_time: datetime | None = None,
    ) -> None:
        self.constraints = constraints
        self.session_id = session_id or ""
        self._events: list[dict] = []

        # M05-01: Temporal auto-tracking — wall-clock elapsed time.
        # If the constraint envelope carries an ``elapsed_minutes`` field,
        # back-date session_start_time so that wall-clock elapsed matches.
        # This preserves backward compatibility with existing code and tests.
        if session_start_time is not None:
            self.session_start_time = session_start_time
        else:
            temp = constraints.get("temporal", {})
            pre_elapsed = temp.get("elapsed_minutes", 0)
            import math as _math
            from datetime import timedelta

            if isinstance(pre_elapsed, (int, float)) and not _math.isfinite(pre_elapsed):
                # NaN or Inf elapsed — treat as extreme overrun
                self.session_start_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
            elif pre_elapsed and pre_elapsed > 0:
                try:
                    self.session_start_time = datetime.now(timezone.utc) - timedelta(
                        minutes=pre_elapsed
                    )
                except (OverflowError, ValueError):
                    # Extreme values (e.g. 1e18 minutes) overflow timedelta.
                    self.session_start_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
            else:
                self.session_start_time = datetime.now(timezone.utc)

        # M05-02: Financial spend tracking — running accumulator.
        # Initialize from the envelope's current_spend (if present) for
        # backward compatibility with constraint templates that pre-seed it.
        fin = constraints.get("financial", {})
        try:
            self._accumulated_spend: float = float(fin.get("current_spend", 0.0))
        except (ValueError, TypeError):
            self._accumulated_spend = 0.0

    def evaluate(
        self,
        action: str,
        resource: str | None = None,
        context: dict | None = None,
    ) -> ConstraintVerdict:
        """Evaluate an action against ALL 5 constraint dimensions.

        Returns the MOST RESTRICTIVE verdict across all dimensions.

        Args:
            action: The action being evaluated (e.g., "read", "write", "delete").
            resource: Optional resource the action targets (path, channel, etc.).
            context: Optional context dict (e.g., {"cost": 5.0} for financial).

        Returns:
            The most restrictive ConstraintVerdict across all dimensions.
        """
        verdicts = [
            self._evaluate_financial(action, resource, context),
            self._evaluate_operational(action, resource, context),
            self._evaluate_temporal(action, resource, context),
            self._evaluate_data_access(action, resource, context),
            self._evaluate_communication(action, resource, context),
        ]

        # Find the most restrictive verdict
        most_restrictive = verdicts[0]
        for v in verdicts[1:]:
            most_restrictive = _more_restrictive(most_restrictive, v)

        # Persist the evaluation event
        event = {
            "action": action,
            "resource": resource,
            "verdict": most_restrictive.level.value,
            "dimension": most_restrictive.dimension,
            "utilization": most_restrictive.utilization,
            "reason": most_restrictive.reason,
            "evaluated_at": _now_utc_iso(),
        }

        if self.session_id:
            # Write to DataFlow persistence
            from praxis.persistence.db_ops import db_create

            db_create(
                "ConstraintEvent",
                {
                    "id": str(uuid.uuid4()),
                    "session_id": self.session_id,
                    "action": action,
                    "resource": resource,
                    "dimension": most_restrictive.dimension,
                    "gradient_result": most_restrictive.level.value,
                    "utilization": most_restrictive.utilization,
                },
            )
        else:
            # In-memory fallback (no session_id — e.g. tests without DB)
            self._events.append(event)

        logger.info(
            "Constraint evaluation: action='%s' resource='%s' -> %s "
            "(dimension=%s, utilization=%.2f)",
            action,
            resource,
            most_restrictive.level.value,
            most_restrictive.dimension,
            most_restrictive.utilization,
        )

        return most_restrictive

    def record_spend(self, amount: float) -> None:
        """Record financial spend, accumulating a running total.

        Args:
            amount: The amount to add to the accumulated spend.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError(
                f"Spend amount must be non-negative, got {amount}. "
                f"Use record_spend(0) if no cost applies."
            )
        self._accumulated_spend += amount

        # Persist to DB when session_id is set
        if self.session_id:
            try:
                from praxis.persistence.db_ops import db_update

                db_update(
                    "Session",
                    self.session_id,
                    {"session_metadata": {"accumulated_spend": self._accumulated_spend}},
                )
            except Exception:
                logger.debug(
                    "Could not persist accumulated_spend for session %s",
                    self.session_id,
                )

        logger.info(
            "Recorded spend %.2f for session %s (total: %.2f)",
            amount,
            self.session_id or "(in-memory)",
            self._accumulated_spend,
        )

    def _evaluate_financial(
        self,
        action: str,
        resource: str | None,
        context: dict | None,
    ) -> ConstraintVerdict:
        """Evaluate the financial dimension.

        Uses the running _accumulated_spend instead of a static current_spend.
        If context includes a "cost", checks whether the action would exceed
        the limit.
        """
        fin = self.constraints.get("financial", {})
        max_spend = fin.get("max_spend", 0)
        current_spend = self._accumulated_spend

        # Check if this action would push over the limit
        action_cost = 0.0
        if context and "cost" in context:
            action_cost = float(context["cost"])

        projected_spend = current_spend + action_cost

        if max_spend > 0:
            utilization = projected_spend / max_spend
        else:
            utilization = 0.0

        # Would exceed hard limit
        if projected_spend > max_spend and max_spend > 0:
            return ConstraintVerdict(
                level=GradientLevel.BLOCKED,
                dimension="financial",
                utilization=utilization,
                reason=(
                    f"Action would exceed financial limit: "
                    f"projected ${projected_spend:.2f} > max ${max_spend:.2f}"
                ),
                action=action,
                resource=resource,
            )

        level = utilization_to_gradient_level(utilization)
        return ConstraintVerdict(
            level=level,
            dimension="financial",
            utilization=utilization,
            reason=(
                f"Financial utilization: "
                f"${current_spend:.2f}/${max_spend:.2f} ({utilization:.0%})"
            ),
            action=action,
            resource=resource,
        )

    def _evaluate_operational(
        self,
        action: str,
        resource: str | None,
        context: dict | None,
    ) -> ConstraintVerdict:
        """Evaluate the operational dimension.

        Checks if the action is in blocked_actions or not in allowed_actions.
        """
        ops = self.constraints.get("operational", {})
        blocked_actions = ops.get("blocked_actions", [])
        allowed_actions = ops.get("allowed_actions", [])

        # Explicitly blocked
        if action in blocked_actions:
            return ConstraintVerdict(
                level=GradientLevel.BLOCKED,
                dimension="operational",
                utilization=1.0,
                reason=f"Action '{action}' is explicitly blocked by operational constraints",
                action=action,
                resource=resource,
            )

        # Not in allowed list (wildcard "*" permits all actions)
        if allowed_actions and "*" not in allowed_actions and action not in allowed_actions:
            return ConstraintVerdict(
                level=GradientLevel.BLOCKED,
                dimension="operational",
                utilization=1.0,
                reason=(
                    f"Action '{action}' is not in allowed actions: {allowed_actions}. "
                    f"Only explicitly allowed actions are permitted."
                ),
                action=action,
                resource=resource,
            )

        return ConstraintVerdict(
            level=GradientLevel.AUTO_APPROVED,
            dimension="operational",
            utilization=0.0,
            reason=f"Action '{action}' is allowed by operational constraints",
            action=action,
            resource=resource,
        )

    def _evaluate_temporal(
        self,
        action: str,
        resource: str | None,
        context: dict | None,
    ) -> ConstraintVerdict:
        """Evaluate the temporal dimension.

        Computes elapsed time from wall clock (session_start_time) instead
        of reading a static value. This means temporal constraints actually
        count down in real time.
        """
        temp = self.constraints.get("temporal", {})
        max_duration = temp.get("max_duration_minutes", 0)

        # M05-01: Wall-clock elapsed time
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - self.session_start_time).total_seconds()
        elapsed = elapsed_seconds / 60.0

        if max_duration > 0:
            utilization = elapsed / max_duration
        else:
            utilization = 0.0

        level = utilization_to_gradient_level(utilization)
        return ConstraintVerdict(
            level=level,
            dimension="temporal",
            utilization=utilization,
            reason=(
                f"Temporal utilization: "
                f"{elapsed:.1f}/{max_duration} minutes ({utilization:.0%})"
            ),
            action=action,
            resource=resource,
        )

    def _evaluate_data_access(
        self,
        action: str,
        resource: str | None,
        context: dict | None,
    ) -> ConstraintVerdict:
        """Evaluate the data access dimension.

        Checks if the resource path is in blocked_paths or not in allowed_paths.
        If no resource is specified, auto-approve (no path to check).
        """
        da = self.constraints.get("data_access", {})
        blocked_paths = da.get("blocked_paths", [])
        allowed_paths = da.get("allowed_paths", [])

        # No resource specified or resource is not a path (channel names etc.)
        # Only file paths (starting with /) are evaluated for data access
        if resource is None or not resource.startswith("/"):
            return ConstraintVerdict(
                level=GradientLevel.AUTO_APPROVED,
                dimension="data_access",
                utilization=0.0,
                reason="No resource path specified — data access check skipped",
                action=action,
                resource=resource,
            )

        # Check blocked paths first
        for blocked in blocked_paths:
            if resource.startswith(blocked):
                return ConstraintVerdict(
                    level=GradientLevel.BLOCKED,
                    dimension="data_access",
                    utilization=1.0,
                    reason=f"Resource '{resource}' matches blocked path '{blocked}'",
                    action=action,
                    resource=resource,
                )

        # Check allowed paths (wildcard "*" permits all paths)
        if allowed_paths and "*" not in allowed_paths:
            path_allowed = any(resource.startswith(ap) for ap in allowed_paths)
            if not path_allowed:
                return ConstraintVerdict(
                    level=GradientLevel.BLOCKED,
                    dimension="data_access",
                    utilization=1.0,
                    reason=(
                        f"Resource '{resource}' is not within any allowed path: "
                        f"{allowed_paths}. Only resources under explicitly "
                        f"allowed paths are accessible."
                    ),
                    action=action,
                    resource=resource,
                )

        return ConstraintVerdict(
            level=GradientLevel.AUTO_APPROVED,
            dimension="data_access",
            utilization=0.0,
            reason=f"Resource '{resource}' is within allowed paths",
            action=action,
            resource=resource,
        )

    def _evaluate_communication(
        self,
        action: str,
        resource: str | None,
        context: dict | None,
    ) -> ConstraintVerdict:
        """Evaluate the communication dimension.

        Uses the resource field as the channel name. Checks if the channel
        is blocked or not in the allowed list.
        """
        comm = self.constraints.get("communication", {})
        blocked_channels = comm.get("blocked_channels", [])
        allowed_channels = comm.get("allowed_channels", [])

        # No channel specified or resource is a file path (not a channel)
        # File paths are handled by data_access, not communication
        if resource is None or resource.startswith("/"):
            return ConstraintVerdict(
                level=GradientLevel.AUTO_APPROVED,
                dimension="communication",
                utilization=0.0,
                reason="No communication channel specified — check skipped",
                action=action,
                resource=resource,
            )

        # Check blocked channels
        if resource in blocked_channels:
            return ConstraintVerdict(
                level=GradientLevel.BLOCKED,
                dimension="communication",
                utilization=1.0,
                reason=f"Channel '{resource}' is explicitly blocked",
                action=action,
                resource=resource,
            )

        # Check allowed channels (wildcard "*" permits all channels)
        if allowed_channels and "*" not in allowed_channels and resource not in allowed_channels:
            return ConstraintVerdict(
                level=GradientLevel.BLOCKED,
                dimension="communication",
                utilization=1.0,
                reason=(
                    f"Channel '{resource}' is not in allowed channels: "
                    f"{allowed_channels}. Only explicitly allowed channels "
                    f"are permitted."
                ),
                action=action,
                resource=resource,
            )

        return ConstraintVerdict(
            level=GradientLevel.AUTO_APPROVED,
            dimension="communication",
            utilization=0.0,
            reason=f"Channel '{resource}' is allowed",
            action=action,
            resource=resource,
        )

    def update_utilization(self, dimension: str, value: float) -> None:
        """Update the utilization value for a constraint dimension.

        Args:
            dimension: The dimension to update.
            value: The new utilization value.

        Raises:
            ValueError: If dimension is not recognized.
        """
        if dimension not in CONSTRAINT_DIMENSIONS:
            raise ValueError(
                f"Unknown dimension '{dimension}'. " f"Valid dimensions: {CONSTRAINT_DIMENSIONS}"
            )

        dim_config = self.constraints.get(dimension, {})

        if dimension == "financial":
            dim_config["current_spend"] = value
        elif dimension == "temporal":
            dim_config["elapsed_minutes"] = value
        else:
            logger.info(
                "update_utilization called for dimension '%s' with value %s "
                "(no standard utilization field — storing as 'current_value')",
                dimension,
                value,
            )
            dim_config["current_value"] = value

        self.constraints[dimension] = dim_config

    def get_status(self) -> dict:
        """Get current constraint status across all dimensions.

        Returns:
            Dict mapping each dimension to its current status including
            utilization ratio and gradient level.
        """
        status = {}

        # Financial — uses runtime accumulated spend
        fin = self.constraints.get("financial", {})
        max_spend = fin.get("max_spend", 0)
        current_spend = self._accumulated_spend
        fin_util = current_spend / max_spend if max_spend > 0 else 0.0
        status["financial"] = {
            "max_spend": max_spend,
            "current_spend": current_spend,
            "utilization": fin_util,
            "level": utilization_to_gradient_level(fin_util).value,
        }

        # Operational
        ops = self.constraints.get("operational", {})
        status["operational"] = {
            "allowed_actions": ops.get("allowed_actions", []),
            "blocked_actions": ops.get("blocked_actions", []),
            "utilization": 0.0,
            "level": GradientLevel.AUTO_APPROVED.value,
        }

        # Temporal — uses wall-clock elapsed time
        temp = self.constraints.get("temporal", {})
        max_dur = temp.get("max_duration_minutes", 0)
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - self.session_start_time).total_seconds()
        elapsed = elapsed_seconds / 60.0
        temp_util = elapsed / max_dur if max_dur > 0 else 0.0
        status["temporal"] = {
            "max_duration_minutes": max_dur,
            "elapsed_minutes": round(elapsed, 1),
            "utilization": temp_util,
            "level": utilization_to_gradient_level(temp_util).value,
        }

        # Data access
        da = self.constraints.get("data_access", {})
        status["data_access"] = {
            "allowed_paths": da.get("allowed_paths", []),
            "blocked_paths": da.get("blocked_paths", []),
            "utilization": 0.0,
            "level": GradientLevel.AUTO_APPROVED.value,
        }

        # Communication
        comm = self.constraints.get("communication", {})
        status["communication"] = {
            "allowed_channels": comm.get("allowed_channels", []),
            "blocked_channels": comm.get("blocked_channels", []),
            "utilization": 0.0,
            "level": GradientLevel.AUTO_APPROVED.value,
        }

        return status

    def get_events(self) -> list[dict]:
        """Return all constraint evaluation events for this enforcer.

        When ``session_id`` is set, reads from the DataFlow database.
        Otherwise falls back to the in-memory ``_events`` list.

        Returns:
            List of constraint event dicts.
        """
        if self.session_id:
            from praxis.persistence.db_ops import db_list

            records = db_list(
                "ConstraintEvent",
                filter={"session_id": self.session_id},
            )
            # Normalize DB records to the same shape as the in-memory dicts
            events = []
            for r in records:
                events.append(
                    {
                        "action": r.get("action", ""),
                        "resource": r.get("resource"),
                        "verdict": r.get("gradient_result", "auto_approved"),
                        "dimension": r.get("dimension", "operational"),
                        "utilization": r.get("utilization", 0.0),
                        "evaluated_at": r.get("created_at", ""),
                    }
                )
            return events

        return list(self._events)


# ---------------------------------------------------------------------------
# HeldAction and HeldActionManager
# ---------------------------------------------------------------------------


@dataclass
class HeldAction:
    """An action that has been held for human approval.

    Attributes:
        held_id: Unique identifier for this held action.
        session_id: The session this held action belongs to.
        action: The action that was held.
        resource: Optional resource the action targets.
        dimension: The constraint dimension that triggered the hold.
        verdict: The ConstraintVerdict that caused the hold.
        created_at: ISO 8601 timestamp of when the hold was created.
        resolved: Whether the hold has been resolved.
        resolved_by: Who resolved the hold (if resolved).
        resolution: "approved" or "denied" (if resolved).
        resolved_at: ISO 8601 timestamp of resolution (if resolved).
    """

    held_id: str
    session_id: str
    action: str
    resource: str | None
    dimension: str
    verdict: ConstraintVerdict
    created_at: str
    resolved: bool = False
    resolved_by: str | None = None
    resolution: str | None = None
    resolved_at: str | None = None


# ---------------------------------------------------------------------------
# Conversion helpers: HeldAction dataclass <-> DB record
# ---------------------------------------------------------------------------


def _verdict_to_payload(verdict: ConstraintVerdict) -> dict:
    """Serialize a ConstraintVerdict to a dict suitable for DB storage."""
    return {
        "level": verdict.level.value,
        "dimension": verdict.dimension,
        "utilization": verdict.utilization,
        "reason": verdict.reason,
        "action": verdict.action,
        "resource": verdict.resource,
    }


def _verdict_from_payload(payload: dict | None) -> ConstraintVerdict:
    """Reconstruct a ConstraintVerdict from a DB verdict_payload dict."""
    if payload is None:
        # Defensive fallback — should not happen in normal operation
        return ConstraintVerdict(
            level=GradientLevel.HELD,
            dimension="operational",
            utilization=0.0,
            reason="(verdict payload missing)",
            action="unknown",
        )
    return ConstraintVerdict(
        level=GradientLevel(payload["level"]),
        dimension=payload["dimension"],
        utilization=payload.get("utilization", 0.0),
        reason=payload.get("reason", ""),
        action=payload.get("action", "unknown"),
        resource=payload.get("resource"),
    )


def _held_to_db(held: HeldAction) -> dict:
    """Convert a HeldAction dataclass instance to a dict for DB insertion."""
    return {
        "id": held.held_id,
        "session_id": held.session_id,
        "action": held.action,
        "resource": held.resource,
        "dimension": held.dimension,
        "verdict_payload": _verdict_to_payload(held.verdict),
        "resolved": held.resolved,
        "resolved_by": held.resolved_by,
        "resolution": held.resolution,
        "resolved_at": held.resolved_at,
    }


def _held_from_db(record: dict) -> HeldAction:
    """Convert a DB record dict back to a HeldAction dataclass instance."""
    # SQLite stores booleans as 0/1 integers — normalize to bool
    resolved_raw = record.get("resolved", False)
    resolved = bool(resolved_raw) if resolved_raw is not None else False

    return HeldAction(
        held_id=record["id"],
        session_id=record["session_id"],
        action=record["action"],
        resource=record.get("resource"),
        dimension=record.get("dimension", "operational"),
        verdict=_verdict_from_payload(record.get("verdict_payload")),
        created_at=record.get("created_at", ""),
        resolved=resolved,
        resolved_by=record.get("resolved_by"),
        resolution=record.get("resolution"),
        resolved_at=record.get("resolved_at"),
    )


class HeldActionManager:
    """Manages held actions that require human approval.

    Held actions are created when a constraint evaluation returns HELD.
    A supervisor must approve or deny the action before it can proceed.

    When ``use_db`` is True (the default), held actions are persisted to
    the DataFlow database via the ``HeldAction`` persistence model.
    When ``use_db`` is False (e.g. in tests without a database), held
    actions are stored in an in-memory dict for backward compatibility.
    """

    def __init__(self, *, use_db: bool = True) -> None:
        self._use_db = use_db
        self._held: dict[str, HeldAction] = {}

    def hold(
        self,
        session_id: str,
        action: str,
        resource: str | None,
        verdict: ConstraintVerdict,
    ) -> HeldAction:
        """Create a held action requiring human approval.

        Args:
            session_id: The session this held action belongs to.
            action: The action being held.
            resource: Optional resource the action targets.
            verdict: The constraint verdict that triggered the hold.

        Returns:
            The created HeldAction.
        """
        held_id = str(uuid.uuid4())
        held = HeldAction(
            held_id=held_id,
            session_id=session_id,
            action=action,
            resource=resource,
            dimension=verdict.dimension,
            verdict=verdict,
            created_at=_now_utc_iso(),
        )

        if self._use_db:
            from praxis.persistence.db_ops import db_create

            db_create("HeldAction", _held_to_db(held))
        else:
            self._held[held_id] = held

        logger.info(
            "Held action %s in session %s: action='%s' dimension='%s' reason='%s'",
            held_id,
            session_id,
            action,
            verdict.dimension,
            verdict.reason,
        )
        return held

    def approve(self, held_id: str, approved_by: str) -> HeldAction:
        """Approve a held action.

        Args:
            held_id: The held action to approve.
            approved_by: Identity of the approver.

        Returns:
            The updated HeldAction.

        Raises:
            KeyError: If held_id not found.
            ValueError: If the action is already resolved.
        """
        held = self.get_held(held_id)
        if held.resolved:
            raise ValueError(
                f"Held action '{held_id}' is already resolved as '{held.resolution}' "
                f"by '{held.resolved_by}'. Cannot approve an already resolved action."
            )

        resolved_at = _now_utc_iso()

        if self._use_db:
            from praxis.persistence.db_ops import db_update

            db_update(
                "HeldAction",
                held_id,
                {
                    "resolved": True,
                    "resolution": "approved",
                    "resolved_by": approved_by,
                    "resolved_at": resolved_at,
                },
            )

        # Update the in-memory object to return consistent state
        held.resolved = True
        held.resolution = "approved"
        held.resolved_by = approved_by
        held.resolved_at = resolved_at

        if not self._use_db:
            self._held[held_id] = held

        logger.info("Approved held action %s by %s", held_id, approved_by)
        return held

    def deny(self, held_id: str, denied_by: str) -> HeldAction:
        """Deny a held action.

        Args:
            held_id: The held action to deny.
            denied_by: Identity of the denier.

        Returns:
            The updated HeldAction.

        Raises:
            KeyError: If held_id not found.
            ValueError: If the action is already resolved.
        """
        held = self.get_held(held_id)
        if held.resolved:
            raise ValueError(
                f"Held action '{held_id}' is already resolved as '{held.resolution}' "
                f"by '{held.resolved_by}'. Cannot deny an already resolved action."
            )

        resolved_at = _now_utc_iso()

        if self._use_db:
            from praxis.persistence.db_ops import db_update

            db_update(
                "HeldAction",
                held_id,
                {
                    "resolved": True,
                    "resolution": "denied",
                    "resolved_by": denied_by,
                    "resolved_at": resolved_at,
                },
            )

        # Update the in-memory object to return consistent state
        held.resolved = True
        held.resolution = "denied"
        held.resolved_by = denied_by
        held.resolved_at = resolved_at

        if not self._use_db:
            self._held[held_id] = held

        logger.info("Denied held action %s by %s", held_id, denied_by)
        return held

    def get_pending(self, session_id: str | None = None) -> list[HeldAction]:
        """Get pending (unresolved) held actions.

        Args:
            session_id: Optional filter by session. None returns all.

        Returns:
            List of unresolved HeldAction instances.
        """
        if self._use_db:
            from praxis.persistence.db_ops import db_list

            db_filter: dict = {"resolved": False}
            if session_id is not None:
                db_filter["session_id"] = session_id
            records = db_list("HeldAction", filter=db_filter, limit=1000)
            return [_held_from_db(r) for r in records]

        # In-memory fallback
        results = []
        for held in self._held.values():
            if held.resolved:
                continue
            if session_id is not None and held.session_id != session_id:
                continue
            results.append(held)
        return results

    def get_held(self, held_id: str) -> HeldAction:
        """Get a specific held action by ID.

        Args:
            held_id: The held action identifier.

        Returns:
            The HeldAction instance.

        Raises:
            KeyError: If not found.
        """
        if self._use_db:
            from praxis.persistence.db_ops import db_read

            record = db_read("HeldAction", held_id)
            if record is None:
                raise KeyError(
                    f"Held action '{held_id}' not found. " f"Verify the held_id is correct."
                )
            return _held_from_db(record)

        # In-memory fallback
        if held_id not in self._held:
            raise KeyError(f"Held action '{held_id}' not found. " f"Verify the held_id is correct.")
        return self._held[held_id]
