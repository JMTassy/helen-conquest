# UNIFIED_CI_REPLAY_HARNESS_V1

## Purpose

A single CI harness that verifies both kernel and adaptation layers under one rule:

**same manifest in ⇒ same bytes out**

This harness operationalizes the replay-determinism and hash-correctness requirements already frozen in HELEN_KERNEL_DOCTRINE_V1:
- Manifests are complete and sufficient to replay decisions
- Hashes are recomputable exactly
- Identical logical inputs yield identical input/output hashes
- Cross-environment determinism is guaranteed

**Status:** READY FOR IMPLEMENTATION
**Prerequisite:** HELEN_KERNEL_DOCTRINE_V1 (locked)

---

## I. Scope

### Targets

1. **wul-core** (Weil Unification Layer v3)
   - Normalization engine
   - Token reduction
   - Glyph encoding

2. **nsps** (Namespace + Structural Pipeline System)
   - Claim graph construction
   - Support/refutation analysis
   - Obligation extraction

3. **kernel** (HELEN OS Kernel)
   - Manifest ingestion
   - Deterministic reduction
   - Receipt generation
   - Ledger append

### Endpoints to Test

| Endpoint | Purpose | Input | Output |
|----------|---------|-------|--------|
| `/api/run_wul_core` | Normalization | manifest | normalized_artifact |
| `/api/run_nsps` | Structure validation | artifact | claim_graph |
| `/api/run_kernel` | Deterministic reduction | manifest | decision + receipt |
| `/api/verify_artifact` | Hash verification | artifact | verification_result |

### Artifacts to Verify

1. **Manifest JSON** — input contract
2. **Output JSON** — decision payload
3. **Declared artifact blobs** — referenced data
4. **Receipt SHA256** — proof of execution
5. **Kernel state hash** — state reproducibility

---

## II. Pass/Fail Rule

A build is **PASS** iff all of the following hold:

### Check 1: Schema Validity
Request, response, manifest, and artifacts must validate against frozen schemas.

```
artifact.schema_version ∈ FROZEN_SCHEMAS
schema_validator(artifact, schema_version) → VALID
```

**Failure:** Any schema validation error → FAIL

---

### Check 2: Receipt Correctness
Receipt hash must recompute exactly from manifest.

```
receipt_sha256 = sha256_jcs(manifest_without_receipt)
```

**Failure:** Mismatch between computed and declared receipt → FAIL

---

### Check 3: Replay Identity
Re-running the same manifest produces byte-identical outputs.

**Test:** Run manifest M three times in same environment
```
output_1 = run(M)
output_2 = run(M)
output_3 = run(M)

assert output_1.payload == output_2.payload == output_3.payload
assert output_1.sha256 == output_2.sha256 == output_3.sha256
assert output_1.receipt == output_2.receipt == output_3.receipt
```

**Failure:** Any byte difference across runs → FAIL

---

### Check 4: No Hidden State
Changing environment variables must not affect outputs.

**Hidden state indicators:**
- Wall clock time
- Hostname or machine identity
- Filesystem iteration order
- Temp path
- Locale
- Process order
- Unordered collection iteration

**Test:** Run manifest M with mutations
```
M_default = manifest as provided
M_clock_off = manifest with system_time_ns + 1000
M_hostname_diff = manifest on different machine
M_locale_diff = manifest with LC_ALL=C

# All must produce identical outputs
assert run(M_default).output == run(M_clock_off).output
assert run(M_default).output == run(M_hostname_diff).output
assert run(M_default).output == run(M_locale_diff).output
```

**Failure:** Environment mutation changes output → FAIL

---

### Check 5: Invariant Preservation

Kernel invariants must remain satisfied across all transitions.

**Invariants to verify:**
1. NO_RECEIPT = NO_SHIP (missing receipt → decision must be NO_SHIP)
2. Blocking obligations prevent SHIP
3. Superteams cannot emit verdicts
4. HER does not mutate kernel state
5. Receipt hashes recompute exactly

**Test:** For each manifest M and each invariant I
```
decision = run(M).decision
state_before = kernel_state before M
state_after = kernel_state after M

assert check_invariant_I(decision, state_before, state_after) == TRUE
```

**Failure:** Any invariant violation → FAIL

