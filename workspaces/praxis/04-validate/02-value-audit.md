# Value Audit

**Date**: 2026-03-15
**Auditor Perspective**: Enterprise CTO evaluating Praxis for adoption
**Method**: Source code review, test suite execution, user flow cross-referencing
**Test Results**: 576 passed, 3 skipped (6.28s)

---

## Overall Assessment

Praxis delivers genuine substance on its core trust propositions. The cryptographic trust chain (Ed25519 genesis, hash-chained audit anchors, JCS-canonical hashing, chain verification) is fully implemented and mathematically sound. The five-dimensional constraint enforcer evaluates all dimensions on every action and returns the most restrictive verdict -- this is not advisory, it is enforcement. The four-level verification gradient (AUTO_APPROVED / FLAGGED / HELD / BLOCKED) is implemented with normative thresholds. Six CO domains are fully configured with domain-specific constraint templates. The CLI works end-to-end for init, session lifecycle, decide, export, and verify. The self-contained verification bundle builder produces ZIP files with client-side Ed25519 verification using SubtleCrypto. 576 tests pass.

However: the product is a strong backend and CLI engine, not yet a complete platform. The web dashboard exists only as API handlers and WebSocket infrastructure -- there is no frontend. The CLI export produces a minimal JSON bundle, not the full ZIP bundle the `BundleBuilder` is capable of. The `praxis status` command shows a Rich table but not the progress-bar constraint gauges described in the user flows. Several user flow details (MCP proxy server, `praxis constraints edit`, inline HELD prompts in CLI) are not yet implemented. The bones are real, but the skin is incomplete.

---

## User Flow Validation

### CLI Practitioner (01-cli-practitioner.md)

| Step                                          | User Flow Description                                                             | Status      | Evidence                                                                                                                                                                                                                                                                                                                                                               |
| --------------------------------------------- | --------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `praxis init --name X --domain Y`             | Creates workspace with genesis, keys, config                                      | **PASS**    | `cli.py` lines 149-189. Creates `.praxis/` directory, generates Ed25519 keypair via `KeyManager`, writes `workspace.json`.                                                                                                                                                                                                                                             |
| `praxis init` output matches spec             | Spec shows detailed output with genesis ID, directory listing, domain constraints | **PARTIAL** | Output is minimal: "Workspace 'X' initialized", domain, template, directory. Does not show genesis record ID, created file listing, default constraints, or "Next steps" guidance.                                                                                                                                                                                     |
| `praxis mcp serve`                            | Start MCP server for AI assistant passthrough                                     | **FAIL**    | No `mcp` subcommand exists in CLI. The `praxis serve` command starts the Nexus API server, not an MCP stdio server. MCP tools are registered on the API app but there is no `praxis mcp serve` stdio transport entry point.                                                                                                                                            |
| `praxis constraints edit`                     | Interactive constraint editor                                                     | **FAIL**    | No `constraints` subcommand exists in CLI. Constraint templates are loaded at session creation but there is no runtime editing command.                                                                                                                                                                                                                                |
| `praxis session start`                        | Start session with context                                                        | **PASS**    | `cli.py` lines 203-230. Creates session via `SessionManager`, generates genesis record, saves to `current-session.json`.                                                                                                                                                                                                                                               |
| `praxis session start --context "..."`        | Spec shows `--context` flag for session description                               | **PARTIAL** | The `start` command does not accept a `--context` argument. The underlying `SessionManager.create_session` does not take a context parameter either.                                                                                                                                                                                                                   |
| `praxis session pause/resume/end`             | Full lifecycle management                                                         | **PASS**    | All three commands implemented (lines 233-313). State machine enforced: ACTIVE -> PAUSED -> ACTIVE -> ARCHIVED.                                                                                                                                                                                                                                                        |
| `praxis session end --summary "..."`          | Spec shows `--summary` flag for session summary                                   | **PARTIAL** | The `end` command does not accept `--summary`. The underlying `end_session()` supports it but CLI does not expose it.                                                                                                                                                                                                                                                  |
| `praxis decide`                               | Record decisions with type, rationale, alternatives, confidence                   | **PARTIAL** | `decide` command exists (lines 357-381) with `--type`, `--decision`, `--rationale`. Missing: `--alternative` (repeatable), `--confidence`, quick capture mode (`praxis decide "text"`).                                                                                                                                                                                |
| `praxis status` with constraint gauges        | Shows progress bars for each constraint dimension                                 | **PARTIAL** | `status` command exists (lines 322-349). Shows a Rich table with session properties and constraint envelope as JSON strings (truncated to 60 chars). Does NOT show progress-bar gauges, utilization percentages, trust state summary, or verification gradient counts.                                                                                                 |
| `praxis export --format bundle`               | Generate self-contained ZIP verification bundle                                   | **PARTIAL** | `export` command exists (lines 389-422) but produces a minimal JSON file, not the full ZIP bundle. The `BundleBuilder` class exists and can produce ZIP bundles with HTML/JS/CSS, but the CLI does not use it.                                                                                                                                                         |
| `praxis verify <bundle>`                      | Verify a bundle's trust chain                                                     | **PARTIAL** | `verify` command exists (lines 430-461). Correctly calls `verify_chain()` when entries and public_keys are present. However, bundles exported by the CLI `export` command do not include entries or public_keys, so verification always falls through to "Bundle has no chain entries to verify". The chain verification code itself is fully implemented and correct. |
| HELD action inline prompt (approve/deny/view) | Terminal-based approval flow for held actions                                     | **FAIL**    | No inline HELD action handling in CLI. The `HeldActionManager` exists in `constraint.py` with full approve/deny logic, but the CLI has no interactive prompt to present held actions and collect user decisions.                                                                                                                                                       |
| Ambient trust indicators                      | AUTO_APPROVED silent, FLAGGED single-line, HELD blocking prompt, BLOCKED error    | **FAIL**    | No ambient trust indicator system in CLI. The constraint enforcer runs and logs results, but there is no mechanism to surface these to the terminal during AI tool use.                                                                                                                                                                                                |

