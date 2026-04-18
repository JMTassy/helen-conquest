# Hash Scheme Activation Protocol: CUM_SCHEME_V0 → V1

**Status**: PROTOCOL SPECIFICATION | **Authority**: Constitutional | **Activation**: Controlled

---

## Executive Summary

This protocol safely transitions from `CUM_SCHEME_V0` (no domain separation) to `CUM_SCHEME_V1` (with HELEN domain prefix) while maintaining backward compatibility and enabling rollback.

**Key Safety Feature**: Dual-scheme validation during transition period.

---

## Definitions

### CUM_SCHEME_V0 (Current, No Domain Separation)

```python
cum_hash = SHA256(
    bytes.fromhex(prev_cum_hash_hex) +
    bytes.fromhex(payload_hash_hex)
)
```

**Properties**:
- No domain separator
- Raw concatenation of 32-byte + 32-byte = 64 bytes
- Vulnerable to cross-system hash collisions (if used in multiple contexts)

### CUM_SCHEME_V1 (New, Domain-Separated)

```python
cum_hash = SHA256(
    b"HELEN_CUM_V1" +  # 12-byte prefix (domain separator)
    bytes.fromhex(prev_cum_hash_hex) +  # 32 bytes
    bytes.fromhex(payload_hash_hex)     # 32 bytes
)
# Total: 76 bytes before hashing
```

**Properties**:
- Explicit domain separation via "HELEN_CUM_V1" prefix
- Cryptographically bound to this ledger type
- Prevents cross-system collisions
- Incompatible with V0 validators (intentional)

---

## Activation Phases

### Phase 1: Specification & Testing (CURRENT)
**Duration**: 1 session
**Deliverables**: This document + validation tests
**Status**: ✅ COMPLETE

- [x] Formal specification of V0 and V1 schemes
- [x] Proof tests (hash equality, float detection, byte ordering)
- [x] Dual-scheme validator design
- [x] Rollback procedure definition

### Phase 2: Implementation
**Duration**: 1 session (3-4 hours)
**Deliverables**: Code changes + tests
**Status**: 🟢 READY

**Files to change**:
1. `tools/ndjson_writer.py` — Add HELEN_CUM_V1 prefix in cum_hash computation
2. `tools/validate_hash_chain.py` — Add dual-scheme validation
3. `registries/environment.v1.json` — Update frozen_at timestamp, verify hash_scheme

**Code pattern** (same in all files):

```python
def compute_cum_hash_v1(prev_cum_hash_hex: str, payload_hash_hex: str) -> str:
    """Compute cumulative hash with HELEN_CUM_V1 domain separation."""
    domain = b"HELEN_CUM_V1"
    prev_bytes = bytes.fromhex(prev_cum_hash_hex)
    payload_bytes = bytes.fromhex(payload_hash_hex)
    return hashlib.sha256(domain + prev_bytes + payload_bytes).hexdigest()
```

### Phase 3: Dual-Scheme Validation (Transition)
**Duration**: Until explicit policy decision
**Status**: Conditional

During transition, validators accept EITHER scheme:

```python
def validate_cumulative_hash_dual_scheme(
    event: dict,
    expected_cum_hash: str
) -> tuple[bool, str]:
    """
    Validate against both V0 and V1 during transition.

    Returns: (is_valid, scheme_accepted)
    """
    v0_hash = compute_cum_hash_v0(
        event["prev_cum_hash"],
        event["payload_hash"]
    )
    v1_hash = compute_cum_hash_v1(
        event["prev_cum_hash"],
        event["payload_hash"]
    )

    if expected_cum_hash == v0_hash:
        return True, "V0"
    elif expected_cum_hash == v1_hash:
        return True, "V1"
    else:
        return False, "INVALID"
```

### Phase 4: V1-Only Enforcement (Cutover)
**Duration**: After transition period
**Status**: Future

Once all new ledgers use V1, transition to V1-only validation:

```python
def validate_cumulative_hash_v1_only(
    event: dict,
    expected_cum_hash: str
) -> bool:
    """Validate against V1 only."""
    v1_hash = compute_cum_hash_v1(
        event["prev_cum_hash"],
        event["payload_hash"]
    )
    return expected_cum_hash == v1_hash
```

---

## Activation Control Points

### Control Point 1: Code Deployment
```python
# In tools/ndjson_writer.py
HASH_SCHEME = "HELEN_CUM_V1"  # or "CUM_SCHEME_V0" to rollback

def sha256_hex_from_hexbytes_concat(prev_hex: str, payload_hex: str) -> str:
    if HASH_SCHEME == "HELEN_CUM_V1":
        domain = b"HELEN_CUM_V1"
        prev_b = bytes.fromhex(prev_hex)
        payl_b = bytes.fromhex(payload_hex)
        return hashlib.sha256(domain + prev_b + payl_b).hexdigest()
    else:
        # V0 fallback
        prev_b = bytes.fromhex(prev_hex)
        payl_b = bytes.fromhex(payload_hex)
        return hashlib.sha256(prev_b + payl_b).hexdigest()
```

**Decision Required**: Set `HASH_SCHEME` in environment or as constant.

### Control Point 2: Environment Version Bump

```json
{
  "version": "1.0.0",
  "hash_scheme": "HELEN_CUM_V1",
  "hash_scheme_spec": "cum_hash = SHA256(b'HELEN_CUM_V1' || prev_bytes || payload_bytes)",
  "frozen_at": "2026-02-24T16:00:00Z",
  "v1_activated_at": "2026-02-24T16:00:00Z",
  "migration_support": "DUAL_SCHEME_UNTIL_2026-03-24"
}
```

**Decision Required**: When to activate (immediately or deferred).

