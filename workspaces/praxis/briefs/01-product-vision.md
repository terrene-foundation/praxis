# Praxis — Product Vision

## What Praxis Is

Praxis is the Terrene Foundation's open-source CO (Cognitive Orchestration) platform — a runtime engine for trust-aware human-AI collaboration across any domain.

CO is the methodology. Praxis is the engine that enforces it.

Where existing AI tools (Claude Code, Cursor, ChatGPT) provide raw AI capability, Praxis adds the governance layer that makes AI collaboration auditable, constrained, and trustworthy. It tracks sessions, captures deliberation, enforces constraints, and produces cryptographic proof of human authorization.

## Why Praxis Exists

### The Problem

Every AI tool today operates statelessly. Each session starts from zero. There is no persistent identity, no constraint enforcement, no audit trail, and no proof that a human supervised the AI's work. This creates three failure modes identified by CO methodology:

1. **Amnesia** — AI forgets instructions and decisions as context fills up
2. **Convention drift** — AI follows generic practices instead of your organization's standards
3. **Safety blindness** — AI optimizes for task completion over regulatory, compliance, and approval requirements

These failures are not model problems — they affect every model equally. They are infrastructure problems. And infrastructure problems require infrastructure solutions.

### The Insight: Trust as Medium, Not Camera

The trust-plane experiment (March 2026) proved that bolting trust onto existing tools doesn't work. When trust infrastructure watches AI from the side (like a security camera), it is:

- Trivially gameable (logs can be fabricated after the fact)
- Not enforced (constraints exist as data but have no consequences)
- Not portable (each tool must reimagine the orchestration)

The correct architecture makes trust the **medium** through which AI operates. Every AI action flows through the trust layer. Constraints are enforced at execution time. Audit anchors are produced as a side effect of execution, not recorded afterward.

Praxis IS that medium.

### The Gap

No existing tool provides:

| Capability | Claude Code | Cursor | ChatGPT | Praxis |
|---|---|---|---|---|
| Persistent sessions across interactions | No | No | Partial | Yes |
| Cryptographic proof of human authorization | No | No | No | Yes |
| Runtime constraint enforcement | No | No | No | Yes |
| Deliberation capture with hash chains | No | No | No | Yes |
| Domain-agnostic (not just codegen) | No | No | Partial | Yes |
| Verification gradient (graduated control) | No | No | No | Yes |
| Independent third-party verification | No | No | No | Yes |

## Who Praxis Serves

### Five Personas

1. **The CLI Practitioner** — Developer, researcher, or analyst who works in a terminal with AI assistants. Needs trust infrastructure that integrates with their existing workflow (MCP, CLI).

2. **The IDE Practitioner** — Works primarily in an IDE (VS Code, Cursor, Windsurf) with AI integration. Needs trust infrastructure accessible from within the editor.

3. **The Non-Technical Collaborator** — Uses AI through chat interfaces or desktop apps. No terminal, no IDE. Needs trust infrastructure through a web or desktop application.

4. **The Supervisor** — Reviews others' AI-assisted work. Does not use AI directly. Needs read-only verification dashboards to confirm trust compliance.

5. **The External Auditor** — Independent verification of trust records. No prior relationship with the practitioner. Needs self-contained verification bundles that can be checked without installing any software.

### Domain Applications

Praxis is domain-agnostic. The same runtime serves:

| Domain | Application | Example Use |
|---|---|---|
| Software Development | COC | Building code with governed AI agents |
| Education | COE | Student-AI collaboration with deliberation-based assessment |
| Governance | COG | Organizational decision-making with AI advisors |
| Research | COR | Academic writing, data analysis, literature review with audit trails |
| Compliance | COComp | Regulatory audits with constrained AI assistants |
| Finance | COF | Financial analysis with spending constraints and approval workflows |

Each domain is a **configuration layer** — domain-specific constraint templates, agent definitions, capture rules, and assessment criteria loaded on top of the same Praxis runtime.

## What Praxis Must Be

### Full-Featured, Not Stripped-Down

Praxis is not a demo, proof-of-concept, or limited version of anything. It is a complete, production-grade platform that stands on its own. Every feature it ships must be fully implemented, properly tested, and genuinely useful.

### Genuinely Open

Apache 2.0 licensed, Foundation-owned, irrevocably open. No "open core" bait-and-switch. No features that exist only to upsell. No artificial limitations. The community must trust that Praxis serves them, not a commercial agenda.

### Standards-First

Praxis implements three open standards published by the Terrene Foundation (all CC BY 4.0):

- **CO** (Cognitive Orchestration) — The methodology
- **EATP** (Enterprise Agent Trust Protocol) — The trust protocol
- **CARE** (Collaborative Autonomous Reflective Enterprise) — The governance philosophy

Any organization can build products on these standards. Praxis is the Foundation's reference implementation that proves the standards work.

## Core Capabilities

### 1. Session Management

Persistent, identity-aware collaboration sessions. Not stateless chat — sessions that remember who you are, what constraints apply, what decisions were made, and what the AI was authorized to do.

- Session lifecycle: Create → Active → Pause → Resume → Archive
- Persistent identity across interactions
- Session history with full audit trail
- Multi-session workspaces for complex projects
- Session export/import for portability

### 2. Deliberation Capture

Cryptographic recording of human-AI reasoning. Every decision produces a signed record that cannot be fabricated after the fact.

