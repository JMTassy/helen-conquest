# HELEN OS — Autonomy Stack Complete

**Commits (Final):**
- `fac8fe8` — Add AUTORESEARCH_STEP_V1 (3/3 green)
- `32ed915` — Add LEDGER_APPEND_V1 (4/4 green)
- `537c9d1` — Freeze membrane baseline (28/28 green)

**Total Test Status:** 35/35 passing ✅

---

## The Stack

### Layer 1: Constitutional Membrane (28 tests)
✅ **Governance Core** (9 modules, 5 schemas)
- Deterministic canonicalization
- Schema validation (fail-closed)
- 6-gate reduction engine
- Typed failure routing
- Admitted-only state mutation
- Determinism proven (REPLAY_PROOF_V1)

**Law:** Only reducer-emitted decisions may mutate state.

---

### Layer 2: Append-Only Ledger (4 tests)
✅ **Decision Journal** (1 module)
- Accepts only SKILL_PROMOTION_DECISION_V1
- Appends immutable entries
- Preserves prior entries (never modifies history)
- Deterministic entry hashing (chain integrity)

**Law:** Only reducer-emitted, append-only decision records may extend history.

**Bridge:** Converts stateless decisions into historical ledger.

---

### Layer 3: Autonomous Research (3 tests)
✅ **Deterministic Autonomy Cycle** (1 module)
- Executes task (envelope)
- Types failure if any (failure_report)
- Builds promotion from typed failure
- Reduces through membrane (decision)
- Applies decision to state (next_state)
- All outputs deterministic (same input → same output)

**Law:** Autonomous exploration is allowed; only reducer-emitted, ledger-bound decisions may alter governed state.

**Key:** Autonomy of exploration ≠ autonomy of sovereignty. All state changes flow through reducer.

---

## The Flow

```
Task Input
    ↓
┌───────────────────────────────────────────────────┐
│ AUTONOMY CYCLE (autoresearch_step_v1)             │
│                                                   │
│ 1. execute_skill(task)                            │
│    ↓ (EXECUTION_ENVELOPE_V1)                      │
│                                                   │
│ 2. if failed: route_failure(...)                  │
│    ↓ (FAILURE_REPORT_V1 or None)                  │
│                                                   │
│ 3. if typed: build_promotion_packet(...)          │
│    ↓ (SKILL_PROMOTION_PACKET_V1)                  │
│                                                   │
│ 4. reduce_promotion_packet(...)                   │
│    ↓ (SKILL_PROMOTION_DECISION_V1)                │
│                                                   │
│ 5. apply_skill_promotion_decision(...)            │
│    ↓ (next_state)                                 │
│                                                   │
│ 6. DETERMINISM GUARANTEED                         │
│    (same task + same state → same output)         │
└───────────────────────────────────────────────────┘
    ↓
Optional: append_decision_to_ledger(...)
    ↓ (DECISION_LEDGER_V1)
    ↓
Next Task or Historical Replay
```

---

## Determinism at Each Layer

### Membrane (Layer 1)
Same packet + same state → same decision hash (PROVEN)

### Ledger (Layer 2)
Same decision + same prior ledger → same entry hash (PROVEN)

### Autonomy (Layer 3)
Same task + same state → same cycle output (PROVEN)

---

## What is Protected

✅ **Membrane prevents:**
- Untyped errors (fail-closed)
- Ad hoc reason codes (9 frozen)
- Invalid schemas (schema-enforced)
- Sovereignty leakage (typed boundary)
- State mutation without reducer approval

✅ **Ledger prevents:**
- Decision rewriting (append-only)
- History loss (all entries preserved)
- Unverifiable state (cryptographic chain)

✅ **Autonomy prevents:**
- Free mutation (all through reducer)
- Untyped failures (failure bridge)
- Proposal without evidence (promotion from failure only)
- Nondeterminism (same input → same output)

---

## What is NOT Included

❌ Ledger persistence (write to disk)
❌ Ledger replay/rollback
❌ Multi-step planning
❌ Agent loop daemon
❌ Chat interface with auto-mutation
❌ Skill evolution without receipts
❌ UI "intelligence"

These are explicitly deferred post-MVP. The stack does NOT become a "free agent."

---

## Architecture Summary

| Layer | Modules | Tests | Purpose | Law |
|-------|---------|-------|---------|-----|
| Membrane | 9 | 28 | Deterministic admission | Only reducer decisions mutate state |
| Ledger | 1 | 4 | Append-only history | Only reducer decisions extend history |
| Autonomy | 1 | 3 | Deterministic exploration | Only reducer decisions alter state |

**Total: 11 modules, 35 tests, 3 laws**

---

## The Claims

✅ **HELEN has an executable, deterministic kernel membrane for skill promotion.**
✅ **HELEN has append-only decision history for institutional memory.**
✅ **HELEN can autonomously execute tasks, propose improvements, and respect governance.**

---

## What This Means

HELEN is now:
- ✅ Deterministic (same input → same output, cryptographically proven)
- ✅ Type-safe (schemas enforce contracts at every boundary)
- ✅ Immutable (decisions never change, history preserved)
- ✅ Governed (all state changes flow through reducer)
- ✅ Exploratory (can execute tasks autonomously)
- ✅ Constrained (autonomy of exploration, not sovereignty)

HELEN is NOT yet:
- ❌ A full sovereign agent (requires persistence, replay, loop)
- ❌ A civilization runtime (requires federation, rollback, scheduling)
- ❌ "Free" (all state changes require reducer approval)

---

## The Stack is Frozen

No more features added without explicit increment. The three layers are:
1. **Membrane** — Decision gate (locked)
2. **Ledger** — History journal (locked)
3. **Autonomy** — Exploration cycle (locked)

Each layer respects the law of the layers below.

---

**Status:** HELEN autonomy stack is complete, tested, and determinism-proven.
**Authority:** Reduces risk through architectural layering, not elimination.
**Next:** If ledger persistence is wanted, add carefully (one module at a time).

---

Commit: `fac8fe8`
Date: 2026-03-13
Test Suite: 35/35 passing ✅
