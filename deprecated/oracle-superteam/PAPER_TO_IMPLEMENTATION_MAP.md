# Paper to Implementation Map

## Purpose

This document maps each theorem, invariant, protocol, and definition in `WUL_ORACLE_PAPER.tex` to concrete implementation artifacts, tests, and schemas in the repository.

---

## Section 3: WUL-CORE v0 - Bounded Symbolic Kernel

### Definition 3.1: WUL token tree

**Paper Statement:**
> A WUL token tree is a finite rooted tree whose nodes are drawn from a fixed kernel registry (primitive IDs with fixed arity and typing constraints). Free text is disallowed in token trees.

**Implementation Artifacts:**
- **Kernel registry:** (To be created) `src/wul/core_kernel.json`
  - Defines primitive IDs (discourse, entities, relations)
  - Each relation has fixed arity
  - Governance section includes `no_free_text: true`, `max_depth`, `max_nodes`

- **Validator:** (To be created) `src/wul/validate.py`
  - Function: `validate_token_tree(tree, kernel, thresholds)`
  - Checks: arity, depth, node count, no free text
  - Returns: `ValidationResult(ok, reason, depth, nodes, has_r15, has_objective_pair)`

**Expected Location:**
```
schemas/wul_token_tree.schema.json  # JSON Schema for token tree structure
src/wul/validate.py                 # Validator implementation
```

---

### Invariant 3.1 (No free text)
**Label:** `\label{inv:no-free-text}`

**Paper Statement:**
> Any artifact classified as "receipt-hashed payload" MUST contain no untyped free-form natural language fields. Where human explanation is required (e.g., audit notes), it MUST be placed in explicitly non-hashed metadata artifacts.

**Implementation Enforcement:**

1. **Schema-level:** All receipt-hashed schemas use `additionalProperties: false` and typed fields only
   - `schemas/decision_record.schema.json` ✅
   - `schemas/tribunal_bundle.schema.json` (to be created)
   - `schemas/briefcase.schema.json` (to be created)

2. **Test enforcement:** (To be created) `tests/test_no_free_text_in_hashed_payloads.py`
   ```python
   def test_decision_record_has_no_free_text():
       schema = load_schema("decision_record.schema.json")
       # Assert all string fields have pattern/enum/format constraints
       # Assert no fields allow arbitrary text
   ```

3. **CI gate:** All hashed artifacts must pass free-text validation before receipt computation

**Artifacts:**
- ✅ `schemas/decision_record.schema.json` (strict typing, no free text)
- ✅ `DECISION_RECORD_DETERMINISM.md` (documents payload vs meta split)
- ⚠️ Need: `tests/test_no_free_text_in_hashed_payloads.py`

---

### Invariant 3.2 (Bounded structure)
**Label:** `\label{inv:bounded}`

**Paper Statement:**
> All token trees must satisfy declared structural constraints (e.g., maximum depth, maximum node count, maximum branching), which are treated as kill-switch policies.

**Implementation Enforcement:**

1. **Kernel registry governance section:**
   ```json
   {
     "governance": {
       "no_free_text": true,
       "max_depth": 64,
       "max_nodes": 512
     }
   }
   ```

2. **Validator checks:** `src/wul/validate.py`
   - Depth check: recursive tree traversal with depth counter
   - Node count: total node accumulator
   - Reject with `DEPTH_EXCEEDED` or `NODE_COUNT_EXCEEDED` reason codes

3. **Test:** (To be created) `tests/test_bounded_structure.py`
   ```python
   def test_depth_exceeds_threshold():
       deep_tree = create_tree_with_depth(65)
       result = validate_token_tree(deep_tree, kernel, {"max_depth": 64})
       assert not result.ok
       assert result.reason == "DEPTH_EXCEEDED"
   ```

**Artifacts:**
- ⚠️ Need: `src/wul/core_kernel.json` with governance section
- ⚠️ Need: `src/wul/validate.py` with depth/node checks
- ⚠️ Need: `tests/test_bounded_structure.py`
- ✅ `REASON_CODES.md` (includes DEPTH_EXCEEDED, NODE_COUNT_EXCEEDED)

---

## Section 4: Receipt Discipline

### Protocol 4.1: Determinism split for decision records
**Label:** `\label{prot:det-split}`

**Paper Statement:**
> The Mayor produces:
> (a) `decision_record.json`: deterministic, receipt-hashed payload (no timestamps).
> (b) `decision_record.meta.json`: non-hashed metadata, including timestamps and environment stamps.

