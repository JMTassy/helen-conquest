# WUL-ORACLE Verification Checklist

## Purpose

This checklist maps every formal claim in `WUL_ORACLE_PAPER.tex` to concrete, testable verification procedures. Use this to validate implementation correctness.

---

## Notation

- ✅ **Verified:** Implementation exists, tests pass, CI enforces
- ⚠️ **Partial:** Implementation exists but tests incomplete
- ❌ **Missing:** Not yet implemented
- 🔒 **Schema-Enforced:** Mechanical enforcement at schema level

---

## Section 3: WUL-CORE v0 - Bounded Symbolic Kernel

### Definition 3.1: WUL Token Tree

**Formal Claim:**
> A WUL token tree is a finite rooted tree whose nodes are drawn from a fixed kernel registry (primitive IDs with fixed arity and typing constraints). Free text is disallowed in token trees.

**Verification Procedure:**

1. ✅ **Kernel registry exists and is hashed**
   - [ ] File: `src/wul/core_kernel.json` exists
   - [ ] Contains: `discourse`, `entities`, `relations` with fixed arity
   - [ ] Hashed: `kernel_hash = SHA256(Canon8785(kernel_registry.json))`
   - [ ] Test: `test_kernel_registry_structure.py`

2. ❌ **Validator rejects non-compiling messages**
   - [ ] Function: `validate_token_tree()` exists in `src/wul/validate.py`
   - [ ] Rejects: free text nodes
   - [ ] Rejects: unknown primitives not in kernel
   - [ ] Rejects: arity violations
   - [ ] Test: `test_validator_rejects_invalid_trees.py`

3. ❌ **Bridge enforces compilation**
   - [ ] Bridge: `src/wul/bridge.py` exists
   - [ ] Non-compiling messages → rejected with reason code
   - [ ] Test: `test_bridge_rejects_non_compiling.py`

**Status:** ❌ Missing — High priority

---

### Invariant 3.1: No Free Text

**Formal Claim:**
> Any artifact classified as "receipt-hashed payload" MUST contain no untyped free-form natural language fields.

**Verification Procedure:**

1. 🔒 **Schema-level enforcement**
   - [x] `decision_record.schema.json`: `additionalProperties: false` ✅
   - [ ] `tribunal_bundle.schema.json`: `additionalProperties: false` ❌
   - [ ] `briefcase.schema.json`: `additionalProperties: false` ❌
   - All string fields have: `pattern`, `enum`, or `format` constraints

2. ✅ **Test enforcement**
   - [x] Test: `test_decision_record_has_no_free_text()` ✅
   - [ ] Test: `test_all_hashed_payloads_have_no_free_text()` ❌
   - Verifies: no string field allows arbitrary text

3. ⚠️ **Documentation enforcement**
   - [x] `DECISION_RECORD_DETERMINISM.md` documents payload vs meta split ✅
   - States: free text only in meta files, not hashed payloads

**Status:** ⚠️ Partial — Schema complete for decision_record, needs extension to other artifacts

---

### Invariant 3.2: Bounded Structure

**Formal Claim:**
> All token trees must satisfy declared structural constraints (e.g., maximum depth, maximum node count, maximum branching), which are treated as kill-switch policies.

**Verification Procedure:**

1. ❌ **Kernel declares bounds**
   - [ ] `core_kernel.json` contains `governance` section:
   ```json
   {
     "governance": {
       "no_free_text": true,
       "max_depth": 64,
       "max_nodes": 512
     }
   }
   ```

2. ❌ **Validator enforces bounds**
   - [ ] Function: `validate_token_tree()` checks depth ≤ 64
   - [ ] Function: `validate_token_tree()` checks node count ≤ 512
   - [ ] Returns: reason codes `DEPTH_EXCEEDED`, `NODE_COUNT_EXCEEDED`

