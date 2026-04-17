# NPC DASHBOARD — CLI Guide

**Purpose:** Terminal interface for viewing NPC observations, metrics, and amendment eligibility.

**Design:** Scriptable, auditable, deterministic output. No GUI ambiguity.

---

## Quick Start

```bash
# Show executive summary
python3 oracle_town/npc_dashboard_cli.py

# Show current observations
python3 oracle_town/npc_dashboard_cli.py show-observations

# Show all metrics
python3 oracle_town/npc_dashboard_cli.py show-metrics

# Check amendment eligibility
python3 oracle_town/npc_dashboard_cli.py show-amendment-eligibility
```

---

## Commands

### `show-observations` (Default)

**Shows:** Most recent NPC observation report

**Output:**
- Observation period (dates)
- All four NPC measurements
- Confidence levels
- System health assessment
- Exception creep status

**Use when:** You want to see what NPCs observed in the current/latest 90-day window

**Example:**
```bash
$ python3 oracle_town/npc_dashboard_cli.py show-observations

======================================================================
                        NPC OBSERVATIONS
======================================================================

Report Period: 2026-01-31 → 2026-04-30
Timestamp:     2026-04-30T23:59:59Z
Doctrine:      v1.0
Duration:      90 days

Observations:

  ACCURACY_WATCHER
    Metric:      accept_outcome_success_rate
    Measurement: 0.71
    Confidence:  HIGH
    Notes:       Of 24 ACCEPT verdicts issued Jan-Apr, 17 outcomes succeeded...

  SPECULATION_TRACKER
    Metric:      capital_at_risk
    Measurement: 700000 EUR
    Confidence:  HIGH
    Notes:       Single active CLASS_III override tracked...

  ...
```

---

### `show-metrics`

**Shows:** All NPC metrics organized by type

**Output:**
- Each NPC type with its metrics
- Measured values
- Confidence levels
- Easy scanning for specific metrics

**Use when:** You want to see all measurements at a glance

**Example:**
```bash
$ python3 oracle_town/npc_dashboard_cli.py show-metrics

======================================================================
                          NPC METRICS BY TYPE
======================================================================

AccuracyWatcher (Verdict Alignment)
  • accept_outcome_success_rate
    Value:      0.71
    Confidence: HIGH

  • false_positive_rate
    Value:      0.29
    Confidence: HIGH

SpeculationTracker (Override Performance)
  • capital_at_risk
    Value:      700000 EUR
    Confidence: HIGH

  ...
```

---

### `show-history`

**Shows:** All historical 90-day observation reports

**Output:**
- Each report with dates, timestamp, health status
- Which NPCs reported in each period
- Chronological order (newest first)

**Use when:** You want to see trend across multiple observation periods

**Example:**
```bash
$ python3 oracle_town/npc_dashboard_cli.py show-history

======================================================================
                       OBSERVATION HISTORY (90-Day Reports)
======================================================================

Available Reports:

1. 2026-01-31 → 2026-04-30
   Reported: 2026-04-30T23:59:59Z
   Health:   STABLE
   NPCs:     accuracy_watcher, speculation_tracker, pattern_detector, risk_analyzer
```

---

### `show-amendment-eligibility`

**Shows:** Whether sufficient NPC evidence exists to propose an amendment

**Output:**
- Current NPC count (require ≥2)
- Observation window duration (require ≥90 days)
- Doctrine version
- Pass/fail on each requirement
- Next steps

**Use when:** You're considering proposing an amendment

**Example:**
```bash
$ python3 oracle_town/npc_dashboard_cli.py show-amendment-eligibility

======================================================================
                       AMENDMENT ELIGIBILITY STATUS
======================================================================

Current Status:
  NPC Types Reporting: 4 (require ≥2)
  Observation Window:  90 days (require ≥90)
  Doctrine Version:    1.0
  Status:              ✓ POTENTIALLY ELIGIBLE

Requirements for Amendment Proposal:
  ✓ ≥2 distinct NPC types:    PASS
  ✓ ≥90 consecutive days:     PASS
  ✓ Same doctrine section:    (check in proposal)

Next Steps:
  • Next observation period ends: 2026-07-31
  • Gather evidence pointing to specific doctrine section
  • Fill AMENDMENT_A_TEMPLATE.md when evidence supports change
```

---

### `show-silence`

**Shows:** Periods when NPCs reported nothing (silence is valid output)

**Output:**
- Which NPCs were silent
- Time periods
- Reasons for silence
- Explanation of why silence matters

