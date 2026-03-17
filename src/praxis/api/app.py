# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Nexus application factory for Praxis.

Creates and configures a Nexus application with all handlers registered.
The Nexus app exposes the Praxis API on three channels simultaneously:
REST API, CLI, and MCP.
"""

from __future__ import annotations

import logging
from typing import Any

from nexus import Nexus

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
from praxis.api.websocket import EventBroadcaster, get_broadcaster

logger = logging.getLogger(__name__)


def create_app(
    config=None,
    session_manager=None,
    key_manager=None,
    key_id: str = "default",
) -> Nexus:
    """Create the Praxis Nexus application.

    Sets up all API handlers, MCP tools, and WebSocket broadcasting.
    If no config is provided, loads from environment via get_config().

    Args:
        config: Optional PraxisConfig. If None, loaded from environment.
        session_manager: Optional pre-configured SessionManager.
        key_manager: Optional pre-configured KeyManager.
        key_id: Key identifier for signing operations.

    Returns:
        Configured Nexus application ready to start.
    """
    if config is None:
        from praxis.config import get_config

        config = get_config()

    # Ensure database tables exist before any handler can access persistence.
    # This must happen before handler registration so that request handlers
    # can safely read/write to the database from the first request onward.
    from praxis.persistence import get_db

    get_db()

    # Initialize the Nexus app
    app = Nexus(
        api_port=config.api_port,
        enable_auth=not config.dev_mode,
        cors_origins=config.cors_origins,
    )

    # Initialize core services if not provided
    if session_manager is None:
        from praxis.core.session import SessionManager

        if key_manager is None:
            from praxis.trust.keys import KeyManager

            key_manager = KeyManager(config.key_dir)
            if not key_manager.has_key(config.key_id):
                key_manager.generate_key(config.key_id)
            key_id = config.key_id

        session_manager = SessionManager(key_manager=key_manager, key_id=key_id)

    # Track per-session service instances
    deliberation_engines: dict[str, Any] = {}
    constraint_enforcers: dict[str, Any] = {}
    audit_chains: dict[str, Any] = {}

    # Shared HeldActionManager (single instance, persists to DB)
    from praxis.core.constraint import HeldActionManager

    held_action_manager = HeldActionManager(use_db=True)

    # Register session handlers
    _register_session_handlers(app, session_manager, audit_chains, key_manager, key_id)

    # Register deliberation handlers
    _register_deliberation_handlers(
        app, session_manager, deliberation_engines, audit_chains, key_manager, key_id
    )

    # Register constraint handlers
    _register_constraint_handlers(app, session_manager, constraint_enforcers)

    # Register held action handlers
    _register_held_action_handlers(app, held_action_manager)

    # Register trust handlers (audit chain, delegation)
    _register_trust_handlers(app, session_manager, audit_chains, key_manager, key_id)

    # Register verification handlers
    _register_verification_handlers(app, audit_chains, key_manager, key_id)

    # Register learning pipeline handlers (CO Layer 5)
    _register_learning_handlers(app)

    # Register Bainbridge Irony detection handlers (M11)
    _register_bainbridge_handlers(app)

    # Register MCP tools
    from praxis.api.mcp import register_mcp_tools

    register_mcp_tools(
        app,
        session_manager,
        deliberation_engines,
        constraint_enforcers,
        audit_chains=audit_chains,
        held_action_manager=held_action_manager,
        key_manager=key_manager,
        key_id=key_id,
    )

    # Register auth login endpoint
    _register_auth_handlers(app, config)

    # Register OAuth2 SSO routes (GitHub, Google)
    _register_oauth_handlers(app, config)

    # Initialize EventBroadcaster and mount WebSocket endpoint
    broadcaster = get_broadcaster()
    _mount_websocket(app, broadcaster, config=config)

    # Wire broadcaster into session handlers so state changes emit events
    _wire_broadcaster(app, session_manager, broadcaster)

    # Register RESTful URL routes via FastAPI router.
    # This gives web dashboards, mobile apps, and other HTTP clients
    # conventional REST paths (POST /sessions, GET /sessions/:id, etc.)
    # alongside the Nexus native paths (POST /workflows/{name}/execute).
    from praxis.api.routes import create_rest_router

    rest_router = create_rest_router(
        session_manager=session_manager,
        deliberation_engines=deliberation_engines,
        constraint_enforcers=constraint_enforcers,
        key_manager=key_manager,
        key_id=key_id,
        audit_chains=audit_chains,
        held_action_manager=held_action_manager,
        config=config,
    )
    # Mount REST routes via Nexus's add_route for Starlette-compatible endpoints
    try:
        from praxis.api.routes import create_rest_router

        rest_router = create_rest_router(
            session_manager=session_manager,
            deliberation_engines=deliberation_engines,
            constraint_enforcers=constraint_enforcers,
            key_manager=key_manager,
            key_id=key_id,
            audit_chains=audit_chains,
            held_action_manager=held_action_manager,
            config=config,
        )
        # Try include_router first (works if Nexus wraps FastAPI directly)
        try:
            app.include_router(rest_router, tags=["Praxis REST API"])
        except (AttributeError, TypeError):
            # Nexus wraps Starlette — mount via add_route for each REST endpoint
            for route in rest_router.routes:
                if hasattr(route, "path") and hasattr(route, "endpoint"):
                    for method in getattr(route, "methods", ["GET"]):
                        app.add_route(route.path, route.endpoint, methods=[method])
            logger.info("Mounted REST routes via Nexus add_route")
    except Exception as exc:
        logger.warning("REST route mounting skipped: %s (Nexus handlers still work)", exc)

    # Add JWT middleware if not dev mode
    if not config.dev_mode:
        from nexus.auth.jwt import JWTConfig, JWTMiddleware

        jwt_config = JWTConfig(
            secret=config.api_secret,
            exempt_paths=[
                "/health",
                "/docs",
                "/openapi.json",
                "/redoc",
                "/auth/login",
                "/auth/firebase",
                "/auth/providers",
                "/auth/github",
                "/auth/github/callback",
                "/auth/google",
                "/auth/google/callback",
            ],
        )
        app.add_middleware(JWTMiddleware, config=jwt_config)

    logger.info(
        "Praxis Nexus app created (port=%d, dev_mode=%s)",
        config.api_port,
        config.dev_mode,
    )

    return app


def _register_session_handlers(
    app: Nexus, session_manager, audit_chains, key_manager, key_id
) -> None:
    """Register session management handlers."""

    @app.handler("create_session", description="Create a new CO collaboration session")
    async def _create_session(
        workspace_id: str,
        domain: str = "coc",
        constraint_template: str = "moderate",
    ) -> dict:
        result = create_session_handler(
            session_manager=session_manager,
            workspace_id=workspace_id,
            domain=domain,
            constraint_template=constraint_template,
        )
        # Automatically create an audit chain for the new session
        if "session_id" in result and "error" not in result:
            session_id = result["session_id"]
            chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
            chain.append(
                action="session_created",
                actor="system",
                result="auto_approved",
                extra_payload={"workspace_id": workspace_id, "domain": domain},
            )
        return result

    @app.handler("list_sessions", description="List CO sessions")
    async def _list_sessions(
        workspace_id: str = "",
        state: str = "",
    ) -> dict:
        return list_sessions_handler(
            session_manager=session_manager,
            workspace_id=workspace_id or None,
            state=state or None,
        )

    @app.handler("get_session", description="Get a CO session by ID")
    async def _get_session(session_id: str) -> dict:
        return get_session_handler(session_manager=session_manager, session_id=session_id)

    @app.handler("pause_session", description="Pause an active session")
    async def _pause_session(session_id: str, reason: str = "") -> dict:
        return pause_session_handler(
            session_manager=session_manager,
            session_id=session_id,
            reason=reason,
        )

    @app.handler("resume_session", description="Resume a paused session")
    async def _resume_session(session_id: str) -> dict:
        return resume_session_handler(session_manager=session_manager, session_id=session_id)

    @app.handler("end_session", description="End (archive) a session")
    async def _end_session(session_id: str, summary: str = "") -> dict:
        return end_session_handler(
            session_manager=session_manager,
            session_id=session_id,
            summary=summary,
        )


def _register_deliberation_handlers(
    app: Nexus, session_manager, deliberation_engines, audit_chains, key_manager, key_id
) -> None:
    """Register deliberation capture handlers."""

    @app.handler("decide", description="Record a human decision")
    async def _decide(
        session_id: str,
        decision: str,
        rationale: str,
        actor: str = "human",
    ) -> dict:
        engine = _get_or_create_engine(session_id, deliberation_engines, key_manager, key_id)
        result = decide_handler(
            engine=engine,
            decision=decision,
            rationale=rationale,
            actor=actor,
        )
        # Create an audit anchor for the decision
        if "error" not in result:
            try:
                chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
                chain.append(
                    action="decision_recorded",
                    actor=actor,
                    result="auto_approved",
                    reasoning_hash=result.get("reasoning_hash"),
                    extra_payload={"record_id": result.get("record_id")},
                )
            except Exception:
                logger.warning(
                    "Failed to create audit anchor for decision in session %s", session_id
                )
        return result

    @app.handler("observe", description="Record an observation")
    async def _observe(
        session_id: str,
        observation: str,
        actor: str = "ai",
    ) -> dict:
        engine = _get_or_create_engine(session_id, deliberation_engines, key_manager, key_id)
        return observe_handler(
            engine=engine,
            observation=observation,
            actor=actor,
        )

    @app.handler("timeline", description="Get the deliberation timeline")
    async def _timeline(
        session_id: str,
        record_type: str = "",
    ) -> dict:
        engine = _get_or_create_engine(session_id, deliberation_engines, key_manager, key_id)
        return timeline_handler(
            engine=engine,
            record_type=record_type or None,
        )


def _register_constraint_handlers(app: Nexus, session_manager, constraint_enforcers) -> None:
    """Register constraint enforcement handlers."""

    @app.handler("get_constraints", description="Get session constraint envelope")
    async def _get_constraints(session_id: str) -> dict:
        return get_constraints_handler(
            session_manager=session_manager,
            session_id=session_id,
        )

    @app.handler(
        "update_constraints", description="Update session constraint envelope (tightening only)"
    )
    async def _update_constraints(
        session_id: str, new_constraints: str = "{}", rationale: str = ""
    ) -> dict:
        import json

        constraints = (
            json.loads(new_constraints) if isinstance(new_constraints, str) else new_constraints
        )
        return update_constraints_handler(
            session_manager=session_manager,
            session_id=session_id,
            new_constraints=constraints,
            rationale=rationale,
        )

    @app.handler("get_gradient", description="Get constraint gradient status")
    async def _get_gradient(session_id: str) -> dict:
        enforcer = _get_or_create_enforcer(session_id, session_manager, constraint_enforcers)
        return get_gradient_handler(enforcer=enforcer)


def _register_held_action_handlers(app: Nexus, held_action_manager) -> None:
    """Register held action management handlers."""

    @app.handler("approve_action", description="Approve a held action")
    async def _approve(held_id: str, approved_by: str = "api-user") -> dict:
        return approve_handler(
            held_action_manager=held_action_manager,
            held_id=held_id,
            approved_by=approved_by,
        )

    @app.handler("deny_action", description="Deny a held action")
    async def _deny(held_id: str, denied_by: str = "api-user") -> dict:
        return deny_handler(
            held_action_manager=held_action_manager,
            held_id=held_id,
            denied_by=denied_by,
        )

    @app.handler("list_held_actions", description="List pending held actions for a session")
    async def _list_held(session_id: str) -> dict:
        return list_held_actions_handler(
            held_action_manager=held_action_manager,
            session_id=session_id,
        )


def _register_trust_handlers(
    app: Nexus, session_manager, audit_chains, key_manager, key_id
) -> None:
    """Register trust chain handlers."""

    @app.handler("delegate", description="Create a delegation record")
    async def _delegate(
        session_id: str,
        delegate_id: str,
    ) -> dict:
        session = session_manager.get_session(session_id)
        return delegate_handler(
            session_id=session_id,
            parent_id=session.get("genesis_id", ""),
            parent_constraints=session["constraint_envelope"],
            delegate_id=delegate_id,
            delegate_constraints=session["constraint_envelope"],
            key_id=key_id,
            key_manager=key_manager,
            parent_hash=session.get("genesis_id", ""),
        )

    @app.handler("get_chain", description="Get audit chain status for a session")
    async def _get_chain(session_id: str) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
        return get_chain_handler(audit_chain=chain)


def _register_verification_handlers(app: Nexus, audit_chains, key_manager, key_id) -> None:
    """Register verification and export handlers."""

    @app.handler("verify_chain", description="Verify a trust chain")
    async def _verify(entries: str = "[]", public_keys: str = "{}") -> dict:
        import json

        return verify_handler(
            entries=json.loads(entries),
            public_keys=json.loads(public_keys),
        )

    @app.handler("export_bundle", description="Export a verification bundle for a session")
    async def _export(session_id: str) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
        return export_handler(
            audit_chain=chain,
            key_manager=key_manager,
            key_id=key_id,
            session_id=session_id,
        )

    @app.handler("audit_status", description="Get audit chain integrity status")
    async def _audit(session_id: str) -> dict:
        chain = _get_or_create_chain(session_id, audit_chains, key_manager, key_id)
        return audit_handler(audit_chain=chain)


# ---------------------------------------------------------------------------
# Learning handlers (CO Layer 5)
# ---------------------------------------------------------------------------


def _register_learning_handlers(app: Nexus) -> None:
    """Register CO Layer 5 learning pipeline handlers."""

    @app.handler("list_learning_proposals", description="List learning evolution proposals")
    async def _list_proposals(domain: str = "coc", status: str = "") -> dict:
        return list_learning_proposals_handler(
            domain=domain,
            status=status or None,
        )

    @app.handler("approve_learning_proposal", description="Approve a learning evolution proposal")
    async def _approve_proposal(
        proposal_id: str,
        domain: str = "coc",
        approved_by: str = "api-user",
    ) -> dict:
        return approve_learning_proposal_handler(
            domain=domain,
            proposal_id=proposal_id,
            approved_by=approved_by,
        )

    @app.handler("reject_learning_proposal", description="Reject a learning evolution proposal")
    async def _reject_proposal(
        proposal_id: str,
        domain: str = "coc",
        rejected_by: str = "api-user",
        reason: str = "",
    ) -> dict:
        return reject_learning_proposal_handler(
            domain=domain,
            proposal_id=proposal_id,
            rejected_by=rejected_by,
            reason=reason,
        )

    @app.handler("analyze_learning", description="Analyze observations for learning patterns")
    async def _analyze(domain: str = "coc") -> dict:
        return analyze_learning_handler(domain=domain)


# ---------------------------------------------------------------------------
# Bainbridge Irony detection handlers (M11)
# ---------------------------------------------------------------------------


def _register_bainbridge_handlers(app: Nexus) -> None:
    """Register Bainbridge's Irony detection and calibration handlers."""

    @app.handler("assess_fatigue", description="Assess approval fatigue risk for a session")
    async def _assess_fatigue(session_id: str) -> dict:
        return fatigue_handler(session_id=session_id)

    @app.handler("assess_capability", description="Assess practitioner capability")
    async def _assess_capability(practitioner_id: str = "human", domain: str = "coc") -> dict:
        return capability_handler(practitioner_id=practitioner_id, domain=domain)

    @app.handler(
        "constraint_review_status",
        description="Get constraint review status for a session",
    )
    async def _constraint_review(session_id: str) -> dict:
        return constraint_review_handler(session_id=session_id)

    @app.handler(
        "domain_calibration",
        description="Run constraint calibration analysis for a domain",
    )
    async def _domain_calibration(domain: str = "coc") -> dict:
        return calibration_handler(domain=domain)