3. ❌ **Test: Kill-switch activation**
   - [ ] Test: `test_depth_exceeds_threshold()`
     - Create tree with depth 65
     - Assert: validation fails with `DEPTH_EXCEEDED`
   - [ ] Test: `test_node_count_exceeds_threshold()`
     - Create tree with 513 nodes
     - Assert: validation fails with `NODE_COUNT_EXCEEDED`

**Status:** ❌ Missing — High priority

**Reason Codes Required:**
- ✅ `DEPTH_EXCEEDED` in `reason_codes.json`
- ✅ `NODE_COUNT_EXCEEDED` in `reason_codes.json`

---

## Section 4: Receipt Discipline

### Protocol 4.1: Determinism Split

**Formal Claim:**
> The Mayor produces: (a) `decision_record.json`: deterministic, receipt-hashed payload (no timestamps). (b) `decision_record.meta.json`: non-hashed metadata.

**Verification Procedure:**

1. 🔒 **Schema prohibits timestamp in hashed payload**
   - [x] `decision_record.schema.json`: no `timestamp` field ✅
   - [x] Schema `required` fields: decision, blocking, receipt_gap, kill_switches_pass, metadata ✅

2. ✅ **Fixtures validate**
   - [x] `decision_record_ship.json`: no timestamp field ✅
   - [x] `decision_record_no_ship.json`: no timestamp field ✅
   - [x] Both pass schema validation ✅

3. ⚠️ **Meta schema exists**
   - [x] Example: `decision_record.meta.json` exists ✅
   - [ ] Schema: `decision_record.meta.schema.json` (optional, recommended) ❌
   - Contains: `decision_record_hash`, `timestamp`, `audit_trail`

4. ❌ **Mayor implementation splits output**
   - [ ] Function: `emit_decision()` in `src/mayor/decide.py`
   - [ ] Writes: `decision_record.json` (no timestamp)
   - [ ] Writes: `decision_record.meta.json` (timestamp included)
   - [ ] Computes: `decision_record_hash` binding the two files

**Status:** ⚠️ Partial — Schema and fixtures complete, Mayor implementation missing

**Documentation:** ✅ `DECISION_RECORD_DETERMINISM.md` fully specifies protocol

---

### Definition 4.2: Required Obligations

**Formal Claim:**
> A run declares a set of *required obligations*, each with a severity level (HARD or SOFT), expected attestor class, and expected evidence paths.

**Verification Procedure:**

1. ❌ **Schema exists**
   - [ ] File: `schemas/tribunal_bundle.schema.json`
   - [ ] Contains: `obligations` array with required fields:
     - `name` (string)
     - `type` (string)
     - `severity` (enum: HARD, SOFT)
     - `expected_attestor` (string)
     - `expected_evidence_paths` (array of RelPath)

2. ❌ **Schema validation enforced**
   - [ ] Test: `test_tribunal_bundle_validates_obligations()`
   - [ ] Rejects: missing severity
   - [ ] Rejects: invalid severity (not HARD/SOFT)
   - [ ] Rejects: absolute paths in evidence_paths

3. ❌ **Fixtures exist**
   - [ ] `tests/fixtures/tribunal_bundle.json`
   - [ ] Contains: mix of HARD and SOFT obligations
   - [ ] Validates: against schema

**Status:** ❌ Missing — Medium priority

---

### Definition 4.3: Receipt Gap

**Formal Claim:**
> The receipt gap $\RG \in \mathbb{N}$ is the count of unsatisfied HARD obligations under the declared policies and verification rules.

**Verification Procedure:**

1. ❌ **Computation function exists**
   - [ ] Function: `compute_receipt_gap(tribunal_bundle, attestations_ledger)` in `src/receipt/compute_gap.py`
   - [ ] Returns: integer ≥ 0
   - [ ] Logic: counts HARD obligations where `is_obligation_satisfied() == False`

