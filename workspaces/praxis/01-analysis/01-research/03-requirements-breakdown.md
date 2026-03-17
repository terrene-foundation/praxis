# Requirements Breakdown

## Executive Summary

- **Feature**: Praxis CO Platform (full product)
- **Complexity**: High (10 capabilities, 5 personas, 6 domain applications, 4 API channels)
- **Risk Level**: Medium (strong framework support from Kailash + EATP; novel integration surface)
- **Estimated Effort**: 16-20 weeks for MVP (v0.1.0), 9-12 months for v1.0

---

## Capability 1: Session Management

**Priority**: P0 (MVP)
**Effort**: M (Medium)
**Dependencies**: Persistence layer, Trust infrastructure (genesis records)

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| SM-001 | Create session | workspace_id, domain, constraints | Session object with genesis | Validate workspace exists, create genesis record, apply constraint template, persist | Duplicate session_id, invalid domain, workspace not found | DataFlow (model), EATP SDK (genesis) |
| SM-002 | Session lifecycle transitions | session_id, target_state | Updated session | State machine: creating -> active -> paused -> resumed -> archived; validate transitions | Invalid transitions (archived -> active), concurrent state changes | DataFlow (update) |
| SM-003 | List sessions | filters (workspace, domain, state) | Session list with summary | Query with pagination, filter by state/domain/workspace | Empty results, large result sets | DataFlow (query) |
| SM-004 | Get session detail | session_id | Full session with trust state | Join session + constraint state + deliberation count + chain length | Session not found, archived session | DataFlow (query) |
| SM-005 | Session persistence across restarts | session_id | Restored session | Load from database, restore in-memory state, reconnect trust chain | Corrupted state, schema migration needed | DataFlow (persistence) |
| SM-006 | Multi-session workspaces | workspace_id | Workspace with session list | Group sessions by workspace, shared constraint templates | Cross-session references, workspace deletion with active sessions | DataFlow (model) |

### Non-Functional Requirements

- Session creation latency: <200ms including genesis record
- Support 1,000+ sessions per instance
- Session state transitions must be atomic (no partial updates)

---

## Capability 2: Deliberation Capture

**Priority**: P0 (MVP)
**Effort**: M
**Dependencies**: Session Management, Trust infrastructure (audit anchors)

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| DC-001 | Record decision | session_id, type, content, reasoning | DeliberationRecord with anchor | Validate session active, hash content (SHA-256 canonical JSON), chain to parent, create audit anchor | Session paused/archived, hash collision (theoretical), empty reasoning | DataFlow, EATP SDK, jcs |
| DC-002 | Record observation | session_id, content, context | DeliberationRecord (observation type) | Lower ceremony than decision -- no alternatives required, still anchored | Very high frequency observations (rate management) | DataFlow, EATP SDK |
| DC-003 | Record escalation | session_id, issue, context, severity | DeliberationRecord (escalation type) | Mark as requiring human attention, may trigger HELD gradient | Escalation during paused session | DataFlow, EATP SDK |
| DC-004 | Get timeline | session_id, filters | Ordered deliberation records | Chronological with type filtering, include gradient events | Large timelines (pagination), cross-session timelines | DataFlow (query) |
| DC-005 | Hash chain integrity | session_id | Integrity result (valid/broken + details) | Walk chain from genesis, verify each hash links to parent | Broken chain (which link?), empty chain | EATP SDK (verify), cryptography |
| DC-006 | Confidence scoring | decision content | Confidence in basis points | Parse reasoning trace for confidence indicators, store as integer (0-10000) | Missing confidence, confidence = 0 or 10000 | Pure Python |

### Non-Functional Requirements

- Decision recording latency: <100ms (must not block AI workflow)
- Hash chain verification: <1s for 10,000 records
- Canonical JSON serialization must use JCS (RFC 8785)

---

## Capability 3: Constraint Enforcement

