# STEP 3 — OBSERVERS INTRODUCED (Complete)

## What Are Observers?

Observers are **read-only epistemic instruments** that measure system behavior without influencing it.

**Key Property**: Observers *see*; they do not *act*. They reveal patterns without reintroducing optimism bias.

---

## Three Observers Deployed

### Observer 1: Refusal Rate Tracker

**File**: `oracle_town/observers/observer_refusal_rate.py`

**Measures**:
- Daily refusal rate (% of claims rejected)
- Weekly trends
- Per-gate refusal contribution
- Overall acceptance soundness

**Output**: Time-series data showing rejection frequency over days/weeks

**Interpretation**:
- Healthy range: 30-70% refusal
- Flat refusal rate indicates stable gatekeeping
- Sudden changes indicate new failure modes

### Observer 2: Gate Firing Entropy

**File**: `oracle_town/observers/observer_gate_firing.py`

**Measures**:
- Which gates are active (firing frequency)
- Gate firing entropy (Shannon entropy of gate distribution)
- Co-firing patterns (gates that fire together)
- Per-gate rejection load

**Output**: Statistical analysis of gate activity

**Interpretation**:
- Entropy > 2.0 indicates healthy diversity
- No single dominant gate is good (distributed load)
- Co-firing patterns reveal overlapping failure modes

### Observer 3: Determinism Verifier

**File**: `oracle_town/observers/observer_determinism.py`

**Measures**:
- Replayability: run historical claims through TRI, verify verdicts match
- K5 determinism verification
- Divergence detection

**Output**: Determinism verification report

**Interpretation**:
- 100% match rate confirms K5 holds
- Any divergence indicates nondeterminism in gates
- Enables full audit trail verification

---

## Master Observer Runner

**File**: `oracle_town/observers/run_all_observers.py`

**Purpose**: Execute all observers in sequence, collect results, produce integrated report

**Command**:
```bash
python3 oracle_town/observers/run_all_observers.py
```

**Output**: Integrated measurement report + JSON stats files

---

## Why Observers Instead of Learning?

**Alternative (Rejected)**: Add learning, scoring, adaptation
- Risk: Reintroduces optimism bias
- Risk: System "learns" to be wrong
- Risk: Constitutional boundaries soften

**Approach (Chosen)**: Observers measure without acting
- Pure measurement (no feedback loops)
- Reveals patterns without changing policy
- Allows discovery without corruption

---

## What Observers Cannot Do

- Suggest policy changes
- Adjust gate thresholds
- Recommend new evidence types
- Propose new claims
- Modify gate logic

Observers are **epistemic instruments**, not **control loops**.

---

## Integration with Constitutional Framework

Observers operate **outside** the constitution:
- They read ledger (immutable record)
- They produce reports (inform humans)
- They never touch gates, claims, or verdicts

This separation prevents: "The system can improve itself without human oversight."

---

## Next Steps (If Authorized)

Once observers are running:

1. **Collect baseline measurements** (run observers weekly)
2. **Establish normal operating ranges** (what does "healthy" look like?)
3. **Set alerting thresholds** (deviation from baseline triggers human review)
4. **Enable long-term trend analysis** (months/years of data)

But these are **read-only operations**. No feedback to the system.

---

## Declaration

**STEP 3 is complete.**

Three read-only observers are now deployed:
- Refusal rate tracking
- Gate firing analysis
- Determinism verification

The constitution remains sealed and unchanged.
Observers will run in parallel to the sealed system.
All measurements are logged but never act on the system.

**Status**: Ready for future operational metrics and long-term analysis.

---

*Observers introduced 2026-02-28*
*Constitution remains: Sealed, Operational, Verified*

