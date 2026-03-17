# Praxis Architecture

## Module Map

```
src/praxis/
  config.py             — Single source of truth for .env config (PraxisConfig frozen dataclass)
  cli.py                — Click CLI entry point, workspace state in .praxis/
  core/
    session.py          — SessionManager: state machine (CREATING->ACTIVE->PAUSED->ARCHIVED)
    deliberation.py     — DeliberationEngine: hash-chained decision/observation/escalation records
    constraint.py       — ConstraintEnforcer: 5-dimension evaluation + HeldActionManager
    domain.py           — Re-exports from domains/loader.py
    learning.py         — LearningPipeline: CO Layer 5 observe-analyze-propose-formalize
    learning_observers.py — Observer functions: wire session activity into learning pipeline
    anti_amnesia.py     — AntiAmnesiaInjector: priority-filtered context reminders
    bainbridge.py       — FatigueDetector, CapabilityTracker, ConstraintReviewTracker
    calibration.py      — CalibrationAnalyzer: false positive/negative, boundary pressure
    rules.py            — DomainRuleEngine: procedural rule evaluation (warnings, not blocks)
    audit_review.py     — SessionAuditReviewer: quality scoring (0-100) for completed sessions
  trust/
    keys.py             — KeyManager: Ed25519 generate/sign/verify, symlink protection, key zeroization
    genesis.py          — GenesisRecord (frozen): root of trust for sessions
    delegation.py       — DelegationRecord (frozen): constraint-tightening delegation chains
    audit.py            — AuditChain: append-only hash-chained audit anchors, DB persistence
    gradient.py         — Pure function: evaluate_action -> GradientVerdict (consolidated single source)
    verify.py           — verify_chain: full chain integrity verification
    crypto.py           — canonical_hash (JCS+SHA256), sign_hash, verify_signature
  api/
    app.py              — create_app(): Nexus application factory
    handlers.py         — 29 handler functions for all API endpoints
    routes.py           — RESTful URL routing (FastAPI APIRouter, conventional paths)
    mcp.py              — 5 MCP tools (trust_check/record/escalate/envelope/status)
    websocket.py        — EventBroadcaster for real-time updates
    auth.py             — JWT create/decode/verify, timing-safe comparison
    errors.py           — PraxisAPIError + error_from_exception, message sanitization
    rate_limit.py       — RateLimiter: sliding window, auth endpoint protection
    middleware.py       — enforce_constraints: pre-handler constraint gate
  mcp/
    proxy.py            — PraxisProxy: MCP stdio proxy, tool interception, auto-capture
  persistence/
    __init__.py         — get_db(), create_tables_sync(), register_models()
    models.py           — 9 DataFlow models (Session, DeliberationRecord, ConstraintEvent,
                           TrustChainEntry, Workspace, HeldAction, LearningObservation,
                           LearningPattern, LearningEvolutionProposal)
    db_ops.py           — Sync CRUD helpers (raw sqlite3), column validation, JSON serialization
    queries.py          — Higher-level query functions with pagination
    archive.py          — Session export/import
  export/
    bundle.py           — BundleBuilder: self-contained ZIP verification bundles
    report.py           — AuditReportGenerator: HTML and JSON reports
    templates/          — HTML/JS/CSS for client-side verification
  domains/
    loader.py           — DomainLoader: discover, load, validate, cache; knowledge helpers
    schema.py           — JSON Schema for domain validation
    coc/coe/cog/cor/cocomp/cof/ — 6 domain YAML configurations
```

## Dependency Flow

```
config.py <-- everything (single source of truth for all settings)
trust/    <-- core/ (session uses genesis, deliberation uses audit/crypto)
core/     <-- api/ (handlers use SessionManager, DeliberationEngine, ConstraintEnforcer)
core/     <-- cli.py (CLI commands call core services directly)
core/     <-- mcp/ (proxy uses ConstraintEnforcer, HeldActionManager)
domains/  <-- core/ (session loads domain templates; learning loads observation targets)
export/   <-- api/ (export handler uses BundleBuilder)
export/   <-- cli.py (CLI bundle export wires to BundleBuilder)
persistence/ <-- core/ (constraint, learning, bainbridge persist via db_ops)
persistence/ <-- trust/ (audit chain persists via TrustChainEntry)
```