# ---------------------------------------------------------------------------
# Auth handlers
# ---------------------------------------------------------------------------


def _register_auth_handlers(app: Nexus, config) -> None:
    """Register the login endpoint on the underlying FastAPI app.

    This is an API-only endpoint (not exposed via CLI or MCP) because
    login is inherently an HTTP operation. Rate limited to prevent
    brute-force attacks.
    """
    from praxis.api.rate_limit import RateLimiter

    login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=60)

    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    async def _login(request: Request) -> JSONResponse:
        # Extract client IP for rate limiting
        client_ip = getattr(request.client, "host", "unknown") if request.client else "unknown"

        if not login_rate_limiter.check(client_ip):
            return JSONResponse(
                {
                    "error": {
                        "type": "rate_limited",
                        "message": "Too many login attempts. Try again later.",
                    }
                },
                status_code=429,
            )

        body = await request.json()
        username = body.get("username", "")
        password = body.get("password", "")
        result = login_handler(
            username=username,
            password=password,
            config=config,
        )
        status = 401 if "error" in result else 200
        return JSONResponse(result, status_code=status)

    async def _firebase_login(request: Request) -> JSONResponse:
        """Authenticate via Firebase ID token (SSO-only login path)."""
        # Extract client IP for rate limiting
        client_ip = getattr(request.client, "host", "unknown") if request.client else "unknown"

        if not login_rate_limiter.check(client_ip):
            return JSONResponse(
                {
                    "error": {
                        "type": "rate_limited",
                        "message": "Too many login attempts. Try again later.",
                    }
                },
                status_code=429,
            )

        body = await request.json()
        id_token = body.get("id_token", "")
        result = await firebase_login_handler(
            id_token=id_token,
            config=config,
        )
        status = 401 if "error" in result else 200
        return JSONResponse(result, status_code=status)

    starlette_app = app._gateway.app
    starlette_app.routes.append(Route("/auth/login", _login, methods=["POST"]))
    starlette_app.routes.append(Route("/auth/firebase", _firebase_login, methods=["POST"]))
    logger.info("Registered auth endpoints: POST /auth/login, POST /auth/firebase")