### Web Dashboard (02-web-dashboard.md)

| Step                                        | User Flow Description                                          | Status      | Evidence                                                                                                                                                                                                                        |
| ------------------------------------------- | -------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Practitioner dashboard with active sessions | Session list, constraint gauges, activity feed                 | **FAIL**    | No web frontend exists. The Nexus API exposes REST endpoints for all operations, but there is no HTML/JS dashboard application.                                                                                                 |
| Session creation wizard                     | Guided setup with domain templates, visual toggles             | **FAIL**    | No frontend. The `create_session` API handler exists and works correctly.                                                                                                                                                       |
| Real-time constraint gauge updates          | WebSocket-driven live updates of constraint utilization        | **PARTIAL** | `EventBroadcaster` exists in `websocket.py` with subscribe/unsubscribe/broadcast. Event types defined for session state changes, constraint updates, held actions, deliberation records. But no frontend consumes these events. |
| Approval card (WHO/WHAT/WHY/CONTEXT)        | Visual approval flow for held actions                          | **FAIL**    | The `HeldAction` dataclass and `HeldActionManager` capture all needed data. The `approve_handler` and `deny_handler` exist. No frontend renders the approval card.                                                              |
| Supervisor team overview                    | Shows all team sessions, delegation trees, escalated approvals | **FAIL**    | No team/supervisor concepts in the current implementation. The `DelegationRecord` and delegation chain infrastructure exist, but there are no user management, role-based views, or team-scoped queries.                        |
| Approval queue with WebSocket updates       | Real-time escalation notifications                             | **FAIL**    | Backend infrastructure exists (held actions + WebSocket broadcaster), no frontend.                                                                                                                                              |
| Visual constraint editor                    | Slider/toggle interface for constraint modification            | **FAIL**    | No frontend. Constraint tightening logic is fully implemented in `SessionManager.update_constraints()`.                                                                                                                         |

### Verification Bundle (03-verification-bundle.md)