## Key Design Decisions

These are fundamental architectural choices. See `workspaces/praxis/decisions.yml` for the full list.

### Trust as Medium, Not Camera

Constraint enforcement is IN the execution path. Actions flow through the trust layer -- they are not observed after the fact. The ConstraintEnforcer returns a verdict (AUTO_APPROVED, FLAGGED, HELD, BLOCKED) that the caller must respect. The MCP proxy embodies this: every tool call passes through constraint evaluation before reaching any downstream server.

### Frozen Dataclasses for Trust Records

GenesisRecord, DelegationRecord, AuditAnchor, ConstraintVerdict, and DomainConfig are all `@dataclass(frozen=True)`. This prevents post-signing mutation that would bypass verification.

### Normative Gradient Thresholds

The CO specification defines the gradient thresholds as normative values. They are hardcoded at 70/90/100 and must not be made configurable:

- < 70% utilization: AUTO_APPROVED
- 70-89%: FLAGGED
- 90-99%: HELD
- > = 100%: BLOCKED

### Domain Configurations Are Pure YAML

No code execution in domain configs. YAML files define constraint templates, phases, capture rules, knowledge, anti-amnesia rules, and domain rules. Validated against JSON Schema at load time.

### Raw sqlite3 with DataFlow Schema

DataFlow handles schema creation (model registration + `create_tables_sync()`). `db_ops.py` handles reads/writes using raw sqlite3 against the same database file. This avoids async connection lifecycle issues while maintaining a single schema source of truth.

### Framework-Independent Handlers

All 29 API handler functions in handlers.py are plain functions that take service instances and return dicts. They are decoupled from Nexus, FastAPI, or any web framework -- testable in isolation.

### CO Layer 5 Learning Pipeline

The observe-analyze-propose-formalize cycle allows domain configurations to evolve based on observed patterns. Five pattern detectors identify misconfigured constraints. All proposals require human approval -- nothing is auto-applied.

### Five Defense-in-Depth Layers

Security is implemented in five layers:

1. Column validation (SQL injection prevention via regex in db_ops)
2. Rate limiting on authentication endpoints
3. Timing-safe comparison for auth tokens
4. Error message sanitization (no internal details in API responses)
5. Key file protections (symlink detection, permissions, path traversal prevention)

## Data Flow: Action Evaluation

```
Client sends action
  -> api/handlers.py (or cli.py, or mcp/proxy.py)
    -> ConstraintEnforcer.evaluate(action, resource, context)
      -> Evaluates ALL 5 dimensions (never short-circuits)
      -> Returns MOST RESTRICTIVE verdict
    -> If HELD: HeldActionManager.hold() -- waits for human approval
    -> If BLOCKED: Return error to client
    -> If AUTO_APPROVED/FLAGGED: Proceed
      -> AuditChain.append() -- signed audit anchor (persisted to DB)
      -> DeliberationEngine.record_*() -- hash-chained record
      -> EventBroadcaster.broadcast() -- WebSocket notification
      -> Learning observers record observation (non-blocking)
```

## Data Flow: Session Lifecycle

```
create_session(workspace_id, domain, template)
  -> Resolve constraint envelope from template
  -> create_genesis(session_id, authority_id, key_id, key_manager, constraints)
  -> Store session with state=ACTIVE (in-memory + DB)
  -> Return session dict

pause_session / resume_session / end_session
  -> Validate state transition against VALID_TRANSITIONS
  -> Update state, timestamp
  -> Persist to DB
  -> Return updated session dict

update_constraints
  -> Validate tightening (_is_tightening checks all 5 dimensions)
  -> Update constraint_envelope
  -> Persist to DB
  -> Return updated session dict
```
