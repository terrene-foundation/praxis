# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
MCP (Model Context Protocol) server tool definitions for Praxis.

Defines the tools that AI assistants (Claude, etc.) use to interact
with the Praxis trust layer during collaboration sessions.

MCP tools:
    trust_check  — Evaluate action against constraint envelope
    trust_record — Record a deliberation entry (decision/observation)
    trust_escalate — Escalate an issue for human review
    trust_envelope — Get current constraint state
    trust_status — Get session status
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_mcp_tools(
    app,
    session_manager,
    deliberation_engines,
    constraint_enforcers,
    audit_chains=None,
    held_action_manager=None,
    key_manager=None,
    key_id=None,
):
    """Register MCP tools with a Nexus application.

    Each tool is registered as a Nexus handler, which makes it
    automatically available as both an MCP tool and a REST endpoint.

    Args:
        app: Nexus application instance.
        session_manager: SessionManager instance.
        deliberation_engines: Dict mapping session_id to DeliberationEngine.
        constraint_enforcers: Dict mapping session_id to ConstraintEnforcer.
        audit_chains: Optional dict mapping session_id to AuditChain.
        held_action_manager: Optional HeldActionManager instance.
        key_manager: Optional KeyManager instance.
        key_id: Optional signing key identifier.
    """

    @app.handler("trust_check", description="Evaluate action against constraint envelope")
    async def trust_check(
        session_id: str,
        action: str,
        resource: str = "",
    ) -> dict[str, Any]:
        """Evaluate an action against the session's constraint envelope.

        Returns the gradient verdict: auto_approved, flagged, held, or blocked.
        When the verdict is HELD, automatically creates a held action that
        requires human approval before the action can proceed.
        """
        if session_id not in constraint_enforcers:
            return {
                "error": {"type": "not_found", "message": f"No enforcer for session '{session_id}'"}
            }

        enforcer = constraint_enforcers[session_id]
        verdict = enforcer.evaluate(
            action=action,
            resource=resource if resource else None,
        )

        result: dict[str, Any] = {
            "level": verdict.level.value,
            "dimension": verdict.dimension,
            "utilization": verdict.utilization,
            "reason": verdict.reason,
            "action": verdict.action,
            "resource": verdict.resource,
        }

        # When verdict is HELD, create a held action for human approval
        if verdict.level.value == "held" and held_action_manager is not None:
            try:
                held = held_action_manager.hold(
                    session_id=session_id,
                    action=action,
                    resource=resource if resource else None,
                    verdict=verdict,
                )
                result["held_action_id"] = held.held_id
                logger.info(
                    "MCP trust_check: created held action %s for session %s",
                    held.held_id,
                    session_id,
                )
            except Exception as exc:
                logger.warning("Failed to create held action: %s", exc)

        # Record the evaluation in the audit chain
        if audit_chains is not None and key_manager is not None and key_id is not None:
            try:
                from praxis.trust.audit import AuditChain

                if session_id not in audit_chains:
                    audit_chains[session_id] = AuditChain(
                        session_id=session_id,
                        key_id=key_id,
                        key_manager=key_manager,
                    )
                chain = audit_chains[session_id]
                chain.append(
                    action=action,
                    actor="ai",
                    result=verdict.level.value,
                    resource=resource if resource else None,
                    extra_payload={
                        "dimension": verdict.dimension,
                        "utilization": verdict.utilization,
                    },
                )
            except Exception as exc:
                logger.warning("Failed to record audit anchor for trust_check: %s", exc)

        return result

    @app.handler("trust_record", description="Record a deliberation entry")
    async def trust_record(
        session_id: str,
        action: str,
        reasoning_trace: str,
        actor: str = "ai",
    ) -> dict[str, Any]:
        """Record a deliberation observation in the session."""
        if session_id not in deliberation_engines:
            return {
                "error": {"type": "not_found", "message": f"No engine for session '{session_id}'"}
            }

        engine = deliberation_engines[session_id]
        record = engine.record_observation(
            observation=f"{action}: {reasoning_trace}",
            actor=actor,
        )
        return {
            "record_id": record["record_id"],
            "anchor_id": record.get("anchor_id"),
            "reasoning_hash": record["reasoning_hash"],
        }

    @app.handler("trust_escalate", description="Escalate an issue for human review")
    async def trust_escalate(
        session_id: str,
        issue: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Escalate an issue for human review."""
        if session_id not in deliberation_engines:
            return {
                "error": {"type": "not_found", "message": f"No engine for session '{session_id}'"}
            }

        engine = deliberation_engines[session_id]
        record = engine.record_escalation(
            issue=issue,
            context=context,
            actor="system",
        )
        return {
            "record_id": record["record_id"],
            "escalation_id": record["record_id"],
            "anchor_id": record.get("anchor_id"),
        }

    @app.handler("trust_envelope", description="Get current constraint state")
    async def trust_envelope(session_id: str) -> dict[str, Any]:
        """Get the current constraint envelope and gradient status."""
        try:
            session = session_manager.get_session(session_id)
            result = {
                "session_id": session_id,
                "constraint_envelope": session["constraint_envelope"],
                "state": session["state"],
            }

            if session_id in constraint_enforcers:
                result["gradient_status"] = constraint_enforcers[session_id].get_status()

            return result
        except KeyError:
            return {"error": {"type": "not_found", "message": f"Session '{session_id}' not found"}}

    @app.handler("trust_status", description="Get session status")
    async def trust_status(session_id: str) -> dict[str, Any]:
        """Get the current session status."""
        try:
            session = session_manager.get_session(session_id)
            return {
                "session_id": session["session_id"],
                "state": session["state"],
                "domain": session["domain"],
                "workspace_id": session["workspace_id"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
                "ended_at": session["ended_at"],
            }
        except KeyError:
            return {"error": {"type": "not_found", "message": f"Session '{session_id}' not found"}}

    logger.info(
        "Registered 5 MCP tools: trust_check, trust_record, trust_escalate, trust_envelope, trust_status"
    )