| Step                                            | User Flow Description                                                | Status      | Evidence                                                                                                                                                                                                                                                                                                      |
| ----------------------------------------------- | -------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Verification portal accepts ZIP uploads         | Browser-based upload and verify                                      | **FAIL**    | No verification portal web application exists. The `verify.html` template in a bundle works standalone but there is no hosted portal at a URL.                                                                                                                                                                |
| Client-side Ed25519 verification (SubtleCrypto) | Browser verifies chain without server                                | **PASS**    | `verifier.js` implements full JCS canonicalization, SHA-256 hashing via `crypto.subtle.digest`, Ed25519 signature verification via `crypto.subtle.verify`, parent-hash chain linkage. Includes Ed25519 support detection with fallback messaging.                                                             |
| Timeline viewer shows all events                | Decisions, observations, constraints in chronological order          | **PASS**    | `viewer.js` implements `renderTimeline()` for deliberation records (decisions with alternatives, observations, escalations with context), `renderConstraints()` with verdict aggregation and per-event log, `renderChainDetail()` showing hash/parent for each entry.                                         |
| Chain integrity display                         | Visual chain verification status with break detection                | **PASS**    | `viewer.js` `renderIntegrityResults()` shows CHAIN VALID / CHAIN BROKEN status, total and verified counts, per-break details with position and reason, Ed25519 support warning.                                                                                                                               |
| Auditor downloads report                        | Export verification report                                           | **FAIL**    | No download/export button in `viewer.js`. The `AuditReportGenerator` exists in `report.py` and produces both HTML and JSON reports, but this is server-side only. The bundle viewer has no client-side report generation.                                                                                     |
| Works WITHOUT an account                        | Zero-installation, no login required                                 | **PASS**    | The `verify.html` bundle is fully self-contained. Loads `bundle-data.js` as a `<script>` tag (avoiding CORS), runs verification client-side. No server calls. `serve.py` fallback included for file:// CORS issues.                                                                                           |
| `algorithm.txt` for manual verification         | Step-by-step verification procedure                                  | **PASS**    | `templates/algorithm.txt` documents the 6-step verification algorithm: parse, verify genesis, verify delegations, verify anchor chain, verify constraint compliance, report.                                                                                                                                  |
| Bundle contains all needed files                | bundle.json, verify.html, algorithm.txt, public-key.pem, schema.json | **PARTIAL** | `BundleBuilder.build()` produces: `index.html`, `data/bundle-data.js`, `verify/verifier.js`, `verify/viewer.js`, `style/styles.css`, `algorithm.txt`, `serve.py`. Missing: standalone `public-key.pem` file (key is embedded in bundle data), `schema.json`, `README.txt`. Close but not exact match to spec. |

---

## Value Proposition Verification

| Claimed Capability                                                    | Status          | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cryptographic proof of human authorization (Ed25519 trust chains)** | **IMPLEMENTED** | `KeyManager` generates/stores Ed25519 keypairs (PEM, mode 600). `create_genesis()` builds signed genesis records with JCS canonical payload and SHA-256 hash. `AuditChain` creates signed, hash-chained audit anchors. `create_delegation()` with constraint tightening enforcement. `verify_chain()` does full recomputation (hash, signature, parent link). Client-side `verifier.js` replicates this in the browser. |
| **5-dimensional constraint enforcement**                              | **IMPLEMENTED** | `ConstraintEnforcer` evaluates all 5 dimensions on every call: financial (budget utilization), operational (allowed/blocked action lists), temporal (elapsed vs. max duration), data_access (path allowlisting/blocklisting), communication (channel allowlisting/blocklisting). Returns the most restrictive verdict. `gradient.py` provides a parallel pure-function evaluator.                                       |
| **Verification gradient (AUTO_APPROVED / FLAGGED / HELD / BLOCKED)**  | **IMPLEMENTED** | `GradientLevel` enum with 4 levels. Threshold mapping: <70% AUTO_APPROVED, 70-89% FLAGGED, 90-99% HELD, >=100% BLOCKED. Comment explicitly marks thresholds as normative and not configurable. Both `ConstraintEnforcer` and `gradient.py` implement identical thresholds.                                                                                                                                              |
| **Deliberation capture with hash chains**                             | **IMPLEMENTED** | `DeliberationEngine` records decisions, observations, and escalations. Each record is JCS-canonicalized and SHA-256 hashed. `parent_record_id` links to previous record's `reasoning_hash`. When `key_manager` is available, records are Ed25519 signed with anchor IDs.                                                                                                                                                |
| **Self-contained verification bundles**                               | **IMPLEMENTED** | `BundleBuilder` produces ZIP files with `index.html`, embedded JS verification (SubtleCrypto Ed25519), JCS canonicalization, timeline viewer, constraint viewer, chain detail view. Pre-export chain verification runs before building. `serve.py` fallback for file:// CORS. Dark/light mode CSS. Print stylesheet.                                                                                                    |
| **6 CO domains**                                                      | **IMPLEMENTED** | All 6 domain directories exist with valid `domain.yml` files: COC (strict/moderate/permissive), COE (year1/year2/year3), COG (advisory/deliberative/executive), COR (exploratory/formal/sensitive), COComp (internal/external), COF (analysis/advisory/trading). Each has all 5 constraint dimensions, workflow phases, and capture rules. `DomainLoader` validates against JSON Schema.                                |
| **MCP server tools**                                                  | **PARTIAL**     | 5 MCP tools registered via Nexus: `trust_check`, `trust_record`, `trust_escalate`, `trust_envelope`, `trust_status`. These are accessible as both REST endpoints and MCP tools through Nexus. However, there is no `praxis mcp serve` stdio transport for local AI assistant integration (the primary use case described in the user flows).                                                                            |

