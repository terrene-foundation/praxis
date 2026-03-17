# Praxis Codebase Reference

Praxis is the Terrene Foundation's open-source CO (Cognitive Orchestration) platform. It provides session management, trust infrastructure, deliberation capture, constraint enforcement, a continuous learning pipeline, and MCP proxy mediation for human-AI collaboration workflows. Version 0.1.0, Apache 2.0 licensed.

## Architecture Rules

### DO

- All configuration from `.env` via `config.py` (PraxisConfig frozen dataclass). No other module reads `os.environ`.
- All trust records are frozen dataclasses (GenesisRecord, DelegationRecord, AuditAnchor, ConstraintVerdict, DomainConfig). Never mutate after creation.
- All handler functions are plain functions returning dicts. No framework coupling.
- All 5 constraint dimensions are always evaluated. Never short-circuit.
- All trust chain signatures use Ed25519. All canonical hashing uses JCS (RFC 8785) + SHA-256.
- Constraints can only be tightened, never loosened. Enforced at both session and delegation levels.
- All learning proposals require human approval. Nothing is auto-applied.
- All column names validated via regex before SQL use. Parameterized queries everywhere.

### DO NOT

- Do not make gradient thresholds configurable. 70/90/100 are normative CO values.
- Do not execute code in domain configurations. Domains are pure YAML validated against JSON Schema.
- Do not use `LocalRuntime` in containers. Use `AsyncLocalRuntime`.
- Do not hardcode secrets, model names, or API keys. Everything from `.env`.
- Do not reference any proprietary product, commercial entity, or non-Foundation codebase.
- Do not treat NaN/Infinity utilization as AUTO_APPROVED. Non-finite values map to BLOCKED.
- Do not let observation failures propagate. Learning observers catch all exceptions silently.
- Do not auto-apply learning proposals. Human approval gate is mandatory.

## Module Map

```
src/praxis/
  config.py              PraxisConfig: frozen dataclass, singleton via get_config()
  cli.py                 Click CLI: workspace state in .praxis/, Rich output
  core/
    session.py           SessionManager: CREATING->ACTIVE->PAUSED->ARCHIVED state machine
    deliberation.py      DeliberationEngine: JCS+SHA256 hash-chained records
    constraint.py        ConstraintEnforcer: 5-dim eval + HeldActionManager, CONSTRAINT_DIMENSIONS
    domain.py            Re-exports from domains/loader.py
    learning.py          LearningPipeline: CO Layer 5 observe-analyze-propose-formalize
    learning_observers.py Observer functions: wire session activity into learning pipeline
    anti_amnesia.py      AntiAmnesiaInjector: priority-filtered context reminders
    bainbridge.py        FatigueDetector, CapabilityTracker, ConstraintReviewTracker
    calibration.py       CalibrationAnalyzer: false positive/negative, boundary pressure
    rules.py             DomainRuleEngine: procedural rule evaluation (warnings, not blocks)
    audit_review.py      SessionAuditReviewer: quality scoring (0-100) for sessions
  trust/
    keys.py              KeyManager: Ed25519 generate/sign/verify, symlink protection, key zeroization
    genesis.py           create_genesis -> frozen GenesisRecord
    delegation.py        create_delegation -> frozen DelegationRecord, validate_constraint_tightening
    audit.py             AuditChain: append-only signed hash chain, DB persistence via TrustChainEntry
    gradient.py          evaluate_action -> GradientVerdict (pure function, consolidated single source)
    verify.py            verify_chain: full chain verification from exported data
    crypto.py            canonical_hash, sign_hash, verify_signature
  api/
    app.py               create_app(): Nexus application factory
    handlers.py          29 handler functions (framework-independent)
    routes.py            RESTful URL routing (FastAPI APIRouter, conventional paths)
    mcp.py               5 MCP tools: trust_check/record/escalate/envelope/status
    websocket.py         EventBroadcaster: real-time pub/sub
    auth.py              JWT create/decode/verify + dev-mode bypass, timing-safe comparison
    errors.py            PraxisAPIError + error_from_exception, message sanitization
    rate_limit.py        RateLimiter: sliding window, auth endpoint protection
    middleware.py        enforce_constraints: pre-handler constraint gate
  mcp/
    proxy.py             PraxisProxy: MCP stdio proxy, tool interception, auto-capture
  persistence/
    __init__.py          get_db(), create_tables_sync(), register_models()
    models.py            9 DataFlow models (Session, DeliberationRecord, ConstraintEvent,
                          TrustChainEntry, Workspace, HeldAction, LearningObservation,
                          LearningPattern, LearningEvolutionProposal)
    db_ops.py            Sync CRUD helpers (raw sqlite3), column validation, JSON serialization
    queries.py           Higher-level query interface with pagination
    archive.py           Session export/import
  export/
    bundle.py            BundleBuilder: self-contained ZIP verification bundles
    report.py            AuditReportGenerator: HTML and JSON reports
  domains/
    loader.py            DomainLoader: discover, load, validate, cache; knowledge helpers
    schema.py            JSON Schema for domain validation
    coc/coe/cog/cor/cocomp/cof/  6 domain YAML configurations
```

