# ORACLE TOWN — Data Absorption Pipeline Status

**Status:** ✓ **FIRST HALF COMPLETE** (OBS → INS → BRF)

This document tracks the implementation status of ORACLE TOWN's 5-layer job pipeline.

---

## Pipeline Overview

```
┌─ Layer 2: Job Orchestration ─────────────────────────────────┐
│                                                                 │
│  [Input] → OBS_SCAN → INS_CLUSTER → BRF_ONEPAGER → [TRI]     │
│                                                    ↓           │
│                                      [PUB, MEM, EVO (parallel)]│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Data Ingestion & Synthesis (✓ COMPLETE)

### 1. OBS_SCAN Module
**File:** `oracle_town/jobs/obs_scan.py` (249 lines)

**Status:** ✓ Complete and Verified

**Purpose:** Load raw observations from multiple sources and structure them deterministically.

**Key Functions:**
- `load_observations_from_directory()` — Load JSON/TXT/MD files
- `structure_observations()` — Normalize, generate deterministic IDs, sort by ID
- `create_receipt()` — Generate SHA-256 signed receipt

**Determinism:** K5 verified (identical outputs on identical inputs)

**Invariants Enforced:**
- I1: Determinism (SHA-256 based IDs, no RNG)
- I4: No timestamps (date-only YYYY-MM-DD)
- K5: Determinism (same input → same output hash)

**Output:**
- `artifacts/observations.json` — Structured list of observations
- `artifacts/obs_receipt.json` — Receipt with observation count + hash

**Sample Run:**
```bash
python3 oracle_town/jobs/obs_scan.py \
  --date 2026-01-30 --run-id 174 \
  --input-dir observations/ \
  --output artifacts/observations.json \
  --receipt artifacts/obs_receipt.json
# Output: 4 observations with deterministic IDs
```

---

### 2. INS_CLUSTER Module
**File:** `oracle_town/jobs/ins_cluster.py` (342 lines)

**Status:** ✓ Complete and Verified

**Purpose:** Cluster observations into themes and detect anomalies.

**Key Functions:**
- `extract_keywords()` — Deterministic keyword extraction
- `cluster_observations()` — Group observations by theme
- `detect_anomalies()` — Find 4 types of anomalies (A1-A4)
  - A1: Low confidence + critical tags
  - A2: High tag complexity + critical
  - A3: Large incident descriptions
  - A4: Customer/user impact
- `create_receipt()` — Generate SHA-256 signed receipt

**Determinism:** K5 verified

**Invariants Enforced:**
- I1: Determinism (keyword extraction sorted)
- K5: Determinism (same insights on same observations)

**Output:**
- `artifacts/insights.json` — Clusters + anomalies
- `artifacts/ins_receipt.json` — Receipt with counts + hash

**Sample Run:**
```bash
python3 oracle_town/jobs/ins_cluster.py \
  --date 2026-01-30 --run-id 174 \
  --observations artifacts/observations.json \
  --output artifacts/insights.json \
  --receipt artifacts/ins_receipt.json
# Output: 4 clusters + 2 anomalies
```

---

### 3. BRF_ONEPAGER Module
**File:** `oracle_town/jobs/brf_onepager.py` (238 lines)

**Status:** ✓ Complete and Verified

**Purpose:** Synthesize insights into a markdown brief with ONE BET statement.

**Key Functions:**
- `generate_one_bet()` — Create single-sentence summary (≤100 chars)
  - HIGH strategy: "HIGH: [anomaly codes]" if critical issues
  - SIGNAL strategy: "SIGNAL: [top cluster]" otherwise
  - NEUTRAL strategy: "NEUTRAL: [insufficient data]" fallback
- `generate_brief_markdown()` — Create narrative with:
  - Key clusters (top 3 by confidence)
  - Anomalies section (HIGH prominently, medium/low lower)
  - Recommendation section (ACTION/MONITOR/NEUTRAL)
- `create_receipt()` — Generate SHA-256 signed receipt

**Determinism:** K5 verified

**Invariants Enforced:**
- I1: Determinism (sorted cluster selection)
- K5: Determinism (same brief on same insights)

**ONE BET Constraint:**
- HARD LIMIT: ≤100 characters
- STRATEGY: Highest confidence hypothesis only
- EXAMPLE: "SIGNAL: Approved Campaign."

**Output:**
- `artifacts/brief.md` — Markdown narrative
- `artifacts/one_bet.txt` — Single-sentence summary
- `artifacts/brf_receipt.json` — Receipt with brief hash

**Sample Run:**
```bash
python3 oracle_town/jobs/brf_onepager.py \
  --date 2026-01-30 --run-id 174 \
  --insights artifacts/insights.json \
  --output artifacts/brief.md \
  --one-bet artifacts/one_bet.txt \
  --receipt artifacts/brf_receipt.json
