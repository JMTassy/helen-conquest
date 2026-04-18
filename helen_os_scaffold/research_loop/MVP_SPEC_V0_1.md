# HELEN RESEARCH LOOP — MVP SPECIFICATION v0.1

**Status:** FROZEN FOR IMPLEMENTATION
**Core Law:** `NO_RECEIPT = NO_SHIP`
**Memory Rule:** Only SHIPped state is optimization memory.
**Frozen Date:** 2026-03-10

---

## 1. THE FIVE FROZEN CONSTANTS

| Constant | Value |
|---|---|
| **Domain** | Retrieval/Ranking code optimization (`ranker.py`) |
| **Metric** | `top1_accuracy` — scalar, frozen benchmark |
| **Budget** | 300s wall clock · 1 editable file · 1 proposal/cycle |
| **Manifest** | `RUN_MANIFEST_V1` (hash-chained, append-only) |
| **Verdict** | `SHIP` / `NO_SHIP` / `QUARANTINE` — reducer-only, gate-first |

Do not reopen any of these until the 20-cycle milestone is achieved.

---

## 2. MASTER LAW

```
proposal ≠ admission ≠ sealed truth

generated content → candidate event → validated receipt → reduced state → observable truth
```

Nothing counts until it crosses the receipt boundary.

---

## 3. ARTIFACT SET (7 artifacts — frozen)

### 3.1 `MISSION_V1`

```json
{
  "mission_id": "MIS_001",
  "domain": "retrieval_ranking",
  "objective": "Maximize top-1 retrieval accuracy on frozen benchmark.",
  "metric_name": "top1_accuracy",
  "maximize": true
}
```

Invariant: `domain` is always `"retrieval_ranking"` for this MVP.

---

### 3.2 `PROPOSAL_V1`

```json
{
  "proposal_id": "PROP_001",
  "proposer": "HER",
  "summary": "< 200 chars",
  "hypothesis": "< 500 chars",
  "mutable_files": ["ranker.py"],
  "replay_command": "python eval.py --seed 42 --dataset frozen_eval.jsonl"
}
```

Invariants:
- `mutable_files` has exactly 1 entry: `"ranker.py"`.
- `proposer` is always `"HER"`.
- `replay_command` is the literal command used for verification.

---

### 3.3 `EXECUTION_RECEIPT_V1`

```json
{
  "receipt_id": "RCP_001",
  "kind": "command | metric | test",
  "command": "python eval.py --seed 42 --dataset frozen_eval.jsonl",
  "stdout_sha256": "<64 hex chars>",
  "stderr_sha256": "<64 hex chars>",
  "artifact_refs": ["metric:top1_accuracy=0.847"]
}
```

Invariant: `stdout_sha256` and `stderr_sha256` are SHA-256 of the captured output.

---

### 3.4 `EVIDENCE_BUNDLE_V1`

```json
{
  "evidence_id": "EV_001",
  "dataset_hash": "<sha256 of frozen_eval.jsonl>",
  "metric_name": "top1_accuracy",
  "metric_value": 0.847,
  "receipt_ids": ["RCP_001", "RCP_002"],
  "notes": []
}
```

Invariant: all `receipt_ids` must exist in the manifest's receipt list.

---

### 3.5 `ISSUE_LIST_V1`

```json
{
  "issue_list_id": "ISSUES_001",
  "issues": [
    {
      "issue_id": "ISS_001",
      "severity": "low | medium | high | blocker",
      "code": "TIMEOUT_RISK",
      "message": "Run took 290s of 300s budget."
    }
  ]
}
```

Invariant: any issue with `severity == "blocker"` sets `G_no_blocking_issue = False`.

---

### 3.6 `VERDICT_V1`

```json
{
  "verdict": "SHIP | NO_SHIP | QUARANTINE",
  "blocking_reason_codes": []
}
```

Allowed reason codes:
```
MISSING_RECEIPTS
REPLAY_FAILED
METRIC_NOT_IMPROVED
BLOCKING_ISSUE
KERNEL_INTEGRITY_FAILED
```

