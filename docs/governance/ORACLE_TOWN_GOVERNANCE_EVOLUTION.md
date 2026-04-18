# Oracle Town Governance Evolution Framework

**Complete guide to exploring emergence across 9 weeks of governance cycles.**

---

## Overview

You now have three independent systems for exploring how Oracle Town learns and evolves through governance cycles:

1. **Test Harness** — Controlled mock governance for rapid exploration
2. **Emergence Forecast** — Architectural predictions of observable patterns
3. **Week 1 Execution Plan** — Real governance cycle capture and analysis

Together, they enable you to study governance evolution from **two angles:**
- **Illustrative**: See what emergence looks like in plausible scenarios
- **Authentic**: Capture real governance history and compare against forecast

---

## The Three Pathways

### Pathway A: Test Harness Exploration (Start Here if You Want Speed)

**What it does:** Generates 9 weeks of realistic governance cycles with predefined scenarios.

**Files:**
- `oracle_town/memory/tools/test_harness.py` — Test cycle generator
- 9 scenarios from "early adaptation" to "stabilized governance"

**Usage:**
```bash
# Generate all 9 test cycles
python3 oracle_town/memory/tools/test_harness.py all

# Extract memory from test cycles
python3 oracle_town/memory/tools/cycle_observer.py --test-runs

# Synthesize weekly heuristics
python3 oracle_town/memory/tools/weekly_synthesizer.py

# Analyze results
cat oracle_town/memory/tacit/heuristics.md
```

**Time:** ~1 hour total for all 9 weeks

**Output:** Test memory database in `oracle_town/memory/test_runs/` with extracted facts

**Reality level:** Illustrative (realistic but controlled scenarios)

---

### Pathway B: Real Execution (Start Here if You Have Governance Logic Ready)

**What it does:** Captures actual governance decisions in the memory system.

**Files:**
- `ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md` — Step-by-step guide

**Usage:**
```bash
# Week 1: Prepare claims and run governance
python3 oracle_town/cli.py --input oracle_town/test_claims_week1.json

# Extract real decisions into memory
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs

# Repeat for Weeks 2-9
```

**Time:** Depends on your governance execution pace (hours to weeks)

**Output:** Production memory database in `oracle_town/memory/entities/` with real decisions

**Reality level:** 100% authentic (your actual mayor logic)

---

### Pathway C: Hybrid (Recommended for First Run)

**What it does:** Combines test harness learning with real execution.

**Approach:**
1. Weeks 1-3: Run test harness to understand patterns
2. Weeks 4-9: Run real governance to validate forecast
3. Compare test predictions vs. real patterns

**Time:** A few hours + governance execution time

**Output:** Both test and production memory, with comparison

**Reality level:** Mixed (illustrative + authentic)

---

## What is Emergence?

In this context: **Measurable phenomena not explicitly programmed that arise from governance rules, memory feedback, and decision cycles.**

Examples:
- Lanes becoming "trusted" through statistical success (not programmed)
- Proposal formats converging on proven patterns (not mandated)
- Governance rules mutating through meta-proposals (not by decree)
- K-Invariant pressure concentrating on specific constraints (not obvious)

---

## Four Categories of Emergence

### 1. Lane Specialization

**Pattern:** Certain lanes become consistently used for certain proposal types.

**Timeline:**
- Weeks 1-3: Random lane selection, mixed results
- Weeks 4-6: Patterns emerge in heuristics.md
- Weeks 7-9: Systematic lane reuse by all mayors

**Observable in:** `memory/entities/lane_performance/*/summary.md`

**Signal:** Some lanes ≥75% success, others ≤25%

---

### 2. Proposal Archetype Convergence

**Pattern:** Diverse proposals converge on proven formats.

**Timeline:**
- Weeks 1-3: Diverse proposal structures
- Weeks 4-6: Winners get copied
- Weeks 7-9: Clustering around successful templates

**Observable in:** `memory/entities/proposal_archetypes/*/items.json`

**Signal:** New proposals structurally similar to Week 1-3 winners

---

### 3. Meta-Governance Drift

**Pattern:** Governance rules evolve through proposals about governance.