**Implementation Artifacts:**
- ✅ `schemas/decision_record.schema.json` (no timestamp field in hashed payload)
- ✅ `tests/fixtures/decision_record.meta.json` (example non-hashed metadata structure)
- ✅ `DECISION_RECORD_DETERMINISM.md` (full specification of split)

**Mayor Implementation:** (To be created) `src/mayor/decide.py`
```python
def emit_decision(decision_data):
    # Hashed payload
    decision_record = {
        "decision": decision_data["decision"],
        "kill_switches_pass": decision_data["kill_switches_pass"],
        "receipt_gap": decision_data["receipt_gap"],
        "blocking": decision_data["blocking"],
        "metadata": decision_data["metadata"]
    }

    # Compute hash
    record_hash = hash_decision_record(decision_record)

    # Non-hashed metadata
    meta = {
        "decision_record_hash": record_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "audit_trail": decision_data["audit_trail"]
    }

    write_json("decision_record.json", decision_record)
    write_json("decision_record.meta.json", meta)
```

**Test:** ✅ `tests/test_mayor_no_ship_invariant.py` (validates schema, no timestamp in fixtures)

---

### Definition 4.2: Required obligations

**Paper Statement:**
> A run declares a set of *required obligations*, each with a severity level (HARD or SOFT), expected attestor class, and expected evidence paths. HARD obligations define the minimal viability boundary for SHIP.

**Implementation Artifacts:**

**Schema:** (To be created) `schemas/tribunal_bundle.schema.json`
```json
{
  "obligations": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["name", "type", "severity", "expected_attestor"],
      "properties": {
        "name": {"type": "string"},
        "type": {"type": "string"},
        "severity": {"enum": ["HARD", "SOFT"]},
        "expected_attestor": {"type": "string"},
        "expected_evidence_paths": {
          "type": "array",
          "items": {"$ref": "#/$defs/RelPath"}
        }
      }
    }
  }
}
```

**Artifacts:**
- ⚠️ Need: `schemas/tribunal_bundle.schema.json`
- ⚠️ Need: Example `tests/fixtures/tribunal_bundle.json`

---

### Definition 4.3: Receipt gap
**Label:** `\label{def:receipt-gap}`

**Paper Statement:**
> The receipt gap $\RG \in \mathbb{N}$ is the count of unsatisfied HARD obligations under the declared policies and verification rules.

**Implementation:**

**Computation function:** (To be created) `src/receipt/compute_gap.py`
```python
def compute_receipt_gap(tribunal_bundle: dict, attestations_ledger: dict) -> int:
    """
    Count unsatisfied HARD obligations.

    An obligation is satisfied iff:
    - attestation_valid == True
    - policy_match == 1 (or equivalent)
    - expected_attestor matches actual attestor (if policy requires)
    """
    hard_obligations = [o for o in tribunal_bundle["obligations"] if o["severity"] == "HARD"]

    satisfied_count = 0
    for obl in hard_obligations:
        if is_obligation_satisfied(obl, attestations_ledger):
            satisfied_count += 1

    return len(hard_obligations) - satisfied_count

def is_obligation_satisfied(obligation: dict, ledger: dict) -> bool:
    # Check attestations_ledger for matching entry
    # Return True iff attestation_valid AND policy_match
    ...
```

**API Endpoint:** `GET /api/runs/:run_id/receipt_gap`
- Implementation: (To be created) `backend/api/receipt_gap.py`

**Test:** (To be created) `tests/test_receipt_gap_computation.py`
```python
def test_receipt_gap_zero_when_all_hard_satisfied():
    tribunal = load_fixture("tribunal_bundle_complete.json")
    ledger = load_fixture("attestations_ledger_complete.json")
    gap = compute_receipt_gap(tribunal, ledger)
    assert gap == 0

def test_receipt_gap_nonzero_when_hard_missing():
    tribunal = load_fixture("tribunal_bundle.json")
    ledger = load_fixture("attestations_ledger_partial.json")
    gap = compute_receipt_gap(tribunal, ledger)
    assert gap == 3
```

**Artifacts:**
- ⚠️ Need: `src/receipt/compute_gap.py`
- ⚠️ Need: `tests/test_receipt_gap_computation.py`
- ⚠️ Need: `backend/api/receipt_gap.py` (if API-based)

---

## Section 5: Mayor Decision Surface

