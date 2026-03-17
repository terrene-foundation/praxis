# Architecture Decision Records

---

## ADR-001: Wrap EATP SDK + Trust-Plane Rather Than Reimplement Trust

### Status

Accepted

### Context

Praxis needs trust infrastructure: genesis records, delegation chains, constraint-tightening verification, audit anchors with Ed25519 signatures, and hash-chained temporal integrity. Two approaches exist:

1. Build trust primitives directly using the `cryptography` library and custom data structures
2. Wrap the existing EATP SDK and trust-plane reference implementation

The EATP SDK (v0.1.0) provides the core trust protocol -- record types, signing, chain verification, and canonical serialization. The trust-plane (v0.2.0) is the reference implementation that proved the architecture works in a Claude Code session (March 2026), with 1,473 tests passing, 14 red-team rounds converged, enterprise features (RBAC, OIDC, SIEM), and a verification bundle system.

Praxis's trust-plane experiment identified six problems. The trust-plane already solved the cryptographic foundation (#5 proof of human authorization, #6 verification gradient). Praxis must solve the remaining four (#1 AI operates trust plane, #2 no constraint enforcement, #3 camera problem, #4 no session tracking) at a higher architectural level.

### Decision

Praxis wraps the EATP SDK and trust-plane as its trust layer. It does not reimplement trust primitives.

Specifically:

- **EATP SDK** provides: record types (Genesis, Delegation, Attestation, Anchor), Ed25519 signing/verification, canonical JSON serialization, chain integrity verification, constraint envelope model
- **trust-plane** provides: reference patterns for trust directory structure, verification bundle generation, template system, trust posture state machine
- **Praxis adds**: session management wrapping trust operations, constraint enforcement as a runtime mediator (not observer), deliberation capture integrated with audit anchors, multi-channel API exposing trust operations, domain engine for CO-specific configuration

The boundary is clear: EATP SDK handles cryptographic trust primitives. Praxis handles session-aware orchestration of those primitives.

### Consequences

#### Positive

- No reimplementation of battle-tested cryptographic code (1,473 tests, 14 red-team rounds)
- Automatic conformance with EATP specification (the SDK IS the spec implementation)
- Faster development -- trust primitives are ready, Praxis focuses on orchestration
- Upgrades to EATP SDK automatically improve Praxis trust operations
- Clear separation of concerns -- trust protocol vs. trust orchestration

#### Negative

- Dependency on EATP SDK release cadence (mitigated: Foundation controls both)
- EATP SDK API surface becomes Praxis's trust API floor (any change propagates)
- Must track EATP SDK breaking changes across major versions
- Additional dependency in the dependency tree

#### Risks

- EATP SDK v0.1.0 may have API instability (mitigated: Foundation controls both, can coordinate releases)
- Trust-plane patterns may not map cleanly to Praxis's session model (mitigated: Praxis adapts patterns, not the other way around)

### Alternatives Considered

#### Option A: Reimplement from scratch using cryptography library

- **Pros**: No external dependency, full control over API surface, can optimize for Praxis's exact needs
- **Cons**: Reimplements 14,000+ lines of tested code, risks specification divergence, duplicates 14 rounds of red-team hardening, maintains two implementations of the same protocol
- **Why rejected**: The EATP SDK exists specifically to prevent this. Reimplementing it contradicts the Foundation's standards-first principle and wastes engineering effort on solved problems.

#### Option B: Fork trust-plane and embed directly

- **Pros**: No runtime dependency, can modify freely, snapshot of known-good code
- **Cons**: Loses upstream improvements, creates maintenance burden for trust primitives, divergence from EATP specification over time
- **Why rejected**: Forking creates the exact problem standards are designed to prevent -- implementation drift from specification.

---

## ADR-002: DataFlow for Persistence vs. Raw SQLAlchemy

### Status

Accepted

### Context

Praxis needs to persist sessions, deliberation records, constraint events, trust chain entries, and workspaces. Two approaches:

1. Use SQLAlchemy directly with manual model definitions, migrations, and query patterns
2. Use Kailash DataFlow, which provides zero-config database operations on top of SQLAlchemy

Praxis has five data models (Session, DeliberationRecord, ConstraintEvent, TrustChainEntry, Workspace) with relatively straightforward query patterns. The most complex query is chain-walking (following parent_hash links through TrustChainEntry records).