---

## Domain Application Coverage

| Domain                  | Templates                         | All 5 Dimensions | Phases                                                                     | Capture Rules                                     | Status   |
| ----------------------- | --------------------------------- | ---------------- | -------------------------------------------------------------------------- | ------------------------------------------------- | -------- |
| **COC (Codegen)**       | strict, moderate, permissive      | Yes              | 5 phases (analyze, plan, implement, validate, codify)                      | auto_capture, decision_types, observation_targets | **PASS** |
| **COE (Education)**     | year1, year2, year3               | Yes              | 4 phases (research, draft, review, revise)                                 | auto_capture, decision_types, observation_targets | **PASS** |
| **COG (Governance)**    | advisory, deliberative, executive | Yes              | 5 phases (agenda_setting, analysis, deliberation, decision, documentation) | auto_capture, decision_types, observation_targets | **PASS** |
| **COR (Research)**      | exploratory, formal, sensitive    | Yes              | 6 phases (literature_review through write_up)                              | auto_capture, decision_types, observation_targets | **PASS** |
| **COComp (Compliance)** | internal, external                | Yes              | 5 phases (scoping through submission)                                      | auto_capture, decision_types, observation_targets | **PASS** |
| **COF (Finance)**       | analysis, advisory, trading       | Yes              | 5 phases (research through documentation)                                  | auto_capture, decision_types, observation_targets | **PASS** |

All 6 domains fully configured and passing validation.

---

## Gaps Found

### Critical Gaps (block the value story)

1. **No MCP stdio server** -- The primary use case (AI assistant operating through Praxis trust layer) requires a `praxis mcp serve` command that starts an MCP server on stdio transport. This is the single most important missing piece. The MCP tools are defined but only accessible through the Nexus HTTP API, not through the stdio protocol that Claude Code, Aider, and other tools use. Without this, the "trust as the medium" promise is theoretical.

2. **No web dashboard frontend** -- The entire web dashboard user flow (practitioner dashboard, session wizard, supervisor overview, approval queue) has no frontend implementation. The backend API is comprehensive (19+ handlers, WebSocket infrastructure), but no HTML/JS/CSS application renders it. This blocks 3 of the 5 user personas described in the user flows.

3. **CLI export does not produce real verification bundles** -- The `praxis export` CLI command produces a minimal JSON file with session metadata only (no trust chain entries, no public keys, no HTML verification). The `BundleBuilder` class can produce full ZIP bundles, but the CLI does not call it. This means the entire export-verify-audit chain is broken at the CLI level even though all the components exist.

### High-Priority Gaps (degrade the demo significantly)

4. **CLI `praxis status` lacks constraint gauges** -- The user flow spec shows Rich progress-bar gauges (`[========--] 82%`) for each constraint dimension. The current implementation shows a Rich table with JSON strings. The `ConstraintEnforcer.get_status()` method returns all the data needed (utilization ratios, gradient levels per dimension), but the CLI does not render it as visual gauges.

5. **CLI `praxis decide` lacks full options** -- Missing `--alternative` (repeatable flag), `--confidence` flag, and the quick capture mode (`praxis decide "Use regression analysis"`). The user flow describes three capture modes; only the explicit CLI mode is partially implemented.

6. **CLI `praxis session start/end` lacks `--context` and `--summary`** -- The user flow shows `praxis session start --context "Analyzing Q1 data"` and `praxis session end --summary "Completed analysis"`. Neither flag exists. The underlying engine supports metadata but the CLI does not pass it through.

7. **No inline HELD action prompting in CLI** -- When a constraint evaluation returns HELD, the user flow describes an interactive terminal prompt with approve/deny/view options. This entire interaction pattern is missing. The `HeldActionManager` has the logic; the CLI has no prompt.