**Use when:** You want to understand what NPCs did NOT observe

**Example:**
```bash
$ python3 oracle_town/npc_dashboard_cli.py show-silence

======================================================================
                         NPC SILENCE ANALYSIS
======================================================================

Why silence matters:
  • Silence = no anomalies detected
  • Silence is valid output (not absence of observation)
  • System is working normally when NPCs have nothing to report
```

---

### `show-summary`

**Shows:** Executive summary (default if no command)

**Output:**
- Latest report metadata
- All observations listed
- System health status
- Next observation window dates

**Use when:** You want a quick overview

**Example:**
```bash
$ python3 oracle_town/npc_dashboard_cli.py show-summary

======================================================================
                         NPC DASHBOARD SUMMARY
======================================================================

Report:
  Window:    2026-01-31 → 2026-04-30 (90 days)
  Generated: 2026-04-30T23:59:59Z

NPC Observations:
  • accuracy_watcher: accept_outcome_success_rate
  • speculation_tracker: capital_at_risk
  • pattern_detector: class_distribution
  • risk_analyzer: override_frequency

System Health:
  Status:      STABLE
  Adherence:   HIGH
  Exception:   Not detected

Next Observation Window:
  Start: May 1, 2026
  End:   July 31, 2026
  Days:  92 days
```

---

## Output Format

All output is:
- **Deterministic** — Same input always produces identical output
- **Text-based** — No rendering ambiguity, easy to parse
- **Color-coded** — Green (healthy), Yellow (caution), Red (alert)
- **Auditable** — Can be logged, piped, or archived

---

## Scripting Examples

### Check if system is healthy
```bash
python3 oracle_town/npc_dashboard_cli.py show-summary | grep "Status:" | grep "STABLE"
if [ $? -eq 0 ]; then
  echo "System is stable"
else
  echo "System shows drift"
fi
```

### Export latest report
```bash
python3 oracle_town/npc_dashboard_cli.py show-observations > npc_report_$(date +%Y-%m-%d).txt
```

### Monitor amendment eligibility
```bash
watch -n 3600 "python3 oracle_town/npc_dashboard_cli.py show-amendment-eligibility"
# Checks every hour if amendment eligibility changes
```

### Check for exception creep
```bash
python3 oracle_town/npc_dashboard_cli.py show-observations | grep -i "exception"
```

---

## Integration with Governance Workflow

**Step 1:** Run dashboard monthly
```bash
python3 oracle_town/npc_dashboard_cli.py show-observations
```

**Step 2:** Check amendment eligibility
```bash
python3 oracle_town/npc_dashboard_cli.py show-amendment-eligibility
```

**Step 3:** If eligible, review history
```bash
python3 oracle_town/npc_dashboard_cli.py show-history
```

**Step 4:** If evidence supports amendment, fill template
```bash
# Open AMENDMENT_A_TEMPLATE.md
# Reference NPC observations from dashboard
# Complete all three gates
```

**Step 5:** At 90-day boundary, collect new report
```bash
# NPCs auto-generate new report
python3 oracle_town/npc_dashboard_cli.py show-observations
```

---

## Data Sources

Dashboard reads from:
- `oracle_town/ledger/observations/` — All NPC observation reports
- DOCTRINE_V1.0 — Baseline document (for reference)

Dashboard does NOT:
- Write to ledger
- Modify observations
- Execute commands
- Change system state

---

## Determinism Testing

All dashboard commands produce deterministic output:

```bash
# Run command twice
python3 oracle_town/npc_dashboard_cli.py show-observations > output1.txt
python3 oracle_town/npc_dashboard_cli.py show-observations > output2.txt

# Compare (should be identical)
diff output1.txt output2.txt
# Result: no differences (deterministic)
```

---

## Color Meanings

| Color | Meaning |
|-------|---------|
| **Green** | Healthy, passing, no issues |
| **Yellow** | Caution, under threshold, review |
| **Red** | Alert, failing, action needed |
| **Cyan** | Headers, structure, organization |
| **Blue** | Data, values, references |

---

## Next Steps

Once you understand NPC observations:

1. **Wait for next period** (May 1 - July 31, 2026)
2. **Monitor system health** (use dashboard monthly)
3. **Gather amendment evidence** (if drift detected)
4. **Propose amendment** (when three gates can be satisfied)
5. **Ratify or reject** (explicit vote required)

---

**NPC DASHBOARD — CLI GUIDE**
**Status:** Operational
**Version:** 1.0
**Last Updated:** January 31, 2026
