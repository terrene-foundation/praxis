# Security Audit — Praxis v0.1.0

**Date**: 2026-03-15
**Scope**: Full codebase (src/praxis/, apps/web/, apps/desktop/, apps/mobile/, packages/praxis_shared/)

## Summary

| Severity | Count |
| -------- | ----- |
| CRITICAL | 3     |
| HIGH     | 7     |
| MEDIUM   | 8     |
| LOW      | 5     |
| PASSED   | 23    |

## Critical Findings

### C1. Path Traversal in KeyManager via key_id

`keys.py` — key_id used directly in filesystem paths without sanitization. `../../etc/passwd` attack possible.
**Fix**: Add validate_id() rejecting `/`, `\`, `..`, null bytes.

### C2. NaN/Infinity Bypass in Constraint Utilization

`gradient.py`, `constraint.py` — NaN comparisons silently return AUTO_APPROVED.
**Fix**: Add `math.isfinite()` check at top of utilization functions.

### C3. Mutable Security-Critical Dataclasses

GenesisRecord, DelegationRecord, AuditAnchor not frozen — fields can be mutated after signing.
**Fix**: Add `frozen=True` to all trust chain dataclasses.

## High Findings

- H1: Database URL logged with credentials in plaintext
- H2: Unbounded in-memory collections (memory exhaustion)
- H3: No API-level rate limiting
- H4: WebSocket auth token in URL query string
- H5: Error messages expose internal details in production
- H6: JWT token stored in localStorage (XSS risk)
- H7: Unvalidated JSON size in verify_chain handler

## Passed Checks (23)

All secrets from .env, Ed25519 via cryptography library, SHA-256 via hashlib, JCS via jcs package, no eval/exec, no SQL injection, HTML escaping in reports and bundles, Flutter secure storage, verification bundles contain only public keys, no CDN dependencies in bundles.