### Decision

Use Kailash DataFlow for all persistence.

DataFlow provides:

- `@db.model` decorator for zero-config model definition
- Automatic table creation and migration support
- Built-in CRUD operations (create, read, update, delete, list, query)
- SQLite for development, PostgreSQL for production (same code)
- Connection pooling and session management
- Type-safe query building

Praxis adds:

- Custom query patterns for chain walking and timeline queries in `persistence/queries.py`
- Alembic migrations for schema evolution in `persistence/migrations/`
- Indexes for performance-critical queries (session_id lookups, hash chain traversal)

### Consequences

#### Positive

- Zero-config database setup for development (SQLite, no install required)
- Same code for development and production (SQLite -> PostgreSQL)
- Eliminates boilerplate for CRUD operations
- Built-in connection pooling and session management
- Consistent with Foundation framework-first directive
- Tested patterns from other Foundation projects

#### Negative

- DataFlow's query DSL may be insufficient for complex chain-walking queries (mitigated: can drop to raw SQLAlchemy for specific queries)
- Adds DataFlow as a dependency (mitigated: already in pyproject.toml, Foundation-owned)
- DataFlow requires integer `id` as primary key (mitigated: use UUID `session_id` as business key alongside auto-increment `id`)

#### Risks

- Chain-walking queries may need raw SQL for performance (mitigated: DataFlow supports raw queries as escape hatch)
- DataFlow schema evolution may conflict with Alembic migrations (mitigated: use Alembic exclusively for migrations, DataFlow for runtime operations)

### Alternatives Considered

#### Option A: Raw SQLAlchemy

- **Pros**: Full control, well-documented, no additional abstraction layer
- **Cons**: More boilerplate (models, sessions, connection management), manual CRUD, must configure SQLite vs PostgreSQL switching
- **Why rejected**: DataFlow handles all of this with less code. Raw SQLAlchemy is the escape hatch when DataFlow's abstractions are insufficient, not the starting point.

#### Option B: Raw SQLite with sqlite3 module

- **Pros**: Zero dependencies, maximum simplicity, no ORM overhead
- **Cons**: No migration support, manual SQL, no PostgreSQL path, no connection pooling, no type safety
- **Why rejected**: Production deployments need PostgreSQL. Building a database abstraction layer from scratch contradicts the framework-first directive.

---

## ADR-003: Nexus for API Serving vs. Standalone FastAPI

### Status

Accepted

### Context

Praxis must serve four API channels: REST, CLI, MCP, and WebSocket. All four share the same business logic (session management, deliberation capture, constraint enforcement, trust operations). Two approaches:

1. Build a standalone FastAPI application with separate CLI (Click) and MCP server implementations
2. Use Kailash Nexus, which deploys a single codebase across REST + CLI + MCP simultaneously

The Praxis API contract (from 04-technical-requirements.md) defines 15+ REST endpoints, 5 MCP tools, and 10+ CLI commands. All map to the same underlying operations.

### Decision

Use Kailash Nexus as the API serving layer.

Nexus provides:

- Single codebase deployed as REST API + CLI + MCP server simultaneously
- Automatic OpenAPI documentation for REST
- Automatic help text for CLI
- Automatic MCP tool registration
- Shared middleware (auth, rate limiting, logging) across all channels
- FastAPI under the hood for REST (with all its async capabilities)

Praxis adds:

