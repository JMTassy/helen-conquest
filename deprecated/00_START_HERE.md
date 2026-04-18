# CONQUEST v2.0 — Start Here

## ✅ What You Have

A **fully functional, deterministic territorial conquest simulation** with:
- 5 agents competing on a 5×5 grid
- 6 archetype-domain pairs with meaningful strategic interactions
- 6-turn epochs that cycle (GROUNDING → SEEING → STRUGGLE → ORDER → BONDING → SHEDDING)
- Conflict mechanics (power + bonus + d4 vs stability + fortress + bonus + d4)
- Reproducible results (fully seeded, deterministic)

## 🚀 How to Run

```bash
python3 conquest_v2_hexacycle.py [SEED]
```

Example:
```bash
python3 conquest_v2_hexacycle.py 111
```

This will:
- Display a 5×5 ASCII grid every turn
- Show agent stats (power, stability, territory)
- Log all conflicts
- Print the winner at turn 36

Takes ~5 seconds to complete.

## 📊 What to Read First

1. **CONQUEST_V2_EXECUTION_SUMMARY.txt** — Quick overview (2 min read)
2. **CONQUEST_V2_BASELINE_REPORT.md** — Detailed results and analysis (5 min read)
3. **conquest_v2_hexacycle.py** — The actual code (13 KB, well-commented)

## 🎯 Baseline Results (3 Seeds Tested)

| Seed | Winner | Archetype | Domain | Tiles |
|------|--------|-----------|--------|-------|
| 111 | EPSILON | GUARDIAN | DEFENSE | 8 |
| 222 | BETA | ARCHITECT | UNITY | 10 |
| 333 | EPSILON | GUARDIAN | DEFENSE | 12 |

**Pattern:** GUARDIAN dominates (2/3 wins), WARLORD always dies.

## ⚙️ System Overview

### Agents
- **ALPHA** (WARLORD / WAR) — Aggressive attacker
- **BETA** (ARCHITECT / UNITY) — Defensive builder
- **GAMMA** (DIPLOMAT / TRADE) — Balanced trader
- **DELTA** (SEER / SCIENCE) — Knowledge-focused
- **EPSILON** (GUARDIAN / DEFENSE) — Fortress specialist

### Epochs (Each 6 Turns)
1. **GROUNDING** (0-5) → GUARDIAN gets +2 stability
2. **SEEING** (6-11) → SEER gets +2 stability
3. **STRUGGLE** (12-17) → WARLORD gets +2 power, -1 stability
4. **ORDER** (18-23) → ARCHITECT gets +2 stability
5. **BONDING** (24-29) → DIPLOMAT gets +1 power, +1 stability
6. **SHEDDING** (30-35) → Attrition phase

### Victory
- **Absolute:** Any agent controls ≥13 tiles (majority of 25)
- **Timeout:** At 36 turns, highest tile count wins

## 🔧 Code Structure

```python
class Archetype(Enum)        # WARLORD, ARCHITECT, DIPLOMAT, SEER, GUARDIAN
class Domain(Enum)           # WAR, UNITY, TRADE, SCIENCE, DEFENSE
class Epoch(Enum)            # GROUNDING, SEEING, STRUGGLE, ORDER, BONDING, SHEDDING

class Tile                    # 5×5 grid, ownership + fortress defense
class Agent                   # Stats: power, stability, territory
class HexaCycleGame           # Main engine (turn execution, conflict, victory)
```

All deterministic, all reproducible, no external dependencies.

## 📈 Next Steps

### Option 1: Phase 1 Expansion (as-is)
- Add mutations (pressure-based trait changes)
- Add Fate Cards (epoch-triggered events)
- Add player control mode
- Add 10 more features

**Timeline:** 1-2 days of focused work

### Option 2: Rebalance First (recommended)
- Fix WARLORD weakness (remove -1 stability malus)
- Reduce GUARDIAN dominance (reduce GROUNDING bonus to +1)
- Boost DIPLOMAT (add SEEING epoch bonus)
- Run 10-seed regression test
- Lock balanced baseline

**Timeline:** 30 minutes of code tweaks + 2 minutes of testing

**Recommendation:** Do Option 2 before Option 1. Better to have balanced archetypes before adding complexity.

## ✅ Verification Checklist

- [x] Code runs without errors
- [x] Determinism verified (same seed = same outcome)
- [x] All mechanics working as designed
- [x] Baseline established (3 seeds tested)
- [x] Documentation complete
- [x] No external dependencies
- [x] Ready for Phase 1

## 📝 Known Issues

**WARLORD always dies**
- Gets +2 power in STRUGGLE, but -1 stability malus makes it unsustainable
- Fix: Remove malus (1 line of code)

**GUARDIAN dominates early**
- Center position + early stability bonus + fortress defense = too strong
- Fix: Reduce GROUNDING bonus to +1 (1 line of code)

**DIPLOMAT is weak**
- BONDING epoch (turns 24-29) is too late for early expansion advantage
- Fix: Add DIPLOMAT bonus in earlier epoch (2 lines of code)

## 📞 Questions?

Check the baseline report for detailed analysis, pattern explanations, and architectural notes.

---

**Status:** ✅ Phase A Complete — Baseline Locked  
**Ready for:** Phase 1 (mutations, fate cards, player control)  
**Date:** February 13, 2026
