# Week 1 Implementation Sprint — Federation Schema + Validator

**Sprint:** SPRINT_001_PATHV1_WK1
**Duration:** 5 days (Mon-Fri)
**Objective:** Lock federation schema, build + test validator

---

## **Daily Standup Format**

Each day ends with:
```
Date: YYYY-MM-DD
Standup:
  ✅ Completed: [task 1], [task 2]
  ⏳ In-progress: [task 3]
  🚧 Blocked: [if any]
  Commits: [N files changed, M commits]
```

---

## **Monday (Day 1): Schema Definition & Freeze**

### **Task 1.1: Finalize Cross-Receipt Schema** (2h)

**What:** Lock the JSON Schema that defines all cross-receipt messages between towns

**File to create:** `schemas/cross_receipt_v1.schema.json`

**Checklist:**
- [ ] Receipt ID pattern: `^XR_[A-Z]_[A-Z]_[0-9]{3}$`
- [ ] From/To town naming: `^Town_[A-Z]$`
- [ ] Ed25519 keys: `^[a-f0-9]{64}$`
- [ ] Signatures: `^[a-f0-9]{128}$`
- [ ] Receipt types enum: `["alliance_proposal", "trade", "proof_of_delivery", "intelligence", "treaty", "betrayal_notice"]`
- [ ] Seal_v3 structure: `{ledger_merkle_root, ledger_size, kernel_hash, env_hash}`
- [ ] Anti-replay ID: `^[A-Z]_[a-z_]+_[0-9]+$`

**Acceptance Criteria:**
- Schema valid per JSON Schema v7
- All properties documented
- No required field is missing
- Frozen (commit message: "FREEZE: cross_receipt_v1.schema.json")

**Deliverable:** `schemas/cross_receipt_v1.schema.json` (frozen)

---

### **Task 1.2: Create Test Vectors** (2h)

**What:** Define deterministic test cases that validator must pass/fail

**File to create:** `artifacts/federation_test_vectors_v1.json`

**Test cases to include:**
- [ ] Valid receipt (schema correct, signature valid)
- [ ] Invalid receipt (missing required field)
- [ ] Valid receipt with invalid signature
- [ ] Valid receipt with invalid seal
- [ ] Duplicate anti-replay_id (same RID twice)

**Acceptance Criteria:**
- 5+ test cases defined
- Each case has: input, expected_output, reason
- Deterministic (same test → same result)
- Frozen (commit: "FREEZE: federation_test_vectors_v1.json")

**Deliverable:** `artifacts/federation_test_vectors_v1.json` (5+ test vectors)

---

### **End of Day 1: Commit**

```bash
git add schemas/cross_receipt_v1.schema.json artifacts/federation_test_vectors_v1.json
git commit -m "FREEZE: Federation schema v1 locked with deterministic test vectors"
```

**Standup:**
```
Mon 2026-02-27
Standup:
  ✅ Completed: Schema frozen, test vectors defined
  ⏳ In-progress: Validator implementation starts Tue
  🚧 Blocked: None
  Commits: 2 files, 1 commit
```

---

## **Tuesday (Day 2): Validator Core Implementation**

### **Task 2.1: Schema Validator Class** (3h)

**What:** Build the validator that checks receipts against schema

**File to create:** `oracle_town/federation/cross_receipt_validator.py`

**Code structure:**
```python
class CrossReceiptValidator:
    def __init__(self, schema_path: str):
        # Load schema from JSON file

    def validate_schema(self, receipt: Dict) -> Tuple[bool, str]:
        # Check against JSON schema
        # Return (valid: bool, message: str)

    def validate_signature(self, receipt: Dict, vk: str) -> Tuple[bool, str]:
        # Verify Ed25519 signature
        # For MVP: deterministic test signature (no cryptography yet)

    def validate_all(self, receipt: Dict, vk: str) -> Dict[str, Any]:
        # Run all checks, return results
```

**Acceptance Criteria:**
- [ ] Validator loads schema without errors
- [ ] Valid receipts pass schema check
- [ ] Invalid receipts fail with specific error message
- [ ] Signature validation works (deterministically)
- [ ] Result dict contains: {schema_valid, signature_valid, admitted}

