# User Flows: CLI Practitioner (P0)

**Date**: 2026-03-15
**Status**: Design
**Persona**: CLI Practitioner (developer, researcher, analyst working in terminal with AI assistants)

---

## Interaction Model

The CLI Practitioner interacts with Praxis through two channels simultaneously:

1. **Direct CLI** -- `praxis` commands for session management, constraint setup, and manual operations
2. **MCP passthrough** -- AI assistant (Claude Code, Aider, etc.) connects to Praxis as an MCP server, and every tool call flows through the trust layer automatically

The key design principle: **trust is the medium, not the camera**. The practitioner does not "activate logging" -- they work within a trust environment. The AI does not get observed from outside -- it operates within constraint envelopes that produce audit anchors as a side effect of execution.

---

## Flow 1: First-Time Setup

### Trigger

User has installed Praxis (`pip install praxis`) and wants to set up a project for trust-aware AI collaboration.

### Step-by-Step

**Step 1: Initialize workspace**

What the user types:

```bash
praxis init --name "Q1 Financial Analysis" --domain research
```

What the user sees:

```
Praxis v0.1.0

Initializing workspace...

  Workspace:   Q1 Financial Analysis
  Domain:      research
  Location:    ./praxis/

  Created:
    praxis/genesis.json          Root of trust (Ed25519 keypair)
    praxis/config.yaml           Workspace configuration
    praxis/constraints/          Constraint envelope definitions
    praxis/sessions/             Session records
    praxis/anchors/              Audit anchor chain

  Default constraints applied (research domain):
    Financial:     $50/session token budget
    Operational:   Read-only by default, write requires confirmation
    Temporal:      No restrictions (research hours vary)
    Data Access:   Project directory only
    Communication: No external API calls without approval

  Genesis record: gen_7f3a8b2c
  Your authority is established. All AI actions will trace back to you.

Next steps:
  1. Start a session:        praxis session start
  2. Connect your AI:        Configure MCP server (see below)
  3. Customize constraints:  praxis constraints edit
```

What happens behind the scenes:

- EATP ESTABLISH operation executes
- Ed25519 keypair generated and stored (`praxis/keys/private.key` at 600 permissions)
- Genesis Record created and self-signed (root of trust)
- Domain template loaded (research template provides sensible default constraints)
- Capability Attestation created for the practitioner
- Config file written with constraint envelope definition
- All artifacts are hash-chained from genesis

**Error states**:

| Error | User sees | Recovery |
|---|---|---|
| Directory already initialized | "This directory already has a Praxis workspace. Use `praxis reinit` to start fresh or `praxis status` to check current state." | `praxis status` or `praxis reinit --force` |
| Missing domain template | "Unknown domain 'X'. Available domains: research, software, education, governance. Use `--domain custom` for blank constraints." | Choose valid domain or use custom |
| Insufficient permissions | "Cannot create praxis/ directory. Check write permissions." | Fix directory permissions |
| Key generation failure | "Cryptographic key generation failed. Ensure `cryptography` package is installed." | Reinstall dependencies |

---

**Step 2: Connect AI assistant via MCP**

What the user types (in their AI assistant config):

