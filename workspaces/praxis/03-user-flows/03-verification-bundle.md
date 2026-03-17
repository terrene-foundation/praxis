# User Flows: Verification Bundle & External Audit (P1)

**Date**: 2026-03-15
**Status**: Design
**Personas**: External Auditor (primary), Supervisor (secondary), CLI Practitioner (generation)

---

## Overview

The Verification Bundle is the centerpiece of Praxis's trust proposition: a self-contained, zero-installation package that allows anyone to independently verify the integrity of a human-AI collaboration session.

The bundle answers five questions:
1. **WHO** was the human authority? (Genesis Record)
2. **WHAT** were the constraints? (Constraint Envelope)
3. **WHEN** did actions occur? (Audit Anchor timestamps)
4. **HOW** were decisions made? (Reasoning Traces)
5. **WAS IT TAMPERED WITH?** (Hash chain verification)

---

## Design Principles

### Zero-Installation Verification

The auditor opens a ZIP file in their browser. No `pip install`, no Docker, no account creation. The HTML file contains embedded JavaScript that performs all cryptographic verification client-side.

### No Server Required

Verification runs entirely in the browser. No data is sent to any server. The auditor can be offline, air-gapped, or behind a firewall. The bundle is self-contained.

### Verifiable by Multiple Methods

Three verification paths, from simplest to most rigorous:

| Path | Audience | Method |
|---|---|---|
| Visual (verify.html) | Non-technical auditor | Open in browser, read the green/red banner |
| Algorithmic (algorithm.txt) | Technical auditor | Follow step-by-step verification procedure manually |
| Programmatic (bundle.json) | System integrator | Feed to any EATP-conformant verification tool |

### Honest About Limitations

The bundle can prove:
- Chain integrity (mathematical -- no tampering since creation)
- Temporal ordering (anchors are in sequence)
- Constraint compliance (no violations recorded)
- Decision existence (decisions were recorded with these timestamps)

The bundle CANNOT prove:
- That the chain was created during actual work (vs. fabricated after)
- That all decisions were recorded (completeness)
- That reasoning traces reflect genuine reasoning (vs. post-hoc rationalization)
- That the human actually reviewed AI output

The bundle viewer must be honest about these limitations. The Caveat pattern is mandatory.

---

## Flow 5: External Audit

### Trigger

An external auditor (ethics board member, journal reviewer, compliance officer) receives a verification bundle and needs to assess trust compliance.

### What the Auditor Receives

A ZIP file (`praxis-bundle-ses_XXXX.zip`) containing:

```
praxis-bundle-ses_9b2c4e1f/
  bundle.json              Complete chain data (machine-readable)
  verify.html              Self-contained verification page (HTML + JS)
  README.txt               Plain-text bundle description
  algorithm.txt            Step-by-step manual verification procedure
  public-key.pem           Genesis authority's public key
  schema.json              JSON Schema for bundle.json validation
```

### Step-by-Step: Non-Technical Auditor

**Step 1: Open the verification page**

The auditor double-clicks `verify.html` or opens it in any modern browser (Chrome, Firefox, Safari, Edge).

What the auditor sees on page load:

```
+------------------------------------------------------------------+
|                                                                    |
|  Praxis Verification Bundle                                       |
|                                                                    |
|  Project:   Q1 Financial Analysis                                 |
|  Author:    Sarah Chen                                             |
|  Duration:  4h 23m across 3 sessions                               |
|  Exported:  2026-03-15 at 14:30 UTC                               |
|                                                                    |
|  +--------------------------------------------------------------+ |
|  |  Verifying chain integrity...                                 | |
|  |  [====================] 100%                                  | |
|  |                                                                | |
|  |  CHAIN INTEGRITY VERIFIED                                     | |
|  |                                                                | |
|  |  147 audit anchors verified                                   | |
|  |  0 breaks in hash chain                                       | |
|  |  Genesis record signature: valid                              | |
|  |  Temporal ordering: monotonic (no timestamp reversals)        | |
|  |  Constraint violations: 0                                     | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  What this means:                                                  |
|  The audit trail has not been tampered with since it was created.  |
|  All records are in the correct order, and no anchors are missing  |
|  from the chain. The author's identity is cryptographically        |
|  confirmed.                                                        |
|                                                                    |
|  What this does NOT prove:                                         |
|  This verification confirms integrity, not completeness. The       |
|  author may have made decisions that were not recorded. The        |
|  reasoning traces reflect what the author declared, not            |
|  necessarily what they were thinking. See the Limitations section  |
|  below for full details.                                           |
|                                                                    |
+------------------------------------------------------------------+
```

