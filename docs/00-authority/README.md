# Authority Documents

This directory contains authoritative reference documents for the Praxis codebase.

## Contents

| Document               | Purpose                                                             |
| ---------------------- | ------------------------------------------------------------------- |
| [CLAUDE.md](CLAUDE.md) | Preloaded instructions for AI-assisted development on this codebase |

## Usage

These documents are designed to be loaded at the start of a development session to provide immediate context about the Praxis architecture, conventions, and constraints. They complement the project-level `CLAUDE.md` at the repository root, which covers project identity, governance, and Foundation context. The documents here focus on implementation-level guidance.

## Current State (v0.1.0)

The Praxis platform is fully implemented with:

- **Trust layer**: Ed25519 key management, genesis records, delegation chains with constraint tightening, append-only audit chains with DB persistence, verification gradient, full chain verification
- **Core layer**: Session state machine, hash-chained deliberation engine, 5-dimensional constraint enforcer with held action management, CO Layer 5 learning pipeline (5 pattern detectors), Bainbridge Irony detection (fatigue, capability, constraint review), calibration analysis, domain rule engine, session audit reviewer
- **Domain layer**: 6 CO domains (COC, COE, COG, COR, COComp, COF), extended YAML schema with knowledge classification, anti-amnesia rules, and domain procedural rules, progressive disclosure, export/import/diff
- **API layer**: 29 framework-independent handlers, RESTful URL routing, 5 MCP tools, WebSocket events, JWT auth with timing-safe comparison, rate limiting, constraint enforcement middleware, error sanitization
- **MCP proxy**: Trust-mediating MCP stdio proxy with tool interception, constraint enforcement, auto-capture of deliberation and audit, tool dimension classification, JSON-RPC fallback
- **Persistence layer**: 9 DataFlow models, raw sqlite3 CRUD helpers with column validation, JSON serialization
- **Export layer**: Self-contained ZIP verification bundles with browser-based Ed25519 verification, HTML/JSON audit reports
- **CLI**: Full command suite including session, deliberation, constraint, trust, domain, learning, and MCP commands
- **Security**: 5 defense-in-depth layers (column validation, rate limiting, timing-safe auth, error sanitization, key file protection)
- **Tests**: 1141 tests across unit, integration, and end-to-end tiers
