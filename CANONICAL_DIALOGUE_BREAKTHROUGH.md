# Canonical Dialogue Format: The Payload/Meta Split Breakthrough

**Date:** 2026-02-22 | **Status:** ✅ Implemented & Tested | **Reference:** SYSTEME_CODE v1.0.0

---

## The Problem: Determinism vs. Reality

Before this breakthrough, the system faced a core tension:

1. **Determinism requires:** Same input → Identical output (byte-for-byte, reproducible)
2. **Reality requires:** Wall-clock timestamps for audit trails and observability

**The conflict:** Including `timestamp_utc` in the hashed payload breaks determinism. Wall-clock time is never reproducible. But omitting timestamps entirely loses critical audit information.

**Previous approach:** Omit timestamps entirely, losing observability.

## The Solution: Split Records into Payload and Meta

**The breakthrough:** Every record is split into TWO parts:

- **PAYLOAD** (hash-bound, deterministic):
  - Fields that must be identical across runs
  - What gets hashed for proof
  - What validates determinism

- **META** (non-hash-bound, observational):
  - Timestamp_utc (wall-clock, non-deterministic)
  - Raw text blobs (for audit trail)
  - Operator notes
  - Anything that varies across runs but doesn't affect logic

**Result:** We can preserve real timestamps AND prove determinism. Best of both worlds.

---

## Implementation: Canonical Dialogue Event Structure

Every event in `town/dialogue.ndjson` follows this structure:

```json
{
  "type": "turn",
  "seq": 0,
  "payload": {
    "turn": 1,
    "hal": {
      "verdict": "PASS",
      "reasons_codes": ["ALL_K_GATES_VERIFIED", "LEDGER_COHERENT"],
      "required_fixes": [],
      "certificates": ["KTAU_OK", "RHO_OK"],
      "refs": {
        "run_id": "run-001",
        "kernel_hash": "aaaa...",
        "policy_hash": "bbbb...",
        "ledger_cum_hash": "cccc...",
        "identity_hash": "dddd..."
      },
      "mutations": []
    },
    "her_text": "All governance checks passed.",
    "channel_contract": "HER_HAL_V1"
  },
  "meta": {
    "timestamp_utc": "2026-02-22T23:30:00.000Z",
    "raw_text": "[HER]\n...\n\n[HAL]\n{...}"
  },
  "payload_hash": "f498e90b83a2724c...",
  "prev_cum_hash": "0000000000000000...",
  "cum_hash": "c7c9c509c2fe9d64..."
}
```

### Key Invariants

1. **`payload_hash = SHA256(Canon(payload))`**
   - Computed from PAYLOAD only
   - Never changes if PAYLOAD doesn't change
   - Deterministic by definition

2. **`cum_hash = SHA256(prev_cum_hash || payload_hash)`**
   - Hash chain that accumulates payload hashes
   - Same input → Same cum_hash across runs (PROOF OF DETERMINISM)
   - Breaks if any previous payload changed

3. **`timestamp_utc` in META, NOT in PAYLOAD**
   - Wall-clock time for audit trail
   - Excluded from hashing
   - Can vary across runs without breaking proofs

4. **`reasons_codes` are deterministic codes, not prose**
   - Use stable enumerations: `["ALL_K_GATES_VERIFIED", "LEDGER_COHERENT"]`
   - Never prose like `["All K-gates verified", "Ledger coherent"]`
   - Sorted lexicographically in payload

5. **Canonical JSON ensures deterministic serialization**
   - Keys sorted alphabetically
   - No whitespace
   - Floats in fixed format
   - No locale dependencies

---

## Three Determinism Issues: Fixed ✅

### Issue 1: Reasons Must Be Sorted Codes (Not Prose)

**Before:** Prose sentences that only happened to be alphabetical
```json
"reasons": ["All K-gates verified", "Ledger coherent"]
```
Problem: If you add `"Byzantine check passed"`, ordering breaks.

**After:** Stable, enumerated codes, always sorted
```json
"reasons_codes": ["ALL_K_GATES_VERIFIED", "BYZANTINE_DETECTION_OK", "LEDGER_COHERENT"]
```
Implementation: `normalize_reason_codes()` converts prose to codes and sorts.