What happens behind the scenes:

- On page load, embedded JavaScript immediately begins verification
- The progress bar shows real-time verification progress (not fake -- it is verifying anchors)
- Verification steps:
  1. Parse `bundle.json` (embedded in the HTML or loaded from ZIP)
  2. Verify Genesis Record self-signature (Ed25519)
  3. Walk the anchor chain from genesis to final anchor
  4. For each anchor: verify `previous_anchor_hash` matches computed hash of previous anchor
  5. Verify all signatures in the delegation chain
  6. Check temporal monotonicity (each timestamp >= previous)
  7. If Reasoning Traces present: verify `reasoning_trace_hash` matches content
  8. Count constraint violations (should be 0 for compliant sessions)
- Total verification time: typically 1-3 seconds for chains under 500 anchors

**If verification fails**:

```
+--------------------------------------------------------------+
|                                                                |
|  CHAIN INTEGRITY FAILURE                                       |
|                                                                |
|  The audit trail has been modified since creation.             |
|                                                                |
|  Issue found at anchor #73 (anc_f4a2b1c3):                    |
|    Expected hash: sha256:7f83b165...                           |
|    Computed hash: sha256:a3c9e412...                           |
|                                                                |
|  This means the data at or before anchor #73 was modified     |
|  after the chain was created. The records after this point     |
|  cannot be trusted.                                            |
|                                                                |
|  Recommendation: Contact the author and request a new bundle  |
|  generated from the original Praxis workspace.                |
|                                                                |
+--------------------------------------------------------------+
```

---

**Step 2: Review the project summary**

What the auditor sees (scrolling down from the verification banner):

```
Project Summary

  Author:          Sarah Chen
  Authority:       Genesis gen_7f3a8b2c (self-signed)
  Domain:          Research (financial analysis)
  Duration:        4 hours 23 minutes
  Sessions:        3

  Session 1: "Initial data exploration"
    Duration: 1h 12m | Decisions: 4 | Anchors: 42
  Session 2: "Year-over-year comparison analysis"
    Duration: 2h 05m | Decisions: 6 | Anchors: 73
  Session 3: "Report drafting and finalization"
    Duration: 1h 06m | Decisions: 2 | Anchors: 32
```

---

**Step 3: Review the constraint envelope**

What the auditor sees:

```
Constraint Envelope

  These rules governed what the AI could do during this project.

  Financial
    Session budget:        $50.00 per session
    Daily budget:          $200.00
    Approval threshold:    $25.00
    Actual spending:       $41.00 (Session 1: $12, Session 2: $18, Session 3: $11)
    Status:                Within bounds

  Operational
    Auto-approved actions: Read files, search, list directories
    Held actions:          Write files, create files
    Blocked actions:       Execute commands, delete files
    Held actions invoked:  3 (2 approved by author, 1 denied by author)
    Blocked actions invoked: 1 (blocked, no override)
    Status:                Within bounds

  Temporal
    Session timeout:       4 hours per session
    Operating hours:       Unrestricted
    Longest session:       2h 05m
    Status:                Within bounds

  Data Access
    Read scope:            Project directory
    Write scope:           output/ and drafts/ subdirectories
    Blocked paths:         ~/.ssh/, ~/.aws/, /etc/
    Out-of-scope attempts: 0
    Status:                Within bounds

  Communication
    External APIs:         Held (requires approval)
    External API calls:    1 (approved by author)
    Email/webhooks:        Blocked
    Status:                Within bounds
```

**Design decision**: The constraint section shows both what was defined and what actually happened. This is the core of constraint compliance verification: the auditor can see that constraints existed AND that they were respected.

---

**Step 4: Review the decision timeline**

What the auditor sees:

```
Decision Timeline

  All decisions are shown in chronological order. Each decision
  includes what was decided, why, and what alternatives were
  considered.

  Session 1: Initial data exploration
  ---
  09:15  SESSION START
         Context: "Exploring Q1 survey data structure and quality"

  09:17  DECISION: Scope
         "Focus on Q1 only -- exclude Q2-Q4 data"
         Rationale: "Q2 data not yet audited by finance team"
         Alternatives: Include all quarters (rejected: Q2 unaudited)
         Confidence: 95%
         Recorded by: Author (human)

  09:23  FLAGGED: Token budget at 80%
         Action: Large dataset analysis (continued, not blocked)

  09:45  DECISION: Methodology
         "Use year-over-year comparison instead of quarter-over-quarter"
         Rationale: "Q4 had anomalous data due to system migration.
                     YoY gives cleaner baseline."
         Alternatives:
           - QoQ with Q4 excluded (rejected: reduces sample size)
           - Rolling 4-quarter average (rejected: smooths signal)
         Confidence: 85%
         Recorded by: Author (human)

  10:12  HELD: External API call
         Action: POST to analytics dashboard API
         Constraint: Communication (external APIs require approval)
         Resolution: APPROVED by author
         Author's note: "Pushing summary stats to shared dashboard
                         for team visibility"

  10:27  SESSION END
         Summary: "Data exploration complete. YoY analysis chosen."
         Files changed: 2 (output/exploration-notes.md, data/q1-clean.csv)

  Session 2: Year-over-year comparison analysis
  ---
  [... continues ...]
```

**Design decisions for the timeline**:

| Decision | Choice | Rationale |
|---|---|---|
| Chronological order | Always (no sorting/filtering) | Auditors need temporal sequence to assess the collaboration flow |
| Decision source labeling | "Recorded by: Author (human)" or "Recorded by: AI assistant" | Auditor needs to distinguish human-initiated from AI-initiated records |
| HELD resolution shown inline | Part of the timeline, not a separate section | Shows the full context of when the hold occurred and how it was resolved |
| Confidence displayed | Always shown for each decision | Part of the audit record; helps assess the author's self-awareness |
| Flagged actions shown | Yes, inline with timeline | Shows constraint boundary awareness during the session |
| Session boundaries marked | Clear visual separation between sessions | Each session has its own context and constraint snapshot |

---

**Step 5: Review the verification details (expandable)**

For technical auditors who want to see the cryptographic details:

```
Verification Details

  Genesis Record
    Authority ID:    sarah.chen@example.edu
    Public Key:      Ed25519 (see public-key.pem)
    Created:         2026-03-15T08:30:00Z
    Signature:       Valid (self-signed, verified)

  Delegation Chain
    Depth: 0 (author is genesis authority)
    No sub-delegations in this bundle

  Anchor Chain
    Total anchors:   147
    First anchor:    anc_a1b2c3d4 (session 1 start)
    Last anchor:     anc_z9y8x7w6 (session 3 end)
    Chain algorithm: SHA-256 with parent hash linking
    All hashes:      Verified
    All signatures:  Verified (Ed25519)

  Temporal Analysis
    First timestamp: 2026-03-15T09:15:00Z
    Last timestamp:  2026-03-15T16:38:00Z
    Ordering:        Strictly monotonic (no reversals)
    Gaps:            None detected
    Average anchor interval: 108 seconds

  Reasoning Trace Verification
    Decisions with reasoning traces: 12/12
    Reasoning trace hashes: All verified
    Reasoning signatures: All verified

  [Download raw chain data (JSON)]
  [View algorithm.txt]
```

---

**Step 6: Produce assessment (optional)**

For domain-specific assessments, the bundle viewer can include assessment templates:

```
Assessment Template (Research Domain)

  Based on your review, assess the following:

  1. Chain Integrity
     [x] Hash chain is unbroken
     [x] All signatures are valid
     [x] Temporal ordering is correct

  2. Constraint Compliance
     [x] All defined constraints were respected
     [x] Held actions were resolved by authorized parties
     [x] No blocked actions were overridden

  3. Decision Quality (your judgment)
     [ ] Decisions show evidence of genuine deliberation
     [ ] Alternatives were meaningfully considered
     [ ] Confidence levels are realistic
     [ ] Reasoning traces are substantive (not perfunctory)

  4. Completeness Assessment (your judgment)
     [ ] Decision density is plausible for the work described
     [ ] Session durations are plausible
     [ ] No suspicious gaps in the timeline

  5. Overall Assessment
     [ ] Acceptable
     [ ] Acceptable with notes
     [ ] Requires further investigation
     [ ] Unacceptable

  Notes:
  [                                               ]

  [Generate Assessment Report (PDF)]
```

