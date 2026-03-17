# Praxis Project Agents

Specialized agents for the Praxis codebase. These supplement the general-purpose agents in the parent `.claude/agents/` directory with deep knowledge of Praxis-specific modules, patterns, and invariants.

## Agent Catalog

| Agent                         | When to Use                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **praxis-trust-expert**       | Working on Ed25519 crypto, genesis records, delegation chains, audit anchors, chain verification, JCS canonicalization, key management, key zeroization, or symlink protection (`src/praxis/trust/`)                                                                                                                                            |
| **praxis-constraint-expert**  | Working on the 5-dimensional constraint enforcer, gradient verdicts (70/90/100 thresholds), held action management, constraint tightening, temporal auto-tracking, financial spend accumulation, enforcement middleware, or phase enforcement (`src/praxis/core/constraint.py`, `src/praxis/trust/gradient.py`, `src/praxis/api/middleware.py`) |
| **praxis-domain-expert**      | Working on CO domain YAML configs, the DomainLoader, schema validation, workflow phases, capture rules, anti-amnesia rules, domain rules, knowledge classification, progressive disclosure, domain export/import/diff, or adding/modifying any of the 6 domains (`src/praxis/domains/`)                                                         |
| **praxis-cli-expert**         | Working on Click commands, Rich output, workspace state (`.praxis/` directory), session lifecycle from CLI, deliberation persistence, learning commands, domain management commands, MCP proxy commands, or bundle export/verify (`src/praxis/cli.py`)                                                                                          |
| **praxis-api-expert**         | Working on Nexus handlers (29 total), RESTful routes, MCP tools, WebSocket events, JWT auth, rate limiting, enforcement middleware, error sanitization, or the app factory (`src/praxis/api/`)                                                                                                                                                  |
| **praxis-bundle-expert**      | Working on BundleBuilder, bundle ZIP structure, client-side SubtleCrypto verification, the HTML/JS viewer, serve.py localhost binding, or audit reports (`src/praxis/export/`)                                                                                                                                                                  |
| **praxis-learning-expert**    | Working on the CO Layer 5 learning pipeline: observation capture, pattern detection (5 types), evolution proposals, human approval gate, or learning persistence models (`src/praxis/core/learning.py`, `src/praxis/core/learning_observers.py`)                                                                                                |
| **praxis-persistence-expert** | Working on DataFlow model definitions (9 models), db_ops CRUD helpers (raw sqlite3), column validation, JSON serialization, table name mapping, or the DataFlow registration pipeline (`src/praxis/persistence/`)                                                                                                                               |
| **praxis-mcp-expert**         | Working on the MCP proxy: tool call interception, constraint enforcement in proxy, auto-capture of deliberation/audit, tool dimension classification, downstream server management, or the JSON-RPC fallback (`src/praxis/mcp/proxy.py`)                                                                                                        |
| **praxis-implementer**        | Coordinating multi-file changes across the codebase, implementing new features that span multiple modules, or needing to understand the dependency graph and correct implementation order                                                                                                                                                       |

## When to Use Which

### Single-Module Changes

Use the specialist for that module:

- Trust chain bug -> **praxis-trust-expert**
- Constraint evaluation issue -> **praxis-constraint-expert**
- New domain config -> **praxis-domain-expert**
- CLI command change -> **praxis-cli-expert**
- API endpoint addition -> **praxis-api-expert**
- Bundle viewer fix -> **praxis-bundle-expert**
- Learning pattern detector bug -> **praxis-learning-expert**
- Database model change -> **praxis-persistence-expert**
- MCP proxy tool classification -> **praxis-mcp-expert**

### Multi-Module Changes

Use **praxis-implementer** to coordinate, then delegate to specialists:

- New feature (e.g., "add attestation records") -> implementer identifies affected layers (trust + core + api + cli), then specialists handle each layer
- Bug spanning modules -> implementer traces the issue through the dependency graph

### Common Combinations

- **Trust + Constraint**: Changes to gradient evaluation (consolidated in `trust/gradient.py`)
- **Domain + Constraint**: Adding/modifying constraint templates
- **API + CLI**: Exposing existing functionality through both channels
- **Trust + Bundle**: Changes to chain verification or export format
- **Learning + Persistence**: Changes to observation storage or pattern detection
- **MCP Proxy + Constraint**: Changes to tool dimension classification or enforcement
- **Bainbridge + Learning**: Fatigue detection feeds into learning pipeline observations

## Key Invariants All Agents Know

These invariants are documented in every specialist agent:

1. **Gradient thresholds are normative**: 70% / 90% / 100% -- not configurable
2. **Five constraint dimensions are canonical**: financial, operational, temporal, data_access, communication -- exact names, exact order
3. **Constraints only tighten**: Never loosen in sessions or delegations
4. **JCS canonicalization required**: Never use `json.dumps()` for hashing
5. **Handlers never raise**: Always return error dicts via `error_from_exception()`
6. **All config from .env**: Via `PraxisConfig` -- never hardcode
7. **Trust is the medium**: Not a camera -- enforcement at execution time
8. **Learning proposals require human approval**: Nothing is auto-applied
9. **Column names validated**: SQL injection prevention via regex in db_ops
10. **Observation failures never propagate**: Learning observers catch all exceptions silently