2. ❌ **Satisfaction predicate correct**
   - [ ] Function: `is_obligation_satisfied(obligation, ledger)`
   - [ ] Returns True iff:
     - attestation_valid == True
     - policy_match == 1 (or equivalent)
     - expected_attestor matches actual (if policy requires)

3. ❌ **Tests verify computation**
   - [ ] Test: `test_receipt_gap_zero_when_all_hard_satisfied()`
     - All HARD obligations have valid attestations
     - Assert: receipt_gap == 0
   - [ ] Test: `test_receipt_gap_counts_only_hard()`
     - 3 HARD unsatisfied, 2 SOFT unsatisfied
     - Assert: receipt_gap == 3 (not 5)
   - [ ] Test: `test_receipt_gap_nonzero_when_hard_missing()`
     - Load partial ledger
     - Assert: receipt_gap == (expected count)

4. ❌ **API endpoint exists**
   - [ ] Endpoint: `GET /api/runs/:run_id/receipt_gap`
   - [ ] Returns: `{"receipt_gap": N, "missing_obligations": [...]}`

**Status:** ❌ Missing — High priority

**Reason Codes Required:**
- ✅ `RECEIPT_GAP_NONZERO` in `reason_codes.json`
- ✅ `HARD_OBLIGATION_UNSATISFIED` in `reason_codes.json`

---

## Section 5: Mayor Decision Surface

### Invariant 5.1: No Silent Failures

**Formal Claim:**
> If the decision is NO_SHIP, then the `blocking` list must contain at least one typed reason code.

**Verification Procedure:**

1. 🔒 **Schema enforces constraint**
   - [x] `decision_record.schema.json` lines 57-70: ✅
   ```json
   {
     "if": {"properties": {"decision": {"const": "NO_SHIP"}}},
     "then": {"properties": {"blocking": {"minItems": 1}}}
   }
   ```

2. ✅ **Positive test**
   - [x] Test: `test_no_ship_fixture_validates()` ✅
   - [x] Fixture: `decision_record_no_ship.json` has non-empty blocking ✅
   - [x] Validates: against schema ✅

3. ✅ **Falsification test**
   - [x] Test: `test_schema_rejects_no_ship_without_blocking()` ✅
   - [x] Creates: NO_SHIP decision with empty blocking array ✅
   - [x] Asserts: schema validation MUST fail ✅
   - [x] Catches: `jsonschema.ValidationError` ✅

4. ❌ **Mayor implementation enforces**
   - [ ] Function: `compute_decision()` in `src/mayor/decide.py`
   - [ ] If returns NO_SHIP, MUST populate blocking array
   - [ ] Each entry: typed reason code from allowlist

**Status:** ✅ Schema + tests verified — Mayor implementation missing

**Reason Code Required:**
- ✅ `NO_SHIP_WITHOUT_BLOCKING_CODES` in `reason_codes.json`

---

### Invariant 5.2: SHIP Implies Zero Gap

**Formal Claim:**
> If the decision is SHIP, then $\RG=0$, kill switches pass, and the `blocking` list is empty.

**Verification Procedure:**

1. 🔒 **Schema enforces all three conditions**
   - [x] `decision_record.schema.json` lines 72-87: ✅
   ```json
   {
     "if": {"properties": {"decision": {"const": "SHIP"}}},
     "then": {
       "properties": {
         "blocking": {"maxItems": 0},
         "receipt_gap": {"const": 0},
         "kill_switches_pass": {"const": true}
       }
     }
   }
   ```

2. ✅ **Positive test**
   - [x] Test: `test_ship_fixture_validates()` ✅
   - [x] Fixture: `decision_record_ship.json` has: ✅
     - decision: "SHIP"
     - blocking: []
     - receipt_gap: 0
     - kill_switches_pass: true