- WebSocket handlers (Nexus may not cover this natively; extend via FastAPI's WebSocket support)
- Custom middleware for trust-context injection (every request gets session context)
- Rate limiting configuration via slowapi
- JWT authentication middleware

### Consequences

#### Positive

- Write business logic once, serve three ways (REST + CLI + MCP)
- API consistency across channels is automatic (same operation, same behavior)
- Reduces surface area for bugs (one implementation, not three)
- MCP integration is built-in (critical for AI assistant use case)
- Consistent with Foundation framework-first directive

#### Negative

- Nexus's channel abstraction may not perfectly fit all Praxis operations (mitigated: can add channel-specific handlers where needed)
- WebSocket support may require extending beyond Nexus (mitigated: FastAPI WebSocket support is accessible underneath)
- Nexus API surface constrains Praxis API design (mitigated: Nexus is designed to be flexible)

#### Risks

- Nexus v1.4.2 may not support all authentication patterns Praxis needs (mitigated: can add FastAPI middleware directly)
- MCP protocol evolution may outpace Nexus updates (mitigated: Foundation controls both)

### Alternatives Considered

#### Option A: Standalone FastAPI + separate CLI + separate MCP server

- **Pros**: Full control over each channel, no framework constraints, can optimize each independently
- **Cons**: Three implementations of the same business logic, three test suites, three sets of middleware, three API surfaces to keep in sync
- **Why rejected**: Triple maintenance burden. The core insight of Nexus is that these channels should share implementation. Building them separately contradicts this insight and the framework-first directive.

#### Option B: FastAPI + Click CLI (no MCP)

- **Pros**: Well-known stack, no framework dependency beyond FastAPI
- **Cons**: No MCP support (critical for AI assistant integration), must build MCP separately, two implementations instead of one
- **Why rejected**: MCP is a P0 requirement for the CLI Practitioner persona. Building it separately defeats the purpose of multi-channel deployment.

---

## ADR-004: Domain Engine as YAML Configuration vs. Code Plugins

### Status

Accepted

### Context

Praxis hosts domain-specific CO applications (COC, COE, COG, etc.). Each domain defines constraint templates, agent team compositions, workflow phases, capture rules, and assessment criteria. Two approaches:

1. YAML configuration files loaded by a generic domain engine
2. Python code plugins with a plugin registration API

The domain application template (from 03-domain-applications.md) specifies a YAML-based directory structure with files for constraints, agents, workflows, capture rules, and knowledge. The briefs explicitly state: "domains are pure configuration" and "no code changes required."

### Decision

Domains are YAML configuration loaded by a generic engine.

The domain engine:

- Loads YAML files from `domains/{name}/` following a fixed directory structure
- Validates all files against JSON Schema definitions
- Resolves constraint templates by name
- Provides agent team definitions to Kaizen for instantiation
- Enforces capture rules at session runtime
- Exposes domain metadata via API

The directory structure per domain:

```
domains/{name}/
  domain.yml              # Metadata, description, version
  constraints/
    default.yml           # Default constraint envelope
    templates/            # Named constraint presets
  agents/
    teams.yml             # Agent team compositions per phase
    definitions/          # Agent role YAML definitions
  workflows/
    phases.yml            # Workflow phases with approval gates
    evidence.yml          # Evidence requirements per phase
  capture/
    rules.yml             # What deliberation to capture
    assessment.yml        # Quality assessment criteria
  knowledge/
    institutional.yml     # Domain-specific institutional knowledge
    anti-amnesia.yml      # Priority classification
```

### Consequences

#### Positive

- Anyone can create a domain without writing Python code
- Domain contributions have a low barrier (YAML is readable by non-developers)
- Domains are portable (copy a directory, load in any Praxis instance)
- Domains are versionable (YAML diffs are meaningful in git)
- Schema validation catches errors at load time, not runtime
- Consistent with the CO principle of domain portability

#### Negative

- YAML cannot express arbitrary logic (mitigated: domain engine handles all logic, YAML is declarative configuration)
- Complex constraint expressions may be hard to express in YAML (mitigated: define a constraint expression DSL that covers the 5 dimensions)
- No runtime code execution in domains (mitigated: this is a feature -- domains are configuration, not code, for security)

#### Risks

- YAML schema may need evolution as domain requirements grow (mitigated: schema versioning from day one)
- Performance concern: parsing many YAML files at session start (mitigated: cache parsed configs, invalidate on file change)
- Community domains may have quality issues (mitigated: schema validation + `praxis domain validate` command)

### Alternatives Considered

#### Option A: Python code plugins with registration API

- **Pros**: Full expressiveness, can encode arbitrary logic, familiar pattern for developers
- **Cons**: High barrier for non-developers (COE users are educators, not developers), security risk (arbitrary code execution in domain definitions), hard to validate without running, not portable across language ecosystems
- **Why rejected**: CO methodology must be accessible to non-developers. The briefs specify that domains are "pure configuration." Code plugins serve developers but exclude the broader audience Praxis targets.

#### Option B: Hybrid (YAML with Python hooks)

- **Pros**: Declarative by default, programmable when needed
- **Cons**: Increases complexity, security boundary unclear (which hooks are safe?), two mental models for domain authors
- **Why rejected**: Premature complexity. If YAML proves insufficient, Python hooks can be added as v2.0 feature with clear security boundaries. Starting with pure YAML enforces simplicity and proves the declarative model works.

---

## ADR-005: Verification Bundles as Self-Contained HTML vs. Requiring Praxis

### Status

Accepted

### Context

Verification bundles are how external auditors (Persona 5) verify trust chains. The auditor receives a file, opens it, and independently confirms that trust protocols were followed. Two approaches:

1. Self-contained HTML/ZIP bundles with embedded JavaScript verification code
2. Bundles that require a Praxis instance or online service for verification

The trust-plane experiment already implemented verification bundles as self-contained HTML with client-side JavaScript. The External Auditor persona requirement explicitly states: "Zero installation -- everything runs in the browser."

### Decision

Verification bundles are fully self-contained. A bundle is a ZIP file containing:

```
bundle.zip/
  index.html              # Entry point, opens in any browser
  data/
    chain.json            # Full trust chain (EATP format)
    session.json          # Session metadata
    deliberation.json     # Deliberation records
    constraints.json      # Constraint events
  verify/
    verifier.js           # Ed25519 verification (SubtleCrypto API)
    chain-walker.js       # Hash chain validation
    ui.js                 # Interactive timeline and tree
  style/
    bundle.css            # Embedded styles (no CDN)
  assets/
    fonts/                # Embedded fonts (no CDN)
```

Key properties:

- **Zero installation**: Double-click `index.html` in any modern browser
- **Zero network**: No external requests, no CDN, no phone-home
- **Cryptographic verification**: Ed25519 signature verification using Web Crypto API (SubtleCrypto)
- **Deterministic**: Same bundle always produces the same verification result
- **Tamper-evident**: Bundle includes its own content hash; any modification invalidates it

### Consequences

#### Positive

- External auditors need zero technical setup (browser only)
- No trust dependency on Praxis being available or running
- No network dependency (works offline, in air-gapped environments)
- Auditors can verify years-old bundles even if Praxis version has changed
- Meets the "no vendor lock-in" platform principle
- Proven pattern from trust-plane experiment

#### Negative

- Ed25519 in browser (SubtleCrypto) has less performance than native implementations (mitigated: verification is bounded by chain length, not throughput)
- Bundle size increases with embedded JS/CSS/fonts (mitigated: typical bundle <10MB, minification reduces size)
- Must maintain JavaScript verification code alongside Python verification code (mitigated: verification algorithm is simple and well-specified by EATP)
- Browser security restrictions may affect file:// protocol loading (mitigated: bundle includes a minimal HTTP server script as fallback)

#### Risks

- SubtleCrypto API may not support Ed25519 in all browsers (mitigated: Ed25519 support is in all major browsers since 2023; include a fallback pure-JS implementation)
- Very large bundles (100K+ anchors) may cause browser memory issues (mitigated: lazy loading with pagination in the viewer)
- Content Security Policy in some enterprise environments may block inline scripts (mitigated: all JS in external files, not inline)

### Alternatives Considered

#### Option A: Require Praxis CLI for verification

- **Pros**: Simpler implementation, full Python verification, no JavaScript maintenance
- **Cons**: Auditors must install Python and Praxis, violates zero-installation requirement, creates dependency on Praxis availability
- **Why rejected**: The External Auditor persona explicitly requires zero installation. If an ethics board member receives a verification bundle, they should be able to open it in Chrome and see results, not install a Python environment.

#### Option B: Online verification service

- **Pros**: No client-side complexity, always up-to-date verification logic, analytics on verification activity
- **Cons**: Requires network, creates centralization (who runs the service?), privacy concern (trust chain data sent to server), availability dependency, violates privacy-by-default principle
- **Why rejected**: Centralized verification contradicts the "no vendor lock-in" and "privacy by default" platform principles. If the verification service goes down, bundles become unverifiable. If the service is compromised, verification results cannot be trusted.

#### Option C: PDF reports only (no interactive verification)

- **Pros**: Universal format, printable, no code execution
- **Cons**: No cryptographic verification (the reader trusts the PDF generator), not interactive, cannot independently confirm chain integrity
- **Why rejected**: PDF is a reporting format, not a verification format. The entire point of verification bundles is that the auditor does not trust the bundle creator -- they independently verify. A PDF that says "chain valid" is just a claim; a bundle with embedded verification code is proof.
