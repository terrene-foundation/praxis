# Persona Requirements

## Five Personas, Five Interaction Modes

Praxis serves five distinct personas. Each requires different tooling, different interaction patterns, and different trust capabilities. A complete platform serves all five — not just the developer.

---

## Persona 1: CLI Practitioner

**Who**: Developer, researcher, data scientist, or analyst who works in a terminal with AI assistants like Claude Code, Aider, or custom scripts.

**How they work**: Terminal-native. Comfortable with git, CLI tools, and Markdown. Their AI assistant is a conversation partner in the terminal.

**What they need from Praxis**:

| Capability | Implementation |
|---|---|
| Initialize trust workspace | `praxis init` in project directory |
| Start/end sessions | `praxis session start` / `praxis session end` |
| Record decisions | `praxis decide --type scope --decision "..." --rationale "..."` |
| Check constraint status | `praxis status` |
| Export verification | `praxis export --format bundle` |
| MCP integration | AI assistant connects to Praxis as MCP server |

**MCP integration is critical**: The AI assistant connects to Praxis via MCP, and every tool call flows through the trust layer. This means:

- Before each tool call, Praxis checks constraints and applies the verification gradient
- After each tool call, Praxis records an audit anchor
- Held actions pause the AI until the practitioner approves
- The practitioner doesn't need to manually log anything — trust capture is automatic

**What they see**:

```
$ praxis init --name "Q1 Analysis" --domain research
Initialized Praxis workspace in ./praxis/
Genesis record created: gen_7f3a...
Default constraint envelope applied (research domain)

$ praxis session start
Session started: ses_9b2c...
Trust context active. MCP server at mcp://localhost:4200

[In Claude Code, connected to Praxis MCP]
> Analyze the survey data in data/survey.csv

[Praxis: AUTO_APPROVED — file read within data access constraints]
[Praxis: FLAGGED — large dataset, approaching token budget (82%)]
[Praxis: HELD — attempting to write results to external API]
  → Approve? [y/n/details]

$ praxis status
Session: ses_9b2c (active, 23 min)
Constraints: Financial 82% | Operational OK | Temporal OK | Data OK | Comm HELD(1)
Decisions: 3 recorded | Audit anchors: 47
```

---

## Persona 2: IDE Practitioner

**Who**: Researcher, writer, or developer who works primarily in an IDE (VS Code, Cursor, Windsurf) with embedded AI assistance.

**How they work**: IDE-native. May not use a terminal at all. AI suggestions appear inline or in a sidebar. They want trust infrastructure accessible from within the editor.

**What they need from Praxis**:

| Capability | Implementation |
|---|---|
| IDE extension | Sidebar panel showing trust state |
| Session management | Start/end via UI buttons |
| Decision recording | Form-based input in sidebar |
| Constraint visibility | Status bar indicator |
| Approval workflow | Inline prompt for held actions |
| MCP integration | IDE's AI connects to Praxis backend |

**Key constraint**: The IDE extension must be lightweight — a sidebar panel that communicates with the Praxis runtime via REST API. The extension doesn't implement trust logic; it's a thin client.

**What they see**:

```
┌─ Editor ──────────────────────┬─ Praxis Panel ────────────┐
│                               │                            │
│  [Code / Document]            │  Session: active (15 min)  │
│                               │                            │
│                               │  Constraints               │
│                               │  ■ Financial: 45%          │
│                               │  ■ Operational: OK         │
│                               │  ■ Temporal: OK            │
│                               │  ■ Data: OK                │
│                               │  ■ Communication: OK       │
│                               │                            │
│                               │  Recent Decisions (3)      │
│                               │  ├ Scope: Focus on Ch. 2   │
│                               │  ├ Method: Use regression  │
│                               │  └ Data: Exclude outliers  │
│                               │                            │
│                               │  [+ Record Decision]       │
│                               │                            │
│                               │  Held Actions (1)          │
│                               │  └ Write to external API   │
│                               │    [Approve] [Deny]        │
│                               │                            │
└───────────────────────────────┴────────────────────────────┘
```

---

## Persona 3: Non-Technical Collaborator

**Who**: Business user, manager, student, or professional who uses AI through chat interfaces (Claude Desktop, ChatGPT) or desktop applications. No terminal. No IDE. May copy-paste between AI chat and Word/Google Docs/Overleaf.

**How they work**: Point-and-click. Chat-based interaction with AI. Documents in familiar tools (Word, Google Docs, Notion). Expects trust infrastructure to be invisible and automatic.

**What they need from Praxis**:

| Capability | Implementation |
|---|---|
| Web dashboard | Browser-based session management |
| Desktop app | Native application with system tray |
| Session wizard | Guided setup ("What are you working on?") |
| Constraint editor | Visual sliders and toggles |
| Approval workflows | One-click approve/deny with context |
| Notifications | System notifications for held actions |
| Export | One-click verification bundle generation |

**Key insight**: This persona has the highest friction if poorly designed and the broadest reach if done right. Most AI users are not developers. A CO platform that only serves developers misses 90% of the market.

**What they see**:

```
┌─ Praxis Dashboard ──────────────────────────────────────────┐
│                                                              │
│  Welcome back, Sarah                                         │
│                                                              │
│  ┌─ Active Sessions ──────────────────────────────────┐     │
│  │                                                     │     │
│  │  📋 Q1 Report (45 min)          [Resume] [Pause]   │     │
│  │     Constraints: OK | 3 decisions | 0 held          │     │
│  │                                                     │     │
│  │  📋 Budget Review (paused)       [Resume]           │     │
│  │     Constraints: Financial 90% | 1 held             │     │
│  │                                                     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─ Needs Your Attention ─────────────────────────────┐     │
│  │                                                     │     │
│  │  ⚠️  Budget Review: AI wants to access payroll data  │     │
│  │     Data Access constraint triggered                 │     │
│  │     [Approve] [Deny] [View Details]                 │     │
│  │                                                     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  [+ New Session]    [View History]    [Export Report]        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Persona 4: Supervisor

**Who**: Professor, manager, compliance officer, or team lead who reviews others' AI-assisted work. Does not use AI directly. Needs to verify that trust protocols were followed.

**How they work**: Receives verification bundles or accesses shared dashboards. Reviews trust chains, decision records, and constraint compliance. May need to approve/deny delegated actions.

**What they need from Praxis**:

| Capability | Implementation |
|---|---|
| Verification dashboard | Read-only web view of trust state |
| Delegation trees | Visual tree of who authorized what |
| Decision review | Browse reasoning traces and alternatives |
| Approval queue | Approve/deny held actions escalated to them |
| Compliance reports | Exportable reports for institutional requirements |
| No installation | Everything works in a browser |

**What they see**:

```
┌─ Supervisor Dashboard ──────────────────────────────────────┐
│                                                              │
│  Team Trust Overview                                         │
│                                                              │
│  ┌─ Active Sessions ──────────────────────────────────┐     │
│  │  Alice: Q1 Analysis (2h, 12 decisions, clean)       │     │
│  │  Bob: Code Review (45m, 3 decisions, 1 flagged)     │     │
│  │  Carol: Research Draft (3h, 8 decisions, clean)     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─ Escalated to You ─────────────────────────────────┐     │
│  │                                                     │     │
│  │  Bob: Wants to deploy to staging                    │     │
│  │  Constraint: Operational (deployment requires       │     │
│  │  supervisor approval)                               │     │
│  │  Reasoning: "Tests pass, reviewed by Alice"         │     │
│  │  [Approve] [Deny] [View Full Context]               │     │
│  │                                                     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─ Trust Chain: Bob's Code Review ───────────────────┐     │
│  │  Genesis (You) ──► Delegation (Bob)                 │     │
│  │    Constraints: No deploy, read-only /prod/         │     │
│  │    47 audit anchors, chain valid ✓                  │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Persona 5: External Auditor

**Who**: Ethics board member, journal reviewer, compliance auditor, or regulator who needs independent verification. No prior relationship with the practitioner. May be non-technical.

**How they work**: Receives a verification bundle (ZIP file). Opens it in a browser. Runs client-side verification without installing anything. Produces an assessment of trust compliance.

**What they need from Praxis**:

| Capability | Implementation |
|---|---|
| Self-contained bundle | ZIP with JSON data + HTML viewer + JS verifier |
| Zero installation | Everything runs in the browser |
| Chain verification | Client-side cryptographic validation |
| Timeline view | Chronological view of all actions and decisions |
| Constraint review | What constraints were defined and whether they held |
| Assessment template | Structured evaluation criteria for different domains |

**What they see**:

```
┌─ Verification Bundle Viewer (browser) ──────────────────────┐
│                                                               │
│  Project: Q1 Financial Analysis                               │
│  Author: Sarah Chen                                           │
│  Duration: 4h 23m across 3 sessions                           │
│                                                               │
│  ┌─ Integrity Check ─────────────────────────────────────┐   │
│  │  Chain integrity: ✓ Valid (147 anchors, no breaks)     │   │
│  │  Genesis record: ✓ Valid signature                     │   │
│  │  Temporal order: ✓ Monotonic timestamps                │   │
│  │  Constraint compliance: ✓ No violations                │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ Decision Timeline ───────────────────────────────────┐   │
│  │  09:15  Session start                                  │   │
│  │  09:17  Decision: Scope — "Focus on Q1 only"          │   │
│  │         Rationale: "Q2 data not yet audited"           │   │
│  │         Confidence: 95%                                │   │
│  │  09:23  FLAGGED: Token budget at 80%                   │   │
│  │  09:45  Decision: Method — "Use YoY comparison"       │   │
│  │  10:12  HELD: External API call → Approved by author   │   │
│  │  ...                                                   │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  [Download Full Report (PDF)]  [Verify Again]                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Cross-Persona Feature Matrix

| Feature | CLI | IDE | Web/Desktop | Supervisor | Auditor |
|---|---|---|---|---|---|
| Initialize workspace | CLI command | Panel button | Wizard | N/A | N/A |
| Start/end sessions | CLI command | Panel button | Dashboard | N/A | N/A |
| Record decisions | CLI + MCP auto | Panel form + MCP | Dashboard form | N/A | N/A |
| View constraints | `praxis status` | Status bar | Dashboard | Dashboard (read-only) | Bundle viewer |
| Approve held actions | Terminal prompt | Inline prompt | Dashboard button | Dashboard button | N/A |
| View audit trail | `praxis audit` | Panel section | Dashboard | Dashboard | Bundle viewer |
| Export verification | `praxis export` | Context menu | Dashboard button | Dashboard button | Already exported |
| Verify integrity | `praxis verify` | Panel button | Dashboard | Dashboard | Bundle viewer (client-side) |
| Delegate authority | `praxis delegate` | Panel form | Dashboard | Dashboard | N/A |
| Browse trust chain | `praxis chain` | Panel tree | Interactive tree | Interactive tree | Bundle tree |

## Priority

1. **CLI Practitioner** — Foundation capability, smallest engineering gap, highest leverage
2. **Web Dashboard** — Enables Personas 3, 4, and 5 simultaneously
3. **External Auditor** — Verification bundles force correct chain integrity
4. **Desktop App** — Native experience for non-technical users
5. **IDE Extension** — High value but significant per-IDE engineering effort
6. **Mobile Companion** — Approval workflows and monitoring from phone/tablet
