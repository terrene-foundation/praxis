# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Learning observation consumers — wire session activity into the learning pipeline.

These functions are called from API handlers and other integration points to
feed observations into the CO Layer 5 learning pipeline. They observe:

1. Constraint evaluations: utilization levels, verdict distribution, action types
2. Held action resolutions: approval rate, review time, approver identity
3. Session lifecycle events: session duration, decision count, phase progression

Each consumer checks whether the observation target is declared in the domain
YAML before recording. Failures are logged but never propagated — observation
is a non-critical side-effect that must not break the main operation.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def observe_constraint_evaluation(
    session_id: str,
    domain: str,
    action: str,
    resource: str | None,
    verdict: str,
    dimension: str,
    utilization: float,
) -> None:
    """Record a constraint evaluation observation.

    Called after every ConstraintEnforcer.evaluate() call to feed
    the learning pipeline with utilization and verdict data.

    Args:
        session_id: The session this evaluation belongs to.
        domain: CO domain for this session.
        action: The action that was evaluated.
        resource: Optional resource the action targets.
        verdict: The gradient verdict (auto_approved, flagged, held, blocked).
        dimension: The most restrictive dimension.
        utilization: The utilization ratio (0.0-1.0).
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain, session_id=session_id)
        pipeline.observe(
            target="constraint_evaluation",
            content={
                "session_id": session_id,
                "action": action,
                "resource": resource,
                "verdict": verdict,
                "dimension": dimension,
                "utilization": utilization,
            },
        )
    except ValueError:
        # Target not in domain's observation_targets — expected, not an error
        logger.debug(
            "constraint_evaluation not in observation targets for domain '%s'",
            domain,
        )
    except Exception as exc:
        logger.debug("Could not record constraint evaluation observation: %s", exc)


def observe_held_action_resolution(
    session_id: str,
    domain: str,
    held_id: str,
    action: str,
    resolution: str,
    resolved_by: str,
    review_time_seconds: float = 0.0,
) -> None:
    """Record a held action resolution observation.

    Called when a held action is approved or denied to track
    approval patterns and review times.

    Args:
        session_id: The session this held action belongs to.
        domain: CO domain for this session.
        held_id: The held action identifier.
        action: The action that was held.
        resolution: "approved" or "denied".
        resolved_by: Identity of the resolver.
        review_time_seconds: Seconds between hold creation and resolution.
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain, session_id=session_id)
        pipeline.observe(
            target="held_action_resolution",
            content={
                "session_id": session_id,
                "held_id": held_id,
                "action": action,
                "resolution": resolution,
                "resolved_by": resolved_by,
                "review_time_seconds": review_time_seconds,
            },
        )
    except ValueError:
        logger.debug(
            "held_action_resolution not in observation targets for domain '%s'",
            domain,
        )
    except Exception as exc:
        logger.debug("Could not record held action resolution observation: %s", exc)


def observe_session_lifecycle(
    session_id: str,
    domain: str,
    event: str,
    constraint_template: str = "",
    duration_minutes: float = 0.0,
    decision_count: int = 0,
    current_phase: str | None = None,
) -> None:
    """Record a session lifecycle observation.

    Called on session start, end, pause, resume, and phase changes
    to track session duration, decision volume, and phase progression.

    Args:
        session_id: The session identifier.
        domain: CO domain for this session.
        event: Lifecycle event type (created, ended, paused, resumed, phase_changed).
        constraint_template: Template used for this session.
        duration_minutes: Session duration at time of event.
        decision_count: Number of decisions recorded in this session.
        current_phase: Current phase name (if applicable).
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain, session_id=session_id)
        pipeline.observe(
            target="session_lifecycle",
            content={
                "session_id": session_id,
                "event": event,
                "constraint_template": constraint_template,
                "duration_minutes": duration_minutes,
                "decision_count": decision_count,
                "current_phase": current_phase,
            },
        )
    except ValueError:
        logger.debug(
            "session_lifecycle not in observation targets for domain '%s'",
            domain,
        )
    except Exception as exc:
        logger.debug("Could not record session lifecycle observation: %s", exc)
