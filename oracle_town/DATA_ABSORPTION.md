# ORACLE TOWN — Data Absorption Pipeline

**Status:** ✓ OBS_SCAN complete and verified

This document describes how ORACLE TOWN ingests raw observations and structures them for analysis through the 5-layer OS.

---

## Overview

The data absorption pipeline transforms raw observations from multiple sources (emails, notes, metrics) into deterministic, structured facts that feed into the daily governance cycle.

```
Raw Data Sources
  ├─ observations/*.json    (JSON arrays, metrics, structured data)
  ├─ observations/*.txt     (email transcripts, notes)
  └─ observations/*.md      (markdown documents, meeting notes)
           ↓
    [OBS_SCAN Module]
           ↓
    Deterministic Structuring
  ├─ ID generation (SHA-256 based, not timestamp)
  ├─ Text normalization (whitespace, control chars)
  ├─ Confidence scoring (1.0 for derived, 0.8-0.95 for sources)
  ├─ Tag extraction & sorting
           ↓
   artifacts/observations.json    [Structured list, sorted by ID]
   artifacts/obs_receipt.json     [SHA-256 hash + placeholder signature]
           ↓
    [INS_CLUSTER Module]    (next: to be implemented)
```

---

## OBS_SCAN Module Implementation

**Location:** `oracle_town/jobs/obs_scan.py`

**Purpose:** Load raw observations from multiple file formats and structure them according to OBS charter.

### Key Functions

#### 1. `load_observations_from_directory(input_dir: Path) -> List[Dict[str, Any]]`

Loads observations from all supported formats in a directory.

**Supported formats:**

- **JSON files** (`.json`)
  - Format: Array of observation objects OR {observations: [array]}
  - Each object should have: source, title, body, tags (optional), confidence (optional)
  - Example:
    ```json
    [
      {
        "source": "analytics_dashboard",
        "title": "Weekly Traffic Report",
        "body": "Total unique visitors: 45,230...",
        "tags": ["metrics", "traffic"],
        "confidence": 0.95
      }
    ]
    ```

- **Text files** (`.txt`)
  - Format: One observation per file
  - Filename becomes the source ID
  - File contents become body
  - Confidence: 1.0 (derived from filename structure)
  - Example: `observations/email_marketing_q1.txt` → source="email_marketing_q1"

- **Markdown files** (`.md`)
  - Format: Markdown document with optional `# Title` heading
  - First `# Heading` becomes title (if present)
  - Full content becomes body
  - Tags: ["document"] (auto-added)
  - Confidence: 0.9 (markdown is structured but less precise than JSON)

**Returns:** Unsorted list of observation dicts (sorting happens in `structure_observations()`)

**Error handling:** Logs warnings to stderr, skips malformed files, continues processing

#### 2. `structure_observations(raw_obs: List[Dict], date: str, run_id: int) -> List[Dict]`

Transforms raw observations into canonical form with deterministic IDs.

**Key transformations:**

- **Text normalization:** Strips whitespace, normalizes internal spaces, removes control chars
  ```python
  text = text.strip()
  text = text.replace('\t', ' ')      # tabs → spaces
  text = ' '.join(text.split())       # normalize internal whitespace
  ```

- **Deterministic ID generation** (K5 invariant: same input → same ID)
  ```python
  id_input = f"{date}:{run_id}:{source}:{title}:{body}".encode('utf-8')
  id_hash = hashlib.sha256(id_input).hexdigest()[:16]
  obs_id = f"obs_{date.replace('-','')}_{id_hash}"
  ```
  - Format: `obs_YYYYMMDD_<16-char-hex>`
  - Example: `obs_20260130_2b17eec49f6d5bd8`
  - NOT timestamp-based (no clock dependency)
  - Hash includes: date, run_id, source, title, body
  - Same observation always produces same ID

- **Confidence clamping** → [0.0, 1.0]
  ```python
  confidence = float(obs.get("confidence", 0.8))
  confidence = max(0.0, min(1.0, confidence))  # clamp to valid range
  ```

