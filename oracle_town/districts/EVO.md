# EVO District Charter

**Module:** Evolution & Self-Adjustment

## Purpose

Monitor decision outcomes, detect policy inefficiencies, and propose threshold adjustments. EVO is the learner—it watches the town's performance and suggests how to get smarter (but never auto-applies changes).

## Inputs

**Required (read-only):**
- `oracle_town/ledger/decisions.jsonl` (all past decisions)
- `oracle_town/ledger/outcomes.jsonl` (optional: feedback on past decisions)
- `oracle_town/memory/index.json` (entity reference for context)
- Current policy config (gates, thresholds, attestor rules)

**No direct state mutations except policy proposals.**

## Outputs

**Artifacts produced:**
- `policy_patch.json` — Proposed threshold adjustments (never auto-applied)
- `evo_analysis.json` — Decision accuracy metrics + improvement suggestions
- `evo_receipt.json` — Cryptographic proof

**State mutations:**
- Writes to `city_current.json`: `modules.EVO.progress`, `modules.EVO.status`, `modules.EVO.desc`
- Appends to `oracle_town/ledger/artifacts.jsonl` (analysis metadata only)
- **Never writes to policy** (read-only; Mayor approval required)

## EVO Analysis Schema

```json
{
  "run_id": 173,
  "date": "2026-01-30",
  "decision_accuracy": {
    "period": "last_30_runs",
    "decisions_analyzed": 30,
    "ship_verdicts": 25,
    "no_ship_verdicts": 5,
    "outcomes_known": 18,
    "correct_decisions": 17,
    "accuracy": 0.944
  },
  "gate_efficiency": {
    "anomaly_threshold": {
      "current": "high",
      "sensitivity": 0.85,
      "false_positives": 2,
      "false_negatives": 1,
      "recommendation": "lower slightly to 0.90"
    }
  },
  "policy_patches": [
    {
      "gate": "anomaly_severity_high_threshold",
      "current_value": "high",
      "proposed_value": "medium_high",
      "justification": "Reduced false positives by 50% in simulation",
      "confidence": 0.87,
      "requires_approval": "tri_attestor_001"
    }
  ]
}
```

## Policy Patch Schema

```json
{
  "id": "patch_20260130_001",
  "run_id": 173,
  "date": "2026-01-30",
  "patches": [
    {
      "gate": "gate_name",
      "current": "value",
      "proposed": "value",
      "rationale": "string",
      "confidence": 0.87,
      "simulation_evidence": "path/to/sim_results.json",
      "requires_approval_from": ["attestor_id_1", "attestor_id_2"]
    }
  ],
  "status": "PROPOSED",
  "requires_manual_review": true
}
```

## Simulation & Evidence

**EVO must produce evidence for any proposal:**

1. Run synthetic decision scenarios with proposed thresholds
2. Compare outcomes to actual history
3. Measure improvement (accuracy, false positives, false negatives)
4. Store simulation results in `oracle_town/state/sim_day_*.json` (git-ignored)
5. Reference simulation in proposal

**Simulation files are deterministic** (K5 invariant) and git-ignored (I7 invariant).

## Gates (Enforced by EVO self-audit)

**EVO cannot propose patch unless:**
1. Analysis covers ≥20 past decisions
2. Proposed patch has ≥0.80 confidence from simulation
3. All patches reference evidence files
4. `evo_receipt.json` signed by evo_attestor_001
5. No patch auto-applies (all PROPOSED, awaiting Mayor review)

**Failure mode:** EVO produces WRN status; analysis available but no patch proposed.

## Determinism Contract

**EVO must guarantee:**
- Same decision history + same policy → identical analysis
- Simulation results deterministic (seeded RNG if needed)
- No timestamps (only run IDs and dates)
- Stable sorting: gate names alphabetical, patches sorted by gate

**Test:** Run EVO twice on same ledger; analysis hash must match.

## Forbidden Actions

- EVO may NOT auto-apply policy changes (only propose)
- EVO may NOT modify decision records or outcomes
- EVO may NOT write to other modules' state
- EVO may NOT call external ML services (must be deterministic local metrics)

## State Writes Allowed

```json
{
  "modules": {
    "EVO": {
      "status": "OFF|BLD|OK|WRN|FLR",
      "progress": 0-8,
      "desc": "string (max 50 chars)"
    }
  }
}
```

## Receipts Required

```json
{
  "evo_receipt": {
    "timestamp_unix": 1706601600,
    "decisions_analyzed": 30,
    "accuracy": 0.944,
    "patches_proposed": 3,
    "analysis_hash": "sha256:vwx234...",
    "run_id": 173,
    "attestor_id": "evo_attestor_001",
    "signature": "ed25519:pqr567..."
  }
}
```

**K0 enforcement:** Only evo_attestor_001 can sign EVO receipts.

## Policy Approval Flow

```
EVO proposes patch
  ↓
Mayor receives proposal (via city_current.json)
  ↓
Human reviews + manual decision
  ↓
If approved: Mayor writes override receipt + applies patch to policy
If rejected: Patch archived; next run proposes differently
```

**Critical:** No auto-application. All policy changes require explicit Mayor approval.

## Metrics Tracked

- **Decision Accuracy:** % of SHIP verdicts that led to successful outcomes
- **Gate Efficiency:** False positive / false negative rates per gate
- **Recommendation Coverage:** % of high-severity anomalies that led to insights
- **Precedent Relevance:** % of surfaced precedents that were actually actionable

## Integration with Daily OS

**Workflow step:**
```bash
python3 oracle_town/jobs/evo_adjust.py \
  --ledger oracle_town/ledger/decisions.jsonl \
  --policy oracle_town/core/policy.json \
  --simulation-dir oracle_town/state/ \
  --output artifacts/evo_analysis.json \
  --patch artifacts/policy_patch.json \
  --receipt artifacts/evo_receipt.json
```

**Non-blocking:** If EVO fails, town continues (WRN status). Patches archived for later review.

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
**Critical:** Proposals only. No auto-apply. Human judgment required.