## Testing

- 1141 tests across unit, integration, and end-to-end tiers
- Run with: `PRAXIS_DEV_MODE=true pytest`
- Dev mode is required because tests do not set production secrets
- Root `conftest.py` auto-loads `.env` for pytest
- Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- Test paths: `tests/unit/`, `tests/integration/`, `tests/e2e/`

## Security Patterns

### Five Defense-in-Depth Layers

1. **Column validation** (db*ops.py): regex `^[a-zA-Z*][a-zA-Z0-9_]{0,63}$` on all dict keys prevents SQL injection
2. **Rate limiting** (rate_limit.py): sliding window on auth endpoints (5 attempts/60s per IP)
3. **Timing-safe auth** (auth.py): `hmac.compare_digest` for JWT comparison; random dev secret
4. **Error sanitization** (errors.py): no internal details in API responses
5. **Key file protection** (keys.py): symlink detection, mode 600, path traversal prevention, key zeroization

### Frozen Records

All trust records (GenesisRecord, DelegationRecord, AuditAnchor) are `@dataclass(frozen=True)`. Any attempt to mutate raises `FrozenInstanceError`. This prevents post-signing tampering.

### NaN/Infinity Guards

Both `_gradient_for_utilization()` (constraint.py) and `_utilization_to_level()` (gradient.py) check `math.isfinite()` and return BLOCKED for non-finite values.

### WebSocket Security

WebSocket connections require authentication on establishment. CORS origins respected from config.

### Bundle serve.py

Binds to `127.0.0.1` (localhost only), not `0.0.0.0`.

## Dependency Graph

```
config.py  <-- everything
trust/     <-- core/ (session uses genesis, deliberation uses crypto)
core/      <-- api/ (handlers call core services)
core/      <-- cli.py
core/      <-- mcp/ (proxy uses constraint enforcer)
domains/   <-- core/ (session loads templates; learning loads targets)
export/    <-- api/ and cli.py
persistence/ <-- core/, trust/ (audit chain persists via TrustChainEntry)
```

## Key Conventions

- Timestamps: ISO 8601 with microseconds and Z suffix (`%Y-%m-%dT%H:%M:%S.%fZ`)
- IDs: UUID4 strings
- Hashes: SHA-256 hex digests
- Signatures: Ed25519, base64url-encoded
- Error responses: `{"error": {"type": "...", "message": "..."}}`
- State transitions: explicit validation via VALID_TRANSITIONS dict
- Constraint dimensions: Financial, Operational, Temporal, Data Access, Communication (exact names, exact order)
- JSON model fields: `Optional[str]` (not `Optional[dict]`) -- DataFlow stores as strings
- Column validation: regex check on all dict keys in db_ops before SQL construction
