# Value Proposition Critique

**Date**: 2026-03-15
**Perspective**: Enterprise buyer (CISO/CTO) + Open-source community evaluator
**Method**: Full codebase audit, dependency analysis, standards review
**Praxis Version**: 0.1.0 (Planning status per PyPI classifier)

---

## 1. Value Proposition Critique: Skeptical Enterprise Buyer

### "Why should I deploy this instead of just using my AI tool's built-in features?"

**The honest answer**: Today, you should not. Praxis is a `__init__.py` file with a version string. There is no runtime, no CLI, no API, no session manager, no constraint enforcer. The entire `src/praxis/` directory contains exactly one file: 9 lines including the copyright header.

But the question deserves a deeper answer, because the *vision* is addressing a real problem that built-in features do not.

Built-in AI tool features (system prompts, custom instructions, memory) are:
- **Stateless across tools**: Your Claude Code conventions do not carry to Cursor. Your ChatGPT memory does not carry to VS Code Copilot.
- **Advisory, not enforced**: You can tell an AI "never delete production files." There is no mechanism to prevent it from doing so. The rule lives inside the context window, and context windows are probabilistic.
- **Unauditable**: There is no cryptographic proof that a human authorized a particular action. There is no tamper-evident log of what was decided and why. There are chat transcripts, which can be edited, cherry-picked, or fabricated.

The value proposition Praxis claims -- deterministic constraint enforcement that sits *between* the AI and its actions, producing cryptographic proof -- is genuinely distinct from what any AI tool provides natively. The question is whether this matters enough to justify the integration cost.

**Verdict**: The problem is real. The solution is theoretical. An enterprise buyer cannot evaluate a platform that does not exist yet.

### "What's the concrete ROI? What cost does this save or risk does it mitigate?"

There is no concrete ROI yet because there is no deployment to measure. But the claimed ROI story maps to three categories:

**Risk mitigation (strongest case)**:
- Regulatory compliance for AI usage (EU AI Act, NIST AI RMF, industry-specific regulations) -- organizations need to demonstrate human oversight of AI decisions. Praxis claims to produce auditable proof of this.
- Data governance violations -- an AI that accesses files it should not, sends data to external APIs, or exceeds spending limits can create liability. Constraint enforcement claims to prevent this.
- Academic integrity -- universities need to distinguish "student used AI as a tool under supervision" from "student had AI do the work." Deliberation capture claims to make this distinction cryptographically verifiable.

**Cost reduction (weaker case)**:
- Reduced time spent on manual audit trail construction -- if trust capture is automatic, humans spend less time documenting their AI interactions.
- Reduced rework from convention drift -- if institutional knowledge is enforced, AI produces work that conforms to organizational standards without repeated correction.

**Revenue enablement (speculative)**:
- Selling AI-augmented services with verifiable trust guarantees -- a consulting firm could demonstrate to clients that their AI usage was constrained and supervised.

**Verdict**: The risk mitigation case is strongest, particularly for regulated industries and education. But without a working product, the ROI is a projection, not a measurement.

### "How does this compare to IBM watsonx.governance or Credo AI?"

This comparison reveals Praxis's positioning challenge:

| Dimension | IBM watsonx.governance | Credo AI | Praxis (claimed) |
|---|---|---|---|
| **Focus** | Model lifecycle governance | AI risk management | Human-AI collaboration governance |
| **Scope** | ML/AI model monitoring, bias, drift | Policy compliance, risk assessment | Session-level constraint enforcement |
| **Deployment** | SaaS / on-prem (paid) | SaaS (paid) | Self-hosted open-source |
| **Trust model** | Proprietary monitoring | Proprietary assessment | Cryptographic trust chains (EATP) |
| **Open source** | No | No | Apache 2.0 |
| **Currently exists** | Yes (production) | Yes (production) | No (planning stage) |

