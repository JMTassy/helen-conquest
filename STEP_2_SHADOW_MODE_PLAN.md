# STEP 2: Shadow Mode Implementation & Testing Plan

**Status:** Ready to Execute
**Objective:** Deploy dispatch routing in non-blocking shadow mode
**Success Criteria:** 100+ runs with 0 crashes, 0 nondeterminism, determinism verified
**Estimated Duration:** 4-6 hours
**Go/No-Go Decision Point:** After shadow summary report

---

## 1. Overview

Shadow mode is a **non-blocking, logging-only** deployment of HELEN_DISPATCH_LAYER_V1.

**What happens:**
- Every input is routed deterministically
- Every routing decision is logged (append-only)
- Zero behavior change to system
- Zero mutations to governed state
- Statistics collected for analysis

**What doesn't happen:**
- No enforcement (DEFER/REJECT still allow fallback)
- No state mutation
- No authority decisions
- No blocking of requests

---

## 2. Artifacts

### Code Modules
- `helen_dispatch_v1_schemas.py` — Data structures (already created)
- `helen_dispatch_v1_router.py` — Routing logic (already created)
- `helen_dispatch_shadow_mode_v1.py` — Shadow mode runner (NEW)
- `test_helen_dispatch_v1.py` — CI tests (already created)

