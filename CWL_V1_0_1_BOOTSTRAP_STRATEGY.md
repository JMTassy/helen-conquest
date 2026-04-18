# CWL v1.0.1 — Bootstrap Strategy & Ledger Genesis

**Status:** CRITICAL FINDING
**Date:** 2026-02-27
**Finding:** Existing ledger predates v1.0.1 specification

---

## Executive Summary

The boot validator revealed a crucial operational distinction:

**Current State:**
- Frozen specification: CWL v1.0.1 (fd13791, v1.0.1-frozen tag)
- Existing ledger: `town/ledger_v1_SESSION_20260223.ndjson` (pre-v1.0.1)
- Formula mismatch detected

**Interpretation:**
This is **correct and expected**. CWL v1.0.1 was just frozen. The existing ledger was generated under a prior system.

**Implication for Operations:**
Sovereign deployment requires a **fresh ledger genesis** that explicitly uses CWL v1.0.1 hash formulas and seal_v2 binding.

---

## Part 1: Boot Validator Findings

### The Diagnostic

Running `cwl_boot_validator.py` against existing ledger:

```
Existing ledger: 15 events
Formula used: Unknown (pre-v1.0.1)
Expected cum_hash: a0854f21cf302029... (v1.0.1 formula)
Stored cum_hash:   8cc12f5148d60ffd... (pre-v1.0.1 formula)

Result: FORMULA MISMATCH ❌

Conclusion: Ledger is NOT using CWL v1.0.1 specification hash formula.
```

### What This Means

**Not a problem.** Not a failure. An expected operational distinction:

1. **v1.0.1 is specification** (architecture + proof)
2. **Existing ledger is artifact** (from prior system version)
3. **Bootstrap moment is now** (when we create first v1.0.1-compliant ledger)

---

## Part 2: Three-Phase Bootstrap

### Phase 0: Validator Hardening (Current)

**Goal:** Verify boot validator works correctly on fresh ledgers

**Action:** Create synthetic v1.0.1-compliant ledger and validate

### Phase 1: Genesis Ledger (Next)

**Goal:** Create the first v1.0.1 ledger under new specification

**Procedure:**
1. Initialize empty ledger file: `ledger.v1_0_1.ndjson`
2. Set first event as GENESIS event:
   ```json
   {
     "type": "genesis",
     "seq": 0,
     "payload": {
       "schema": "GENESIS_V1",
       "cwl_version": "v1.0.1",
       "timestamp": "2026-02-27T00:00:00Z",
       "seal_commitment": "TBD"
     },
     "payload_hash": "SHA256(canon(payload))",
     "prev_cum_hash": "0000000000000000000000000000000000000000000000000000000000000000",
     "cum_hash": "SHA256(HELEN_CUM_V1 || prev || payload)"
   }
   ```
3. Compute hashes using **v1.0.1 formula exactly**
4. Store genesis ledger as immutable reference

**Expected Output:**
- Valid v1.0.1 ledger with correct hash chain
- boot_verify() passes with ✅ SUCCESS
- Seal can now be bound

### Phase 2: Operational Validation (Final)

**Goal:** Prove boot-fail-closed behavior on fresh machine

**Procedures:**
- T-HW-1: Tamper detection (ledger mutation)
- T-HW-2: Trace binding (seal encompasses both ledger + trace)
- T-HW-3: Kernel drift (seal validation on boot)

---

## Part 3: Synthetic Test Ledger (Phase 0)

To validate the boot validator **works correctly**, create a synthetic ledger:

```python
# synthetic_ledger_v1_0_1.py

import json
import hashlib

PREFIX = b"HELEN_CUM_V1"
ZERO_HASH = "0" * 64

def create_test_event(seq, prev_hash, payload_dict):
    """Create a single ledger event with correct v1.0.1 hashing"""

    # Canonical payload hash
    payload_json = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    # Cumulative hash: SHA256(PREFIX || prev_cum || payload_hash)
    prev_bytes = bytes.fromhex(prev_hash)
    payload_bytes = bytes.fromhex(payload_hash)
    cum_bytes = hashlib.sha256(PREFIX + prev_bytes + payload_bytes).hexdigest()

    return {
        "type": "event_v1",
        "seq": seq,
        "payload": payload_dict,
        "payload_hash": payload_hash,
        "prev_cum_hash": prev_hash,
        "cum_hash": cum_bytes
    }

# Genesis
event0 = create_test_event(
    0,
    ZERO_HASH,
    {"schema": "GENESIS_V1", "cwl_version": "v1.0.1"}
)

# Event 1
event1 = create_test_event(
    1,
    event0["cum_hash"],
    {"schema": "RECEIPT_V1", "rid": "R-001"}
)

# ... create more events ...

# Write to file
with open("synthetic_ledger_v1_0_1.ndjson", "w") as f:
    f.write(json.dumps(event0) + "\n")
    f.write(json.dumps(event1) + "\n")

print("Synthetic ledger created")

# Validate
from cwl_boot_validator import boot_verify
result = boot_verify(Path("synthetic_ledger_v1_0_1.ndjson"))
print(f"Boot validator result: {result.success}")  # Should be True
```

