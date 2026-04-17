# ORACLE TOWN State Management — Implementation Complete

## Executive Summary

The canonical state management system is **production-ready** with all 8 immutable invariants enforced and verified. This system provides deterministic, git-friendly state snapshots for ORACLE TOWN's 7-module governance pipeline.

**Commit:** `835f17f` — state: canonical state management system with 8 enforced invariants

---

## What Was Delivered

### Core Tools (5 executables)

1. **render_home.py** (6.5 KB)
   - Deterministic ASCII renderer for HOME page
   - Enforces I2 invariant: all framed lines exactly 72 chars
   - `assert_width()` gate exits with code 1 on violation
   - No LLM calls, no I/O beyond reading JSON

2. **normalize_state.py** (2.2 KB)
   - Canonical JSON formatter enforcing I8 invariant
   - Sorts top-level keys alphabetically
   - Preserves MODULE_ORDER for modules dict (I5 invariant)
   - Custom JSON encoder handles nested sorting
   - Usage: `python3 oracle_town/normalize_state.py state/city_current.json`

3. **diff_city.py** (2.7 KB)
   - Delta-only comparator showing only changed modules
   - Reduces git noise compared to full-file diffs
   - Works with `rotate_state.py` to show what changed

4. **rotate_state.py** (789 B)
   - Copies current → prev before new run
   - Preserves history for diff comparison
   - Essential first step in daily workflow

5. **simulate_14_days.py** (2.9 KB)
   - Generates 28 simulation state files (14 days × 2)
   - All outputs git-ignored (I7 invariant)
   - Used for forward-looking analysis

### State Files (2 canonical examples)

- **state/city_current.json** (source of truth)
- **state/city_prev.json** (immediately previous)
- Both normalized to canonical format (I8)

### Documentation (3 specs)

1. **STATE_SYSTEM_CANONICAL.md** (7.5 KB)
   - Contract document defining all invariants
   - Procedural verification commands (not claims)
   - Failure modes & recovery strategies
   - Key design decisions explained

2. **TOOLS_SUMMARY.md** (5.1 KB)
   - Quick reference for all tools
   - Schema definition for state JSON
   - Daily workflow checklist
   - Integration guidance

3. **FINAL_VERIFICATION.sh** (2.2 KB)
   - Comprehensive test harness
   - Tests all 8 invariants
   - Exits 0 on success, 1 on failure

### Configuration

- **.gitignore**
  - Blocks `state/sim_day_*.json` (generated, not committed)
  - Also blocks Python cache (\_\_pycache\_\_, .pyc files)

---

## All 8 Invariants Enforced

| # | Invariant | Enforcement | Test |
|---|-----------|------------|------|
| I1 | **Determinism** | Same input → identical output bytes | `python3 oracle_town/render_home.py > out1.txt` (2×, diff) |
| I2 | **Width Guarantee** | Framed lines exactly 72 chars | `python3 oracle_town/render_home.py` (assert_width gate) |
| I3 | **JSON Format** | Valid JSON, UTF-8, 2-space indent | `python3 -m json.tool state/city_current.json` |
| I4 | **No Timestamps** | Date-only (YYYY-MM-DD), no wallclock | Code review (render_home.py has no time calls) |
| I5 | **Module Order** | Fixed OBS→INS→BRF→TRI→PUB, MEM↔EVO | `normalize_state.py` preserves order + verification |
| I6 | **Progress Range** | 0-8 clamped (8-tick bar) | `bar()` function enforces clamp(0, 8) |
| I7 | **Sim Outputs** | Generated files git-ignored | `.gitignore` blocks `sim_day_*.json` |
| I8 | **Canonical Format** | Sorted top-level keys, fixed module order | `normalize_state.py` + custom JSON encoder |

**Verification:** `bash oracle_town/FINAL_VERIFICATION.sh`

```
✓ I1: Determinism (byte-identical output)
✓ I2: Width Guarantee (assert_width() gate active)
✓ I3: JSON Format (valid JSON)
✓ I4: No Timestamps (date-only, no time)
✓ I5: Module Order (fixed OBS→EVO)
✓ I6: Progress Range (0-8 clamped)
✓ I7: Sim Outputs (.gitignore blocks them)
✓ I8: Canonical Format (sorted keys, stable diffs)
```

---

## Key Technical Decisions

### 1. ASCII-only Rendering (I2 invariant)
- Python's `len(s)` counts Unicode codepoints, not display columns
- Emoji width varies by terminal/font (wcwidth required)
- ASCII guarantees: 1 character = 1 display column
- Width assertion becomes portable and verifiable

### 2. 70 Inner Columns
- Total frame width: 72 chars (70 + 2 borders ┃...┃)
- Fits 80-column terminals (70 + 2 + 8-char safety margin)
- Prevents overflow on legacy terminals

### 3. Fail-Closed Assertion Gate
- `assert_width()` function checks all lines
- Exits with code 1 if ANY framed line ≠ 72 chars
- Prevents silent drift: violation is immediately visible
- Enforced in `main()` BEFORE printing

