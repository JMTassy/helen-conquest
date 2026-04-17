# TRI District Charter

**Module:** Tribunal & Verification

## Purpose

Verify that all previous modules (OBS, INS, BRF) have produced valid, signed artifacts and have passed immutable gates. TRI is the gatekeeper—it enforces K1 fail-closed (no receipt, no ship) and prevents invalid claims from reaching the Mayor.

## Inputs

**Required (all must exist):**
- `artifacts/observations.json` + `artifacts/obs_receipt.json`
- `artifacts/insights.json` + `artifacts/anomalies.json` + `artifacts/ins_receipt.json`
- `artifacts/brief.md` + `artifacts/one_bet.txt` + `artifacts/brf_receipt.json`
- `oracle_town/keys/public_keys.json` (attestor registry, read-only)

**No direct state mutations.** TRI only reads and verifies.

## Outputs

**Artifacts produced:**
- `tri_verdict.json` — Verdict: SHIP or NO_SHIP with reasoning
- `tri_receipt.json` — Cryptographic proof of verification

**State mutations:**
- Writes to `city_current.json`: `modules.TRI.progress`, `modules.TRI.status`, `modules.TRI.desc`
- Appends to `oracle_town/ledger/decisions.jsonl` with verdict record

## Verification Gates (K-Invariants)

**K0: Authority Separation**
- Each receipt signed by correct attestor (obs_attestor_001, ins_attestor_001, brf_attestor_001)
- Signature verification uses ed25519 from public key registry
- Attestor IDs match expected modules

**K1: Fail-Closed Default**
- If any receipt missing: **NO_SHIP**
- If any signature invalid: **NO_SHIP**
- If any JSON invalid: **NO_SHIP**
- Default is always rejection unless all gates pass

**K2: No Self-Attestation**
- No module may sign its own receipt (checked via attestor_id ≠ module_id)

**K3: Quorum Requirements**
- At minimum: OBS + INS + BRF must all be OK or WRN (not FLR)
- Anomaly severity check: if any HIGH severity anomalies, must have explicit override receipt

**K7: Policy Pinning**
- All receipts must reference same `policy_hash` (gates are immutable for this run)
- If policy changed mid-run, TRI rejects with NO_SHIP

## Verdict Schema

```json
{
  "id": "tri_20260130_001",
  "date": "2026-01-30",
  "run_id": 173,
  "decision": "SHIP|NO_SHIP",
  "reasoning": "string",
  "blocked_by": ["anomaly_code_1"],
  "overrides": [],
  "policy_hash": "sha256:jkl012...",
  "verified_modules": {
    "OBS": {"status": "OK", "receipt_valid": true},
    "INS": {"status": "OK", "receipt_valid": true},
    "BRF": {"status": "OK", "receipt_valid": true}
  }
}
```

## Failure Modes & Recovery

| Condition | Verdict | Recovery |
|-----------|---------|----------|
| Missing receipt | NO_SHIP | Re-run module, re-sign receipt |
| Invalid signature | NO_SHIP | Verify attestor key in registry, re-sign |
| HIGH anomaly + no override | NO_SHIP | Address issue in INS, re-run |
| Policy hash mismatch | NO_SHIP | Ensure no policy changes mid-run |
| Invalid JSON | NO_SHIP | Validate artifact schema, re-produce |

## Gates (Enforced by TRI Itself)

**TRI cannot produce SHIP verdict unless:**
1. All three module receipts exist and valid
2. All three modules are OK or WRN (none FLR)
3. No HIGH anomalies without override
4. All signatures cryptographically valid
5. No self-attestations detected
6. Policy hash matches expected value
7. Quorum of distinct attestors (min 3 different people/keys)

**Default:** NO_SHIP (K1 fail-closed)

## Determinism Contract

**TRI must guarantee:**
- Same input artifacts + same policy hash → identical verdict
- Verification logic is pure (no RNG, no environment reads)
- Verdict hash stable: `json.dumps(verdict, sort_keys=True, indent=2)`

**Test:** Run TRI twice on same artifacts; verdict hash must match.

## Forbidden Actions

- TRI may NOT modify receipts or artifacts
- TRI may NOT override K-invariants without explicit Mayor authorization
- TRI may NOT add new attestors to registry (read-only)
- TRI may NOT create override receipts (only the Mayor can)

## State Writes Allowed

```json
{
  "modules": {
    "TRI": {
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
  "tri_receipt": {
    "timestamp_unix": 1706601600,
    "verdict": "SHIP|NO_SHIP",
    "verdict_hash": "sha256:mno345...",
    "verified_artifacts": 3,
    "policy_hash": "sha256:jkl012...",
    "run_id": 173,
    "attestor_id": "tri_attestor_001",
    "signature": "ed25519:ghi456..."
  }
}
```

**K0 enforcement:** Only tri_attestor_001 can sign TRI receipts.

## Integration with Daily OS

**Workflow step:**
```bash
python3 oracle_town/jobs/tri_gate.py \
  --obs-receipt artifacts/obs_receipt.json \
  --ins-receipt artifacts/ins_receipt.json \
  --brf-receipt artifacts/brf_receipt.json \
  --policy-hash "sha256:jkl012..." \
  --output artifacts/tri_verdict.json \
  --receipt artifacts/tri_receipt.json
```

**Output:** SHIP or NO_SHIP, feeds directly to Mayor (PUB module depends on this).

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
**Critical:** No override possible without explicit Mayor receipt (K1 dominance).