### Invariant 5.1: No silent failures
**Label:** `\label{inv:no-silent}`

**Paper Statement:**
> If the decision is NO_SHIP, then the `blocking` list must contain at least one typed reason code.

**Implementation Enforcement:**

1. **Schema-level:** `schemas/decision_record.schema.json` lines 57-70
   ```json
   {
     "if": {"properties": {"decision": {"const": "NO_SHIP"}}},
     "then": {"properties": {"blocking": {"minItems": 1}}}
   }
   ```

2. **Test:** ✅ `tests/test_mayor_no_ship_invariant.py`
   - `test_no_ship_fixture_validates()` — Positive case
   - `test_schema_rejects_no_ship_without_blocking()` — Falsification

**Enforcement Surface:**
- ✅ Schema validates at upload time (API endpoint)
- ✅ Mayor computation function MUST populate blocking array for NO_SHIP
- ✅ CI test ensures schema rejects violations

---

### Invariant 5.2: SHIP implies zero gap and passed gates
**Label:** `\label{inv:ship-implies}`

**Paper Statement:**
> If the decision is SHIP, then $\RG=0$, kill switches pass, and the `blocking` list is empty.

**Implementation Enforcement:**

1. **Schema-level:** `schemas/decision_record.schema.json` lines 72-87
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

2. **Test:** ✅ `tests/test_mayor_no_ship_invariant.py`
   - `test_ship_fixture_validates()` — Positive case
   - `test_schema_rejects_ship_with_blocking()` — Falsification
   - `test_schema_rejects_ship_with_nonzero_receipt_gap()` — Falsification
   - `test_schema_rejects_ship_with_kill_switch_failure()` — Falsification

**Mayor Decision Function:** (To be created) `src/mayor/decide.py`
```python
def compute_decision(tribunal_bundle, policies, receipt_root_payload):
    """
    Pure function implementing Paper Invariant 5.2.

    decision = SHIP iff (kill_switches_pass == True AND receipt_gap == 0)
    """
    kill_pass = policies.get("kill_switches_pass")
    rg = receipt_root_payload.get("receipt_gap")

    if kill_pass and rg == 0:
        return {
            "decision": "SHIP",
            "kill_switches_pass": True,
            "receipt_gap": 0,
            "blocking": []
        }
    else:
        # Compute blocking reasons
        blocking = []
        if not kill_pass:
            blocking.append({"code": "KILL_SWITCH_FAILED", "detail": "..."})
        if rg > 0:
            blocking.append({"code": "RECEIPT_GAP_NONZERO", "detail": f"{rg} HARD obligations unsatisfied"})

        return {
            "decision": "NO_SHIP",
            "kill_switches_pass": kill_pass,
            "receipt_gap": rg,
            "blocking": blocking
        }
```

**Artifacts:**
- ✅ Schema enforcement (`decision_record.schema.json`)
- ✅ Test enforcement (`test_mayor_no_ship_invariant.py`)
- ⚠️ Need: `src/mayor/decide.py` with pure decision function
- ⚠️ Need: `tests/test_mayor_purity.py` (already specified in summary, needs creation)

---

### Definition 5.3: Reason-code allowlist

**Paper Statement:**
> All blocking codes appearing in decision records must be elements of a machine-readable allowlist (`reason_codes.json`). CI tests enforce membership and prohibit ad-hoc codes.

**Implementation Artifacts:**
- ✅ `reason_codes.json` (30 canonical codes)
- ✅ `REASON_CODES.md` (single source of truth, human-readable)
- ✅ `tests/test_reason_codes_allowlist.py` (enforcement test)

**Test Implementation:**
```python
def test_blocking_codes_in_allowlist():
    allowlist = load_reason_codes_allowlist()
    for fixture_path in iter_decision_record_fixtures():
        decision_record = json.load(open(fixture_path))
        for entry in decision_record.get("blocking", []):
            code = entry["code"]
            assert code in allowlist, f"Code not in allowlist: {code}"
```

**CI Integration:** (To be created) `.github/workflows/reason_codes_sync.yml`
```yaml
- name: Check reason codes sync
  run: |
    python scripts/sync_reason_codes.py --check
    # Fails if reason_codes.json doesn't match REASON_CODES.md
```

**Artifacts:**
- ✅ `reason_codes.json`
- ✅ `REASON_CODES.md`
- ✅ `tests/test_reason_codes_allowlist.py`
- ⚠️ Need: `scripts/sync_reason_codes.py` (extract codes from MD, compare to JSON)
- ⚠️ Need: `.github/workflows/reason_codes_sync.yml`