- **Tag deduplication & sorting**
  ```python
  tags = sorted(set(tags))  # Remove duplicates, sort alphabetically
  ```

- **Length constraints:**
  - title: max 100 chars
  - body: max 500 chars
  - source: normalized, no length limit (usually short)

**Returns:** List of structured observations, sorted by ID (deterministic order)

**Observation schema:**
```python
{
  "id": "obs_20260130_2b17eec49f6d5bd8",         # Deterministic SHA-256 based
  "date": "2026-01-30",                           # YYYY-MM-DD only (no timestamp)
  "run_id": 174,                                  # Execution run number
  "source": "analytics_dashboard",                # Origin system/file
  "title": "Weekly Traffic Report - Week 1",      # Short summary (≤100 chars)
  "body": "Total unique visitors: 45,230...",     # Full content (≤500 chars)
  "tags": ["metrics", "performance", "traffic"],  # Sorted, deduplicated
  "confidence": 0.95,                             # [0.0, 1.0] clamped
  "links": []                                     # Cross-references (empty during OBS)
}
```

#### 3. `create_receipt(observations: List[Dict], run_id: int, attestor_id: str) -> Dict`

Creates a receipt structure for cryptographic signing.

**Receipt schema:**
```json
{
  "obs_receipt": {
    "observation_count": 4,
    "observations_hash": "sha256:99f1b99b932d8be43754e00cd214ebe732d833bcc781949dc2d14807fa0f423e",
    "run_id": 174,
    "attestor_id": "obs_attestor_001",
    "signature": "ed25519:PLACEHOLDER_SIGNATURE",
    "note": "Signature placeholder; actual signing by attestor_id required"
  }
}
```

**Key fields:**
- `observations_hash`: SHA-256 of canonical JSON representation of all observations
  - Canonical format: `json.dumps(observations, sort_keys=True, separators=(',', ':'), ensure_ascii=True)`
  - Same list always produces same hash (K5 determinism)
- `signature`: Placeholder; actual Ed25519 signature added by TRI module
- `attestor_id`: Which attestor should sign this receipt

**Cryptographic binding:**
- Hash depends on all observations (any change invalidates hash)
- Signature will be tied to attestor public key from registry
- TRI module verifies signature matches observations_hash

---

## Usage Example

### Basic execution:

```bash
cd "JMT CONSULTING - Releve 24"

python3 oracle_town/jobs/obs_scan.py \
  --date 2026-01-30 \
  --run-id 174 \
  --input-dir observations/ \
  --output artifacts/observations.json \
  --receipt artifacts/obs_receipt.json \
  --verbose
```

**Output:**
```
[OBS] Scanning observations from: observations/
[OBS] Loaded 4 raw observations
[OBS] Structured 4 observations
      - obs_20260130_2b17eec49f6d5bd8: sample_email_001
      - obs_20260130_2ec5aa7d7a864c99: Weekly Traffic Report - Week 1
      - obs_20260130_93016a7834f411bc: Support ticket spike - Database connection issues
      ... and 1 more
[OBS] Observations saved: artifacts/observations.json
[OBS] Receipt saved: artifacts/obs_receipt.json
[OBS] Total observations: 4
[OBS] ✓ Complete
```

### Verification:

```bash
# Check structured observations
cat artifacts/observations.json | jq '.[] | {id, title, confidence}'

# Check receipt
cat artifacts/obs_receipt.json | jq '.obs_receipt | {observation_count, observations_hash}'

# Verify determinism (K5)
python3 oracle_town/jobs/obs_scan.py --date 2026-01-30 --run-id 174 --input-dir observations/ --output artifacts/obs_v1.json
python3 oracle_town/jobs/obs_scan.py --date 2026-01-30 --run-id 174 --input-dir observations/ --output artifacts/obs_v2.json
shasum -a 256 artifacts/obs_v1.json artifacts/obs_v2.json
# Both should have identical SHA-256 hash
```

