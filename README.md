# Praxis

**Open-source CO (Cognitive Orchestration) platform for trust-aware human-AI collaboration.**

Praxis makes CO methodology operational — providing session management, trust infrastructure, deliberation capture, and constraint enforcement for human-AI collaboration across any domain.

## What Is Praxis?

CO (Cognitive Orchestration) is the Terrene Foundation's open methodology for structuring human-AI collaboration. Praxis is the runtime platform that enforces it.

Think of it this way: CO describes _how_ humans and AI should collaborate. Praxis is the engine that _makes it happen_ — tracking sessions, capturing deliberation, enforcing constraints, and producing cryptographic proof of human authorization.

### Key Capabilities

- **Session Management** — Persistent collaboration sessions with identity, not stateless interactions
- **Deliberation Capture** — Record human-AI reasoning with cryptographic integrity
- **Constraint Enforcement** — Five-dimensional runtime enforcement (Financial, Operational, Temporal, Data Access, Communication)
- **Trust Infrastructure** — EATP-based trust chains, verification gradient, proof of human authorization
- **Domain Applications** — Pluggable CO domains: COC (codegen), COE (education), COG (governance)
- **Tool Agnostic** — MCP + REST API for integration with any client tool

## Foundation Ecosystem

Praxis is part of the Terrene Foundation's open-source ecosystem:

| Product                                                          | Purpose                                                   | License    |
| ---------------------------------------------------------------- | --------------------------------------------------------- | ---------- |
| **Praxis**                                                       | CO collaboration platform                                 | Apache 2.0 |
| [CARE Platform](https://github.com/terrene-foundation/care)      | Enterprise governance                                     | Apache 2.0 |
| [Kailash SDK](https://github.com/terrene-foundation/kailash)     | Workflow orchestration (Core + DataFlow + Nexus + Kaizen) | Apache 2.0 |
| [EATP SDK](https://github.com/terrene-foundation/eatp)           | Trust protocol SDK                                        | Apache 2.0 |
| [trust-plane](https://github.com/terrene-foundation/trust-plane) | EATP reference implementation                             | Apache 2.0 |

## Quick Start

```bash
# Install
pip install praxis-co

# Or install from source
git clone https://github.com/terrene-foundation/praxis.git
cd praxis
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
praxis init        # Initialize a new CO workspace
praxis session     # Start a collaboration session
```

## Architecture

```
┌─────────────────────────────────────────┐
│            Client Tools                  │
│  (Claude Code, VS Code, Web, Mobile)    │
└────────────┬────────────────────────────┘
             │ MCP / REST API
┌────────────▼────────────────────────────┐
│           Praxis Runtime                 │
│                                          │
│  Session Manager → Deliberation Capture  │
│         ↓                ↓               │
│     Constraint Enforcer (EATP)           │
│         ↓                                │
│     Trust Plane (cryptographic chains)   │
└──────────────────────────────────────────┘
```

**Trust is the medium, not the camera.** Every AI action flows through the trust layer — constraints are enforced at execution time, not observed after the fact.

## CO Domain Applications

Praxis hosts domain-specific CO applications:

- **COC** (Codegen) — Anti-amnesia patterns, institutional knowledge engineering, Human-on-the-Loop development
- **COE** (Education) — Process-based assessment using deliberation logs, academic integrity through cryptographic proof
- **COG** (Governance) — Constitutional compliance, governance workflow orchestration

Each domain is a configuration layer: domain-specific constraint templates, capture rules, and assessment criteria.

## Built With

Praxis is built on Foundation-owned open-source frameworks:

- [**Kailash Core SDK**](https://github.com/terrene-foundation/kailash) — Workflow orchestration (140+ nodes)
- [**Kailash DataFlow**](https://github.com/terrene-foundation/kailash) — Zero-config database operations
- [**Kailash Nexus**](https://github.com/terrene-foundation/kailash) — Multi-channel deployment (API + CLI + MCP)
- [**Kailash Kaizen**](https://github.com/terrene-foundation/kailash) — AI agent framework
- [**EATP SDK**](https://github.com/terrene-foundation/eatp) — Trust protocol implementation
- [**trust-plane**](https://github.com/terrene-foundation/trust-plane) — EATP reference implementation (trust chain management, verification)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
black --check src/

# Type check
mypy src/
```

## Standards

Praxis implements three open standards published by the Terrene Foundation:

| Standard | Full Name                                      | Type                    |
| -------- | ---------------------------------------------- | ----------------------- |
| **CO**   | Cognitive Orchestration                        | Methodology (CC BY 4.0) |
| **EATP** | Enterprise Agent Trust Protocol                | Protocol (CC BY 4.0)    |
| **CARE** | Collaborative Autonomous Reflective Enterprise | Philosophy (CC BY 4.0)  |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

Apache 2.0 — see [LICENSE](LICENSE).

Copyright 2026 Terrene Foundation.