**Deliverable:** `oracle_town/federation/cross_receipt_validator.py` (working class)

---

### **Task 2.2: Unit Tests** (2h)

**What:** Test validator against test vectors

**File to create:** `tests/test_cross_receipt_validator.py`

**Tests to write:**
```python
def test_valid_receipt():
    # Valid receipt passes all checks

def test_invalid_receipt_missing_field():
    # Missing required field fails schema

def test_invalid_receipt_bad_pattern():
    # Field pattern mismatch fails

def test_signature_valid():
    # Correct signature passes

def test_signature_invalid():
    # Wrong signature fails
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] 100% code coverage (validator.py)
- [ ] Tests use frozen test vectors
- [ ] Deterministic (run 3x, all pass)

**Deliverable:** `tests/test_cross_receipt_validator.py` (5 passing tests)

---

### **End of Day 2: Commit**

```bash
git add oracle_town/federation/cross_receipt_validator.py tests/test_cross_receipt_validator.py
git commit -m "IMPL: Cross-receipt validator with 5 unit tests, all passing"
```

**Standup:**
```
Tue 2026-02-27
Standup:
  ✅ Completed: Validator class, 5 unit tests (all passing)
  ⏳ In-progress: Policy enforcement starts Wed
  🚧 Blocked: None
  Commits: 2 files, 1 commit
```

---

## **Wednesday (Day 3): Policy & Admissibility**

### **Task 3.1: Town Authorization Policies** (2h)

**What:** Define what each town allows/forbids

**Files to create:**
- `artifacts/federation_policy_town_a.json`
- `artifacts/federation_policy_town_b.json`

**Policy structure:**
```json
{
  "town_id": "Town_A",
  "allowed_issuers": [
    {
      "town_id": "Town_B",
      "vk": "vk_b_hex",
      "allowed_receipt_types": ["alliance_proposal", "trade"],
      "max_per_day": 10
    }
  ],
  "forbidden_receipt_types": ["ledger_mutation", "authority_claim"]
}
```

**Acceptance Criteria:**
- [ ] Town_A policy defined
- [ ] Town_B policy defined
- [ ] Policies reference each other (A allows B, B allows A)
- [ ] Forbidden types locked (authority_claim always forbidden)
- [ ] Frozen (commit: "FREEZE: federation_policy_town_*.json")

**Deliverable:** 2 town policies (frozen)

---

### **Task 3.2: Admissibility Checker** (2h)

**What:** Implement binary decision logic

**File to create:** `oracle_town/federation/admissibility.py`

**Code structure:**
```python
class AdmissibilityChecker:
    def __init__(self, town_policy: Dict):
        self.policy = town_policy
        self.seen_rids = set()  # Anti-replay cache

    def is_admitted(self, receipt: Dict) -> Tuple[bool, str]:
        # Binary decision: (True/"admitted" OR False/"reason")
        # Check 1: Issuer allowed?
        # Check 2: Type allowed?
        # Check 3: Not already seen (anti-replay)?
        # Check 4: Seal binding valid?
        # All must pass
```

**Acceptance Criteria:**
- [ ] All 4 checks implemented
- [ ] Anti-replay working (duplicate RIDs rejected)
- [ ] Policy enforcement working
- [ ] No partial trust (all ANDed)

**Deliverable:** `oracle_town/federation/admissibility.py` (working checker)

---

### **End of Day 3: Commit**

```bash
git add artifacts/federation_policy_town_*.json oracle_town/federation/admissibility.py
git commit -m "IMPL: Town policies + admissibility checker with anti-replay"
```

**Standup:**
```
Wed 2026-02-27
Standup:
  ✅ Completed: Town policies, admissibility checker
  ⏳ In-progress: Integration tests start Thu
  🚧 Blocked: None
  Commits: 3 files, 1 commit
```

---

## **Thursday (Day 4): Integration & Testing**

### **Task 4.1: Integration Tests (Schema + Validator + Policy)** (3h)

**What:** Test full pipeline: receipt → schema check → signature → policy → admit/reject

**File to create:** `tests/test_federation_integration.py`

**Test scenarios:**
```python
def test_clean_import():
    # Valid receipt, allowed type, correct signature → ADMITTED

