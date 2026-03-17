# E2E Round 2 — CLI Lifecycle + Security Fixes Verification

**Date**: 2026-03-16
**Executor**: e2e-playwright agent (Sonnet 4.6)
**Working directory**: `/tmp/praxis-e2e-test2/`
**Praxis install**: `/Users/esperie/repos/terrene/praxis/src/praxis`

---

## Test 1: Full CLI Lifecycle

### Step 1: Init workspace
**Command**: `PRAXIS_DEV_MODE=true praxis init --name "E2E Test" --domain coc --template moderate`
**Expected**: `.praxis/` directory created, `workspace.json` has correct name/domain/template
**Actual**:
```
Workspace 'E2E Test' initialized
  Domain: coc
  Template: moderate
  Directory: /private/tmp/praxis-e2e-test2/.praxis
```
`workspace.json` confirmed: `{"id": "...", "name": "E2E Test", "domain": "coc", "constraint_template": "moderate", "key_id": "workspace"}`
`.praxis/keys/` directory created with `workspace.key` (mode 600) and `workspace.pub`.
**Status**: PASS

---

### Step 2: Start session
**Command**: `praxis session start --context "Testing full lifecycle"`
**Expected**: `current-session.json` created with `state: "active"` and a valid genesis record
**Actual**:
```
Session started
  Session ID: e943fce4-e9c1-4634-95f0-7ba24519d17c
  Domain: coc
  State: active
  Context: Testing full lifecycle
```
`current-session.json` confirmed:
- `state: "active"`
- `genesis_id`: SHA-256 hex hash (64 chars)
- `genesis_chain_entry`: full payload with all 9 fields (`type`, `version`, `session_id`, `authority_id`, `namespace`, `domain`, `constraints`, `signer_key_id`, `created_at`), plus `content_hash`, `signature`, `signer_key_id`, `parent_hash: null`
- `constraint_envelope`: all 5 dimensions populated from `moderate` template

**Note**: `genesis_chain_entry` is a new field added in this round to fix the bundle hash mismatch (see bugs section).
**Status**: PASS

---

### Step 3: Record decisions
**Command 3a**: `praxis decide --type scope --decision "Focus on user auth" --rationale "Critical path" --alternative "Skip auth" --alternative "Use OAuth only" --confidence 0.9`
**Expected**: Decision recorded with hash, 2 alternatives, 90% confidence
**Actual**:
```
Decision recorded
  Record ID: 47a23440-95ab-48e7-8b3d-5cb8ba9fd0c6
  Hash: 761ffe26833ea59f...
  Alternatives: 2 considered
  Confidence: 90%
```
**Status**: PASS

**Command 3b**: `praxis decide --type architecture --decision "Use JWT tokens" --rationale "Stateless, scalable" --confidence 0.85`
**Expected**: Second decision recorded with chained hash
**Actual**:
```
Decision recorded
  Record ID: e0a51509-991e-40c2-b82e-31af2695d632
  Hash: 01cfc820a856be16...
  Confidence: 85%
```
Deliberation file `.praxis/deliberation-e943fce4-....json` confirmed on disk with 2 records.
**Status**: PASS

---

### Step 4: Check status with gauges
**Command**: `praxis status`
**Expected**: Visual gauge bars for all 5 constraint dimensions, session info panel
**Actual**:
```
╭─────────────────── Session ────────────────────╮
│ E2E Test                                        │
│   ID: e943fce4-e9c1...  Domain: coc  State: ACTIVE
│   Started: 2026-03-15T16:...                    │
╰─────────────────────────────────────────────────╯

Constraint Gauges
  Financial       ░░░░░░░░░░░░░░░░░░░░   0%  $0 / $100
  Operational     ████████████████████  OK
  Temporal        ░░░░░░░░░░░░░░░░░░░░   0%  min0 / min120
  Data Access     ████████████████████  OK
  Communication   ████████████████████  OK
```
All 5 constraint dimensions rendered. Green gauges at 0% utilization as expected.
**Status**: PASS

---

### Step 5: Export verification bundle (ZIP)
**Command**: `praxis export --format bundle`
**Expected**: ZIP file created containing `index.html`, `verifier.js`, `viewer.js`, `styles.css`, `algorithm.txt`, `bundle-data.js`; no hash mismatch warning; `chain_valid: true`
**Actual**:
```
Verification bundle exported to /private/tmp/praxis-e2e-test2/praxis-e943fce4-bundle.zip
  Open in browser or run: praxis verify /private/tmp/.../praxis-e943fce4-bundle.zip
```
ZIP contents verified: `['index.html', 'data/bundle-data.js', 'verify/verifier.js', 'verify/viewer.js', 'style/styles.css', 'algorithm.txt', 'serve.py']`
`bundle-data.js` confirmed:
- `chain_valid: true` (no hash mismatch)
- `chain entries: 1` (genesis)
- `deliberation records: 2` (both decisions persisted)

**Status**: PASS (was FAIL before fix — see bugs section)

---

### Step 6: Verify the bundle
**Command**: `praxis verify praxis-e943fce4-bundle.zip`
**Expected**: Reads ZIP, parses bundle-data.js, reports chain status
**Actual**:
```
Verifying ZIP bundle: praxis-e943fce4-bundle.zip
  Session: e943fce4-e9c1-4634-95f0-7ba24519d17c
  Chain entries: 1
  Pre-export chain valid: True
Chain verified: 1/1 entries valid
```
**Status**: PASS (was FAIL before fix — see bugs section)

---

### Step 7: JSON export
**Command**: `praxis export --format json`
**Expected**: JSON file created with session metadata
**Actual**:
```
JSON exported to /private/tmp/praxis-e2e-test2/praxis-e943fce4.json
```
JSON contents confirmed: `session_id`, `workspace`, `domain`, `state`, `constraint_envelope`, `genesis_id`, `created_at` all present.
**Status**: PASS

