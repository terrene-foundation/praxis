# CO Methodology Audit for Praxis

**Date**: 2026-03-15
**Status**: Complete
**Auditor**: COC Expert (CO methodology analysis)
**Sources**: CO specification (7 first principles, 5-layer architecture), Praxis briefs (01-05), trust-plane experiment (vision critique), CO domain applications (COC, COE, COG, COComp, COR/CORP)

---

## Executive Summary

Praxis is architecturally well-aligned with CO methodology. The product vision correctly identifies the six infrastructure problems (from the trust-plane experiment) and maps them to CO's five-layer architecture. The "trust as medium, not camera" insight is the defining architectural decision, and it is the correct one.

However, this audit identifies five structural gaps, three Bainbridge's Irony risks, and specific edge cases where the three failure modes could still penetrate the platform. Most gaps are addressable through design rather than fundamental rearchitecture.

---

## 1. CO Compliance Audit: Seven Principles

### Principle 1: Institutional Knowledge Thesis

**CO Requirement**: The primary determinant of AI output quality is not model capability but the institutional context surrounding the model. A CO implementation MUST provide mechanisms to encode organization-specific institutional knowledge in machine-readable form (L2-1 through L2-7).

**Praxis Assessment**: STRONG ALIGNMENT

Praxis addresses this principle through the Domain Engine (pluggable domain applications) and the Context layer (master directives, knowledge hierarchies). The domain application template (brief 03) correctly structures institutional knowledge encoding with:

- Agent team compositions (Layer 1 mapping)
- Constraint templates (Layer 3 mapping)
- Workflow definitions (Layer 4 mapping)
- Capture rules (Layer 5 mapping)
- Assessment criteria (Layer 5 mapping)

**Gaps Identified**:

1. **No explicit knowledge import/export protocol.** The brief describes domains as "pure configuration" (YAML files), but there is no specification for how institutional knowledge migrates between Praxis instances. If Organization A builds a compliance domain configuration with 200 institutional knowledge entries, how does Organization B adopt their base and customize? CO L2-6 requires "living documents, updated when conventions change" --- this implies knowledge must be portable, not just configurable.

2. **No distinction between institutional and generic knowledge.** CO Principle 1 requires that a CO implementation MUST distinguish institutional knowledge (organization-specific) from generic domain knowledge (available in training data). The Praxis domain template treats all knowledge as domain knowledge without this critical distinction. A compliance domain's knowledge about MAS reporting conventions is institutional. Knowledge about what MAS is, is generic. Praxis should model this distinction because it determines what the AI can be trusted to know versus what must be explicitly encoded.

3. **Progressive disclosure is implied but not enforced.** CO L2-3 SHOULD follow progressive disclosure. The domain template has a `knowledge/` directory with `institutional.yml` and `anti-amnesia.yml`, but there is no mechanism ensuring that Praxis loads knowledge progressively rather than dumping everything into context. The runtime must implement progressive disclosure as a loading strategy, not just a file organization convention.

**Recommendation**: Add a knowledge classification model (institutional vs generic), a knowledge portability protocol (export/import/customize), and enforce progressive disclosure at the runtime level.

---

### Principle 2: Brilliant New Hire

**CO Requirement**: AI onboarding is a first-class concern. The onboarding architecture MUST be persistent across sessions and practitioners --- not per-session, not per-individual.

**Praxis Assessment**: STRONG ALIGNMENT

This is where Praxis excels beyond any existing tool. Session persistence is the core value proposition. The Session Manager provides persistent identity across interactions, and the Domain Engine provides consistent onboarding configuration across all practitioners using the same domain.

The workspace model (brief 02) correctly separates individual session state from shared organizational context. A practitioner inherits the domain configuration (shared onboarding) and creates session-specific state (individual work).

**Gaps Identified**:

1. **No practitioner-level knowledge accumulation.** CO Principle 2 requires onboarding that is persistent across sessions AND practitioners. Praxis persists sessions and shares domain configurations, but there is no model for practitioner-specific accumulated knowledge. If Practitioner A works 50 sessions in the compliance domain and develops expertise in MAS reporting, that expertise does not transfer to Practitioner B. The Learning layer (L5) captures observations, but the pipeline from observation to practitioner-portable knowledge is not specified.

**Recommendation**: Design a knowledge inheritance model where new practitioners inherit not just the domain configuration but also the accumulated knowledge from the Learning layer --- formalized patterns, calibrated confidence thresholds, and curated observations.

---

### Principle 3: Three Failure Modes