**Priority**: P0 (MVP)
**Effort**: L (Large)
**Dependencies**: Session Management, Trust infrastructure (verification gradient)

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| CE-001 | Financial constraints | action, estimated_cost | Gradient verdict | Track cumulative cost, compare to session budget, return AUTO_APPROVED/FLAGGED/HELD/BLOCKED | Cost estimation unavailable, budget exhausted mid-action, refunds | Pure Python |
| CE-002 | Operational constraints | action, resource | Gradient verdict | Check action against allow/block lists, pattern matching on resources | Wildcards, nested paths, action not in any list | Pure Python |
| CE-003 | Temporal constraints | action, timestamp | Gradient verdict | Check against time windows, session duration limits, deadlines | Timezone handling, clock skew, DST transitions | Pure Python |
| CE-004 | Data access constraints | action, file_path/data_classification | Gradient verdict | Check path against read/write allow lists, classification levels | Symlinks, relative paths, path traversal attempts | Pure Python |
| CE-005 | Communication constraints | action, channel, recipient | Gradient verdict | Check against allowed channels and recipients, content rules | New channels not in allow list, broadcast actions | Pure Python |
| CE-006 | Multi-dimension evaluation | action with full context | Combined gradient verdict | Evaluate all 5 dimensions, return strictest verdict (BLOCKED > HELD > FLAGGED > AUTO_APPROVED) | Conflicting dimensions, dimension not configured | Pure Python |
| CE-007 | Constraint envelope CRUD | session_id, constraint updates, reasoning | Updated envelope with audit | Store constraint changes with reasoning trace, enforce tightening-only for delegations | Loosening attempt, removing a dimension, empty envelope | DataFlow, EATP SDK |
| CE-008 | Held action resolution | held_action_id, decision (approve/deny), reasoning | Resolution record + audit anchor | Record human decision, create attestation, resume or reject action | Timeout on held action, approver not authorized, double-approve | DataFlow, EATP SDK |

### Non-Functional Requirements

- Constraint evaluation latency: <10ms per dimension, <50ms total
- Constraint enforcement is deterministic -- same input always produces same output
- No false negatives on BLOCKED actions (security-critical)

---

## Capability 4: Trust Infrastructure

**Priority**: P0 (MVP)
**Effort**: L
**Dependencies**: EATP SDK, trust-plane, cryptography library

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| TI-001 | Genesis record creation | human identity, constraint envelope | Genesis record (Ed25519 signed) | Generate keypair if needed, create root of trust, sign with human's key | Key already exists, re-genesis for existing workspace | EATP SDK, cryptography |
| TI-002 | Delegation chain | parent_id, delegatee, constraints | Delegation record (signed) | Validate constraints are subset of parent (tightening only), sign, chain | Constraint widening attempt, deep delegation chains (> 10 levels) | EATP SDK |
| TI-003 | Verification gradient engine | action, context, constraints | Gradient classification (4 levels) | Classify action against constraint utilization thresholds, session posture | Threshold edge cases (exactly at boundary), missing context | Pure Python, EATP SDK |
| TI-004 | Audit anchor chain | action, result, session_id | Anchor with hash link to previous | Create tamper-evident record, hash-chain to previous anchor, Ed25519 sign | First anchor (no parent), concurrent anchors (ordering), high-throughput | EATP SDK, jcs |
| TI-005 | Trust chain query | session_id, depth | Full trust chain | Walk from genesis through delegations to current session, include all anchors | Incomplete chains, cross-session chains | DataFlow (query) |
| TI-006 | Chain verification | chain_data | Verification result | Verify every signature, verify hash chain continuity, verify constraint tightening | Broken link (which one?), invalid signature (which record?), key rotation | EATP SDK |
| TI-007 | Trust posture state machine | session events | Posture level | Track posture progression: SUPERVISED -> ASSISTED -> SHARED_PLANNING -> DELEGATED | Posture regression (should it be possible?), posture across sessions | Pure Python |
| TI-008 | Key management | — | Keys stored securely | Generate Ed25519 keypairs, store with filesystem permissions (600) or OS keychain | Key rotation, key compromise, multi-device | cryptography, OS keychain |