Key differences:
- watsonx.governance and Credo AI govern *AI models* (fairness, bias, drift, compliance of the model itself). Praxis governs *human-AI collaboration sessions* (what was decided, who authorized it, what constraints applied).
- watsonx and Credo are enterprise SaaS products with sales teams, support, and SLAs. Praxis is an open-source project with no support infrastructure.
- Praxis's cryptographic approach (Ed25519 trust chains, hash-chained audit anchors) is technically differentiated -- neither watsonx nor Credo produce independently verifiable cryptographic proof of human authorization.

**Verdict**: Praxis is not competing with watsonx.governance or Credo AI. They solve adjacent but different problems. watsonx governs the model. Praxis claims to govern the human-AI interaction. This distinction is legitimate but will require significant market education.

### "Is the open-source angle a strength or a weakness?"

**Strengths**:
- Auditable trust layer -- if you are producing cryptographic proof of governance, the software that produces it should be auditable. Black-box trust is weaker trust.
- No vendor lock-in on governance infrastructure -- organizations concerned about AI governance should be concerned about depending on a single vendor for that governance.
- Data sovereignty -- everything runs on your infrastructure with no telemetry or phone-home.
- Foundation governance (Singapore CLG, not a VC-funded startup that might pivot or get acquired).

**Weaknesses**:
- No enterprise support, no SLA, no professional services.
- No track record of production deployments.
- Heavy dependency on Foundation-owned packages (Kailash SDK, EATP SDK, trust-plane) that are not widely adopted.
- The Foundation's sustainability model is unclear at best. Standards licensing under CC BY 4.0 generates no revenue by design.

**Verdict**: The open-source angle is a strength for the trust proposition specifically (verifiable trust should be built on verifiable software). But the ecosystem immaturity is a significant weakness for enterprise adoption.

### "The cryptographic proof sounds impressive -- but who is actually asking for this today?"

Three constituencies have emerging demand:

1. **Regulated industries (banking, healthcare, government)**: EU AI Act Article 14 requires "human oversight" of high-risk AI systems. "We have chat logs" is weak evidence. "We have Ed25519-signed, hash-chained audit anchors with verification gradient classification" is stronger evidence. But regulators have not yet specified what "adequate evidence of human oversight" means.

2. **Education**: Universities are struggling with AI academic integrity. The current approach (AI detection tools) is failing spectacularly -- false positives harm students, and detection is unreliable. A shift from "detect AI usage" to "verify supervised AI collaboration" is philosophically sound but requires institutional adoption of a new assessment paradigm (the "Mirror Thesis" described in the COE domain).

3. **Professional services (consulting, audit, legal)**: Firms using AI to augment client work need to demonstrate responsible usage. A Big 4 audit firm using AI to review financial statements needs proof that a human supervised the AI's work. Today they rely on process documentation. Cryptographic proof is stronger but currently unnecessary because regulators are not requiring it.

**Verdict**: Demand is emerging but not mature. Education is the most immediate use case because the pain (AI integrity crisis) is acute and the alternative (AI detection) is failing. Regulated industries will follow when regulations specify evidence requirements. Professional services will adopt when clients or regulators demand it.

---

## 2. Value Proposition Critique: Open-Source Community

### "Is this solving a real problem I have, or is it governance theater?"

**The honest assessment**: For most individual developers, this is governance theater. If you are writing code alone with Claude Code, you do not need cryptographic proof of human authorization. You authorized yourself. The constraint enforcement is interesting (budget limits, file access restrictions) but achievable with simpler tools (filesystem permissions, API spend alerts).

Where it becomes real:
- **Team settings**: When multiple developers use AI, and a manager needs to verify that AI usage followed organizational rules, there is a genuine gap. Git commit history does not tell you what the AI was allowed to do versus what it actually did.
- **Educational settings**: A student submitting AI-assisted work has a genuine need to prove their supervision. Today there is no good way to do this.
- **Compliance requirements**: If your organization mandates AI usage governance, you need a tool that provides it. Today the options are manual process documentation or expensive enterprise platforms.