**CO Requirement**: A CO implementation MUST address all three failure modes. Addressing fewer than three is not CO-conformant. Amnesia through anti-amnesia mechanisms (L3-3). Convention drift through institutional knowledge encoding (L2). Safety blindness through deterministic enforcement (L3).

**Praxis Assessment**: ALL THREE ADDRESSED (see detailed analysis in Section 2)

Praxis addresses all three failure modes at the infrastructure level, which is the correct approach. The constraint enforcer handles safety blindness (deterministic, not advisory). The domain engine handles convention drift (institutional knowledge replaces generic defaults). Session persistence and the trust chain handle amnesia (state survives across interactions).

The key insight from the trust-plane vision critique --- that trust must be the medium, not a camera --- directly addresses all three failure modes simultaneously. If the AI cannot act without flowing through the trust infrastructure, then:

- Amnesia is countered because the constraint envelope is re-evaluated at every action (not stored in the AI's context window)
- Convention drift is countered because domain conventions are enforced at the constraint layer (not suggested in a rule file)
- Safety blindness is countered because safety checks are in the execution path (not a parallel observation)

**Gaps**: See Section 2 for edge cases.

---

### Principle 4: Human-on-the-Loop

**CO Requirement**: Structured points for human judgment. Between approval gates, AI operates autonomously within the defined envelope. MUST NOT require human approval for every action (in-the-loop). MUST NOT allow AI to operate without boundaries (out-of-the-loop).

**Praxis Assessment**: STRONG ALIGNMENT

The verification gradient (AUTO_APPROVED / FLAGGED / HELD / BLOCKED) is a direct implementation of Human-on-the-Loop. It is the single most important design element in Praxis for CO conformance:

- AUTO_APPROVED = AI operates within the envelope, no human needed (on-the-loop)
- FLAGGED = Human is notified, AI proceeds (on-the-loop with visibility)
- HELD = Human must approve before execution (targeted in-the-loop)
- BLOCKED = Forbidden, no path forward (envelope boundary)

This is exactly what CO specifies: the human defines the envelope (constraint configuration), the AI operates within it, and the human intervenes only at defined points (held actions, approval gates).

**Gaps Identified**:

1. **Constraint calibration feedback loop is missing.** The verification gradient classifies actions, but there is no mechanism for the human to say "this was AUTO_APPROVED but should have been HELD." Without this feedback, the constraint envelope does not improve over time. CO L5 requires observation mechanisms that capture what works and what doesn't --- the gradient classification accuracy is a prime observation target.

2. **Trust posture progression is mentioned but not specified.** EATP defines trust postures (Pseudo-Agent, Supervised, Shared Planning, Continuous Insight, Delegated) that calibrate the verification gradient's sensitivity. The Praxis briefs mention the verification gradient but do not specify how trust postures evolve during a session or across sessions. A new practitioner should start at Supervised (most actions HELD). An experienced practitioner with a proven track record could operate at Shared Planning (most actions AUTO_APPROVED). This progression operationalizes the "on-the-loop" position for different maturity levels.

**Recommendation**: Add gradient accuracy tracking to the Learning layer. Specify trust posture progression logic.

---

### Principle 5: Deterministic Enforcement

**CO Requirement**: Critical rules MUST be enforced by deterministic mechanisms operating outside the AI model's context window. Hard enforcement blocks violations before they take effect. Anti-amnesia re-injects at every interaction. Defense in depth for highest-risk rules.

**Praxis Assessment**: STRONG ALIGNMENT --- THIS IS THE CORE ARCHITECTURE

Praxis's constraint enforcer is the architectural embodiment of Principle 5. The five-dimensional constraint model (Financial, Operational, Temporal, Data Access, Communication) provides the enforcement categories. The verification gradient provides the enforcement mechanism. The trust plane provides the cryptographic proof.

The critical design decision --- that the constraint enforcer sits IN the execution path, not alongside it --- is correct per the vision critique. When a tool call flows through Praxis, the constraint enforcer evaluates it BEFORE forwarding to the underlying tool. This is Tier 3 enforcement (transport-level) from the CO specification, which is the strongest possible enforcement architecture.

**Gaps Identified**:

1. **No anti-amnesia mechanism specified.** This is surprising given how central anti-amnesia is to CO. The trust-plane experiment identified anti-amnesia as the "single most important mechanism" in COC. Praxis's architecture makes anti-amnesia less critical than in COC (because constraints are enforced at the infrastructure level, not in the AI's context), but it is still needed for domain conventions that cannot be expressed as constraints. For example, a compliance domain convention like "always check precedent database before issuing new interpretations" is procedural knowledge, not a constraint. It needs anti-amnesia injection to survive context window compression.