### Non-Functional Requirements

- Ed25519 signing latency: <5ms per operation
- Chain verification: O(n) where n is chain length
- Keys stored with 600 permissions minimum (or OS keychain)

---

## Capability 5: Domain Engine

**Priority**: P1 (important, but MVP can ship with COC only)
**Effort**: M
**Dependencies**: Session Management, Constraint Enforcement

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| DE-001 | Load domain configuration | domain name (coc/coe/cog) | Domain config object | Parse YAML files from domains/{name}/, validate schema, return typed config | Missing domain, invalid YAML, schema violation | PyYAML (via Kailash) |
| DE-002 | Constraint template resolution | domain, template_name | Constraint envelope | Load template from domain config, merge with workspace defaults | Template not found, conflicting constraints | Pure Python |
| DE-003 | Agent team definition | domain, workflow_phase | Agent team config | Return agent definitions for the current phase, including routing rules | Phase not in domain, no agents defined for phase | Kaizen (agent defs) |
| DE-004 | Capture rule enforcement | domain, action, context | Capture instruction | Determine what deliberation evidence to record for this action in this domain | Action not in capture rules (default behavior?) | Pure Python |
| DE-005 | Domain validation | domain directory path | Validation result | Validate all YAML files against schema, check constraint coherence, verify agent refs | Partial domain (some files missing), circular references | Pure Python |
| DE-006 | Custom domain registration | domain config directory | Registered domain | Validate, copy/link to domains directory, make available for session creation | Name collision, invalid structure | Pure Python, DataFlow |

### Non-Functional Requirements

- Domain loading: <100ms at session start
- YAML parsing cached after first load
- Domain configs are immutable during a session

---

## Capability 6: Multi-Channel Client API

**Priority**: P0 (MVP -- REST + CLI + MCP)
**Effort**: L
**Dependencies**: All core capabilities (Session, Deliberation, Constraint, Trust)

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| API-001 | REST API | HTTP requests | JSON responses | Full CRUD for sessions, deliberation, constraints, trust, verification | Auth failure, malformed JSON, rate limiting | Nexus (REST channel) |
| API-002 | CLI | Terminal commands | Formatted output | `praxis init`, `praxis session start/end`, `praxis status`, `praxis export` | No active session, interrupted command | Nexus (CLI channel) + Click |
| API-003 | MCP server | MCP tool calls | MCP tool responses | trust_check, trust_record, trust_escalate, trust_envelope, trust_status | MCP connection drops, tool timeout | Nexus (MCP channel) |
| API-004 | Authentication | Bearer token / API key | Auth result | JWT validation, token refresh, rate limiting per identity | Expired token, invalid signature, rate limit exceeded | Nexus middleware, slowapi |
| API-005 | Rate limiting | Request metadata | Allow/deny | IP-based (10K cap) + identity-based limits, configurable per endpoint | Burst traffic, legitimate high-volume clients | slowapi |
| API-006 | WebSocket streaming | WS connection | Event stream | Real-time session events, constraint state changes, held action notifications | Connection drops, reconnection, backpressure | Nexus (WS channel) |

### Non-Functional Requirements

- REST API latency: <100ms for reads, <200ms for writes
- MCP tool call latency: <150ms
- WebSocket message delivery: <50ms from event
- Rate limiting: 10,000 requests/hour per IP (default)

### Priority Breakdown

| Channel | Priority | Rationale |
|---------|----------|-----------|
| REST API | P0 | Foundation for all clients |
| CLI | P0 | CLI Practitioner persona |
| MCP | P0 | AI assistant integration |
| WebSocket | P1 | Real-time dashboard updates |

---

## Capability 7: Web Dashboard

