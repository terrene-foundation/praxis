# Vision Gap Audit — What We May Have Missed

**Date**: 2026-03-16
**Status**: Complete
**Method**: Three-agent parallel audit (deep-analyst, co-expert, value-auditor) against full codebase

---

## Executive Summary

Praxis went from 9 lines of code to 7,371 lines of production Python with 677 passing tests, 54 TypeScript files (web dashboard), and 99 Dart files (desktop + mobile). The CLI value chain works end-to-end: init, session, decide, status, export, verify — all with real Ed25519 cryptography, JCS canonical serialization, and SHA-256 hash chains.

However, there is a fundamental gap between tested component logic and an operational end-to-end product. Every data store is in-memory (lost on restart), domain YAML configs are never consulted during session creation, frontends point at URL patterns that don't match the backend, the MCP "medium" architecture is not implemented (tools are alongside, not intercepting), and WebSocket is defined but never mounted.

---

## What Actually Works Today

| Capability                                   | Status   | Evidence                                                             |
| -------------------------------------------- | -------- | -------------------------------------------------------------------- |
| `praxis init` creates workspace with genesis | Works    | CLI creates .praxis/ directory, Ed25519 keypair, genesis record      |
| `praxis session start/end` lifecycle         | Works    | Full state machine (creating → active → paused → archived)           |
| `praxis decide` with crypto signing          | Works    | JCS-canonicalized, SHA-256 hashed, hash-chained deliberation records |
| `praxis status` constraint dashboard         | Works    | Five-dimension constraint gauges with Rich formatting                |
| `praxis export` verification bundle          | Works    | Self-contained ZIP with HTML viewer + JS verifier                    |
| `praxis verify` chain validation             | Works    | Ed25519 signature verification, hash chain integrity                 |
| `praxis delegate` with tightening            | Works    | Monotonic constraint shrinking enforced                              |
| 5-dimensional constraint enforcement         | Works    | Financial, Operational, Temporal, Data Access, Communication         |
| Verification gradient (4 levels)             | Works    | AUTO_APPROVED / FLAGGED / HELD / BLOCKED                             |
| Trust chain (genesis → delegation → anchor)  | Works    | Cryptographic chain with integrity verification                      |
| 6 domain YAML configurations                 | Defined  | Schema-validated, loadable, but not influencing runtime              |
| 677 tests passing                            | Verified | 3 rounds of red teaming, round 3: 0 bugs in 101 tests                |

---

## Critical Gaps (Product Doesn't Work End-to-End)

### Gap 1: All Data Is In-Memory — Lost on Restart

**Severity: CRITICAL**

SessionManager, DeliberationEngine, ConstraintEnforcer, HeldActionManager, AuditChain — all store state in Python dicts and lists. DataFlow models are defined in `persistence/models.py`, `get_db()` is wired in `persistence/__init__.py`, but no core service calls `get_db()`. The queries module explicitly states: "For now, these work with in-memory stores."

**Impact**: No session survives a server restart. No demo can span two terminal sessions. No real-world use is possible.

### Gap 2: Frontend-Backend URL Mismatch

**Severity: CRITICAL**

The web dashboard calls RESTful URLs (`POST /sessions`, `GET /sessions/:id`). Flutter apps call `/api/sessions`. But Nexus maps handlers to its own URL scheme (handler-name based). Every frontend API call will 404 against the actual backend.

### Gap 3: MCP Is "Alongside", Not "Medium"

**Severity: HIGH**

CLAUDE.md states "Trust infrastructure must be the medium through which AI operates." But MCP tools (`trust_check`, `trust_record`) are voluntary — the AI must choose to call them. There is no MCP proxy/stdio transport that sits BETWEEN an AI assistant and its tools, intercepting and enforcing constraints before forwarding. The AI is still self-policing.

### Gap 4: Domain YAML Never Influences Session Creation

**Severity: HIGH**