3. ✅ **Falsification tests (3 separate violations)**
   - [x] Test: `test_schema_rejects_ship_with_blocking()` ✅
     - SHIP + non-empty blocking → schema MUST reject
   - [x] Test: `test_schema_rejects_ship_with_nonzero_receipt_gap()` ✅
     - SHIP + receipt_gap=1 → schema MUST reject
   - [x] Test: `test_schema_rejects_ship_with_kill_switch_failure()` ✅
     - SHIP + kill_switches_pass=false → schema MUST reject

4. ❌ **Mayor decision function implements logic**
   - [ ] Function: `compute_decision()` pure function
   - [ ] Logic: `decision = SHIP iff (kill_switches_pass AND receipt_gap == 0)`
   - [ ] Test: `test_mayor_purity_recompute_matches_output()`
     - Recompute decision from hashed inputs
     - Assert: matches actual decision output

**Status:** ✅ Schema + falsification tests verified — Mayor purity test missing

**Reason Codes Required:**
- ✅ `SHIP_WITH_BLOCKING_CODES` in `reason_codes.json`
- ✅ `SHIP_WITH_NONZERO_RECEIPT_GAP` in `reason_codes.json`
- ✅ `SHIP_WITH_KILL_SWITCH_FAILURE` in `reason_codes.json`

---

### Definition 5.3: Reason-Code Allowlist

**Formal Claim:**
> All blocking codes appearing in decision records must be elements of a machine-readable allowlist (`reason_codes.json`). CI tests enforce membership and prohibit ad-hoc codes.

**Verification Procedure:**

1. ✅ **Allowlist exists and is machine-readable**
   - [x] File: `reason_codes.json` exists ✅
   - [x] Structure: `{"version": "v0.1", "codes": [...]}` ✅
   - [x] Count: 30 canonical codes ✅

2. ✅ **Human-readable source exists**
   - [x] File: `REASON_CODES.md` exists ✅
   - [x] Contains: description, policy, enforcement for each code ✅
   - [x] Single source of truth ✅

3. ✅ **Test enforces allowlist membership**
   - [x] Test: `test_blocking_codes_in_allowlist()` ✅
   - [x] For each fixture in `tests/fixtures/decision_record_*.json`: ✅
     - Load decision record
     - For each blocking code
     - Assert: code in allowlist
   - [x] Error message: includes code, fixture name, allowlist location ✅

4. ✅ **Allowlist integrity tests**
   - [x] Test: `test_allowlist_has_no_duplicates()` ✅
   - [x] Test: `test_allowlist_format_valid()` ✅
     - Pattern: `^[A-Z0-9_]{3,64}$`
   - [x] Test: `test_allowlist_sorted()` ✅
     - Alphabetically sorted

5. ❌ **CI enforces sync**
   - [ ] Script: `scripts/sync_reason_codes.py`
     - Parses: `REASON_CODES.md` section 3
     - Extracts: all code names
     - Compares: to `reason_codes.json`
     - Fails: if diff detected
   - [ ] CI workflow: `.github/workflows/reason_codes_sync.yml`
     - Runs: `python scripts/sync_reason_codes.py --check`
     - Blocks: PRs if codes out of sync

**Status:** ✅ Allowlist + tests complete — CI sync script missing

---

## Section 6: Pipeline Stages and Artifact Model

### Definition 6.1: Run Index

**Formal Claim:**
> A run produces a `run_index.json` summarizing stage status, equivalence pins, primary KPIs ($\RG$, kill-switch status, decision), and an artifact list with $\sha$ hashes.

**Verification Procedure:**

1. ❌ **Schema exists**
   - [ ] File: `schemas/run_index.schema.json`
   - [ ] Required fields:
     - run_id, claim_id
     - eq_pins (inputs_hash, config_hash, kernel_hash, canon_impl_id)
     - stages (array with name, status, artifacts)
     - summary (receipt_gap, kill_switches_pass, decision, stage)

