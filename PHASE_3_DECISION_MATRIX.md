# Phase 3: Decision Matrix (Post-Receipt)

**Status**: Awaiting L2 Artifact (Receipt)
**Authority**: HAL (Governance Layer)
**Date**: 2026-02-22

---

## Overview

After Phase 1 (receipt generation) completes, the metrics will indicate which of 4 paths to follow:

1. **L3_INJECTION** — Force adversarial feedback (strengthen narrative coherence)
2. **K_RHO_UPGRADE** — Harden kernel (fix contract layer)
3. **ENTROPY_TEST** — Controlled perturbation (measure resilience)
4. **ORACLE_FORECAST** — Strategic module for CONQUEST (optional next phase)

---

## Decision Tree

```
Receipt Generated
    ↓
[Overall Status = PASS?]
    ├─→ NO → [Schema errors or broken hashes present?]
    │         ├─→ YES → K_RHO_UPGRADE (fix kernel)
    │         └─→ NO → FAIL (stop, investigate)
    │
    └─→ YES → [Check Metrics]
              ├─→ synergy_index < 1.0 OR metacognition == 0?
              │   └─→ YES → L3_INJECTION (strengthen feedback)
              │
              ├─→ gwt_broadcast_score < threshold?
              │   └─→ YES → ENTROPY_TEST (measure resilience)
              │
              └─→ All metrics healthy
                  └─→ YES → ORACLE_FORECAST (next module, optional)
```

---

## Metric Thresholds

| Metric | Weak | Healthy |
|--------|------|---------|
| **synergy_index** | < 0.5 | ≥ 0.5 |
| **metacognition_index** | = 0 | ≥ 1 |
| **gwt_broadcast_score** | < 3 | ≥ 3 |
| **continuity_status** | FAIL | PASS |
| **overall_status** | FAIL | PASS |

---

## Escalation Paths

### Path 1: L3_INJECTION (Weak Feedback)

**Trigger**:
```
synergy_index < 1.0 OR metacognition_index == 0
```

**Diagnosis**: Agents are not referencing each other or correcting themselves.

**Action**:
1. Inject adversarial question into NPC reasoning
2. Force explicit contradiction in ledger
3. Measure if HELEN detects + corrects it
4. Recompute metrics
5. Confirm metacognition_index increases

**Success Criteria**:
- metacognition_index ≥ 1 after injection
- synergy_index ≥ 0.5 after injection
- overall_status = PASS

**Next**: If successful, move to ORACLE_FORECAST. If not, escalate to K_RHO_UPGRADE.

---

### Path 2: K_RHO_UPGRADE (Boundary Weakness)

**Trigger**:
```
continuity_status == FAIL OR schema_errors > 0
```

**Diagnosis**: Ledger has structural errors (broken hash chain, unknown types).

**Action**:
1. Tighten schema (reduce unknown types)
2. Reinforce hash chain (validate recompute more strictly)
3. Add required event type if needed
4. Re-run analyzer
5. Confirm overall_status = PASS

**Success Criteria**:
- No schema_errors
- continuity_intact = true
- overall_status = PASS

**Next**: If successful, re-evaluate metrics. If not, investigate logger.

---

### Path 3: ENTROPY_TEST (Low Broadcast)

**Trigger**:
```
overall_status == PASS AND gwt_broadcast_score < 3
```

**Diagnosis**: Agents are not reusing extracted facts in replies.

**Action**:
1. Inject controlled fact ("system:override_enabled")
2. Track if fact appears in subsequent NPC replies
3. Measure broadcast_score
4. Measure Lyapunov resilience (agent stays coherent despite perturbation)

**Success Criteria**:
- gwt_broadcast_score ≥ 3 after injection
- Agent replies remain coherent (no contradictions)
- overall_status = PASS

**Next**: If successful, move to ORACLE_FORECAST. If not, escalate to L3_INJECTION.

---

### Path 4: ORACLE_FORECAST (Optional Next Module)

**Trigger**:
```
overall_status == PASS AND synergy_index ≥ 0.5 AND
metacognition_index ≥ 1 AND gwt_broadcast_score ≥ 3
```

**Diagnosis**: All metrics healthy. System is ready for strategic module.

**What it is**: ORACLE_FORECAST module for CONQUEST

**Purpose**:
- Extend governance system (Oracle Town) to CONQUEST game
- Add predictive forecasting for game outcomes
- Embed decision-making via ledger receipts
- Test governance at scale (multi-agent strategy simulation)

**Architecture**:
```
CONQUEST (Game State)
    ↓
ORACLE_FORECAST (Prediction)
    ├─ Forecast cost/benefit of each action
    ├─ Propose risk-ranked moves
    ├─ Emit receipts (no execute without approval)
    └─ Ledger tracks all decisions
    ↓
Mayor Decision
    ├─ Accept forecast-ranked move → SHIP
    └─ Reject → ABORT + feedback to oracle
```