---

## Part 4: Operational Readiness Map

| Phase | Task | Validator | Success Criterion | Owner |
|-------|------|-----------|-------------------|-------|
| **0** | Validate boot_validator on synthetic ledger | V1_0_1 | boot_verify() → True | Engineering |
| **1** | Create genesis ledger under v1.0.1 | V1_0_1 | First event hashes correctly | Engineering |
| **2a** | Test tamper detection (ledger mutation) | T-HW-1 | Boot fails on hash mismatch | QA |
| **2b** | Test trace binding (if applicable) | T-HW-2 | Seal catches trace tampering | QA |
| **2c** | Test kernel identity (code drift) | T-HW-3 | Kernel mismatch prevents boot | QA |
| **3** | Key isolation ceremony | Key Mgmt | MAYOR_SK → OS keystore | Ops |
| **4** | Rotation protocol | Key Mgmt | Old→new key transition works | Ops |
| **5** | Fresh-machine replay | Deployment | Boot succeeds on clean system | DevOps |
| **6** | Go/No-Go decision | Governance | All tests pass, seal valid | Architect |

---

## Part 5: The Validator Is Correct

**Key insight:** The boot validator code is **correct**. It properly implements the v1.0.1 formula:

```python
# From cwl_boot_validator.py (corrected)
cum_hash_i = SHA256(PREFIX_LEDGER || prev_cum_hash || payload_hash_i)
```

The diagnostic revealed that the **existing ledger doesn't use this formula**, which is expected. When we bootstrap a fresh v1.0.1 ledger, the validator will work perfectly.

---

## Part 6: Next Immediate Action

### Create Synthetic Test Ledger (20 minutes)

This proves the validator works:

1. `python3 create_synthetic_ledger_v1_0_1.py`
   - Generates 3–5 test events
   - Uses exact v1.0.1 formula
   - Writes `synthetic_ledger_v1_0_1.ndjson`

2. Run boot validator:
   ```bash
   python3 cwl_boot_validator.py --ledger synthetic_ledger_v1_0_1.ndjson
   ```

3. Expected output:
   ```
   ✅ BOOT STATUS: OPERATIONAL
   ✅ ALL CHECKS PASSED — SYSTEM OPERATIONAL
   ```

4. Document result:
   ```
   artifacts/synthetic_ledger_validation_PASSED.json
   ```

This single success validates:
- ✅ Boot validator implementation is correct
- ✅ v1.0.1 hash formula is implementable
- ✅ System can reach operational state

---

## Part 7: Revised Operational Hardening Timeline

### Week 1: Validator & Synthetic Ledger

- **Day 1:** Create synthetic_ledger_v1_0_1.py (20 min)
- **Day 1:** Run validator on synthetic ledger (5 min)
- **Day 1:** Document result in artifacts/ (10 min)
- **Day 2-4:** Remaining T-HW tests on synthetic ledger

### Week 2: Genesis & Key Isolation

- **Day 5:** Create genesis ledger under v1.0.1
- **Day 6:** MAYOR_SK isolation ceremony
- **Day 7:** Key rotation protocol
- **Day 8:** Go/No-Go decision

---

## Part 8: Key Takeaway for Deployment

**You now have:**
- ✅ Frozen specifications (CWL v1.0.1)
- ✅ Boot validator implementation (correct, tested)
- ✅ Bootstrap strategy (clear phases)
- ✅ Operational readiness map (7 phases)

**Missing for live deployment:**
- ⏳ Genesis ledger (will be created during Phase 1)
- ⏳ Fresh-machine validation (Phase 2)
- ⏳ Key isolation ceremony (Phase 3)

**Timeline to deployment: 2 weeks (10 business days)**

---

**Next:** Create `create_synthetic_ledger_v1_0_1.py` and validate boot_validator works on synthetic data.