2. **Defense in depth is not modeled.** CO recommends 5+ independent enforcement mechanisms for highest-risk rules. Praxis has constraint enforcement (one mechanism). Where are the other four? Defense in depth requires: (a) constraint enforcement in the execution path, (b) anti-amnesia injection into AI context, (c) session-start verification, (d) domain-specific rule files, (e) audit trail review. Praxis currently specifies only (a).

**Recommendation**: Design an anti-amnesia mechanism for Praxis sessions (not as critical as in COC, but still needed for procedural conventions). Model defense in depth explicitly: which enforcement mechanisms protect which rules, and how many independent layers exist for each.

---

### Principle 6: Bainbridge's Irony

**CO Requirement**: Layer construction SHOULD deepen practitioner expertise, not degrade it. Include mechanisms to detect whether practitioners are becoming more or less capable.

**Praxis Assessment**: PARTIAL ALIGNMENT --- DEEPEST RISK (see Section 3)

Praxis's deliberation capture is the primary mechanism for addressing Bainbridge's Irony. By recording reasoning traces, confidence scores, and alternative considerations, the system forces articulation of reasoning. This is the correct approach: making tacit knowledge explicit deepens understanding.

However, the product vision (brief 01) does not explicitly address Bainbridge's Irony as a design concern. It appears implicitly in the deliberation capture design but is not called out as a risk to be managed. This is a gap because Praxis automates trust infrastructure --- the very thing that, if automated carelessly, creates the irony where humans lose the ability to exercise the oversight the system depends on.

**Gaps**: See Section 3 for full analysis.

---

### Principle 7: Knowledge Compounds

**CO Requirement**: Observations from AI-assisted work compound across sessions, practitioners, and time periods. Captured observations MUST be reviewed by a human before becoming formalized institutional knowledge. MUST NOT auto-promote patterns.

**Praxis Assessment**: PARTIAL ALIGNMENT

The deliberation capture engine records decision reasoning, and the domain engine provides the framework for knowledge accumulation. However, the Praxis briefs do not specify a full Observe-Capture-Evolve pipeline (the core of CO Layer 5).

**Gaps Identified**:

1. **No observation mechanism specified.** What does Praxis observe during sessions? COG observes 7 targets (workflow sequences, agent combinations, rule violations, decision patterns, cross-reference failures, publication rejections, terminology drift). COC observes tool usage, workflow patterns, errors, and fixes. Praxis's briefs do not specify observation targets.

2. **No pattern analysis pipeline.** CO L5 requires analyzing observations for recurring patterns with confidence scores. The Praxis briefs describe deliberation capture but not the downstream pipeline that identifies patterns in captured deliberation.

3. **No evolution proposal mechanism.** CO L5 requires proposing formalization of successful patterns. Praxis does not specify how observed patterns become proposed domain configuration changes, or how those proposals are presented to humans for approval.

4. **No human approval gate for knowledge formalization.** CO L5-2 and L5-3 are MUST/MUST NOT requirements: human approval is mandatory, auto-promotion is forbidden. The Praxis briefs do not explicitly enforce this constraint.

**Recommendation**: Design the full L5 pipeline: observation targets per domain, pattern analysis with confidence scoring, evolution proposals with human approval gates. This is not optional for CO conformance.

---

## 2. Three Failure Modes: Detailed Analysis

### 2.1 Amnesia

**How Praxis Counters Amnesia**:

| Mechanism | How It Works | CO Alignment |
|---|---|---|
| Session persistence | Session state survives across interactions; context is not lost when the session pauses and resumes | Addresses the core amnesia problem (stateless sessions) |
| Constraint enforcement in execution path | Constraints are evaluated at action time, independent of the AI's context window | CO L3-2: enforcement outside context window |
| Deliberation capture | Decisions are recorded and retrievable, so prior reasoning is not lost | CO L5: knowledge capture |
| Trust chain | Cryptographic records of prior actions cannot be forgotten or rewritten | CO L3-7: deterministic enforcement |
| Domain configuration | Institutional knowledge is loaded from configuration, not from the AI's memory | CO L2-1: master directive every session |

**Edge Cases Where Amnesia Could Still Penetrate**:

1. **Intra-session amnesia for non-constraint knowledge.** Praxis enforces constraints at the infrastructure level, but domain conventions that are advisory (not enforceable as constraints) still depend on the AI's context window. A compliance domain convention like "prefer conservative interpretations for new regulations" is judgment-level guidance, not a constrainable action. If the session runs long enough, this guidance will be evicted from the AI's context. Praxis needs an anti-amnesia mechanism for domain conventions --- not as critical as in raw AI tools (because the constraint layer catches the most dangerous violations), but still needed for quality.