Invariant: `SHIP` carries zero blocking codes. `NO_SHIP` carries at least one.

---

### 3.7 `RUN_MANIFEST_V1` (the sovereign artifact)

```json
{
  "manifest_version": "RUN_MANIFEST_V1",
  "manifest_id": "MAN_001",
  "ts_utc": "2026-03-10T12:00:00Z",
  "mission": { "...": "MISSION_V1" },
  "proposal": { "...": "PROPOSAL_V1" },
  "receipts": [ "...EXECUTION_RECEIPT_V1..." ],
  "evidence": { "...": "EVIDENCE_BUNDLE_V1" },
  "issues": { "...": "ISSUE_LIST_V1" },
  "gates": {
    "G_receipts_present":    true,
    "G_replay_ok":           true,
    "G_metric_improved":     true,
    "G_no_blocking_issue":   true,
    "G_kernel_integrity_ok": true
  },
  "verdict": { "...": "VERDICT_V1" },
  "parent_manifest_hash": "<sha256 of previous manifest | genesis zeros>",
  "config_hash":           "<sha256 of frozen config>",
  "environment_hash":      "<sha256 of frozen environment manifest>",
  "model_digest":          "<sha256 of model weights / version pin>",
  "manifest_hash":         "<sha256 of all above fields, canonical JSON>"
}
```

Invariant: `manifest_hash = SHA256(canonical_json(all_fields_except_manifest_hash))`.
Invariant: `parent_manifest_hash` points to the previous admitted manifest, or `"0" * 64` for genesis.

---

## 4. GATE VECTOR

```
G_receipts_present    = all required receipts are present and valid
G_replay_ok           = strict deterministic replay (see §4.1)
G_metric_improved     = metric_value >= best_admitted_metric + 0.002
G_no_blocking_issue   = no issue with severity == "blocker"
G_kernel_integrity_ok = manifest_hash verifies deterministically
```

### 4.1 G_replay_ok — Frozen Deterministic Replay Definition

`G_replay_ok = True` if and only if re-running `proposal.replay_command` under
the frozen environment produces **all** of the following:

| Field | Condition |
|---|---|
| `exit_code` | equals the originally recorded exit code (`0` for success) |
| `metric_after` | equals the originally recorded `evidence.metric_value` exactly |
| `stdout_sha256` | equals the originally recorded receipt `stdout_sha256` exactly |
| `stderr_sha256` | equals the originally recorded receipt `stderr_sha256` exactly |
| `eval_output_hash` | equals the hash of the evaluation output file exactly |

**Tie-breaks, random seeds, and evaluation ordering are part of the frozen
deterministic policy and may not vary across cycles.**
"Close enough" is not a valid replay. Any single hash mismatch → `G_replay_ok = False` → `NO_SHIP`.

The frozen environment is defined by `environment_hash`:
a SHA256 of the environment manifest (Python version, package versions,
OS, filesystem paths, evaluation dataset path and hash).
If the environment changes between proposal and replay, the run is void.

Improvement threshold: **+0.002** (0.2 percentage points minimum).

---

## 5. FROZEN VERDICT REDUCER

```python
def compute_verdict(gates):
    # Kill-switch: integrity failure → QUARANTINE (not NO_SHIP)
    if not gates.G_kernel_integrity_ok:
        return VerdictV1("QUARANTINE", ["KERNEL_INTEGRITY_FAILED"])

    reasons = []
    if not gates.G_receipts_present:   reasons.append("MISSING_RECEIPTS")
    if not gates.G_replay_ok:          reasons.append("REPLAY_FAILED")
    if not gates.G_no_blocking_issue:  reasons.append("BLOCKING_ISSUE")
    if not gates.G_metric_improved:    reasons.append("METRIC_NOT_IMPROVED")

    if reasons:
        return VerdictV1("NO_SHIP", reasons)
    return VerdictV1("SHIP", [])
```

