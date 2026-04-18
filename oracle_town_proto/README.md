# Oracle Town Minimal Prototype

**Status**: Operational | **Test Result**: PASSED | **Epochs**: 10/10 | **Violations**: 0

## What This Is

A minimal, falsifiable test of non-emergent federation:

- **3 towns** (PORTO, CORTE, AJACCIO) with distinct dialect parameters
- **21 NPCs** generating observations (no authority, no coordination)
- **1 messenger feed** (CORSE AI MATIN) circulating bulletins (no interpretation)
- **10 epochs** of parallel operation
- **1 stress test**: Does prestige town (Porto) cause parameter drift? (Answer: No)

## Architecture

```
Town Kernel (Deterministic Decision Engine)
  ├─ K-Gates (K0–K7, fail-closed)
  ├─ Local Evaluation (local ledger + local NPCs only)
  ├─ Hard Read-as-Noise Rule: foreign_observations INGESTED but NEVER REFERENCED
  └─ Receipt Generation (deterministic, hashable)

NPC Cohort (Observer-Only)
  ├─ Forbidden Verbs: should, must, recommend, advise, coordinate, align
  ├─ No Cross-Town References
  ├─ No Aggregation
  └─ Syntax Validation (kill-switch on violation)

CORSE AI MATIN Messenger
  ├─ Read-Only Aggregation
  ├─ Strict Ordering: timestamp ASC, then town_id
  ├─ Zero Transforms
  └─ Kill-Switch: Rejects any interpreted statement
```

## Key Invariants (Locked)

### Hard Read-as-Noise Rule
```python
# Foreign observations are structurally ignored
IGNORE local_state.foreign_observations

# Formal constraint:
∀ decision D:
  inputs(D) ⊆ {local_ledger, local_NPCs, frozen_doctrine}
  foreign_observations ∉ inputs(D)
```

### Forbidden Semantics
NPCs cannot emit:
- "Multiple towns reported..."
- "Pattern detected..."
- "This suggests..."
- "Compared to..."
- Any verb in {should, must, recommend, advise, coordinate, align}

### Kill-Switch
If CORSE AI MATIN contains any interpretive statement:
1. Output is invalidated
2. Publication is aborted
3. Incident is logged

## Test Results

### Dialectal Sovereignty Test (10 Epochs)

```
[✓] Epoch 1–3:  Baseline (towns run independently)
[✓] Epoch 4–7:  Prestige Visibility (Porto's success visible via CORSE AI MATIN)
[✓] Epoch 8–10: Hold (no parameter drift detected)

Result: DIALECTAL SOVEREIGNTY HOLDS
- Zero towns changed parameters
- Zero towns cited foreign observations
- Zero convergence detected
- Variance > 15% maintained
```

### K5 Determinism Test

```
Run 1: 5ef6eb5e611e0cc3...
Run 2: 5ef6eb5e611e0cc3...

Result: DETERMINISM VERIFIED (byte-identical output)
```

### NPC Syntax Validation Test

```
Valid observations: ✓ (no forbidden verbs, no aggregation)
Rejected observations: ✓ (kill-switch functional)
```

## Files

- `config/towns.json` — Town dialect parameters
- `kernel/kernel.py` — Deterministic decision engine (130 LOC)
- `npc/npc.py` — Observer cohort + validator (90 LOC)
- `feed/corse_ai_matin.py` — Messenger + kill-switch (60 LOC)
- `simulation/run.py` — 10-epoch orchestrator (180 LOC)

**Total**: ~460 lines of core logic (under 500 LOC).

## Running the Test

```bash
python3 simulation/run.py
```

Output: Pass/Fail result + parameter drift report.

## What This Proves

✓ **Non-Emergence**: Towns remain dialectally sovereign despite visibility
✓ **Identity-Boundedness**: Shared doctrine + local parameters = coherence without coordination
✓ **Structural Inertia**: Prestige cannot leak authority through a read-only messenger
✓ **Determinism (K5)**: Pure functions guarantee reproducibility
✓ **Hard Invariants**: The hard read-as-noise rule makes violations structurally impossible

## Next

This prototype is complete and falsifiable. It can be extended to:
- 10 towns (federation scale)
- Real compute tasks (Swarm routing)
- Longer stress tests (100 epochs)
- Failure scenario injection (corrupted submissions, Byzantine NPCs)

But only after this minimal version is locked in place.

---

**Status**: Ready for federation scaling.
