# Honest Enforcement Status
## What Is Actually Enforced (Receipt-Grade Only)

**Date:** 2026-01-22
**Audit Standard:** Only claim what CI enforces

---

## Receipt-Grade (Exit-1 Enforced)

| Test | Status | Command | Receipt |
|------|--------|---------|---------|
| 1. Mayor-only verdict output | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if non-Mayor writes decisions/ |
| 2. Factory emits attestations only | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if Factory contains SHIP/NO_SHIP |
| 3. Mayor dependency purity | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if Mayor imports creative/districts |
| 4. NO RECEIPT = NO SHIP | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if Mayor allows SHIP without receipts |
| 5. Kill-switch absolute priority | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if kill-switch doesn't block SHIP |
| 6. Replay determinism | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if decision digest changes |
| 7. Schema validation fail-closed | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if invalid payload not rejected |
| 8. Ledger chain integrity | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if tamper not detected |
| 9. Mayor I/O purity | ✅ **Enforced** | `python3 run_constitutional_tests.py` | Exits 1 if Mayor reads forbidden files |

**Test Run Receipt:**
```
$ python3 run_constitutional_tests.py
Result: 9/9 tests passed
🎉 ALL CONSTITUTIONAL TESTS PASSED
Exit code: 0
```

**What This Proves:**
- Tests run in actual environment (no pytest required)
- Tests fail with exit code 1 on violation
- jsonschema dependency installed and working
- AST-based enforcement (not keyword scanning)

---

## Spec-Grade (Module Exists, Not Wired)

| Component | Status | What Exists | What's Missing |
|-----------|--------|-------------|----------------|
| Schema validation | 📋 **Not wired** | `schema_validation.py` module | validate_or_raise() not called at boundaries |
| Ledger integration | 📋 **Not wired** | `ledger.py` module | Mayor.decide() doesn't read from ledger |
| CI receipt emission | 📋 **Not tested** | `emit_receipt_bundle.py` script | Not run in CI, no artifacts produced |

**Critical Gap:**
- **Test 7** proves `validate_or_raise()` **works**
- Does NOT prove `validate_or_raise()` is **called at boundaries**
- Mayor/Factory/Translator could bypass validation

---

## The "Kill Shot" Test (Not Yet Written)

**What We Need:** Test 10 - Boundary Validation Enforced

```python
def run_test_10_boundary_validation_enforced():
    """
    Test 10: Invalid payloads cannot reach Mayor through pipeline.

    This is the real enforcement test. Tests 7-9 prove tools work.
    Test 10 proves tools are wired into the system.
    """
    # 1. Create invalid Briefcase (missing required fields)
    invalid_briefcase = {"run_id": "TEST", "claim_id": "CLM"}  # Missing obligations

    # 2. Try to pass it through Mayor
    try:
        mayor = MayorV2()
        decision = await mayor.decide(invalid_briefcase, [])  # Should raise
        return False  # If we get here, validation was bypassed
    except SchemaValidationError:
        return True  # Validation blocked invalid input
```

**Status:** Not yet implemented.

**Why This Matters:**
Without Test 10, a developer could:
1. Import `MayorV2` directly
2. Pass raw dict instead of validated Briefcase
3. Bypass schema validation entirely

Test 10 proves: **No code path reaches Mayor without validation.**

---

## Honest Claims vs. Soft Claims

### ❌ Soft Claims (Not Yet True)

**Before (overclaimed):**
- "Schema validation is fail-closed" → Correct claim: "Schema validator works; not yet wired at boundaries"
- "Runtime enforcement complete" → Correct claim: "Runtime tests pass; boundaries not validated"
- "Production-ready" → Correct claim: "Test-ready; boundary validation pending"

### ✅ Honest Claims (Receipt-Grade)

**What I can defend under audit:**
1. **9 constitutional tests pass** (receipt: test run output above)
2. **Schema validator rejects invalid payloads** (receipt: Test 7 output)
3. **Ledger detects tampering** (receipt: Test 8 output)
4. **Mayor I/O purity enforced** (receipt: Test 9 AST scan)
5. **Tests run without pytest** (receipt: test run succeeded)
6. **jsonschema dependency installed** (receipt: Test 7 imported successfully)