2. ❌ **Schema validation**
   - [ ] Test: `test_run_index_validates_against_schema()`
   - [ ] Fixture: `tests/fixtures/run_index.json`
   - [ ] Rejects: missing required fields
   - [ ] Rejects: invalid stage status (not in enum)
   - [ ] Rejects: invalid decision (not SHIP/NO_SHIP/PENDING)

3. ❌ **API endpoint exists**
   - [ ] Endpoint: `GET /api/runs/:run_id/index`
   - [ ] Returns: `run_index.json` for specified run
   - [ ] Validates: response against schema

4. ❌ **Hash integrity**
   - [ ] Test: `test_run_index_artifact_hashes_match_blobs()`
   - [ ] For each artifact in run_index:
     - Fetch: blob via `GET /api/runs/:run_id/artifacts/:path`
     - Compute: SHA-256 hash
     - Assert: matches hash in run_index

**Status:** ❌ Missing — Medium priority

---

## Section 7: Falsification and Evaluation Protocols

### Protocol 7.1: Ablation-First Evaluation

**Formal Claim:**
> To claim governance benefit from WUL--ORACLE constraints, the system must be evaluated under ablations that explicitly remove or weaken core mechanisms.

**Verification Procedure:**

1. ❌ **Ablation configs exist**
   - [ ] Directory: `configs/ablations/`
   - [ ] Baseline: `A0_baseline.json` (R15=ON, FreeText=OFF, Injection=CANONICAL)
   - [ ] Kill tests:
     - `A1_no_r15.json` (R15=OFF)
     - `A2_free_text.json` (FreeText=ON)
   - [ ] Stress tests:
     - `A3_random_injection.json`
     - `A4_high_adversarial.json` (adversarial_fraction=0.5)
     - `A5_long_horizon.json` (horizon=10000)

2. ❌ **Ablation runner exists**
   - [ ] Function: `run_ablation(ablation_config, seed)` in `src/ablation/run_ablation.py`
   - [ ] Returns:
     ```python
     {
       "survival_length": int,
       "final_receipt_gap": int,
       "obligation_satisfaction_rate": float,
       "trace_hash": str,
       "artifacts": {...}
     }
     ```

3. ❌ **Acceptance criteria tests**
   - [ ] Test: `test_baseline_survives_minimum_length()`
     - Run: A0 with seed=42
     - Assert: survival_length ≥ T_min (100)
   - [ ] Test: `test_no_r15_fails_early()`
     - Run: A1 with seed=42
     - Assert: reason_code == "R15_INVALID"
     - Assert: step <= 1
   - [ ] Test: `test_ablation_stability_advantage()`
     - Run: A0, A1, A2 with multiple seeds
     - Assert: med(A0) ≥ T_min
     - Assert: At least 2 ablations: med(ablation) ≤ 0.5 * med(A0)

**Status:** ❌ Missing — Low priority (research phase)

---

### Protocol 7.2: Cross-Runtime Determinism

**Formal Claim:**
> A determinism claim is only accepted if artifact hashes match across a declared matrix of runtimes (e.g., Python versions, OS families), under a pinned canonicalization rule.

**Verification Procedure:**

1. ❌ **Golden reference exists**
   - [ ] File: `ci/golden_hashes_v0.json`
   - [ ] Contains:
     ```json
     {
       "baseline": "A0",
       "seed": 42,
       "expected_hashes": {
         "kernel_hash": "...",
         "run_spec_hash": "...",
         "trace_hash": "...",
         "artifact_root_hash": "...",
         "receipt_root_hash": "..."
       }
     }
     ```

2. ❌ **CI matrix exists**
   - [ ] File: `.github/workflows/cross_runtime_determinism.yml`
   - [ ] Matrix:
     - python: ['3.10', '3.11', '3.12']
     - os: [ubuntu-latest, macos-latest]
   - [ ] Steps:
     1. Run baseline with seed=42
     2. Extract hashes
     3. Upload artifacts
     4. Compare all hashes
     5. Fail if any mismatch

