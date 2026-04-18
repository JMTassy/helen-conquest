# UNIFIED_CI_REPLAY_HARNESS_V0

**Status:** FREEZE_CANDIDATE
**Version:** v0 (zero-drift: no allowed changes)
**Date:** 2026-03-11
**Scope:** wul-core (symbolic VM) + nsps (sensor VM)

---

## 0. Purpose

A single CI harness verifies both VMs under one rule:

**Same manifest in → same bytes out.**

This matches the replay-determinism and hash-correctness requirements already fixed in ORACLE/HELEN:
- A complete run manifest must be sufficient to replay the decision.
- Hashes must recompute exactly.
- Identical logical inputs must yield identical input/output hashes.

---

## 1. Scope

**Targets:**
- `wul-core` (symbolic VM)
- `nsps` (sensor VM)

**Endpoints:**
- `/api/run_symbolic`
- `/api/run_sensor`
- `/api/verify_artifact`

**Artifacts checked:**
- Manifest JSON
- Output JSON
- All declared artifact blobs
- Receipt SHA256

---

## 2. Pass/Fail Rule

A build is **PASS** iff all of the following hold:

### 1. Schema validity
Request, response, manifest, and artifacts validate against frozen schemas.

### 2. Receipt correctness
```
receipt_sha256 == sha256_jcs(manifest_without_receipt)
```
Where `manifest_without_receipt` = manifest object with `receipt_sha256` field omitted.

### 3. Replay identity
Re-running the same manifest produces byte-identical:
- `outputs.payload`
- `outputs.sha256`
- `artifacts[i].sha256`
- `receipt_sha256`

### 4. No hidden state
Mutating wall-clock, hostname, temp path, locale, or process order does not change outputs.

### 5. Invariant checks
- **Symbolic VM:** `NO_RECEIPT = NO_SHIP`, blocking obligations force `NO_SHIP`, superteams cannot emit verdicts.
- **Both VMs:** Replay determinism and schema validity remain true.

**Any failure = FAIL.**

---

## 3. Test Matrix

### T1 — Golden Replay

Run each frozen manifest 3 times in the same environment.

**Requirement:** Hashes match exactly across all 3 runs.

### T2 — Cross-Environment Replay

Run the same manifest across at least:
- Linux image A
- Linux image B

**Requirement:** Same outputs required.

### T3 — Seed Fuzzing

For each VM, run 1000 seeds over a fixed frozen corpus/config.

**Requirement:** Zero nondeterministic drift.

### T4 — Artifact Diff

Canonical diff only:
- If JCS bytes differ → fail.
- No semantic or textual "close enough" layer.

### T5 — Adversarial Perturbation

**Symbolic VM:**
- Namespace collision
- Max-node flood
- Malformed token injection

**Sensor VM:**
- Corpus pollution
- OOV inflation
- Reordered corpus entries

**Requirement:** Deterministic reject or deterministic gated output, never unstable behavior.

### T6 — Doctrine Integrity

Change doctrine hash without version bump → hard fail.

**Requirement:** Any undeclared doctrine change causes immediate rejection.

### T7 — Hidden-State Mutation

Change:
- Wall clock
- Locale
- Temp path
- Process order

**Requirement:** Outputs must not drift.

---

## 4. Output Contract

CI emits **JSON only**:

```json
{
  "suite": "unified_ci_replay_v0",
  "status": "pass|fail",
  "vm": "symbolic|sensor",
  "manifest_sha256": "...",
  "doctrine_hash": "...",
  "runs": [
    {
      "name": "T1_golden_replay",
      "ok": true,
      "expected_sha256": "...",
      "observed_sha256": "..."
    }
  ],
  "failures": []
}
```

**Failure object structure:**

```json
{
  "test_id": "T3",
  "seed": "...",
  "expected_sha256": "...",
  "observed_sha256": "...",
  "failure_reason": "nondeterministic_drift"
}
```

---

## 5. Zero-Drift Criterion

For frozen version `v0`:
- **Allowed changes:** none.
- Any byte drift in outputs, artifacts, or receipts is a regression.
- **Recovery path:** explicit version increment only (`v1`, with changelog).

---

## 6. Scenario Pack (Next Artifact)

The highest-value next artifact is a machine-readable CI scenario pack:

**20 canonical manifests:**
- 10 for `wul-core`
- 10 for `nsps`

Each manifest must include:
- Frozen schema version
- Doctrine hash
- Environment hash
- Explicit seed
- Expected receipt hashes

Format: `ci_scenario_pack_v0.json`

---

## 7. Canonicalization Regime

All hash computations use `JCS_SHA256_V1`:

```python
import json, hashlib

def jcs_bytes(obj):
    """RFC 8785 JSON Canonicalization Scheme"""
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode('utf-8')

def sha256_jcs(obj):
    return hashlib.sha256(jcs_bytes(obj)).hexdigest()

def compute_receipt_sha256(artifact_without_receipt):
    return sha256_jcs(artifact_without_receipt)
```

---

## 8. Implementation Notes

### Cross-VM Receipt Engine

The receipt engine must be shared, not duplicated:
```python
# helen_os/kernel/receipt_engine.py
def verify_receipt(artifact: dict) -> bool:
    without_receipt = {k: v for k, v in artifact.items() if k != 'receipt_sha256'}
    expected = sha256_jcs(without_receipt)
    return artifact.get('receipt_sha256') == expected
```

### Hidden-State Isolation

To test for hidden state, the harness must:
1. Capture baseline output with default environment.
2. Mutate each environmental variable independently.
3. Re-run and compare byte-for-byte.
4. Report any diff as a hidden-state violation.

### Adversarial Input Normalization

All adversarial inputs must still be valid JSON. The harness injects valid-but-extreme payloads, not malformed bytes.

---

## 9. Relation to HELEN_KERNEL_DOCTRINE_V1

This harness is the external proof surface for the invariants stated in `spec/HELEN_KERNEL_DOCTRINE_V1.md`.

| Invariant | Tested by |
|-----------|-----------|
| Replay Law (1.1) | T1, T2, T7 |
| Mutation Law (1.2) | T4, T6 |
| Receipt Law (1.3) | Pass condition 2 |
| Sovereignty Law (1.4) | T5 symbolic |
| Doctrine Law (1.5) | T6 |
| Stability Monitor (§14) | T3 seed fuzzing |

---

*This is a FREEZE_CANDIDATE. Any change to this spec requires an explicit version bump and changelog.*
*Companion: `spec/HELEN_KERNEL_DOCTRINE_V1.md`*