**Verdict**: Real problem for teams and institutions. Governance theater for solo developers. The question is whether the open-source community skews toward solo developers (where adoption will be low) or team/institutional contexts (where adoption could be meaningful).

### "Can I use this without buying into the entire Foundation ecosystem?"

**Current dependency chain**:
```
praxis
  -> kailash (Core SDK, not published on PyPI as pure Python -- only enterprise Rust version exists)
  -> kailash-nexus (not published on PyPI)
  -> kailash-dataflow (not published on PyPI)
  -> kailash-kaizen (not published on PyPI)
  -> eatp (exists, installed from local source at 0.1.0)
  -> trust-plane (exists, installed at 0.2.0)
```

This is a serious adoption concern. As of today:
- `kailash` (pure Python) is not available via `pip install`. Only `kailash-enterprise` exists, and it is labeled "Proprietary" license.
- `kailash-nexus`, `kailash-dataflow`, `kailash-kaizen` are not published on PyPI.
- `eatp` and `trust-plane` exist and are installable, but only from local/source builds.

An outsider running `pip install praxis` today would fail because 4 of 6 Foundation dependencies do not exist as published packages.

**Verdict**: You cannot currently use Praxis at all, let alone without the Foundation ecosystem. The dependency on unpublished packages is a hard blocker for community adoption. Until `kailash` (pure Python, Apache 2.0) is published on PyPI, Praxis is effectively internal software regardless of its license.

### "Is the architecture genuinely open, or is it vendor-locked to Foundation packages?"

The architecture is deeply coupled to Foundation packages:
- **Kailash Core SDK**: All workflow orchestration. Not substitutable with standard Python libraries (FastAPI, Celery, etc.) without rewriting the core.
- **Kailash DataFlow**: All database operations. Not substitutable with SQLAlchemy or Django ORM without rewriting persistence.
- **Kailash Nexus**: All API exposure (REST + CLI + MCP). Not substitutable with FastAPI or Flask without rewriting the API layer.
- **Kailash Kaizen**: All AI agent operations. Not substitutable with LangChain, CrewAI, or similar without rewriting agent logic.
- **EATP SDK**: All trust operations. This one is defensible -- EATP is the trust protocol Praxis implements, so depending on the EATP SDK is appropriate.
- **trust-plane**: Trust environment management. Also defensible as the reference implementation.

The EATP/trust-plane dependency is architecturally justified -- you cannot implement EATP without the EATP SDK. But the Kailash dependency is a choice, not a requirement. Session management, database persistence, API routing, and agent orchestration are generic problems with well-established Python solutions. Using Foundation-specific frameworks for all of them creates a dependency structure that is practically vendor-locked, even if legally open.

**Counter-argument**: All frameworks create lock-in (Django, Rails, Spring). Kailash is no different. The question is whether Kailash's value (workflow orchestration, DataFlow zero-config, Nexus multi-channel) justifies the lock-in cost. For Foundation-internal projects, it clearly does. For community adoption of Praxis, it creates a barrier: contributors must learn Kailash before contributing.

**Verdict**: The trust layer (EATP, trust-plane) is genuinely open and the coupling is justified. The infrastructure layer (Kailash Core, DataFlow, Nexus, Kaizen) is technically open but practically creates Foundation ecosystem lock-in. This will limit external contributions.

### "What's my 5-minute experience? Can I actually get value quickly?"

**Current 5-minute experience**:
1. `git clone https://github.com/terrene-foundation/praxis.git` -- works
2. `pip install -e ".[dev]"` -- fails (kailash, kailash-nexus, kailash-dataflow, kailash-kaizen not on PyPI)
3. End of experience.

**Claimed 5-minute experience (from README)**:
1. `pip install praxis` -- not published on PyPI
2. `praxis init` -- CLI entry point exists in pyproject.toml but `praxis.cli:main` does not exist
3. `praxis session` -- does not exist