3. ❌ **Test validates golden reference**
   - [ ] Test: `test_hashes_match_golden_reference()`
   - [ ] Run: A0 baseline with seed=42
   - [ ] For each hash in golden reference:
     - Compute: hash from current run
     - Assert: matches golden value
   - [ ] If mismatch:
     - Reason code: `GOLDEN_HASH_MISMATCH`
     - Decision: NO_SHIP

4. ❌ **Canonicalization pinned**
   - [ ] Canon impl: RFC 8785 (pinned)
   - [ ] Test: `test_canon_impl_id_recorded()`
     - Assert: canon_impl_id == "rfc8785:v1" (or declared)
   - [ ] Reason code: `CANON_IMPL_ID_INVALID` if mismatch

**Status:** ❌ Missing — Low priority (CI infrastructure)

**Reason Codes Required:**
- ✅ `GOLDEN_HASH_MISMATCH` in `reason_codes.json`
- ✅ `REPLAY_NONDETERMINISM` in `reason_codes.json`
- ✅ `CANON_IMPL_ID_INVALID` in `reason_codes.json`

---

## Overall Verification Status

### ✅ Verified (9 items)
1. Decision record schema (2020-12, `additionalProperties: false`)
2. NO_SHIP invariant: schema enforces minItems ≥ 1
3. SHIP invariant: schema enforces maxItems=0, receipt_gap=0, kill_switches_pass=true
4. Falsification tests for all schema invariants
5. Reason codes allowlist (30 codes)
6. Allowlist enforcement test
7. Allowlist integrity tests (no duplicates, valid format, sorted)
8. Determinism split: fixtures have no timestamps
9. Documentation: REASON_CODES.md, DECISION_RECORD_DETERMINISM.md

### ⚠️ Partial (2 items)
1. No free text invariant: schema complete for decision_record, needs extension
2. Determinism split: schema + fixtures complete, Mayor implementation missing

### ❌ Missing - High Priority (6 items)
1. WUL-CORE kernel registry (`core_kernel.json`)
2. Token tree validator (`validate.py`)
3. Bounded structure tests
4. Mayor decision function (`decide.py`)
5. Mayor purity test
6. Receipt gap computation (`compute_gap.py`)

### ❌ Missing - Medium Priority (5 items)
1. Tribunal bundle schema
2. Run index schema
3. Receipt gap computation tests
4. API endpoints (receipt_gap, run_index)
5. Additional fixture files

### ❌ Missing - Low Priority (7 items)
1. Ablation configs
2. Ablation runner
3. Ablation tests
4. Cross-runtime determinism CI
5. Golden hashes reference
6. Reason codes sync script
7. CI workflows

---

## Verification Workflow

For each implementation artifact:

1. **Create implementation**
   - Code file exists
   - Type hints included
   - Docstrings reference paper (e.g., "implements Invariant 5.2")

2. **Create positive test**
   - Valid case passes
   - Fixture exists if needed
   - Test name references paper element

3. **Create falsification test**
   - Invalid case fails with correct reason code
   - Error message is clear and actionable

4. **Add CI gate**
   - Test runs in CI on every PR
   - Failure blocks merge

5. **Update this checklist**
   - Mark item as ✅ Verified
   - Document: file paths, test names, reason codes

---

## Priority Order for Implementation

### Immediate (Week 1)
1. WUL-CORE kernel + validator
2. Mayor decision function
3. Receipt gap computation

### Short-term (Week 2)
1. Mayor purity test
2. Tribunal bundle schema
3. Receipt gap API endpoint

### Medium-term (Month 1)
1. Run index schema
2. Additional schemas (briefcase, etc.)
3. Full API surface

### Long-term (Research Phase)
1. Ablation infrastructure
2. Cross-runtime determinism CI
3. Reason codes sync automation

---

**Last Updated:** January 2026

**Next Review:** After each implementation milestone, update verification status
