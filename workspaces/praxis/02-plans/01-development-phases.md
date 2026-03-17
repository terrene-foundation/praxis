# Development Plan — Full Platform

## Approach

Praxis is CO. All domains, all personas, all channels ship together. Development uses COC methodology — full ecosystem delivery, not phased MVPs.

---

## Products

| Product | Technology | Personas Served |
|---------|-----------|----------------|
| **CLI** | Click + Rich | CLI Practitioner |
| **API + MCP** | Kailash Nexus (REST + MCP + WebSocket) | All clients |
| **Web Dashboard** | React | Practitioner, Supervisor, Auditor |
| **Desktop App** | Flutter | Non-Technical Collaborator, Supervisor |
| **Mobile App** | Flutter (iOS, Android, iPadOS, Android tablet) | Supervisor, Practitioner (approvals) |

## Domains

All ship together — CO is domain-agnostic:

| Domain | Application |
|--------|------------|
| **COC** | CO for Codegen |
| **COE** | CO for Education |
| **COG** | CO for Governance |
| **COR** | CO for Research |
| **COComp** | CO for Compliance |
| **COF** | CO for Finance |

---

## Core Runtime

| Component | Purpose | Built With |
|-----------|---------|------------|
| Session Manager | Persistent collaboration sessions with identity | Kailash Core SDK, DataFlow |
| Deliberation Capture | Record human-AI reasoning with cryptographic integrity | EATP SDK, jcs |
| Constraint Enforcer | 5-dimensional runtime enforcement (deterministic) | Pure Python, EATP SDK |
| Trust Plane | Cryptographic trust chains, verification gradient | EATP SDK, trust-plane, cryptography |
| Domain Engine | Pluggable CO domain applications (YAML config) | PyYAML, Kaizen |
| Verification & Export | Self-contained verification bundles | Jinja2, SubtleCrypto |

---

## Source Architecture

```
src/praxis/
  __init__.py
  cli.py                        # Click CLI entry point
  config.py                     # .env configuration
  core/
    session.py                  # Session lifecycle state machine
    deliberation.py             # Deliberation capture engine
    constraint.py               # 5-dimensional constraint enforcer
    domain.py                   # Domain config loader
  trust/
    genesis.py                  # Genesis record creation (wraps EATP SDK)
    delegation.py               # Delegation chain management
    gradient.py                 # Verification gradient engine
    audit.py                    # Audit anchor chain
    bundle.py                   # Verification bundle generation
    keys.py                     # Ed25519 key management
  api/
    handlers.py                 # Nexus handlers (shared across channels)
    mcp.py                      # MCP tool definitions
    websocket.py                # WebSocket event streaming
  persistence/
    models.py                   # DataFlow models
    queries.py                  # Custom query patterns
    migrations/                 # Alembic schema migrations
  export/
    bundle.py                   # Bundle builder (ZIP assembly)
    report.py                   # Audit report generator
    templates/                  # HTML/JS/CSS for bundle viewer
  domains/
    coc/                        # COC domain YAML configs
    coe/                        # COE domain YAML configs
    cog/                        # COG domain YAML configs
    cor/                        # COR domain YAML configs
    cocomp/                     # COComp domain YAML configs
    cof/                        # COF domain YAML configs
    loader.py                   # Domain configuration loader
```

## Frontend Architecture

```
web/                            # React web dashboard
  src/
    pages/
      practitioner/             # Session management, constraints, timeline
      supervisor/               # Team overview, approval queue, delegation
      auditor/                  # Verification, chain inspection, reports
    components/
      constraints/              # Constraint gauges, visual editor
      timeline/                 # Deliberation timeline
      trust-chain/              # Chain visualization, delegation tree
      approval/                 # Held action approval cards

desktop/                        # Flutter desktop app
  lib/
    screens/
      session_wizard.dart       # Guided session setup
      dashboard.dart            # Main dashboard
      constraint_editor.dart    # Visual constraint editor
      approval.dart             # Approval workflows
    services/
      praxis_api.dart           # REST API client
      websocket.dart            # Real-time updates
      notifications.dart        # System notifications

mobile/                         # Flutter mobile (iOS, Android, iPadOS, Android tablet)
  lib/
    screens/
      session_monitor.dart      # Session status
      approval.dart             # One-tap approve/deny
      trust_chain.dart          # Chain browsing
    services/
      praxis_api.dart           # REST API client
      push_notifications.dart   # Push notification handling
```

---

## Dependencies

Develop against local editable installs. Publish to PyPI at release.

| Package | Version | Purpose |
|---------|---------|---------|
| kailash | >=0.12.5 | Workflow orchestration (140+ nodes) |
| kailash-nexus | >=1.4.2 | Multi-channel API (REST + CLI + MCP) |
| kailash-dataflow | >=0.12.4 | Zero-config database operations |
| kailash-kaizen | >=1.2.5 | AI agent framework |
| eatp | >=0.1.0 | Trust protocol SDK |
| trust-plane | >=0.2.0 | EATP reference implementation |