---

## III. Test Matrix

Five test classes cover all critical paths.

### T1: Golden Replay

**Objective:** Verify determinism within single environment

**Procedure:**
```
for manifest in GOLDEN_MANIFESTS:
    hashes = []
    for run in 1..3:
        output = execute(manifest)
        hashes.append(sha256_jcs(output))

    assert hashes[0] == hashes[1] == hashes[2]
```

**Test cases:**
- 5 golden manifests from each layer (wul, nsps, kernel)
- 15 total golden cases

**Pass criteria:**
- All 15 manifests produce bit-identical output across 3 runs
- Receipt hashes match exactly

**Expected duration:** ~30 seconds

---

### T2: Cross-Environment Replay

**Objective:** Verify determinism across different execution environments

**Procedure:**
```
manifest = single frozen manifest
env_1 = Linux A image (docker)
env_2 = Linux B image (docker)

output_1 = execute(manifest, env_1)
output_2 = execute(manifest, env_2)

assert output_1 == output_2 (byte-identical)
```

**Test cases:**
- 1 manifest × 2 environments = 2 executions
- Ubuntu 22.04 LTS vs Ubuntu 24.04 LTS

**Pass criteria:**
- Outputs byte-identical across both OS versions
- No locale/timezone/kernel version dependency

**Expected duration:** ~60 seconds

---

### T3: Seed Fuzzing

**Objective:** Verify determinism under random seed variation

**Procedure:**
```
fixed_corpus = frozen test manifests (100 items)
seed_count = 1000

for seed in range(seed_count):
    for manifest in fixed_corpus:
        m_seeded = manifest with deterministic_seed = seed
        output = execute(m_seeded)
        hashes.append(sha256_jcs(output))

# All hashes for same manifest/seed pair must be identical
for manifest in fixed_corpus:
    for seed in range(seed_count):
        assert consistent_hash(manifest, seed)
```

**Test cases:**
- 100 fixed manifests
- 1000 seeds
- 100,000 total executions

**Pass criteria:**
- Zero nondeterministic drift
- All outputs reproducible from seed

**Expected duration:** ~5 minutes

---

### T4: Artifact Diff (Canonical Only)

**Objective:** Verify hash equality using canonical JSON comparison

**Procedure:**
```
artifact_1 = first execution output
artifact_2 = second execution output

canon_1 = canonical_json(artifact_1)
canon_2 = canonical_json(artifact_2)

assert canon_1 == canon_2 (byte-for-byte)
assert sha256(canon_1) == sha256(canon_2)
```

**Test cases:**
- All 15 golden manifests
- All 100 seed-fuzz manifests
- Total: ~115 artifact comparisons

**Pass criteria:**
- Zero semantic "close enough" layer
- Only byte-exact equality counts

**Expected duration:** ~30 seconds

---

### T5: Adversarial Perturbation

**Objective:** Verify deterministic rejection under adversarial input

**Procedure:**
```
adversarial_cases = malformed manifests (30 items)

for case in adversarial_cases:
    result = execute(case)

    # Must be deterministic (pass or fail consistently)
    assert result.status in (ACCEPTED, REJECTED)
    assert result.status == execute(case).status  # Runs 2 and 3 match
```

**Adversarial cases for wul/nsps:**
- Namespace collision attacks
- Max-node flood (graph explosion)
- Malformed token sequences
- Invalid UTF-8 encoding
- Circular obligation references

**Adversarial cases for kernel:**
- Missing required fields
- Schema version mismatches
- Doctrine hash disagreement
- Receipt forgery attempts
- State mutation attempts

**Pass criteria:**
- All adversarial cases produce deterministic outcomes
- Never unstable/flaky behavior
- Always either ACCEPTED or REJECTED (never intermediate)

**Expected duration:** ~60 seconds

---

## IV. Output Contract

The CI harness emits **JSON only**. No other output formats.

### CI Output Schema

