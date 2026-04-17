# ORACLE TOWN — State Management (Canonical)

Deterministic, git-friendly state snapshots + terminal renderers for ORACLE TOWN's 7-module pipeline.

## What This Provides

- **JSON state files** (`city_prev.json`, `city_current.json`)
- **Deterministic renderer** (`render_home.py`) with width guarantee
- **Delta comparator** (`diff_city.py`) for minimal diffs
- **State normalizer** (`normalize_state.py`) for canonical formatting
- **Optional tools**: state rotator, 14-day simulator

## Directory Contract

```
oracle_town/
  state/
    city_current.json        [source of truth for latest run]
    city_prev.json           [immediately previous state, used for diffs]
    sim_day_*.json           [generated, NOT committed (see .gitignore)]

  render_home.py             [deterministic HOME renderer]
  diff_city.py               [delta-only comparator]
  normalize_state.py         [canonical JSON formatter (sorted keys, stable diffs)]
  rotate_state.py            [copies current → prev before new run]
  simulate_14_days.py        [generates sim states]
  .gitignore                 [ignores sim_day_*.json]
```

## Immutable Invariants

These invariants are **enforced** (not aspirational):

### I1: Determinism
Same JSON input to the same renderer version → identical output bytes.

**Enforcement:**
- No RNG calls
- No environment reads
- No wallclock time in rendering
- Pure functions only
- Test: run 2× and byte-compare output

### I2: Width Guarantee (ASCII mode)

Framed output lines (containing borders ┃...┃) are **exactly 72 characters** in `len()`.

- Inner content: 70 columns
- Borders: 1 char each (┃ left, ┃ right)
- Total: 70 + 2 = 72

**Enforcement:** `assert_width()` gate in `render_home.py`
- Fires if any framed line ≠ 72 chars
- Exit code 1 on failure
- Test: `python3 oracle_town/render_home.py` should succeed without assertion errors

### I3: State Format

State files are **JSON only**.

- Sorted keys (for stable diffs): `json.dumps(..., sort_keys=True)`
- 2-space indents
- Trailing newline
- Encoding: UTF-8

**Enforcement:** Schema validation (optional, can add later)

### I4: No Implicit Timestamps

Date field `YYYY-MM-DD` is allowed. Wallclock time is forbidden (breaks determinism).

**Enforcement:** Code review + tests

### I5: Module Order Fixed

Modules always appear in this order: `OBS, INS, BRF, TRI, PUB, MEM, EVO`.

**Enforcement:** `MODULE_ORDER` tuple in code

### I6: Progress Range Fixed

`progress ∈ {0..8}` (integer, rendered as 8-tick bar).

**Enforcement:** Clamped in `bar()` function

### I7: Simulation Outputs Are Generated

Files `state/sim_day_*.json` are build outputs.

**Enforcement:** `.gitignore` blocks them from git

---

## State Schema

### Top-level fields

```json
{
  "date": "2026-01-30",              // YYYY-MM-DD only
  "run_id": 173,                     // Sequential integer
  "mode": "DAILY",                   // Enum: DAILY, SIM, etc.
  "one_bet": "string",               // Single-sentence summary
  "queue": ["task1", "task2"],       // Up to 7 in-progress items
  "alerts": [],                      // Optional alert list
  "anomalies": [                     // Optional anomaly list
    {
      "code": "string",
      "severity": "weak|medium|high",
      "module": "OBS|INS|..."
    }
  ],
  "modules": {
    "OBS": { "status": "OFF|BLD|OK|WRN|FLR", "progress": 0-8, "desc": "..." },
    // ... one per module in MODULE_ORDER
  },
  "artifacts": ["file1", "file2"]    // Build outputs, reports, etc.
}
```

---

## Daily Workflow

1. **Rotate state** (preserve history for diff)
   ```bash
   python3 oracle_town/rotate_state.py
   ```

2. **Write new `city_current.json`** (your pipeline updates it)

3. **Normalize state** (canonical formatting for stable diffs)
   ```bash
   python3 oracle_town/normalize_state.py oracle_town/state/city_current.json
   ```

4. **Render HOME** (with width assertion)
   ```bash
   python3 oracle_town/render_home.py
   ```
   (Fails if any framed line ≠ 72 chars)

5. **Show delta**
   ```bash
   python3 oracle_town/diff_city.py
   ```

6. **Commit state**
   ```bash
   git add oracle_town/state/city_*.json
   git commit -m "Daily OS run 174: OBS+INS progressing"
   ```

---

## Verification Commands

### Test determinism
```bash
python3 oracle_town/render_home.py > out1.txt
python3 oracle_town/render_home.py > out2.txt
diff out1.txt out2.txt  # Should be identical
```

### Test width gate
```bash
python3 oracle_town/render_home.py
# Should succeed. If any line ≠ 72 chars, exits with error.
```

### Test delta output
```bash
python3 oracle_town/diff_city.py
# Should show only changed modules (minimal noise).
```

### Test rotation
```bash
python3 oracle_town/rotate_state.py
# Should copy city_current.json → city_prev.json.
```

### Generate simulator
```bash
python3 oracle_town/simulate_14_days.py
# Generates 28 files (14 days × 2 per day).
# All are in state/sim_day_*.json (ignored by git).
```

### Normalize state files
```bash
python3 oracle_town/normalize_state.py oracle_town/state/city_current.json
# Rewrites JSON with sorted keys, 2-space indents, trailing newline.
# Ensures stable diffs in git (no key-order churn).
```

---

## Key Design Decisions

### Why ASCII-only?
`len(s)` == display width is the portable contract. Emoji width varies across terminals/fonts; guaranteeing it requires `wcwidth` + terminal detection, which is fragile. ASCII has no surprises.

**Future:** Could add `--unicode` mode (glyph layer) as best-effort cosmetic layer.

### Why 70 inner columns?
Fits 80-column terminals (70 + 2 borders + 8-char safety margin).

### Why JSON with `sort_keys=True`?
Stable diffs. If keys vary in order, git diffs are noisy. Sorting prevents that.

### Why separate rotate script?
Explicit step before writing new state. Ensures diff history is preserved. Easy to integrate into CI/automation.

### Why `.gitignore` simulation files?
Simulation outputs are deterministic but generated. Committing them pollutes git history. Users can generate them on-demand with `simulate_14_days.py`.

---

## Failure Modes

| Scenario | Detection | Fix |
|----------|-----------|-----|
| Framed line exceeds 72 chars | `assert_width()` fires | Reduce content or split line |
| Simulation files get committed | Git shows `sim_day_*.json` | Add to `.gitignore` (already done) |
| Diff shows many changes when only one module changed | State keys out of order | Use `json.dumps(..., sort_keys=True)` |
| Rendering differs on second run | Wallclock time in output | Remove all timestamp code from `render_home.py` |
| Artifact names cause width overflow | `assert_width()` fires | Truncate artifact names in state or use shorter names |

---

## Summary

This state system enforces **determinism** (via pure functions), **width** (via assertion gate), **auditability** (via JSON + sorted keys), and **portability** (via ASCII-only rendering).

All invariants are **testable** and **enforceable**. None are aspirational.

---

**Status:** Production-ready
**Last Verified:** 2026-01-30
**Enforcement:** Active (assert_width() gate in place)