**Timeline:**
- Weeks 1-3: Rules fixed
- Weeks 4-6: Meta-proposals attempt changes
- Weeks 7-9: Governance has mutated (within K-Invariants)

**Observable in:** `memory/entities/decisions/` where type="meta_governance"

**Signal:** New rules in heuristics.md, changed quorum or lane logic

---

### 4. K-Invariant Pressure Mapping

**Pattern:** Some K-Invariants stressed more than others.

**Timeline:**
- Weeks 1-9: Blocking reasons cluster around specific codes

**Observable in:** `memory/entities/invariant_events/*/summary.md`

**Signal:** K3 violations >> K0, K5 (shows which constraints are hard)

---

## Emergence Forecast

See `ORACLE_TOWN_EMERGENCE_FORECAST.md` for:
- Detailed architectural analysis of each emergence type
- How to detect each pattern
- Cycle-by-cycle predictions
- Safety constraints (what cannot emerge)
- Methods to spot emergence in your data

---

## Week 1 Execution Plan

See `ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md` for:
- Step-by-step real governance execution
- How to prepare test claims
- How to extract memory from real decisions
- Failure recovery procedures
- Timeline for weeks 2-9
- Monitoring and convergence detection

---

## How to Detect Emergence

### Lane Specialization
```bash
cat oracle_town/memory/entities/lane_performance/*/summary.md
# Look for: Consistent lane usage, clear success rate winners
```

### Proposal Convergence
```bash
grep -r "type" oracle_town/memory/entities/decisions/*/items.json | cut -d: -f3 | sort | uniq -c
# Count by week: are later proposals similar to earlier winners?
```

### Meta-Governance
```bash
grep -r "meta_governance" oracle_town/memory/entities/decisions/
# Are there proposals about changing governance rules?
```

### K-Pressure
```bash
grep -r "blocking_reasons" oracle_town/memory/entities/invariant_events/
# Which blocker codes appear most? Which K-Invariants are stressed?
```

### Heuristic Evolution
```bash
# Week 1 snapshot
git show HEAD:oracle_town/memory/tacit/heuristics.md > /tmp/heur_w1.md

# Week 9 snapshot
cat oracle_town/memory/tacit/heuristics.md > /tmp/heur_w9.md

# Diff them
diff /tmp/heur_w1.md /tmp/heur_w9.md
# What changed from Week 1 to Week 9?
```

---

## Quick Start

### 5-Minute Quickest Path
```bash
# Generate and analyze test cycles
python3 oracle_town/memory/tools/test_harness.py all
python3 oracle_town/memory/tools/cycle_observer.py --test-runs
python3 oracle_town/memory/tools/weekly_synthesizer.py
cat oracle_town/memory/tacit/heuristics.md
```

Result: See test emergence in action immediately.

### 30-Minute Learning Path
```bash
# Read the forecast
cat ORACLE_TOWN_EMERGENCE_FORECAST.md

# Run test harness
python3 oracle_town/memory/tools/test_harness.py all
python3 oracle_town/memory/tools/cycle_observer.py --test-runs
python3 oracle_town/memory/tools/weekly_synthesizer.py

# Compare forecast vs. results
# Did the test scenarios match predictions?
```

Result: Understand what emergence is, then see it happen.

### Real Execution Path
```bash
# Read the plan
cat ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md

# Prepare claims
# (Your governance environment)

# Run actual governance
python3 oracle_town/cli.py --input oracle_town/test_claims_week1.json

# Extract memory
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs

# Repeat for weeks 2-9
```

Result: Oracle Town learns from real governance.

---

## File Structure

```
oracle_town/
├── memory/
│   ├── tools/
│   │   ├── test_harness.py          ← NEW: Test cycle generator
│   │   ├── cycle_observer.py        ← UPDATED: --test-runs flag
│   │   ├── weekly_synthesizer.py    ← (unchanged)
│   │   └── memory_lookup.py         ← (unchanged)
│   ├── test_runs/                   ← Generated by test_harness.py
│   │   ├── week_01.json
│   │   ├── week_02.json
│   │   └── ... week_09.json
│   ├── entities/
│   │   ├── decisions/
│   │   ├── lane_performance/
│   │   ├── invariant_events/
│   │   └── proposal_archetypes/
│   ├── tacit/
│   │   ├── heuristics.md            ← Autogenerated, evolves with synthesis
│   │   └── rules_of_thumb.md
│   └── daily/                       ← Cycle logs
│       ├── cycle-001.json
│       └── ...

Root:
├── ORACLE_TOWN_EMERGENCE_FORECAST.md         ← NEW: Predictions
├── ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md       ← NEW: Real execution
├── ORACLE_TOWN_GOVERNANCE_EVOLUTION.md       ← NEW: This file
└── ...
```

