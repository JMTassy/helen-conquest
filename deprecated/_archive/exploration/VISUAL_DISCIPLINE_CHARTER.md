# Visual Discipline Charter

**Oracle Town iso-coaster Visualization**

Date: January 31, 2026
Status: FROZEN (Constitutional)

---

## Purpose

This charter defines immutable visual rules for iso-coaster rendering of Oracle Town's CityState.

The iso-coaster visualization is **read-only, non-authoritative, and purely descriptive**. It renders the jurisdiction's state without interpretation, inference, or visual deception.

---

## Scope

This applies to:
- `oracle_town/city_state_renderer.py` — ASCII snapshot renderer (K5 deterministic)
- `oracle_town/iso_coaster_config.py` — Tileset and building mappings (frozen)
- Any future HTML/graphics renderer built from the above

This does NOT apply to:
- TRI gate logic (authority layer, separate governance)
- Ledger storage (append-only data, separate layer)
- Dashboard widgets (separate from iso-coaster)

---

## Core Principle

> **Visibility without deception.**

The visualization shows what is. It does not suggest, infer, predict, or encourage.

---

## The Eight Immutable Rules

### ❌ Rule 1: No Speculative Animations

**What this forbids:**
- Buildings that "construct themselves" during a run
- Progress animations (growing, shrinking, appearing)
- "Loading" visuals while decisions are pending
- Gradual illumination as verdicts are issued

**Why:**
Animations suggest causality and progress where only data exists. A building's state only matters *after* TRI has decided. Showing it "build" conflates intention with outcome.

**What is allowed:**
- Static snapshot at run completion
- Diff view (previous state → current state) with explicit timestamp
- Fade between static frames (not during the run)

---

### ❌ Rule 2: No Progress Bars Tied to REJECT

**What this forbids:**
- "X verdicts processed" bars that include REJECT counts
- Progress indicating "10/15 verdicts analyzed" (rejection is not progress)
- Animations that "succeed" when verdicts are issued (even REJECT)
- Visual momentum that makes rejection feel like forward motion

**Why:**
REJECT is not a failed attempt. It is a decision. Rendering it as "progress" toward ACCEPT normalizes the confusion between authority and outcome.

**What is allowed:**
- Simple counts: "ACCEPT: 1 | REJECT: 6" (raw data)
- Distinction in visual weight: REJECT is heavy, clear, and unambiguous
- No aggregation that conflates ACCEPT and REJECT

---

### ❌ Rule 3: No "Attempted" States

**What this forbids:**
- Intermediate module states like BUILDING, LOADING, PENDING, VALIDATING
- Visual distinction between "in progress" and "complete"
- Spinners or progress wheels
- "Elapsed time" displays

**Why:**
The snapshot is either complete (after TRI) or it is not shown at all. There is no "in-between" that iso-coaster should visualize.

The system either issued a receipt or it did not. Anything else is fiction.

**What is allowed:**
- Only three states: OK, OFF, FAIL
- Timestamp on the snapshot (when was this taken?)
- Run ID (which run is this?)

---

### ❌ Rule 4: No Predictions

**What this forbids:**
- "Next verdict likely to ACCEPT" hints
- Visual clustering by predicted outcome
- Confidence scores embedded in building appearance
- Arrows pointing to "likely next" modules

**Why:**
Only TRI knows the verdict. Visualization that suggests outcomes violates the constitution.

**What is allowed:**
- Historical data (what was the last verdict?)
- Ledger references (search past outcomes)
- Explicit caveat: "this is a snapshot, not a forecast"

---

### ❌ Rule 5: No Auto-Expansion of Details

**What this forbids:**
- Clicking on a building reveals hidden verdict history
- Hover-over tooltips with inline verdicts
- Expandable/collapsible sections
- Progressive disclosure of information

**Why:**
iso-coaster is a map, not a database query tool. Details belong in the Interactive Explorer (Phase 6), not in the visualization.

Mixing visualization with data exploration conflates reading the map with reading the ledger.

**What is allowed:**
- Fixed layout, fixed information
- Links to other interfaces (Inspector, Dashboard)
- Explicit mode switch ("View in Inspector")

---

### ❌ Rule 6: No Gamification

**What this forbids:**
- Points, badges, achievements
- Celebration animations (confetti, sparkles)
- Streak counters ("20 days with >80% acceptance")
- "Level up" progression
- Leaderboards or comparative scoring

**Why:**
Governance is serious. The visual language must reflect weight, not achievement.

A jurisdiction that looks like a game weakens the constitutional force.

**What is allowed:**
- Accurate metrics (raw counts, rates, historical trends)
- Emphasis on refusal (make rejection *visible*, not hidden)
- Austere, formal presentation

---

### ❌ Rule 7: No Reinterpretation of Silence

**What this forbids:**
- Rendering REFUSE as "pending" or "gray" (ambiguous)
- Showing absence as "interesting" or "worth watching"
- Visual weight that suggests "nothing is happening" is the same as "something unexpected occurred"
- Icons that blur the line between OFF and FAIL

**Why:**
REFUSE is a valid outcome. When TRI rejects a claim, that decision *is* the result. Rendering it as "lighter" or "softer" than ACCEPT normalizes the confusion that rejection is somehow less important.