```json
{
  "suite": "unified_ci_replay_v1",
  "status": "pass | fail",
  "run_id": "RUN-2026-03-12-001",
  "timestamp_ns": 1700000000000000000,
  "vm": "wul_core | nsps | kernel",
  "manifest_sha256": "sha256:...",
  "summary": {
    "tests_run": 115,
    "tests_passed": 115,
    "tests_failed": 0,
    "duration_ms": 125000
  },
  "runs": [
    {
      "test_name": "T1_golden_replay",
      "status": "pass",
      "cases": 15,
      "duration_ms": 30000,
      "details": {
        "manifest_hash": "sha256:...",
        "run_1_hash": "sha256:...",
        "run_2_hash": "sha256:...",
        "run_3_hash": "sha256:...",
        "match": true
      }
    },
    {
      "test_name": "T2_cross_environment",
      "status": "pass",
      "cases": 1,
      "duration_ms": 60000,
      "details": {
        "manifest_hash": "sha256:...",
        "env_1_hash": "sha256:...",
        "env_2_hash": "sha256:...",
        "match": true
      }
    },
    {
      "test_name": "T3_seed_fuzzing",
      "status": "pass",
      "cases": 100000,
      "duration_ms": 300000,
      "drift_count": 0
    },
    {
      "test_name": "T4_artifact_diff",
      "status": "pass",
      "cases": 115,
      "duration_ms": 30000
    },
    {
      "test_name": "T5_adversarial_perturbation",
      "status": "pass",
      "cases": 30,
      "duration_ms": 60000,
      "flaky_cases": 0
    }
  ],
  "failures": []
}
```

### Failure Output Example

```json
{
  "suite": "unified_ci_replay_v1",
  "status": "fail",
  "run_id": "RUN-2026-03-12-002",
  "failures": [
    {
      "test_name": "T1_golden_replay",
      "manifest": "GOLDEN-005",
      "run_1_hash": "sha256:abc...",
      "run_2_hash": "sha256:def...",
      "run_3_hash": "sha256:abc...",
      "error": "Non-deterministic output: run 2 differs from runs 1 and 3",
      "severity": "CRITICAL"
    }
  ]
}
```

---

## V. Zero-Drift Rule

For frozen version **v1**, the rule is absolute:

### Allowed Changes
- **None**

### Regression Definition
Any byte drift in:
- Output payloads
- Artifact hashes
- Receipts
- Kernel state hashes

= **REGRESSION** (build FAIL)

### Recovery Path
Only explicit version increment allowed:
```
v1 → v2 (new version number)
     (with explicit changelog documenting drift)
```

**Law:** "Byte drift requires version bump and changelog."

---

## VI. Test Execution Environment

### Hardware Requirements

**Minimum:**
- 4 CPU cores
- 8 GB RAM
- SSD storage (1 GB for test artifacts)

**Recommended:**
- 8 CPU cores
- 16 GB RAM
- Fast SSD (NVMe)

### Software Requirements

**Docker images:**
- ubuntu:22.04
- ubuntu:24.04

**Runtime:**
- Python 3.9+
- jsonschema library
- pytest or similar test runner

### Isolation Requirements

Each test run must:
- Use clean container (no leftover state)
- Isolate network (no external calls)
- Disable hyperthreading (determinism)
- Fix CPU governor to performance mode
- No concurrent processes during test

---

## VII. CI Integration

### GitHub Actions Example

```yaml
name: HELEN OS CI - Unified Replay

on: [push, pull_request]

jobs:
  replay_test:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v3

      - name: Run Unified CI Replay Harness V1
        run: |
          python unified_ci_replay_harness_v1.py \
            --suite all \
            --output ci_results.json

      - name: Verify Results
        run: |
          python -c "
          import json
          with open('ci_results.json') as f:
            results = json.load(f)
          assert results['status'] == 'pass', f\"CI FAILED: {results['failures']}\"
          print(f\"✅ All {results['summary']['tests_run']} tests passed\")
          "

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: ci_results
          path: ci_results.json
```

---

## VIII. Baseline Test Manifests

The harness requires baseline manifests for golden replay and seed fuzzing.

### Golden Manifests (15 total)

**WUL Core (5):**
- golden_wul_001.json
- golden_wul_002.json
- golden_wul_003.json
- golden_wul_004.json
- golden_wul_005.json

**NSPS (5):**
- golden_nsps_001.json
- golden_nsps_002.json
- golden_nsps_003.json
- golden_nsps_004.json
- golden_nsps_005.json

