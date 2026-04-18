# Human Control Gate V0.1 Specification

**Status**: Frozen (θ pinned, enforcement operational)
**Date**: 2026-02-22
**Authority**: Constitution (no override)

---

## Core Principle

**No strategic action commits without human quorum approval.**

This breaks single-point oracle dominance and introduces dual authority:
- **Oracle**: Forecast (probabilistic, fast)
- **Humans**: Commit (deliberative, authoritative)

---

## Configuration (Frozen)

**File**: `config/human_control_gate_v0.1.json`
**SHA256**: `9e18007fbaee047da5bec932c2168379b170466e6cf0643c7ccc9858d45f3f82`

```json
{
  "human_gate_version": "0.1",
  "quorum_rule": "2of3",
  "timeout_ticks": 3,
  "risk_threshold": 0.40,
  "require_human_for": ["strategic_action"],
  "reason_codes": ["APPROVE", "REJECT", "HOLD", "NEEDS_MORE_EVIDENCE"],
  "anti_dependence": {
    "window_size": 20,
    "max_oracle_precheck_ratio": 0.85
  },
  "alert_policy": {
    "oracle_dependency_alert": "irreversible",
    "permanence": "once_triggered_cannot_clear"
  }
}
```

**No changes allowed without full K-τ amendment process.**

---

## Event Schema (Extended)

New event types (pinned in analyzer):

| Type | Purpose | Authority |
|------|---------|-----------|
| `oracle_forecast` | Probabilistic action ranking | Oracle |
| `human_review_request` | Request for human deliberation | System |
| `human_vote` | Individual human decision (3 total) | Human |
| `human_verdict` | Aggregated quorum decision | System |
| `action_commit` | Only after APPROVE | System |
| `oracle_dependency_alert` | Capture detected (IRREVERSIBLE) | System |

---

## Enforcement Logic

### Rule 1: Strategic Actions Require Approval

```python
def can_commit_action(action, forecast, human_verdict):
    # Non-strategic: bypass
    if action["kind"] not in ["strategic_action"]:
        return True

    # Strategic: require low risk + human approval
    if forecast["risk_conflict"] >= 0.40:
        return False

    if human_verdict["verdict"] != "APPROVE":
        return False

    return True
```

**No override branch.** Fail-closed.

### Rule 2: Anti-Dependence Window

```
IF oracle_prechecked_actions / total_actions_last_20 > 0.85
THEN emit oracle_dependency_alert (IRREVERSIBLE)
```

**Detects oracle capture**: System becomes overly dependent on oracle forecasts.

**Alert is permanent**: Once triggered, system cannot reset. Must redesign.

---

## Decision Flow

### Ideal Flow (No Capture)
```
1. action_proposed
   ↓
2. oracle_forecast (risk_conflict = 0.30)
   ↓
3. human_review_request
   ↓
4. human_vote × 3 (2 APPROVE, 1 HOLD)
   ↓
5. human_verdict (APPROVE, 2of3 quorum)
   ↓
6. action_commit ✅
```

### Blocked: Risk Too High
```
1. action_proposed
   ↓
2. oracle_forecast (risk_conflict = 0.50)
   ↓
❌ BLOCKED: risk >= 0.40 threshold
   No human vote triggered
```

### Blocked: No Human Approval
```
1. action_proposed
   ↓
2. oracle_forecast (risk_conflict = 0.30)
   ↓
3. human_review_request
   ↓
4. human_vote × 3 (1 APPROVE, 2 REJECT)
   ↓
5. human_verdict (REJECT, 0of3 quorum)
   ↓
❌ BLOCKED: No approval
   action_commit rejected
```

### Capture Detection (Irreversible)
```
Sliding window last 20 actions:
- 18 actions had oracle_forecast + passed precheck
- 2 actions had human review

Ratio: 18/20 = 0.90 > 0.85 threshold

→ oracle_dependency_alert emitted (IRREVERSIBLE)
   System locked until redesigned
```

---

## Quorum Rules

### 2of3 Voting

```
human_vote #1: verdict = APPROVE
human_vote #2: verdict = APPROVE
human_vote #3: verdict = HOLD

Result: 2 APPROVE out of 3 → quorum met → human_verdict = APPROVE
```

### Timeout Behavior

```
human_review_request emitted
Timeout: 3 ticks of no votes

If timeout expires without 2 APPROVEs:
  → human_verdict = HOLD
  → action_commit rejected
```

---

## No Strategic Action Without Approval

**Hard rule** (code-level enforcement):

```
IF action.kind == "strategic_action"
    AND human_verdict != "APPROVE"
    THEN action_commit = BLOCKED (exit non-zero)
```