**Verdict**: The 5-minute experience is nonexistent. The README describes commands that do not work. The Quick Start section is aspirational documentation for software that has not been written.

### "Is the scope realistic for an open-source project?"

The product vision describes:
- 5 personas (CLI, IDE, Web, Supervisor, Auditor)
- 6+ domains (COC, COE, COG, COR, COComp, COF)
- 4 client channels (CLI, REST, MCP, WebSocket)
- 3 client applications (Web dashboard, Desktop app, Mobile companion)
- Full cryptographic trust infrastructure
- IDE extensions for multiple editors
- Self-contained verification bundles with embedded JavaScript
- Multi-language support (implied by "across any domain")

For context: Comparable open-source projects with similar scope aspirations:
- **MLflow** (ML lifecycle) -- started by Databricks (100+ engineers), 3+ years to mature, focused on ONE domain
- **Apache Airflow** (workflow orchestration) -- started by Airbnb (large engineering team), 4+ years to production readiness, focused on ONE problem
- **Grafana** (observability) -- started by a single developer, but focused on ONE problem (dashboards), not five personas across six domains

**Verdict**: The scope is unrealistic for a Foundation project unless the Foundation has a team of 20+ dedicated engineers. Attempting to ship CLI + Web + Desktop + Mobile + IDE extensions across 6 domains simultaneously will produce nothing complete rather than something useful. The most successful open-source projects start with ruthless scope reduction: one persona, one domain, one channel, done excellently.

---

## 3. Unique Selling Points: Honest Assessment

### USP 1: Cryptographic Proof of Human Authorization
**Rating: Aspirational**

The concept is genuinely unique. No existing tool produces Ed25519-signed, hash-chained proof that a human authorized specific AI actions. This is technically differentiated and, if regulation catches up, could become highly valuable.

But: the EATP SDK exists (113 Python files, 73K+ lines) and trust-plane exists (40+ files). The cryptographic infrastructure has substance behind it. This is not vaporware at the protocol level -- the protocol and SDK are real. The gap is in Praxis making it accessible.

Risk: "Cryptographic proof" is only as strong as the weakest link. If the human can approve actions without reading them (one-click rubber-stamp), the proof proves nothing. The verification gradient (AUTO_APPROVED/FLAGGED/HELD/BLOCKED) partially addresses this, but the human behavior problem remains.

### USP 2: Five-Dimensional Constraint Enforcement
**Rating: Aspirational**

The five constraint dimensions (Financial, Operational, Temporal, Data Access, Communication) are well-defined and genuinely useful. The concept of deterministic enforcement (not advisory) is architecturally sound.

But: No constraint enforcer exists in the codebase. The EATP SDK has constraint modules (`constraints/evaluator.py`, `constraints/dimension.py`, `constraints/builtin.py`) that provide building blocks, but the Praxis-level five-dimensional model is not implemented.

Comparative: Some of this exists in simpler forms. AWS IAM provides operational and data access constraints. Budget alerts provide financial constraints. These are not five-dimensional or session-aware, but they exist and work.

### USP 3: Deliberation Capture
**Rating: Real (concept) / Aspirational (implementation)**

Recording *what was decided, why, what alternatives were considered, and who approved it* is genuinely valuable and genuinely absent from current AI tools. Chat logs capture what was said, not what was decided. There is a meaningful difference.

The Mirror Thesis in education (assess the student's decisions, not the AI's output) is an intellectually compelling framework that no competitor has articulated.

Risk: Capture quality depends on human discipline. If practitioners do not record meaningful reasoning, the deliberation log becomes a box-checking exercise.

### USP 4: Verification Gradient (AUTO_APPROVED / FLAGGED / HELD / BLOCKED)
**Rating: Table Stakes (concept) / Aspirational (implementation)**

Graduated access control is not new. AWS IAM has Allow/Deny. GitHub has branch protection levels. Kubernetes has RBAC tiers. The four-level gradient is a reasonable design but not unique.