```json
{
  "mcpServers": {
    "praxis": {
      "command": "praxis",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

What the user sees (when the AI assistant connects):

```
[Praxis MCP] Server started on stdio
[Praxis MCP] Workspace: Q1 Financial Analysis
[Praxis MCP] Genesis: gen_7f3a8b2c
[Praxis MCP] Tools registered: 12 (all constraint-evaluated)
[Praxis MCP] Ready. All tool calls will flow through trust layer.
```

What happens behind the scenes:

- Praxis starts an MCP server (stdio transport for local, SSE for remote)
- The MCP server wraps the downstream tool servers (filesystem, git, etc.)
- Every tool call is intercepted by the Constraint Enforcer before execution
- The AI assistant sees Praxis tools, not raw tools -- trust is transparent to the AI
- A Delegation Record is created for the AI assistant session with constraints inherited from the workspace

**AI UX considerations**:

- **Stream of Thought**: When the MCP server starts, it provides clear status about what is being enforced. The practitioner sees the trust infrastructure activating, not just "server started."
- **Disclosure**: The AI assistant should know it is operating through Praxis. The MCP server provides system context explaining that actions are constraint-evaluated.
- **Controls**: The practitioner can stop the MCP server at any time with Ctrl+C or `praxis mcp stop`.

---

**Step 3: Customize constraints (optional)**

What the user types:

```bash
praxis constraints edit
```

What the user sees:

```
Current constraint envelope for: Q1 Financial Analysis

  Financial:
    max_session_cost:     $50.00
    daily_limit:          $200.00
    approval_threshold:   $25.00          [edit? y/n]

  Operational:
    allowed_actions:      [read_file, search, list_directory]
    held_actions:         [write_file, create_file, delete_file]
    blocked_actions:      [execute_command]  [edit? y/n]

  Temporal:
    operating_hours:      unrestricted
    session_timeout:      4h              [edit? y/n]

  Data Access:
    read_paths:           [./]
    write_paths:          [./output/, ./drafts/]
    blocked_paths:        [~/.ssh/, ~/.aws/]  [edit? y/n]

  Communication:
    external_apis:        held (requires approval)
    email:                blocked
    webhooks:             blocked          [edit? y/n]

Save changes? [y/n]
```

What happens behind the scenes:

- Current Constraint Envelope loaded from `praxis/constraints/envelope.yaml`
- Each edit creates a new Constraint Envelope version (old version preserved in chain)
- Changes are signed by the practitioner's key
- Audit Anchor created for the constraint change with reasoning trace: "Practitioner modified constraints"
- The "constraints can only tighten" rule is enforced for sub-delegations (the practitioner can loosen their own constraints since they are the genesis authority)

---

## Flow 2: Constrained AI Session

### Trigger

Practitioner has an initialized workspace and wants to start working with their AI assistant.

### Step-by-Step

**Step 1: Start session**

What the user types:

```bash
praxis session start --context "Analyzing Q1 survey data for board report"
```

What the user sees:

```
Session started: ses_9b2c4e1f
  Context:     Analyzing Q1 survey data for board report
  Constraints: Active (research domain defaults)
  MCP:         Connected (Claude Code)
  Trust state: Clean (0 decisions, 0 anchors)

Session is active. Your AI assistant is now operating through the trust layer.
```

What happens behind the scenes:

- New session record created with unique ID
- Session linked to genesis record via delegation chain
- Constraint Envelope snapshot taken (session inherits current workspace constraints)
- Session-start Audit Anchor created with:
  - Session context
  - Constraint envelope hash
  - Environment metadata (OS, tool versions, model ID if available)
  - Timestamp (signed)
- MCP server notified of active session
- File system snapshot (hashes of all files in project directory)

---

**Step 2: AI works within constraints (AUTO_APPROVED actions)**

What the practitioner does: Works normally with their AI assistant. They ask it to analyze a CSV file.

What the user sees in Claude Code:

```
> Analyze the survey data in data/survey.csv and summarize key findings

[Claude reads data/survey.csv]
[Praxis: AUTO_APPROVED -- read_file within data access constraints]

The survey data contains 1,247 responses across 5 categories...
```

What the practitioner sees from Praxis (ambient, non-intrusive):

Nothing extra. AUTO_APPROVED actions are silent by default. The practitioner configured their trust envelope and the AI is operating within it. No interruption needed.

What happens behind the scenes:

- AI assistant calls `read_file` tool via MCP
- Praxis MCP proxy intercepts the tool call
- Constraint Enforcer evaluates: Is `data/survey.csv` within `read_paths`? Yes.
- Verification result: AUTO_APPROVED
- Tool call forwarded to downstream filesystem MCP server
- Audit Anchor created: action=read_file, path=data/survey.csv, verdict=AUTO_APPROVED
- Anchor hash-chained to previous anchor

**AI UX pattern**: This is the **human-on-the-loop** pattern in action. The human defined the envelope. Within the envelope, the AI operates autonomously. The human's contribution was the constraint definition, not per-action approval.

---

**Step 3: AI approaches a boundary (FLAGGED action)**

What happens: The AI's analysis is complex and token usage is climbing.

What the user sees:

```
[Praxis: FLAGGED -- token budget at 82% ($41/$50)]

