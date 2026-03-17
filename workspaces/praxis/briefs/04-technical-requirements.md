# Technical Requirements

## Runtime Architecture

### Core Runtime

Praxis is a Python application built on Foundation-owned open-source frameworks. The runtime is the trust-aware backend that client tools connect to.

```
praxis/
├── core/
│   ├── session.py          # Session lifecycle management
│   ├── deliberation.py     # Deliberation capture engine
│   ├── constraint.py       # 5-dimensional constraint enforcer
│   ├── domain.py           # Domain application loader
│   └── config.py           # Configuration from .env
├── trust/
│   ├── genesis.py          # Genesis record creation
│   ├── delegation.py       # Delegation chain management
│   ├── gradient.py         # Verification gradient engine
│   ├── audit.py            # Audit anchor chain
│   ├── bundle.py           # Verification bundle generation
│   └── posture.py          # Trust posture state machine
├── api/
│   ├── rest.py             # Nexus REST API handlers
│   ├── mcp.py              # MCP server (FastMCP)
│   ├── cli.py              # CLI commands (Click)
│   └── websocket.py        # WebSocket event streaming
├── persistence/
│   ├── models.py           # DataFlow models
│   ├── queries.py          # Query patterns
│   └── migrations/         # Schema migrations
├── domains/
│   ├── coc/                # CO for Codegen
│   ├── coe/                # CO for Education
│   ├── cog/                # CO for Governance
│   └── loader.py           # Domain configuration loader
├── web/
│   ├── dashboard/          # Web dashboard (React or lightweight alternative)
│   └── static/             # Static assets
└── export/
    ├── bundle.py           # Verification bundle builder
    ├── report.py           # Audit report generator
    └── templates/          # HTML/PDF templates
```

### Data Models (DataFlow)

```python
@db.model
class Session:
    id: int                         # Primary key (DataFlow requirement)
    session_id: str                 # UUID, unique
    workspace_id: str               # Workspace this session belongs to
    domain: str                     # COC, COE, COG, etc.
    state: str                      # creating, active, paused, archived
    genesis_id: str                 # Reference to genesis record
    constraint_envelope: dict       # Active constraints (5 dimensions)
    created_at: datetime
    updated_at: datetime

@db.model
class DeliberationRecord:
    id: int
    session_id: str
    record_type: str                # decision, observation, escalation, intervention
    content: dict                   # Type-specific content
    reasoning_trace: dict           # Full reasoning trace
    reasoning_hash: str             # SHA-256 of canonical JSON
    parent_record_id: str           # Hash chain link
    anchor_id: str                  # EATP audit anchor reference
    created_at: datetime

@db.model
class ConstraintEvent:
    id: int
    session_id: str
    action: str                     # What was attempted
    dimension: str                  # Which constraint dimension
    gradient_result: str            # auto_approved, flagged, held, blocked
    utilization: float              # Current utilization percentage
    resolved_by: str                # human_approved, human_denied, auto, timeout
    created_at: datetime

@db.model
class TrustChainEntry:
    id: int
    session_id: str
    entry_type: str                 # genesis, delegation, attestation, anchor
    payload: dict                   # Type-specific EATP data
    signature: str                  # Ed25519 signature (hex)
    parent_hash: str                # Hash of parent entry
    content_hash: str               # SHA-256 of canonical JSON payload
    created_at: datetime

@db.model
class Workspace:
    id: int
    workspace_id: str               # UUID, unique
    name: str
    domain: str                     # Default domain for sessions
    constraint_template: str        # Default constraint template
    created_at: datetime
    updated_at: datetime
```

### API Contract

All APIs exposed via Nexus (REST + CLI + MCP simultaneously):

```python
# Session management
POST   /sessions              # Create session (with genesis)
GET    /sessions               # List sessions
GET    /sessions/{id}          # Get session details
POST   /sessions/{id}/pause    # Pause session
POST   /sessions/{id}/resume   # Resume session
POST   /sessions/{id}/end      # End session (generate attestation)

# Deliberation
POST   /sessions/{id}/decide   # Record a decision
POST   /sessions/{id}/observe  # Record an observation
GET    /sessions/{id}/timeline # Get deliberation timeline

# Constraints
GET    /sessions/{id}/constraints     # Get current constraint state
PUT    /sessions/{id}/constraints     # Update constraints (with reasoning)
GET    /sessions/{id}/gradient        # Get gradient status

# Trust operations
POST   /sessions/{id}/delegate        # Create delegation
POST   /sessions/{id}/approve/{held}  # Approve held action
POST   /sessions/{id}/deny/{held}     # Deny held action
GET    /sessions/{id}/chain           # Get trust chain

# Verification
POST   /sessions/{id}/verify          # Verify chain integrity
POST   /sessions/{id}/export          # Generate verification bundle
GET    /sessions/{id}/audit           # Get audit report

# MCP tools (exposed via MCP server)
trust_check(action, resource, context)  → verdict
trust_record(action, reasoning_trace)   → anchor_id
trust_escalate(issue, context)          → escalation_id
trust_envelope()                         → constraint_state
trust_status()                           → session_status
```

### Deployment Options

| Mode | Command | Use Case |
|---|---|---|
| **Local** | `praxis serve` | Individual practitioner, development |
| **Docker** | `docker compose up` | Team deployment, consistent environment |
| **Systemd** | `praxis install-service` | Persistent server on Linux |

### Security Requirements

- All trust operations use Ed25519 signatures (via EATP SDK)
- Private keys stored with filesystem permissions (600) or OS keychain
- API authentication via bearer tokens (JWT)
- WebSocket connections require authentication
- Verification bundles are read-only (no write-back path)
- No secrets in logs (trust chain content is signed, not secret)
- Rate limiting on all API endpoints (slowapi, 10K IP cap)

### Testing Strategy

- **Unit tests**: Pure logic — constraint evaluation, gradient calculation, chain validation
- **Integration tests**: Full stack — session lifecycle with real DataFlow, real EATP SDK
- **E2E tests**: Client-to-server — MCP client → Praxis → trust chain → verification bundle
- **Property tests**: Constraint tightening always holds, chains never break, gradients are monotonic
- **Conformance tests**: EATP specification compliance (from EATP SDK conformance suite)