---

## Sample Data Structure

### observations/sample_email_001.txt
```
Subject: Marketing campaign Q1 2026 launch approved
From: marketing@company.com

The Q1 2026 marketing campaign has been approved by leadership. Budget: $250K. Timeline: Jan 30 - Mar 31. ...
```

### observations/sample_metrics_002.json
```json
[
  {
    "source": "analytics_dashboard",
    "title": "Weekly Traffic Report - Week 1",
    "body": "Total unique visitors: 45,230. Page load time: 2.3s (avg)...",
    "tags": ["metrics", "traffic", "performance"],
    "confidence": 0.95
  }
]
```

### observations/sample_notes_003.md
```markdown
# Engineering Team Standup - 2026-01-29

## Attendees
- Lead Engineer: Alice Chen
...

## Key Decisions
### API Rate Limiting
...
```

---

## Integration with Daily Workflow

### Step 1: Prepare observations
```bash
# Place raw observations in observations/ directory
ls observations/
# sample_email_001.txt
# sample_metrics_002.json
# sample_notes_003.md
```

### Step 2: Run OBS_SCAN (part of os_runner.py)
```bash
python3 oracle_town/os_runner.py --date 2026-01-30 --run-id 174 --mode daily
# Internally calls OBS_SCAN → artifacts/observations.json
```

### Step 3: Verify outputs
```bash
# Check structured observations
cat artifacts/observations.json | jq '.[] | {id, title, confidence}'

# Feed to next module (INS_CLUSTER)
python3 oracle_town/jobs/ins_cluster.py \
  --date 2026-01-30 \
  --run-id 174 \
  --observations artifacts/observations.json \
  --output artifacts/insights.json
  # (next module: not yet implemented)
```

---

## Key Invariants Enforced

| Invariant | Mechanism | Verification |
|-----------|-----------|--------------|
| **I1: Determinism** | SHA-256 based IDs, no RNG, no env reads | Run OBS_SCAN twice with same inputs → identical files |
| **I4: No Timestamps** | Date-only YYYY-MM-DD, no `datetime.now()` calls | `grep -r "datetime.now\|time.time" oracle_town/jobs/obs_scan.py` (empty) |
| **K5: Determinism** | Observations hash doesn't change for same inputs | `shasum observations_v1.json observations_v2.json` (identical) |

---

## Design Rationale

### Why SHA-256 based IDs?

- **Deterministic:** Same observation always produces same ID
- **No clock dependency:** Doesn't break if run at different times
- **Content-aware:** ID changes if observation changes
- **Auditable:** Can be replayed and verified independently

### Why normalize text?

- **Consistency:** Emails might have tabs, markdown might have trailing spaces
- **Canonicalization:** Reduces accidental duplicates from formatting
- **Width safety:** Removes control chars that could break rendering

### Why separate tags and sort?

- **Consistency:** Multiple sources might use different tag orders
- **Deduplication:** Avoids ["incident", "incident", "critical"] → ["critical", "incident"] sorted, deduplicated
- **Determinism:** Tags always appear in same order

### Why confidence scoring?

- **Accuracy tracking:** JSON metrics (high confidence) vs. handwritten notes (lower confidence)
- **INS module input:** Will use confidence to weight clustering
- **Audit trail:** Shows source quality per observation

---

## Next Steps

1. **INS_CLUSTER** (next module): Read observations.json, cluster into themes
2. **BRF_ONEPAGER**: Synthesize clusters into brief + ONE BET
3. **TRI_GATE**: Verify receipts, enforce K-gates, decide SHIP/NO_SHIP
4. **PUB_DELIVERY**: Record decision to ledger (if SHIP)
5. **MEM_LINK**: Link entities in memory graph
6. **EVO_ADJUST**: Analyze past decisions, propose policy patches

---

**Status:** OBS_SCAN ✓ Complete and Verified (K5 determinism tested)

**Last Updated:** 2026-01-30