8. **Domain templates not wired into CLI session creation** -- `praxis init --domain research` would need to load the COR domain template. The CLI `init` stores the domain name in workspace config, but `praxis session start` loads constraint templates from `CONSTRAINT_TEMPLATES` (hardcoded strict/moderate/permissive in `session.py`), not from the domain YAML files. The `DomainLoader` exists and can load domain-specific templates, but this is not connected to the session creation path.

### Medium-Priority Gaps (polish issues)

9. **No `praxis reinit` command** -- The user flow error handling specifies this command for re-initialization.

10. **No `praxis audit` or `praxis chain` commands** -- The progressive disclosure spec describes `praxis audit` for full audit trail and `praxis chain` for complete trust chain display.

11. **Session end output is minimal** -- The user flow shows a detailed end summary (duration, decisions, anchors, files changed, attestation). The CLI prints only "Session ended".

12. **Verification portal not hosted** -- The spec references `verify.praxis.terrene.dev` as a hosted verification portal. This would be a separate deployment concern but is worth noting.

13. **Bundle missing `README.txt`, `public-key.pem`, `schema.json`** -- The spec lists these as bundle contents. The public key is embedded in the JS data file instead of as a standalone PEM. The algorithm.txt is present but README and schema are not.

---

## Strengths

### 1. Cryptographic Integrity Is Real

The trust chain is not a sketch or a data model -- it is a mathematically sound implementation. Ed25519 keys are generated and stored with proper file permissions (600). JCS canonicalization ensures deterministic hashing across platforms. SHA-256 content hashes link anchors in a parent-hash chain. Signatures are verified using the `cryptography` library. The `verify_chain()` function enumerates all breaks rather than stopping at the first one (good for forensics). The client-side `verifier.js` faithfully reproduces this algorithm using the Web Crypto API. This is not theater; this is cryptography.

### 2. Constraint Enforcement Is Not Advisory

The five-dimensional constraint enforcer does not suggest -- it evaluates and returns verdicts. The `evaluate()` method checks all five dimensions and returns the MOST RESTRICTIVE verdict. The gradient thresholds are hardcoded and explicitly marked as normative ("MUST NOT be made configurable"). The `HeldActionManager` correctly tracks held actions with full lifecycle (create, approve, deny). The constraint tightening invariant is enforced on both `SessionManager.update_constraints()` and `create_delegation()`. This is enforcement, not logging.

### 3. Six Domains Are Substantive

Each of the six domains has been designed with genuine domain expertise. COE year-based progressive autonomy, COG deliberative governance with constitutional compliance, COF with the hard rule that AI advises but humans authorize capital deployment, COComp with mandatory human sign-off on submissions, COR with sensitive-research constraints limiting data access to `/research/` only. These are not copy-paste templates with different labels -- they reflect real domain requirements.

### 4. The Architecture Is Correctly Layered

Core logic (session state machine, constraint enforcement, deliberation capture, trust chain operations) is cleanly separated from API handlers, CLI, and persistence. Handlers are plain functions that take service instances as parameters -- no framework coupling. The same handler serves REST, MCP, and CLI. This makes the codebase genuinely testable (576 passing tests in 6 seconds) and extensible.

### 5. Self-Contained Verification Bundles Are Honest

The verification bundle design is honest about its limitations. The spec includes a "What this does NOT prove" section, the viewer includes a "limitations" caveat, and the assessment template separates mathematical facts (auto-checked) from human judgment (manual). This is unusual and valuable -- most products oversell their cryptographic guarantees.

### 6. Test Coverage Is Comprehensive

576 tests across unit, integration, conformance, and e2e test directories. Tests cover CLI invocation, session lifecycle, trust chain creation and verification, constraint enforcement across all five dimensions, delegation with constraint tightening, bundle building, domain loading and validation, API handlers, key management, and more. The test infrastructure is solid and the pass rate is 100%.

---

## Recommendations

### Before First Public Demo (Critical)

1. **Wire `BundleBuilder` to CLI `export` command.** The `BundleBuilder` exists and works. The CLI needs to call it instead of dumping a minimal JSON file. This connects the export-verify chain end to end.