**Priority**: P1 (enables 3 of 5 personas)
**Effort**: XL
**Dependencies**: REST API, WebSocket API

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| WD-001 | Practitioner view | Session data via REST | Interactive dashboard | Session management, constraint gauges, deliberation timeline, decision recording | No active sessions, many sessions | React or lightweight SPA |
| WD-002 | Supervisor view | Team session data | Read-only dashboard | Team overview, escalated action queue, trust chain visualization, delegation trees | No team members, large teams | React or lightweight SPA |
| WD-003 | Auditor view | Trust chain data | Verification interface | Chain inspection, integrity verification, compliance report generation | Very large chains, broken chains | React or lightweight SPA |
| WD-004 | Analytics | Aggregated session data | Charts and metrics | Session duration, constraint utilization, decision frequency, trust posture trends | No data yet, cross-workspace analytics | React + charting library |
| WD-005 | Approval queue | Held actions | Approve/deny interface | List held actions with context, one-click approve/deny, reasoning input | No held actions, expired holds | React |

### Non-Functional Requirements

- Dashboard load time: <2s
- Real-time updates via WebSocket
- Mobile-responsive design
- No external CDN dependencies (self-contained)

---

## Capability 8: Desktop Application

**Priority**: P2 (nice to have)
**Effort**: XL
**Dependencies**: REST API, WebSocket API, Web Dashboard (share components)

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| DA-001 | Session wizard | User input via GUI | New session | Guided setup: "What are you working on?" -> domain selection -> constraint preview | First-time user, no workspaces | Electron/Tauri + React |
| DA-002 | System tray | Background process | Tray icon with status | Show session status, notification count, quick actions | Multiple sessions active, tray not supported | Electron/Tauri |
| DA-003 | Visual constraint editor | Slider/toggle input | Constraint envelope | Visual representation of 5 dimensions, real-time feedback on gradient thresholds | Touch-only devices, accessibility | React components |
| DA-004 | Notifications | Session events | OS notifications | Push for held actions, flagged events, session milestones | Do-not-disturb mode, notification fatigue | OS notification APIs |
| DA-005 | Offline mode | Cached session data | Local-first operation | Queue changes when offline, sync when reconnected, conflict resolution | Conflicting changes, extended offline, large queue | IndexedDB/SQLite |

### Non-Functional Requirements

- Application startup: <3s
- Memory usage: <200MB
- Cross-platform: macOS, Windows, Linux

---

## Capability 9: Mobile Companion

**Priority**: P3 (future)
**Effort**: XL
**Dependencies**: REST API, Push notification infrastructure

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| MC-001 | Push notifications | Session events | Mobile push | Held action alerts, constraint warnings, session status changes | Notification permissions denied, battery optimization | Flutter / React Native |
| MC-002 | Approve/deny | Tap action | Resolution record | One-tap approve/deny with optional reasoning | Fat-finger approve, no context visible | Flutter / React Native |
| MC-003 | Session monitor | Poll/WS | Status view | Session list with status, constraint gauges, recent events | Poor connectivity, battery drain | Flutter / React Native |
| MC-004 | Trust chain browser | Chain data | Tree view | Browse delegation tree, verify integrity, view anchor details | Deep chains on small screen, slow rendering | Flutter / React Native |

### Non-Functional Requirements

- App size: <50MB
- Battery impact: minimal (efficient polling or push-only)
- Platform: iOS + Android

---

## Capability 10: Verification & Export

**Priority**: P0 (MVP -- verification bundles are core to trust)
**Effort**: M
**Dependencies**: Trust infrastructure, Deliberation capture

### Functional Requirements