What would be unique: the gradient applied *to individual AI actions in real-time within a collaboration session*, informed by multi-dimensional constraints. That specific combination does not exist elsewhere. But it also does not exist in Praxis yet.

### USP 5: Domain-Agnostic Architecture
**Rating: Questionable**

The claim that the same runtime serves codegen, education, governance, research, compliance, and finance is architecturally plausible (domain as configuration layer) but practically unproven.

Risk: Domain-agnostic often means domain-shallow. A constraint system that is equally useful for a student writing an essay and a trader executing financial transactions would need to be so generic that it provides little domain-specific value, or so configurable that it requires significant domain expertise to set up.

The most successful platforms are domain-specific first and domain-agnostic later (if ever). Kubernetes started with container orchestration. Airflow started with data pipelines. Grafana started with time-series dashboards. None of them started with "any domain."

### USP 6: Self-Contained Verification Bundles
**Rating: Real**

A ZIP file containing JSON data + HTML viewer + JavaScript verifier that allows independent third-party verification without installing any software is genuinely unique and genuinely valuable. No competitor provides this.

The trust-plane package already has `bundle.py`, suggesting this capability has implementation behind it.

This is the kind of feature that makes an auditor's eyes light up: "I can verify the entire trust chain in my browser without installing your software?" That is a powerful demo moment.

### USP 7: Tool-Agnostic Integration (MCP + REST + CLI)
**Rating: Table Stakes**

Multi-channel API exposure is standard practice. MCP support is increasingly common. REST APIs are universal. CLI is expected. This is not a differentiator; it is a minimum requirement.

### USP 8: Trust as Medium, Not Camera
**Rating: Aspirational**

The architectural distinction between trust infrastructure that *watches* (camera) versus trust infrastructure that *mediates* (medium) is philosophically sound and technically meaningful. If Praxis actually routes all AI actions through the trust layer (not just logging them), it is architecturally differentiated.

But: this is an architecture claim that requires a working implementation to validate. The trust-plane experiment (March 2026) identified the camera problem. Praxis is the proposed solution. The solution does not exist yet.

---

## 4. Adoption Bottlenecks: Top 5

### Bottleneck 1: Dependencies Do Not Exist (CRITICAL)

`kailash`, `kailash-nexus`, `kailash-dataflow`, and `kailash-kaizen` are not published on PyPI as Apache 2.0 packages. `pip install praxis` would fail. This is not a minor issue -- it is an absolute blocker. No one can use Praxis until its dependencies are installable.

**Severity**: Showstopper
**Fix**: Publish Kailash Python packages on PyPI with Apache 2.0 licensing before Praxis 0.1.0.

### Bottleneck 2: No Working Software (CRITICAL)

The entire `src/praxis/` directory contains one file with 9 lines. There is no session manager, no constraint enforcer, no deliberation capture, no CLI, no API, no web dashboard, no domain engine. The project is in planning stage (confirmed by `Development Status :: 1 - Planning` in pyproject.toml).

**Severity**: Showstopper
**Fix**: Build the core runtime before anything else. Session management + constraint enforcement + deliberation capture as a working CLI.

### Bottleneck 3: Behavior Change Required (HIGH)

Adopting Praxis requires practitioners to change how they work with AI:
- Start sessions explicitly (instead of just opening a chat)
- Record decisions with reasoning (instead of just accepting AI output)
- Respond to held actions (instead of uninterrupted flow)
- Export verification bundles (new workflow step)

Each of these is friction. The value must exceed the friction for every individual interaction, not just in aggregate. If recording a decision takes 30 seconds and happens 10 times per session, that is 5 minutes of overhead per session. The value of that 5 minutes must be immediately apparent.

**Severity**: High
**Mitigation**: Automatic capture where possible (MCP integration captures tool calls automatically). Manual recording only for decisions that require human reasoning. Make the overhead invisible for routine actions (AUTO_APPROVED) and meaningful only for significant ones (HELD).

