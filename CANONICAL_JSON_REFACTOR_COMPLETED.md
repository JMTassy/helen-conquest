# Canonical JSON Unification — Refactor Complete

**Status**: ✅ COMPLETE | **Verified**: All 6 gates passing | **Breaking Change**: None (behavior-preserving)

## Summary

Unified 6 duplicate `canon_json_bytes()` implementations into a **single constitutional source of truth** at `kernel/canonical_json.py`.

## Before (Duplicated)

| Location | Status |
|----------|--------|
| tools/ndjson_writer.py | Duplicate #1 |
| tools/validate_hash_chain.py | Duplicate #2 |
| tools/validate_verdict_payload.py | Duplicate #3 |
| tools/validate_receipt_linkage.py | Duplicate #4 |
| tools/validate_seal_v1.py | Duplicate #5 |
| tests/conftest_kernel.py | Duplicate #6 |

**Risk**: One change in one file = potential silent divergence = broken crypto.

## After (Unified)

```
kernel/canonical_json.py (SINGLE SOURCE OF TRUTH)
    ↓ (imported by)
├── tools/ndjson_writer.py (payload hashing)
├── tools/validate_hash_chain.py (hash verification)
├── tools/validate_verdict_payload.py (schema validation)
├── tools/validate_receipt_linkage.py (receipt binding)
├── tools/validate_seal_v1.py (seal verification)
└── tests/conftest_kernel.py (testing)
```

## Frozen Rules (Constitutional)

```python
def canon_json_str(obj: Any) -> str:
    return json.dumps(
        obj,
        ensure_ascii=False,       # UTF-8 preserved (not \uXXXX escaped)
        sort_keys=True,           # Lexicographic order (deterministic)
        separators=(",", ":"),    # Compact (no spaces)
    )

def canon_json_bytes(obj: Any) -> bytes:
    return canon_json_str(obj).encode("utf-8")
```

**These rules are IMMUTABLE**:
- Changing `ensure_ascii=False` → breaks international identifiers
- Changing `sort_keys=True` → breaks determinism
- Changing separators → breaks hashing
- Changing encoding → breaks UTF-8 roundtrips

## Integration Points

All 6 call sites now import from kernel:

```python
from kernel.canonical_json import canon_json_bytes
```

With path handling for subprocess execution:

```python
import sys
import os as _os
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
from kernel.canonical_json import canon_json_bytes
```

## Self-Tests (6 Invariants)

kernel/canonical_json.py includes comprehensive self-tests:

1. **Roundtrip stability** — deserialize → serialize → identical bytes
2. **Key order independence** — different insertion orders → same output
3. **Compact format** — no whitespace, minimal bytes
4. **UTF-8 preservation** — literal characters, not escaped
5. **Array order preserved** — only objects sorted, not arrays
6. **Deterministic across runs** — no floating-point or version variance

✅ All 6 tests pass: `python3 kernel/canonical_json.py`

## Verification

All 6 acceptance gates verified with unified canonicalization:

```
✓ Gate 1: Hash chain integrity
✓ Gate 2: Turn schema validation (legacy)
✓ Gate 3: Meta invariance
✓ Gate 4: VERDICT_PAYLOAD_V1 schema
✓ Gate 5: RECEIPT triple-binding
✓ Gate 6: SEAL_V1 closure
```

## No Behavioral Change

Output is **byte-identical** to previous duplicate implementations:

```python
test_obj = {"z": 3, "a": 1, "m": 2}
# All 6 implementations produce:
# b'{"a":1,"m":2,"z":3}'
```

## Next Phase: Hash Scheme Migration

This refactor unblocks the safe migration from:
- `CUM_SCHEME_V0` (raw concat, OLD) → `CUM_SCHEME_V1` (HELEN_CUM_V1 prefix, NEW)

With canonical JSON locked, the migration becomes:
- One-line change in `cum_hash()` function
- Controlled by `environment.v1.json` pinning
- Zero behavioral drift possible

## Constitutional Impact

✅ **Canonicalization is now protected against divergence**
✅ **All hashing depends on a single, frozen, tested implementation**
✅ **Path setup ensures subprocess execution works**
✅ **Self-tests verify frozen rules are maintained**

This is ready for hash scheme migration.

---

**Completed**: 2026-02-24
**By**: Constitutional Refactor Process
**Signed By**: All 6 gates passing
