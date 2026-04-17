# OBS District Charter

**Module:** Observation & Data Collection

## Purpose

Ingest raw observations (notes, emails, meetings, metrics, signals) and structure them as normalized facts. OBS is the frontline sensor layer—it collects, validates, and emits observations for downstream processing.

## Inputs

**Sources (read-only):**
- External notes/documents (user-provided)
- Email digests (optional structured feed)
- Metrics feeds (JSON/CSV snapshots)
- Past observations from `oracle_town/ledger/observations.jsonl`

**No direct state mutations.** OBS only reads `city_current.json` to understand current context (date, run_id, mode).

## Outputs

**Artifacts produced:**
- `observations.json` — Array of structured observation objects
- `obs_receipt.json` — Cryptographic proof of work

**State mutations:**
- Writes to `city_current.json`: `modules.OBS.progress`, `modules.OBS.status`
- Appends to `oracle_town/ledger/observations.jsonl` (one JSON line per observation)

## Observation Schema

```json
{
  "id": "obs_20260130_001",
  "date": "2026-01-30",
  "run_id": 173,
  "source": "email|note|metric|meeting",
  "title": "string (max 100 chars)",
  "body": "string (max 500 chars)",
  "tags": ["tag1", "tag2"],
  "confidence": 0.0,
  "links": []
}
```

**Constraints:**
- `id` must be unique and deterministic (date_serial)
- `date` must match run date (YYYY-MM-DD only, no time)
- `confidence` is 0.0–1.0, clamped
- All text fields are trimmed and normalized (no tabs, no trailing whitespace)

## Gates (Enforced by TRI)

**OBS cannot proceed to next module unless:**
1. At least 1 observation collected (progress ≥ 1)
2. `observations.json` is valid JSON with sorted keys
3. All observations have unique IDs
4. No observation references a future date
5. `obs_receipt.json` exists and is cryptographically signed

**Failure mode:** TRI → NO_SHIP (K1 fail-closed)

## Determinism Contract

**OBS must guarantee:**
- Same input notes + same date → identical `observations.json` output
- No RNG, no timestamps (only date field, which is pinned to run date)
- No environment variable reads
- Sorted output (observations sorted by ID)
- Stable serialization: `json.dumps(..., sort_keys=True, indent=2)`

**Test:** Run OBS twice on same input; hash must match.

## Forbidden Actions

- OBS may NOT modify past observations (append-only ledger)
- OBS may NOT write to any module's state except its own progress
- OBS may NOT call external APIs (data collection must be from provided inputs)
- OBS may NOT use timestamps or wall-clock time

## State Writes Allowed

```json
{
  "modules": {
    "OBS": {
      "status": "OFF|BLD|OK|WRN|FLR",
      "progress": 0-8,
      "desc": "string (max 50 chars)"
    }
  }
}
```

**Status meanings:**
- `OFF` — not started
- `BLD` — building (in progress)
- `OK` — complete and passed gates
- `WRN` — complete but anomalies detected
- `FLR` — failed gates; blocking further modules

## Receipts Required

OBS must produce a cryptographic receipt signed by a registered attestor. Receipt structure:

```json
{
  "obs_receipt": {
    "timestamp_unix": 1706601600,
    "observation_count": 5,
    "observations_hash": "sha256:abc123...",
    "run_id": 173,
    "attestor_id": "obs_attestor_001",
    "signature": "ed25519:xyz789..."
  }
}
```

**K0 enforcement:** Only attestor_obs_001 (or equivalent) can sign OBS receipts.

## Integration with Daily OS

**Workflow step:**
```bash
# Part of os_runner.py job graph
python3 oracle_town/jobs/obs_scan.py \
  --date "2026-01-30" \
  --run-id 173 \
  --input-dir observations/ \
  --output-file artifacts/observations.json \
  --receipt-file artifacts/obs_receipt.json
```

**Before next module (INS):** TRI gate verifies receipt exists and is valid.

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