**Design decision**: Items 1-2 are auto-checked based on verification results (mathematical facts). Items 3-5 require human judgment -- the system provides the evidence but the auditor makes the call. This is honest about what cryptography can prove and what requires human assessment.

---

### Step-by-Step: Technical Auditor

**Alternative path**: The technical auditor ignores `verify.html` and works directly with the data.

**Step 1: Open `algorithm.txt`**

```
Verification Algorithm for Praxis Bundles
Version: 1.0

This document describes how to verify a Praxis verification bundle
without using the provided verify.html tool. You can implement this
algorithm in any programming language or verify by hand.

STEP 1: Parse bundle.json
  The bundle is a JSON file with the following top-level structure:
  {
    "version": "1.0",
    "genesis": { ... },
    "delegations": [ ... ],
    "constraints": { ... },
    "anchors": [ ... ],
    "decisions": [ ... ],
    "sessions": [ ... ]
  }

STEP 2: Verify Genesis Record
  a. Extract the public key from genesis.public_key
  b. Compute the signing payload:
     - Concatenate: authority_id + created + policy_uri + reasoning_trace_hash
     - Apply JCS (RFC 8785) canonical serialization
  c. Verify genesis.signature against the payload using Ed25519
  d. If verification fails: CHAIN INVALID (genesis signature failed)

STEP 3: Verify Delegation Chain
  For each delegation record in delegations[]:
    a. Verify that delegator has authority to delegate
       (trace chain_ref back to genesis)
    b. Verify that scope is a subset of delegator's scope
       (constraints can only tighten)
    c. Compute signing payload including reasoning_trace_hash
    d. Verify signature using delegator's key
    e. If reasoning_trace is present:
       - Compute SHA-256 of JCS-canonicalized reasoning_trace
       - Verify it matches reasoning_trace_hash
       - Verify reasoning_signature
    f. If any check fails: CHAIN INVALID at this delegation

STEP 4: Verify Anchor Chain
  For each anchor in anchors[] (in order):
    a. If first anchor: verify parent_anchor_hash is null
    b. If not first anchor: compute SHA-256 of previous anchor's
       canonical JSON serialization. Verify it matches this
       anchor's parent_anchor_hash.
    c. Verify anchor signature
    d. Verify timestamp >= previous anchor's timestamp (monotonic)
    e. If reasoning_trace is present:
       - Compute SHA-256 of JCS-canonicalized reasoning_trace
       - Verify it matches reasoning_trace_hash
       - Verify reasoning_signature
    f. If any check fails: CHAIN INVALID at anchor #N

STEP 5: Verify Constraint Compliance
  For each anchor:
    a. Check that the action described is within the constraint
       envelope active at that point in the chain
    b. If verdict is HELD: verify that a subsequent anchor
       records an APPROVED or DENIED resolution
    c. If verdict is BLOCKED: verify no execution anchor follows

STEP 6: Report
  If all steps pass: CHAIN INTEGRITY VERIFIED
  If any step fails: report the specific failure point
```

**Step 2: Implement verification independently**

The technical auditor can:
- Write their own verification script in Python, JavaScript, or any language
- Use the EATP SDK's `verify_chain()` function directly
- Use any third-party EATP-conformant verification tool
- Verify entirely by hand (for the most rigorous audit)

The bundle is designed to be verifiable by ANY implementation of the EATP specification, not just by Praxis tools.

---

## Bundle Generation Flow

### From CLI

```bash
praxis export --session ses_9b2c4e1f --format bundle --output report.zip
```

### From Web Dashboard

Supervisor or practitioner clicks "Export Verification Bundle" on a session page.

### What Happens During Generation

1. **Chain validation**: Before generating the bundle, Praxis verifies the entire chain internally. If the chain is broken, the export fails with an explanation.

2. **Confidentiality filtering**: Reasoning Traces with confidentiality levels above the bundle's target audience are redacted. The `reasoning_trace_hash` is preserved (proving reasoning existed), but the content is replaced with `[REDACTED: confidential]`. This follows the EATP privacy model.

3. **Public key inclusion**: The genesis authority's public key is included so the auditor can verify signatures without needing to contact the author.

4. **HTML generation**: The `verify.html` file is generated with:
   - Embedded `bundle.json` (for single-file verification)
   - Embedded JavaScript verification library (no CDN dependencies)
   - Responsive layout (works on desktop and mobile browsers)
   - Print stylesheet (for paper-based compliance filing)
   - Accessibility: WCAG AA compliance, screen reader support, keyboard navigation

