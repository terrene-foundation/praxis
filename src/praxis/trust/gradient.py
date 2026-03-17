# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Verification gradient engine — classifies actions into four trust levels.

The gradient engine evaluates a proposed action against the session's active
constraint envelope across all five dimensions (Financial, Operational,
Temporal, Data Access, Communication). The evaluation is deterministic:
same inputs always produce the same output.

Gradient thresholds are normative CO specification values and MUST NOT be
made configurable:
    - AUTO_APPROVED: utilization < 70%
    - FLAGGED: utilization 70-89%
    - HELD: utilization 90-99% or explicit hold rules
    - BLOCKED: utilization >= 100% or explicitly forbidden
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class GradientLevel(str, Enum):
    """The four trust verification levels per CO specification.

    These are ordered by severity: AUTO_APPROVED < FLAGGED < HELD < BLOCKED.
    """

    AUTO_APPROVED = "auto_approved"
    FLAGGED = "flagged"
    HELD = "held"
    BLOCKED = "blocked"


# Severity ordering for worst-case aggregation
_SEVERITY_ORDER = [
    GradientLevel.AUTO_APPROVED,
    GradientLevel.FLAGGED,
    GradientLevel.HELD,
    GradientLevel.BLOCKED,
]


@dataclass
class GradientVerdict:
    """Result of evaluating an action against the constraint envelope.

    The verdict includes the most severe gradient level across all five
    dimensions, the determining dimension, the maximum utilization,
    and a human-readable reason.
    """

    level: GradientLevel
    dimension: str
    utilization: float
    reason: str
    action: str
    resource: str | None


def utilization_to_gradient_level(utilization: float) -> GradientLevel:
    """Map a utilization fraction to a gradient level using CO thresholds.

    This is the single source of truth for gradient threshold calculations.
    Both the trust layer (gradient engine) and core layer (constraint enforcer)
    MUST use this function.

    Thresholds (normative, not configurable):
        < 0.70 -> AUTO_APPROVED
        0.70 - 0.89 -> FLAGGED
        0.90 - 0.99 -> HELD
        >= 1.00 -> BLOCKED
    """
    if not math.isfinite(utilization):
        return GradientLevel.BLOCKED
    if utilization >= 1.0:
        return GradientLevel.BLOCKED
    if utilization >= 0.90:
        return GradientLevel.HELD
    if utilization >= 0.70:
        return GradientLevel.FLAGGED
    return GradientLevel.AUTO_APPROVED


# Backward-compatible alias — existing callers use this name
_utilization_to_level = utilization_to_gradient_level


def _evaluate_financial(constraints: dict, current_state: dict) -> tuple[GradientLevel, float, str]:
    """Evaluate the financial dimension.

    Returns:
        (level, utilization, reason)
    """
    financial = constraints.get("financial", {})
    state = current_state.get("financial", {})
    max_spend = financial.get("max_spend", 0)
    current_spend = state.get("current_spend", 0)

    if max_spend <= 0:
        return GradientLevel.AUTO_APPROVED, 0.0, "No financial limit set"

    utilization = current_spend / max_spend
    level = utilization_to_gradient_level(utilization)

    if level == GradientLevel.BLOCKED:
        reason = f"Financial limit exceeded: {current_spend}/{max_spend} ({utilization:.0%})"
    elif level == GradientLevel.HELD:
        reason = f"Financial limit approaching: {current_spend}/{max_spend} ({utilization:.0%})"
    elif level == GradientLevel.FLAGGED:
        reason = f"Financial utilization elevated: {current_spend}/{max_spend} ({utilization:.0%})"
    else:
        reason = f"Financial within limits: {current_spend}/{max_spend} ({utilization:.0%})"

    return level, utilization, reason


def _evaluate_operational(
    action: str, constraints: dict, current_state: dict
) -> tuple[GradientLevel, float, str]:
    """Evaluate the operational dimension.

    Checks:
        1. Whether the action is in allowed_actions (blocked if not)
        2. Rate limit utilization against max_actions_per_hour
    """
    operational = constraints.get("operational", {})
    state = current_state.get("operational", {})

    # Check if action is in allowed list
    allowed_actions = operational.get("allowed_actions", [])
    if allowed_actions and action not in allowed_actions:
        return (
            GradientLevel.BLOCKED,
            1.0,
            f"Action '{action}' not in allowed actions: {allowed_actions}",
        )

    # Check rate limit
    max_actions = operational.get("max_actions_per_hour", 0)
    actions_this_hour = state.get("actions_this_hour", 0)

    if max_actions <= 0:
        return GradientLevel.AUTO_APPROVED, 0.0, "No operational rate limit set"

    utilization = actions_this_hour / max_actions
    level = utilization_to_gradient_level(utilization)

    if level == GradientLevel.BLOCKED:
        reason = f"Operational rate limit exceeded: {actions_this_hour}/{max_actions}"
    elif level == GradientLevel.HELD:
        reason = f"Operational rate limit approaching: {actions_this_hour}/{max_actions}"
    elif level == GradientLevel.FLAGGED:
        reason = f"Operational utilization elevated: {actions_this_hour}/{max_actions}"
    else:
        reason = f"Operational within limits: {actions_this_hour}/{max_actions}"

    return level, utilization, reason