**Test Result:** ✅ PASS - Same input produces identical sorted codes

---

### Issue 2: Timestamp Must Be Meta-Only (Not in Payload)

**Before:** Timestamp in payload breaks determinism
```json
{
  "turn": 1,
  "timestamp_utc": "2026-02-22T23:30:01.234Z",  // ❌ Non-deterministic!
  ...
}
```
Problem: Same logic, different wall-clock time → different hash.

**After:** Timestamp in meta, excluded from hashing
```json
{
  "payload": {
    "turn": 1,
    "hal": {...},
    ...
    // ❌ NO timestamp here
  },
  "meta": {
    "timestamp_utc": "2026-02-22T23:30:01.234Z"  // ✅ For audit trail only
  },
  "payload_hash": "...",  // computed from PAYLOAD only
  "cum_hash": "..."       // includes only payload_hash
}
```

**Test Result:** ✅ PASS - Same input twice (2 seconds apart) produces identical hashes

---

### Issue 3: Config Fields Must Match Your Actual Schema

**Before:** Config pointed to wrong field
```json
{
  "text_field": "text",          // ❌ Points to raw text blob
  "hal_object_field": "hal_parsed"
}
```

**After:** Config updated to match actual schema
```json
{
  "text_field": null,                    // ✅ Don't parse text blob
  "hal_object_field": "hal_parsed"       // ✅ Use parsed HAL object directly
}
```

File updated: `scripts/her_hal_detector_config.json` ✅

---

## Formal Guarantees

The split payload/meta architecture provides these guarantees:

| Guarantee | How It Works | Proof |
|-----------|-------------|-------|
| **Determinism** | Same payload → Same payload_hash → Same cum_hash | Run twice, compare cum_hash (identical) |
| **Non-repudiation** | cum_hash chain is immutable; tampering breaks chain | Alter any payload, cum_hash changes, breaking all subsequent hashes |
| **Auditability** | Timestamps in meta preserve observability | Read meta for when events occurred |
| **Reproducibility** | Payload-level replay can recreate exact states | Run with recorded payload sequence; output deterministic |
| **Composability** | K-τ, K-ρ, CouplingGate all bind to payload chain | Formal gates only validate payload hash integrity |

---

## Test Results

All tests in `test_canonical_dialogue.py` pass:

```
TEST 1: Payload/Meta Split
  ✅ timestamp_utc correctly placed in META (not PAYLOAD)

TEST 2: Determinism - Same Input Produces Same Hashes
  ✅ Same payload_hash despite different timestamps
  ✅ Same cum_hash (deterministic hash chain)

TEST 3: Reason Code Normalization & Sorting
  ✅ Prose → Codes conversion
  ✅ Lexicographic sorting

TEST 4: Canonical JSON Determinism
  ✅ Identical canonicalization across calls
```

---

## Integration: What Changed

### 1. **street1_runner_with_dialogue.py** (Rewritten)

**New features:**
- `build_canonical_dialogue_event()` - Creates payload/meta split events
- `normalize_reason_codes()` - Converts prose to codes, sorts
- Hash chain tracking: `get_last_cum_hash()`, `get_last_seq()`
- Cumulative hashing: every turn builds on previous

**Function signature:**
```python
def build_canonical_dialogue_event(
    turn: int,
    her_text: str,
    hal: Dict[str, Any],
    raw_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Build event with payload/meta split, hashing, cumulative chain."""
    ...
```

### 2. **Schemas Created**

- **`dialogue_event.canonical.schema.json`** - JSON Schema for the event structure
  - Defines payload, meta, hash fields
  - Validates HAL_VERDICT_V1 structure
  - Enforces lexicographic sorting rules

- **`hal_reason_codes.enum.json`** - Enumeration of stable reason codes
  - 50+ stable codes (never change)
  - Organized by category (determinism, gates, authority, etc.)
  - Canonical reason_code_registry (sorted)

### 3. **Validators**

**New NDJSON validator:** `her_hal_validate_ndjson.cjs`
- Reads `town/dialogue.ndjson` directly
- Validates event structure
- Verifies hash chain integrity (cumulative)
- Detects HER/HAL moments (veto + adaptation + continuity)
- Reports determinism proof status

