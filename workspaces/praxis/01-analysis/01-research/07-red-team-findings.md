# Red Team Findings

**Date**: 2026-03-15
**Status**: Complete

---

## Seven Structural Gaps

### Gap 1: COE vs COC as First Domain — Scope Contradiction

The value auditor recommends COE (Education) as the killer use case. The red team disagrees — the entire `.claude/` configuration (29 agents, 25+ skills, 8 rules, 9 commands) IS COC infrastructure running in production today. COC has implementation momentum; COE is a specification with zero code.

COE also requires server-side infrastructure, multi-user workflows, and university partnerships — architecturally more complex, not less.

**Decision needed**: COC first (formalize what works) or COE first (stronger market pull)?

### Gap 2: Dependency Showstopper Is Worse Than Stated

None of the six Foundation packages are pip-installable from PyPI. The EATP SDK and trust-plane live inside a monorepo that hasn't been migrated. `pip install praxis` fails immediately.

**This is a blocking precondition, not a risk to mitigate.**

### Gap 3: README Describes Non-Existent Product

The README shows `praxis init`, `praxis session`, and `pip install praxis` — none of which work. This damages credibility on first contact.

### Gap 4: MVP Doesn't Fully Prove "Trust as Medium"

The MVP scope doesn't specify whether Praxis sits BETWEEN the AI and tools (medium) or BESIDE them (camera). The trust-plane experiment's MCP proxy architecture (the actual "medium" implementation) isn't explicitly in the MVP requirements.

### Gap 5: 6-8 Week Timeline Needs Adjustment

With dependency resolution, DataFlow integration, EATP wrapping, and verification bundle generation — the full P0 scope likely needs 10-14 weeks, not 6-8. Consider splitting into MVP-alpha (CLI-only, 6-8 weeks) and MVP-beta (+API +MCP, 6-8 weeks more).

### Gap 6: Missing Risks

- **Self-referential bootstrapping**: Praxis claims to be necessary, but isn't being used to build itself
- **Layer 5 has no implementation precedent**: The observe-capture-evolve pipeline has never been built anywhere
- **No user acquisition strategy**: How does the first user discover Praxis?
- **Trust deskilling**: The deeper Bainbridge's Irony — automating trust degrades the skills needed to exercise trust

### Gap 7: ADR-004 (YAML Domains) vs CO Enforcement Requirements

YAML configuration is loaded into context (Tier 1, soft). CO requires hard enforcement outside the context window (Tier 3). Domain configuration (YAML) and domain enforcement (code) must be distinguished.

---

## Decision Points

1. **COC or COE first?** Evidence supports COC. Market pull supports COE.
2. **Dependency strategy?** Local editable installs for development, PyPI publication as release gate.
3. **MVP-alpha scope?** CLI-only prototype acceptable as first deliverable?
4. **Medium vs camera in MVP?** Must the MVP demonstrate intermediary architecture?
5. **Layer 5 deferral?** CO-L1L2L3L4 partial conformance acceptable for v1.0?
6. **README rewrite?** Should reflect actual state now. (Strong recommendation: yes.)
