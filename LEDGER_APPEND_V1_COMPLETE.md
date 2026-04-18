# LEDGER_APPEND_V1 — Complete

**Commit:** `32ed915`
**Date:** 2026-03-13
**Test Status:** 4/4 passing ✅
**Full Suite:** 32/32 passing (28 membrane + 4 ledger) ✅

---

## What This Increment Adds

LEDGER_APPEND_V1 bridges the membrane from stateless decision gate to institutional memory kernel.

**Before:** packet → reducer → state (decisions lost to time)
**After:** packet → reducer → state + ledger (decisions recorded for history)

---

## The Bridge

### What it does

1. **Accepts only SKILL_PROMOTION_DECISION_V1**
   - Rejects all other objects
   - Returns ledger unchanged on non-decision input

2. **Appends immutable entries**
   - One entry per decision
   - Entry has: index, decision, prev_hash, entry_hash
   - No entries are modified or deleted

3. **Preserves prior entries**
   - Each append leaves all previous entries intact
   - Ledger grows monotonically

4. **Computes deterministic entry hash**
   - Hash = SHA256(canonical(decision) + prev_hash)
   - Chain: each entry references the prior entry's hash
   - Same decision on same ledger → same entry hash (proof of determinism)

---

## Schema: DECISION_LEDGER_V1

```json
{
  "schema_name": "DECISION_LEDGER_V1",
  "schema_version": "1.0.0",
  "ledger_id": "string",
  "entries": [
    {
      "entry_index": integer,
      "prev_entry_hash": string | null,
      "decision": SKILL_PROMOTION_DECISION_V1,
      "entry_hash": "sha256:..."
    }
  ]
}
```

**Properties:**
- `entry_index` — Position in ledger (0-indexed, monotonic)
- `prev_entry_hash` — Hash of prior entry (None for first)
- `decision` — Complete reducer-emitted decision
- `entry_hash` — Deterministic chain hash

---

## Module: decision_ledger_v1.py

**Single function:**
```python
def append_decision_to_ledger(
    ledger: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
```

**Law:**
```
Only reducer-emitted, append-only decision records may extend governed history.
```

**Behavior:**
1. If decision is not SKILL_PROMOTION_DECISION_V1 → return ledger unchanged
2. If ledger schema invalid → return ledger unchanged
3. Otherwise → create new entry, append to ledger, return new ledger

**Immutability:** Always returns new dict, never modifies input.

---

## Tests (4 total)

### 1. Valid Decision Appends
- Proves: valid decision appends to empty ledger
- Checks: entry_index=0, prev_hash=None, entry_hash present

### 2. Invalid Object Does Not Append
- Proves: non-decision objects don't append
- Checks: ledger unchanged when given invalid schema

### 3. Appending Preserves Previous Entries
- Proves: multiple appends preserve all prior entries
- Checks: first entry hash unchanged, second entry prev_hash chains to first

### 4. Same Decision on Same Ledger = Same Hash
- Proves: determinism of entry hashing
- Checks: appending same decision twice → identical hashes

---

## What This Enables

### Replayable History

Once decisions are in the ledger, they can be:
- Audited (who decided, when, why)
- Traced (decision → state change → new decision)
- Replayed (same ledger prefix → same state evolution)
- Verified (cryptographically chain-checked)

### Institutional Memory

The membrane is no longer just a moment-in-time decision gate. It becomes:
- A decision journal
- An immutable record
- A foundation for rollback/replay
- A basis for federation (sharing ledger across kernels)

---

## Flow: Decision → Ledger → State

```
packet.json
    ↓ (validation)
validators.py
    ↓ (decision)
skill_promotion_reducer.py
    ↓ (SKILL_PROMOTION_DECISION_V1)
        ├→ apply_skill_promotion_decision()
        │       ↓ (state mutation)
        │  new state.json
        │
        └→ append_decision_to_ledger()
                ↓ (ledger append)
           decision_ledger.json
```

---

## Test Coverage

**Membrane (28 tests):**
- Determinism, failure routing, state mutation, reason codes, etc.

**Ledger Append (4 tests):**
- Valid append, invalid reject, preservation, determinism

**Total: 32/32 passing** ✅

---

## What This Is NOT

This increment:
- Does NOT implement ledger persistence (that's next)
- Does NOT implement ledger replay/rollback
- Does NOT implement federation
- Does NOT implement historical indexing

It is the minimal bridge from "decision gate" to "decision journal."

---

## What Comes After (Optional)

If ledger persistence is added:
1. **Ledger Persistence** — Write ledger to NDJSON file
2. **Ledger Replay** — Read ledger, replay decisions to recompute state
3. **Federation** — Share ledger across kernels with CROSS_RECEIPT_V1
4. **Rollback** — Revert to prior ledger position

But those are explicitly post-MVP enhancements.

---

## Authority Record

**Proven at this scope:**
- Append-only decision recording ✅
- Deterministic entry hashing ✅
- Chain integrity (prev_hash linking) ✅
- Immutability (no mutation of prior entries) ✅

**Not yet proven:**
- Persistence
- Replay
- Federation
- Rollback

**Status:** Ledger append layer complete and tested. Membrane now has memory.

---

**Commit:** `32ed915` — Add LEDGER_APPEND_V1: append-only decision history (4/4 green)