The statistical analysis reveals three significant correlations...
```

What happens behind the scenes:

- After each tool call, the Constraint Enforcer updates cumulative tracking
- Token cost estimate pushed past 80% of session budget ($50)
- Verification result: FLAGGED (valid with minor violation)
- Action proceeds (FLAGGED does not block)
- Audit Anchor created with `verdict=FLAGGED` and `detail="token_budget_82_percent"`
- Practitioner is notified but workflow is not interrupted

**Design decision**: FLAGGED is informational. It tells the practitioner "you're approaching a boundary" without stopping work. This prevents the annoyance of false stops while maintaining awareness. The notification is brief and non-blocking -- a single line in the terminal output, not a modal dialog.

---

**Step 4: AI hits a soft limit (HELD action)**

What happens: The AI tries to write results to an external API endpoint.

What the user sees:

```
[Praxis: HELD -- external API call requires approval]

  Action:      POST https://api.analytics.example.com/results
  Constraint:  Communication (external_apis: held)
  Reason:      External API calls are configured to require human approval
  Context:     AI wants to push analysis results to shared analytics dashboard

  What would you like to do?
  [a] Approve this action
  [d] Deny this action
  [v] View full request details
  [s] Approve and add to allowed list for this session
  [q] Deny and add to blocked list for this session
  >
```

What happens behind the scenes:

- AI assistant calls a tool that would make an external HTTP request
- Constraint Enforcer evaluates: `external_apis` is set to `held`
- Verification result: HELD
- Tool call is NOT forwarded -- it is queued
- HELD Audit Anchor created with reasoning: "External API call intercepted, awaiting human approval"
- MCP proxy returns a hold response to the AI assistant
- The AI assistant's execution pauses on this tool call
- Timer starts (configurable; default: no auto-approve per EATP spec)

**If practitioner approves** (`a`):

```
> a
[Praxis: APPROVED -- external API call authorized by practitioner]
[Praxis: Audit anchor: anc_f4a2... (HELD -> APPROVED)]

POST to analytics API completed. Results uploaded successfully.
```

Behind the scenes:
- Practitioner's approval creates an Audit Anchor with `verdict=HELD_APPROVED`
- The approval is signed by the practitioner's key
- The held tool call is released and forwarded to the downstream server
- The reasoning trace records: "Practitioner approved external API call after review"

**If practitioner denies** (`d`):

```
> d
[Praxis: DENIED -- external API call blocked by practitioner]

I'll save the results locally instead. Writing to output/results.json...
```

Behind the scenes:
- Denial creates an Audit Anchor with `verdict=HELD_DENIED`
- The tool call is rejected with an explanation passed back to the AI
- The AI assistant receives the denial reason and can adapt

**Design decisions for held actions**:

| Decision | Choice | Rationale |
|---|---|---|
| Presentation | Inline in terminal flow | CLI practitioners expect terminal interaction, not separate windows |
| Options | 5 choices (approve, deny, details, approve+allow, deny+block) | Covers the common cases without overwhelming |
| Timeout | No auto-approve (per EATP spec) | HELD exists because human judgment is needed; auto-approve defeats the purpose |
| AI awareness | AI is told the action was held and receives the outcome | Allows the AI to adapt its plan (e.g., save locally instead of pushing externally) |

---

**Step 5: AI hits a hard limit (BLOCKED action)**

What happens: The AI tries to execute a shell command, which is blocked for research domain.

What the user sees:

```
[Praxis: BLOCKED -- command execution is forbidden in this constraint envelope]

  Action:      execute_command("rm -rf old_data/")
  Constraint:  Operational (blocked_actions: execute_command)
  Status:      BLOCKED -- this action cannot proceed

  To change this constraint: praxis constraints edit