---

## Decision Tree: Which Pathway?

```
Do you want to:

├─ See emergence immediately?
│  └─ Use Pathway A (Test Harness)
│     Command: python3 oracle_town/memory/tools/test_harness.py all
│
├─ Understand what's theoretically possible?
│  └─ Read: ORACLE_TOWN_EMERGENCE_FORECAST.md
│     Then run Pathway A to validate
│
├─ Run real governance and capture it?
│  └─ Use Pathway B (Real Execution)
│     Read: ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md
│     Prepare claims and run your governance
│
└─ Learn by doing?
   └─ Use Pathway C (Hybrid)
      Pathway A first (learn), then Pathway B (validate)
```

---

## What's New

### New Tools
- **test_harness.py** (550 lines) — Generates realistic governance cycles

### New Documents
- **ORACLE_TOWN_EMERGENCE_FORECAST.md** (400 lines) — Predictions & detection
- **ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md** (350 lines) — Real execution guide

### Updated Tools
- **cycle_observer.py** — Added `--test-runs` flag for test harness support

---

## Safety & Data Integrity

### Test Data
- Clearly marked `type: "TEST_RUN"` in all test cycles
- Stored in separate `memory/test_runs/` directory
- Cannot pollute production memory

### Production Data
- Real governance cycles go to `memory/entities/` as usual
- No mixing with test data
- Full audit trail maintained

### No Fake Data in Production
- Test harness generates in `test_runs/`
- Real execution goes to production `entities/`
- You control which path populates which directory

---

## Success Criteria

### Test Harness (Pathway A)
✅ All 9 cycles generated
✅ cycle_observer.py extracts ≥30 facts
✅ weekly_synthesizer.py regenerates summaries
✅ heuristics.md shows pattern evolution
✅ Results match EMERGENCE_FORECAST.md predictions

### Real Execution (Pathway B)
✅ Governance cycle completes successfully
✅ Decision record is well-formed JSON
✅ cycle_observer.py extracts real facts
✅ Memory entities created and populated
✅ Heuristics reflect actual governance patterns

### Comparison (Pathway C)
✅ Test forecast matches test results
✅ Real patterns similar to or differ from forecast
✅ Differences reveal how realistic the test harness is

---

## Next Steps

1. **Choose a pathway** (A, B, or C)
2. **Run the commands** for that pathway
3. **Analyze the results** using the emergence detection methods
4. **Compare against forecast** (EMERGENCE_FORECAST.md)
5. **Plan weeks 2-9** (real execution) or **Continue test harness**

---

## Questions?

### "What is emergence exactly?"
See: ORACLE_TOWN_EMERGENCE_FORECAST.md → "What is Emergence?"

### "How do I run real governance?"
See: ORACLE_TOWN_WEEK1_EXECUTION_PLAN.md → "Week 1 Execution Steps"

### "What patterns should I expect?"
See: ORACLE_TOWN_EMERGENCE_FORECAST.md → "Emergence Forecast (Cycle-by-Cycle)"

### "How do I detect emergence?"
See: This document → "How to Detect Emergence"

---

## The Big Picture

Oracle Town is now equipped to:

✅ Learn from its own decisions (memory system)
✅ Explore emergence in controlled conditions (test harness)
✅ Capture real governance evolution (real execution plan)
✅ Detect and analyze patterns (emergence forecast)

You can now study governance evolution at scale, understand what emerges naturally, and validate predictions against reality.

**Oracle Town is ready for its journey.**

Choose a pathway and begin.

---

**Created:** Session of 2026-01-28
**Status:** All three systems ready for immediate use
**Maintenance:** Low (test harness and forecast are static; execution plan is documentation)
