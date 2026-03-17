# Risk Analysis: Praxis CO Platform

**Date**: 2026-03-15
**Analyst**: Deep Analysis Specialist
**Complexity Score**: 27 (Complex)
**Status**: Complete

---

## Executive Summary

Praxis faces ten significant risks spanning technical, adoption, integration, scope, and trust dimensions. The most critical risks are adoption friction (three new standards required simultaneously), scope overextension (five personas and six-plus domains from v0.1.0), and the dependency chain depth (six Foundation packages, all early-stage). The deepest risk is philosophical: Praxis asks organizations to change how they think about AI collaboration, not just what tools they use.

---

## I. Complexity Assessment

| Dimension | Score (1-10) | Justification |
|-----------|-------------|---------------|
| **Governance** | 8 | Three open standards (CO, EATP, CARE) must be correctly implemented. Standards are still in draft. |
| **Technical** | 9 | Cryptographic trust chains, five-dimensional constraint enforcement, MCP proxy architecture, session management, deliberation capture, domain engine -- each is a system; together they are an architecture. |
| **Strategic** | 10 | Novel category creation. No established market. Must educate users on the problem before selling the solution. Five personas, six-plus domains. |

**Total: 27 (Complex)** — highest complexity tier.

---

## II. Risk Register: Top 10 Failure Points

### Risk 1: Adoption Friction — Three Standards Is Too Many

| Attribute | Value |
|-----------|-------|
| **Category** | Adoption |
| **Likelihood** | High (4/5) |
| **Impact** | Critical (5/5) |
| **Priority** | CRITICAL |

Praxis requires users to accept three new open standards: CO, EATP, CARE. Together they create a conceptual barrier that few organizations will voluntarily climb.

**Root cause**: Standards were designed for composability and independent adoption, but the reference implementation requires all three simultaneously.

**Mitigation**:
- Lead with domain value (COC, COE, COG), not protocol value
- Make the standards invisible to end users
- Create progressive adoption path: start with COC, add trust infrastructure as pain is felt
- Publish "zero-to-first-session" guides requiring zero standards knowledge

**Success Criteria**: 80% of first-time users complete first session without reading any specification.

---

### Risk 2: Scope Overextension — Five Personas, Six Domains

| Attribute | Value |
|-----------|-------|
| **Category** | Scope |
| **Likelihood** | High (4/5) |
| **Impact** | Critical (5/5) |
| **Priority** | CRITICAL |

Attempting to serve all personas and domains from v0.1.0 risks delivering none of them well.

**Root cause**: Implementation scope inherited from standards specification scope rather than independently scoped.

**Mitigation**:
- Phase 1: COC only. One persona: CLI practitioner.
- Phase 2: Add IDE practitioner persona.
- Phase 3: Add COE as second domain, with non-technical collaborator persona.
- Phase 4: Add supervisor and auditor personas.
- Phase 5: Remaining domains.

**Success Criteria**: Phase 1 has 100 active COC users before Phase 2 begins.

---

### Risk 3: Dependency Chain Depth — Six Foundation Packages

| Attribute | Value |
|-----------|-------|
| **Category** | Technical |
| **Likelihood** | Medium (3/5) |
| **Impact** | Critical (5/5) |
| **Priority** | CRITICAL |

All six Foundation packages are pre-1.0 with evolving APIs, creating compound stability risk.

**Mitigation**:
- Pin all dependency versions explicitly (already done)
- Create integration tests verifying Praxis works with pinned versions
- Establish monthly dependency update cadence with regression testing
- Maintain compatibility matrix

**Success Criteria**: Zero dependency-caused regressions in any release.

---

### Risk 4: Camera-to-Medium Transition — Architectural Novelty

| Attribute | Value |
|-----------|-------|
| **Category** | Technical |
| **Likelihood** | Medium (3/5) |
| **Impact** | Major (4/5) |
| **Priority** | MAJOR |

Translating "trust is the medium" from principle to production code for arbitrary AI tools across arbitrary domains is the hardest unsolved technical challenge.

**Mitigation**:
- Start with proven architecture: MCP proxy from trust-plane experiment
- Extend one client at a time: Claude Code first, VS Code second, web third
- Accept some clients operate in "camera mode" initially while medium architecture matures

**Success Criteria**: MCP proxy mediates 100% of tool calls for at least one client with <50ms latency overhead.

---

### Risk 5: Cryptographic Overhead — Performance at Scale

| Attribute | Value |
|-----------|-------|
| **Category** | Technical |
| **Likelihood** | Medium (3/5) |
| **Impact** | Major (4/5) |
| **Priority** | MAJOR |

Every action flows through constraint evaluation, audit anchor creation, and chain extension. This adds latency to every interaction.

**Mitigation**:
- Use verification gradient: Quick (~1ms) for low-risk, Standard (~5ms) for moderate, Full (~50ms) for critical
- Cache constraint evaluation results where constraints haven't changed
- Perform cryptographic operations asynchronously where possible
- Benchmark continuously with latency budgets in CI

**Success Criteria**: P95 overhead <10ms Quick, <25ms Standard, <100ms Full.

---

### Risk 6: MCP Ecosystem Maturity — Protocol Still Evolving

| Attribute | Value |
|-----------|-------|
| **Category** | Integration |
| **Likelihood** | Medium (3/5) |
| **Impact** | Major (4/5) |
| **Priority** | MAJOR |

MCP is young and still evolving. Breaking changes require Praxis changes.

**Mitigation**:
- Isolate MCP behind abstraction layer (Nexus provides this)
- Support REST API as fallback protocol
- Monitor and contribute to MCP specification