2. **Cross-session amnesia for deliberation context.** Praxis records deliberations, but does the AI automatically retrieve relevant prior deliberations when a new session starts? If Practitioner A decided in Session 12 that "we interpret regulatory X conservatively," does Session 13's AI know this without being explicitly told? The session manager persists state, but the AI's context window is still finite. Loading 50 sessions of deliberation history into context is not feasible. Praxis needs a retrieval mechanism that surfaces relevant prior deliberations without overwhelming context.

3. **Multi-practitioner amnesia.** When Practitioner B takes over from Practitioner A, what transfers? Session state and domain configuration transfer, but the tacit knowledge that Practitioner A developed --- the intuitions about which constraint configurations work, which approval workflows are too strict, which domain conventions matter most --- does not transfer unless it has been formalized through the L5 pipeline.

### 2.2 Convention Drift

**How Praxis Counters Convention Drift**:

| Mechanism | How It Works | CO Alignment |
|---|---|---|
| Domain engine | Domain-specific conventions loaded as configuration, replacing generic defaults | CO L2: institutional knowledge |
| Constraint templates | Domain-appropriate defaults (strict/moderate/permissive) provide convention baselines | CO L3: guardrails |
| Agent team compositions | Specialized agents carry domain-specific knowledge | CO L1: intent |
| Workflow phases | Domain-specific workflows enforce procedural conventions | CO L4: instructions |

**Edge Cases Where Convention Drift Could Still Penetrate**:

1. **Convention drift within unconstrained action spaces.** Praxis enforces conventions that map to constraints (financial limits, operational boundaries, data access controls). But many organizational conventions are stylistic, procedural, or judgmental --- they cannot be expressed as constraint dimensions. How a compliance officer phrases client communications, how a researcher structures arguments, how a developer names variables. These conventions drift toward generic patterns when the AI's context fills up and the convention guidance is evicted. The constraint enforcer cannot catch this because it is not a constraint violation --- it is a quality degradation.

2. **Domain configuration staleness.** The domain configuration encodes current conventions, but conventions evolve. If the configuration is not updated when conventions change, the system enforces outdated conventions. This is worse than no enforcement --- it actively prevents the organization from evolving. CO L2-6 requires living documents. Praxis needs a mechanism to detect when domain configurations may be stale (e.g., if observation patterns show practitioners consistently overriding a convention, the configuration may need updating).

3. **Drift between Praxis-mediated and non-Praxis work.** Practitioners may use AI outside Praxis (direct Claude conversations, Cursor without Praxis integration). Conventions enforced within Praxis sessions drift freely in non-Praxis work. Praxis cannot control this, but it should be aware of it --- the verification bundle should make clear which work was Praxis-mediated and which was not.

### 2.3 Safety Blindness

**How Praxis Counters Safety Blindness**:

| Mechanism | How It Works | CO Alignment |
|---|---|---|
| Verification gradient | HELD/BLOCKED actions cannot proceed without human approval | CO L4-2: approval gates |
| Five-dimensional constraints | Financial, operational, temporal, data access, communication boundaries | EATP constraint dimensions |
| Trust chain | Every action produces an audit anchor; bypassing the trust layer is architecturally impossible | CO L3-7: blocks before effect |
| Delegation chains | Authority flows downward; child never gets more than parent | EATP delegation |
| Verification bundles | Independent third-party verification of the entire trust chain | EATP verification |

**Edge Cases Where Safety Blindness Could Still Penetrate**:

1. **Constraint completeness.** The five EATP dimensions are comprehensive but not exhaustive. What about ethical constraints? Reputational constraints? Environmental constraints? A compliance AI that stays within all five dimensions but produces advice that is technically legal yet reputationally catastrophic has violated an implicit safety boundary that no constraint dimension covers. Praxis could address this by allowing domain-specific constraint dimensions beyond the EATP five, or by defining a "domain safety" dimension that captures domain-specific safety concerns not covered by the standard five.

2. **Constraint specification errors.** The constraint enforcer is deterministic: it enforces exactly what is specified. If the constraint is specified incorrectly (too permissive, wrong threshold, missing edge case), the enforcer will faithfully enforce the wrong boundary. A financial constraint of "$200/session" that should have been "$20/session" will not be caught by Praxis --- it will be enforced as specified. The Learning layer should observe constraint utilization and flag configurations that appear miscalibrated (e.g., a financial constraint that is never approached suggests it may be too permissive).