2. **Add `praxis mcp serve` with stdio transport.** This is the entire value proposition for CLI practitioners. Without it, the AI assistant cannot operate through the trust layer. The MCP tools are already defined -- they just need a stdio entry point.

3. **Upgrade `praxis status` to show visual constraint gauges.** Use Rich progress bars (`rich.progress.Progress` or `rich.bar_chart.BarChart`) to render utilization. The data is already computed by `ConstraintEnforcer.get_status()`.

4. **Add `--context` to `session start`, `--summary` to `session end`, `--alternative`/`--confidence` to `decide`.** These are the fields that make the deliberation capture meaningful. Without them, the decision records are sparse.

### Before Beta Release (High)

5. **Connect domain YAML templates to session creation.** When `praxis session start` runs, it should look up the workspace domain and template from the `DomainLoader` instead of using the hardcoded `CONSTRAINT_TEMPLATES`.

6. **Implement inline HELD action prompting in CLI.** When the constraint enforcer returns HELD, the CLI should present an interactive prompt with approve/deny/details options.

7. **Build the web dashboard.** The API surface is ready. A minimal dashboard with session list, constraint gauges, and approval queue would activate 3 additional user personas.

### Before GA Release (Medium)

8. Add `praxis audit`, `praxis chain`, and `praxis status --verbose` for progressive disclosure.
9. Add `praxis reinit --force` and `praxis constraints edit`.
10. Enrich the bundle to include `README.txt`, standalone `public-key.pem`, and `schema.json`.
11. Add hosted verification portal.
12. Add `praxis export --format markdown --output report.md` using `AuditReportGenerator`.

---

## Severity Table

| Issue                                                      | Severity | Impact                                                  | Fix Category |
| ---------------------------------------------------------- | -------- | ------------------------------------------------------- | ------------ |
| No `praxis mcp serve` stdio entry point                    | CRITICAL | Primary use case (AI through trust layer) is inoperable | CLI/MCP      |
| CLI export produces minimal JSON, not full bundle          | CRITICAL | Export-verify chain is broken at CLI level              | CLI          |
| No web dashboard frontend                                  | CRITICAL | 3 user personas have no interface                       | FRONTEND     |
| `praxis status` lacks visual constraint gauges             | HIGH     | Key differentiator (visual trust state) not visible     | CLI          |
| Domain YAML templates not wired to session creation        | HIGH     | 6 carefully designed domains are unused at runtime      | FLOW         |
| `praxis decide` missing alternatives/confidence/quick mode | HIGH     | Deliberation capture is limited                         | CLI          |
| `praxis session start/end` missing context/summary flags   | HIGH     | Session metadata is impoverished                        | CLI          |
| No inline HELD prompting in CLI                            | HIGH     | Approval flow does not exist for CLI users              | CLI          |
| No `praxis constraints edit` command                       | MEDIUM   | Constraint customization impossible from CLI            | CLI          |
| No `praxis audit`/`praxis chain` commands                  | MEDIUM   | Progressive disclosure not available                    | CLI          |
| Session end output is minimal                              | MEDIUM   | User gets no session summary at end                     | CLI          |
| Bundle missing README/public-key.pem/schema.json           | MEDIUM   | Not fully conformant with spec                          | EXPORT       |
| No hosted verification portal                              | LOW      | Independent verification requires bundle files          | DEPLOYMENT   |

---

## Bottom Line

Praxis has genuine cryptographic substance. The trust chain, constraint enforcement, verification gradient, and deliberation capture are not stubs or sketches -- they are complete, tested, mathematically sound implementations. The six CO domain configurations reflect real domain expertise. The architecture is clean and well-tested. The self-contained verification bundle with client-side Ed25519 verification is a real differentiator.

What is missing is the user-facing surface that would let someone actually experience this substance. The CLI commands exist but lack the polish and completeness described in the user flows (no gauges, no inline prompts, no full bundle export, no MCP stdio server). The web dashboard has a complete backend but no frontend. The domain templates are not wired to session creation.

The highest-impact fix is connecting the existing `BundleBuilder` to the CLI `export` command and adding `praxis mcp serve` with stdio transport. These two changes would complete the core value chain: practitioner works with AI -> trust layer enforces constraints -> deliberation is captured -> bundle is exported -> auditor verifies independently. Every piece of this chain is implemented; the wiring between the CLI and the underlying engines is what needs to be completed.

This is a product with real bones and no skin. The bones are excellent. Add the skin.