**Success Criteria**: MCP breaking changes absorbed within one sprint (2 weeks).

---

### Risk 7: Trust Bootstrapping — Who Trusts the Trust Platform?

| Attribute | Value |
|-----------|-------|
| **Category** | Trust |
| **Likelihood** | Medium (3/5) |
| **Impact** | Major (4/5) |
| **Priority** | MAJOR |

A trust platform must itself be trusted. For a v0.1.0 project, establishing initial credibility is a genuine challenge.

**Mitigation**:
- Independent security audit of EATP cryptographic implementation before v1.0
- Use well-established primitives (Ed25519, SHA-256, RFC 8785 JCS)
- Open-source everything so trust is verifiable, not asserted
- Build track record through pilot deployments

**Success Criteria**: Independent security audit completed before v1.0. Zero cryptographic vulnerabilities in first 12 months.

---

### Risk 8: Knowledge Compounding — Does Layer 5 Actually Work?

| Attribute | Value |
|-----------|-------|
| **Category** | Strategic |
| **Likelihood** | Medium (3/5) |
| **Impact** | Significant (3/5) |
| **Priority** | SIGNIFICANT |

CO Principle 7 asserts knowledge compounds -- a testable hypothesis, not a proven fact. If knowledge does not compound, one of CO's seven pillars falls.

**Mitigation**:
- Make observation capture automatic (zero human effort)
- Make curation lightweight (approve/reject, not write)
- Demonstrate compounding effects early with measurable metrics

**Success Criteria**: Measurable quality improvement (>10%) from session 1 to session 10.

---

### Risk 9: Foundation Single Point of Failure

| Attribute | Value |
|-----------|-------|
| **Category** | Strategic |
| **Likelihood** | Low (2/5) |
| **Impact** | Critical (5/5) |
| **Priority** | SIGNIFICANT |

All standards, SDKs, and the platform are owned by one Foundation. If it fails, the entire stack is affected.

**Mitigation**:
- Recruit external contributors and maintainers aggressively
- Establish independent governance for standards
- Apache 2.0 ensures code survives regardless

**Success Criteria**: At least 3 external maintainers within 18 months of v1.0.

---

### Risk 10: Conceptual Heaviness — "What Problem Does This Solve?"

| Attribute | Value |
|-----------|-------|
| **Category** | Adoption |
| **Likelihood** | High (4/5) |
| **Impact** | Significant (3/5) |
| **Priority** | SIGNIFICANT |

The value proposition requires understanding novel concepts. Competitors describe themselves in terms practitioners already understand.

**Mitigation**:
- Describe Praxis in outcomes: "prove your AI was authorized," "guarantee your AI follows the rules"
- Create domain-specific landing pages
- Show, don't tell: interactive demos
- Market will come as AI autonomy increases

**Success Criteria**: First-time users explain Praxis's value in one sentence after a 10-minute demo.

---

## III. Risk Prioritization Matrix

```
                     Impact
                 1    2    3    4    5
            +----+----+----+----+----+
         5  |    |    |    |    |    |
            +----+----+----+----+----+
         4  |    |    | R10|R4  |R1  |
            |    |    |    |R5  |R2  |
            |    |    |    |R6  |    |
            +----+----+----+----+----+
         3  |    |    | R8 |R7  |R3  |
            +----+----+----+----+----+
         2  |    |    |    |    |R9  |
            +----+----+----+----+----+
         1  |    |    |    |    |    |
            +----+----+----+----+----+

CRITICAL:     R1 (Adoption Friction), R2 (Scope), R3 (Dependencies)
MAJOR:        R4 (Camera-to-Medium), R5 (Crypto Overhead),
              R6 (MCP Maturity), R7 (Trust Bootstrap)
SIGNIFICANT:  R8 (Knowledge Compounding), R9 (Foundation SPOF),
              R10 (Conceptual Heaviness)
```

---

## IV. Inconsistencies Found

1. **CLAUDE.md lists three domain applications (COC, COE, COG).** Briefs list six. Additional three have minimal specification. Scope risk applies.

2. **pyproject.toml declares `Development Status :: 1 - Planning`.** Underlying components (trust-plane, EATP SDK) are more mature. Accurate for Praxis as product but understates foundation maturity.

3. **"Six Problems" list omits the orchestration gap as a first-class item.** It is mentioned but not numbered or in the architecture diagram. This gap motivates Praxis's existence as a runtime.

---

## V. Decision Points Requiring Stakeholder Input

1. **Launch scope**: One persona + one domain, or broader? Risk 2 argues strongly for narrow.
2. **Trust-plane absorption**: Separate dependency or absorbed into Praxis?
3. **Security audit timing**: Before or after v1.0?
4. **MCP protocol version**: Target version and multi-version support?
5. **Performance budgets**: Acceptable latency overhead per action?
6. **External maintainers**: Recruitment plan?

---

## VI. Recommended Implementation Phases

| Phase | Timeline | Focus | Target |
|-------|----------|-------|--------|
| **0: Foundation** | Months 1-2 | Core session manager, constraint enforcer | CLI practitioner, COC only |
| **1: Minimum Viable Medium** | Months 3-4 | MCP proxy with enforcement, deliberation capture | Working trust-as-medium for Claude Code |
| **2: Developer Experience** | Months 5-6 | COC fully operational, VS Code integration | Developer adoption |
| **3: Second Domain** | Months 7-9 | COE domain, non-technical persona, academic pilot | Prove domain portability |
| **4: Enterprise Readiness** | Months 10-12 | Supervisor/auditor personas, security audit | Enterprise pilots |