### Bottleneck 4: Learning Curve for the Conceptual Framework (MEDIUM)

CO has seven first principles, five layers, three failure modes, five constraint dimensions, four verification gradient levels, five personas, and six domain applications. This is a significant conceptual load.

Compare: Git has three concepts (working directory, staging area, repository). Docker has three concepts (image, container, registry). Kubernetes has four core concepts (pod, service, deployment, namespace). Praxis has approximately 20 core concepts before a user writes their first session.

**Severity**: Medium
**Mitigation**: Progressive disclosure. A user should need to understand exactly three concepts to start: session, constraint, decision. Everything else should be discoverable through use, not required upfront.

### Bottleneck 5: Trust in the Platform Itself (MEDIUM)

A governance platform must be trustworthy. Praxis is version 0.1.0, has no production deployments, no security audit, no formal specification compliance testing, and no organizational track record. Asking an enterprise to trust their AI governance to an unproven platform is a hard sell.

The Foundation governance structure (Singapore CLG, Apache 2.0, no commercial coupling) is good on paper but unproven in practice. There is no public board, no governance charter, no track record of community responsiveness.

**Severity**: Medium
**Fix**: First production deployment with published case study. Security audit by a recognized firm. EATP specification conformance test suite with published results.

---

## 5. Killer Use Case: The Gateway Drug

### Recommendation: COE (Education) for University Research Supervision

**Why this, and not codegen or enterprise governance?**

**Not codegen (COC)**: Developers already have workflows. Adding governance to `git commit` is friction with unclear value for individual developers. The pain is not acute enough -- developers are not being sued for unsupervised AI usage.

**Not enterprise governance (COG)**: Enterprise sales require proof of production readiness, support contracts, and SLAs. Praxis is years away from credibly selling to enterprise governance buyers.

**Education is the gateway because:**

1. **The pain is acute and growing**: Every university is struggling with AI academic integrity right now. AI detection tools are failing (false positives, unreliable detection). The current paradigm ("detect and punish AI usage") is collapsing. There is an urgent need for an alternative paradigm.

2. **The alternative paradigm is intellectually compelling**: The Mirror Thesis (assess the student's decisions, not the AI's output) is a genuine contribution to educational philosophy. It shifts from "Did you use AI?" to "How did you supervise your AI collaboration?" This is where the world is heading.

3. **The cryptographic proof has immediate value**: A student submitting a verification bundle that proves they made 12 conscious decisions, considered alternatives, and stayed within constraints is dramatically more credible than a student saying "I swear I wrote this myself."

4. **The buyer can deploy immediately**: A single professor can adopt Praxis for one course. No enterprise procurement. No IT approval. No budget committee. One person, one course, one semester. If it works, the department adopts it. If the department adopts it, the university mandates it.

5. **The scope is constrained**: One domain (COE), one persona (student as CLI/web practitioner), one supervisor (professor), one auditor (academic integrity board). This is a tractable scope for a small team.

6. **Success is measurable**: Did the professor find the deliberation logs useful for assessment? Did students demonstrate learning through their decision records? Did the verification bundle convince the integrity board? These are concrete, measurable outcomes.

7. **It creates upward pull**: A university that adopts Praxis for student AI supervision will want it for research collaboration (COR), then for institutional governance (COG). Education is the wedge that opens the institutional market.

### What the Minimum Viable COE Looks Like

```
praxis init --domain coe --template year2
praxis session start --assignment "Research Essay: Climate Policy"
# Student works with AI, Praxis captures deliberation
praxis session end
praxis export --format bundle --for-submission
```

Output: A verification bundle the professor opens in their browser. They see:
- Timeline of all AI interactions
- 8 conscious decisions with reasoning
- 3 alternatives considered and rejected
- Constraint compliance (stayed within Year 2 limits)
- Chain integrity verified (tamper-evident)