**What I cannot claim:**
1. "Boundaries are validated" - No proof
2. "CI emits receipts" - Script exists but not run
3. "Mayor reads only ledger" - Ledger exists but Mayor doesn't use it yet

---

## The Determinism Caveat

**Test 6 claim:** "Replay determinism verified"

**What Test 6 actually proves:**
- Same Briefcase → same decision digest (excluding timestamps)

**What Test 6 does NOT prove:**
- Ledger entries have deterministic hashes (they include timestamps)
- Same inputs to Factory → same receipt bundle hash

**Honest language:**
- "Decision replay is deterministic (content-based, excluding timestamps)"
- NOT: "System is fully deterministic"

**If you want stronger determinism:**
Split hashes into:
- `content_sha256` - semantic hash (no timestamps)
- `entry_sha256` - audit hash (includes timestamps, for chain linking)

---

## Mayor I/O Test Bypass Scenarios

**Test 9 detects:**
- `open("ui_event_stream.json")`
- `Path("creative/output.json").read_text()`

**Test 9 does NOT detect:**
- `io.open(path)` - different import
- `builtins.open` aliasing
- `importlib.resources.read_text(...)`
- Dynamic paths: `open(f"{base_dir}/file.json")`

**Stricter enforcement (Option A):**
Mayor must NEVER do file reads. Period.
- Allow writing decision record only
- All inputs via in-memory objects (briefcase, attestations)

**Current enforcement (Option B):**
Mayor may open files in `decisions/` only (for writing)
- Test 9 checks literal paths only
- Can be bypassed with dynamic paths

**Recommended:** Option A (strict). No file reads in Mayor at all.

---

## Next Commits (Smallest to Receipt-Grade)

### Commit 1: Add Test 10 (Boundary Validation Enforced)
**Time:** 30 minutes
**Files:**
1. Add `run_test_10_boundary_validation_enforced()` to `run_constitutional_tests.py`
2. Wire `validate_or_raise()` into `MayorV2.decide()` (1 line at entry)
3. Wire `validate_or_raise()` into `Briefcase.__init__()` (fail at construction)

**Receipt:** Test 10 passes, proves validation cannot be bypassed.

---

### Commit 2: Make Mayor Read-Only (Strict I/O)
**Time:** 15 minutes
**Action:** Remove all `open()` calls from Mayor except decision write.

**Receipt:** Test 9 updated to ban ALL file reads in Mayor.

---

### Commit 3: Test CI Receipt Emission
**Time:** 10 minutes
**Command:**
```bash
python tools/emit_receipt_bundle.py
```

**Receipt:** `artifacts/receipt_bundle.json` created, validated, ledger chain verified.

---

## Bottom Line (Audit-Grade Truth)

**What is enforced (9/9 tests):**
- Constitutional tests: 6/6 passing ✅
- Enforcement tests: 3/3 passing ✅
- All tests run without pytest ✅
- All tests exit 1 on failure ✅

**What is tooling (exists but not wired):**
- Schema validation module ✅ (not called at boundaries)
- Ledger module ✅ (Mayor doesn't read from it)
- CI receipt emitter ✅ (not run in CI yet)

**What is missing (critical gaps):**
- Test 10 (boundary validation enforced) ❌
- Ledger integration with Mayor ❌
- CI receipt emission tested ❌

**Time to genuinely receipt-grade:** ~1 hour (3 commits above)

**Honest status label:** "Test-Ready, Boundary Validation Pending"

---

## References

### Test Receipts
- Test run output: See above (`9/9 tests passed`)
- Test source: `run_constitutional_tests.py` (lines 308-514 for Tests 7-9)
- Module source: `oracle_town/core/schema_validation.py`, `oracle_town/core/ledger.py`

### Overclaims Corrected
- ❌ "Production-ready" → ✅ "Test-ready"
- ❌ "Schema validation enforced" → ✅ "Schema validator works; not wired"
- ❌ "Runtime enforcement complete" → ✅ "Runtime tests pass; boundaries pending"

---

**Status:** 🔧 Test Infrastructure Complete, Boundary Wiring Pending (1 hour)
**Next:** Add Test 10, wire validation at boundaries, test CI receipt emission
**Contact:** JMT CONSULTING - Relevé 24
**Date:** 2026-01-22