5. **Integrity seal**: The bundle itself has a SHA-256 hash of its contents recorded in `verify.html`. If any file in the ZIP is modified after generation, the seal check fails on page load.

---

## Edge Cases

| Situation | Handling |
|---|---|
| Bundle for session with chain break | Export fails. User sees: "Chain integrity failure detected at anchor #N. Cannot generate verification bundle for a broken chain. Run `praxis verify` for details." |
| Bundle for session with HELD action still pending | Export proceeds with a warning. HELD action appears in timeline as "PENDING (not yet resolved)." Auditor sees this as an open item. |
| Bundle contains reasoning traces with mixed confidentiality | Each trace handled per its confidentiality level. PUBLIC traces included in full. RESTRICTED traces included for direct participants, redacted for others. CONFIDENTIAL and above: hash-only. |
| Very large session (10,000+ anchors) | Bundle is generated but verify.html may be slow to load. A progress indicator shows verification progress. Recommendation: use programmatic verification for large sessions. |
| Multiple sessions in one bundle | Each session is a separate section in the timeline. Sessions share the same genesis and delegation chain but have independent anchor sequences. |
| Auditor's browser has JavaScript disabled | `verify.html` shows a `<noscript>` message: "JavaScript is required for client-side verification. Alternatively, use algorithm.txt for manual verification or bundle.json with an EATP-conformant tool." |
| Bundle opened on mobile device | Responsive layout adapts. Verification runs normally. Timeline is scrollable. Assessment template works on mobile. |
| Auditor wants to compare two bundles | Not supported in v1. Recommendation: open each in a separate browser tab. Future: diff view comparing two bundles side-by-side. |

---

## What the Auditor Can Conclude

This table must be displayed in every verification bundle. Honesty about limitations is mandatory.

| Conclusion | Basis | Confidence Level |
|---|---|---|
| "The chain has not been tampered with since creation" | Hash chain and Ed25519 signature verification | HIGH (mathematical proof) |
| "These records were created in this sequence" | Anchor ordering with parent hash linking | HIGH (mathematical proof) |
| "These constraints were defined and respected" | Constraint envelope in chain + no violation anchors | HIGH (for defined constraints) |
| "File X had this hash at time Y" | File hash in anchor at timestamp | HIGH (mathematical proof) |
| "The author declared these decisions with this reasoning" | Decision records with reasoning traces | MEDIUM (self-reported) |
| "The chain was created during actual work" | Temporal plausibility analysis | LOW (circumstantial) |
| "All relevant decisions were recorded" | Cannot be determined from chain data alone | CANNOT DETERMINE |
| "The reasoning traces reflect genuine reasoning" | Cannot be determined from chain data alone | CANNOT DETERMINE |
| "The author actually supervised the AI" | Decision density + temporal patterns (indirect) | LOW (behavioral inference) |

### Strengthening Confidence

The bundle's confidence can be strengthened by cross-referencing with external evidence:

| External Evidence | What It Adds |
|---|---|
| Git commit history | Timestamps corroborate anchor timestamps |
| Institutional access logs | Confirms the author was present during claimed sessions |
| Submission timestamps | Bundle creation aligns with submission deadline |
| Network logs | MCP connection timestamps corroborate session activity |
| Multiple independent bundles | Same decisions appear across bundles from different team members |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Self-contained ZIP | Single file contains everything needed for verification | Zero-dependency distribution |
| Client-side verification | All crypto runs in browser | Auditor does not trust any server |
| Three verification paths | HTML (easy), algorithm.txt (manual), bundle.json (programmatic) | Different auditor expertise levels |
| Honest limitations section | Prominently displayed in every bundle | Trust is built by honesty about what can and cannot be proved |
| Assessment template included | Domain-specific checklist for auditor judgment | Separates mathematical proof from human judgment |
| No CDN dependencies in HTML | All JavaScript embedded | Works offline, air-gapped, behind firewalls |
| Confidentiality filtering | Reasoning traces redacted per EATP levels | Privacy protection even in verification bundles |
| Print stylesheet | Bundle can be printed for paper-based compliance | Some compliance processes require paper records |
| WCAG AA accessibility | Screen reader support, keyboard navigation | Auditors may have accessibility needs |
| Integrity seal on ZIP | Hash of bundle contents checked on page load | Detects post-generation modification of bundle files |
