# Domain Applications

## CO Is Domain-Agnostic

Praxis implements CO (Cognitive Orchestration) as a domain-agnostic runtime. The seven first principles — Institutional Knowledge, Brilliant New Hire, Three Failure Modes, Human-on-the-Loop, Deterministic Enforcement, Bainbridge's Irony, Knowledge Compounds — apply equally to software engineering, education, research, governance, compliance, and finance.

Each domain is a **configuration layer** on the same runtime. A domain application defines:

1. **Agent team compositions** — Which specialized agents handle which tasks
2. **Constraint templates** — Domain-appropriate default constraints
3. **Workflow phases** — Structured stages with approval gates
4. **Capture rules** — What deliberation evidence to record and how
5. **Assessment criteria** — How to evaluate the quality of human-AI collaboration

## Domain Application Template

Every domain application follows this structure:

```
domains/
└── {domain}/
    ├── domain.yml              # Domain metadata and description
    ├── constraints/
    │   ├── default.yml         # Default constraint envelope
    │   └── templates/          # Constraint presets (strict, moderate, permissive)
    ├── agents/
    │   ├── teams.yml           # Agent team compositions per workflow phase
    │   └── definitions/        # Agent role definitions
    ├── workflows/
    │   ├── phases.yml          # Workflow phases and approval gates
    │   └── evidence.yml        # What evidence each phase produces
    ├── capture/
    │   ├── rules.yml           # What deliberation to capture
    │   └── assessment.yml      # Quality assessment criteria
    └── knowledge/
        ├── institutional.yml   # Domain-specific institutional knowledge
        └── anti-amnesia.yml    # P0-P3 priority classification
```

---

## Domain: COC (CO for Codegen)

**Purpose**: Software development with governed AI agents.

**Agent teams**:

| Phase | Agents | Purpose |
|---|---|---|
| Analyze | deep-analyst, requirements-analyst, sdk-navigator | Research and validate the project idea |
| Plan | todo-manager, requirements-analyst, framework-advisor | Create comprehensive development roadmap |
| Implement | tdd-implementer, testing-specialist, code-reviewer, security-reviewer | Build one task at a time |
| Validate | e2e-runner, value-auditor, security-reviewer | Test from user and adversarial perspectives |
| Codify | documentation-validator, pattern-observer | Capture institutional knowledge |

**Constraint templates**:

| Template | Financial | Operational | Temporal | Data Access | Communication |
|---|---|---|---|---|---|
| **Strict** | $10/session | No deploy, no delete | Business hours | Read src/, write src/ only | No external APIs |
| **Moderate** | $50/session | Deploy to staging | 8h max session | Read/write project dirs | Approved APIs only |
| **Permissive** | $200/session | Full operations | No limit | Full filesystem | All external |

**Workflow phases**:

```
/analyze → /todos → /implement → /redteam → /codify → /deploy
```

Each phase has an approval gate. Human reviews output before the next phase begins.

**Capture rules**:
- Every file change produces an audit anchor
- Architecture decisions recorded as reasoning traces
- Test results attached to milestone records
- Security review attestations required before deployment

**Assessment criteria**:
- Test coverage (quantitative)
- Security review completion (attestation-based)
- Architecture decision quality (reasoning trace evaluation)
- Knowledge capture completeness (institutional knowledge growth)

---

## Domain: COE (CO for Education)

**Purpose**: Student-AI collaboration with process-based assessment.

**The educational insight**: CO's five layers become a pedagogical progression. Students don't just use AI — they learn to structure AI collaboration, which is the skill that matters.

| Year | CO Layers Available | What's Assessed |
|---|---|---|
| 1 | Guardrails only (given) | Quality of work within fixed constraints |
| 2 | Guardrails + Context (partial) | Ability to define institutional knowledge |
| 3 | All five layers (full) | Quality of the entire CO setup + output |
| 4 | Meta (teach others) | Setup usability by other students |

**Agent teams**:

| Phase | Agents | Purpose |
|---|---|---|
| Research | literature-reviewer, methodology-advisor | Guide research process |
| Draft | writing-assistant, citation-manager | Support drafting with proper attribution |
| Review | peer-review-simulator, methodology-critic | Simulate peer review |
| Revise | revision-tracker, consistency-checker | Track changes and reasoning |

**Constraint templates**:

| Template | Financial | Operational | Temporal | Data Access | Communication |
|---|---|---|---|---|---|
| **Year 1** | $5/session | Read-only, no generation | Class period | Course materials only | No external |
| **Year 2** | $15/session | Read + draft | Assignment period | Course + library | Approved sources |
| **Year 3** | $30/session | Full operations | Project duration | Full access | All sources |

**Capture rules**:
- Every AI interaction produces a deliberation record
- Decision points captured with explicit reasoning
- Revision history tracked at paragraph level
- Time-on-task captured (not just output)

**Assessment criteria** (Mirror Thesis):
- **What the student decided** (not what the AI generated)
- **Why they decided it** (reasoning quality)
- **What alternatives they considered** (critical thinking)
- **Where they intervened** (escalation and intervention records)
- **How they evolved constraints** (institutional design ability)