**Usage:**
```bash
node scripts/her_hal_validate_ndjson.cjs
# or
node scripts/her_hal_validate_ndjson.cjs --file custom/dialogue.ndjson --moment-window 7
```

### 4. **Config File Fixed**

`scripts/her_hal_detector_config.json` updated:
```json
{
  "text_field": null,
  "hal_object_field": "hal_parsed"
}
```

---

## Next Steps (Immediate)

### 1. Run Canonical Format End-to-End

```bash
# Generate a test turn
cat > /tmp/test_turn.txt << 'EOF'
[HER]
Testing the canonical dialogue format.

[HAL]
{"verdict":"WARN","reasons_codes":["FORMAT_EXTRA_WHITESPACE"],"required_fixes":["TRIM_WHITESPACE"],"certificates":["KTAU_OK"],"refs":{"run_id":"test-001","kernel_hash":"aaaa...","policy_hash":"bbbb...","ledger_cum_hash":"cccc...","identity_hash":"dddd..."},"mutations":[]}
EOF

# Emit to runner
cat /tmp/test_turn.txt | python3 tools/street1_runner_with_dialogue.py

# Validate output
node scripts/her_hal_validate_ndjson.cjs
```

### 2. Test BLOCK → ADAPT Scenario (To Find Moment)

Create a 3-turn scenario:
- **Turn 1:** HELEN proposes to add timestamp to payload
- **Turn 2:** MAYOR BLOCK with reason `NONDETERMINISM_TIMESTAMP`
- **Turn 3:** HELEN revises to move timestamp to meta; MAYOR PASS

This will trigger the HER/HAL moment detector.

### 3. Run Full CI Pipeline

Once dialogue log has some events:
```bash
# K-τ coherence gate
python3 scripts/helen_k_tau_lint.py --run-id CANONICAL-PROOF

# K-ρ viability gate
python3 scripts/helen_rho_lint.py artifacts/rho_manifest.json ...

# Determinism sweep (multiple seeds, compare cum_hash)
bash scripts/street1_determinism_sweep_real.sh
```

---

## Why This Matters

This breakthrough solves the **fundamental tension in the system**:

- **Before:** You could have determinism OR observability, not both
- **After:** You can have both

**Implications:**
1. **Formal proofs bind to payload chain** — K-τ, K-ρ gates validate only deterministic data
2. **Real timestamps preserved** — Audit trails show when decisions occurred
3. **Reproducible experiments** — Same payload sequence → Same outcome (provable)
4. **Scalable CI** — Determinism sweeps can run 100+ times without losing timestamp data

**For your system:**
- HELEN can propose changes and know they're reproducible
- MAYOR can decide based on deterministic logic and immutable records
- Observers can see when events happened (meta timestamps) while proofs remain deterministic (payload hashes)

---

## Related Files

| File | Purpose |
|------|---------|
| `schemas/dialogue_event.canonical.schema.json` | Event structure + validation rules |
| `schemas/hal_reason_codes.enum.json` | Stable reason code enumeration |
| `tools/street1_runner_with_dialogue.py` | Rewritten with canonical format |
| `scripts/her_hal_validate_ndjson.cjs` | NDJSON format validator + moment detector |
| `scripts/test_canonical_dialogue.py` | Test suite (all pass ✅) |
| `scripts/her_hal_detector_config.json` | Updated config (fixed) |
| `SYSTEME_CODE v1.0.0` | Architectural specification (referenced throughout) |

---

## References

- **SYSTEME_CODE v1.0.0**
  - Section 1.3: Record shape (UNIVERSAL)
  - Section 4.2: Canonical turn event
  - Section 5.2: Validator B (NDJSON mode)
  - Section 8.2: Runtime bridge principle

- **Formal Invariants** (I1-I8)
  - I5: Deterministic Termination (empirical sweep)
  - I6: Anchor Chain (cum_hash as proof)
  - I8: No Hidden State (payload logging)

---

## Summary

✅ **Payload/Meta Split Implemented**
✅ **Timestamps in Meta, Hashing on Payload**
✅ **Reason Codes Deterministic & Sorted**
✅ **Cumulative Hash Chain Verified**
✅ **NDJSON Validator Created**
✅ **All Tests Passing**

**The system is now ready for determinism-aware dialogue logging and formal verification.**
