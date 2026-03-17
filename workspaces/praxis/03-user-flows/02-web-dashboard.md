# User Flows: Web Dashboard (P1)

**Date**: 2026-03-15
**Status**: Design
**Personas**: Non-Technical Collaborator, Supervisor, External Auditor (browser-based)

---

## Overview

The Web Dashboard serves three sub-personas through a single browser-based interface with role-based views. It is the second priority after CLI because it simultaneously enables three personas (Non-Technical Collaborator, Supervisor, Auditor) who cannot use a terminal.

The dashboard communicates with the Praxis runtime via REST API and WebSocket (for real-time updates). It does NOT implement trust logic -- it is a thin client that renders trust state from the backend.

---

## Shared Design Principles

### Trust Communication Without Intrusion

The dashboard uses a graduated visibility model adapted from the CLI patterns:

| Trust State | Visual Treatment | Interaction |
|---|---|---|
| AUTO_APPROVED | No indicator (clean state) | None required |
| FLAGGED | Amber accent on constraint indicator | Visible in constraint panel; no action needed |
| HELD | Prominent card in "Needs Attention" area | Requires user decision (approve/deny) |
| BLOCKED | Red indicator with explanation | Informational only (action already prevented) |

### AI State Indicators

The dashboard must always answer: **What is the AI doing right now?**

| State | Indicator | What the user understands |
|---|---|---|
| Idle | Dim session card | AI is waiting for instructions |
| Active | Pulsing accent on session card | AI is working within constraints |
| Waiting (HELD) | Amber alert badge | AI is paused, waiting for human decision |
| Blocked | Red indicator on session | AI tried something forbidden; it was stopped |
| Session ended | Archived status with checkmark | Work is complete; trust chain is sealed |

### Progressive Disclosure

Non-technical users see simple surfaces. Supervisors see delegation trees. Auditors see cryptographic details. All three access the same data through different lenses.

```
Non-Technical:   "3 decisions made, all constraints OK"
Supervisor:      "3 decisions made, chain valid, 1 flagged action in operational dimension"
Auditor:         "73 anchors, SHA-256 chain unbroken, Ed25519 signatures valid, 0 violations"
```

---

## Flow A: Non-Technical Collaborator

### Persona Profile

Business user, student, or professional who uses AI through chat interfaces. No terminal, no IDE. Expects trust infrastructure to be guided and visual.

### Sub-Flow A1: First Session Setup (Session Wizard)

**Trigger**: User logs in for the first time or clicks "New Session."

**Step 1: Welcome and orientation**

What the user sees:

```
Welcome to Praxis

Praxis helps you work with AI safely and accountably.
Everything your AI does will be tracked and verifiable.

What are you working on today?

  [ Start a new project ]     [ Join an existing project ]
```

**Design decision**: No jargon. "Genesis record" becomes "your project's trust foundation." "Constraint envelope" becomes "the rules for what AI can do." The system explains in outcomes, not mechanisms.

**Step 2: Project setup (if new)**

What the user sees:

```
New Project

  Project name:     [Q1 Board Report                    ]
  What kind of work? [dropdown: Research / Writing / Analysis / Code / Custom]

  Based on your selection, we've set up sensible defaults:

  What AI can do automatically:
    Read your project files                           [toggle: on]
    Search for information                            [toggle: on]
    Create draft documents                            [toggle: on]

  What AI needs your approval for:
    Modify existing files                             [toggle: on]
    Access data outside your project folder           [toggle: on]
    Connect to external services                      [toggle: on]

  What AI cannot do:
    Delete files                                      [always blocked]
    Run system commands                               [always blocked]
    Share data externally without approval             [always blocked]

  Spending limit per session: [$50    ] (estimated AI usage cost)

  [ Create Project ]
```

What happens behind the scenes:

- User selections map to EATP constraint dimensions
- The toggle interface is a visual representation of the Constraint Envelope
- "What AI can do automatically" = actions with AUTO_APPROVED verdict
- "What AI needs your approval for" = actions with HELD verdict
- "What AI cannot do" = actions with BLOCKED verdict
- Genesis Record, Constraint Envelope, and initial Delegation Record created
- Ed25519 keypair generated (managed by the server; the user does not interact with keys)

**AI UX patterns applied**:

- **Templates**: The "what kind of work" dropdown loads a domain-specific constraint template (research, writing, analysis, code)
- **Suggestions**: Toggle defaults are pre-set based on the selected work type
- **Draft Mode**: Constraints can be adjusted before the session starts (preview the rules before committing)
- **Caveat**: A brief note explains that spending limits are estimates based on typical token usage

**Error states**:

| Error | User sees | Recovery |
|---|---|---|
| Project name already exists | "A project with this name already exists. Choose a different name or open the existing project." | Rename or navigate to existing |
| Server connection lost | "Unable to connect to Praxis. Check your connection and try again." | Retry button |

---

**Step 3: Start working**

What the user sees after project creation:

```
Q1 Board Report -- Session Active

  Session started 2 minutes ago

  Constraints                               Needs Your Attention
  Financial:     [====------] 12%            (none right now)
  Operational:   OK
  Temporal:      OK
  Data:          OK
  Communication: OK

  Recent Activity
  10:02  Session started
  10:03  AI read project-brief.md (auto-approved)
  10:04  AI read data/q1-results.csv (auto-approved)

  Decisions Made
  (none yet)

  [Record a Decision]   [Pause Session]   [End Session]
```

**Design decision**: The activity feed shows AUTO_APPROVED actions as a lightweight log. Unlike the CLI (where AUTO_APPROVED is silent), the dashboard shows them because non-technical users benefit from seeing that the system is working. The feed is scrollable and timestamped but not attention-demanding.

---

### Sub-Flow A2: Handling a Held Action

**Trigger**: AI tries an action that requires human approval.

What the user sees:

```
  +---------------------------------------------------------+
  |  Needs Your Attention                                    |
  |                                                          |
  |  AI wants to modify an existing file                     |
  |                                                          |
  |  File: output/draft-report.md                            |
  |  Action: Replace the executive summary with a            |
  |          revised version                                 |
  |  Why this needs approval: Modifying existing files       |
  |          requires your confirmation                      |
  |                                                          |
  |  [View Changes]  [Approve]  [Deny]                      |
  |                                                          |
  +---------------------------------------------------------+
```

If the user clicks "View Changes":

```
  Changes AI wants to make to output/draft-report.md:

  Current executive summary (first 5 lines):
    "Q1 results show moderate growth across..."

  Proposed executive summary (first 5 lines):
    "Q1 results exceeded projections by 12%, driven by..."

  Full diff available: [Show Full Diff]

  [Approve These Changes]   [Deny]   [Ask AI to Revise]
```

What happens behind the scenes:

- WebSocket pushes HELD event to the dashboard in real-time
- The HELD action card appears in the "Needs Your Attention" area
- If the user was on another browser tab, a browser notification appears: "Praxis: AI needs your approval"
- Clicking Approve creates a HELD_APPROVED Audit Anchor signed by the user's session key
- Clicking Deny creates a HELD_DENIED Audit Anchor and returns the denial to the AI
- Clicking "Ask AI to Revise" denies the current action but sends guidance back to the AI

**AI UX patterns applied**:

- **Verification**: Confirmation gate before an irreversible action (file modification)
- **Action Plan**: The "View Changes" option shows what the AI proposes to do before it does it
- **Controls**: Approve, Deny, and "Ask AI to Revise" give the user three levels of response
- **Disclosure**: The card clearly labels this as an AI-initiated action requiring human judgment

**Design decisions for held actions in the dashboard**:

| Decision | Choice | Rationale |
|---|---|---|
| Notification channel | Browser notification + in-app card | Non-technical users may not be watching the dashboard constantly |
| Default visibility | Above the fold, prominent | This is the most important interaction; it should not be missed |
| Action descriptions | Plain language, not technical | "AI wants to modify an existing file" not "write_file operation intercepted by constraint enforcer" |
| Diff presentation | Side-by-side summary, expandable | Most users want the gist; power users can expand to see full diff |
| Timeout behavior | No auto-approve; amber warning after 10 minutes of no response | Per EATP spec; the warning reminds the user that AI is waiting |

---

### Sub-Flow A3: Visual Constraint Editor

**Trigger**: User wants to adjust what AI can and cannot do.

What the user sees:

```
Constraint Settings -- Q1 Board Report

  Spending Limit
    Per session:  [=====|----] $50
    Per day:      [========|-] $200
    Approval above: [==|-------] $25

  File Access
    Can read:     Project folder and subfolders        [change]
    Can write:    output/ and drafts/ only             [change]
    Cannot access: System files, SSH keys, credentials  [locked]

  External Connections
    External APIs:     Needs your approval              [toggle]
    Email sending:     Blocked                          [toggle]
    Web browsing:      Needs your approval              [toggle]

  Time Limits
    Session timeout:   4 hours                          [change]
    Working hours:     No restriction                   [change]

  [Save Changes]   [Reset to Defaults]
```

What happens behind the scenes:

