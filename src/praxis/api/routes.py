# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
RESTful URL routes for the Praxis API.

Maps RESTful paths (POST /sessions, GET /sessions/:id, etc.) to the
framework-independent handler functions in handlers.py.

Nexus registers handlers at POST /workflows/{name}/execute by default.
This module provides a FastAPI APIRouter with conventional REST paths
so web dashboards, mobile apps, and other HTTP clients can call the API
using the URL scheme they expect.

Both URL schemes work simultaneously:
    - POST /workflows/create_session/execute  (Nexus native)
    - POST /sessions                          (RESTful)

The router is included in the Nexus app via app.include_router().
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Request

from praxis.api.handlers import (
    analyze_learning_handler,
    approve_handler,
    approve_learning_proposal_handler,
    audit_handler,
    calibration_handler,
    capability_handler,
    constraint_review_handler,
    create_session_handler,
    decide_handler,
    delegate_handler,
    deny_handler,
    end_session_handler,
    export_handler,
    fatigue_handler,
    firebase_login_handler,
    get_chain_handler,
    get_constraints_handler,
    get_gradient_handler,
    get_session_handler,
    list_held_actions_handler,
    list_learning_proposals_handler,
    list_sessions_handler,
    login_handler,
    observe_handler,
    pause_session_handler,
    reject_learning_proposal_handler,
    resume_session_handler,
    timeline_handler,
    update_constraints_handler,
    verify_handler,
)

logger = logging.getLogger(__name__)


