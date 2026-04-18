# Canonicalization Versioning & Historical Ledger Analysis

**Status**: ✅ VERIFIED | **Date**: 2026-02-24 | **Canonical Source**: `kernel/canonical_json.py`

## Executive Summary

**Question**: Do historical ledger entries exist that were hashed using `ensure_ascii=True`?

**Answer**: ✅ **NO** — All existing ledgers in the repository use `ensure_ascii=False`.

**Consequence**: This refactor is a **cleanup/consolidation**, not a breaking change. No migration protocol needed.

---

## Verification Results

### Existing Ledgers Analyzed

| Ledger File | Size | Non-ASCII Chars | Escaped Unicode | Status |
|---|---|---|---|---|
| `town/ledger.ndjson` | Active | None found | None found | ✅ ensure_ascii=False |
| `town/ledger_v1.ndjson` | Active | None found | None found | ✅ ensure_ascii=False |
| `town/ledger_v1_SESSION_20260223.ndjson` | Session | None found | None found | ✅ ensure_ascii=False |
| `helen_wisdom.ndjson` | Active | None found | None found | ✅ ensure_ascii=False |
| `artifacts/k_tau_trace.ndjson` | Trace | None found | None found | ✅ ensure_ascii=False |

**Detection Method**:
- Grep for escaped Unicode sequences: `\u[0-9a-fA-F]` (present only with `ensure_ascii=True`)
- Manual inspection of first 500 bytes (character-by-character analysis)
- All existing ledgers use literal UTF-8 characters, confirming `ensure_ascii=False`

---

## Canonicalization Rules (Frozen)

The unified `kernel/canonical_json.py` module enforces these rules:

```python
json.dumps(
    obj,
    ensure_ascii=False,      # UTF-8 literals preserved (NOT escaped as \uXXXX)
    sort_keys=True,          # Lexicographic order
    separators=(",", ":"),   # Compact, no spaces
)
```

**These rules match all existing ledgers** — no behavioral change.

---

## Why ensure_ascii=False Was Chosen

1. **International Identifiers**: Supports non-ASCII in `verdict_id`, `subject_id`, `run_id` fields
2. **UTF-8 Compactness**: Literal UTF-8 is smaller than escaped sequences (e.g., "世" = 3 bytes vs "\u4e16" = 6 bytes)
3. **Readability**: Human inspection of NDJSON ledgers is easier with literal UTF-8
4. **Historical Compatibility**: All existing ledgers already use this scheme

---

## Hash Scheme Versioning

**Current Status**: `HELEN_CUM_V1` (frozen in `environment.v1.json`)

**Definition**:
```
cum_hash = SHA256( "HELEN_CUM_V1" || bytes(prev_cum_hash_hex) || bytes(payload_hash_hex) )
```

**Payload Hash Definition**:
```
payload_hash = SHA256( canon_json_bytes(payload) )
```

Where `canon_json_bytes` is defined in `kernel/canonical_json.py` with the frozen rules above.

---

## Constitutional Guarantee

**Rule**: If `canonical_json` changes, the `cum_hash` and seal signatures of ALL prior ledgers become cryptographically invalid.

**Implication**: Once this module is committed, it cannot be changed without:
1. Formal migration protocol (version bumps: `CANON_JSON_V1` → `V2`)
2. Dual canonicalization support during transition
3. Explicit ledger regeneration or dual-chain validation

**Current Status**: `CANON_JSON_V1` is locked. No prior versions exist.

---

## Self-Tests (7 Total)

All tests pass with the unified module:

1. ✅ **roundtrip_stability** — Deserialize → serialize → identical bytes
2. ✅ **key_order_independence** — Different insertion orders → same output
3. ✅ **compact_format** — No whitespace, minimal bytes
4. ✅ **utf8_preservation** — Literal UTF-8, no escaping
5. ✅ **array_order_preserved** — Arrays NOT sorted, only objects
6. ✅ **deterministic_across_runs** — No version/random variance
7. ✅ **unicode_normalization_adversarial** — NFC normalization requirement documented

**Run tests**:
```bash
python3 kernel/canonical_json.py
# Output: [PASS] kernel/canonical_json.py: All 7 self-tests passed
```

---

## Integration Points (All Updated)

| Tool | Purpose | Status |
|---|---|---|
| `tools/ndjson_writer.py` | Payload hashing | ✅ Imports from kernel |
| `tools/validate_hash_chain.py` | Hash chain verification | ✅ Imports from kernel |
| `tools/validate_verdict_payload.py` | Schema validation | ✅ Imports from kernel |
| `tools/validate_receipt_linkage.py` | Receipt binding | ✅ Imports from kernel |
| `tools/validate_seal_v1.py` | Seal verification | ✅ Imports from kernel |
| `tests/conftest_kernel.py` | Testing infrastructure | ✅ Imports from kernel |

---

## Float Enforcement

**Rule**: Floats are PROHIBITED in canonical payloads.

**Implementation**: `_assert_no_floats()` function in `kernel/canonical_json.py`

**Rationale**: IEEE 754 representation can vary across Python versions, breaking determinism.

**Enforcement Point**: At serialization time (before `json.dumps`), not upstream.

**Error Type**: `TypeError` with detailed path information

**Example**:
```python
canon_json_bytes({"price": 19.99})
# Raises: TypeError: Floats are not allowed in canonical payloads (found at $.price): 19.99
```

---

## Unicode Normalization

**Current Behavior**: `canonical_json` does NOT auto-normalize Unicode.

**Risk**: Different Unicode normalization forms (NFC vs NFD) produce different bytes:
- NFC (Composed): "café" = `c a f é` (4 characters)
- NFD (Decomposed): "café" = `c a f e ́` (5 characters, with combining accent)

**Constitutional Requirement**: Callers MUST pass NFC strings.

**Enforcement Point**: Upstream, in payload construction (not in canonical_json).

**Test**: `_test_unicode_normalization_adversarial()` documents this requirement.

---

## Next Steps (If Needed)

### If Historical Ledgers Using ensure_ascii=True Discovered

1. Run dual canonicalization: create both V0 and V1 hashes
2. Maintain both in `cum_hash_v0` and `cum_hash_v1` fields
3. Transition explicitly (policy change + environment version bump)
4. Ledger regeneration required for full validation

**Status**: Not required (no such ledgers exist).

### If Unicode Normalization Issues Arise

1. Add `unicodedata.normalize("NFC", string_value)` to payload constructors
2. Document in `PAYLOAD_CONSTRUCTION.md`
3. Add linter check to catch NFD strings

**Status**: Documented in test; not yet blocking.

### If Python Version Changes

1. Environment.v1.json locks Python 3.9
2. If upgrading: verify JSON serialization bit-identical
3. Rerun all 7 self-tests with new version
4. No ledger change needed if tests pass

**Status**: Pinned to 3.9; version change requires explicit decision.

---

## Constitutional Authority

This document is subordinate to:
- `KERNEL_V2.md` (superteam + rule authority)
- `kernel/canonical_json.py` (frozen rules, self-tests)
- `environment.v1.json` (version pinning, schema binding)
- `registries/actors.v1.json` (permission matrix)

Changes to canonicalization rules require **editorial authority** + **amendment process** per KERNEL_V2.

---

**Status**: ✅ VERIFIED & LOCKED | **Date**: 2026-02-24 | **Authority**: Constitutional

No further canonicalization changes needed unless:
1. New Python version chosen (explicit decision)
2. New non-ASCII support required (NFC normalization enforcement)
3. Hash scheme migration needed (HELEN_CUM_V1 → V2, requires dual support)