# Output: brief.md (519 chars) + one_bet.txt (26 chars)
```

---

## Phase 2: Verification (Next)

### 4. TRI_GATE Module (🔲 TODO)
**File:** `oracle_town/jobs/tri_gate.py` (NOT YET IMPLEMENTED)

**Purpose:** Verify all receipts (OBS, INS, BRF) and enforce K-gates (K0-K7).

**K-Invariants to Enforce:**
- K0: Authority Separation (verify attestor registered)
- K1: Fail-Closed Default (NO_SHIP if any receipt missing)
- K2: No Self-Attestation (attestor_id ≠ module_id)
- K3: Quorum-by-Class (min 3 distinct attestors)
- K4: Revocation Works (removed keys cannot sign)
- K5: Determinism (same inputs → same decision)
- K7: Policy Pinning (policy hash immutable)

**Inputs:**
- `artifacts/observations.json` + obs_receipt.json
- `artifacts/insights.json` + ins_receipt.json
- `artifacts/brief.md` + one_bet.txt + brf_receipt.json
- `oracle_town/keys/public_keys.json` (attestor registry)
- Policy hash (pinned for this run)

**Output:**
- `artifacts/tri_verdict.json` — SHIP or NO_SHIP decision
- `artifacts/tri_receipt.json` — Verification receipt

**Logic:**
```
For each module (OBS, INS, BRF):
  1. Load receipt
  2. Verify signature against public key registry (K0)
  3. Check attestor_id ≠ module_id (K2)
  4. Verify artifact hash matches receipt (K5)

Aggregate:
  1. Count distinct attestor classes (K3 quorum)
  2. Check all critical modules signed (K1)
  3. Verify policy hash unchanged (K7)

Decision:
  - All pass → SHIP
  - Any fail → NO_SHIP
```

---

### 5. PUB_DELIVERY Module (🔲 TODO)
**File:** `oracle_town/jobs/pub_delivery.py` (NOT YET IMPLEMENTED)

**Purpose:** Record decision to append-only ledger (if TRI verdict is SHIP).

**Inputs:**
- `artifacts/tri_verdict.json` (decision)
- Previous ledger state: `oracle_town/ledger/decisions.jsonl`

**Output:**
- `oracle_town/ledger/decisions.jsonl` (APPENDED)
- `artifacts/pub_receipt.json`

**Logic:**
```
If tri_verdict == "SHIP":
  1. Create decision record:
     {
       "id": "dec_20260130_...",
       "date": "2026-01-30",
       "run_id": 174,
       "verdict": "SHIP",
       "reasoning": "...",
       "observation_ids": [...],
       "insight_ids": [...],
       "policy_hash": "sha256:...",
       "decision_hash": "sha256:..."
     }
  2. APPEND (never rewrite) to decisions.jsonl
  3. Git records cumulative growth

If tri_verdict == "NO_SHIP":
  1. No ledger entry
  2. Report: "Decision blocked by TRI gates"