```

What happens behind the scenes:

- Constraint Enforcer evaluates: `execute_command` is in `blocked_actions`
- Verification result: BLOCKED
- Tool call is immediately rejected (not queued, not held)
- BLOCKED Audit Anchor created
- `EATPBlockedError` raised and returned to MCP
- AI receives clear explanation of why the action was blocked

**Design decision**: BLOCKED is absolute. No "override" button. No "are you sure?" prompt. The constraint says blocked, the action does not proceed. If the practitioner wants to change this, they modify their constraint envelope -- a deliberate act that creates its own audit trail.

---

**Step 6: Record a decision (deliberation capture)**

What the user types:

```bash
praxis decide \
  --type methodology \
  --decision "Use year-over-year comparison instead of quarter-over-quarter" \
  --rationale "Q4 had anomalous data due to system migration. YoY gives cleaner baseline." \
  --alternative "QoQ comparison with Q4 excluded" \
  --alternative "Rolling 4-quarter average" \
  --confidence 0.85
```

What the user sees:

```
Decision recorded: dec_3a7f1e9b
  Type:        methodology
  Decision:    Use year-over-year comparison instead of quarter-over-quarter
  Confidence:  85%
  Alternatives: 2 considered
  Anchor:      anc_8c2d... (chain position: 53)
```

What happens behind the scenes:

- Decision Record created with structured fields:
  - `decision`: What was decided
  - `rationale`: Why (free text, but structured for later analysis)
  - `alternatives_considered`: What other options were evaluated
  - `confidence`: Self-assessed (0.0 to 1.0)
  - `methodology`: How the decision was reached
- The Decision Record is wrapped in a Reasoning Trace (EATP Section 6)
- Reasoning Trace hash computed (SHA-256 of JCS-canonicalized content)
- Reasoning Signature created using practitioner's key
- Audit Anchor created with the reasoning trace attached
- Hash-chained to previous anchor (temporal integrity)
- Confidentiality level defaults to `restricted` (configurable)

**AI can also record decisions via MCP**: If the AI assistant recognizes a decision point during conversation, it can call the `praxis_decide` MCP tool to record it automatically. The practitioner sees the decision appear in their session log.

---

**Step 7: Check session status**

What the user types:

```bash
praxis status
```

What the user sees:

```
Session: ses_9b2c4e1f (active, 47 min)
Context: Analyzing Q1 survey data for board report

Constraints:
  Financial:     ████████░░  82% ($41.00 / $50.00)
  Operational:   ██████████  OK  (3 held, 0 blocked today)
  Temporal:      ██████████  OK  (47m / 4h timeout)
  Data Access:   ██████████  OK  (12 reads, 2 writes)
  Communication: ██████████  OK  (1 held -> approved)

Trust State:
  Audit anchors:   67
  Chain integrity:  Valid (unbroken)
  Decisions:        4 recorded
  Actions held:     3 (2 approved, 1 denied)
  Actions blocked:  1

Verification Gradient:
  AUTO_APPROVED:   58
  FLAGGED:         5
  HELD:            3
  BLOCKED:         1
```

**AI UX pattern**: This is the **Stream of Thought** pattern adapted for CLI. Instead of showing real-time AI reasoning, it shows real-time trust state. The practitioner can see at a glance: how much of their constraint budget is used, how many actions required intervention, and whether the chain is intact.

**Design decision -- visual density**: CLI practitioners want dense, scannable information. The status output uses progress bars for constraint utilization, counts for actions, and a clear valid/invalid indicator for chain integrity. No prose explanations at this level -- those are available via `praxis status --verbose`.

---

**Step 8: End session**

What the user types:

```bash
praxis session end --summary "Completed Q1 analysis. YoY comparison chosen. Three key findings documented in output/report.md"
```

What the user sees:

```
Session ended: ses_9b2c4e1f

Session Summary:
  Duration:       52 minutes
  Decisions:      4 recorded
  Audit anchors:  73
  Chain:          Valid (unbroken from genesis)

  Constraint utilization:
    Financial:     82% ($41.00)
    Operational:   3 held (2 approved, 1 denied), 1 blocked
    Temporal:      52m of 4h
    Data:          12 reads, 2 writes, all within bounds
    Communication: 1 external API (approved)

  Files changed:  3
    output/report.md        (created)
    output/results.json     (created)
    data/survey_cleaned.csv (created)

  Attestation:    att_5e9c... (session attestation generated)
  Export:         praxis export --session ses_9b2c4e1f

