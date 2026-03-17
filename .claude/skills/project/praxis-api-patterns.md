# Praxis API Patterns

## Overview

The Praxis API is built with Kailash Nexus, exposing endpoints on three channels simultaneously: REST API, CLI, and MCP. All business logic lives in plain handler functions that are framework-independent.

## Key Files

| File                | Purpose                                                                   |
| ------------------- | ------------------------------------------------------------------------- |
| `api/app.py`        | `create_app()` -- Nexus application factory                               |
| `api/handlers.py`   | 29 handler functions (plain functions, no framework dependency)           |
| `api/routes.py`     | RESTful URL routing (`create_rest_router()`)                              |
| `api/mcp.py`        | 5 MCP tools for AI assistant integration                                  |
| `api/websocket.py`  | `EventBroadcaster` for real-time updates                                  |
| `api/auth.py`       | JWT token create/decode/verify + dev-mode bypass, timing-safe comparison  |
| `api/errors.py`     | `PraxisAPIError` + `error_from_exception()` mapping, message sanitization |
| `api/rate_limit.py` | `RateLimiter` -- sliding window rate limiting for auth endpoints          |
| `api/middleware.py` | `enforce_constraints()` -- pre-handler constraint gate                    |

## 29 Handler Categories

**Session** (7): login, create_session, list_sessions, get_session, pause_session, resume_session, end_session

**Deliberation** (3): decide, observe, timeline

**Constraint** (3): get_constraints, update_constraints, get_gradient

**Trust** (5): delegate, approve, deny, list_held_actions, get_chain

**Verification** (3): verify, export, audit

**Learning** (4): list_learning_proposals, approve_learning_proposal, reject_learning_proposal, analyze_learning

**Bainbridge/Calibration** (4): fatigue, capability, constraint_review, calibration

## RESTful Routes

Both URL schemes work simultaneously:

- `POST /workflows/create_session/execute` (Nexus native)
- `POST /sessions` (RESTful via routes.py)

Key routes include: `/auth/login` (rate limited), `/sessions/*`, `/learning/*`, `/practitioners/{id}/capability`, `/domains/{domain}/calibration`, `/health`.

## Rate Limiting

`RateLimiter` on login endpoint: 5 attempts per 60-second window per IP. In-memory sliding window.

## Enforcement Middleware

```python
result = enforce_constraints(enforcer, held_manager, session_id, action, resource)
if result is not None:
    return result  # BLOCKED (403) or HELD (202)
```

## Security Patterns

- Error message sanitization: no internal details in API responses
- WebSocket authentication on connection establishment
- CORS on WebSocket from config
- Timing-safe auth with `hmac.compare_digest`
- Random dev secret (not hardcoded)

## Error Handling

All errors are `PraxisAPIError` instances returned as `{"error": {"type": "...", "message": "..."}}`. Exception mapping via `error_from_exception()`:

- KeyError -> 404, ValueError -> 400, InvalidStateTransitionError -> 409, etc.