```

---

### 6. MEM_LINK Module (🔲 TODO)
**File:** `oracle_town/jobs/mem_link.py` (NOT YET IMPLEMENTED)

**Purpose:** Update memory graph with entities and relationships.

**Inputs:**
- `artifacts/insights.json` (clusters)
- `oracle_town/memory/index.json` (entity registry)

**Output:**
- `oracle_town/memory/index.json` (UPDATED)
- `oracle_town/memory/entities/*.json` (APPENDED events)
- `artifacts/mem_receipt.json`

**Logic:**
```
For each insight:
  1. Extract entities (persons, projects, decisions, topics)
  2. Create or update entity in memory/index.json
  3. Append event to memory/entities/{entity_id}.json
  4. Link relationships (observed_in, involved_in, blocked_by, similar_to)

Example:
  Insight: "Campaign launch with 500K reach"
  Entities: ["campaign_001", "launch_event_001"]
  Relationships: ["campaign_001" --involved_in--> "marketing_q1_001"]
```

---

### 7. EVO_ADJUST Module (🔲 TODO)
**File:** `oracle_town/jobs/evo_adjust.py` (NOT YET IMPLEMENTED)

**Purpose:** Analyze past decisions and propose policy improvements.

**Inputs:**
- `oracle_town/ledger/decisions.jsonl` (past 30 decisions)
- `oracle_town/memory/` (entity outcomes)

**Output:**
- `artifacts/policy_patch.json` (PROPOSED, not applied)
- `artifacts/evo_receipt.json`

**Logic:**
```
1. Load past 30 decisions
2. For each decision:
   - Check outcome (did it predict correctly?)
   - Measure accuracy
   - Identify patterns
3. Propose policy patches:
   - Adjust anomaly thresholds
   - Reweight cluster clustering
   - Update confidence bounds
4. Status: PROPOSED (never auto-apply)
5. Await Mayor (human) approval
```

---

## Daily Workflow (Complete)

### End-to-End Execution

```bash
# 1. Rotate state
python3 oracle_town/rotate_state.py

# 2. Run complete pipeline
python3 oracle_town/os_runner.py --date 2026-01-30 --run-id 174 --mode daily

# Internally executes:
#   OBS_SCAN    → observations.json + obs_receipt.json
#   INS_CLUSTER → insights.json + ins_receipt.json
#   BRF_ONEPAGER → brief.md + one_bet.txt + brf_receipt.json
#   TRI_GATE    → tri_verdict.json (SHIP or NO_SHIP)
#   [If SHIP]:
#     PUB_DELIVERY → decision_record.jsonl + pub_receipt.json
#     MEM_LINK     → memory/index.json updated
#     EVO_ADJUST   → policy_patch.json (proposed)

# 3. Render output
python3 oracle_town/render_home.py
python3 oracle_town/diff_city.py

# 4. Commit state
git add oracle_town/state/city_*.json
git add oracle_town/ledger/*.jsonl
git add oracle_town/memory/
git commit -m "Run 174: daily OS execution complete"
```

---

## Invariant Verification

### Completed Modules (OBS, INS, BRF)

| Invariant | OBS | INS | BRF | Method |
|-----------|-----|-----|-----|--------|
| I1: Determinism | ✓ | ✓ | ✓ | SHA-256 based IDs, no RNG |
| I4: No Timestamps | ✓ | ✓ | ✓ | Date-only YYYY-MM-DD |
| K5: Determinism | ✓ | ✓ | ✓ | Identical hash on identical inputs |

**Test Results:**
```bash
# All 3 modules pass K5 determinism
python3 oracle_town/jobs/obs_scan.py ... --run 1
python3 oracle_town/jobs/obs_scan.py ... --run 2
# hash_run1 == hash_run2 ✓

# Same for INS and BRF
```

---

## Data Structure Example

### Sample Observation
```json
{
  "id": "obs_20260130_2b17eec49f6d5bd8",
  "date": "2026-01-30",
  "run_id": 174,
  "source": "analytics_dashboard",
  "title": "Weekly Traffic Report - Week 1",
  "body": "Total unique visitors: 45,230...",
  "tags": ["metrics", "performance", "traffic"],
  "confidence": 0.95,
  "links": []
}
```

### Sample Insight (Cluster)
```json
{
  "id": "ins_20260130_ab656edd5c74a1d1",
  "date": "2026-01-30",
  "run_id": 174,
  "cluster": "bounce_direct",
  "theme": "Cluster: Bounce Direct",
  "observation_count": 1,
  "observation_ids": ["obs_20260130_2ec5aa7d7a864c99"],
  "avg_confidence": 0.95,
  "tags": ["metrics", "performance", "traffic"],
  "links": []
}
```

### Sample Insight (Anomaly)
```json
{
  "id": "anom_20260130_10a56a90d0abe18a",
  "date": "2026-01-30",
  "run_id": 174,
  "type": "anomaly",
  "code": "A4",
  "severity": "medium",
  "obs_id": "obs_20260130_93016a7834f411bc",
  "description": "Observable customer/user impact detected",
  "links": []
}
```

### Sample Brief
```markdown
# ORACLE TOWN Brief — Run 000174
**Date:** 2026-01-30

## Key Clusters
- **Cluster: Approved Campaign** (1 obs, conf: 100%)
- **Cluster: Bounce Direct** (1 obs, conf: 95%)
- **Cluster: Affected Connection** (1 obs, conf: 92%)

## 📋 Medium/Low Severity Anomalies
- **A4** [MEDIUM]: Observable customer/user impact detected

## 🎯 Recommendation
**MONITOR**: Cluster: Approved Campaign. Continue observation and analysis.
```

### Sample ONE BET
```
SIGNAL: Approved Campaign.
```

---

## Configuration Files

### Key Registry
**File:** `oracle_town/keys/public_keys.json` (🔲 TODO)

**Purpose:** Register attestor public keys for signature verification.

**Example:**
```json
{
  "obs_attestor_001": {
    "public_key": "ed25519_public_key_hex",
    "class": "obs",
    "status": "active",
    "revoked_at": null
  },
  "ins_attestor_001": {
    "public_key": "ed25519_public_key_hex",
    "class": "ins",
    "status": "active",
    "revoked_at": null
  },
  "brf_attestor_001": {
    "public_key": "ed25519_public_key_hex",
    "class": "brf",
    "status": "active",
    "revoked_at": null
  }
}
```

### Sample Observations
**Directory:** `observations/` (✓ Created)

Contains 3 sample files:
- `sample_email_001.txt` — Email transcript
- `sample_metrics_002.json` — Structured metrics
- `sample_notes_003.md` — Meeting notes

---

## Next Steps

### Immediate (For TRI_GATE Implementation)
1. Create key registry: `oracle_town/keys/public_keys.json`
2. Register attestor keys (need test keys or generate them)
3. Implement TRI_GATE module:
   - Load receipts
   - Verify signatures
   - Enforce K0-K7 gates
   - Decide SHIP/NO_SHIP

### Then (For PUB, MEM, EVO)
1. Implement PUB_DELIVERY
2. Implement MEM_LINK
3. Implement EVO_ADJUST

### Finally (Integration)
1. Hook os_runner.py to execute all 7 jobs in order
2. Test full daily cycle
3. Set up cron for automation

---

## Statistics

### Code Metrics

| Module | Lines | Functions | Determinism |
|--------|-------|-----------|-------------|
| obs_scan.py | 249 | 4 | ✓ K5 verified |
| ins_cluster.py | 342 | 5 | ✓ K5 verified |
| brf_onepager.py | 238 | 6 | ✓ K5 verified |
| **TOTAL** | **829** | **15** | **✓ All tested** |

### Outputs Generated

**Per Run:**
- 4 observations → 4 insights → 6 insight records (4 clusters + 2 anomalies)
- 1 brief (519 chars) + 1 ONE BET (26 chars)
- 3 receipts (OBS, INS, BRF)

**Artifacts Directory:**
- 20+ test files generated (for determinism verification)
- 4 pipeline test files (pipe_*.json)

---

## Status Summary

| Component | Status | Quality | Notes |
|-----------|--------|---------|-------|
| OBS_SCAN | ✓ Complete | Production | K5 determinism verified |
| INS_CLUSTER | ✓ Complete | Production | K5 determinism verified |
| BRF_ONEPAGER | ✓ Complete | Production | K5 determinism verified |
| TRI_GATE | 🔲 TODO | Planning | K0-K7 gate implementation |
| PUB_DELIVERY | 🔲 TODO | Planning | Ledger recording |
| MEM_LINK | 🔲 TODO | Planning | Entity graph building |
| EVO_ADJUST | 🔲 TODO | Planning | Policy analysis |
| os_runner.py | ✓ Scaffold | Ready | DAG orchestrator |
| Integration | 🔲 TODO | Pending | Full pipeline test |

---

**Last Updated:** 2026-01-30
**Phase Completion:** 3 of 7 modules complete
**Next Milestone:** Implement TRI_GATE (cryptographic verification)

