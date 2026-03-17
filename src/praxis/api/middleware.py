# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Constraint enforcement middleware for Praxis API routes.

Evaluates the session's constraint envelope before action-producing handlers
execute. Returns appropriate HTTP responses based on the gradient verdict:

    - AUTO_APPROVED / FLAGGED: allow the request through
    - HELD: return HTTP 202 with the held_action_id
    - BLOCKED: return HTTP 403 with an explanation

Usage:
    from praxis.api.middleware import enforce_constraints

    # Wrap a handler call:
    result = enforce_constraints(
        enforcer=enforcer,
        held_manager=held_manager,
        session_id="sess-123",
        action="write",
        resource="/src/main.py",
        context={"cost": 5.0},
    )
    if result is not None:
        return result  # Constraint blocked or held the action
    # ... proceed with handler logic
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def enforce_constraints(
    enforcer,
    held_manager,
    session_id: str,
    action: str,
    resource: str | None = None,
    context: dict | None = None,
) -> dict[str, Any] | None:
    """Evaluate constraints and return an error response if the action is blocked or held.

    This function is designed to be called before action-producing handlers.
    If the action passes constraint checks (AUTO_APPROVED or FLAGGED), it
    returns None, allowing the handler to proceed. If the action is BLOCKED
    or HELD, it returns an appropriate response dict that the caller should
    return directly as the HTTP response.

    Args:
        enforcer: ConstraintEnforcer instance for the session.
        held_manager: HeldActionManager instance.
        session_id: The session identifier.
        action: The action being attempted (e.g., "write", "delete", "deploy").
        resource: Optional resource the action targets.
        context: Optional context dict (e.g., {"cost": 5.0}).

    Returns:
        None if the action is allowed (AUTO_APPROVED or FLAGGED).
        A dict with error/held information if BLOCKED (403) or HELD (202).
    """
    from praxis.core.constraint import GradientLevel

    try:
        verdict = enforcer.evaluate(
            action=action,
            resource=resource,
            context=context,
        )
    except Exception as exc:
        logger.error(
            "Constraint evaluation failed for action '%s' on resource '%s': %s",
            action,
            resource,
            exc,
        )
        return {
            "error": {
                "type": "internal_error",
                "message": "Constraint evaluation failed. Check server logs.",
            },
            "status_code": 500,
        }

    if verdict.level == GradientLevel.BLOCKED:
        logger.info(
            "Middleware: BLOCKED action='%s' resource='%s' reason='%s'",
            action,
            resource,
            verdict.reason,
        )
        return {
            "error": {
                "type": "forbidden",
                "message": f"Action blocked by {verdict.dimension} constraint: {verdict.reason}",
            },
            "status_code": 403,
            "verdict": {
                "level": verdict.level.value,
                "dimension": verdict.dimension,
                "utilization": verdict.utilization,
                "reason": verdict.reason,
            },
        }

    if verdict.level == GradientLevel.HELD:
        held = held_manager.hold(
            session_id=session_id,
            action=action,
            resource=resource,
            verdict=verdict,
        )
        logger.info(
            "Middleware: HELD action='%s' resource='%s' held_id='%s'",
            action,
            resource,
            held.held_id,
        )
        return {
            "held_action_id": held.held_id,
            "message": (
                f"Action held for human approval due to "
                f"{verdict.dimension} constraint: {verdict.reason}"
            ),
            "status_code": 202,
            "verdict": {
                "level": verdict.level.value,
                "dimension": verdict.dimension,
                "utilization": verdict.utilization,
                "reason": verdict.reason,
            },
        }

    # AUTO_APPROVED or FLAGGED — let the request through
    if verdict.level == GradientLevel.FLAGGED:
        logger.info(
            "Middleware: FLAGGED (allowed) action='%s' resource='%s' reason='%s'",
            action,
            resource,
            verdict.reason,
        )

    return None