def create_rest_router(
    session_manager,
    deliberation_engines: dict[str, Any],
    constraint_enforcers: dict[str, Any],
    key_manager,
    key_id: str,
    audit_chains: dict[str, Any],
    held_action_manager=None,
    config=None,
) -> APIRouter:
    """Create a FastAPI APIRouter with RESTful URL mappings.

    Each route delegates to the same handler functions used by Nexus,
    keeping the single-source-of-truth principle intact.

    Args:
        session_manager: SessionManager instance.
        deliberation_engines: Dict mapping session_id to DeliberationEngine.
        constraint_enforcers: Dict mapping session_id to ConstraintEnforcer.
        key_manager: KeyManager instance.
        key_id: Default signing key identifier.
        audit_chains: Dict mapping session_id to AuditChain.
        held_action_manager: Optional shared HeldActionManager instance.
        config: Optional PraxisConfig instance.

    Returns:
        Configured FastAPI APIRouter.
    """
    # Import helpers that are also used in app.py
    from praxis.api.app import (
        _get_or_create_chain,
        _get_or_create_engine,
        _get_or_create_enforcer,
    )

    router = APIRouter()

    # -----------------------------------------------------------------------
    # Auth endpoints
    # -----------------------------------------------------------------------

    from praxis.api.rate_limit import RateLimiter

    login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=60)

    @router.post("/auth/login", tags=["Auth"])
    async def rest_login(request: Request, body: dict = Body(...)) -> dict:
        client_ip = getattr(request.client, "host", "unknown") if request.client else "unknown"

        if not login_rate_limiter.check(client_ip):
            return {
                "error": {
                    "type": "rate_limited",
                    "message": "Too many login attempts. Try again later.",
                }
            }

        return login_handler(
            username=body.get("username", ""),
            password=body.get("password", ""),
            config=config,
        )

    @router.post("/auth/firebase", tags=["Auth"])
    async def rest_firebase_login(request: Request, body: dict = Body(...)) -> dict:
        """Authenticate via Firebase ID token (SSO-only login path)."""
        client_ip = getattr(request.client, "host", "unknown") if request.client else "unknown"

        if not login_rate_limiter.check(client_ip):
            return {
                "error": {
                    "type": "rate_limited",
                    "message": "Too many login attempts. Try again later.",
                }
            }

        return await firebase_login_handler(
            id_token=body.get("id_token", ""),
            config=config,
        )

    # -----------------------------------------------------------------------
    # Session endpoints
    # -----------------------------------------------------------------------

    @router.post("/sessions", tags=["Sessions"])
    async def rest_create_session(body: dict = Body(...)) -> dict:
        return create_session_handler(
            session_manager=session_manager,
            workspace_id=body.get("workspace_id", ""),
            domain=body.get("domain", "coc"),
            constraint_template=body.get("constraint_template", "moderate"),
            constraints=body.get("constraints"),
            authority_id=body.get("authority_id", "local-user"),
        )

    @router.get("/sessions", tags=["Sessions"])
    async def rest_list_sessions(
        workspace_id: str = Query("", description="Filter by workspace"),
        state: str = Query("", description="Filter by session state"),
    ) -> dict:
        return list_sessions_handler(
            session_manager=session_manager,
            workspace_id=workspace_id or None,
            state=state or None,
        )

    @router.get("/sessions/{session_id}", tags=["Sessions"])
    async def rest_get_session(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        return get_session_handler(
            session_manager=session_manager,
            session_id=session_id,
        )

    @router.post("/sessions/{session_id}/pause", tags=["Sessions"])
    async def rest_pause_session(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(default={}),
    ) -> dict:
        return pause_session_handler(
            session_manager=session_manager,
            session_id=session_id,
            reason=body.get("reason", ""),
        )

    @router.post("/sessions/{session_id}/resume", tags=["Sessions"])
    async def rest_resume_session(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        return resume_session_handler(
            session_manager=session_manager,
            session_id=session_id,
        )

    @router.post("/sessions/{session_id}/end", tags=["Sessions"])
    async def rest_end_session(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(default={}),
    ) -> dict:
        return end_session_handler(
            session_manager=session_manager,
            session_id=session_id,
            summary=body.get("summary", ""),
        )

    # -----------------------------------------------------------------------
    # Deliberation endpoints
    # -----------------------------------------------------------------------

    @router.post("/sessions/{session_id}/decide", tags=["Deliberation"])
    async def rest_decide(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(...),
    ) -> dict:
        engine = _get_or_create_engine(session_id, deliberation_engines, key_manager, key_id)
        return decide_handler(
            engine=engine,
            decision=body.get("decision", ""),
            rationale=body.get("rationale", ""),
            actor=body.get("actor", "human"),
            alternatives=body.get("alternatives"),
            confidence=body.get("confidence"),
        )

    @router.post("/sessions/{session_id}/observe", tags=["Deliberation"])
    async def rest_observe(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(...),
    ) -> dict:
        engine = _get_or_create_engine(session_id, deliberation_engines, key_manager, key_id)
        return observe_handler(
            engine=engine,
            observation=body.get("observation", ""),
            actor=body.get("actor", "ai"),
            confidence=body.get("confidence"),
        )

    @router.get("/sessions/{session_id}/timeline", tags=["Deliberation"])
    async def rest_timeline(
        session_id: str = Path(..., description="Session ID"),
        record_type: str = Query("", description="Filter by record type"),
        limit: int = Query(100, description="Maximum records to return"),
        offset: int = Query(0, description="Records to skip"),
    ) -> dict:
        engine = _get_or_create_engine(session_id, deliberation_engines, key_manager, key_id)
        return timeline_handler(
            engine=engine,
            record_type=record_type or None,
            limit=limit,
            offset=offset,
        )

    # -----------------------------------------------------------------------
    # Constraint endpoints
    # -----------------------------------------------------------------------

    @router.get("/sessions/{session_id}/constraints", tags=["Constraints"])
    async def rest_get_constraints(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        return get_constraints_handler(
            session_manager=session_manager,
            session_id=session_id,
        )

    @router.put("/sessions/{session_id}/constraints", tags=["Constraints"])
    async def rest_update_constraints(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(...),
    ) -> dict:
        # Extract rationale from the body (M11-02: mandatory constraint rationale)
        rationale = body.pop("rationale", "")
        return update_constraints_handler(
            session_manager=session_manager,
            session_id=session_id,
            new_constraints=body,
            rationale=rationale,
        )

    @router.get("/sessions/{session_id}/gradient", tags=["Constraints"])
    async def rest_get_gradient(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        enforcer = _get_or_create_enforcer(session_id, session_manager, constraint_enforcers)
        return get_gradient_handler(enforcer=enforcer)

    # -----------------------------------------------------------------------
    # Trust endpoints
    # -----------------------------------------------------------------------

    @router.post("/sessions/{session_id}/delegate", tags=["Trust"])
    async def rest_delegate(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(...),
    ) -> dict:
        session = session_manager.get_session(session_id)
        return delegate_handler(
            session_id=session_id,
            parent_id=session.get("genesis_id", ""),
            parent_constraints=session["constraint_envelope"],
            delegate_id=body.get("delegate_id", ""),
            delegate_constraints=body.get("delegate_constraints", session["constraint_envelope"]),
            key_id=key_id,
            key_manager=key_manager,
            parent_hash=session.get("genesis_id", ""),
        )

    @router.get("/sessions/{session_id}/held-actions", tags=["Trust"])
    async def rest_list_held_actions(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        if held_action_manager is None:
            return {
                "error": {"type": "not_configured", "message": "HeldActionManager not available"}
            }
        return list_held_actions_handler(
            held_action_manager=held_action_manager,
            session_id=session_id,
        )

    @router.post("/sessions/{session_id}/approve/{held_id}", tags=["Trust"])
    async def rest_approve(
        session_id: str = Path(..., description="Session ID"),
        held_id: str = Path(..., description="Held action ID"),
        body: dict = Body(default={}),
    ) -> dict:
        if held_action_manager is None:
            return {
                "error": {"type": "not_configured", "message": "HeldActionManager not available"}
            }
        return approve_handler(
            held_action_manager=held_action_manager,
            held_id=held_id,
            approved_by=body.get("approved_by", "api-user"),
        )

    @router.post("/sessions/{session_id}/deny/{held_id}", tags=["Trust"])
    async def rest_deny(
        session_id: str = Path(..., description="Session ID"),
        held_id: str = Path(..., description="Held action ID"),
        body: dict = Body(default={}),
    ) -> dict:
        if held_action_manager is None:
            return {
                "error": {"type": "not_configured", "message": "HeldActionManager not available"}
            }
        return deny_handler(
            held_action_manager=held_action_manager,
            held_id=held_id,
            denied_by=body.get("denied_by", "api-user"),
        )

    @router.get("/sessions/{session_id}/chain", tags=["Trust"])
    async def rest_get_chain(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
        return get_chain_handler(audit_chain=chain)

    # -----------------------------------------------------------------------
    # Verification endpoints
    # -----------------------------------------------------------------------

    @router.post("/sessions/{session_id}/verify", tags=["Verification"])
    async def rest_verify(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(default={}),
    ) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)

        # Build entries from the audit chain
        entries = []
        for anchor in chain.anchors:
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

        return verify_handler(
            entries=entries,
            public_keys={key_id: public_pem},
        )

    @router.post("/sessions/{session_id}/export", tags=["Verification"])
    async def rest_export(
        session_id: str = Path(..., description="Session ID"),
        body: dict = Body(default={}),
    ) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
        return export_handler(
            audit_chain=chain,
            key_manager=key_manager,
            key_id=key_id,
            session_id=session_id,
        )

    @router.get("/sessions/{session_id}/audit", tags=["Verification"])
    async def rest_audit(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
        return audit_handler(audit_chain=chain)

    # -----------------------------------------------------------------------
    # Learning endpoints (CO Layer 5)
    # -----------------------------------------------------------------------

    @router.get("/learning/proposals", tags=["Learning"])
    async def rest_list_learning_proposals(
        domain: str = Query("coc", description="CO domain"),
        status: str = Query("", description="Filter by status (pending, approved, rejected)"),
    ) -> dict:
        return list_learning_proposals_handler(
            domain=domain,
            status=status or None,
        )

    @router.post("/learning/proposals/{proposal_id}/approve", tags=["Learning"])
    async def rest_approve_learning_proposal(
        proposal_id: str = Path(..., description="Proposal ID"),
        body: dict = Body(default={}),
    ) -> dict:
        return approve_learning_proposal_handler(
            domain=body.get("domain", "coc"),
            proposal_id=proposal_id,
            approved_by=body.get("approved_by", "api-user"),
        )

    @router.post("/learning/proposals/{proposal_id}/reject", tags=["Learning"])
    async def rest_reject_learning_proposal(
        proposal_id: str = Path(..., description="Proposal ID"),
        body: dict = Body(default={}),
    ) -> dict:
        return reject_learning_proposal_handler(
            domain=body.get("domain", "coc"),
            proposal_id=proposal_id,
            rejected_by=body.get("rejected_by", "api-user"),
            reason=body.get("reason", ""),
        )

    @router.post("/learning/analyze", tags=["Learning"])
    async def rest_analyze_learning(
        body: dict = Body(default={}),
    ) -> dict:
        return analyze_learning_handler(
            domain=body.get("domain", "coc"),
        )

    # -----------------------------------------------------------------------
    # Bainbridge Irony detection endpoints (M11)
    # -----------------------------------------------------------------------

    @router.get("/sessions/{session_id}/fatigue", tags=["Bainbridge"])
    async def rest_fatigue(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        return fatigue_handler(session_id=session_id)

    @router.get("/sessions/{session_id}/constraint-review", tags=["Bainbridge"])
    async def rest_constraint_review(
        session_id: str = Path(..., description="Session ID"),
    ) -> dict:
        return constraint_review_handler(session_id=session_id)

    @router.get("/practitioners/{practitioner_id}/capability", tags=["Bainbridge"])
    async def rest_capability(
        practitioner_id: str = Path(..., description="Practitioner ID"),
        domain: str = Query("coc", description="CO domain"),
    ) -> dict:
        return capability_handler(
            practitioner_id=practitioner_id,
            domain=domain,
        )

    @router.get("/domains/{domain}/calibration", tags=["Bainbridge"])
    async def rest_calibration(
        domain: str = Path(..., description="CO domain"),
    ) -> dict:
        return calibration_handler(domain=domain)

    # -----------------------------------------------------------------------
    # Health endpoint
    # -----------------------------------------------------------------------

    @router.get("/health", tags=["System"])
    async def health() -> dict:
        from praxis import __version__
        from praxis.domains.loader import DomainLoader

        # Discover available domains
        try:
            loader = DomainLoader()
            domains = loader.list_domains()
        except Exception:
            domains = []

        # Check database connectivity
        db_status = "disconnected"
        try:
            from praxis.persistence import get_db

            get_db()
            db_status = "connected"
        except Exception:
            db_status = "error"

        return {
            "status": "ok",
            "version": __version__,
            "domains": domains,
            "db_status": db_status,
        }

    logger.info("REST router created with RESTful URL mappings")
    return router