# ---------------------------------------------------------------------------
# OAuth2 SSO handlers
# ---------------------------------------------------------------------------


def _register_oauth_handlers(app: Nexus, config) -> None:
    """Register OAuth2 SSO routes for GitHub and Google.

    Only registers routes for providers that have client IDs configured
    in the environment. If no providers are configured, this is a no-op.
    """
    from praxis.api.oauth import register_oauth_routes

    starlette_app = app._gateway.app
    register_oauth_routes(starlette_app, config)


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


def _mount_websocket(app: Nexus, broadcaster: EventBroadcaster, config=None) -> None:
    """Mount the WebSocket event streaming endpoint at /ws/events.

    Nexus wraps FastAPI, so we access the underlying FastAPI app to
    register a native WebSocket route. Clients connect here to receive
    real-time events for session state changes, constraint updates,
    held action resolutions, and deliberation records.

    In production mode, clients must provide a valid JWT token as a
    ``token`` query parameter (e.g. ``/ws/events?token=<jwt>``).
    In dev mode, connections are accepted without authentication.
    """
    import asyncio
    import json

    from starlette.routing import WebSocketRoute
    from starlette.websockets import WebSocketDisconnect

    async def websocket_events(websocket):
        # M3 (CORS): Check Origin header in production mode
        if config and not config.dev_mode and config.cors_origins:
            origin = websocket.headers.get("origin", "")
            if origin not in config.cors_origins:
                await websocket.close(code=4003, reason="Origin not allowed")
                return

        # Authenticate WebSocket connections in production mode
        if config and not config.dev_mode:
            token = websocket.query_params.get("token")
            if not token:
                await websocket.close(code=4001, reason="Authentication required")
                return
            try:
                from praxis.api.auth import decode_token

                decode_token(token, config.api_secret)
            except Exception:
                await websocket.close(code=4001, reason="Invalid token")
                return

        await websocket.accept()
        try:
            queue = broadcaster.subscribe()
        except RuntimeError:
            await websocket.close(code=4008, reason="Too many connections")
            return
        try:
            while True:
                event = await queue.get()
                await websocket.send_text(json.dumps(event))
        except WebSocketDisconnect:
            pass
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug("WebSocket connection closed: %s", exc)
        finally:
            broadcaster.unsubscribe(queue)

    starlette_app = app._gateway.app
    starlette_app.routes.append(WebSocketRoute("/ws/events", websocket_events))
    logger.info("Mounted WebSocket endpoint: /ws/events")