**QUARANTINE** = integrity failure, audit-only, never enters optimization memory.
**NO_SHIP** = rejected for functional reasons, audit-only.
**SHIP** = admitted to ledger, updates best metric, feeds future HER context.

---

## 6. STATE PERSISTENCE LAW

**Optimization memory law (frozen):**

> Only SHIPped state is optimization memory.

Persist only:
- best shipped `ranker.py` artifact hash
- best shipped `top1_accuracy` value
- best shipped manifest hash
- shipped run lineage (chain of parent hashes)

**Never use** as optimization memory:
- NO_SHIP artifacts
- QUARANTINE artifacts
- raw HER reflections
- rejected proposals
- symbolic annotations
- narrative summaries

---

## 7. REDUCER STATE EVOLUTION

Let `s_t` = best-known admitted state at cycle `t`.

```
s_{t+1} = Admit(s_t, p_t, e_t, m_t)   if verdict == SHIP
         = s_t                           if verdict == NO_SHIP
         = s_t                           if verdict == QUARANTINE
```

Only SHIP mutates best-known optimization state.

---

## 8. ROLE SEPARATION

| Role | Can | Cannot |
|------|-----|--------|
| HER (proposer) | Generate proposals, diffs, hypotheses | Mutate state, certify truth, admit runs |
| Critic | Inspect outputs, emit ISSUE_LIST_V1 | Ship runs |
| MAYOR / Reducer | Compute verdict, authorize admission | Improvise outside frozen gates |
| Kernel | Validate schema, check replay, maintain chain | Accept unverified mutations |

---

## 9. EXPERIMENT BUDGET (per cycle)

| Constraint | Value |
|---|---|
| Wall-clock budget | 300 seconds hard limit |
| Editable files | 1 (`ranker.py`) |
| Proposals per cycle | 1 |
| Admitted results per cycle | 1 |
| Network access | Prohibited |
| New files outside working dir | Prohibited |
| Shell commands | Allowlist only |

---

## 10. DEFINITION OF DONE (v0 success criteria)

The MVP is complete when the system can:

1. **Run 20 consecutive cycles** without manual intervention.
2. **Mutate one module only** (`ranker.py`).
3. **Append 20 immutable manifests** (hash-chain verified).
4. **Replay every shipped run** deterministically from manifest.
5. **Improve metric at least once** (`top1_accuracy` ≥ baseline + 0.002).
6. **Keep authority in kernel** (HER cannot self-admit).
7. **Reject invalid proposals correctly** (NO_SHIP triggered on gate failure).

---

## 11. ENGINEERING BUILD ORDER

Build in this exact order:

| # | Artifact | Why first |
|---|---|---|
| 1 | `manifest_ledger.py` | The anchor. Everything orbits it. |
| 2 | `verdict_reducer.py` | The only authority function. |
| 3 | `replay_checker.py` | Enforces G_replay_ok. |
| 4 | `bounded_harness.py` | Enforces budget and file isolation. |
| 5 | `benchmark_target.py` | Freezes the baseline metric. |

**Then:** add HER proposer → Critic → run 20 cycles → adversarial audit.

---

## 12. ADVERSARIAL AUDIT (deferred to Phase F)

After 20 cycles, run:
- receipt spoofing
- replay drift
- prompt injection into proposal lane
- hidden file mutation
- metric gaming
- canonicalization drift

Until this passes, the system is **pre-certification**.

---

## 13. SYSTEM POSITION

This spec defines a **governed optimization loop**, not:
- a sentient system
- a world simulator
- a multi-domain civilization engine
- an AGI branding exercise

The correct description:
> HELEN Research Loop v0.1 is a lawful, replayable, self-improving retrieval/ranking kernel
> operating on one file (`ranker.py`), one scalar metric (`top1_accuracy`),
> one bounded budget (300s), one canonical manifest (`RUN_MANIFEST_V1`),
> and one fixed verdict reducer.

The seed crystal. No more, no less.

---

*This specification is frozen. Do not reopen domain, metric, budget, manifest, or verdict until the 20-cycle milestone is achieved.*