`SessionManager.create_session()` uses hardcoded `CONSTRAINT_TEMPLATES` (strict/moderate/permissive). The 6 domain YAML files define different, domain-specific templates but are never loaded during session creation. `DomainLoader` is only used by `praxis domain list` and `praxis domain validate` CLI commands.

### Gap 5: No WebSocket Endpoint Mounted

**Severity: HIGH**

`EventBroadcaster` exists with subscribe/unsubscribe/broadcast methods. But `create_app()` never registers a WebSocket route, never mounts the broadcaster, and never calls `broadcast()` from any handler. Both web and mobile frontends expect `/ws/events` that doesn't exist.

### Gap 6: No Authentication Login Endpoint

**Severity: HIGH**

Frontends call `POST /auth/login`. `auth.py` provides `create_token()` and `decode_token()`, but no handler calls them. Dev mode bypasses auth, but production auth is broken.

---

## Major Gaps (Features Partially Working or Missing)

### Gap 7: Constraints Are Advisory, Not Enforced in API Flow

**Severity: MAJOR**

The `trust_check` MCP tool evaluates constraints but doesn't block. The AI receives the verdict but is free to ignore it. No middleware intercepts actual operations and refuses blocked actions. `HeldActionManager` exists but is never wired into any handler.

### Gap 8: Temporal and Financial Constraints Are Fiction

**Severity: MAJOR**

Temporal: `elapsed_minutes` starts at 0 and never updates. No timer, no middleware, no periodic task. A session could run 24 hours under a 30-minute constraint.

Financial: `current_spend` starts at 0 and never increments. No operation feeds cost data into the enforcer.

### Gap 9: Audit Chain Not Created During API Sessions

**Severity: MAJOR**

`AuditChain` works in isolation and via CLI, but `create_app()` never instantiates one per session. The `export_handler` needs an `audit_chain` but is never registered as a Nexus handler.

### Gap 10: No Runtime Phase Tracking

**Severity: MAJOR**

Domain YAMLs define phases with `approval_gate: true` (COC: analyze, plan, implement, validate, codify). But no session lifecycle code references phases, no state machine enforces transitions, and no approval gate blocks progression.

### Gap 11: Observation Targets Are Dead Configuration

**Severity: MEDIUM**

All 6 domain YAMLs declare `observation_targets` (required by schema). No code reads or acts on them. They are validated configuration with no consumers.

---

## CO Methodology Compliance

| CO Layer              | Status               | Key Finding                                                                                       |
| --------------------- | -------------------- | ------------------------------------------------------------------------------------------------- |
| Layer 1: Intent       | Conformant           | Domain engine supports agent specialization                                                       |
| Layer 2: Context      | Partially conformant | No institutional vs. generic knowledge distinction, no progressive disclosure                     |
| Layer 3: Guardrails   | Conformant (in CLI)  | Constraint enforcer works in CLI path; not wired in API path                                      |
| Layer 4: Instructions | Partially conformant | Phase definitions exist; no runtime enforcement                                                   |
| Layer 5: Learning     | **Not conformant**   | Zero runtime implementation. No observation pipeline, no pattern analysis, no evolution proposals |

### Eight Previously Identified CO Gaps — Status

| #   | Gap                                                | Status                                                           |
| --- | -------------------------------------------------- | ---------------------------------------------------------------- |
| 1   | Layer 5 (Learning) not implemented                 | **Still open** — zero L5 code exists                             |
| 2   | Anti-amnesia mechanism missing                     | **Still open** — no injection mechanism                          |
| 3   | Bainbridge's Irony not addressed                   | **Still open** — HeldActionManager has raw data but no analysis  |
| 4   | No constraint calibration feedback                 | **Partially addressed** — events logged, no analysis pipeline    |
| 5   | Knowledge portability not specified                | **Partially addressed** — session export works; L5 knowledge not |
| 6   | No institutional vs. generic knowledge distinction | **Still open**                                                   |
| 7   | Progressive disclosure enforcement missing         | **Still open** — no phase tracking to drive it                   |
| 8   | Defense in depth not modeled                       | **Still open** — single prevention layer                         |

