# INS District Charter

**Module:** Insight & Clustering

## Purpose

Cluster observations into themes, detect anomalies, and produce actionable insights. INS synthesizes raw data into patterns that feed decision-making.

## Inputs

**Required:**
- `artifacts/observations.json` (from OBS)
- `oracle_town/ledger/observations.jsonl` (historical context, read-only)
- `oracle_town/memory/index.json` (entity references, read-only)

**No direct state mutations.** INS reads `city_current.json` for context only.

## Outputs

**Artifacts produced:**
- `insights.json` — Array of insight clusters
- `anomalies.json` — Flagged anomalies with severity
- `ins_receipt.json` — Cryptographic proof

**State mutations:**
- Writes to `city_current.json`: `modules.INS.progress`, `modules.INS.status`, `anomalies[]`
- Appends to `oracle_town/ledger/observations.jsonl` if new links discovered

## Insight Schema

```json
{
  "id": "ins_20260130_001",
  "date": "2026-01-30",
  "run_id": 173,
  "theme": "string (max 100 chars)",
  "observations": ["obs_20260130_001", "obs_20260130_003"],
  "confidence": 0.85,
  "action_items": ["item1", "item2"],
  "tags": ["category1"]
}
```

## Anomaly Schema

```json
{
  "code": "anomaly_code",
  "severity": "weak|medium|high",
  "module": "INS",
  "observation_ids": ["obs_xxx"],
  "description": "string"
}
```

**Severity guide:**
- `weak` — Interesting but non-blocking
- `medium` — Requires investigation
- `high` — Potential blocker for SHIP

## Gates (Enforced by TRI)

**INS cannot proceed unless:**
1. At least 1 insight cluster produced (progress ≥ 1)
2. `insights.json` valid JSON with sorted keys
3. All insight IDs unique and deterministic
4. Anomalies list valid or empty
5. `ins_receipt.json` signed by registered attestor

**Failure mode:** TRI → NO_SHIP (K1 fail-closed)

## Determinism Contract

**INS must guarantee:**
- Same observations input → identical insights output
- Clustering deterministic (no RNG; use hash-based seeding if needed)
- No timestamps (only date, pinned to run date)
- Stable serialization: sorted keys, 2-space indents
- Same historical ledger → same anomaly detection

**Test:** Run INS twice on same observations; hash must match.

## Forbidden Actions

- INS may NOT modify observations (read-only)
- INS may NOT write to other modules' state
- INS may NOT call external ML services (must be deterministic local algorithm)
- INS may NOT generate new entity IDs (only reference existing ones from memory)

## State Writes Allowed

```json
{
  "modules": {
    "INS": {
      "status": "OFF|BLD|OK|WRN|FLR",
      "progress": 0-8,
      "desc": "string (max 50 chars)"
    }
  },
  "anomalies": [
    {
      "code": "anomaly_code",
      "severity": "weak|medium|high",
      "module": "INS"
    }
  ]
}
```

## Receipts Required

```json
{
  "ins_receipt": {
    "timestamp_unix": 1706601600,
    "insight_count": 3,
    "insights_hash": "sha256:def456...",
    "anomaly_count": 1,
    "run_id": 173,
    "attestor_id": "ins_attestor_001",
    "signature": "ed25519:abc789..."
  }
}
```

**K0 enforcement:** Only ins_attestor_001 (or equivalent) can sign INS receipts.

## Integration with Daily OS

**Workflow step:**
```bash
python3 oracle_town/jobs/ins_cluster.py \
  --observations artifacts/observations.json \
  --output artifacts/insights.json \
  --anomalies artifacts/anomalies.json \
  --receipt artifacts/ins_receipt.json
```

**Before BRF:** TRI gate verifies receipt and anomaly severity levels.

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