---

## What Users Can Do

### CLI Practitioner

```bash
praxis init --name "Q1 Analysis" --domain coc
praxis session start
# AI assistant connects via MCP, every action constrained and anchored
praxis status
praxis decide --type scope --decision "Focus on Q1" --rationale "Q2 data not audited"
praxis session end
praxis export --format bundle
praxis verify bundle.zip
```

### Web Dashboard User

- Start sessions from a browser with a guided wizard
- See constraint gauges (5 dimensions) updating in real-time
- Approve or deny held actions with one click
- Record decisions through a simple form
- View deliberation timeline with chronological events
- Export verification bundles

### Supervisor

- Team overview showing all active sessions
- Approval queue for escalated actions
- Delegation tree visualization
- Trust chain inspection
- Compliance report generation

### External Auditor

- Open verification bundle ZIP in any browser
- Client-side cryptographic chain verification (zero installation)
- Timeline view of all actions and decisions
- Constraint compliance assessment
- Download PDF report

### Desktop App User

- Session wizard ("What are you working on?")
- System tray with session status
- Visual constraint editor (sliders and toggles)
- OS notifications for held actions
- Offline capability with sync

### Mobile App User

- Push notifications for held actions
- One-tap approve/deny from anywhere
- Session status monitoring
- Trust chain browsing
- Constraint alerts

---

## API Contract

All endpoints via Nexus (REST + CLI + MCP simultaneously):

```
# Sessions
POST   /sessions              CREATE session (with genesis)
GET    /sessions               LIST sessions
GET    /sessions/{id}          GET session detail
POST   /sessions/{id}/pause    PAUSE session
POST   /sessions/{id}/resume   RESUME session
POST   /sessions/{id}/end      END session (generate attestation)

# Deliberation
POST   /sessions/{id}/decide   RECORD decision
POST   /sessions/{id}/observe  RECORD observation
GET    /sessions/{id}/timeline GET deliberation timeline

# Constraints
GET    /sessions/{id}/constraints     GET constraint state
PUT    /sessions/{id}/constraints     UPDATE constraints
GET    /sessions/{id}/gradient        GET gradient status

# Trust
POST   /sessions/{id}/delegate        CREATE delegation
POST   /sessions/{id}/approve/{held}  APPROVE held action
POST   /sessions/{id}/deny/{held}     DENY held action
GET    /sessions/{id}/chain           GET trust chain

# Verification
POST   /sessions/{id}/verify          VERIFY chain integrity
POST   /sessions/{id}/export          GENERATE verification bundle
GET    /sessions/{id}/audit           GET audit report

# MCP Tools
trust_check(action, resource, context)  -> verdict
trust_record(action, reasoning_trace)   -> anchor_id
trust_escalate(issue, context)          -> escalation_id
trust_envelope()                        -> constraint_state
trust_status()                          -> session_status
```

---

## Data Models

```python
@db.model
class Session:
    id: int
    session_id: str               # UUID, unique
    workspace_id: str
    domain: str                   # coc, coe, cog, cor, cocomp, cof
    state: str                    # creating, active, paused, archived
    genesis_id: str
    constraint_envelope: dict     # Active constraints (5 dimensions)
    created_at: datetime
    updated_at: datetime

@db.model
class DeliberationRecord:
    id: int
    session_id: str
    record_type: str              # decision, observation, escalation, intervention
    content: dict
    reasoning_trace: dict
    reasoning_hash: str           # SHA-256 of canonical JSON
    parent_record_id: str         # Hash chain link
    anchor_id: str                # EATP audit anchor reference
    created_at: datetime

@db.model
class ConstraintEvent:
    id: int
    session_id: str
    action: str
    dimension: str
    gradient_result: str          # auto_approved, flagged, held, blocked
    utilization: float
    resolved_by: str
    created_at: datetime

@db.model
class TrustChainEntry:
    id: int
    session_id: str
    entry_type: str               # genesis, delegation, attestation, anchor
    payload: dict
    signature: str                # Ed25519 signature
    parent_hash: str
    content_hash: str
    created_at: datetime

@db.model
class Workspace:
    id: int
    workspace_id: str
    name: str
    domain: str
    constraint_template: str
    created_at: datetime
    updated_at: datetime
```

---

## Testing Strategy

- **Unit tests**: Constraint evaluation, gradient calculation, chain validation
- **Integration tests**: Full session lifecycle with real DataFlow and EATP SDK
- **E2E tests**: Client -> Praxis -> trust chain -> verification bundle
- **Property tests**: Constraint tightening invariant, chain integrity invariant
- **Conformance tests**: EATP specification compliance
