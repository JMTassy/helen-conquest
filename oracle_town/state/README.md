# ORACLE TOWN State Management System

Deterministic, diffable, git-friendly city state visualization for ORACLE TOWN Daily OS.

## Overview

This directory (`/oracle_town/state/`) manages the persistent state of ORACLE TOWN's 7-module system:
- **OBS** (Observation Collector)
- **INS** (Insight Engine)
- **BRF** (Brief Factory)
- **TRI** (Tribunal)
- **PUB** (Publisher)
- **MEM** (Memory Linker)
- **EVO** (Self-Evolution)

All state is stored as **JSON** and rendered deterministically as **ASCII/Unicode terminal output** (≤70 columns).

---

## Core Files

### State Files (JSON)

**`city_prev.json`** — Previous run state
- Blueprint for diff comparison
- Updated by `rotate_state.py` before each run
- Contains: date, run_id, module statuses, queue, alerts, anomalies

**`city_current.json`** — Current run state
- Single source of truth for town state
- Updated by your Daily OS pipeline
- Schema identical to `city_prev.json`

**Structure Example:**
```json
{
  "date": "2026-01-30",
  "run_id": 173,
  "mode": "DAILY",
  "one_bet": "BRF v1: Home ASCII + City Growth",
  "queue": ["OBS scan", "INS cluster", "BRF draft"],
  "alerts": [],
  "anomalies": [
    {"type": "digest_drift", "severity": "weak", "module": "INS"}
  ],
  "modules": {
    "OBS": {"status": "OK", "progress": 8, "desc": "12 notes -> 5 claims"},
    "INS": {"status": "OK", "progress": 6, "desc": "3 themes + 1 anomaly"},
    "BRF": {"status": "BLD", "progress": 2, "desc": "drafted brief v1"},
    "TRI": {"status": "OFF", "progress": 0, "desc": ""},
    ...
  },
  "artifacts": []
}
```

### Render Scripts

**`render_home.py`** — Basic 70-column ASCII renderer (stable)
- Loads `city_current.json`
- Produces deterministic HOME page
- No emoji, pure ASCII
- Usage: `python3 render_home.py`

**`render_home_enhanced.py`** — Enhanced renderer with symbols & glyphs
- Loads `city_current.json`
- Supports two modes:
  - `--ascii`: ASCII-safe (✓▲!✗·· badges, no emoji)
  - `--unicode`: Unicode-enhanced (emoji + symbols in dedicated columns)
- **Glyphs:**
  - Role icons: 👁 OBS, 🧠 INS, 📝 BRF, ⚖ TRI, 📣 PUB, 🗃 MEM, 🧬 EVO
  - Status badges: ✓ OK, ▲ BLD, ! WRN, ✗ FLR, · OFF
  - Gravity symbols: ⚠ alerts, 🕳 anomalies
  - Ritual sigils: ⟐∿ ⊕ ∴ ⧉
- **Width-safe:** Uses `wcwidth` for emoji (counts emoji as 2 cols)
- Usage:
  - `python3 render_home_enhanced.py --unicode` (default)
  - `python3 render_home_enhanced.py --ascii`

### State Management Scripts

**`rotate_state.py`** — State rotation (before each run)
- Moves `city_current.json` → `city_prev.json`
- Backs up previous state for diff comparison
- Returns previous run metadata
- Usage: `python3 rotate_state.py`

**`diff_city.py`** — Diff viewer (delta-only output)
- Compares `city_prev.json` vs `city_current.json`
- Prints only changed modules/statuses
- Git-friendly (minimal noise)
- Usage: `python3 diff_city.py`

**`simulate_14_days.py`** — 14-day growth simulator
- Generates 14 pairs of state files: `sim_day_XX_prev.json` + `sim_day_XX_current.json`
- Progressive unlocking: 1 module per day (max)
- Days 1-7: New module unlocks (OBS→INS→BRF→TRI→PUB→MEM→EVO)
- Days 8-14: Continuous refinement (no new unlocks)
- Usage: `python3 simulate_14_days.py`

---

## Workflows

