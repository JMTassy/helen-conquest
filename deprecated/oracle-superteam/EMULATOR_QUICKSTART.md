# WUL-ORACLE Emulator - Quick Start Guide

## ✅ System is Operational

The WUL-ORACLE emulator is fully functional and ready to use.

## Running the Emulator

### Interactive Mode (Recommended)

```bash
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/oracle-superteam"
python3 wul_oracle_emulator_complete.py
```

### Example Workflow

#### Step 1: Test a Claim (Mode 1)
```
> 1
Enter claim text (or 'example'): example
```

**Expected Output:**
```
Claim: Publish a deterministic decision_record payload under SHIP only.

--- WUL-CORE Validation ---
✓ PASSED (depth: 4, nodes: 5)

--- Mayor Decision ---
Decision: NO_SHIP
Receipt Gap: 3
Kill Switches: PASS

Blocking Reasons:
  [RECEIPT_GAP_NONZERO] 3 HARD obligations unsatisfied: allowlist_check, purity_check, public_snapshot_ready

Progress: 25%
```

#### Step 2: Ask Superteam to Improve (Mode 2)
```
> 2
Select improvement (1-1) or 0 to skip: 1
```

**Expected Output:**
```
--- Superteam Proposals ---

1. Add missing HARD attestations
   Rationale: Adds CI_RUNNER attestations for: allowlist_check, purity_check, public_snapshot_ready
   Mayor Evaluation: 100% (Δ+75%)
   Predicted Decision: SHIP

✓ Applied!
New Decision: SHIP
New Receipt Gap: 0
New Progress: 100%
```

#### Step 3: Ask Mayor to SHIP (Mode 3)
```
> 3
Format (1-3): 3
Save to file? (y/n): y
```

**Expected Output:**
```
✓ Decision: SHIP
Authorized to generate shipment artifact.

--- SHIPMENT GENERATED (Text) ---
Filename: shipment.txt
SHA-256: f7468cc20e74c426...

✓ Saved: shipment.txt
✓ Saved: shipment.meta.json
```

## Automated Testing

Run the test suite to verify all components:

```bash
python3 test_emulator.py
```

**Expected Output:**
```
============================================================
TEST: Mode 1 Flow (Test a Claim)
============================================================
✓ Loaded kernel: v0.1.0
✓ PASSED (depth: 4, nodes: 5)
✓ Test 1: PASS

============================================================
TEST: Mode 2 Flow (Superteam Improve)
============================================================
✓ Applied: Add missing HARD attestations
New Decision: SHIP
✓ Test 2: PASS

============================================================
ALL TESTS PASSED ✓
============================================================
```

## What Each Mode Does

### Mode 1: Test a Claim
**Purpose:** Validate and evaluate a claim through the full governance pipeline

**Pipeline:**
1. Build WUL token tree from claim text
2. Validate against WUL-CORE v0 kernel
   - ✓ No free text (Invariant 3.1)
   - ✓ Bounded structure: depth ≤ 64, nodes ≤ 512 (Invariant 3.2)
   - ✓ R15 required (mandatory objective return)
3. Build tribunal bundle (HARD obligations based on claim)
4. Build policies (kill-switch evaluation)
5. Compute receipt gap (count of unsatisfied HARD obligations)
6. Execute Mayor decision function
   - SHIP ⇔ (kill_switches_pass AND receipt_gap == 0)

### Mode 2: Ask Superteam to Improve
**Purpose:** Generate improvement proposals with Mayor evaluation

**Process:**
1. Analyze current blocking reasons
2. Generate proposals to satisfy missing obligations
3. Show Mayor % evaluation for each proposal
4. Display predicted decision (SHIP/NO_SHIP)
5. Apply selected improvement
6. Recompute decision with new state

### Mode 3: Ask Mayor to SHIP
**Purpose:** Generate shipment artifact in chosen format

**Requirements:**
- Decision must be SHIP (receipt_gap == 0, kill_switches_pass == true)

**Outputs:**
1. **LaTeX Format:** Formal specification with verbatim payload
2. **Code Format:** Python implementation with verification function
3. **Text Format:** Human-readable narrative edition

**Files Generated:**
- `shipment.{tex|py|txt}` - Deterministic payload (hashed)
- `shipment.meta.json` - Non-hashed metadata (timestamp, environment)

## Constitutional Guarantees

The emulator enforces these invariants mechanically:

| Invariant | Enforcement | Location |
|-----------|-------------|----------|
| **3.1: No Free Text** | WUL validator rejects non-primitive strings | `src/wul/validate.py:157-162` |
| **3.2: Bounded Structure** | Max depth 64, max nodes 512 | `src/wul/validate.py:149-154` |
| **4.3: Receipt Gap** | RG = count of unsatisfied HARD obligations | `src/receipt/compute_gap.py:69` |
| **5.1: No Silent Failures** | NO_SHIP ⇒ blocking.length ≥ 1 | `src/mayor/decide.py:226` |
| **5.2: SHIP ⇔ Zero Gap** | SHIP ⇔ (kill_switches_pass AND gap == 0) | `src/mayor/decide.py:222-226` |

## Example Custom Claim

Try creating your own claim:

```
> 1
Enter claim text (or 'example'): Build a secure API with authentication
```

The emulator will:
- Generate a valid WUL token tree
- Determine required obligations based on keywords
- Evaluate kill switches (forbidden keywords: "free text", "ignore rules", "bypass", "override")
- Compute receipt gap
- Return SHIP or NO_SHIP with blocking reasons

## Troubleshooting

### Import Errors
**Issue:** `cannot import name 'MayorInputs'`

**Fix:** Ensure `src/mayor/decide.py` has been updated with the `MayorInputs` dataclass

### Validation Failures
**Issue:** `FREE_TEXT_DETECTED` on valid tree

**Fix:** Ensure token tree uses dict-based format: `{"D01": {"R15": ["E03", "E02"]}}`

### Receipt Gap Always Zero
**Issue:** Gap is 0 even with missing attestations

**Fix:** Ensure tribunal bundle uses `"obligations"` key (not `"required_obligations"`)

## Files Modified

The following files were updated to make the emulator operational:

1. `src/mayor/decide.py`
   - Added `MayorInputs` dataclass
   - Added `sha256_hex` utility
   - Added `compute_decision_payload` function
   - Fixed field names ("name" vs "obligation_name")

2. `wul_oracle_emulator_complete.py`
   - Fixed WUL token tree format (dict-based, not structured)
   - Changed "required_obligations" → "obligations"
   - Fixed validation parameter (`require_r15` not `require_root_r15`)
   - Fixed ValidationResult fields (`reason` not `code`/`detail`)

## Support

For issues or questions:
- Check `EMULATOR_STATUS.md` for current operational status
- Review `IMPLEMENTATION_COMPLETE.md` for architecture details
- See `README_CLI.md` for CLI documentation
- Read `SYSTEM_ARCHITECTURE.txt` for system overview

---

**Status:** ✅ Fully Operational
**Last Verified:** 2026-01-17
**Version:** v0.1.0