---

## Section 6: Pipeline Stages and Artifact Model

### Definition 6.1: Run index

**Paper Statement:**
> A run produces a `run_index.json` summarizing stage status, equivalence pins, primary KPIs ($\RG$, kill-switch status, decision), and an artifact list with $\sha$ hashes. The UI is permitted to depend only on this index plus blob access to artifacts.

**Implementation:**

**Schema:** (To be created) `schemas/run_index.schema.json`
```json
{
  "type": "object",
  "required": ["run_id", "claim_id", "eq_pins", "stages", "summary"],
  "properties": {
    "run_id": {"type": "string"},
    "claim_id": {"type": "string"},
    "eq_pins": {
      "type": "object",
      "required": ["inputs_hash", "config_hash", "kernel_hash", "canon_impl_id"],
      "properties": {
        "inputs_hash": {"$ref": "#/$defs/Sha256Hex"},
        "config_hash": {"$ref": "#/$defs/Sha256Hex"},
        "kernel_hash": {"$ref": "#/$defs/Sha256Hex"},
        "canon_impl_id": {"type": "string", "pattern": "^[a-z0-9_:-]+$"}
      }
    },
    "stages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "status", "artifacts"],
        "properties": {
          "name": {"type": "string"},
          "status": {"enum": ["NOT_STARTED", "RUNNING", "COMPLETED", "FAILED"]},
          "artifacts": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["path", "sha256"],
              "properties": {
                "path": {"type": "string"},
                "sha256": {"$ref": "#/$defs/Sha256Hex"},
                "size": {"type": "integer"}
              }
            }
          },
          "reason_codes": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    },
    "summary": {
      "type": "object",
      "required": ["receipt_gap", "kill_switches_pass", "decision", "stage"],
      "properties": {
        "receipt_gap": {"type": "integer", "minimum": 0},
        "kill_switches_pass": {"type": "boolean"},
        "decision": {"enum": ["SHIP", "NO_SHIP", "PENDING"]},
        "stage": {"type": "string"}
      }
    }
  }
}
```

**API Endpoint:** `GET /api/runs/:run_id/index`
- Implementation: (To be created) `backend/api/run_index.py`
- Returns: `run_index.json` for the specified run

**Artifacts:**
- ⚠️ Need: `schemas/run_index.schema.json`
- ⚠️ Need: `backend/api/run_index.py`
- ⚠️ Need: Example `tests/fixtures/run_index.json`

---

## Section 7: Falsification and Evaluation Protocols

### Protocol 7.1: Ablation-first evaluation
**Label:** `\label{prot:ablation}`

**Paper Statement:**
> To claim governance benefit from WUL--ORACLE constraints, the system must be evaluated under ablations that explicitly remove or weaken core mechanisms, including:
> (a) Remove objective anchoring operator (e.g., R15 removed).
> (b) Disable or randomize injection (control vs targeted injection).
> (c) Allow free text (even constrained) within payload artifacts.
> (d) Increase adversarial agent fraction and extend horizon length.

**Implementation:**

**Ablation Config:** (To be created) `configs/ablations/`
```
ablations/
  A0_baseline.json          # R15=ON, FreeText=OFF, Injection=CANONICAL
  A1_no_r15.json            # R15=OFF (kill test)
  A2_free_text.json         # FreeText=ON (kill test)
  A3_random_injection.json  # Injection=RANDOM
  A4_high_adversarial.json  # adversarial_fraction=0.5
  A5_long_horizon.json      # horizon=10000
```

**Ablation Runner:** (To be created) `src/ablation/run_ablation.py`
```python
def run_ablation(ablation_config: dict, seed: int) -> dict:
    """
    Run single ablation with fixed seed.

    Returns:
        {
          "survival_length": int,
          "final_receipt_gap": int,
          "obligation_satisfaction_rate": float,
          "trace_hash": str,
          "artifacts": {...}
        }
    """
    ...

def run_ablation_matrix(ablation_configs: list, seeds: list) -> pd.DataFrame:
    """
    Run full ablation matrix.

    Returns DataFrame with columns:
    - ablation_id
    - seed
    - survival_length
    - receipt_gap
    - satisfaction_rate
    """
    ...
```

