# WUL-ORACLE Interactive CLI

## Quick Start

```bash
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/oracle-superteam"
python3 wul_oracle_cli.py
```

## Features

The CLI provides three interactive modes for testing the complete WUL-ORACLE governance pipeline:

### Mode 1: Test a Claim
Validates and evaluates a claim through the full governance pipeline:
1. Build WUL token tree from claim
2. Validate against WUL-CORE v0 (bounded structure, no free text, R15 required)
3. Build tribunal bundle with HARD/SOFT obligations
4. Simulate superteam attestations
5. Compute receipt gap
6. Execute Mayor decision function

**Example:**
```
Select option (1-4): 1
Enter claim (or 'example' for pre-loaded claim): example
```

**Output:**
- Validation result (depth, nodes, R15 check)
- Tribunal obligations (HARD/SOFT)
- Receipt gap calculation
- Mayor decision (SHIP/NO_SHIP with blocking reasons)

---

### Mode 2: Ask Superteam to Improve
Simulates iterative improvement with Mayor evaluation:
1. Shows current blocking reasons
2. Generates improvement proposals from superteam
3. Displays Mayor's % evaluation of each improvement
4. Applies improvements and recomputes decision

**Example:**
```
Select option (1-4): 2
Apply improvements? (y/n): y
```

**Output:**
- Proposed improvements with impact analysis
- Mayor score (% improvement per proposal)
- Updated receipt gap after improvements
- New decision status

---

### Mode 3: Ask Mayor to SHIP
Generates final shipment artifact in chosen format:
1. LaTeX (formal specification)
2. Code (Python implementation)
3. Text (narrative edition)

**Example:**
```
Select option (1-4): 3
Format (1-3): 1
Save to file? (y/n): y
```

**Output:**
- Formatted shipment artifact
- SHA-256 hash
- Metadata file with timestamp and hashes

---

## Architecture

### Core Components

**WUL-CORE Validator** (`src/wul/validate.py`)
- Enforces Invariant 3.1: No free text
- Enforces Invariant 3.2: Bounded structure (depth ≤ 64, nodes ≤ 512)
- Checks arity against kernel registry
- Requires R15 (objective return)

**Receipt Gap Computation** (`src/receipt/compute_gap.py`)
- Implements Paper Definition 4.3
- Counts unsatisfied HARD obligations
- Returns typed reason codes

**Mayor Decision Function** (`src/mayor/decide.py`)
- Implements Invariant 5.2: SHIP iff (kill_switches_pass AND receipt_gap == 0)
- Pure function: same inputs → same output
- Enforces NO_SHIP → non-empty blocking array
- Splits output: deterministic payload + non-hashed metadata

**Kernel Registry** (`src/wul/core_kernel.json`)
- 5 discourse primitives (D01-D05)
- 7 entity primitives (E01-E07)
- 15 relation primitives (R01-R15)
- Governance constraints (max_depth, max_nodes, no_free_text)

---

## Example Session

```
WUL-ORACLE Interactive CLI
Receipt-First Governance for Multi-Agent Systems
Version: v0.1.0 | Paper: WUL_ORACLE_PAPER.tex

MAIN MENU
1. Test a Claim
2. Ask Superteam to Improve
3. Ask Mayor to SHIP
4. Exit

Select option (1-4): 1

MODE 1: TEST A CLAIM
Enter claim (or 'example' for pre-loaded claim): example

Step 1: Build WUL Token Tree
Token Tree:
{
  "D01": {
    "R15": ["E02", "E03"]
  },
  "objective_return": {
    "R15": ["E02", "E03"]
  }
}

Step 2: Validate Against WUL-CORE v0
✓ Validation PASSED
  - Depth: 2/64
  - Nodes: 5/512
  - Has R15: True

Step 3: Build Tribunal Bundle
Obligations: 4
  [HARD] wul_validation - validation
  [HARD] determinism_check - determinism
  [HARD] schema_validation - schema
  [SOFT] documentation - docs

Step 4: Simulate Attestations (Superteam)
Attestations received: 2

Step 5: Compute Receipt Gap
Receipt Gap: 2
✗ 2 HARD obligations unsatisfied:
  - determinism_check: HARD_OBLIGATION_UNSATISFIED
    ⚠ No attestation found for determinism_check
  - schema_validation: HARD_OBLIGATION_UNSATISFIED
    ⚠ No attestation found for schema_validation

Step 6: Mayor Decision
✗ Decision: NO_SHIP
⚠ Blocking reasons:
  [RECEIPT_GAP_NONZERO] 2 HARD obligations unsatisfied: determinism_check, schema_validation

Test Complete
Summary: NO_SHIP | Receipt Gap: 2 | Kill Switches: PASS
```

