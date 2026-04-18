# WUL-ORACLE: Constitutional Governance System

## Overview

This repository implements **WUL-ORACLE**, a receipt-first governance framework for multi-agent systems where outcomes are determined by validated artifacts rather than narrative interpretation.

---

## System Architecture

### Three Core Pillars

**1. Programs-as-Traces**
- Bounded WUL token trees compiled from agent messages
- No free text in receipt-hashed payloads
- Structural constraints: max depth 64, max nodes 512
- Mandatory objective anchoring (R15 operator)

**2. Receipts-as-Evidence**
- Deterministic artifact trail with SHA-256 hashes
- Payload/meta split: timestamps in non-hashed metadata only
- Receipt gap: count of unsatisfied HARD obligations
- Attestation ledger with policy matching

**3. Governance-as-Purity**
- Mayor decision function: pure, deterministic, recomputable
- Schema-enforced invariants (2020-12, `additionalProperties: false`)
- Closed-loop reason codes (30 canonical codes in allowlist)
- Three-gate validation: schema, allowlist, purity

---

## Document Navigation

### 📄 Formal Specification
**`WUL_ORACLE_PAPER.tex`** — LaTeX paper defining theorems, invariants, protocols
- Section 3: WUL-CORE v0 bounded symbolic kernel
- Section 4: Receipt discipline (hashed vs non-hashed split)
- Section 5: Mayor decision surface with schema invariants
- Section 6: Pipeline stages and artifact model
- Section 7: Falsification protocols (ablations, determinism checks)

**Compile:** `pdflatex WUL_ORACLE_PAPER.tex`

---

### 🗺️ Implementation Mapping
**`PAPER_TO_IMPLEMENTATION_MAP.md`** — Maps each paper element to concrete artifacts

**Status Overview:**
- ✅ **Completed:** Decision record schema, reason codes, NO_SHIP invariant tests
- ⚠️ **High Priority:** WUL-CORE kernel, validator, Mayor decision function, receipt gap computation
- ⚠️ **Medium Priority:** Tribunal bundle schema, run index schema, APIs
- ⚠️ **Low Priority:** Ablation infrastructure, cross-runtime determinism CI

---

### 🔧 Constitutional Documents

**Core Schemas (2020-12):**
- `schemas/decision_record.schema.json` — Mayor output with schema-enforced invariants
  - NO_SHIP ⇒ blocking non-empty (minItems: 1)
  - SHIP ⇒ blocking empty, receipt_gap=0, kill_switches_pass=true
  - `additionalProperties: false` throughout

**Reason Code Registry:**
- `REASON_CODES.md` — Single source of truth (30 codes, human-readable)
- `reason_codes.json` — Machine-readable allowlist for CI enforcement

**Determinism Contract:**
- `DECISION_RECORD_DETERMINISM.md` — Payload/meta split specification
  - decision_record.json: receipt-hashed (no timestamps)
  - decision_record.meta.json: audit metadata (timestamps allowed)

---

### 🧪 Test Suite

**Schema Enforcement:**
- `tests/test_mayor_no_ship_invariant.py`
  - NO_SHIP requires non-empty blocking array
  - SHIP requires receipt_gap=0, kill_switches_pass=true, empty blocking
  - Falsification tests: schema MUST reject violations

**Reason Code Enforcement:**
- `tests/test_reason_codes_allowlist.py`
  - All blocking codes must be in `reason_codes.json`
  - No typos, no ad-hoc codes
  - Allowlist integrity: no duplicates, valid format, sorted

**Fixtures:**
- `tests/fixtures/decision_record_ship.json` — Valid SHIP decision
- `tests/fixtures/decision_record_no_ship.json` — Valid NO_SHIP with blocking codes
- `tests/fixtures/decision_record.meta.json` — Non-hashed metadata schema

---

### 🖥️ UI Integration

**`UI_INTEGRATION_SPEC.md`** — Frontend/backend contract for MVP
- API endpoints: artifact storage, schema validation, receipt gap computation
- Component architecture: RunsListView, BriefcaseBuilderWizard, MayorDecisionPanel
- UX guardrails: freeze is one-way door, payload vs meta badges, reason code dropdowns
- Three-gate validation display: 📋 Schema, 📜 Allowlist, 🔐 Purity

