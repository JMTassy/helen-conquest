# Mode A: Daily Emulation Loop (Observe-Only)

**Status:** Governance observes, analyzes, learns. Zero execution. Zero authority.

## Overview

Mode A is the safe operating mode for ORACLE TOWN: produce daily briefs, trend analysis, and immutable ledger entries—but never grant execution authority.

```
Observations (artifacts/)
  ↓
OBS_SCAN → INS_CLUSTER → BRF_ONEPAGER → TREND_MEMORY
  ↓
[TRI Gate] → REJECT (expected)
[Mayor Signs] → Receipt (world_mutation_allowed=false)
  ↓
Ledger (immutable record of "what would have happened")
```

**Key Property:** Even with zero execution, you get:
- Daily briefs you can read/share
- 7-day cluster trends (what's persistent, new, fading)
- Full audit trail (all decisions recorded)
- Determinism checks (K5 verification)

## Running Daily Emulation Loop

### Quick Start

```bash
cd "JMT CONSULTING - Releve 24"
bash oracle_town/daily_emulation_loop.sh
```

This:
1. Reads observations from `artifacts/` directory
2. Runs OBS_SCAN → INS_CLUSTER → BRF_ONEPAGER
3. Compares today's clusters to 7-day history (TREND_MEMORY)
4. Runs through TRI Gate + Mayor signature
5. Stores brief in `oracle_town/ledger/briefs/brief_YYYY-MM-DD.json`
6. Outputs hashes for determinism verification

### Expected Output

```
=== Mode A: Daily Emulation Loop ===
Date: 2026-01-30
Run ID: emu_2026-01-30

[1/5] OBS_SCAN: Normalize observations...
[2/5] INS_CLUSTER: Cluster insights...
[3/5] BRF_ONEPAGER: Synthesize brief...
[4/5] TREND_MEMORY: Compare to 7-day history...
[5/5] Authority Chain (TRI + Mayor)...

=== Determinism Check (K5) ===
OBS_SCAN:     [SHA-256 hash]
INS_CLUSTER:  [SHA-256 hash]
BRF_ONEPAGER: [markdown format]
TREND_MEMORY: [SHA-256 hash]

Brief (read-only):
# ORACLE TOWN Brief — Run 000175
**Date:** 2026-01-30
## Key Clusters
...

Trend Report (JSON):
{
  "signal_strength": 75,
  "stability": "high",
  "recommendation": "INVESTIGATE"
}

Expected TRI Verdict:
Decision: REJECT (no authority)

Expected Receipt:
Decision: REJECT | Mutation Allowed: false

=== End Mode A Emulation Loop ===
```

## Observations Format

Place observation files in `artifacts/` directory. Format: plain text, one per file.

```bash
artifacts/
├── obs_marketing_email.txt
├── obs_infrastructure_metrics.txt
└── obs_customer_feedback.txt
```

Each file should contain a single observation (paragraph or bullet list).

### Example Observation

```
Marketing campaign "Q1 Growth Initiative" launched Tuesday.
Target: 10K sign-ups, 15% conversion.
Current: 3.2K sign-ups, 12% conversion after 48 hours.
Status: On track, monitoring daily.
```

## Trend Memory: 7-Day Clustering

**What It Does:**

For each run, TREND_MEMORY compares today's clusters to the past 7 days and identifies:

1. **NEW** — First appearance today
2. **PERSISTENT** — Seen N days in a row (signal strength indicator)
3. **FADING** — Was present, now absent for 2+ days
4. **ANOMALY_RECUR** — Anomaly pattern repeating

### Example Output

```json
{
  "analysis": {
    "new_clusters": ["API Performance"],
    "persistent_clusters": {
      "Marketing Campaigns": 5,
      "Infrastructure Health": 3,
      "Security Alerts": 2
    },
    "fading_clusters": [
      {
        "cluster": "Customer Sentiment",
        "last_seen_days_ago": 3
      }
    ]
  },
  "summary": {
    "signal_strength": 75,
    "stability": "high",
    "recommendation": "CONTINUE_MONITORING"
  }
}
```

### Recommendation Logic

| Scenario | Recommendation |
|----------|---|
| 3+ persistent clusters, 0 new | `CONTINUE_MONITORING` |
| 2+ persistent, 1 new | `CONTINUE_MONITORING` |
| More new than persistent | `INVESTIGATE` |
| Fading cluster reappears | `INVESTIGATE` |
| Signal strength < 50% | `ALERT` |

## Ledger Structure

Every Mode A run creates immutable records:

```
oracle_town/ledger/
├── briefs/
│   ├── brief_2026-01-24.json
│   ├── brief_2026-01-25.json
│   └── brief_2026-01-30.json
└── 2026/01/
    └── claim_emu_2026-01-30_daily_brief/
        ├── claim.json         (proposal)
        ├── tri_verdict.json   (unsigned verification)
        └── mayor_receipt.json (signed REJECT receipt)
```

**Note:** All Mode A claims are expected to be REJECT (no authority for emulation claims). This is correct. The ledger records the decision, not the outcome.

## Determinism Verification (K5)

After each run, hashes are computed for all outputs:

```bash
OBS_SCAN:     abc123def456...
INS_CLUSTER:  789xyz...
BRF_ONEPAGER: markdown (no hash)
TREND_MEMORY: fedcba987...
```

**If hashes differ on re-run with same inputs:** There's a non-determinism bug. Fix before anything else.

To re-verify manually:

```bash
python3 -c "
import json, hashlib
data = json.load(open('/tmp/obs_out.json'))
print(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
"
```

## Automation: Cron Scheduling

Run Mode A daily at 9 AM:

```bash
# Add to crontab
0 9 * * * cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24" && bash oracle_town/daily_emulation_loop.sh >> /tmp/mode_a_log.txt 2>&1
```

Or run every 6 hours for continuous monitoring:

```bash
0 */6 * * * cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24" && bash oracle_town/daily_emulation_loop.sh >> /tmp/mode_a_log.txt 2>&1
```

## Operational Value

Even though Mode A **never executes**, it provides:

1. **Discovery** — What observations cluster together? What's novel?
2. **Tracking** — Which themes persist? Which fade?
3. **Audit Trail** — Full immutable record of reasoning
4. **Hardening Foundation** — When you move to Mode B (with authority), all decisions replay deterministically
5. **Intelligence** — Trend memory gives you signal over noise

## Next Steps (Mode B: With Authority)

When you're ready to allow execution:

1. Register attestor keys in `oracle_town/keys/public_keys.json`
2. Set policy: `--policy-hash` points to actual frozen policy
3. Change claim `"scope"` from `"read-only"` to `"execute"`
4. Mode B claims will ACCEPT (not REJECT) and set `world_mutation_allowed=true`

But Mode A runs indefinitely. Pure observation, pure safety.

---

**Command Reference:**

```bash
# Run single daily cycle
bash oracle_town/daily_emulation_loop.sh

# Run one component in isolation
python3 oracle_town/jobs/obs_scan.py --help
python3 oracle_town/jobs/ins_cluster.py --help
python3 oracle_town/jobs/brf_onepager.py --help
python3 oracle_town/jobs/trend_memory.py --help

# Check yesterday's brief
cat oracle_town/ledger/briefs/brief_2026-01-29.json

# View trend analysis
python3 -c "import json; print(json.dumps(json.load(open('/tmp/trend_report.json'))['summary'], indent=2))"
```

---

**Mode A Status:** ✓ Live. Running daily.