### New CO Gaps Discovered

- **Duplicated gradient engine**: `core/constraint.py` and `trust/gradient.py` both implement the same gradient thresholds independently — consistency risk
- **Observation target consumers**: Schema requires them, runtime ignores them
- **Phase enforcement**: Defined in YAML, not enforced at runtime

---

## Value Proposition Re-Evaluation

### What Changed

| Issue (March 15)                            | Severity Then | Status Now                                                               |
| ------------------------------------------- | ------------- | ------------------------------------------------------------------------ |
| No working software (9 lines)               | CRITICAL      | **RESOLVED** — 7,371 lines, full CLI works                               |
| Dependencies not on PyPI                    | CRITICAL      | **RESOLVED** — all 6 packages published                                  |
| README describes non-existent functionality | HIGH          | **MOSTLY RESOLVED** — README matches CLI reality                         |
| Scope too large                             | HIGH          | **PARTIALLY RESOLVED** — impressive execution, but frontends unconnected |
| Behavior change required                    | MEDIUM        | Unchanged — inherent to the product                                      |

### New Issue: PyPI Package Name Conflict

The `praxis` package name on PyPI is already taken by a different project (version 1.4.0, unrelated). `pip install praxis` installs the wrong thing.

### What Would Make This Demo-Ready (2-Week Sprint)

**Week 1: Make the backend operational**

1. Wire DataFlow persistence (or file-based persistence) so state survives restarts
2. Load domain YAML templates during session creation (replace hardcoded templates)
3. Wire temporal auto-tracking and financial spend accumulation
4. Mount WebSocket endpoint and wire EventBroadcaster

**Week 2: Connect frontends**

1. Reconcile REST URL scheme between Nexus handlers and frontend API clients
2. Register missing handlers (update_constraints, export, auth/login)
3. Test web dashboard against running backend; fix integration issues
4. Resolve PyPI naming (publish as `praxis-co` or `terrene-praxis`)

### Single Most Impactful Next Step

**File-based or DataFlow session persistence.** Everything downstream depends on it: web dashboard, multi-session demos, approval workflows, any demo that spans more than one terminal session. The CLI already writes some state to `.praxis/`, so the pattern exists.

---

## Decision Points for You

These require your input before implementation:

1. **Persistence strategy**: Wire the existing DataFlow models into SessionManager (full database), or start with file-based persistence to `.praxis/` directory (simpler, faster)?

2. **MCP medium vs. alongside**: Should we build the MCP proxy (stdio transport that intercepts AI tool calls and enforces constraints before forwarding) now, or accept the current "AI voluntarily calls trust_check" model for v0.1.0?

3. **Domain YAML authority**: Should session creation load constraint templates from domain YAML files, making the 6 domain configs actually drive behavior?

4. **PyPI package name**: Publish as `praxis-co`, `terrene-praxis`, or something else? The `praxis` name is taken.

5. **Phase enforcement**: Should workflow phases (with approval gates) be enforced in the session state machine? This would add phase-based transitions and block progression until approval.

6. **Layer 5 timing**: Is the Learning layer (observation pipeline, pattern analysis, evolution proposals) work for v0.1.0, or a v0.2.0 goal?

---

## Success Criteria

Praxis is "vision-complete" when:

1. `praxis init && praxis session start && praxis decide && praxis export` produces a valid bundle — **and survives a server restart**
2. `praxis serve` starts a server where the web dashboard can create sessions, record decisions, see constraint gauges, and export bundles
3. An MCP client (Claude Code) connects to Praxis and has tool calls intercepted and constraint-checked **before** execution
4. Creating a session with `--domain coe --template strict` uses COE's strict constraints, not hardcoded ones
5. The verification bundle opens in a browser and verifies the chain client-side with real Ed25519
6. Temporal and financial constraints update automatically during a session