Session archived. Trust chain intact.
```

What happens behind the scenes:

- File system diff computed (current hashes vs. session-start snapshot)
- Session-end Audit Anchor created with:
  - Duration
  - File change summary (paths, operation type, diff stats)
  - Decision count
  - Constraint utilization summary
  - Session summary (practitioner-provided)
- Capability Attestation generated for the session (EATP Element 4)
- The attestation is a signed declaration: "This session operated within these constraints, produced these decisions, and maintained chain integrity"
- Session status changes to `archived`
- MCP proxy continues running (for next session) but logs that the session has ended

---

## Flow 3: Decision Recording (Deliberation Capture)

### Trigger

During an AI collaboration session, the practitioner makes a significant decision and wants to record it with full reasoning.

### Three Capture Modes

**Mode 1: CLI explicit (practitioner-initiated)**

```bash
praxis decide \
  --type scope \
  --decision "Remove Section 5 (implementation details)" \
  --rationale "Reviewer 2 says it distracts from the theoretical contribution" \
  --alternative "Keep Section 5 but shorten" \
  --alternative "Move to appendix" \
  --confidence 0.9
```

**Mode 2: MCP automatic (AI-initiated)**

The AI assistant recognizes a decision point and records it via the `praxis_decide` MCP tool:

```
[Praxis MCP] Decision recorded by AI assistant: dec_7b2f...
  Type:        argument
  Decision:    Frame analysis as complementary to existing approaches
  Rationale:   Positioning analysis shows convergence on methodology
  Alternatives: 2 considered
  Confidence:  0.85
```

The practitioner sees this in their session log and can amend or override it.

**Mode 3: Quick capture (minimal friction)**

```bash
praxis decide "Use regression analysis for Q1 data"
```

Records a decision with just the decision text. Type defaults to `general`, confidence defaults to `0.7`, no alternatives recorded. For moments when stopping to fill in all fields would break flow.

### Decision Record Structure

Every decision, regardless of capture mode, produces the same underlying structure:

```
Decision Record (dec_XXXX)
  decision:                 string (what was decided)
  rationale:                string (why)
  type:                     enum (scope, methodology, argument, design, data, other)
  alternatives_considered:  string[] (what was rejected and why)
  confidence:               float 0.0-1.0 (self-assessed)
  methodology:              string (how the decision was reached)
  evidence:                 EvidenceRef[] (what informed it)
  source:                   enum (human, ai, collaborative)
  session_id:               string (link to session)
  timestamp:                ISO 8601

Wrapped in:
  Reasoning Trace (EATP Section 6)
    reasoning_trace_hash:   SHA-256 of JCS-canonicalized content
    reasoning_signature:    Ed25519 signature by the practitioner
    confidentiality:        ConfidentialityLevel (default: restricted)

Anchored by:
  Audit Anchor (hash-chained to previous anchor)
```

### Edge Cases

| Situation | Handling |
|---|---|
| Decision recorded with no active session | Create an orphan decision linked to workspace genesis. Warn: "No active session. Decision will be recorded at workspace level." |
| AI records a decision the practitioner disagrees with | `praxis decide amend dec_7b2f --decision "..." --rationale "..."` creates an amendment anchor linked to the original |
| Practitioner wants to retract a decision | `praxis decide retract dec_7b2f --reason "..."` creates a retraction anchor. Original remains in chain (immutable) but is marked retracted. |
| Confidence below 0.5 | Accepted without warning. Low confidence is legitimate (uncertainty is honest). |
| Very long rationale | Accepted up to 50,000 characters (EATP input validation limit). Warning above 10,000 characters. |

---

## Flow 4: Export and Verification

### Trigger

Session is complete and the practitioner wants to share trust evidence with a supervisor, auditor, or collaborator.

### Step-by-Step

**Step 1: Export verification bundle**

```bash
praxis export --session ses_9b2c4e1f --format bundle
```

What the user sees:

```
Generating verification bundle for session ses_9b2c4e1f...

  Chain validation:  Pass (73 anchors, 0 breaks)
  Genesis included:  Yes (gen_7f3a8b2c)
  Decisions:         4 included
  Constraints:       5 dimensions, all documented

  Bundle created: praxis-bundle-ses_9b2c4e1f.zip (142 KB)

  Contents:
    bundle.json           All chain data (machine-readable)
    verify.html           Self-contained verification page
    README.txt            Bundle description and verification instructions
    algorithm.txt         Step-by-step manual verification procedure

  Share this file with your supervisor or auditor.
  They can open verify.html in any browser to verify independently.
