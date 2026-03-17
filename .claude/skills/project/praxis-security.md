# Praxis Security Patterns

## Overview

Praxis implements five defense-in-depth layers to protect the trust infrastructure, persistence layer, and API surface.

## Layer 1: SQL Injection Prevention (db_ops)

Column name validation via regex: `^[a-zA-Z_][a-zA-Z0-9_]{0,63}$`. All dict keys passed to `db_create`, `db_update`, `db_list`, and `db_count` are validated. Violations raise `ValueError`. All SQL values use parameterized queries (`?` placeholders).

## Layer 2: Rate Limiting (api/rate_limit.py)

In-memory sliding window rate limiter on authentication endpoints. Login: 5 attempts per 60-second window per IP address. Exceeding the limit returns a rate_limited error immediately.

## Layer 3: Timing-Safe Auth (api/auth.py)

JWT validation uses `hmac.compare_digest` for timing-safe comparison. This prevents timing attacks that could extract secret information by measuring response times.

In dev mode, the API secret is generated randomly (not hardcoded), preventing accidental production deployment with a known secret.

## Layer 4: Error Sanitization (api/errors.py)

Error messages returned to clients never include internal details. Stack traces, file paths, and database errors are replaced with generic messages. `error_from_exception()` sanitizes all messages before returning to clients.

## Layer 5: Key File Protection (trust/keys.py)

- **Path traversal prevention**: key*id validated against `^[a-zA-Z0-9*\-\.]+$`
- **Symlink detection**: key file paths verified not to be symlinks before read/write
- **File permissions**: private keys set to mode 0o600 (owner read/write only)
- **Key zeroization**: private key bytes overwritten in memory after signing

## Additional Security Patterns

### WebSocket Authentication

WebSocket connections require authentication on establishment. CORS origins respected from config.

### Frozen Records

Trust records (GenesisRecord, DelegationRecord, AuditAnchor) are `@dataclass(frozen=True)`, preventing post-signing mutation.

### NaN/Inf Guard

Non-finite utilization values map to BLOCKED. Prevents auto-approving on corrupted math.

### Bundle serve.py Localhost Binding

The verification bundle's `serve.py` binds to `127.0.0.1` only, not `0.0.0.0`.

### JSON-RPC Line Size Limit

MCP proxy drops lines exceeding 10 MB to prevent memory exhaustion.

### Constraint Tightening Invariant

Constraints can only be tightened, never loosened, at both session and delegation levels.

### Learning Proposal Human Gate

Evolution proposals from the learning pipeline are NEVER auto-applied.