- Decision records with reasoning traces
- Confidence scoring (basis points for precision)
- Alternative tracking (what options were considered)
- Evidence linking (what informed the decision)
- Hash-chained temporal integrity (records cannot be reordered)

### 3. Constraint Enforcement

Five-dimensional runtime enforcement that actually prevents actions, not just logs them.

| Dimension | What It Controls | Example |
|---|---|---|
| Financial | Spending limits, token budgets | "Max $50/session" |
| Operational | Allowed/blocked actions | "No file deletion" |
| Temporal | Active hours, deadlines, timeouts | "Only during business hours" |
| Data Access | Read/write paths, data classifications | "No access to /secrets/" |
| Communication | Channels, recipients, content rules | "No external API calls" |

Constraint enforcement is deterministic — not probabilistic, not advisory. When a constraint says "blocked," the action does not proceed.

### 4. Trust Infrastructure

EATP-based cryptographic trust chains providing:

- **Genesis Record** — Root of trust establishing human authority
- **Delegation Records** — Constraint-tightening delegation chains (child never gets more authority than parent)
- **Verification Gradient** — Four-level action classification:
  - AUTO_APPROVED — Routine, within safe bounds
  - FLAGGED — Approaching limits, proceed with visibility
  - HELD — Requires human approval before execution
  - BLOCKED — Forbidden, action rejected
- **Audit Anchors** — Tamper-evident, hash-chained records of every action
- **Verification Bundles** — Self-contained exports for independent third-party verification

### 5. Domain Engine

Pluggable CO domain applications. Each domain defines:

- **Agent team compositions** — Which specialized agents handle which tasks
- **Constraint templates** — Domain-appropriate default constraints
- **Workflow definitions** — Structured phases with approval gates
- **Capture rules** — What deliberation evidence to record
- **Assessment criteria** — How to evaluate collaboration quality

### 6. Multi-Channel Client API

Tool-agnostic integration via:

- **MCP (Model Context Protocol)** — For AI assistant integration (Claude Code, Cursor, etc.)
- **REST API** — For web, mobile, and custom client integration
- **CLI** — Direct terminal access to all capabilities
- **WebSocket** — Real-time event streaming for live dashboards

### 7. Web Dashboard

Browser-based interface for all personas:

- **Practitioner view** — Session management, constraint status, deliberation history
- **Supervisor view** — Read-only verification dashboard, approval queue for held actions
- **Auditor view** — Trust chain inspection, verification bundle generation, compliance reports
- **Analytics** — Session metrics, constraint utilization, trust posture progression

### 8. Desktop Application

Native desktop application (cross-platform) for non-technical collaborators:

- Session management without terminal access
- Visual constraint editor
- Approval workflows for held actions
- Notification system for constraint events
- Offline capability with sync

### 9. Mobile Companion

Mobile application for approval workflows and monitoring:

- Push notifications for held actions
- One-tap approve/deny from anywhere
- Session status monitoring
- Trust chain browsing
- Constraint alerts

### 10. Verification & Export

Independent verification capabilities:

- **Verification Bundles** — Self-contained ZIP/HTML packages with embedded verification code
- **Audit Reports** — Human-readable reports with timeline, constraints, deliberation summary
- **Chain Verification** — Cryptographic validation of entire audit chain integrity
- **Export Formats** — JSON (machine-readable), HTML (browser-viewable), PDF (printable)

## Technical Foundation

### Built On Foundation-Owned Open Source

| Framework | Purpose |
|---|---|
| Kailash Core SDK | Workflow orchestration (140+ nodes) |
| Kailash DataFlow | Zero-config database operations |
| Kailash Nexus | Multi-channel deployment (API + CLI + MCP) |
| Kailash Kaizen | AI agent framework |
| EATP SDK | Trust protocol implementation |
| trust-plane | EATP reference implementation |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
│  CLI │ Web Dashboard │ Desktop App │ Mobile │ MCP │ REST    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Praxis Runtime                              │
│                                                              │
│  ┌────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │ Session    │  │ Deliberation    │  │ Domain           │ │
│  │ Manager    │  │ Capture Engine  │  │ Engine           │ │
│  └─────┬──────┘  └───────┬─────────┘  └────────┬─────────┘ │
│        │                 │                      │            │
│  ┌─────▼─────────────────▼──────────────────────▼─────────┐ │
│  │              Constraint Enforcer                        │ │
│  │  (5 dimensions, deterministic, in the execution path)  │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │              Trust Plane (EATP)                         │ │
│  │  Genesis → Delegation → Constraint → Attestation →     │ │
│  │  Audit Anchor (hash-chained, Ed25519 signed)           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Persistence (DataFlow)                     │ │
│  │  SQLite (dev) │ PostgreSQL (production)                 │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Success Criteria

Praxis succeeds when:

1. A researcher can run `praxis init` and have trust infrastructure for their AI-assisted project in under 60 seconds
2. A student can demonstrate to their professor, via cryptographic proof, that they supervised their AI collaboration
3. A compliance officer can enforce spending limits on AI usage that cannot be bypassed
4. An auditor can independently verify an entire collaboration audit trail without installing any software
5. A developer can switch between Claude Code, Cursor, and VS Code while maintaining the same trust context
6. A supervisor can review and approve held actions from their phone
7. Any domain (codegen, education, governance, research, compliance, finance) can define its own CO configuration and run on Praxis without forking

## What Comes Next

See `02-plans/` for the development roadmap. The plan is organized by what users can DO at each milestone, not by technical components.