---

## Integration with Paper

The CLI directly implements formal elements from `WUL_ORACLE_PAPER.tex`:

| Paper Element | Implementation | File |
|---------------|----------------|------|
| Definition 3.1 (WUL token tree) | `validate_token_tree()` | `src/wul/validate.py` |
| Invariant 3.1 (No free text) | `no_free_text` check | `src/wul/validate.py:114` |
| Invariant 3.2 (Bounded structure) | Depth/node checks | `src/wul/validate.py:119-123` |
| Definition 4.3 (Receipt gap) | `compute_receipt_gap()` | `src/receipt/compute_gap.py:13` |
| Protocol 4.1 (Determinism split) | `emit_decision_with_meta()` | `src/mayor/decide.py:63` |
| Invariant 5.1 (No silent failures) | Blocking array logic | `src/mayor/decide.py:41-57` |
| Invariant 5.2 (SHIP implies zero gap) | Decision logic | `src/mayor/decide.py:60` |

---

## Reason Codes Emitted

The CLI uses canonical reason codes from `reason_codes.json`:

- `R15_INVALID` — Token tree missing R15
- `FREE_TEXT_DETECTED` — Free text found in hashed payload
- `DEPTH_EXCEEDED` — Tree depth > 64
- `NODE_COUNT_EXCEEDED` — Node count > 512
- `ARITY_MISMATCH` — Relation arity incorrect
- `HARD_OBLIGATION_UNSATISFIED` — HARD obligation not satisfied
- `ATTESTATION_INVALID` — Attestation signature invalid
- `POLICY_MATCH_FAILED` — Attestation doesn't match policy
- `RECEIPT_GAP_NONZERO` — Receipt gap > 0
- `KILL_SWITCH_FAILED` — Kill switch failed

---

## Testing

Run the validator directly:

```bash
cd src/wul
python3 validate.py
```

Expected output:
```
Valid tree: True, R15: True
Free text tree: False, Reason: FREE_TEXT_DETECTED
Deep tree: False, Reason: DEPTH_EXCEEDED, Depth: 70
```

---

## Next Steps

1. **Add Real Attestations:** Replace simulated attestations with actual verification
2. **Cross-Runtime Determinism:** Add Python 3.10/3.11/3.12 CI matrix
3. **Schema Integration:** Validate all artifacts against JSON Schema 2020-12
4. **Ablation Matrix:** Run A0-A6 ablations with survival length metrics
5. **UI Integration:** Connect CLI to web UI via API endpoints

---

## Files Created

```
oracle-superteam/
├── wul_oracle_cli.py                    # Interactive CLI (main)
├── src/
│   ├── wul/
│   │   ├── core_kernel.json             # WUL-CORE v0 kernel
│   │   ├── validate.py                  # Token tree validator
│   │   └── __init__.py
│   ├── receipt/
│   │   ├── compute_gap.py               # Receipt gap computation
│   │   └── __init__.py
│   └── mayor/
│       ├── decide.py                    # Mayor decision function
│       └── __init__.py
```

---

**Status:** ✅ Fully functional constitutional governance CLI
**Last Updated:** January 2026
