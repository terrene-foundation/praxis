# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
API handler functions for all Praxis endpoints.

Each handler is a plain function that:
1. Takes core service instances and request parameters
2. Calls the appropriate core service method
3. Returns a formatted response dict
4. Handles errors gracefully (returns error dicts, never raises)

These handlers are independent of any web framework — they can be
called from Nexus, FastAPI, CLI, MCP, or directly in tests.
"""

from __future__ import annotations

import hmac
import logging
import math
from typing import Any

from praxis.api.errors import error_from_exception

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth handlers
# ---------------------------------------------------------------------------


def login_handler(
    username: str,
    password: str,
    config,
) -> dict[str, Any]:
    """Authenticate a user and return a JWT access token.

    In dev mode, any username/password combination is accepted.
    In production mode, validates against PRAXIS_ADMIN_USER and
    PRAXIS_ADMIN_PASSWORD from the environment configuration.

    Args:
        username: The username to authenticate.
        password: The password to authenticate.
        config: PraxisConfig instance providing dev_mode, api_secret,
                admin_user, and admin_password.

    Returns:
        Dict with 'access_token' and 'token_type' on success,
        or error dict on failure.
    """
    from praxis.api.auth import AuthenticationError, create_token

    try:
        if not username or not password:
            raise ValueError("Username and password are required")

        if config.dev_mode:
            # Dev mode: accept any credentials
            token = create_token(user_id=username, secret=config.api_secret)
            logger.info("Handler: Dev-mode login for user '%s'", username)
            return {"access_token": token, "token_type": "bearer"}

        # Production: validate against configured admin credentials
        if not config.admin_user or not config.admin_password:
            raise AuthenticationError(
                "Login is not configured. Set PRAXIS_ADMIN_USER and "
                "PRAXIS_ADMIN_PASSWORD environment variables."
            )

        if not (
            hmac.compare_digest(username, config.admin_user)
            and hmac.compare_digest(password, config.admin_password)
        ):
            raise AuthenticationError("Invalid username or password")

        token = create_token(user_id=username, secret=config.api_secret)
        logger.info("Handler: Production login for user '%s'", username)
        return {"access_token": token, "token_type": "bearer"}

    except Exception as exc:
        logger.error("Handler: Login failed for user '%s': %s", username, exc)
        return error_from_exception(exc).to_dict()


async def firebase_login_handler(
    id_token: str,
    config,
) -> dict[str, Any]:
    """Authenticate a user via Firebase ID token and return a Praxis JWT.

    Verifies the Firebase ID token against Google's public certificates,
    creates or updates the user in the database, and returns a Praxis JWT
    with the user's identity.

    Args:
        id_token: The Firebase ID token from the frontend.
        config: PraxisConfig instance providing api_secret.

    Returns:
        Dict with 'access_token', 'token_type', and 'user' on success,
        or error dict on failure.
    """
    from praxis.api.auth import create_token
    from praxis.api.firebase import extract_user_info, verify_firebase_token
    from praxis.persistence.db_ops import db_create, db_read, db_update

    try:
        if not id_token:
            raise ValueError("Firebase ID token is required")

        # Verify the Firebase ID token
        decoded = await verify_firebase_token(id_token)

        # Extract normalized user info
        user_info = extract_user_info(decoded)
        uid = user_info["uid"]
        email = user_info["email"]
        display_name = user_info["display_name"]
        photo_url = user_info["photo_url"]
        provider = user_info["provider"]

        # Create or update user in database
        from praxis.persistence.db_ops import _now_iso

        existing_user = db_read("User", uid)
        if existing_user is None:
            # First login -- create user
            db_create(
                "User",
                {
                    "id": uid,
                    "email": email,
                    "display_name": display_name,
                    "photo_url": photo_url or "",
                    "provider": provider,
                    "role": "practitioner",
                    "last_login_at": _now_iso(),
                },
            )
            role = "practitioner"
            logger.info(
                "Handler: Created new user uid=%s email=%s provider=%s",
                uid,
                email,
                provider,
            )
        else:
            # Returning user -- update last login and profile info
            db_update(
                "User",
                uid,
                {
                    "email": email,
                    "display_name": display_name,
                    "photo_url": photo_url or "",
                    "provider": provider,
                    "last_login_at": _now_iso(),
                },
            )
            role = existing_user.get("role", "practitioner")
            logger.info(
                "Handler: Returning user uid=%s email=%s",
                uid,
                email,
            )

        # Create Praxis JWT with user identity
        token = create_token(user_id=uid, secret=config.api_secret)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": uid,
                "email": email,
                "display_name": display_name,
                "photo_url": photo_url,
                "provider": provider,
                "role": role,
            },
        }

    except Exception as exc:
        logger.error("Handler: Firebase login failed: %s", exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Session handlers
# ---------------------------------------------------------------------------


def create_session_handler(
    session_manager,
    workspace_id: str,
    domain: str = "coc",
    constraint_template: str = "moderate",
    constraints: dict | None = None,
    authority_id: str = "local-user",
) -> dict[str, Any]:
    """Create a new CO collaboration session.

    Args:
        session_manager: SessionManager instance.
        workspace_id: Workspace identifier. Must not be empty.
        domain: CO domain (coc, coe, cog, etc.).
        constraint_template: Constraint template name.
        constraints: Explicit constraint envelope (overrides template).
        authority_id: Identity of the session creator.

    Returns:
        Session dict on success, or error dict on failure.
    """
    try:
        session = session_manager.create_session(
            workspace_id=workspace_id,
            domain=domain,
            constraint_template=constraint_template,
            constraints=constraints,
            authority_id=authority_id,
        )
        logger.info("Handler: Created session %s", session["session_id"])
        return session
    except Exception as exc:
        logger.error("Handler: Failed to create session: %s", exc)
        return error_from_exception(exc).to_dict()


def list_sessions_handler(
    session_manager,
    workspace_id: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    """List sessions, optionally filtered.

    Args:
        session_manager: SessionManager instance.
        workspace_id: Optional workspace filter.
        state: Optional state filter.

    Returns:
        Dict with 'sessions' key containing list of session dicts.
    """
    try:
        sessions = session_manager.list_sessions(workspace_id=workspace_id, state=state)
        return {"sessions": sessions}
    except Exception as exc:
        logger.error("Handler: Failed to list sessions: %s", exc)
        return error_from_exception(exc).to_dict()


def get_session_handler(
    session_manager,
    session_id: str,
) -> dict[str, Any]:
    """Get a session by ID.

    Args:
        session_manager: SessionManager instance.
        session_id: The session identifier.

    Returns:
        Session dict on success, or error dict on failure.
    """
    try:
        return session_manager.get_session(session_id)
    except Exception as exc:
        logger.error("Handler: Failed to get session %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


def pause_session_handler(
    session_manager,
    session_id: str,
    reason: str = "",
) -> dict[str, Any]:
    """Pause an active session.

    Args:
        session_manager: SessionManager instance.
        session_id: The session identifier.
        reason: Optional reason for pausing.

    Returns:
        Updated session dict, or error dict on failure.
    """
    try:
        return session_manager.pause_session(session_id, reason=reason)
    except Exception as exc:
        logger.error("Handler: Failed to pause session %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


def resume_session_handler(
    session_manager,
    session_id: str,
) -> dict[str, Any]:
    """Resume a paused session.

    Args:
        session_manager: SessionManager instance.
        session_id: The session identifier.

    Returns:
        Updated session dict, or error dict on failure.
    """
    try:
        return session_manager.resume_session(session_id)
    except Exception as exc:
        logger.error("Handler: Failed to resume session %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


def end_session_handler(
    session_manager,
    session_id: str,
    summary: str = "",
) -> dict[str, Any]:
    """End (archive) a session.

    Args:
        session_manager: SessionManager instance.
        session_id: The session identifier.
        summary: Optional session summary.

    Returns:
        Updated session dict, or error dict on failure.
    """
    try:
        return session_manager.end_session(session_id, summary=summary)
    except Exception as exc:
        logger.error("Handler: Failed to end session %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Deliberation handlers
# ---------------------------------------------------------------------------


def decide_handler(
    engine,
    decision: str,
    rationale: str,
    actor: str = "human",
    alternatives: list[str] | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Record a decision.

    Args:
        engine: DeliberationEngine instance.
        decision: The decision that was made.
        rationale: Why this decision was made.
        actor: Who made the decision.
        alternatives: Other options considered.
        confidence: Confidence level [0.0, 1.0].

    Returns:
        Deliberation record dict, or error dict on failure.
    """
    try:
        if confidence is not None:
            if not isinstance(confidence, (int, float)) or not math.isfinite(confidence):
                return {
                    "error": {
                        "type": "validation_error",
                        "message": "confidence must be a finite number",
                    }
                }
            if not (0.0 <= confidence <= 1.0):
                return {
                    "error": {
                        "type": "validation_error",
                        "message": "confidence must be between 0.0 and 1.0",
                    }
                }

        return engine.record_decision(
            decision=decision,
            rationale=rationale,
            actor=actor,
            alternatives=alternatives,
            confidence=confidence,
        )
    except Exception as exc:
        logger.error("Handler: Failed to record decision: %s", exc)
        return error_from_exception(exc).to_dict()