3. **Emergent safety failures across constraint dimensions.** An action may be safe in each individual constraint dimension but unsafe in combination. A data access operation that is within bounds AND a communication operation that is within bounds could combine to create a data exfiltration path. Cross-dimensional constraint analysis is not specified in the Praxis briefs.

---

## 3. Bainbridge's Irony Assessment

This is the deepest risk Praxis faces. The analysis follows.

### The Irony Stated

As Praxis automates trust infrastructure, it creates the conditions where:

1. Humans approve actions without understanding them (because the system handles trust evaluation)
2. Humans defer to constraint configurations without understanding why those constraints exist (because the system enforces them)
3. Humans stop developing the judgment needed to set constraints (because the system works well enough without refinement)

This is precisely Bainbridge's prediction: the more automated the system, the more critical human oversight becomes, but the harder it is for humans to maintain the capability for that oversight.

### Three Specific Risks

#### Risk 1: Approval Fatigue on Held Actions

The verification gradient produces HELD actions that require human approval. In a busy session, the practitioner may see dozens of held actions. Each requires reading context, understanding the constraint evaluation, and making a judgment. The temptation is to approve-all, especially when the first ten held actions were all legitimate.

**How this manifests**: The held action mechanism works perfectly in testing and early use. After six months, the practitioner's approval rate is 99.7%, with an average review time of 1.3 seconds per held action. The system has not failed --- the human has stopped providing meaningful oversight. The approval is a rubber stamp.

**CO's answer**: CO Principle 6 requires "mechanisms to detect whether practitioners are becoming more or less capable of independent judgment over time." Praxis should track held action metrics: approval rate, review time, approval-after-context-expansion rate. If approval rate exceeds a threshold with sub-threshold review time, Praxis should surface a warning. Not to the AI --- to the human. "Your held action approval rate is 99.7% with an average review time of 1.3 seconds. Are your constraints correctly calibrated, or are you experiencing approval fatigue?"

#### Risk 2: Constraint Configuration Ossification

Domain configurations are set once and enforced continuously. Over time, the constraints become "the way things are" rather than "the boundaries we chose." New practitioners inherit configurations they did not design and therefore do not understand. They know what the constraints ARE but not WHY they exist.

**How this manifests**: Organization A sets up a compliance domain with specific data access constraints. The original compliance officer who designed them leaves. The new compliance officer inherits a working system. Six months later, a regulatory change makes one constraint obsolete. The new officer does not know which constraint to update because they never understood the design rationale.

**CO's answer**: CO L2 requires institutional knowledge encoding. The constraint rationale is institutional knowledge. Every constraint should carry a rationale field: why it exists, what risk it mitigates, when it was last reviewed. Praxis should surface "constraint review due" reminders --- not just "this constraint exists" but "this constraint was last reviewed 180 days ago and has never been triggered. Does it still serve its purpose?"

#### Risk 3: Deliberation Capture as Performative Compliance

The deliberation capture engine records reasoning traces, confidence scores, and alternatives. This is valuable only if the human genuinely deliberates. If the human learns that the system records deliberation, they may provide performative reasoning --- plausible-sounding rationale that satisfies the system without reflecting genuine thought.

**How this manifests**: The student (COE), the researcher (CORP), or the compliance officer (COComp) learns to produce well-structured rationale quickly. The deliberation log looks excellent. The reasoning was never genuine --- it was constructed to satisfy the capture requirement.

**CO's answer**: The trust-plane vision critique addresses this directly. "Going through the motions that produces a continuous, temporally-consistent hash chain with structured deliberation evidence is much harder to fake than 'type anything in the rationale field.'" Praxis's temporal integrity (hash chains with monotonic timestamps) provides indirect evidence of engagement --- reading time versus content length, editing patterns, pushback against AI suggestions. This is not proof of genuine deliberation, but it raises the bar significantly above self-reported testimony.

### Design Principles to Counter Bainbridge's Irony

1. **Instrument the human, not just the AI.** Track approval patterns, review times, constraint review frequency, deliberation depth over time. Surface this data to the human as self-assessment, not surveillance.

2. **Require periodic constraint review.** Every constraint should have a review date. When constraints go unreviewed, surface them for human re-evaluation. This forces the human to re-engage with the rationale.

3. **Make constraint rationale mandatory.** A constraint without a rationale is a constraint that will ossify. The rationale is the institutional knowledge that prevents ossification.

4. **Design for discovery, not just compliance.** The deliberation capture should help humans discover their own reasoning patterns, not just record them. "Over the last 10 sessions, you consistently overrode the AI's conservative interpretation. This may indicate your constraint configuration is too restrictive --- or it may indicate the AI is correctly flagging risks you are choosing to accept."

