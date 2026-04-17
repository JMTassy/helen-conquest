# PUB District Charter

**Module:** Publication & Delivery

## Purpose

Take a SHIP verdict from TRI and publish it: write decision records, emit artifacts, and prepare the town state for commitment. PUB is the executor—it makes the verdict real.

## Inputs

**Required:**
- `artifacts/tri_verdict.json` (from TRI)
- `artifacts/tri_receipt.json` (from TRI)
- `artifacts/brief.md` (from BRF)
- `oracle_town/state/city_current.json` (current state snapshot)

**No direct state mutations except authorized writes.**

## Outputs

**Artifacts produced:**
- `decision_record.jsonl` — Append-only decision entry
- `pub_manifest.json` — List of published artifacts
- `pub_receipt.json` — Cryptographic proof

**State mutations:**
- Writes to `city_current.json`: `modules.PUB.progress`, `modules.PUB.status`, `artifacts[]` (5 most recent)
- Appends to `oracle_town/ledger/decisions.jsonl` with full verdict + artifacts

## Publication Flow

1. **Verify TRI verdict** → If NO_SHIP, halt (PUB stays OFF)
2. **Record decision** → Append to ledger
3. **Prepare artifacts** → Collect all outputs from this run
4. **Update state** → Reflect in city_current.json
5. **Sign receipt** → Create pub_receipt.json
6. **Ready for commit** → State snapshot ready for git

## Decision Record Schema

```json
{
  "id": "dec_20260130_001",
  "date": "2026-01-30",
  "run_id": 173,
  "verdict": "SHIP",
  "brief": "brief_v1.md",
  "observation_ids": ["obs_xxx", "obs_yyy"],
  "insight_ids": ["ins_aaa", "ins_bbb"],
  "artifacts": ["brief_v1.md", "insights.json", "decision_record.jsonl"],
  "attestations": {
    "obs_attestor_001": "signature_hash",
    "ins_attestor_001": "signature_hash",
    "brf_attestor_001": "signature_hash",
    "tri_attestor_001": "signature_hash"
  },
  "policy_hash": "sha256:jkl012...",
  "decision_hash": "sha256:pqr678..."
}
```

## Artifact Manifest Schema

```json
{
  "run_id": 173,
  "date": "2026-01-30",
  "artifacts": [
    {"name": "brief_v1.md", "type": "markdown", "hash": "sha256:..."},
    {"name": "insights.json", "type": "json", "hash": "sha256:..."},
    {"name": "observations.json", "type": "json", "hash": "sha256:..."},
    {"name": "decision_record.jsonl", "type": "jsonl", "hash": "sha256:..."}
  ]
}
```

## Gates (Enforced by EVO & continuous audit)

**PUB cannot proceed unless:**
1. TRI verdict is SHIP (no publication on NO_SHIP)
2. All upstream receipts present and valid
3. `pub_receipt.json` signed by pub_attestor_001
4. Decision record valid JSON with all required fields
5. Artifact manifest complete (all files listed exist)

**Failure mode:** PUB stays OFF; town waits for next run.

## Determinism Contract

**PUB must guarantee:**
- Same TRI verdict + same artifacts → identical decision record
- Manifest ordering deterministic (sort by artifact name)
- No timestamps (only date/run_id for metadata)
- Hash calculation stable: canonical JSON + consistent file reading

**Test:** Run PUB twice on same input; decision hash must match.

## Forbidden Actions

- PUB may NOT modify TRI verdict (read-only)
- PUB may NOT skip recording to ledger
- PUB may NOT truncate decision history
- PUB may NOT write to MEM or EVO state (read-only)

## State Writes Allowed

```json
{
  "modules": {
    "PUB": {
      "status": "OFF|BLD|OK|FLR",
      "progress": 0-8,
      "desc": "string (max 50 chars)"
    }
  },
  "artifacts": ["recent_artifact_1", "recent_artifact_2", ...]
}
```

**Max 5 artifacts** in state (space-constrained for rendering).

## Receipts Required

```json
{
  "pub_receipt": {
    "timestamp_unix": 1706601600,
    "decision_id": "dec_20260130_001",
    "decision_hash": "sha256:pqr678...",
    "artifact_count": 4,
    "run_id": 173,
    "attestor_id": "pub_attestor_001",
    "signature": "ed25519:jkl789..."
  }
}
```

**K0 enforcement:** Only pub_attestor_001 can sign PUB receipts.

## NO_SHIP Handling

If TRI returns NO_SHIP:
- PUB status remains OFF
- No decision record written
- No artifacts committed
- MEM links created (for future analysis of why it failed)
- Next run will try again

This prevents "zombie" published decisions.

## Integration with Daily OS

**Workflow step:**
```bash
python3 oracle_town/jobs/pub_delivery.py \
  --verdict artifacts/tri_verdict.json \
  --tri-receipt artifacts/tri_receipt.json \
  --brief artifacts/brief.md \
  --output artifacts/decision_record.jsonl \
  --manifest artifacts/pub_manifest.json \
  --receipt artifacts/pub_receipt.json
```

**After PUB:** All upstream artifacts locked in. Ready for git commit + MEM linking.

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