def observe_handler(
    engine,
    observation: str,
    actor: str = "ai",
    confidence: float | None = None,
) -> dict[str, Any]:
    """Record an observation.

    Args:
        engine: DeliberationEngine instance.
        observation: What was observed.
        actor: Who made the observation.
        confidence: Confidence level [0.0, 1.0].

    Returns:
        Deliberation record dict, or error dict on failure.
    """
    try:
        return engine.record_observation(
            observation=observation,
            actor=actor,
            confidence=confidence,
        )
    except Exception as exc:
        logger.error("Handler: Failed to record observation: %s", exc)
        return error_from_exception(exc).to_dict()


def timeline_handler(
    engine,
    record_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Get the deliberation timeline.

    Args:
        engine: DeliberationEngine instance.
        record_type: Optional filter by record type.
        limit: Maximum records to return.
        offset: Records to skip.

    Returns:
        Dict with 'records' and 'total' keys.
    """
    try:
        records, total = engine.get_timeline(
            record_type=record_type,
            limit=limit,
            offset=offset,
        )
        return {"records": records, "total": total}
    except Exception as exc:
        logger.error("Handler: Failed to get timeline: %s", exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Constraint handlers
# ---------------------------------------------------------------------------


def get_constraints_handler(
    session_manager,
    session_id: str,
) -> dict[str, Any]:
    """Get the constraint envelope for a session.

    Args:
        session_manager: SessionManager instance.
        session_id: The session identifier.

    Returns:
        Dict with 'constraint_envelope' key, or error dict.
    """
    try:
        session = session_manager.get_session(session_id)
        return {"constraint_envelope": session["constraint_envelope"]}
    except Exception as exc:
        logger.error("Handler: Failed to get constraints for %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


def update_constraints_handler(
    session_manager,
    session_id: str,
    new_constraints: dict,
    rationale: str = "",
) -> dict[str, Any]:
    """Update the constraint envelope (tightening only).

    A rationale is required explaining WHY the constraints differ from
    the domain YAML baseline. The rationale is stored as a deliberation
    observation for audit purposes.

    Args:
        session_manager: SessionManager instance.
        session_id: The session identifier.
        new_constraints: Proposed new constraint envelope.
        rationale: Explanation of why these constraints differ from baseline.
            Required for constraint updates.

    Returns:
        Updated session dict, or error dict on failure.
    """
    try:
        if not rationale:
            raise ValueError(
                "A rationale is required when updating constraints. "
                "Explain why these constraints differ from the domain baseline."
            )

        session = session_manager.update_constraints(session_id, new_constraints)

        # Store the rationale as a deliberation observation
        try:
            from praxis.core.deliberation import DeliberationEngine

            engine = DeliberationEngine(session_id=session_id)
            engine.record_observation(
                observation=(
                    f"Constraint update rationale: {rationale}. "
                    f"Updated constraint envelope for session {session_id}."
                ),
                actor="system",
            )
        except Exception as obs_exc:
            logger.warning(
                "Handler: Could not record constraint update rationale " "for session %s: %s",
                session_id,
                obs_exc,
            )

        return session
    except Exception as exc:
        logger.error("Handler: Failed to update constraints for %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


def get_gradient_handler(
    enforcer,
) -> dict[str, Any]:
    """Get the current constraint gradient status.

    Args:
        enforcer: ConstraintEnforcer instance.

    Returns:
        Dict with 'dimensions' key containing per-dimension status.
    """
    try:
        status = enforcer.get_status()
        return {"dimensions": status}
    except Exception as exc:
        logger.error("Handler: Failed to get gradient status: %s", exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Trust handlers
# ---------------------------------------------------------------------------


def delegate_handler(
    session_id: str,
    parent_id: str,
    parent_constraints: dict,
    delegate_id: str,
    delegate_constraints: dict,
    key_id: str,
    key_manager,
    parent_hash: str,
) -> dict[str, Any]:
    """Create a delegation record.

    Args:
        session_id: Session this delegation belongs to.
        parent_id: ID of the parent record.
        parent_constraints: Parent constraint envelope.
        delegate_id: Identity of the delegate.
        delegate_constraints: Delegate constraint envelope (must be tighter).
        key_id: Signing key identifier.
        key_manager: KeyManager instance.
        parent_hash: Content hash of the parent record.

    Returns:
        Delegation record dict, or error dict on failure.
    """
    try:
        from praxis.trust.delegation import create_delegation

        delegation = create_delegation(
            session_id=session_id,
            parent_id=parent_id,
            parent_constraints=parent_constraints,
            delegate_id=delegate_id,
            delegate_constraints=delegate_constraints,
            key_id=key_id,
            key_manager=key_manager,
            parent_hash=parent_hash,
        )
        return {
            "delegation_id": delegation.delegation_id,
            "session_id": delegation.session_id,
            "delegate_id": delegation.delegate_id,
            "constraints": delegation.constraints,
            "content_hash": delegation.content_hash,
            "parent_hash": delegation.parent_hash,
            "created_at": delegation.created_at,
        }
    except Exception as exc:
        logger.error("Handler: Failed to create delegation: %s", exc)
        return error_from_exception(exc).to_dict()


def approve_handler(
    held_action_manager,
    held_id: str,
    approved_by: str,
) -> dict[str, Any]:
    """Approve a held action.

    Args:
        held_action_manager: HeldActionManager instance.
        held_id: The held action identifier.
        approved_by: Identity of the approver.

    Returns:
        Dict with resolution details, or error dict.
    """
    try:
        held = held_action_manager.approve(held_id, approved_by)
        return {
            "held_id": held.held_id,
            "resolution": held.resolution,
            "resolved_by": held.resolved_by,
            "resolved_at": held.resolved_at,
        }
    except Exception as exc:
        logger.error("Handler: Failed to approve held action %s: %s", held_id, exc)
        return error_from_exception(exc).to_dict()


def deny_handler(
    held_action_manager,
    held_id: str,
    denied_by: str,
) -> dict[str, Any]:
    """Deny a held action.

    Args:
        held_action_manager: HeldActionManager instance.
        held_id: The held action identifier.
        denied_by: Identity of the denier.

    Returns:
        Dict with resolution details, or error dict.
    """
    try:
        held = held_action_manager.deny(held_id, denied_by)
        return {
            "held_id": held.held_id,
            "resolution": held.resolution,
            "resolved_by": held.resolved_by,
            "resolved_at": held.resolved_at,
        }
    except Exception as exc:
        logger.error("Handler: Failed to deny held action %s: %s", held_id, exc)
        return error_from_exception(exc).to_dict()


def list_held_actions_handler(
    held_action_manager,
    session_id: str,
) -> dict[str, Any]:
    """List pending held actions for a session.

    Args:
        held_action_manager: HeldActionManager instance.
        session_id: The session identifier.

    Returns:
        Dict with 'held_actions' key containing list of held action dicts.
    """
    try:
        pending = held_action_manager.get_pending(session_id=session_id)
        return {
            "held_actions": [
                {
                    "held_id": h.held_id,
                    "session_id": h.session_id,
                    "action": h.action,
                    "resource": h.resource,
                    "dimension": h.dimension,
                    "reason": h.verdict.reason,
                    "utilization": h.verdict.utilization,
                    "created_at": h.created_at,
                }
                for h in pending
            ],
            "total": len(pending),
        }
    except Exception as exc:
        logger.error("Handler: Failed to list held actions: %s", exc)
        return error_from_exception(exc).to_dict()


def get_chain_handler(
    audit_chain,
) -> dict[str, Any]:
    """Get the trust chain status.

    Args:
        audit_chain: AuditChain instance.

    Returns:
        Dict with chain length, head hash, and integrity status.
    """
    try:
        valid, breaks = audit_chain.verify_integrity()
        return {
            "chain_length": audit_chain.length,
            "head_hash": audit_chain.head_hash,
            "valid": valid,
            "breaks": breaks,
        }
    except Exception as exc:
        logger.error("Handler: Failed to get chain: %s", exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Verification handlers
# ---------------------------------------------------------------------------


def verify_handler(
    entries: list[dict],
    public_keys: dict[str, str],
) -> dict[str, Any]:
    """Verify a trust chain from exported data.

    Args:
        entries: Ordered list of chain entries.
        public_keys: Mapping of key_id to PEM-encoded public key.

    Returns:
        Verification result dict.
    """
    try:
        from praxis.trust.verify import verify_chain

        result = verify_chain(entries=entries, public_keys=public_keys)
        return {
            "valid": result.valid,
            "total_entries": result.total_entries,
            "verified_entries": result.verified_entries,
            "breaks": result.breaks,
        }
    except Exception as exc:
        logger.error("Handler: Failed to verify chain: %s", exc)
        return error_from_exception(exc).to_dict()


def export_handler(
    audit_chain,
    key_manager,
    key_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Export a verification bundle for a session.

    Args:
        audit_chain: AuditChain instance.
        key_manager: KeyManager instance for exporting public keys.
        key_id: The signing key identifier.
        session_id: The session identifier.

    Returns:
        Verification bundle dict with entries, public keys, and metadata.
    """
    try:
        # Build entries from audit chain anchors
        entries = []
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

        # Export public key
        public_pem = key_manager.export_public_pem(key_id)
        if isinstance(public_pem, bytes):
            public_pem = public_pem.decode("utf-8")

        public_keys = {key_id: public_pem}

        return {
            "session_id": session_id,
            "entries": entries,
            "public_keys": public_keys,
            "chain_length": audit_chain.length,
        }
    except Exception as exc:
        logger.error("Handler: Failed to export bundle: %s", exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Learning handlers
# ---------------------------------------------------------------------------


def list_learning_proposals_handler(
    domain: str,
    status: str | None = None,
) -> dict[str, Any]:
    """List learning evolution proposals for a domain.

    Args:
        domain: CO domain to list proposals for.
        status: Optional filter (pending, approved, rejected).

    Returns:
        Dict with 'proposals' key containing list of proposal dicts.
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain)
        proposals = pipeline.get_proposals(status=status)
        return {"proposals": proposals, "total": len(proposals)}
    except Exception as exc:
        logger.error("Handler: Failed to list learning proposals: %s", exc)
        return error_from_exception(exc).to_dict()


def approve_learning_proposal_handler(
    domain: str,
    proposal_id: str,
    approved_by: str,
) -> dict[str, Any]:
    """Approve a learning evolution proposal.

    Does NOT auto-apply the change. Returns a diff for the human
    to review and manually apply to the domain configuration.

    Args:
        domain: CO domain the proposal belongs to.
        proposal_id: The proposal to approve.
        approved_by: Identity of the approver.

    Returns:
        Dict with approval details and YAML diff recommendation.
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain)
        result = pipeline.formalize(proposal_id, approved_by)
        return result
    except Exception as exc:
        logger.error("Handler: Failed to approve learning proposal %s: %s", proposal_id, exc)
        return error_from_exception(exc).to_dict()


def reject_learning_proposal_handler(
    domain: str,
    proposal_id: str,
    rejected_by: str,
    reason: str = "",
) -> dict[str, Any]:
    """Reject a learning evolution proposal.

    Args:
        domain: CO domain the proposal belongs to.
        proposal_id: The proposal to reject.
        rejected_by: Identity of the rejector.
        reason: Optional reason for rejection.

    Returns:
        Dict with rejection details.
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain)
        result = pipeline.reject(proposal_id, rejected_by, reason)
        return result
    except Exception as exc:
        logger.error("Handler: Failed to reject learning proposal %s: %s", proposal_id, exc)
        return error_from_exception(exc).to_dict()


def analyze_learning_handler(
    domain: str,
) -> dict[str, Any]:
    """Run learning analysis on accumulated observations.

    Args:
        domain: CO domain to analyze.

    Returns:
        Dict with 'patterns' key containing detected patterns.
    """
    try:
        from praxis.core.learning import LearningPipeline

        pipeline = LearningPipeline(domain=domain)
        patterns = pipeline.analyze()
        return {
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence,
                    "evidence_count": len(p.evidence),
                    "domain": p.domain,
                }
                for p in patterns
            ],
            "total": len(patterns),
        }
    except Exception as exc:
        logger.error("Handler: Failed to analyze learning for domain %s: %s", domain, exc)
        return error_from_exception(exc).to_dict()


# ---------------------------------------------------------------------------
# Bainbridge Irony handlers
# ---------------------------------------------------------------------------


def fatigue_handler(
    session_id: str,
) -> dict[str, Any]:
    """Assess approval fatigue risk for a session.

    Args:
        session_id: The session to assess.

    Returns:
        Fatigue assessment dict, or error dict on failure.
    """
    try:
        from praxis.core.bainbridge import FatigueDetector

        detector = FatigueDetector()
        return detector.assess(session_id)
    except Exception as exc:
        logger.error("Handler: Failed to assess fatigue for %s: %s", session_id, exc)
        return error_from_exception(exc).to_dict()


def capability_handler(
    practitioner_id: str,
    domain: str,
) -> dict[str, Any]:
    """Assess a practitioner's capability.

    Args:
        practitioner_id: The actor to assess.
        domain: CO domain scope.

    Returns:
        Capability assessment dict, or error dict on failure.
    """
    try:
        from praxis.core.bainbridge import CapabilityTracker

        tracker = CapabilityTracker()
        return tracker.assess_capability(practitioner_id, domain)
    except Exception as exc:
        logger.error(
            "Handler: Failed to assess capability for %s in %s: %s",
            practitioner_id,
            domain,
            exc,
        )
        return error_from_exception(exc).to_dict()


def constraint_review_handler(
    session_id: str,
) -> dict[str, Any]:
    """Get constraint review status for a session.

    Args:
        session_id: The session to check.

    Returns:
        Review status dict, or error dict on failure.
    """
    try:
        from praxis.core.bainbridge import ConstraintReviewTracker

        tracker = ConstraintReviewTracker()
        return tracker.get_review_status(session_id)
    except Exception as exc:
        logger.error(
            "Handler: Failed to get review status for %s: %s",
            session_id,
            exc,
        )
        return error_from_exception(exc).to_dict()


def calibration_handler(
    domain: str,
) -> dict[str, Any]:
    """Run constraint calibration analysis for a domain.

    Args:
        domain: CO domain to analyze.

    Returns:
        Calibration report dict, or error dict on failure.
    """
    try:
        from praxis.core.calibration import CalibrationAnalyzer

        analyzer = CalibrationAnalyzer()
        return analyzer.analyze(domain)
    except Exception as exc:
        logger.error(
            "Handler: Failed to run calibration analysis for %s: %s",
            domain,
            exc,
        )
        return error_from_exception(exc).to_dict()


def audit_handler(
    audit_chain,
) -> dict[str, Any]:
    """Get audit chain status.

    Args:
        audit_chain: AuditChain instance.

    Returns:
        Dict with chain length, integrity status, and any breaks.
    """
    try:
        valid, breaks = audit_chain.verify_integrity()
        return {
            "chain_length": audit_chain.length,
            "valid": valid,
            "breaks": breaks,
        }
    except Exception as exc:
        logger.error("Handler: Failed to get audit status: %s", exc)
        return error_from_exception(exc).to_dict()