### Daily Run Workflow

```bash
# 1. Rotate state (preserve history)
python3 rotate_state.py

# 2. Run ORACLE TOWN Daily OS pipeline
#    (updates city_current.json with new run data)
python3 oracle_town/os_runner.py --mode daily

# 3. Render HOME page
python3 state/render_home_enhanced.py --unicode

# 4. View diffs
python3 state/diff_city.py

# 5. Commit to git
git add oracle_town/state/city_*.json
git commit -m "Daily OS run 173: OBS+INS+BRF progressing"
```

### Simulation Workflow

```bash
# Generate 14 days of simulated growth
python3 simulate_14_days.py

# Render Day 7 (all modules unlocked)
python3 << 'EOF'
import json
from render_home_enhanced import render

with open('sim_day_07_current.json') as f:
    state = json.load(f)

lines = render(state, mode='unicode')
for line in lines:
    print(line)
EOF

# View Day 7 diffs
python3 << 'EOF'
import json
from diff_city import diff
# Load sim_day_06_current.json and sim_day_07_current.json, compare
EOF
```

---

## Module Status Lifecycle

Each module progresses through states:

```
OFF  → BLD  → OK  (normal flow)
       ↓
      WRN  → OK  (warning, recovering)
       ↓
      FLR     (failed, blocked)
```

**Status Meanings:**
- **OFF** — Not yet unlocked
- **BLD** — Building/initializing (progress 0-7)
- **OK** — Operational (progress 8)
- **WRN** — Warning/degraded (progress 4-7, recovery path)
- **FLR** — Failed/blocked (progress 0-1, requires intervention)

**Progress Bar:**
- 8-tick bar: `████████` (0-8 filled ticks, then empty)
- Updated independently of status
- Used for partial completion tracking

---

## Constraints (Immutable)

These constraints ensure determinism, diffability, and git-friendliness:

1. **≤70 Column Width** — All rendered lines fit in 70-char terminal (plus 2-char borders)
2. **Deterministic Rendering** — Same JSON input always produces identical output
3. **Emoji-Safe Width** — Emoji counted as 2 columns (via `wcwidth` library)
4. **No Timestamps** — State uses `date` field only (format: YYYY-MM-DD)
5. **JSON-Only State** — No YAML, TOML, or mixed formats
6. **Module Order Fixed** — Always OBS, INS, BRF, TRI, PUB, MEM, EVO
7. **1-Module-Per-Day Max** — Simulator respects realistic growth constraints

---

## Examples

### Current State (Day 1)

```json
{
  "date": "2026-01-30",
  "run_id": 173,
  "one_bet": "BRF v1: Home ASCII + City Growth",
  "modules": {
    "OBS": {"status": "OK", "progress": 8, "desc": "12 notes -> 5 claims"},
    "INS": {"status": "OK", "progress": 6, "desc": "3 themes + 1 anomaly"},
    "BRF": {"status": "BLD", "progress": 2, "desc": "drafted brief v1"},
    "TRI": {"status": "OFF", "progress": 0, "desc": ""},
    "PUB": {"status": "OFF", "progress": 0, "desc": ""},
    "MEM": {"status": "OFF", "progress": 0, "desc": ""},
    "EVO": {"status": "OFF", "progress": 0, "desc": ""}
  }
}
```