---

### Step 8: End session
**Command**: `praxis session end --summary "E2E test complete"`
**Expected**: Session state changes to `"archived"`
**Actual**:
```
Session ended
```
`current-session.json` state confirmed: `"archived"`
**Status**: PASS

---

### Step 9: List domains
**Command**: `praxis domain list`
**Expected**: Table showing all available CO domains
**Actual**: Table with 6 domains — `coc`, `cocomp`, `coe`, `cof`, `cog`, `cor`
**Status**: PASS

---

### Step 10: Validate a domain
**Command**: `praxis domain validate coc`
**Expected**: Passes validation with no errors
**Actual**:
```
Domain 'coc' is valid
```
**Status**: PASS

---

## Test 2: Security Fixes Verification

### C1: Path traversal rejection
**Command**: `km.generate_key('../../etc/passwd')`
**Expected**: `ValueError` raised with clear message
**Actual**:
```
PASS: key_id contains forbidden characters: '../../etc/passwd'. Key IDs must not contain '/', '\', '..', or null bytes.
```
**Status**: PASS

---

### C2: NaN bypass rejection
**Command**: `_utilization_to_level(float('nan'))` and `_utilization_to_level(float('inf'))`
**Expected**: Both return `GradientLevel.BLOCKED`
**Actual**:
```
NaN -> blocked
PASS: NaN correctly blocked
PASS: Inf correctly blocked
```
**Status**: PASS

---

### C3: Frozen dataclasses
**Command**: Attempt to mutate `GenesisRecord.content_hash`
**Expected**: `AttributeError` raised (frozen dataclass)
**Actual**:
```
PASS: GenesisRecord is frozen
```
**Status**: PASS

---

## Test 3: Full Test Suite

**Command**: `PRAXIS_DEV_MODE=true python -m pytest tests/ -v --tb=short`
**Expected**: All tests pass
**Actual**:
```
======================== 576 passed, 3 skipped in 4.09s ========================
```
3 skipped tests are intentionally skipped — they require a running Praxis server (`@pytest.mark.skip(reason="E2E tests require running Praxis server")`).
**Status**: PASS (576/576, 3 expected skips)

---

## Bugs Found and Fixed

### Bug 1 (FIXED): `praxis verify` crashes on ZIP bundles

**Root cause**: The `verify` command called `path.read_text()` on all inputs, which raises `UnicodeDecodeError` on binary ZIP files.

**Fix**: The `verify` command now detects ZIP files by extension and magic bytes (`zipfile.is_zipfile`). For ZIP inputs it opens the archive, reads `data/bundle-data.js`, strips the `window.PRAXIS_BUNDLE = ...;` JS wrapper, and parses the JSON. It then runs the trust chain verifier against the embedded chain entries and public keys.

**Files changed**: `/Users/esperie/repos/terrene/praxis/src/praxis/cli.py` — `verify` command

---

### Bug 2 (FIXED): Bundle `chain_valid: False` — genesis payload hash mismatch

**Root cause**: When building the trust chain for the bundle, the `export` command reconstructed the genesis entry using a truncated payload `{"type": "genesis", "session_id": ...}`. The `genesis_id` stored in the session file is the SHA-256 hash of the full 9-field genesis payload (including `version`, `authority_id`, `namespace`, `domain`, `constraints`, `signer_key_id`, `created_at`). The mismatch between the truncated payload and the stored hash caused `chain_valid: False` and the pre-export warning.

**Fix**:
1. `SessionManager.create_session` now builds and stores a `genesis_chain_entry` dict containing the complete `payload`, `content_hash`, `signature`, `signer_key_id`, and `parent_hash: null`.
2. The `session start` CLI command persists `genesis_chain_entry` to `current-session.json`.
3. The `export` command reads `genesis_chain_entry` directly from the session file instead of reconstructing it.

**Files changed**:
- `/Users/esperie/repos/terrene/praxis/src/praxis/core/session.py` — `create_session`
- `/Users/esperie/repos/terrene/praxis/src/praxis/cli.py` — `session start`, `export`

---

### Bug 3 (FIXED): Bundle contains 0 deliberation records

**Root cause**: `DeliberationEngine` stores records in memory (`self._records: list`). The `decide` command created an engine, recorded the decision, then discarded the instance. When `export` ran, it created a new engine instance with an empty list, so `engine.get_timeline()` returned no records.

**Fix**:
1. The `decide` command loads existing records from `.praxis/deliberation-<session_id>.json` before recording, so the hash chain remains continuous across CLI invocations.
2. After recording, it writes all records back to disk.
3. The `export` command reads from `.praxis/deliberation-<session_id>.json` directly instead of instantiating a new engine.

**Files changed**: `/Users/esperie/repos/terrene/praxis/src/praxis/cli.py` — `decide`, `export`

---

## Summary

| Test | Steps | Status |
|------|-------|--------|
| CLI lifecycle (10 steps) | init, session start/end, decide x2, status, export bundle, verify ZIP, export JSON, domain list, domain validate | 10/10 PASS |
| Security fixes (3 checks) | Path traversal, NaN bypass, frozen genesis | 3/3 PASS |
| Full test suite | 579 collected | 576 PASS, 3 SKIP (expected), 0 FAIL |

3 bugs were discovered and fixed during this round:
- `praxis verify` crashing on ZIP bundles (binary decode error)
- Bundle `chain_valid: False` due to truncated genesis payload reconstruction
- Bundle containing 0 deliberation records due to in-memory-only storage

All three fixes are backward-compatible and did not break any existing tests.