5. **Measure practitioner capability independently.** CO Principle 6 SHOULD include mechanisms to detect capability changes. Praxis could periodically present the human with a scenario (removed from the constraint envelope) and ask them to make a judgment. Their judgment quality, compared to previous assessments, indicates whether their capability is growing or degrading.

---

## 4. Institutional Knowledge Strategy

### What Knowledge Praxis Must Capture

Praxis operates at two levels: it is a platform (with its own institutional knowledge) and it hosts domains (each with their own institutional knowledge). Both levels need knowledge capture.

#### Platform-Level Institutional Knowledge

| Knowledge | Why It Matters | How to Capture |
|---|---|---|
| Constraint calibration patterns | Which constraint configurations work well for which domains and team sizes | Observe constraint utilization rates across deployments |
| Trust posture progression models | How quickly practitioners can move from Supervised to Shared Planning | Observe held action approval accuracy over time |
| Domain configuration templates | What works as a starting point for new domain configurations | Analyze successful domain deployments |
| Anti-pattern catalog | Constraint configurations that look correct but fail in practice | Capture post-incident reviews |
| Verification gradient calibration | Optimal thresholds for AUTO_APPROVED vs FLAGGED vs HELD vs BLOCKED | Observe false positive/negative rates |

#### Domain-Level Institutional Knowledge

| Knowledge | Why It Matters | How to Capture |
|---|---|---|
| Convention exceptions | Where organizational practice legitimately diverges from domain defaults | Observe human overrides of domain conventions |
| Safety boundary evolution | How constraint boundaries should tighten or relax over time | Observe constraint boundary pressure (actions clustering near limits) |
| Approval workflow efficiency | Which held actions are consistently approved (suggesting over-constraint) | Observe approval rates by action type |
| Knowledge gap detection | Which institutional knowledge is missing (actions fail due to missing context) | Observe AI failures attributable to missing context |
| Cross-domain patterns | Patterns that apply across multiple domains (e.g., all domains need anti-amnesia for procedural conventions) | Cross-domain observation analysis |

### How Knowledge Should Compound

The Observe-Capture-Evolve pipeline for Praxis:

**Observe**: Every session produces structured data --- constraint evaluations, verification gradient classifications, held action resolutions, deliberation records, session metrics. This data is the observation layer.

**Capture**: Periodic analysis (automated with human review) identifies patterns:
- Constraints that are never triggered (may be unnecessary or misconfigured)
- Constraints that are triggered frequently (may be too restrictive)
- Actions that cluster near constraint boundaries (boundary may need recalibration)
- Held actions that are always approved (constraint may be too conservative)
- Held actions that are always denied (constraint may need to be promoted to BLOCKED)

**Evolve**: Pattern analysis produces proposals:
- "Constraint X has never been triggered in 500 sessions. Consider removing or recalibrating."
- "Action type Y is held 95% of the time and approved 98% of the time. Consider moving to FLAGGED."
- "Domain Z consistently overrides convention W. Consider updating the domain configuration."

All proposals require human approval. The human disposes. This is the Critical Constraint from CO L5.

### Knowledge Portability

A critical design question: how does institutional knowledge flow between Praxis instances?

1. **Domain configurations** are YAML files --- portable by definition.
2. **Learned patterns** (from the L5 pipeline) should be exportable as proposed domain configuration updates.
3. **Deliberation archives** should be exportable for independent analysis.
4. **Constraint calibration data** (utilization rates, boundary pressure, approval rates) should be exportable for benchmarking.