### Configuration
- Shadow ledger path: `.shadow_ledger_<session_id>.ndjson`
- Summary report path: `.shadow_report_<session_id>.json`
- Store refs: {context://shadow, ledger://shadow, transcript://shadow}

---

## 3. Execution Plan

### Phase 1: Bootstrap (15 min)

```python
from helen_dispatch_shadow_mode_v1 import DispatchShadowMode

shadow = DispatchShadowMode(
    session_id="shadow_test_20260404_001",
    manifest_ref="helen_manifest_v1",
    shadow_ledger_path=".shadow_ledger.ndjson"
)
```

**Verify:**
- ✅ Shadow mode initializes without crash
- ✅ Session ID is valid
- ✅ Manifest ref is present
- ✅ Store refs are correct

### Phase 2: Input Runs (30-60 min)

**Test input distribution** (should cover all InputTypes):

| Input Type | Count | Example |
|---|---|---|
| USER_QUERY | 25 | `{"text": "..."}` |
| SLASH_COMMAND | 5 | `{"slash_command": "/status"}` |
| CLAIM_OBJECT | 15 | `{"claim_id": "...", "text": "..."}` |
| CLAIM_BUNDLE | 10 | `{"claims": [...]}` |
| CLAIM_EXTRACTION_REQUEST | 10 | `{"claim_extraction": true}` |
| ARTIFACT_REQUEST | 8 | `{"artifact_type": "report"}` |
| AUDIT_REQUEST | 8 | `{"audit_type": "knowledge_health"}` |
| SOURCE_INGEST | 5 | `{"source_id": "...", "content": "..."}` |
| UNRESOLVED_POINTER | 8 | `{"unresolved_pointers": [...]}` |
| PROMOTION_REQUEST | 5 | `{"promote_to": "canonical"}` |
| PIPELINE_SUBSTITUTION_REQUEST | 2 | `{"pipeline_substitution": true}` |
| TEMPLE_OBSERVATION | 10 | `{"temple": true, "hypothesis": "..."}` |
| MEMORY_REQUEST | 4 | `{"memory_op": "read"}` |
| AUDIT_REQUEST | 2 | `{"audit_type": "..."}` |
| **TOTAL** | **113** | **Good baseline for 100+ runs** |

**For each input:**
```python
result = shadow.process_input_shadow(input_obj, input_id=f"test_{i}")
shadow.log_shadow_run(result)
print(f"Run {i}: {result['status']} → {result['receipt']['primary_route']}")
```

**What to expect:**
- ✅ All runs complete without crash
- ✅ All receipts have receipt_hash
- ✅ All reason_codes are frozen (from DISPATCH_REASON_CODES)
- ✅ No nondeterminism detected

### Phase 3: Determinism Verification (15 min)

**Repeat sample inputs 5 times each, verify hash consistency:**

```python
# Test determinism on subset
sample_inputs = [
    {"text": "What is X?"},
    {"claim_extraction": true},
    {"temple": true},
]

for sample in sample_inputs:
    is_deterministic = shadow.verify_determinism_sample(sample, runs=5)
    print(f"Determinism check on {sample}: {'✅ PASS' if is_deterministic else '❌ FAIL'}")
```

**Success criteria:**
- ✅ Same input → same route 5/5 times
- ✅ Same route → same receipt_hash 5/5 times

### Phase 4: Summary Generation (5 min)

```python
summary = shadow.generate_summary()
report_path = shadow.write_summary_report()
print(f"Report: {report_path}")
```

**Output format:**
```json
{
  "total_runs": 113,
  "successful_runs": 113,
  "crash_count": 0,
  "nondeterminism_count": 0,
  "invalid_receipt_count": 0,
  "route_distribution": {
    "AGENT": 45,
    "SKILL": 35,
    "KERNEL": 12,
    "DEFER": 8,
    "TEMPLE": 10,
    "REJECT": 3
  },
  "input_type_distribution": {
    "USER_QUERY": 25,
    "CLAIM_OBJECT": 15,
    ...
  },
  "unresolved_pointer_count": 8,
  "promotion_attempts_count": 5,
  "temple_observations_count": 10,
  "determinism_verified": true,
  "determinism_sample_size": 5,
  "timestamp_generated": "2026-04-04T..."
}
```

### Phase 5: Go/No-Go Decision (5 min)

```python
go, reason, summary = shadow.go_no_go_decision()
print(reason)
```

**Acceptance criteria (ALL must pass):**

| Criterion | Threshold | Why |
|---|---|---|
| min_runs_100 | ≥ 100 runs | Statistical significance |
| crash_rate_zero | 0 crashes | Stability |
| nondeterminism_zero | 0 cases | Determinism proven |
| determinism_verified | True | Same-input hash match |
| route_distribution_reasonable | All major routes tested | Coverage |

---

## 4. Success Metrics

### Must Have (Go criteria)
- ✅ **100+ runs completed**
- ✅ **0 crashes**
- ✅ **0 nondeterminism detected**
- ✅ **Determinism verified (5-run sample)**
- ✅ **All receipts valid (have receipt_hash)**
- ✅ **Route distribution sensible** (no single route > 80%)

### Should Have (Quality checks)
- ✅ KERNEL routes for promotion/substitution only
- ✅ DEFER routes for unresolved pointers
- ✅ TEMPLE routes isolated (no canonical effects)
- ✅ All reason_codes from frozen set
- ✅ No ad hoc strings in reason_codes

### Nice to Have (Performance)
- ⚠️ Avg routing latency < 10ms
- ⚠️ No memory leaks (simple check)
- ⚠️ Shadow ledger < 5MB for 100 runs

---

## 5. Failure Modes & Recovery

### If crash detected
**Action:** Stop, investigate, fix, restart
1. Check error message in result
2. Debug specific input that crashed
3. Fix in router or schemas
4. Delete shadow ledger
5. Restart from bootstrap

### If nondeterminism detected
**Action:** Investigate and fix
1. Identify which input causes inconsistency
2. Check for:
   - Timestamp/random components in receipt (BAD)
   - Different route for same input (BAD)
   - Missing reason_codes on second run (BAD)
3. Fix root cause
4. Restart determinism verification

### If route distribution seems wrong
**Action:** Review and confirm it's OK
1. Check if distribution matches expectations
2. Confirm no single route dominates (> 80%)
3. Confirm edge routes exist (REJECT, DEFER, TEMPLE)
4. If OK, proceed

---

## 6. Transition to STEP 3

### When to proceed
✅ All go criteria met → **IMMEDIATE** go to STEP 3

### When to hold
❌ Any go criterion failed → **FIX** → **RESTART shadow mode**

### Handoff to STEP 3
1. Copy `.shadow_report_<session_id>.json` to `shadow_results/`
2. Mark STEP 2 ✅ complete
3. Begin STEP 3: CI test enforcement

---

## 7. Monitoring Dashboard (Optional)

If needed, create simple ASCII dashboard:

```
HELEN DISPATCH SHADOW MODE — LIVE MONITOR
========================================

Session: shadow_test_20260404_001
Started: 2026-04-04T10:00:00Z
Elapsed: 00:15:32

RUNS COMPLETED: 87 / 100 target
├─ Successful: 87
├─ Crashed: 0
└─ Nondeterministic: 0

ROUTE DISTRIBUTION:
├─ AGENT:   38 (43%)  ████████
├─ SKILL:   31 (36%)  ███████
├─ KERNEL:  10 (11%)  ██
├─ DEFER:    5 (6%)   █
├─ TEMPLE:   3 (3%)   █
└─ REJECT:   0 (0%)

DETERMINISM:
  ✅ Verified on 3 sample inputs (15 runs)

STATUS: ON TRACK
  Next target: 100 runs
  Est. completion: 00:18:00
```

---

## 8. Final Output

After STEP 2 complete:

**Files created/updated:**
1. `.shadow_ledger_<session_id>.ndjson` — All routing receipts (append-only)
2. `.shadow_report_<session_id>.json` — Summary statistics
3. `STEP_2_SHADOW_MODE_RESULTS.md` — Human-readable summary

**Example summary:**
```markdown
# STEP 2 Shadow Mode Results

**Session:** shadow_test_20260404_001
**Date:** 2026-04-04
**Status:** ✅ GO FOR STEP 3

## Summary
- Total runs: 113
- Successful: 113
- Crashes: 0
- Nondeterminism: 0
- Determinism verified: Yes

## Route Distribution
- AGENT: 45 (40%)
- SKILL: 35 (31%)
- KERNEL: 12 (11%)
- DEFER: 8 (7%)
- TEMPLE: 10 (9%)
- REJECT: 3 (3%)

## Edge Cases
- Unresolved pointers routed to DEFER: 8 ✅
- Promotions routed to KERNEL: 5 ✅
- Temple observations isolated: 10 ✅

## Determinism Proof
Sample inputs verified 5 runs each:
- INPUT_1 (user query): 5/5 identical hashes ✅
- INPUT_2 (claim extraction): 5/5 identical hashes ✅
- INPUT_3 (temple observation): 5/5 identical hashes ✅

## Verdict
All acceptance criteria met. Ready for STEP 3 enforcement.

---
Generated: 2026-04-04T10:30:00Z
```

---

## Next Steps (STEP 3)

After shadow mode proves deterministic and crash-free:

1. **STEP 3:** Enable enforcement (DEFER/REJECT actually block)
2. **STEP 3 tests:** CI suite validation
3. **STEP 4:** Pressure signal integration
4. **STEP 5:** Affect translation
5. **STEP 6:** Knowledge audit patch
6. **STEP 7-10:** Full rollout

---

**Ready to execute STEP 2. Awaiting your confirmation to proceed with shadow runs.**