### Rendered Output (Unicode Mode)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ORACLE TOWN — HOME  2026-01-30  DAILY  000173                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ONE BET : BRF v1: Home ASCII + City Growth                            ┃
┃QUEUE(≤7): OBS scan | INS cluster | BRF draft                        ┃
┃⚠:0  🕳:1 (digest_drift/weak)                                        ┃
┃⸻ SIGILS: ⟐∿ ⊕ ∴ ⧉                                              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃MOD │ ◆ │ ST │ PROG     │ NOTES                                  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃OBS │ 👁 │ ✓ │ ████████ │ 12 notes -> 5 claims           ┃
┃INS │ 🧠 │ ✓ │ ██████░░ │ 3 themes + 1 anomaly           ┃
┃BRF │ 📝 │ ▲ │ ██░░░░░░ │ drafted brief v1               ┃
┃TRI │ ⚖ │ · │ ░░░░░░░░ │                                ┃
┃PUB │ 📣 │ · │ ░░░░░░░░ │                                ┃
┃MEM │ 🗃 │ · │ ░░░░░░░░ │                                ┃
┃EVO │ 🧬 │ · │ ░░░░░░░░ │                                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃(no artifacts)                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Rendered Output (ASCII Mode)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ORACLE TOWN — HOME  2026-01-30  DAILY  000173                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ONE BET : BRF v1: Home ASCII + City Growth                            ┃
┃QUEUE(≤7): OBS scan | INS cluster | BRF draft                        ┃
┃A:0  o:1 (digest_drift/weak)                                          ┃
┃⸻ SIGILS: ⟐∿ ⊕ ∴ ⧉                                              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃MOD │ ST │ PROG     │ NOTES                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃OBS │ ✓ │ ████████ │ 12 notes -> 5 claims                 ┃
┃INS │ ✓ │ ██████░░ │ 3 themes + 1 anomaly                 ┃
┃BRF │ ^ │ ██░░░░░░ │ drafted brief v1                      ┃
┃TRI │ - │ ░░░░░░░░ │                                       ┃
┃PUB │ - │ ░░░░░░░░ │                                       ┃
┃MEM │ - │ ░░░░░░░░ │                                       ┃
┃EVO │ - │ ░░░░░░░░ │                                       ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃(no artifacts)                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Diff Output

```
DIFF: 2026-01-29 (run 172) → 2026-01-30 (run 173)

- ONE_BET: Init: OBS only
+ ONE_BET: BRF v1: Home ASCII + City Growth

MODULE CHANGES:
  - OBS | ████░░░░ | setup
  + OBS | ████████ | 12 notes -> 5 claims
  - INS | ░░░░░░░░ |
  + INS | ██████░░ | 3 themes + 1 anomaly
  - BRF | ░░░░░░░░ |
  + BRF | ██░░░░░░ | drafted brief v1

QUEUE CHANGE:
  - []
  + ['OBS scan', 'INS cluster', 'BRF draft']

ANOMALIES CHANGE:
  + digest_drift/weak
```

---

## Git Integration

All state files are JSON, making them perfectly diffable:

```bash
# See what changed between runs
git diff city_prev.json city_current.json

# See full history
git log --oneline oracle_town/state/city_current.json

# Revert to previous state
git checkout HEAD~1 oracle_town/state/city_current.json
```

---

## Testing

Verify the system works:

```bash
# Test render (basic)
python3 render_home.py

# Test render (enhanced, unicode)
python3 render_home_enhanced.py --unicode

# Test render (enhanced, ascii)
python3 render_home_enhanced.py --ascii

# Test diff
python3 diff_city.py

# Test rotation
python3 rotate_state.py

# Test simulation (14 days)
python3 simulate_14_days.py
ls sim_day_*.json | wc -l  # Should show 28 files
```

---

## Future Extensions

1. **Artifact Tracking** — Store build outputs, reports, receipts in `artifacts` field
2. **Event Log** — Per-module event history (append-only)
3. **Metrics Dashboard** — Accuracy, latency, success rates over time
4. **Export Formats** — HTML, Markdown, CSV snapshots (from JSON state)
5. **State Validation** — JSON schema enforcement
6. **Replay Mode** — Replayable state history for auditing

---

## References

- Parent: `/oracle_town/` — ORACLE TOWN Daily OS
- CLAUDE.md: Project documentation
- IMPLEMENTATION_ROADMAP.md: 8-week phased plan

---

**Status:** Complete and production-ready

**Constraints Enforced:**
- ✅ ≤70 column width (hard)
- ✅ Deterministic rendering
- ✅ Emoji-safe (wcwidth)
- ✅ JSON state (diffable, git-friendly)
- ✅ No timestamps in state
- ✅ Module order fixed
- ✅ 1-module-per-day max in simulator

**Last Updated:** 2026-01-30
