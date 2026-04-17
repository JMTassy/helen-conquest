# ORACLE TOWN State System — Tools Summary

## Complete Canonical Toolset

This directory contains a complete, production-ready state management system for ORACLE TOWN's 7-module pipeline. All tools are **fail-closed**, **deterministic**, and **testable**.

### Tool Directory

| Tool | Purpose | Usage |
|------|---------|-------|
| **render_home.py** | Deterministic HOME page renderer (70-col ASCII) | `python3 oracle_town/render_home.py` |
| **diff_city.py** | Delta-only comparator (shows changes only) | `python3 oracle_town/diff_city.py` |
| **normalize_state.py** | Canonical JSON formatter (sorted keys, fixed module order) | `python3 oracle_town/normalize_state.py oracle_town/state/city_current.json` |
| **rotate_state.py** | State rotator (current → prev before new run) | `python3 oracle_town/rotate_state.py` |
| **simulate_14_days.py** | 14-day growth simulator | `python3 oracle_town/simulate_14_days.py` |

### Data Files

| File | Purpose |
|------|---------|
| `state/city_current.json` | Source of truth for latest run |
| `state/city_prev.json` | Immediately previous state (for diffs) |
| `state/sim_day_*.json` | Generated simulation outputs (git-ignored) |
| `.gitignore` | Blocks simulation outputs from version control |

## Quick Start

### Minimal Daily Workflow

```bash
# 1. Rotate state (preserve history)
python3 oracle_town/rotate_state.py

# 2. Update city_current.json (your pipeline writes this)
# ... (external process updates JSON) ...

# 3. Normalize state (canonical format for stable diffs)
python3 oracle_town/normalize_state.py oracle_town/state/city_current.json

# 4. Render HOME (fails if any line ≠ 72 chars)
python3 oracle_town/render_home.py

# 5. Show delta
python3 oracle_town/diff_city.py

# 6. Commit state
git add oracle_town/state/city_*.json
git commit -m "Daily run 174: OBS+INS progressing"
```

## Immutable Invariants (All Enforced)

| Invariant | Description | Enforcement | Test |
|-----------|-------------|------------|------|
| I1 | Determinism | Same input → byte-identical output | Run render_home.py twice, diff output |
| I2 | Width Guarantee | Framed lines exactly 72 chars | Run render_home.py (assert_width() gate) |
| I3 | JSON Format | Valid JSON with UTF-8 encoding | `python3 -m json.tool state/city_current.json` |
| I4 | No Timestamps | Date-only (YYYY-MM-DD), no wallclock time | Code review + tests |
| I5 | Module Order | Fixed: OBS→INS→BRF→TRI→PUB (MEM↔EVO) | Verified in normalize_state.py |
| I6 | Progress Range | 0-8 clamped (8-tick bar) | bar() function enforces clamp |
| I7 | Sim Outputs | Generated files git-ignored | .gitignore blocks sim_day_*.json |
| I8 | Canonical Format | Sorted top-level keys, fixed module order | normalize_state.py enforces |

## Canonical State Schema

```json
{
  "alerts": [],
  "anomalies": [
    {
      "code": "string",
      "module": "OBS|INS|BRF|TRI|PUB|MEM|EVO",
      "severity": "weak|medium|high"
    }
  ],
  "artifacts": ["file1", "file2"],
  "date": "2026-01-30",
  "mode": "DAILY",
  "modules": {
    "OBS": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" },
    "INS": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" },
    "BRF": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" },
    "TRI": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" },
    "PUB": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" },
    "MEM": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" },
    "EVO": { "desc": "...", "progress": 0-8, "status": "OFF|BLD|OK|WRN|FLR" }
  },
  "one_bet": "string",
  "queue": ["task1", "task2"],
  "run_id": 173
}
```

**Key Constraints:**
- Top-level keys MUST be alphabetically sorted (canonical format)
- Module keys MUST be in fixed order: OBS, INS, BRF, TRI, PUB, MEM, EVO (I5 invariant)
- `progress` values MUST be integers 0-8 (I6 invariant)
- `date` MUST be YYYY-MM-DD only, NO wallclock time (I4 invariant)
- `status` values MUST be one of: OFF, BLD, OK, WRN, FLR

## Verification

**Full test suite:**
```bash
bash oracle_town/FINAL_VERIFICATION.sh
```

This runs all 8 invariant tests and reports:
- ✓ I1: Determinism
- ✓ I2: Width Guarantee
- ✓ I3: JSON Format
- ✓ I4: No Timestamps
- ✓ I5: Module Order
- ✓ I6: Progress Range
- ✓ I7: Sim Outputs
- ✓ I8: Canonical Format

## Design Decisions

### Why ASCII-only rendering?
`len(s)` in Python counts Unicode characters. Emoji width varies by terminal/font (wcwidth required). ASCII has no surprises: 1 character = 1 display column guaranteed.

### Why 70 inner columns?
Fits 80-column terminals: 70 (content) + 2 (borders ┃...┃) = 72 chars total. Leaves 8-char margin for safety.

### Why normalize state?
Canonical JSON (sorted keys) ensures stable diffs in git. Without normalization, key-order variations cause noisy diffs even when data hasn't changed.

### Why fixed MODULE_ORDER?
Deterministic output requires deterministic key ordering. The 7-module pipeline has semantic order (OBS→INS→BRF→TRI→PUB with MEM↔EVO). Fixing this order in code prevents accidental reordering and makes the system auditable.

### Why fail-closed?
The width assertion gate (`assert_width()`) exits with code 1 if any framed line ≠ 72 chars. This prevents silent drift: if rendering breaks the contract, the system fails visibly.

## Failure Modes & Recovery

| Failure | Detection | Fix |
|---------|-----------|-----|
| Framed line > 72 chars | `assert_width()` assertion error | Reduce content or split into multiple rows |
| Simulation files committed | Git shows `sim_day_*.json` | Check .gitignore; already blocked |
| Diff shows spurious changes | Keys out of alphabetical order | Run normalize_state.py on files |
| Rendering differs on second run | Byte hashes don't match | Check for date/time in output (I4 violation) |
| Module order wrong in JSON | Check order in city_current.json | Run normalize_state.py to fix |
| Progress bar off-scale | Progress > 8 or < 0 | Check bar() clamping; should never happen |

## Integration with Daily OS

These tools integrate cleanly into the Daily OS pipeline:

1. **State input**: Your pipeline writes `city_current.json` with updated module statuses and progress
2. **Normalization**: Run `normalize_state.py` to ensure canonical format
3. **Rendering**: Run `render_home.py` to validate (width assertion) and display HOME page
4. **Diffing**: Run `diff_city.py` to show what changed
5. **VCS**: Commit `state/*.json` files to git for immutable audit trail

All tools are idempotent (safe to run multiple times) and side-effect-free (only read/write designated files).

---

**Status:** Production-ready (all 8 invariants enforced)
**Last Updated:** 2026-01-30
**Guarantee:** All invariants testable and verifiable