**MVP Acceptance Criteria:**
- ✅ Concierge: create/freeze/dispatch briefcase
- ✅ Team packets: upload/merge/diff with reason codes
- ✅ Factory: attach artifacts, render stage cards
- ✅ Receipt gap: compute, display, navigate to missing obligations
- ✅ Mayor: upload/compute decision with three-gate validation
- ✅ Publish: emit public page with hash pointers

---

## Key Invariants (Mechanically Enforced)

### Invariant 3.1: No Free Text
> Any artifact classified as "receipt-hashed payload" MUST contain no untyped free-form natural language fields.

**Enforcement:**
- Schema: `additionalProperties: false`, typed fields only
- Test: `tests/test_no_free_text_in_hashed_payloads.py` (to be created)
- CI: Schema validation gate on all hashed artifacts

---

### Invariant 3.2: Bounded Structure
> All token trees must satisfy declared structural constraints (max depth, max nodes, max branching).

**Enforcement:**
- Kernel: `src/wul/core_kernel.json` governance section
- Validator: `src/wul/validate.py` depth/node checks
- Test: `tests/test_bounded_structure.py` (to be created)
- Reason codes: `DEPTH_EXCEEDED`, `NODE_COUNT_EXCEEDED`

---

### Invariant 5.1: No Silent Failures
> If decision is NO_SHIP, then blocking list must contain at least one typed reason code.

**Enforcement:**
- Schema: `"if": {"decision": "NO_SHIP"}, "then": {"blocking": {"minItems": 1}}`
- Test: `tests/test_mayor_no_ship_invariant.py::test_schema_rejects_no_ship_without_blocking`
- API: Upload validation rejects violations

---

### Invariant 5.2: SHIP Implies Zero Gap
> If decision is SHIP, then receipt_gap=0, kill_switches_pass=true, blocking=[].

**Enforcement:**
- Schema: `"if": {"decision": "SHIP"}, "then": {"receipt_gap": {"const": 0}, ...}`
- Test: `tests/test_mayor_no_ship_invariant.py::test_schema_rejects_ship_with_nonzero_receipt_gap`
- Mayor function: `src/mayor/decide.py` (to be created)

---

## Receipt Gap: Core KPI

### Definition
```
receipt_gap = count of unsatisfied HARD obligations
```

### Computation
```python
def compute_receipt_gap(tribunal_bundle, attestations_ledger):
    hard_obligations = [o for o in tribunal_bundle["obligations"] if o["severity"] == "HARD"]
    satisfied = [o for o in hard_obligations if is_satisfied(o, attestations_ledger)]
    return len(hard_obligations) - len(satisfied)

def is_satisfied(obligation, ledger):
    # True iff attestation_valid==True AND policy_match==1
    ...
```

### UI Integration
- **Primary KPI:** Displayed prominently on runs list and run detail top bar
- **Clickable:** Navigates to missing obligations list with reason codes
- **Color coding:** Green (0), Red (>0)

---

## Reason Code System

### Registry Structure

**Machine-Readable:** `reason_codes.json`
```json
{
  "version": "v0.1",
  "codes": [
    "R15_INVALID",
    "RECEIPT_GAP_NONZERO",
    "PURITY_VIOLATION",
    "NO_SHIP_WITHOUT_BLOCKING_CODES",
    ...
  ]
}
```

**Human-Readable:** `REASON_CODES.md`
- 30 canonical codes across 10 categories
- Each code has: description, policy, enforcement mechanism
- Single source of truth, version controlled

### Categories
1. WUL-CORE Validation (7 codes)
2. Bridge Validation (4 codes)
3. Receipt System (4 codes)
4. Mayor Purity (1 code)
5. Kill Switches (1 code)
6. Ablation Matrix (3 codes)
7. Cross-Runtime Determinism (2 codes)
8. Schema Validation (2 codes)
9. Tribunal Obligations (2 codes)
10. Mayor Invariant Violations (4 codes)

### Lifecycle
- **Adding codes:** Update REASON_CODES.md → regenerate reason_codes.json → CI enforces sync
- **Deprecating codes:** Mark `[DEPRECATED]`, maintain backward compatibility for 2 minor versions
- **Immutability:** Existing code semantics MUST NOT change (add new codes instead)