def test_seal_spoofing():
    # Invalid seal → REJECTED

def test_policy_mismatch():
    # Type not in allowlist → REJECTED

def test_anti_replay():
    # Duplicate RID → REJECTED (second time)

def test_issuer_not_allowed():
    # From unauthorized town → REJECTED
```

**Acceptance Criteria:**
- [ ] All 5 scenarios passing
- [ ] Deterministic (run 3x, identical results)
- [ ] Clean output (no exceptions)
- [ ] Full audit trail (each step logged)

**Deliverable:** 5 passing integration tests

---

### **Task 4.2: Determinism Validation** (1h)

**What:** Prove validator is deterministic (no RNG, no time, no globals)

**File to create:** `tests/test_validator_determinism.py`

**Test:**
```python
def test_determinism():
    for i in range(10):
        result = validator.validate(same_receipt, same_vk)
        assert result == expected_result
```

**Acceptance Criteria:**
- [ ] 10 runs with same input → identical output
- [ ] No random element detected
- [ ] Validator uses only pure functions

**Deliverable:** Determinism proven (test passes 10 times)

---

### **End of Day 4: Commit**

```bash
git add tests/test_federation_integration.py tests/test_validator_determinism.py
git commit -m "TEST: Integration tests + determinism proof, all passing"
```

**Standup:**
```
Thu 2026-02-27
Standup:
  ✅ Completed: 5 integration tests, determinism verified
  ⏳ In-progress: Documentation + final audit Fri
  🚧 Blocked: None
  Commits: 2 files, 1 commit
```

---

## **Friday (Day 5): Documentation & Audit**

### **Task 5.1: Document Schema** (1h)

**What:** Write user-facing documentation

**File to create:** `docs/FEDERATION_SCHEMA_GUIDE.md`

**Content:**
- Explain each field in cross-receipt
- Show example valid receipt
- Show example invalid receipt
- Explain anti-replay mechanism
- Explain admissibility checks

**Acceptance Criteria:**
- [ ] All schema fields explained
- [ ] Examples are valid JSON
- [ ] Clear enough for auditor to understand

**Deliverable:** `docs/FEDERATION_SCHEMA_GUIDE.md`

---

### **Task 5.2: Audit Checklist** (1h)

**What:** Create checklist for independent auditor

**File to create:** `artifacts/WEEK_1_AUDIT_CHECKLIST.md`

**Checklist:**
```markdown
## SCHEMA COMPLIANCE
- [ ] Schema matches frozen spec (schemas/cross_receipt_v1.schema.json)
- [ ] All test vectors pass
- [ ] No breaking changes to schema

## VALIDATOR CORRECTNESS
- [ ] Valid receipts pass schema check
- [ ] Invalid receipts fail with specific error
- [ ] Signature validation working
- [ ] All 5 unit tests passing

## POLICY ENFORCEMENT
- [ ] Town policies defined and frozen
- [ ] Admissibility checker follows policy
- [ ] Anti-replay mechanism working
- [ ] Duplicate RIDs rejected

## DETERMINISM
- [ ] 10 runs with same input → identical output
- [ ] No RNG, no time, no globals in validator
- [ ] Pure function validation

## INTEGRATION
- [ ] 5 integration tests passing
- [ ] Clean error messages
- [ ] Full audit trail logged

## READINESS
- [ ] Documentation complete
- [ ] All code reviewed
- [ ] Ready for Week 2
```

**Acceptance Criteria:**
- [ ] All items checked ✅
- [ ] Zero blockers
- [ ] Approved for handoff to Week 2

**Deliverable:** Week 1 audit checklist (100% passing)

---

### **Task 5.3: Final Commit & Summary** (1h)

**What:** Final week 1 summary

**Files to commit:**
```bash
git add docs/FEDERATION_SCHEMA_GUIDE.md artifacts/WEEK_1_AUDIT_CHECKLIST.md
git commit -m "DOC: Federation schema guide + Week 1 audit checklist, all items passing"
```

**Create week summary:**

File: `artifacts/WEEK_1_SUMMARY.md`

```markdown
# Week 1 Summary: Federation Schema + Validator

**Status:** ✅ COMPLETE

