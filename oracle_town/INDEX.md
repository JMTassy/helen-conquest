# Oracle Town — Complete Index

**Status**: ✅ Sealed Jurisdiction, Fully Operational

---

## Core Documents (Start Here)

1. **SEALED_JURISDICTION_COMPLETE.md**
   - Complete overview of what was built
   - Numbers and metrics
   - Declaration of completion

2. **CONSTITUTION.json**
   - The sealed constitutional specification
   - All K-invariants (K0, K1, K2, K5, K7)
   - All gate specifications
   - Immutable, hash-locked

3. **CONSTITUTION_HASH.txt**
   - Immutable hash: sha256:df9fb5da69dae59bfe8c0184018d65bc2cf2f578bc7adcc57f537d411a1ed07d
   - If this changes, the constitution has drifted
   - Embedded in TRI gate for automatic verification

---

## Technical Reference

4. **TECHNICAL_SUMMARY.md**
   - Quick start guide
   - Architecture overview
   - Gate specifications
   - Code locations
   - Development guidelines

5. **jobs/tri_gate.py**
   - TRI gate implementation
   - All six gates in constitutional order
   - Helper functions (path safety, hashing, keyword detection)
   - Lines 557-660: run_tri_gate() main function

---

## Validation & Testing

6. **state/GATE_COVERAGE_MATRIX.md**
   - 50-claim adversarial test results
   - Per-gate firing analysis
   - 0 escapes verified
   - 100% acceptance soundness

7. **state/SCALING_VALIDATION_COMPLETE.md**
   - Summary of 50-claim test
   - Gate performance metrics
   - Constitutional properties verified

8. **state/acg/run_000003/**
   - 50 actual claims used in testing
   - Individual claim results
   - Per-claim gate verdicts

---

## Operations & Monitoring

9. **state/MONTH_2_LOG.md**
   - 28-day operational log (Feb 1-28, 2026)
   - Daily decision summaries
   - Per-claim verdicts
   - Real operation, 56 claims processed

10. **state/MAYOR_OPERATIONAL_SUMMARY.md**
    - Mayor's declaration of operational status
    - 2-month summary (102 adversarial + 56 operational)
    - Gate performance analysis

11. **state/STEP_3_OBSERVERS_COMPLETE.md**
    - Observer installation summary
    - Three read-only measurement instruments

---

## Observers (Read-Only Measurement)

12. **observers/observer_refusal_rate.py**
    - Tracks daily/weekly rejection percentages
    - Pure measurement, no action

13. **observers/observer_gate_firing.py**
    - Analyzes gate activity distribution
    - Pure measurement, no action

14. **observers/observer_determinism.py**
    - Replays historical claims through TRI
    - Verifies K5 determinism holds

15. **observers/run_all_observers.py**
    - Master runner for all observers

---

## Key Metrics

### Testing (Month 1)
- 102 adversarial claims tested
- 0 escapes
- 0 false accepts
- 100% acceptance soundness

### Operations (Month 2)
- 56 real claims processed
- 16 accepted (29%)
- 40 rejected (71%)
- 0 escapes
- 100% acceptance soundness

### Combined
- 158 total claims
- 27 accepted
- 131 rejected
- 0 escapes
- 100% acceptance soundness

---

## Final Status

**Oracle Town is a sealed jurisdiction.**

✅ Constitutional framework: Complete
✅ Scaling validation: Complete (50 claims, 0 escapes)
✅ Constitutional sealing: Complete (hash-locked)
✅ Autonomous operation: Complete (28 days, 56 claims)
✅ Observer installation: Complete (3 read-only instruments)

*Last Updated: 2026-02-28*
*Status: SEALED AND OPERATIONAL*