---

## Domain: COG (CO for Governance)

**Purpose**: Organizational decision-making with AI advisors under constitutional constraints.

**Agent teams**:

| Phase | Agents | Purpose |
|---|---|---|
| Analyze | policy-analyst, regulatory-scanner | Analyze governance context |
| Propose | proposal-drafter, impact-assessor | Draft proposals with impact analysis |
| Review | constitutional-reviewer, stakeholder-analyst | Check against organizational constitution |
| Decide | decision-recorder, precedent-tracker | Record decisions with full reasoning |

**Constraint templates**:

| Template | Financial | Operational | Temporal | Data Access | Communication |
|---|---|---|---|---|---|
| **Advisory** | $20/session | Read-only analysis | Meeting duration | Public documents | Internal only |
| **Deliberative** | $50/session | Draft proposals | Decision deadline | Internal + precedent | Committee only |
| **Executive** | $100/session | Full drafting | Fiscal year | All organizational | All stakeholders |

**Capture rules**:
- Every policy recommendation linked to constitutional basis
- Stakeholder impact analysis required for material decisions
- Precedent citations tracked and verified
- Dissenting considerations recorded (not just consensus)

---

## Domain: COR (CO for Research)

**Purpose**: Academic research, data analysis, and publication with full audit trail.

**Agent teams**:

| Phase | Agents | Purpose |
|---|---|---|
| Literature | search-specialist, synthesis-advisor | Literature review and gap identification |
| Methodology | methodology-advisor, statistical-consultant | Research design and method selection |
| Analysis | data-analyst, visualization-specialist | Data processing and analysis |
| Writing | writing-assistant, citation-manager | Manuscript drafting |
| Review | peer-review-simulator, ethics-checker | Pre-submission review |

**Constraint templates**:

| Template | Financial | Operational | Temporal | Data Access | Communication |
|---|---|---|---|---|---|
| **Exploratory** | $20/session | Read + analyze | No limit | Public datasets | No external |
| **Formal** | $50/session | Read + analyze + draft | Grant period | Approved datasets | Collaborators |
| **Sensitive** | $100/session | Full operations | IRB approval period | All data (with classification) | Ethics board |

**Capture rules**:
- Data transformations produce audit anchors (reproducibility)
- Statistical method choices recorded as reasoning traces
- Literature search queries and selection criteria captured
- AI contribution to writing tracked at paragraph level

**Assessment criteria**:
- Methodological rigor (reasoning trace quality on method choices)
- Data handling transparency (audit chain completeness)
- Honest limitations (constraint declarations accurate and complete)
- Reproducibility (verification bundle sufficient to replicate)

---

## Domain: COComp (CO for Compliance)

**Purpose**: Regulatory compliance audits with constrained AI assistants.

**Agent teams**:

| Phase | Agents | Purpose |
|---|---|---|
| Scope | regulation-mapper, gap-identifier | Map applicable regulations |
| Evidence | evidence-collector, document-reviewer | Gather compliance evidence |
| Test | control-tester, exception-tracker | Test controls against requirements |
| Report | report-generator, finding-summarizer | Generate compliance report |

**Constraint templates**:

| Template | Financial | Operational | Temporal | Data Access | Communication |
|---|---|---|---|---|---|
| **Internal** | $30/session | Read + analyze | Audit period | Internal docs | Internal only |
| **External** | $100/session | Read + analyze + draft | Filing deadline | Client docs (NDA) | Audit committee |

---

## Domain: COF (CO for Finance)

**Purpose**: Financial analysis with spending controls and approval hierarchies.

**Agent teams**:

| Phase | Agents | Purpose |
|---|---|---|
| Gather | data-aggregator, source-validator | Collect financial data from approved sources |
| Analyze | financial-analyst, risk-assessor | Run analyses with methodology tracking |
| Model | model-builder, scenario-tester | Build financial models with assumption tracking |
| Report | report-generator, compliance-checker | Generate reports with regulatory compliance |

**Constraint templates**:

| Template | Financial | Operational | Temporal | Data Access | Communication |
|---|---|---|---|---|---|
| **Analysis** | $20/session | Read-only | Business hours | Market data | Internal only |
| **Advisory** | $50/session | Read + model | Client engagement | Client + market | Client team |
| **Trading** | $200/session | Full (with approval chain) | Trading hours | All financial data | Compliance-approved |

---

## Creating New Domains

Any organization can create a domain application by following the template structure. Praxis ships with COC, COE, and COG. Additional domains (COR, COComp, COF) are planned. Community-contributed domains are welcome.

To create a new domain:

1. Copy the template directory structure
2. Define constraint templates for your domain
3. Define agent team compositions for each workflow phase
4. Define capture rules (what deliberation evidence matters)
5. Define assessment criteria (how to evaluate collaboration quality)
6. Test with `praxis domain validate`
7. Submit as a pull request to the Praxis repository

The domain engine loads domain configurations at session start and enforces them throughout the session. No code changes required — domains are pure configuration.