def _wire_broadcaster(app: Nexus, session_manager, broadcaster: EventBroadcaster) -> None:
    """Attach a listener to SessionManager so state changes emit WebSocket events.

    SessionManager supports an on_state_change callback. When fired,
    we broadcast the event to all connected WebSocket clients.
    """

    async def _broadcast_session_event(event_type: str, data: dict) -> None:
        """Fire-and-forget broadcast; errors are logged, never propagated."""
        try:
            await broadcaster.broadcast(event_type, data)
        except Exception as exc:
            logger.warning("Failed to broadcast %s event: %s", event_type, exc)

    # If the session manager supports a state-change hook, wire it up.
    # Otherwise, broadcasting will happen through explicit handler calls.
    if hasattr(session_manager, "on_state_change"):
        import asyncio

        def _sync_callback(session_id: str, old_state: str, new_state: str, session_data: dict):
            event_data = {
                "session_id": session_id,
                "old_state": old_state,
                "new_state": new_state,
                "data": session_data,
            }
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_broadcast_session_event("session_state_changed", event_data))
            except RuntimeError:
                # No running event loop (e.g. during tests) — skip broadcast
                pass

        session_manager.on_state_change = _sync_callback
        logger.info("Wired EventBroadcaster to SessionManager state-change hook")
    else:
        logger.debug(
            "SessionManager does not support on_state_change hook; "
            "WebSocket events will be broadcast through handler-level calls"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_MAX_CACHED_SESSIONS = 1000


def _evict_if_needed(cache: dict, session_manager=None) -> None:
    """Remove entries for archived or unknown sessions when the cache is too large.

    If there is no session_manager available (or if eviction of archived
    sessions is insufficient), the oldest entries are removed by insertion
    order as a fallback.

    Args:
        cache: The per-session service cache to evict from.
        session_manager: Optional SessionManager for checking session state.
    """
    if len(cache) <= _MAX_CACHED_SESSIONS:
        return

    to_remove: list[str] = []

    # First pass: remove archived or unknown sessions
    if session_manager is not None:
        for sid in list(cache.keys()):
            try:
                s = session_manager.get_session(sid)
                if s.get("state") == "archived":
                    to_remove.append(sid)
            except (KeyError, Exception):
                to_remove.append(sid)
            if len(cache) - len(to_remove) <= _MAX_CACHED_SESSIONS:
                break

    # Second pass: if still over limit, remove oldest entries
    if len(cache) - len(to_remove) > _MAX_CACHED_SESSIONS:
        for sid in list(cache.keys()):
            if sid not in to_remove:
                to_remove.append(sid)
            if len(cache) - len(to_remove) <= _MAX_CACHED_SESSIONS:
                break

    for sid in to_remove:
        cache.pop(sid, None)

    if to_remove:
        logger.debug("Evicted %d cached session service(s)", len(to_remove))


def _get_or_create_engine(session_id, engines, key_manager, key_id):
    """Get or lazily create a DeliberationEngine for a session."""
    if session_id not in engines:
        from praxis.core.deliberation import DeliberationEngine

        _evict_if_needed(engines)
        engines[session_id] = DeliberationEngine(
            session_id=session_id,
            key_manager=key_manager,
            key_id=key_id,
        )
    return engines[session_id]


def _get_or_create_enforcer(session_id, session_manager, enforcers):
    """Get or lazily create a ConstraintEnforcer for a session."""
    if session_id not in enforcers:
        from praxis.core.constraint import ConstraintEnforcer

        _evict_if_needed(enforcers, session_manager)
        session = session_manager.get_session(session_id)
        enforcers[session_id] = ConstraintEnforcer(
            session["constraint_envelope"],
            session_id=session_id,
        )
    return enforcers[session_id]


def _get_or_create_chain(session_id, chains, key_manager, key_id):
    """Get or lazily create an AuditChain for a session."""
    if session_id not in chains:
        from praxis.trust.audit import AuditChain

        _evict_if_needed(chains)
        chains[session_id] = AuditChain(
            session_id=session_id,
            key_id=key_id,
            key_manager=key_manager,
        )
    return chains[session_id]