**Kernel (5):**
- golden_kernel_001.json
- golden_kernel_002.json
- golden_kernel_003.json
- golden_kernel_004.json
- golden_kernel_005.json

### Seed-Fuzz Corpus (100)

Fixed 100-item corpus (deterministic across runs):
- corpus_001.json through corpus_100.json
- Covers all major code paths
- Includes edge cases and boundary conditions

---

## IX. Expected Results

### Passing Build

```
UNIFIED_CI_REPLAY_V1 RESULTS
============================
Suite: all
Status: PASS ✅

T1 Golden Replay:           PASS (15/15, 30s)
T2 Cross-Environment:       PASS (1/1, 60s)
T3 Seed Fuzzing:            PASS (100,000/100,000, 5m)
T4 Artifact Diff:           PASS (115/115, 30s)
T5 Adversarial:             PASS (30/30, 60s)

Total:  115,145 test cases
Passed: 115,145
Failed: 0
Duration: ~7 minutes
Drift: ZERO

✅ DETERMINISM VERIFIED
✅ HASH STABILITY VERIFIED
✅ CROSS-ENVIRONMENT REPLAY VERIFIED
✅ ADVERSARIAL ROBUSTNESS VERIFIED
```

### Failing Build

```
UNIFIED_CI_REPLAY_V1 RESULTS
============================
Suite: all
Status: FAIL ❌

T1 Golden Replay:           FAIL (14/15, 30s)
  - GOLDEN-005: Run 2 hash differs from runs 1,3
    Severity: CRITICAL

T2 Cross-Environment:       PASS
T3 Seed Fuzzing:            PASS
T4 Artifact Diff:           PASS
T5 Adversarial:             PASS

Failures: 1
Error: Non-deterministic output detected

❌ BUILD FAILED - Determinism regression in T1
```

---

## X. Implementation Checklist

- [ ] Create /tests/ci_replay/ directory
- [ ] Implement T1_golden_replay() function
- [ ] Implement T2_cross_environment() function
- [ ] Implement T3_seed_fuzz() function
- [ ] Implement T4_artifact_diff() function
- [ ] Implement T5_adversarial_perturbation() function
- [ ] Create 15 golden manifests
- [ ] Create 100-item test corpus
- [ ] Create CI output schema validator
- [ ] Implement JSON-only output writer
- [ ] Add GitHub Actions workflow
- [ ] Document baseline test results
- [ ] Create failure triage playbook

---

## XI. Troubleshooting

### Non-Deterministic Output

**Symptom:** T1 or T3 fails with hash mismatch

**Diagnosis:**
1. Check for time-dependent code (wall clock, datetime)
2. Check for random entropy (random module, uuid)
3. Check for unordered iteration (dicts, sets)
4. Check for floating-point arithmetic (use Decimal)
5. Run with `strace` to check system calls

**Fix:** Remove non-deterministic dependency, re-run

### Cross-Environment Failure

**Symptom:** T2 fails; same manifest produces different output on different OS

**Diagnosis:**
1. Check for OS-specific code paths
2. Check for locale-dependent string operations
3. Check for timezone-dependent parsing
4. Check for architecture-specific behavior

**Fix:** Abstract OS-specific behavior, use canonical forms

### Adversarial Flakiness

**Symptom:** T5 fails; same adversarial case sometimes accepted, sometimes rejected

**Diagnosis:**
1. Check for race conditions
2. Check for nondeterministic error handling
3. Check for flaky validation logic

**Fix:** Make validation deterministic, re-run

---

## XII. Freeze Condition

This harness is **LOCKED** when:

✅ 1. All 5 test classes (T1–T5) are implemented
✅ 2. Output contract is finalized (JSON schema)
✅ 3. Golden manifests are frozen (15 total)
✅ 4. Seed corpus is frozen (100 items)
✅ 5. Baseline results recorded (passing build)
✅ 6. GitHub Actions integration working
✅ 7. Zero-drift rule is enforced
✅ 8. Failure triage procedures documented

Once locked, the harness is the authoritative determinism test suite.

---

**Status:** READY FOR IMPLEMENTATION
**Prerequisite:** HELEN_KERNEL_DOCTRINE_V1 (locked)
**Frozen by:** HELEN OS Kernel Authority
**Date:** 2026-03-12