- Each control maps to a specific EATP constraint dimension and parameter
- Slider/toggle changes do not take effect until "Save Changes" is clicked
- On save, a new Constraint Envelope version is created
- An Audit Anchor records the constraint change with a reasoning trace: "User modified constraints via dashboard"
- The old constraint envelope is preserved in the chain (immutable history)
- If the user is the genesis authority, they can loosen constraints
- If the user is a delegate (e.g., student under professor's constraints), they can only tighten -- controls for loosening are disabled with an explanation: "Your supervisor set this minimum. Contact them to request a change."

**AI UX patterns applied**:

- **Parameters**: Visual controls for adjusting AI behavior boundaries
- **Preset Styles**: "Reset to Defaults" loads the domain template
- **Caveat**: Tooltips explain the implications of each constraint change (e.g., "Removing the spending limit means AI token usage is uncapped")

---

### Sub-Flow A4: Recording a Decision

**Trigger**: User made an important decision during their work and wants to record it.

What the user sees after clicking "Record a Decision":

```
Record a Decision

  What did you decide?
  [Switched from quarterly to annual comparison    ]

  Why?
  [Q4 data was affected by system migration, making]
  [quarterly trends unreliable for this period.     ]

  What other options did you consider? (optional)
    [+ Add alternative]
    1. Quarter-over-quarter with Q4 excluded
    2. Rolling average

  How confident are you?
    [====|-----]  50%  60%  70%  80%  90%  100%
                             ^

  [Record Decision]   [Cancel]
```

**Design decisions**:

- "What did you decide?" and "Why?" are the only required fields
- Alternatives and confidence are optional but visible (not hidden behind "advanced")
- Confidence slider defaults to 70% (a reasonable middle ground)
- The form is short enough to fill in under 30 seconds
- No technical terminology: "confidence" not "basis points," "alternatives" not "rejected hypotheses"

---

## Flow B: Supervisor

### Persona Profile

Professor, manager, compliance officer, or team lead who reviews others' AI-assisted work. Does not use AI directly. Needs read-only verification dashboards and the ability to approve escalated actions.

### Sub-Flow B1: Team Overview

**Trigger**: Supervisor logs into their dashboard.

What the user sees:

```
Team Overview

  Active Sessions
  +-------------------------------------------------------+
  | Alice    Q1 Analysis        2h 12m    12 decisions     |
  |          Constraints: OK    Chain: Valid                |
  +-------------------------------------------------------+
  | Bob      Code Review        45m       3 decisions      |
  |          Constraints: 1 FLAGGED   Chain: Valid         |
  +-------------------------------------------------------+
  | Carol    Research Draft      3h 5m     8 decisions      |
  |          Constraints: OK    Chain: Valid                |
  +-------------------------------------------------------+

  Escalated to You (1)
  +-------------------------------------------------------+
  |  Bob needs your approval                               |
  |                                                        |
  |  Action: Deploy application to staging environment     |
  |  Constraint: Operational (deployment requires          |
  |    supervisor approval per team policy)                 |
  |  Bob's note: "All tests pass, Alice reviewed the code" |
  |                                                        |
  |  [Approve]  [Deny]  [View Full Context]                |
  +-------------------------------------------------------+

  Recent Completed Sessions
  Alice   Q4 Retrospective     Yesterday   15 decisions   [View]
  Carol   Literature Review    2 days ago  22 decisions   [View]
```

What happens behind the scenes:

- Dashboard fetches active sessions for all team members under this supervisor's delegation tree
- Each session shows real-time constraint status via WebSocket
- Escalated actions come from delegation chains where the supervisor is the next approver
- The supervisor sees only sessions within their delegation scope (they cannot see sessions from other teams)

**AI UX patterns applied**:

- **Stream of Thought (adapted)**: The team overview is a real-time feed of trust state across the team, not individual AI reasoning traces
- **Controls**: Approve/Deny for escalated actions
- **Verification**: Read-only chain validation status per session

---

### Sub-Flow B2: Session Inspection

**Trigger**: Supervisor clicks "View" on a completed session or clicks a team member's active session.

What the user sees:

```
Session Detail: Alice -- Q1 Analysis

  Duration:     2h 12m
  Status:       Active
  Decisions:    12 recorded
  Audit anchors: 147
  Chain:        Valid (unbroken)

  Delegation Chain
  +-------------------------------------------+
  |  You (genesis authority)                    |
  |    |                                        |
  |    +-- Alice (delegate)                     |
  |         Constraints:                        |
  |           Financial: $50/session            |
  |           Operational: no deploy, no delete |
  |           Data: project directory only      |
  +-------------------------------------------+

  Constraint Utilization
  Financial:     [======----] 62% ($31.00 / $50.00)
  Operational:   OK (0 held, 0 blocked)
  Temporal:      OK (2h 12m / 4h timeout)
  Data Access:   OK (34 reads, 8 writes)
  Communication: OK (0 external calls)

  Decision Timeline
  09:15  Decision: Scope -- "Focus on customer segments A and B"
         Rationale: "C and D are too small for statistical significance"
         Confidence: 90%
         [View full decision]

  09:32  Decision: Methodology -- "Use cohort analysis"
         Rationale: "Cross-sectional would miss the Q3 onboarding effect"
         Confidence: 85%
         Alternatives: 2 considered
         [View full decision]

  10:12  FLAGGED: Token budget at 75%
         Action: Large dataset analysis (continued)

  10:45  Decision: Data -- "Exclude inactive accounts"
         ...

  Action Log (147 anchors)
  [Show full action log]   [Export verification bundle]

  Compliance Report
  [Generate report]
```

What happens behind the scenes:

- Session data loaded from Praxis backend via REST API
- Delegation chain reconstructed from EATP trust lineage
- Decision timeline assembled from Audit Anchors with attached Reasoning Traces
- Chain integrity verified client-side (the dashboard verifies the hash chain to confirm the display is trustworthy)

**Design decisions**:

| Decision | Choice | Rationale |
|---|---|---|
| Decision display depth | Summary by default, expandable to full | Supervisors scan first, then drill into specific decisions |
| Action log visibility | Collapsed by default | 147 individual anchors is too much detail for initial review |
| Chain verification | Run client-side on page load | Supervisor should not need to trust the server's claim that the chain is valid |
| Delegation tree | Visual tree, not text list | Shows authority hierarchy at a glance |

---

### Sub-Flow B3: Approving an Escalated Action

**Trigger**: A team member's action was HELD and the constraint requires supervisor approval.

What the user sees:

```
Approval Required

  Team member:    Bob
  Session:        Code Review (45 min active)
  Action:         Deploy application to staging environment

  Why this was held:
    Bob's constraint envelope says deployment actions require
    supervisor approval. This is a team policy you set.

  Context from Bob:
    "All tests pass (147/147). Alice reviewed the code.
     Staging deployment is needed to test the webhook integration."

  Evidence:
    Test results:   147 passed, 0 failed
    Code review:    Approved by Alice (decision dec_4a2f)
    Files changed:  12 files in src/ directory

  Delegation chain for this action:
    You (genesis) --> Bob (delegate, operational constraints)

  [Approve]   [Deny]   [Approve with Conditions]

  If you approve, this creates a signed record that you
  authorized Bob's deployment to staging.
```

If supervisor clicks "Approve with Conditions":

```
Add conditions to your approval:

  [Only deploy to staging-01, not staging-02  ]
  [Must roll back if health check fails within 5 minutes]

  [Approve with These Conditions]   [Cancel]
```

What happens behind the scenes:

- Approval creates an Audit Anchor signed by the supervisor's key
- The anchor includes: original HELD action, supervisor's decision, conditions (if any), timestamp
- The Reasoning Trace on the anchor records: supervisor identity, approval rationale, conditions
- The HELD action is released and forwarded to the downstream tool
- If conditions are attached, they are added to the Constraint Envelope for this specific action
- Bob's AI assistant receives the approval and can proceed with the deployment
- Bob sees in his terminal: `[Praxis: APPROVED by supervisor -- deploy to staging authorized]`

**Cross-channel approval**: This same approval flow works across channels:

| Channel | How supervisor approves |
|---|---|
| Web Dashboard | Click Approve button (as described above) |
| Mobile Companion (future) | Push notification with approve/deny buttons |
| Email (future) | Link to approval page with one-click approve |

---

### Sub-Flow B4: Delegation Management

**Trigger**: Supervisor wants to change a team member's constraints or add a new team member.

What the user sees:

```
Delegation Management

  Current Delegations

  +----------------------------------------------------+
  | Alice                                               |
  |   Status: Active                                    |
  |   Constraints:                                      |
  |     Financial: $50/session, $200/day                |
  |     Operational: read, write (no deploy, no delete) |
  |     Data: project directory only                    |
  |     Communication: external APIs need approval      |
  |   Active sessions: 1                                |
  |   [Edit Constraints]  [Revoke]                      |
  +----------------------------------------------------+

  +----------------------------------------------------+
  | Bob                                                 |
  |   Status: Active                                    |
  |   Constraints:                                      |
  |     Financial: $100/session, $400/day               |
  |     Operational: read, write, deploy (with approval)|
  |     Data: project + staging environment             |
  |     Communication: external APIs need approval      |
  |   Active sessions: 1                                |
  |   [Edit Constraints]  [Revoke]                      |
  +----------------------------------------------------+

  [+ Add Team Member]
```

If supervisor clicks "Revoke":

```
Revoke Bob's delegation?

  This will immediately:
  - End all of Bob's active sessions
  - Prevent Bob from starting new sessions
  - Revoke any sub-delegations Bob has made

  Bob's existing session data and audit trail will be preserved.

  [Confirm Revocation]   [Cancel]
```

What happens behind the scenes:

- Revocation triggers EATP cascade revocation
- All downstream delegations from Bob are automatically invalidated
- Audit Anchors record each revocation in the chain
- Bob's active MCP connections receive a revocation event
- Bob sees: `[Praxis: Session terminated -- your delegation has been revoked by your supervisor]`

**Constraint tightening rule**: When a supervisor edits a delegate's constraints, they can only tighten relative to their own constraints. The UI enforces this: sliders and toggles that would exceed the supervisor's own authority are disabled with a tooltip: "This exceeds your own authority. Contact your supervisor to request expanded delegation."

---

## Flow C: External Auditor (Browser-Based)

### Persona Profile

External party (ethics board member, journal reviewer, compliance auditor) who needs independent verification. No account, no installation.

**This flow is documented in detail in `03-verification-bundle.md`. Below is the dashboard entry point.**

### Sub-Flow C1: Auditor Portal

**Trigger**: Auditor has received a link or ZIP file containing a verification bundle.

What the user sees (at `verify.praxis.terrene.dev` or by opening `verify.html` from the ZIP):

```
Praxis Verification Portal

  Verify a collaboration session independently.
  No account required. All verification runs in your browser.

  [Upload Bundle (.zip)]

  or drag and drop a .zip file here

  How it works:
    1. Upload the verification bundle you received
    2. Your browser verifies the cryptographic chain
    3. Review the timeline, decisions, and constraints
    4. No data is sent to any server -- everything runs locally
```

**Design decisions**:

- Zero-installation: Everything runs client-side in the browser
- No account required: Auditors should not need to create an account to verify trust evidence
- Privacy: No data leaves the browser (client-side JS does all verification)
- Transparency: The verification algorithm is visible in `algorithm.txt` within the bundle

---

## Approval UX Across Channels

Held actions can be approved through multiple channels. The design must be consistent across all of them.

### Approval Card Anatomy

Every approval request, regardless of channel, contains the same information:

```
1. WHO is requesting     (team member name and role)
2. WHAT they want to do  (action in plain language)
3. WHY it was held       (which constraint triggered)
4. CONTEXT              (the team member's note/reasoning)
5. EVIDENCE             (supporting data if available)
6. CHAIN                (delegation path from approver to requester)
7. ACTIONS              (approve / deny / approve with conditions)
```

### Channel-Specific Adaptations

| Element | Web Dashboard | Mobile (future) | Email (future) |
|---|---|---|---|
| WHO | Full name + session link | Name + session summary | Name in subject line |
| WHAT | Full action description | Abbreviated (tap to expand) | Summary paragraph |
| WHY | Constraint name + explanation | Constraint name | Constraint name |
| CONTEXT | Full text | Abbreviated (tap to expand) | Full text |
| EVIDENCE | Expandable section | Link to dashboard | Link to dashboard |
| CHAIN | Visual delegation tree | Text chain (You -> Name) | Text chain |
| ACTIONS | Three buttons | Two buttons (approve/deny) | Link to approval page |

### Approval Timing

```
t=0        Action HELD
t=0-5s     Notification sent to approver (WebSocket push, mobile push, or email)
t=5s-10m   Amber "waiting" indicator on requester's session
t=10m      Reminder notification to approver
t=30m      Second reminder
t=1h       Warning: "This action has been waiting for 1 hour"
t=4h       Escalation: notification to approver's supervisor (if configured)
NEVER      Auto-approve (per EATP specification)
```

**Design decision -- no auto-approve**: The EATP specification is explicit that HELD actions should not auto-approve after a timeout. The held verdict exists because human judgment is needed. Instead, the system escalates through reminders and eventually notifies the next person up the delegation chain.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Single app, multiple views | Role-based views in one web app | Reduces engineering effort; shared components for common patterns |
| Client-side chain verification | Browser verifies hash chains | Auditor must not need to trust the server |
| No account for auditors | Bundle verification without login | Zero-friction independent verification |
| Constraint editor as visual controls | Toggles, sliders, dropdowns | Non-technical users cannot write YAML constraint files |
| Real-time updates via WebSocket | Live constraint state and held action notifications | Held actions need immediate attention |
| Progressive disclosure per role | Non-tech sees outcomes, supervisor sees chains, auditor sees crypto | Each role needs different depth |
| Delegation tree as visual hierarchy | Tree diagram, not list | Authority relationships are inherently hierarchical |
| Cross-channel approval consistency | Same information in every channel | Approver should have the same context regardless of where they approve |
| No AI chat in dashboard (v1) | Dashboard is for trust management, not for AI conversation | Mixing AI chat and trust management creates confusion about the product's purpose |