**Test:** (To be created) `tests/test_ablation_matrix.py`
```python
def test_baseline_survives_minimum_length():
    config = load_ablation_config("A0_baseline.json")
    result = run_ablation(config, seed=42)
    assert result["survival_length"] >= 100  # T_min

def test_no_r15_fails_early():
    config = load_ablation_config("A1_no_r15.json")
    result = run_ablation(config, seed=42)
    assert result["reason_code"] == "R15_INVALID"
    assert result["step"] <= 1
```

**Artifacts:**
- ⚠️ Need: `configs/ablations/` directory with JSON configs
- ⚠️ Need: `src/ablation/run_ablation.py`
- ⚠️ Need: `tests/test_ablation_matrix.py`
- ⚠️ Need: Documentation of ablation acceptance criteria (similar to ABLAT_MATRIX.md from summary)

---

### Protocol 7.2: Determinism matrix
**Label:** `\label{prot:determinism}`

**Paper Statement:**
> A determinism claim is only accepted if artifact hashes match across a declared matrix of runtimes (e.g., Python versions, OS families), under a pinned canonicalization rule. Any mismatch is a NO_SHIP condition with typed blocking reasons.

**Implementation:**

**CI Matrix:** (To be created) `.github/workflows/cross_runtime_determinism.yml`
```yaml
name: Cross-Runtime Determinism

on: [push, pull_request]

jobs:
  determinism-matrix:
    strategy:
      matrix:
        python: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, macos-latest]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}

      - name: Run baseline with fixed seed
        run: |
          python src/ablation/run_ablation.py \
            --config configs/ablations/A0_baseline.json \
            --seed 42 \
            --output artifacts/run_${{ matrix.os }}_${{ matrix.python }}.json

      - name: Extract hashes
        run: |
          python scripts/extract_hashes.py \
            artifacts/run_${{ matrix.os }}_${{ matrix.python }}.json \
            > hashes_${{ matrix.os }}_${{ matrix.python }}.txt

      - name: Upload hashes
        uses: actions/upload-artifact@v3
        with:
          name: hashes-${{ matrix.os }}-${{ matrix.python }}
          path: hashes_${{ matrix.os }}_${{ matrix.python }}.txt

  compare-hashes:
    needs: determinism-matrix
    runs-on: ubuntu-latest
    steps:
      - name: Download all hashes
        uses: actions/download-artifact@v3

      - name: Compare hashes across matrix
        run: |
          python scripts/compare_hashes.py hashes-* --fail-on-mismatch
```

**Golden Hashes:** (To be created) `ci/golden_hashes_v0.json`
```json
{
  "baseline": "A0",
  "seed": 42,
  "expected_hashes": {
    "kernel_hash": "a1b2c3...",
    "run_spec_hash": "d4e5f6...",
    "trace_hash": "a7b8c9...",
    "artifact_root_hash": "d0e1f2...",
    "receipt_root_hash": "a3b4c5..."
  }
}
```

**Test:** (To be created) `tests/test_cross_runtime_determinism.py`
```python
def test_hashes_match_golden_reference():
    golden = load_golden_hashes("ci/golden_hashes_v0.json")
    result = run_ablation(load_config("A0_baseline.json"), seed=42)

    for hash_name in ["kernel_hash", "run_spec_hash", "trace_hash"]:
        assert result[hash_name] == golden["expected_hashes"][hash_name], \
            f"GOLDEN_HASH_MISMATCH: {hash_name}"
```

**Artifacts:**
- ⚠️ Need: `.github/workflows/cross_runtime_determinism.yml`
- ⚠️ Need: `ci/golden_hashes_v0.json`
- ⚠️ Need: `scripts/extract_hashes.py`
- ⚠️ Need: `scripts/compare_hashes.py`
- ⚠️ Need: `tests/test_cross_runtime_determinism.py`

---

## Implementation Status Summary

### ✅ Completed (Hardened in Previous Work)

| Artifact | Paper Reference | Status |
|----------|----------------|--------|
| `schemas/decision_record.schema.json` | Invariants 5.1, 5.2 | ✅ 2020-12, schema-enforced |
| `reason_codes.json` | Definition 5.3 | ✅ 30 canonical codes |
| `REASON_CODES.md` | Definition 5.3 | ✅ Single source of truth |
| `tests/test_reason_codes_allowlist.py` | Definition 5.3 | ✅ Enforcement test |
| `tests/test_mayor_no_ship_invariant.py` | Invariants 5.1, 5.2 | ✅ Schema + falsification |
| `DECISION_RECORD_DETERMINISM.md` | Protocol 4.1 | ✅ Payload/meta split |
| `tests/fixtures/decision_record_*.json` | Protocol 4.1 | ✅ No timestamps |
| `UI_INTEGRATION_SPEC.md` | Definition 6.1 | ✅ API contract |