### 4. Canonical JSON Format (I8 invariant)
- `sort_keys=True` for all keys EXCEPT modules list
- Custom `CanonicalEncoder` preserves MODULE_ORDER
- Ensures stable diffs in git (no key-order churn)
- Determinism requires deterministic key ordering

### 5. Custom JSON Encoder
- Standard `json.dumps(..., sort_keys=True)` sorts ALL keys
- Breaks I5 invariant (MODULE_ORDER would be alphabetized)
- Solution: `CanonicalEncoder` class that:
  - Sorts top-level keys alphabetically
  - Preserves MODULE_ORDER for modules dict
  - Recursively sorts nested dicts (except modules)

---

## Daily Workflow Integration

```bash
# 1. Rotate state (preserve history for diff)
python3 oracle_town/rotate_state.py

# 2. Update city_current.json (your pipeline writes this)
# ... external process updates JSON ...

# 3. Normalize state (canonical format)
python3 oracle_town/normalize_state.py oracle_town/state/city_current.json

# 4. Render HOME (width assertion gate)
python3 oracle_town/render_home.py

# 5. Show delta
python3 oracle_town/diff_city.py

# 6. Commit state
git add oracle_town/state/city_*.json
git commit -m "Daily run 174: state updated"
```

Each tool is:
- **Idempotent** (safe to run multiple times)
- **Side-effect-free** (only reads/writes designated files)
- **Deterministic** (same input → same output)
- **Fail-closed** (exits 1 on violation, not silent)

---

## Files by Size

```
oracle_town/
├── normalize_state.py           2.2 KB  (custom JSON encoder + normalizer)
├── render_home.py               6.5 KB  (deterministic renderer)
├── diff_city.py                 2.7 KB  (delta comparator)
├── rotate_state.py              0.8 KB  (state rotator)
├── simulate_14_days.py          2.9 KB  (simulator)
├── .gitignore                   0.3 KB  (blocks sim_day_*.json)
├── STATE_SYSTEM_CANONICAL.md    7.5 KB  (contract document)
├── TOOLS_SUMMARY.md             5.1 KB  (quick reference)
├── FINAL_VERIFICATION.sh        2.2 KB  (test harness)
├── IMPLEMENTATION_COMPLETE.md   (this file)
└── state/
    ├── city_current.json        1.6 KB  (source of truth)
    └── city_prev.json           1.6 KB  (previous state)
```

**Total:** ~33 KB of code + documentation (highly focused, no fluff)

---

## Quality Assurance

### Tests Run
- ✓ I1: Determinism (2 runs, byte-compare)
- ✓ I2: Width gate (assert_width fires on violations)
- ✓ I3: JSON validity (json.tool validation)
- ✓ I4: No timestamps (code inspection, no time imports)
- ✓ I5: Module order (verified in normalized JSON)
- ✓ I6: Progress clamp (bar() function enforces)
- ✓ I7: .gitignore (grep checks for rule)
- ✓ I8: Canonical format (sorted keys, fixed order)
- ✓ All tools executable and accessible

### Edge Cases Covered
- Long artifact names (truncated by pad() to fit 70 cols)
- Tabs in content (replaced with spaces in pad())
- Missing previous state (diff handles gracefully)
- Empty modules/artifacts lists (handled by render_home.py)
- Variable-length status names (padded to 3 cols)

### Failure Modes & Recovery
See "Failure Modes" table in STATE_SYSTEM_CANONICAL.md (lines 207-214)

---

## Integration Checklist

- [x] Commit canonical toolset to git
- [x] Document all 8 invariants with testable procedures
- [x] Implement fail-closed assertion gate (I2)
- [x] Implement canonical format enforcement (I8)
- [x] Add .gitignore for generated outputs (I7)
- [x] Create comprehensive verification script
- [x] Document schema and constraints
- [x] Verify determinism (I1)
- [x] Verify width guarantee (I2)
- [x] Verify module order (I5)

---

## Next Steps (For Daily OS Integration)

1. **Integrate into daily pipeline** → Call tools in workflow order (rotate, normalize, render, diff, commit)

2. **Set up scheduled runs** → Cron job or scheduler to run daily/hourly

3. **Add observation collection** → Ingest claims, verdicts, insights into city_current.json

4. **Build dashboard** → Read state files and render real-time view (can reuse render_home.py output)

5. **Archive for continuity** → Keep git history clean; state files are immutable records

---

## References

- **Contract:** STATE_SYSTEM_CANONICAL.md
- **Quick Ref:** TOOLS_SUMMARY.md
- **Tests:** bash oracle_town/FINAL_VERIFICATION.sh
- **Schema:** city_current.json (canonical example)

---

**Status:** ✓ PRODUCTION READY

All invariants enforced, verified, and documented. Ready for integration into Daily OS pipeline.

**Last Verified:** 2026-01-30