## Deliverables
- [x] Cross-receipt schema v1 (frozen)
- [x] Deterministic test vectors (5+)
- [x] Cross-receipt validator (working)
- [x] Unit tests (5 passing)
- [x] Town authorization policies (2)
- [x] Admissibility checker (with anti-replay)
- [x] Integration tests (5 passing)
- [x] Determinism proof (10 runs identical)
- [x] Documentation
- [x] Audit checklist (100% passing)

## Metrics
- Lines of code: 400+ (validator + tests)
- Test coverage: 100% (validator.py)
- Determinism: ✅ Verified (10 runs)
- Commits: 5
- Files created: 12

## Readiness
- Week 2: Town-to-town protocol implementation
- Week 3: End-to-end federation testing
- Week 4: Audit & determinism validation

## Next Steps
Monday: Begin Task 1 of Week 2 (FederatedTown class)
```

---

### **End of Day 5: Final Commit**

```bash
git add artifacts/WEEK_1_SUMMARY.md
git commit -m "COMPLETE: Week 1 federation schema + validator, ready for Week 2"
```

**Final Standup:**
```
Fri 2026-02-27
Standup:
  ✅ Completed: Schema frozen, validator built, all tests passing
  ✅ WEEK 1 COMPLETE
  Metrics:
    • 400+ LOC
    • 10 tests passing
    • 100% test coverage
    • Determinism verified (10 runs)
  Next: Week 2 begins Monday (Town-to-town protocol)
  Commits: 5 files, 5 commits
```

---

## **Week 1 Success Criteria (All Must Pass)**

✅ **Schema**
- [ ] frozen (commit history shows FREEZE tag)
- [ ] matches spec exactly
- [ ] test vectors defined

✅ **Validator**
- [ ] loads schema without error
- [ ] passes all unit tests
- [ ] 100% code coverage
- [ ] deterministic (10 runs identical)

✅ **Policy**
- [ ] Town_A and Town_B defined
- [ ] mutually referencing (A allows B, B allows A)
- [ ] frozen

✅ **Admissibility**
- [ ] 4 checks (schema, signature, issuer, type)
- [ ] anti-replay working
- [ ] binary decision (admitted or rejected)

✅ **Testing**
- [ ] 5 unit tests + 5 integration tests
- [ ] all passing
- [ ] determinism proven

✅ **Documentation**
- [ ] Schema guide written
- [ ] Audit checklist 100% passing
- [ ] Ready for auditor review

✅ **Git**
- [ ] 5 clean commits
- [ ] no force-pushes
- [ ] clear messages

---

## **Files Created This Week**

```
schemas/
  └─ cross_receipt_v1.schema.json         (Frozen)

oracle_town/federation/
  ├─ cross_receipt_validator.py            (400 LOC)
  └─ admissibility.py                      (200 LOC)

artifacts/
  ├─ federation_test_vectors_v1.json       (Frozen)
  ├─ federation_policy_town_a.json         (Frozen)
  ├─ federation_policy_town_b.json         (Frozen)
  └─ WEEK_1_SUMMARY.md

tests/
  ├─ test_cross_receipt_validator.py       (5 tests)
  ├─ test_federation_integration.py        (5 tests)
  └─ test_validator_determinism.py         (1 test)

docs/
  └─ FEDERATION_SCHEMA_GUIDE.md

artifacts/
  └─ WEEK_1_AUDIT_CHECKLIST.md            (All items ✅)
```

---

## **Running Week 1 Locally**

```bash
# Setup
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
source .venv/bin/activate

# Run all Week 1 tests
pytest tests/test_cross_receipt_validator.py -v
pytest tests/test_federation_integration.py -v
pytest tests/test_validator_determinism.py -v

# Expected output: 11 tests passing ✅

# Check determinism (run 3 times)
python3 -m pytest tests/test_validator_determinism.py::test_determinism -v
python3 -m pytest tests/test_validator_determinism.py::test_determinism -v
python3 -m pytest tests/test_validator_determinism.py::test_determinism -v

# All 3 runs should have identical output
```

---

**Week 1: Ready to Execute** 🚀

**Start:** Monday (now, if you want)
**End:** Friday (this week)
**Deliverable:** Frozen schema + working validator

Ready?

---

Last Updated: 2026-02-27
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