This enables a knowledge economy: organizations share domain configurations (general compliance domain), customize them (our firm's compliance domain), and contribute improvements back (our calibration data shows constraint X should be tighter).

---

## 5. Domain Application Validation

### Validation Framework

For each domain application, I assess against the CO Application Template (04-application-template.md) validation checklist:

- Layer 1: At least 2 agent specializations, routing rules
- Layer 2: Master directive, progressive disclosure, single source of truth
- Layer 3: Rule classification, hard enforcement, anti-amnesia, defense in depth
- Layer 4: Structured workflow with approval gates, evidence requirements
- Layer 5: Observation mechanism, human approval for formalization

### COC (CO for Codegen)

**Status**: Reference implementation (most mature)

**Strengths**:
- 29+ agent specializations across 7 phases (far exceeds L1 minimum)
- 28 skill directories with 100+ files (comprehensive knowledge hierarchy)
- 9 rule files + 9 hooks (full enforcement architecture)
- Anti-amnesia hook fires every user interaction
- Defense in depth with 5-8 layers for critical rules
- 7-phase workflow with 4 quality gates
- JSONL observation logging with confidence scoring

**As a Praxis domain**: COC maps cleanly to the Praxis domain template. Agent teams, constraint templates, workflow phases, capture rules, and assessment criteria are all well-defined. The constraint templates (strict/moderate/permissive) provide a good model for other domains.

**Gap**: COC's existing implementation runs inside Claude Code's hook system. Migrating to Praxis means the enforcement moves from Claude Code hooks (Tier 2, process-level) to Praxis's constraint enforcer (Tier 3, transport-level). This is an upgrade in enforcement strength. The migration path should be documented.

### COE (CO for Education)

**Status**: In analysis, pilot planned

**Strengths**:
- 7 agents (2 student-facing, 5 assessment) with clear routing
- The COE Spectrum (4 levels of student freedom) is a pedagogically sophisticated mapping of CO layers to educational progression
- Dual workflow (student + instructor) correctly models the two-sided nature of education
- EATP constraint mapping identifies which dimensions apply and which do not (Financial is N/A)
- Anti-amnesia fires every interaction

**As a Praxis domain**: COE is the strongest validation of Praxis's domain-agnostic architecture. If Praxis can serve COE (education) as well as COC (codegen), domain-agnosticism is proven. The key test: can Praxis's constraint enforcer handle COE's unique requirements?

- Model constraint (all students use the same model): maps to Operational constraint
- Scope boundary (stay within assignment): maps to Operational constraint
- Hash chain integrity (unbroken audit chain): maps to the trust plane, not a constraint dimension
- Temporal constraints (assignment period, submission deadline): maps to Temporal constraint

**Gap**: COE requires server-side genesis records and server-side timestamps to prevent gaming. This requires Praxis to operate as a server, not just a local process. The Praxis architecture supports this (it runs as a service), but the COE-specific requirement for anti-gaming server-side validation should be explicitly modeled.

**Missing CO Element**: Defense in depth is marked "pending implementation" in the COE validation checklist. This is a risk because COE faces adversarial users (students who may try to game the system), making defense in depth more critical than in other domains.

### COG (CO for Governance)

**Status**: In production (self-hosting)

**Strengths**:
- 22+ agents across 7 categories (the most agent-dense domain)
- Full validation checklist passed (the only domain to do so)
- 13 rule files with graduated enforcement (Critical/Hard, Critical/Soft+, Advisory/Soft)
- Defense in depth with 7 layers for Terrene naming (highest-risk rule)
- Living implementation --- this repository IS the COG implementation

**As a Praxis domain**: COG presents a unique challenge: it is self-hosting. The Terrene Foundation uses COG to govern its own standards development, including the development of Praxis. When COG migrates to Praxis, Praxis will be governing its own development. This creates a recursive trust challenge: who verifies the verifier?

**CO insight**: COG is the strongest proof that CO works. A methodology that can govern its own development has a self-consistency property that externally-governed methodologies lack. Praxis should preserve this self-hosting capability when COG migrates.

### COComp (CO for Compliance)

**Status**: Proposed (sketch only)

**Strengths**:
- Clean structural mapping to all five layers
- Honest about limitations ("does not prove practical effectiveness")
- EATP constraint dimensions map naturally to compliance concerns
- The amnesia/convention-drift/safety-blindness analysis is detailed and domain-specific

**As a Praxis domain**: COComp is the domain that most directly benefits from Praxis's infrastructure. Compliance work requires cryptographic audit trails, deterministic constraint enforcement, and independent verification --- exactly what Praxis provides. The regulatory filing workflow maps naturally to Praxis's session + workflow + constraint architecture.

**Missing CO Elements**:
- No actual agent definitions (only described, not specified)
- No anti-amnesia content specified (only described in principle)
- Defense in depth described as a pattern but no specific implementation proposed
- Knowledge hierarchy described but not implemented

**Risk**: COComp is the domain where incorrect enforcement has the highest external consequences (regulatory penalties, legal liability). Constraint specification errors are especially dangerous here. Praxis should provide COComp-specific validation tools: "does this constraint configuration actually prevent the regulatory violations it claims to prevent?"

### COR/CORP (CO for Research)

**Status**: Production (deployed for CARE thesis)

**Strengths**:
- 6 agents with clear specializations (literature, field expertise, claims verification, argument critique, writing, cross-reference)
- Teaching obligation is a novel CO innovation: agents must teach as they work
- Honest limitations section is unusually thorough
- Clear EATP integration strategy (optional, not required)

**As a Praxis domain**: CORP demonstrates that CO layers adapt to domains where the human needs to LEARN, not just supervise. The teaching obligation changes the agent interaction model from "execute and report" to "teach and co-create." Praxis's agent framework (Kaizen) must support this distinction.

**Missing CO Elements**:
- Knowledge base management capabilities are implied but not specified
- The "deliberation record is authored by the AI" limitation (acknowledged in honest limitations) is a structural challenge that Praxis should address. If deliberation records are AI-authored summaries of human decisions, they are evidence of what the AI interpreted, not what the human decided. Praxis could address this by allowing direct human annotation of deliberation records.

### COF (CO for Finance)

**Status**: Described in Praxis brief 03, no standalone CO application document

**Assessment**: COF is the least developed domain application. Brief 03 provides constraint templates and agent teams but no analysis of the three failure modes, no anti-amnesia design, no defense in depth, and no learning pipeline. This is below the threshold for CO conformance.

**Recommendation**: Before implementing COF as a Praxis domain, complete the CO Application Template analysis. Financial domains have the highest-consequence constraint failures (unauthorized transactions, regulatory violations with financial penalties). Rigorous CO analysis is a prerequisite.

### Domain Applications Not in Praxis Brief 03

The CO specification documents four applications (COC, COE, COG, COComp). CORP exists as a published application. Praxis brief 03 lists six domains (COC, COE, COG, COR, COComp, COF). The mapping:

| CO Spec | Praxis Brief | Status |
|---|---|---|
| COC | COC | Aligned |
| COE | COE | Aligned |
| COG | COG | Aligned |
| COComp | COComp | Aligned |
| CORP | COR | Name difference (COR vs CORP). Praxis brief uses "COR"; the published application uses "CORP". Recommend standardizing. |
| --- | COF | No CO application document exists. Needs analysis before implementation. |

---

## 6. Summary of Findings

### CO Conformance Status

| CO Layer | Praxis Status | Key Gaps |
|---|---|---|
| Layer 1: Intent | Conformant | Domain engine supports agent specialization and routing |
| Layer 2: Context | Partially conformant | Missing: institutional vs generic knowledge distinction, progressive disclosure enforcement, knowledge portability protocol |
| Layer 3: Guardrails | Conformant (strong) | Missing: anti-amnesia mechanism for non-constraint conventions, defense-in-depth modeling |
| Layer 4: Instructions | Conformant | Workflow phases with approval gates supported per domain |
| Layer 5: Learning | Not yet conformant | Missing: observation targets, pattern analysis pipeline, evolution proposals, human approval gate for formalization |

### Priority Recommendations

1. **Design the L5 pipeline (MUST for CO conformance).** Without observation, capture, and evolution mechanisms, Praxis is not CO-conformant. This is the most critical gap.

2. **Add anti-amnesia for procedural conventions.** Praxis's constraint enforcement handles safety and boundary enforcement, but procedural conventions that cannot be expressed as constraints need anti-amnesia injection.

3. **Address Bainbridge's Irony explicitly.** Add approval fatigue detection, mandatory constraint rationale, periodic constraint review, and practitioner capability tracking.

4. **Implement constraint calibration feedback.** The Learning layer should observe constraint utilization, boundary pressure, and gradient accuracy to improve constraint configurations over time.

5. **Complete COF analysis.** Do not implement a financial domain without rigorous CO Application Template analysis.

6. **Standardize COR/CORP naming.** Minor but important for consistency.

7. **Design knowledge portability.** Enable domain configurations, learned patterns, and calibration data to flow between Praxis instances.

### What Praxis Gets Right

The architectural decision that trust is the medium, not a camera, is the single most important insight. It simultaneously addresses all three failure modes, implements Tier 3 enforcement, and creates the conditions where institutional knowledge compounds. This insight, drawn from the trust-plane vision critique and embodied in Praxis's constraint-enforcer-in-the-execution-path architecture, is what makes Praxis a genuine CO implementation rather than a trust-logging tool bolted onto the side of existing AI tools.

The verification gradient (AUTO_APPROVED / FLAGGED / HELD / BLOCKED) is the operational expression of Human-on-the-Loop. It is the correct calibration mechanism for balancing AI autonomy with human oversight.

The domain-agnostic architecture, validated by six distinct domain applications with structurally different requirements, demonstrates that CO generalizes beyond codegen. This is the strongest possible evidence for CO's domain-portability principle.

---

_This audit assesses Praxis against the CO specification (CC BY 4.0, Terrene Foundation). It identifies gaps that should be addressed during implementation. It does not assess implementation quality, test coverage, or operational readiness --- those are separate concerns._