---

## Mayor Decision Surface

### Pure Decision Function
```python
def compute_decision(tribunal_bundle, policies, receipt_root_payload):
    """
    Pure function: decision = SHIP iff (kill_switches_pass AND receipt_gap == 0)
    """
    kill_pass = policies["kill_switches_pass"]
    rg = receipt_root_payload["receipt_gap"]

    if kill_pass and rg == 0:
        return {"decision": "SHIP", "blocking": [], ...}
    else:
        blocking = []
        if not kill_pass:
            blocking.append({"code": "KILL_SWITCH_FAILED", ...})
        if rg > 0:
            blocking.append({"code": "RECEIPT_GAP_NONZERO", ...})
        return {"decision": "NO_SHIP", "blocking": blocking, ...}
```

### Three-Gate Validation

**Gate 1: Schema Validation**
- JSON Schema 2020-12 with `allOf` invariants
- `additionalProperties: false` prevents bypass
- Rejects: missing fields, wrong types, invalid enums

**Gate 2: Reason Code Allowlist**
- All `blocking[].code` must be in `reason_codes.json`
- Prevents: typos, ad-hoc codes, undocumented codes

**Gate 3: Purity Check**
- Recompute decision from hashed inputs
- Must match actual decision output
- Prevents: hidden logic, discretionary overrides, smuggled inputs

### Output Split
- **decision_record.json:** Deterministic, receipt-hashed (no timestamps)
- **decision_record.meta.json:** Non-hashed audit metadata (timestamps, execution duration, hostname, git commit)

---

## Falsification Protocols

### Ablation Matrix

**Baseline (A0):**
- R15=ON, FreeText=OFF, Injection=CANONICAL
- Adversarial fraction: 0.2
- Horizon: 100 steps

**Kill Tests:**
- **A1:** Remove R15 → MUST fail with `R15_INVALID` within step 1
- **A2:** Allow free text → MUST degrade (measure survival length)
- **A3:** Random injection → Compare stability vs canonical

**Adversarial Tests:**
- **A4:** High adversarial fraction (0.5)
- **A5:** Long horizon (10000 steps)

**Acceptance Criteria:**
- A0 median runtime ≥ T_min (100ms)
- At least 2 ablations: med(ablation) ≤ 0.5 * med(A0)
- Kill tests fail as expected with correct reason codes

---

### Cross-Runtime Determinism

**Matrix:**
- Python: 3.10, 3.11, 3.12
- OS: Ubuntu, macOS
- Canonicalization: RFC 8785 (pinned)

**Golden Reference:** `ci/golden_hashes_v0.json`
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

**Enforcement:**
- CI runs baseline with seed=42 across matrix
- All hashes must match golden reference
- Mismatch → NO_SHIP with `GOLDEN_HASH_MISMATCH` reason code

---

## Implementation Roadmap

### Phase 1: Core Kernel (HIGH Priority)
- [ ] `src/wul/core_kernel.json` — Primitive registry
- [ ] `src/wul/validate.py` — Token tree validator
- [ ] `tests/test_bounded_structure.py` — Falsification tests
- [ ] `schemas/wul_token_tree.schema.json` — JSON Schema

### Phase 2: Mayor & Receipt Gap (HIGH Priority)
- [ ] `src/mayor/decide.py` — Pure decision function
- [ ] `src/receipt/compute_gap.py` — Receipt gap computation
- [ ] `tests/test_mayor_purity.py` — Recomputation test
- [ ] `tests/test_receipt_gap_computation.py` — Gap computation tests

### Phase 3: Schemas & APIs (MEDIUM Priority)
- [ ] `schemas/tribunal_bundle.schema.json` — Obligations structure
- [ ] `schemas/run_index.schema.json` — Run summary
- [ ] `backend/api/receipt_gap.py` — API endpoint
- [ ] `backend/api/run_index.py` — API endpoint

### Phase 4: Evaluation Infrastructure (LOW Priority)
- [ ] `configs/ablations/*.json` — Ablation configs
- [ ] `src/ablation/run_ablation.py` — Ablation runner
- [ ] `.github/workflows/cross_runtime_determinism.yml` — CI matrix
- [ ] `scripts/sync_reason_codes.py` — MD→JSON sync