The professor assesses the *quality of the student's decisions*, not the quality of the essay.

### What This Requires

1. Working CLI with `init`, `session`, `decide`, `export` commands
2. EATP trust chain creation and management
3. Five-dimensional constraint enforcement (even basic)
4. Deliberation capture with hash chaining
5. Verification bundle generation (HTML + JS + JSON)
6. COE domain configuration (Year 1-4 templates)

This is achievable as a focused 3-month sprint with 2-3 engineers, if Foundation dependencies (Kailash) are available.

---

## Severity Table

| Issue | Severity | Impact | Fix Category |
|---|---|---|---|
| Foundation dependencies not published on PyPI | CRITICAL | No one can install Praxis | ECOSYSTEM |
| No working software (9 lines of code) | CRITICAL | Nothing to evaluate or adopt | IMPLEMENTATION |
| README describes non-existent functionality | HIGH | Destroys credibility on first contact | DOCUMENTATION |
| Scope covers 5 personas, 6 domains, 4 channels, 3 apps | HIGH | Guarantees nothing ships completely | STRATEGY |
| kailash (pure Python) has Proprietary Rust alternative | HIGH | Confusing open-source narrative | ECOSYSTEM |
| No production deployment or case study | MEDIUM | No proof the concept works | VALIDATION |
| 20+ core concepts before first session | MEDIUM | Steep learning curve | DESIGN |
| No community governance track record | MEDIUM | Trust deficit for governance platform | GOVERNANCE |
| Sustainability model unclear (CC BY 4.0 = no licensing revenue) | MEDIUM | Long-term viability concern | STRATEGY |
| Behavior change required for every AI interaction | MEDIUM | Adoption friction at individual level | DESIGN |

---

## What a Compelling First Release Would Look Like

A Praxis 0.1.0 that would earn a skeptical CTO's respect:

1. **One command to install**: `pip install praxis` works on any machine with Python 3.11+.
2. **Five commands to use**: `praxis init`, `praxis session start`, `praxis decide`, `praxis session end`, `praxis export`.
3. **One domain done well**: COE with Year 1-4 constraint templates, working deliberation capture, and verification bundle generation.
4. **One verification bundle that works**: Open in a browser, see the timeline, verify the chain, assess the decisions. No server required.
5. **One case study**: A professor used Praxis for one assignment in one course. Here is what they found. Here is what the students submitted. Here is what the verification looked like.
6. **Zero conceptual overhead to start**: Run `praxis init`, follow the prompts, start working. Learn about trust chains and constraint dimensions later.

What this does NOT include: web dashboard, desktop app, mobile app, IDE extension, 5 additional domains, WebSocket streaming, multi-user team features, enterprise deployment, Docker orchestration. All of those come later, after the core works and one use case proves the concept.

---

## Bottom Line

Praxis is an ambitious and intellectually rigorous vision for a problem that genuinely exists: there is no infrastructure for governed, auditable, trust-verified human-AI collaboration. The CO methodology is thoughtful, the EATP protocol has real engineering behind it (113 source files, 73K+ lines), and the trust-plane experiment informed sound architectural decisions.

But today Praxis is a vision document with a version number, not a software product. The `src/` directory has 9 lines of code. The dependencies are not installable. The README describes commands that do not exist. The scope (5 personas, 6 domains, 3 client applications) is unrealistic for a Foundation project without a large dedicated engineering team.

The single most impactful action is: *stop planning and start building*. Pick one persona (student), one domain (education), one channel (CLI), and ship something that works end-to-end by the end of Q2 2026. A working CLI that produces a verification bundle a professor can open in their browser would be worth more than all five product briefs combined.

If I were advising the Foundation's board, I would say: "The intellectual foundation is strong, the trust protocol is real, and the market timing for education is good. But you need to ship working software before the window closes. AI governance is a land grab right now, and you are writing planning documents while others are shipping products."