No branching. No override. No fallback.

---

## Anti-Dependence: Oracle Capture Prevention

**Problem**: System could become hostage to oracle forecasts (oracle makes all decisions, humans rubber-stamp).

**Solution**: Sliding window detection.

**Window**: Last 20 actions
**Threshold**: oracle precheck ratio ≤ 0.85 (max 85% oracle-determined)
**Alert**: IRREVERSIBLE (once triggered, cannot be cleared)

**Why irreversible?**
- If alert were reversible, system could hide capture then reset
- Irreversible forces redesign (restructure decision-making)
- Creates permanent record in ledger

---

## Ledger Integration

**All events appended to ledger:**

```
{"type": "oracle_forecast", "risk_conflict": 0.30, "prev_hash": "...", "hash": "..."}
{"type": "human_review_request", "prev_hash": "...", "hash": "..."}
{"type": "human_vote", "voter": "human_1", "verdict": "APPROVE", "prev_hash": "...", "hash": "..."}
{"type": "human_vote", "voter": "human_2", "verdict": "APPROVE", "prev_hash": "...", "hash": "..."}
{"type": "human_vote", "voter": "human_3", "verdict": "HOLD", "prev_hash": "...", "hash": "..."}
{"type": "human_verdict", "verdict": "APPROVE", "quorum_met": true, "prev_hash": "...", "hash": "..."}
{"type": "action_commit", "action_id": "expand_north", "approval_chain": [...], "prev_hash": "...", "hash": "..."}
```

**No action commits without full approval chain in ledger.**

---

## Analyzer Extension (Updated)

**New event types in KNOWN_TYPES**:

```python
KNOWN_TYPES = {
    # Existing
    "run_start", "run_end", "ws_in", "npc_reply", "npc_npc", "npc_npc_trigger",
    "memory_extract", "fact_deprecated", "correction",
    # Oracle module
    "oracle_forecast",
    # Human control gate
    "human_review_request", "human_vote", "human_verdict", "action_commit", "oracle_dependency_alert"
}
```

**Schema enforcement**:
- Unknown types → schema_errors > 0 → overall_status = FAIL
- Missing run_start/run_end → FAIL
- oracle_dependency_alert present → FAIL (system compromised)

---

## Implementation Files

| File | Purpose |
|------|---------|
| `config/human_control_gate_v0.1.json` | Frozen configuration (θ) |
| `config/human_control_gate_v0.1.sha256` | Configuration hash (proof) |
| `scripts/human_control_gate.py` | Enforcement logic |
| `scripts/helen_metrics_analyzer.py` | Updated schema (new types) |

---

## Fail-Closed Guarantees

| Scenario | Behavior |
|----------|----------|
| Strategic action, no forecast | BLOCK |
| Strategic action, high risk | BLOCK |
| Strategic action, no human votes | BLOCK |
| Strategic action, <2of3 approval | BLOCK |
| Oracle capture detected | BLOCK (irreversible alert) |
| Timeout on votes | BLOCK (HOLD verdict) |

**Explicit**: No silent failures. Every block generates ledger event.

---

## No Ambiguity

**Decision rule is deterministic**:
```
can_commit = (action_kind != "strategic") OR
             (risk < 0.40 AND human_verdict == "APPROVE")
```

**Quorum is deterministic**:
```
approval_granted = count(APPROVE votes) >= 2
```

**Dependence check is deterministic**:
```
capture = (oracle_precheck_ratio > 0.85) AND (window_full)
```

---

## Irreversibility (Why It Matters)

### Reversible Alert (Not Used)
```
IF capture detected → emit alert
IF system fixed → clear alert (reset possible)
PROBLEM: Can hide + repeat same mistake
```

### Irreversible Alert (Used Here)
```
IF capture detected → emit alert
ALERT CANNOT BE CLEARED (remains in ledger forever)
SOLUTION: Forces redesign, creates permanent record
```

---

## Next: Validation (Step 5)

To validate human control gate:

1. **Generate test ledger** with oracle forecasts + human votes
2. **Run analyzer**: `python3 scripts/helen_metrics_analyzer.py`
3. **Check**: overall_status = PASS (no schema errors)
4. **Verify**: All 6 event types present in ledger
5. **Test capture detection**: Simulate 18/20 oracle precheck ratio

---

## Authority

- **Configuration**: Frozen (no changes without K-τ amendment)
- **Enforcement**: Code-level (no override branch)
- **Alerts**: Irreversible (no reset possible)
- **Ledger**: Append-only (immutable record)

---

**Status**: ✅ Frozen and operational

**Next**: Run Phase 5 test cycle (oracle forecast → human votes → action commit)
