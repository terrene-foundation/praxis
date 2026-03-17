# Praxis — Open-Source CO Platform

This repository is **Praxis** — the Terrene Foundation's open-source CO (Cognitive Orchestration) platform for trust-aware human-AI collaboration across any domain.

Praxis is Foundation-owned, Apache 2.0 licensed, and irrevocably open. It implements CO methodology as a runtime platform — providing session management, trust infrastructure, deliberation capture, and constraint enforcement for human-AI collaboration workflows.

## What This Is

An open-source platform that makes CO methodology operational. Where CO is the methodology (how humans and AI should collaborate), Praxis is the engine that enforces it — tracking sessions, capturing deliberation, enforcing constraints, and producing cryptographic proof of human authorization.

**What it is NOT**: A CLI wrapper or IDE plugin. Praxis is the trust-aware runtime that tools connect to. Claude Code, VS Code, desktop apps, and web interfaces are all *clients* of Praxis — not the other way around.

## Foundation Ecosystem

Praxis exists within the Terrene Foundation's open-source ecosystem:

| Product | Purpose | License |
|---------|---------|---------|
| **Praxis** | CO collaboration platform | Apache 2.0 |
| [CARE Platform](https://github.com/terrene-foundation/care) | Enterprise governance | Apache 2.0 |
| [Kailash SDK](https://github.com/terrene-foundation/kailash) | Workflow orchestration (Core SDK) | Apache 2.0 |
| [Kailash DataFlow](https://github.com/terrene-foundation/kailash) | Zero-config database operations | Apache 2.0 |
| [Kailash Nexus](https://github.com/terrene-foundation/kailash) | Multi-channel deployment (API+CLI+MCP) | Apache 2.0 |
| [Kailash Kaizen](https://github.com/terrene-foundation/kailash) | AI agent framework | Apache 2.0 |
| [EATP SDK](https://github.com/terrene-foundation/eatp) | Trust protocol SDK | Apache 2.0 |
| [trust-plane](https://github.com/terrene-foundation/trust-plane) | EATP reference implementation | Apache 2.0 |

- **CARE Platform** governs organizations (enterprise agent trust, ShadowEnforcer, verification gradient)
- **Praxis** powers collaboration (CO sessions, deliberation capture, constraint enforcement for human-AI work)
- Both are built on the Kailash Python SDK (Core + DataFlow + Nexus + Kaizen) and EATP trust layer (EATP SDK + trust-plane)

## CO Domain Applications

Praxis hosts domain-specific CO applications:

| Application | Domain | Description |
|-------------|--------|-------------|
| **COC** | Codegen | CO for software development (anti-amnesia, institutional knowledge) |
| **COE** | Education | CO for learning (process-based assessment, deliberation logs) |
| **COG** | Governance | CO for organizational governance (constitutional compliance) |

Each domain application is a configuration layer on top of Praxis — domain-specific constraint templates, capture rules, and assessment criteria.

## Absolute Directives

These override ALL other instructions.

### 0. Foundation Independence — No Commercial Coupling

Praxis is a **Terrene Foundation project**. It is fully independent. There is NO relationship between Praxis and any commercial product, proprietary codebase, or commercial entity.

**MUST NOT**:

- Reference, discuss, compare with, or design against any proprietary product
- Import, depend on, or interface with any proprietary SDK or codebase
- Use language like "open-source version of X" or "counterpart to Y" — Praxis is its own product
- Consider commercial differentiation, market positioning, or competitive features — that is not a concern of this project
- Reference any Rust SDK, proprietary runtime, or commercial deployment — Praxis uses Foundation-owned open-source tooling exclusively

**MUST**:

- Design Praxis on its own merits as the best possible open-source CO platform
- Reference only Foundation-owned open standards (CARE, EATP, CO) and Foundation-owned SDKs (Kailash Python, EATP SDK, trust-plane)
- Treat Praxis as a standalone product that exists to serve the open-source community
- Make all architectural decisions based on what is best for Praxis users, not based on what any other product does or doesn't do

Third parties may build commercial products on top of Praxis and Foundation standards — that is the intended model. But Praxis itself has no knowledge of, dependency on, or design consideration for any such product.

### 1. Framework-First

Never write code from scratch before checking whether the Kailash frameworks already handle it.

- Instead of direct SQL/SQLAlchemy → check with **dataflow-specialist**
- Instead of FastAPI/custom API → check with **nexus-specialist**
- Instead of custom MCP server/client → check with **mcp-specialist**
- Instead of custom agent platform → check with **kaizen-specialist**

### 2. .env Is the Single Source of Truth

All API keys and model names MUST come from `.env`. Never hardcode model strings. Root `conftest.py` auto-loads `.env` for pytest.

### 3. Implement, Don't Document

When you discover a missing feature, endpoint, or record — **implement or create it**. Do not note it as a gap and move on.

### 4. Standards Alignment

Every implementation decision must align with CO, EATP, and CARE specifications. Praxis is the reference implementation of CO methodology — it must embody the seven first principles correctly.

### 5. Trust Is the Medium

Trust infrastructure must be the medium through which AI operates, not a camera watching from the side. Every AI action flows through the trust layer — constraints are enforced at execution time, not observed after the fact.

## Architecture Overview

### The Six Problems Praxis Solves

These were identified through the trust-plane experiment (Claude Code session, March 2026):

1. **AI operates Trust Plane** — AI shouldn't manage its own trust infrastructure
2. **No constraint enforcement** — Rules are advisory without runtime enforcement
3. **Camera problem** — Trust infrastructure watches instead of mediating
4. **No session tracking** — No persistent identity across collaboration sessions
5. **No proof of human authorization** — Human decisions leave no cryptographic trail
6. **Verification gradient not applied** — Classification without consequences

Plus the **orchestration gap**: AI carries all trust orchestration burden (not portable across tools).

### Core Architecture

```
┌─────────────────────────────────────────────────┐
│                 Client Tools                     │
│  (Claude Code, VS Code, Desktop, Web, Mobile)   │
└──────────────┬──────────────────────────────────┘
               │ MCP / API
┌──────────────▼──────────────────────────────────┐
│              Praxis Runtime                       │
│  ┌─────────────┐  ┌──────────────┐              │
│  │ Session Mgr  │  │ Deliberation │              │
│  │              │  │ Capture      │              │
│  └──────┬──────┘  └──────┬───────┘              │
│         │                │                       │
│  ┌──────▼────────────────▼───────┐              │
│  │     Constraint Enforcer       │              │
│  │  (EATP SDK enforce module)    │              │
│  └──────┬────────────────────────┘              │
│         │                                        │
│  ┌──────▼──────────────────────┐                │
│  │    Trust Plane (EATP)       │                │
│  │  Genesis → Delegation →     │                │
│  │  Constraint → Attestation   │                │
│  └─────────────────────────────┘                │
└──────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Built With |
|-----------|---------|------------|
| Session Manager | Persistent collaboration sessions with identity | Kailash Core SDK |
| Deliberation Capture | Record human-AI reasoning with cryptographic integrity | EATP SDK |
| Constraint Enforcer | Runtime enforcement of five constraint dimensions | EATP enforce module |
| Trust Plane | Cryptographic trust chains, verification gradient | trust-plane |
| Domain Engine | Pluggable CO domain applications (COC, COE, COG) | Kaizen agents |
| Client API | MCP + REST for tool integration | Nexus |
| Persistence | Session and trust data storage | DataFlow |

## Critical Execution Rules

```python
# ALWAYS: runtime.execute(workflow.build())
# NEVER: workflow.execute(runtime)
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())

# Async (Docker/FastAPI):
runtime = AsyncLocalRuntime()
results, run_id = await runtime.execute_workflow_async(workflow.build(), inputs={})

# String-based nodes only
workflow.add_node("NodeType", "node_id", {"param": "value"})

# Return structure is always (results, run_id)
```

## Kailash Platform

| Framework | Purpose | Install |
|-----------|---------|---------|
| **Core SDK** | Workflow orchestration, 140+ nodes | `pip install kailash` |
| **DataFlow** | Zero-config database operations | `pip install kailash-dataflow` |
| **Nexus** | Multi-channel deployment (API+CLI+MCP) | `pip install kailash-nexus` |
| **Kaizen** | AI agent framework | `pip install kailash-kaizen` |

All frameworks are built ON Core SDK — they don't replace it.

## The Trinity

| Standard | Full Name | Type | License |
|----------|-----------|------|---------|
| **CARE** | Collaborative Autonomous Reflective Enterprise | Philosophy | CC BY 4.0 |
| **EATP** | Enterprise Agent Trust Protocol | Protocol | CC BY 4.0 |
| **CO** | Cognitive Orchestration | Methodology | CC BY 4.0 |

- **COC** = CO for Codegen (first domain application of CO)
- CARE planes: **Trust Plane** + **Execution Plane**
- Constraint dimensions: Financial, Operational, Temporal, Data Access, Communication
- CO seven first principles: Structured Dialogue, Deliberation Capture, Trust Verification, Constraint Enforcement, Human-on-the-Loop, Continuous Learning, Domain Portability

## Workspace Commands

| Command | Phase | Purpose |
|---------|-------|---------|
| `/start` | — | New user orientation |
| `/analyze` | 01 | Research and validate |
| `/todos` | 02 | Create project roadmap |
| `/implement` | 03 | Build one task at a time |
| `/redteam` | 04 | Test from adversarial angles |
| `/codify` | 05 | Capture knowledge |
| `/ws` | — | Check project status |
| `/wrapup` | — | Save progress before ending |

## Key Reference Locations

| Content | Location |
|---------|----------|
| Foundation truths | `~/repos/terrene/terrene/docs/00-anchor/` |
| Standards (CARE, EATP, CO) | `~/repos/terrene/terrene/docs/02-standards/` |
| CARE Platform (governance) | `~/repos/terrene/care/` |
| Trust Plane experiment | `~/repos/terrene/terrene/workspaces/trust-plane/` |
| COE workspace | `~/repos/terrene/terrene/workspaces/coe/` |