---

## File Structure

```
oracle-superteam/
├── WUL_ORACLE_PAPER.tex                    # Formal specification (LaTeX)
├── PAPER_TO_IMPLEMENTATION_MAP.md          # Paper → code mapping
├── README_CONSTITUTIONAL_SYSTEM.md         # This file
├── DECISION_RECORD_DETERMINISM.md          # Payload/meta split
├── REASON_CODES.md                         # 30 canonical codes
├── UI_INTEGRATION_SPEC.md                  # Frontend/backend contract
│
├── schemas/
│   ├── decision_record.schema.json         # ✅ Mayor output (2020-12)
│   ├── tribunal_bundle.schema.json         # ⚠️ To be created
│   ├── run_index.schema.json               # ⚠️ To be created
│   └── wul_token_tree.schema.json          # ⚠️ To be created
│
├── reason_codes.json                       # ✅ Machine-readable allowlist
│
├── tests/
│   ├── test_mayor_no_ship_invariant.py     # ✅ Schema + falsification
│   ├── test_reason_codes_allowlist.py      # ✅ Allowlist enforcement
│   ├── test_bounded_structure.py           # ⚠️ To be created
│   ├── test_mayor_purity.py                # ⚠️ To be created
│   ├── test_receipt_gap_computation.py     # ⚠️ To be created
│   └── fixtures/
│       ├── decision_record_ship.json       # ✅ Valid SHIP
│       ├── decision_record_no_ship.json    # ✅ Valid NO_SHIP
│       └── decision_record.meta.json       # ✅ Non-hashed metadata
│
├── src/
│   ├── wul/
│   │   ├── core_kernel.json                # ⚠️ To be created
│   │   └── validate.py                     # ⚠️ To be created
│   ├── mayor/
│   │   └── decide.py                       # ⚠️ To be created
│   ├── receipt/
│   │   └── compute_gap.py                  # ⚠️ To be created
│   └── ablation/
│       └── run_ablation.py                 # ⚠️ To be created
│
├── configs/
│   └── ablations/                          # ⚠️ To be created
│       ├── A0_baseline.json
│       ├── A1_no_r15.json
│       └── ...
│
├── ci/
│   └── golden_hashes_v0.json               # ⚠️ To be created
│
└── backend/
    └── api/
        ├── receipt_gap.py                  # ⚠️ To be created
        └── run_index.py                    # ⚠️ To be created
```

---

## Quick Start

### 1. Validate Existing Schemas
```bash
# Install dependencies
pip install jsonschema pytest

# Run schema validation tests
pytest tests/test_mayor_no_ship_invariant.py -v
pytest tests/test_reason_codes_allowlist.py -v
```

### 2. Compile Paper (requires LaTeX)
```bash
pdflatex WUL_ORACLE_PAPER.tex
pdflatex WUL_ORACLE_PAPER.tex  # Run twice for references
```

### 3. Review Constitutional Documents
```bash
# Schema with invariants
cat schemas/decision_record.schema.json

# Reason codes registry
cat REASON_CODES.md
cat reason_codes.json

# Determinism contract
cat DECISION_RECORD_DETERMINISM.md

# Implementation mapping
cat PAPER_TO_IMPLEMENTATION_MAP.md
```

---

## Citation

If you use WUL-ORACLE in your research or project, please cite:

```bibtex
@techreport{tassy2026wuloracle,
  title={WUL--ORACLE: A Receipt-First Governance Framework for Deterministic, Auditable Multi-Agent Coordination},
  author={Tassy Simeoni, Jean Marie},
  institution={Lemuria Global / Oracle--Superteam},
  year={2026},
  month={January},
  address={Paris, France}
}
```

---

## License

Constitutional documents (schemas, specifications) are released under CC BY 4.0.
Implementation code is licensed under MIT (see LICENSE file).

---

## Contact

For questions, clarifications, or implementation support:
- Repository: `oracle-superteam/`
- Documentation: See `PAPER_TO_IMPLEMENTATION_MAP.md` for detailed mappings

---

**System Status:** Constitutional hardening complete. Core kernel and evaluation infrastructure in progress.

**Last Updated:** January 2026