| ID | Requirement | Input | Output | Business Logic | Edge Cases | Framework |
|----|-------------|-------|--------|----------------|------------|-----------|
| VE-001 | Verification bundle generation | session_id | Self-contained ZIP (JSON + HTML + JS) | Collect all trust chain data, embed client-side verification code, bundle as ZIP | Very large sessions (100K+ anchors), multi-session bundles | Pure Python, Jinja2 |
| VE-002 | Client-side chain verification | Bundle data (in browser) | Verification result | JavaScript re-implementation of chain verification, runs entirely in browser | Ed25519 verification in JS (SubtleCrypto), large chains (memory) | Vanilla JS (SubtleCrypto) |
| VE-003 | Audit report generation | session_id, format | Human-readable report | Timeline, constraint summary, decision digest, integrity status | Very long sessions, multi-format (HTML, PDF, JSON) | Jinja2 templates |
| VE-004 | JSON export | session_id | EATP-standard JSON | Export trust chain in EATP standard format for machine consumption | Forward compatibility, schema versioning | Pure Python, jcs |
| VE-005 | Bundle viewer | HTML file in browser | Interactive timeline | Chronological view, filtering, search, constraint review, assessment template | Offline use (no CDN), accessibility, large datasets | Vanilla HTML/CSS/JS |

### Non-Functional Requirements

- Bundle generation: <10s for sessions with 10,000 anchors
- Bundle size: <10MB for typical sessions
- Bundle viewer works in any modern browser without installation
- No external dependencies in bundle (fully self-contained)

---

## Cross-Cutting Requirements

### Persistence (DataFlow)

**Priority**: P0
**Effort**: M
**Dependencies**: Kailash DataFlow

| ID | Requirement | Description |
|----|-------------|-------------|
| PER-001 | DataFlow models | Session, DeliberationRecord, ConstraintEvent, TrustChainEntry, Workspace |
| PER-002 | SQLite for development | Zero-config local database |
| PER-003 | PostgreSQL for production | Connection pooling, concurrent access |
| PER-004 | Schema migrations | Alembic-managed, non-destructive |
| PER-005 | Query patterns | Efficient queries for timeline, chain walking, session listing |

### Configuration

**Priority**: P0
**Effort**: S (Small)
**Dependencies**: python-dotenv

| ID | Requirement | Description |
|----|-------------|-------------|
| CFG-001 | .env as source of truth | All API keys, model names, database URLs from .env |
| CFG-002 | Config validation | Fail fast on missing required config |
| CFG-003 | Config layering | .env -> environment variables -> CLI flags -> defaults |

### Logging & Observability

**Priority**: P1
**Effort**: S
**Dependencies**: structlog

| ID | Requirement | Description |
|----|-------------|-------------|
| LOG-001 | Structured logging | JSON-formatted logs via structlog |
| LOG-002 | No secrets in logs | Filter sensitive fields from log output |
| LOG-003 | Request tracing | Correlation IDs across API requests |

---

## Framework Mapping Summary

| Framework | Components It Handles |
|-----------|----------------------|
| **Kailash Core SDK** | Workflow orchestration for internal pipelines (session lifecycle, constraint evaluation) |
| **Kailash DataFlow** | All persistence -- models, queries, migrations, SQLite/PostgreSQL |
| **Kailash Nexus** | All API channels -- REST, CLI, MCP served from single codebase |
| **Kailash Kaizen** | Domain engine agent definitions, team compositions, routing |
| **EATP SDK** | Genesis records, delegation chains, audit anchors, signatures, verification |
| **trust-plane** | Reference patterns for trust chain operations, verification bundles |
| **cryptography** | Ed25519 key generation, signing, verification |
| **jcs** | Canonical JSON serialization (RFC 8785) for deterministic hashing |
| **Click + Rich** | CLI commands, formatted terminal output |
| **slowapi** | API rate limiting |
| **structlog** | Structured logging |
| **Alembic** | Database schema migrations |

---

## Priority Summary

| Priority | Capabilities | Rationale |
|----------|-------------|-----------|
| **P0** | Session Management, Deliberation Capture, Constraint Enforcement, Trust Infrastructure, API (REST+CLI+MCP), Verification & Export, Persistence, Configuration | Core CO methodology. Without these, Praxis has no reason to exist. |
| **P1** | Domain Engine (full), Web Dashboard, WebSocket API, Logging | Enables 4 of 5 personas and domain portability. |
| **P2** | Desktop Application | Important for non-technical users but not for initial adoption. |
| **P3** | Mobile Companion | Valuable for approval workflows but depends on mature backend. |