**What is allowed:**
- FAIL state for actual errors (module crashed, ledger unavailable)
- OFF state for inactive modules (not running)
- REJECT is rendered in the ledger, not in the iso-coaster visualization
- If iso-coaster shows REJECT count, it must be visually equivalent to ACCEPT count (equal weight)

---

### ❌ Rule 8: No "Helpful" Inferences

**What this forbids:**
- Suggesting what "should" happen next
- Auto-coloring based on heuristics
- Filling in missing data with assumed values
- "Intelligent" defaults that make absence look like presence

**Why:**
The visualization serves truth, not user comfort. If data is missing, that absence must be visible and honest (use ∅ symbol, empty space, or explicit "unknown").

**What is allowed:**
- Honest defaults (∅ for missing, 0 for uncounted)
- Clear marking of data age ("stale" if >1 hour old)
- Warnings when data is incomplete

---

## How to Enforce This Charter

### For Code Review

When adding features to iso-coaster:

1. **Check the rules** — Which rule does this feature touch?
2. **Assume the worst** — Could this be misused? (It can. Assume it will be.)
3. **Reference this charter** — Quote the specific rule being violated.
4. **Say no clearly** — "This violates Rule 5 (no auto-expansion). Rejected."

### For Future Contributors

If you want to add a "helpful" visual feature:

1. Read this charter first
2. Find the rule it violates
3. Propose an alternative that doesn't
4. If no alternative exists, the feature doesn't belong

### For Users

If you see iso-coaster doing something not listed in the "What is allowed" sections:

1. Take a screenshot
2. Open an issue: "Potential Visual Discipline violation (Rule X)"
3. Reference this charter

---

## Examples of Correct & Incorrect Usage

### ✅ CORRECT: Simple Snapshot

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ORACLE TOWN — 2026-01-31 RUN daily-01      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Policy: v7 (sha256:abc123…)
┃ Verdicts: ACCEPT 1 | REJECT 6
┃
┃        [OBS] OK   ████▉
┃         │
┃      [TRI] OK   ████▉
```

**Why correct:**
- Fixed layout
- No animation
- Equal visual weight for verdict counts
- Clear timestamps
- No interpretation

---

### ❌ INCORRECT: Speculative Animation

```
[OBS] activating…
  ↻ (spinner)
  Building [OBS] tower
  Progress: ███░░░░░░ 30%

Estimated ACCEPT rate: 85% (probably safe)
Next: INSIGHT will likely process successfully
```

**Why incorrect:**
- Spinner (Rule 1 — speculation)
- Progress bar (Rule 2 — progress tied to verdicts)
- PENDING state (Rule 3 — no intermediate states)
- Prediction (Rule 4 — "likely process")
- Helpful inference (Rule 8 — "probably safe")

---

### ✅ CORRECT: Honest Diff

```
BEFORE (2026-01-30 daily-01):
  [OBS] OK   ████▉
  [TRI] OK   ████▉
  Verdicts: ACCEPT 2 | REJECT 4

AFTER (2026-01-31 daily-02):
  [OBS] OK   ████▉
  [TRI] OK   ████▉
  Verdicts: ACCEPT 1 | REJECT 6

Change: ACCEPT -1 | REJECT +2
```

**Why correct:**
- Explicit timestamps
- Side-by-side comparison
- Raw delta (no interpretation)
- No "trend" claims

---

### ❌ INCORRECT: Gamified Visualization

```
🎉 YOU'VE PROCESSED 10 VERDICTS! 🎉

Accuracy Streak: 5 days ✓ ✓ ✓ ✓ ✓

TOP PERFORMER MODULE:
  INSIGHT: 🏆 42 patterns detected

Next Goal: 50 patterns (80% complete) ███████░
```

**Why incorrect:**
- Celebration (Rule 6 — gamification)
- Streaks (Rule 6 — achievement scoring)
- Badges (Rule 6 — visual rankings)
- Progress bar toward arbitrary goal (Rule 2 & 6)

---

## Amendment Process

**This charter cannot be amended without formal governance.**

To propose a change:

1. Open an issue with title: `[VISUAL_DISCIPLINE] Proposed Change to Rule X`
2. Explain why the rule is wrong
3. Propose exact replacement language
4. Cite constitutional precedent or architectural necessity
5. Wait for review (minimum 14 days)

Amendments require consensus from:
- Architecture team (oracle_town/MAINTAINERS.md)
- At least two independent reviewers
- No objections from governance authority (TRI)

**Default: reject.**

---

## Related Documents

- `oracle_town/city_state_renderer.py` — Implementation (K5 deterministic)
- `oracle_town/iso_coaster_config.py` — Configuration (frozen tileset)
- `CLAUDE.md` — Architecture (three-layer model)
- `ORACLE_TOWN_ASCII_MAP.txt` — Visual overview

---

## Closing Statement

This visualization is not entertainment. It is **evidence**.

Evidence must be:
- Honest
- Complete (where known)
- Free of suggestion
- Reproducible
- Diff-able

If you are tempted to make iso-coaster "prettier," remember:

> The aesthetics of governance is austerity.

Beauty that deceives is corruption.

---

**Signed:** Oracle Town Architecture Team
**Date:** January 31, 2026
**Status:** IMMUTABLE (Constitutional)