def _evaluate_temporal(constraints: dict, current_state: dict) -> tuple[GradientLevel, float, str]:
    """Evaluate the temporal dimension."""
    temporal = constraints.get("temporal", {})
    state = current_state.get("temporal", {})
    max_duration = temporal.get("max_duration_minutes", 0)
    elapsed = state.get("elapsed_minutes", 0)

    if max_duration <= 0:
        return GradientLevel.AUTO_APPROVED, 0.0, "No temporal limit set"

    utilization = elapsed / max_duration
    level = utilization_to_gradient_level(utilization)

    if level == GradientLevel.BLOCKED:
        reason = f"Session duration exceeded: {elapsed}/{max_duration} minutes"
    elif level == GradientLevel.HELD:
        reason = f"Session duration approaching limit: {elapsed}/{max_duration} minutes"
    elif level == GradientLevel.FLAGGED:
        reason = f"Session duration elevated: {elapsed}/{max_duration} minutes"
    else:
        reason = f"Session duration within limits: {elapsed}/{max_duration} minutes"

    return level, utilization, reason


def _evaluate_data_access(
    resource: str | None, constraints: dict
) -> tuple[GradientLevel, float, str]:
    """Evaluate the data access dimension.

    Checks whether the resource path is covered by any allowed_paths.
    A wildcard '*' allows all paths.
    """
    data_access = constraints.get("data_access", {})
    allowed_paths = data_access.get("allowed_paths", [])

    # No resource to check — allow
    if resource is None:
        return GradientLevel.AUTO_APPROVED, 0.0, "No resource specified"

    # Wildcard allows everything
    if "*" in allowed_paths:
        return GradientLevel.AUTO_APPROVED, 0.0, "Wildcard path access"

    # Check if resource starts with any allowed path
    for path in allowed_paths:
        if resource.startswith(path):
            return GradientLevel.AUTO_APPROVED, 0.0, f"Resource within allowed path: {path}"

    return (
        GradientLevel.BLOCKED,
        1.0,
        f"Resource '{resource}' not within allowed paths: {allowed_paths}",
    )


def _evaluate_communication(
    constraints: dict, current_state: dict
) -> tuple[GradientLevel, float, str]:
    """Evaluate the communication dimension.

    Checks whether the requested communication channel is allowed.
    """
    communication = constraints.get("communication", {})
    state = current_state.get("communication", {})
    allowed_channels = communication.get("allowed_channels", [])
    requested_channel = state.get("requested_channel", None)

    # No channel specified — allow
    if requested_channel is None:
        return GradientLevel.AUTO_APPROVED, 0.0, "No communication channel requested"

    # Check if requested channel is in allowed list
    if requested_channel in allowed_channels:
        return (
            GradientLevel.AUTO_APPROVED,
            0.0,
            f"Channel '{requested_channel}' is allowed",
        )

    return (
        GradientLevel.BLOCKED,
        1.0,
        f"Channel '{requested_channel}' not in allowed channels: {allowed_channels}",
    )


def evaluate_action(
    action: str,
    resource: str | None,
    constraints: dict,
    current_state: dict,
) -> GradientVerdict:
    """Evaluate an action against the 5-dimensional constraint envelope.

    This is a pure function — no side effects, no database calls, no external I/O.
    All state comes from the parameters. Same inputs always produce the same output.

    All five dimensions are always evaluated, even if one is already BLOCKED.
    The final verdict is the most severe (worst-case) across all dimensions.

    Args:
        action: The action being evaluated (e.g. "read_file", "deploy").
        resource: The resource being acted upon (e.g. file path).
        constraints: The 5-dimensional constraint envelope.
        current_state: Current utilization state.

    Returns:
        A GradientVerdict with the most severe level, determining dimension,
        max utilization, human-readable reason, and the action/resource.
    """
    # Evaluate all five dimensions — never short-circuit
    results: list[tuple[str, GradientLevel, float, str]] = []

    fin_level, fin_util, fin_reason = _evaluate_financial(constraints, current_state)
    results.append(("financial", fin_level, fin_util, fin_reason))

    ops_level, ops_util, ops_reason = _evaluate_operational(action, constraints, current_state)
    results.append(("operational", ops_level, ops_util, ops_reason))

    temp_level, temp_util, temp_reason = _evaluate_temporal(constraints, current_state)
    results.append(("temporal", temp_level, temp_util, temp_reason))

    data_level, data_util, data_reason = _evaluate_data_access(resource, constraints)
    results.append(("data_access", data_level, data_util, data_reason))

    comm_level, comm_util, comm_reason = _evaluate_communication(constraints, current_state)
    results.append(("communication", comm_level, comm_util, comm_reason))

    # Find the most severe verdict (worst-case aggregation)
    worst_dim = "financial"
    worst_level = GradientLevel.AUTO_APPROVED
    worst_reason = ""
    max_utilization = 0.0

    for dim_name, dim_level, dim_util, dim_reason in results:
        severity = _SEVERITY_ORDER.index(dim_level)
        worst_severity = _SEVERITY_ORDER.index(worst_level)

        if severity > worst_severity:
            worst_level = dim_level
            worst_dim = dim_name
            worst_reason = dim_reason

        if dim_util > max_utilization:
            max_utilization = dim_util

    # If worst reason is empty (all auto_approved), provide a summary
    if not worst_reason:
        worst_reason = "All dimensions within limits"

    return GradientVerdict(
        level=worst_level,
        dimension=worst_dim,
        utilization=max_utilization,
        reason=worst_reason,
        action=action,
        resource=resource,
    )