### ⚠️ High Priority (Core WUL-CORE)

| Artifact | Paper Reference | Criticality |
|----------|----------------|-------------|
| `src/wul/core_kernel.json` | Definition 3.1, Inv 3.2 | HIGH |
| `src/wul/validate.py` | Definition 3.1, Inv 3.2 | HIGH |
| `schemas/wul_token_tree.schema.json` | Definition 3.1 | HIGH |
| `tests/test_bounded_structure.py` | Invariant 3.2 | HIGH |
| `src/mayor/decide.py` | Invariant 5.2 | HIGH |
| `src/receipt/compute_gap.py` | Definition 4.3 | HIGH |

### ⚠️ Medium Priority (Schemas & APIs)

| Artifact | Paper Reference | Criticality |
|----------|----------------|-------------|
| `schemas/tribunal_bundle.schema.json` | Definition 4.2 | MEDIUM |
| `schemas/run_index.schema.json` | Definition 6.1 | MEDIUM |
| `backend/api/receipt_gap.py` | Definition 4.3 | MEDIUM |
| `backend/api/run_index.py` | Definition 6.1 | MEDIUM |
| `tests/test_receipt_gap_computation.py` | Definition 4.3 | MEDIUM |

### ⚠️ Low Priority (Evaluation Infrastructure)

| Artifact | Paper Reference | Criticality |
|----------|----------------|-------------|
| `configs/ablations/*.json` | Protocol 7.1 | LOW |
| `src/ablation/run_ablation.py` | Protocol 7.1 | LOW |
| `tests/test_ablation_matrix.py` | Protocol 7.1 | LOW |
| `.github/workflows/cross_runtime_determinism.yml` | Protocol 7.2 | LOW |
| `ci/golden_hashes_v0.json` | Protocol 7.2 | LOW |
| `scripts/sync_reason_codes.py` | Definition 5.3 | LOW |

---

## Next Concrete Steps (Prioritized)

### Step 1: WUL-CORE Kernel & Validator (HIGH)
1. Create `src/wul/core_kernel.json` with:
   - Discourse primitives (D01-D05)
   - Entity primitives (E01-E07)
   - Relation primitives (R15 with arity 2)
   - Governance: `no_free_text: true`, `max_depth: 64`, `max_nodes: 512`

2. Create `src/wul/validate.py` with:
   - `validate_token_tree()` function
   - Arity checking against kernel
   - Depth/node counting
   - No free text enforcement
   - Return typed `ValidationResult`

3. Create `tests/test_bounded_structure.py` with falsification tests

### Step 2: Mayor Decision Function (HIGH)
1. Create `src/mayor/decide.py` implementing pure decision function
2. Create `tests/test_mayor_purity.py` (recompute from hashed inputs)
3. Integrate with existing `test_mayor_no_ship_invariant.py`

### Step 3: Receipt Gap Computation (HIGH)
1. Create `src/receipt/compute_gap.py`
2. Create `tests/test_receipt_gap_computation.py`
3. Create `backend/api/receipt_gap.py` endpoint

### Step 4: Schemas (MEDIUM)
1. Create `schemas/tribunal_bundle.schema.json`
2. Create `schemas/run_index.schema.json`
3. Create `schemas/wul_token_tree.schema.json`
4. Add schema validation tests

### Step 5: Ablation Infrastructure (LOW - Research Phase)
1. Create ablation configs in `configs/ablations/`
2. Implement `src/ablation/run_ablation.py`
3. Create CI matrix for cross-runtime determinism
4. Add golden hashes reference

---

## Verification Checklist

For each paper element, implementation is complete when:
- [ ] Schema exists (if applicable) with 2020-12 + additionalProperties:false
- [ ] Implementation code exists with type hints
- [ ] Positive test exists (valid case passes)
- [ ] Falsification test exists (invalid case fails with correct reason code)
- [ ] CI gate exists (automated enforcement)
- [ ] Documentation references paper label (e.g., "implements Invariant 5.2")

---

**END OF PAPER_TO_IMPLEMENTATION_MAP.md**