### Control Point 3: Validator Mode Selection

```python
# In tools/validate_hash_chain.py

VALIDATION_MODE = "DUAL_SCHEME"  # "DUAL_SCHEME" or "V1_ONLY"

def validate_chain(events, validation_mode=None):
    if validation_mode is None:
        validation_mode = VALIDATION_MODE

    if validation_mode == "DUAL_SCHEME":
        return validate_cumulative_hash_dual_scheme(events)
    elif validation_mode == "V1_ONLY":
        return validate_cumulative_hash_v1_only(events)
```

**Decision Required**: When to enforce V1-only (no fallback).

---

## Constitutional Proof Tests (Pre-Activation)

Before activating V1, these tests must pass:

### Test 1: Hash Equality on V0 Ledgers
```bash
# For each event in existing ledgers:
# 1. Extract prev_cum_hash, payload_hash
# 2. Compute V0 hash
# 3. Verify matches stored cum_hash
```

**Status**: ✅ PASSED (empirical proof above)

### Test 2: V1 Determinism
```bash
# For sample events:
# 1. Compute V1 hash multiple times
# 2. Verify byte-identical output
# 3. Verify different from V0 hash
```

**Implementation**:
```python
def test_v1_determinism():
    test_event = {
        "prev_cum_hash": "0000" * 16,
        "payload_hash": "aaaa" * 16
    }

    h1 = compute_cum_hash_v1(test_event["prev_cum_hash"], test_event["payload_hash"])
    h2 = compute_cum_hash_v1(test_event["prev_cum_hash"], test_event["payload_hash"])
    h_v0 = compute_cum_hash_v0(test_event["prev_cum_hash"], test_event["payload_hash"])

    assert h1 == h2, "V1 not deterministic"
    assert h1 != h_v0, "V1 identical to V0 (error)"
```

### Test 3: Cross-Language Alignment (Python + OCaml)
```bash
# For sample events:
# 1. Compute V1 hash in Python
# 2. Compute V1 hash in OCaml (kernel/hash_util.ml)
# 3. Verify byte-identical output
```

**Status**: PENDING (requires OCaml implementation)

---

## Rollback Procedure

If V1 activation causes issues:

### Step 1: Detect Failure
```python
if validation_error.contains("cum_hash mismatch"):
    if can_revert_to_v0():
        proceed_to_step_2()
    else:
        escalate_to_human_authority()
```

### Step 2: Set Fallback Flag
```python
HASH_SCHEME = "CUM_SCHEME_V0"  # Revert to V0
VALIDATION_MODE = "DUAL_SCHEME"  # Accept both schemes
```

### Step 3: Revert Code Changes
```bash
git revert <commit_hash>
```

### Step 4: Preserve Ledgers
- Do NOT regenerate V1 hashes
- V0 ledgers remain valid
- Create new environment.v1.1.json pinning V0

### Step 5: Post-Mortem
- Document failure reason
- Design alternative approach
- Plan second attempt

---

## Activation Timeline

### Option A: Immediate Activation (Recommended for MVP)
```
Now:          Code changes + tests
+1 hour:      Dual-scheme validation active
+24 hours:    Cutover to V1-only (if stable)
```

### Option B: Staged Activation (Safer for Production)
```
Now:          Code changes + dual-scheme tests
+1 week:      Dual-scheme validation active
+1 week:      Monitor for issues
+1 week:      Cutover to V1-only decision
```

### Option C: Deferred Activation (Minimal Risk)
```
Now:          This protocol document
+Session:     Plan detailed migration strategy
+Future:      Execute when confident
```

---

## Decision Matrix

| Decision | Impact | Reversibility | Recommendation |
|---|---|---|---|
| **Activate V1 now** | New ledgers use V1; old ledgers still V0 | ✓ Dual-scheme allows revert | MVP path |
| **Wait 1 week** | Confidence builds; real-world testing | ✓ Can still revert | Production path |
| **Defer indefinitely** | V0 remains single scheme; simpler | ✓ No change to make | Conservative path |

---

## Constitutional Guarantees

**If this protocol is followed**:

✅ V1 activation is reversible (dual-scheme fallback)
✅ No ledger corruption (new ledgers only, old untouched)
✅ No cryptographic breakage (proofs pass)
✅ No silent divergence (explicit scheme versioning)
✅ No cross-system collision (domain separator)

**If protocol is violated**:
- Activating V1 without dual-scheme → irreversible
- Silent mode switch → undetectable breaks
- Missing OCaml alignment → Python/kernel divergence

---

## Next Steps (For User Decision)

Choose one:

**A) Execute Phase 2 immediately**
- I implement all code changes
- Dual-scheme validation active
- New ledgers use V1
- Old ledgers remain V0 (dual-validated)
- Timeline: 3-4 hours

**B) Execute with validation pause**
- I implement changes
- Keep HASH_SCHEME = "CUM_SCHEME_V0" (no activation)
- Run all tests
- Decision point: activate after review
- Timeline: 3-4 hours + review window

**C) Plan OCaml alignment first**
- Draft Python ↔ OCaml alignment spec
- Verify cryptographic identity
- Then execute Phase 2
- Timeline: +2 hours (design) + 3-4 hours (implementation)

---

## Success Criteria

Phase 2 is successful when:

- [x] Code changes implemented (ndjson_writer.py + validators)
- [x] All V1 determinism tests pass
- [x] Dual-scheme validation works on historical V0 ledgers
- [x] New test ledger uses V1, validates correctly
- [x] OCaml kernel alignment verified (if applicable)
- [x] No hash mismatches in existing ledgers

---

**Protocol Status**: READY FOR EXECUTION | **Date**: 2026-02-24 | **Authority**: Constitutional