```

**Step 2: Export in other formats**

```bash
# Human-readable report
praxis export --session ses_9b2c4e1f --format markdown --output report.md

# Machine-readable data
praxis export --session ses_9b2c4e1f --format json --output session.json

# All sessions in workspace
praxis export --all --format bundle --output full-workspace.zip
```

---

## Trust Communication Design

How the system communicates trust state without being intrusive.

### Ambient Trust Indicators

The terminal output uses a graduated visibility model:

| Verification Level | Terminal Output | Visibility |
|---|---|---|
| AUTO_APPROVED | Nothing (silent) | Invisible -- no interruption for routine actions |
| FLAGGED | Single-line info: `[Praxis: FLAGGED -- reason]` | Noticeable but non-blocking |
| HELD | Multi-line prompt with options | Blocking -- requires practitioner decision |
| BLOCKED | Single-line error: `[Praxis: BLOCKED -- reason]` | Visible error, no action possible |

### Design Principle: Quiet When Good, Loud When Important

The trust layer should feel like a well-functioning governance system: you don't notice it when everything is within bounds, it gets your attention when something needs judgment, and it is immovable when something is forbidden.

This mirrors the human-on-the-loop principle: the human defined the envelope. Within the envelope, execution is autonomous and quiet. At the boundary, the human is consulted. Beyond the boundary, the action is stopped.

### Progressive Disclosure for Trust Details

```
Level 1: praxis status                    -- Dashboard summary (counts, percentages)
Level 2: praxis status --verbose          -- Detailed constraint state with recent actions
Level 3: praxis audit                     -- Full audit trail with anchors
Level 4: praxis audit --anchor anc_8c2d   -- Individual anchor with full chain context
Level 5: praxis chain                     -- Complete trust chain from genesis to current
```

Each level adds detail. The practitioner chooses their depth. Default output optimizes for quick scanning.

---

## Error Recovery

| Scenario | Recovery |
|---|---|
| MCP connection lost mid-session | Session remains active. Reconnect with same session ID. Actions during disconnection are not captured (gap in chain, noted in session summary). |
| Terminal crashes during held action | Held action remains in queue. On restart, `praxis status` shows pending held actions. |
| Key file corrupted | `praxis recover --from-backup` uses backup key. If no backup, `praxis reinit` with new genesis (old chain is archived but verification will note the discontinuity). |
| Chain integrity failure detected | `praxis verify` reports exactly which anchor broke the chain. Cannot be auto-fixed (by design -- if a chain breaks, something happened). |
| Constraint budget exhausted | Session continues but all actions in that dimension are HELD. Practitioner can expand the constraint or end the session. |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Trust infrastructure position | Medium (not camera) | Per vision critique: AI operates THROUGH trust, not alongside it |
| Default constraint strictness | Domain-template defaults | Reduces setup friction; practitioner can customize later |
| AUTO_APPROVED visibility | Silent | Noise-free for routine operations; trust is felt through absence of problems |
| HELD timeout behavior | No auto-approve | Per EATP spec: HELD exists because human judgment is needed |
| BLOCKED override | Not possible inline | Constraint changes are a separate deliberate action with their own audit trail |
| Decision source tracking | human / ai / collaborative | Important for downstream analysis (who initiated the decision?) |
| Chain gaps on disconnect | Noted, not fatal | Pragmatic: CLI environments lose connections. The gap is honestly recorded. |
| MCP proxy architecture | Transparent proxy | AI assistant does not know it is proxied; trust is infrastructure-level, not prompt-level |