**Implementation Phases**:
1. **Phase A**: Export CONQUEST game state to ORACLE format
2. **Phase B**: Build ORACLE_FORECAST kernel (predictor)
3. **Phase C**: Integrate Mayor into decision loop
4. **Phase D**: Test on 100-run sample (verify governance stable)

**Success Criteria**:
- Oracle forecasts are >70% accurate (ex-post)
- All decisions logged + verifiable
- Determinism holds across 100 runs
- Mayor approval flow works without bottleneck

---

## How to Execute

### Step 1: Generate Receipt
```bash
python3 scripts/helen_metrics_analyzer.py
```

### Step 2: Check overall_status
```bash
cat runs/street1/interaction_proxy_metrics.json | jq '.indexes.overall_status'
# Expected: "PASS"
```

### Step 3: Read Metrics
```bash
jq '.indexes | {synergy_index, metacognition_index, continuity_status, overall_status}' \
  runs/street1/interaction_proxy_metrics.json
```

### Step 4: Apply Decision Matrix
- If overall_status = FAIL → **K_RHO_UPGRADE**
- Else if synergy_index < 1.0 → **L3_INJECTION**
- Else if gwt_broadcast_score < 3 → **ENTROPY_TEST**
- Else → **ORACLE_FORECAST**

### Step 5: Execute Escalation
See "Escalation Paths" above for specific steps.

---

## Example: Decision Flow

**Scenario**: Street1 session runs, HELEN computes metrics.

**Output**:
```json
{
  "indexes": {
    "synergy_index": 0.6,
    "metacognition_index": 2,
    "gwt_broadcast_score": 5,
    "continuity_status": "PASS",
    "overall_status": "PASS"
  }
}
```

**Decision**:
- overall_status = PASS ✅
- synergy_index = 0.6 ✅ (threshold is 0.5)
- metacognition_index = 2 ✅ (threshold is 1)
- gwt_broadcast_score = 5 ✅ (threshold is 3)

**Result**: All thresholds met → **ORACLE_FORECAST** (proceed to optional next module)

---

## Timeline

| Phase | Duration | Output |
|-------|----------|--------|
| Phase 1: Receipt Generation | ~30 min | interaction_proxy_metrics.json |
| Phase 2: Validation | ~15 min | overall_status check |
| Phase 3: Decision Matrix | immediate | escalation path determined |
| Phase 4: Escalation Execution | varies | L3_INJECTION, K_RHO, ENTROPY, or ORACLE |
| Phase 5: Post-Dive Actions | ~30 min | Re-run analyzer, compare hashes |

---

## Authority & No Branching Ambiguity

**Rule**: The receipt chooses the vector.

- No human discretion on "which path looks better"
- No negotiation on thresholds
- No "defer" option (all paths are executable)
- Deterministic: same receipt metrics → same path, every time

**Escalation rule**:
```
IF overall_status == FAIL
    THEN MANDATORY K_RHO_UPGRADE (no deviation)
ELSE IF synergy_index < 0.5 OR metacognition_index == 0
    THEN MANDATORY L3_INJECTION (no deviation)
ELSE IF gwt_broadcast_score < 3
    THEN MANDATORY ENTROPY_TEST (no deviation)
ELSE
    THEN OPTIONAL ORACLE_FORECAST (ready when you are)
```

---

## Next Steps (Immediate)

1. ✅ Hardened analyzer deployed (scripts/helen_metrics_analyzer.py)
2. ✅ CI gate created (scripts/ci_verify_street1_metrics.sh)
3. ⏳ **Awaiting**: Phase 1 execution (run analyzer on actual Street1 ledger)
4. ⏳ **Then**: Phase 2 validation (check overall_status)
5. ⏳ **Then**: Phase 3 decision (apply matrix)
6. ⏳ **Then**: Phase 4 escalation (execute path A, B, C, or D)

---

## Optional: ORACLE_FORECAST Module Details

If Phase 3 decision is **ORACLE_FORECAST**, the following module is specified and ready:

### What ORACLE_FORECAST Is
A predictive governance layer that:
- Forecasts outcomes of strategic actions
- Ranks moves by risk/reward
- Requires Mayor approval before execution
- Logs all decisions to ledger

### Where to Find Specification
`ORACLE_FORECAST_MODULE_SPEC.md` (to be created if escalation reaches this path)

### Expected Timeline
- Module spec: complete
- Implementation: 4-6 hours (Phase A-D)
- Testing: 2-3 hours (100-run determinism sweep)
- Deployment: CI integration ready

---

**Status**: Ready for Phase 1 (Receipt Generation)

**Execute now**: `python3 scripts/helen_metrics_analyzer.py`

**Then report**: overall_status + metrics for Phase 3 decision.
