# CONQUEST: Week 1 Design Sprint Brief
**For: Next AI Agent / Design Lead**
**Duration**: 5 working days (40 hours focused work)
**Deliverables**: 3 finalized specs ready for engineering

---

## CONTEXT (Read This First)

You are inheriting a **complete product specification** that was synthesized in EXPAND → SELECT → SHIP cycle.

**Your job is NOT to re-design. Your job is to DETAIL.**

The architecture is locked. The governance is locked. The scoring is locked.

Your job: Make decisions on things that are still ambiguous.

---

## THE SPECIFICATION (TL;DR)

**Product**: Modular competitive tabletop game with digital companion + creator economy.

**4-layer architecture**:
1. **Tabletop** (duel system, cards, physical die) — must work offline
2. **Duo mode** (cards + IA die introduces variance)
3. **Digital companion** (avatar, castle, Elo ranking, seasons)
4. **Creator studio** (post-MVP, gated at 10K DAU)

**Monetization**: Option C (Hybrid Controlled)
- MVP: Reputation only (no revenue)
- Month 6: Creator Program (closed, contracts, 30% share)
- Year 2: Marketplace (if anti-fraud hardened)

**Success metrics** (12-month):
- 15,000 MAU
- 30% J30 retention
- 3+ duels/user/day
- 40%+ organic growth

**Read**:
- `CONQUEST_COMPLETE_PACKAGE.md` (navigation)
- `CONQUEST_SPECIFICATION_MVP.md` (full spec)
- `CONQUEST_GOVERNANCE_CONSTITUTION.md` (rules, sections I + II for scoring)

---

## WEEK 1 DELIVERABLES (3 Documents)

### Deliverable 1: CONQUEST_DUEL_MECHANIC_SPEC.md
**What it is**: Complete duel system ruleset. Clear enough to code. Clear enough to playtest.

**What it must contain**:
1. **Win condition** (how does a duel end?)
   - HP-based (first to 0 HP loses)?
   - Territory-based (control 3+ zones)?
   - Resource-based (deplete opponent's deck)?
   - Combination of above?

2. **Turn structure** (exactly what happens each turn?)
   - Phase 1: Player A acts (play card OR activate ability OR pass)
   - Phase 2: Player B responds OR passes
   - Phase 3: Resolve effects
   - Phase 4: IA Die roll (determines next turn's event)
   - Repeat until win condition met

3. **Card mechanics** (what can cards do?)
   - Damage (HP reduction)
   - Defense (HP gain or block)
   - Abilities (triggered or activated)
   - Resources (mana, energy, cooldowns)
   - Stat ranges (HP: 3-8, Damage: 1-5, Cost: 1-7)

4. **IA Die mechanics** (what does the die do?)
   - Reroll outcome
   - Multiplicator (2x/0.5x reward)
   - Event injection (random card)
   - Twist (swap cards)
   - Penalty (lose resource, skip turn)
   - Bonus (extra action)
   - Each has % chance, scaling with rounds played

5. **Depth metrics** (how do we know it has depth?)
   - Estimated number of distinct game states
   - Average match duration (target: 12-15 min)
   - Estimated number of viable deck archetypes (target: 5+)
   - Skill ceiling (how much does player skill matter vs. luck?)

6. **Playtest success criteria**
   - Players want to play again immediately (replay rate target: 60%+)
   - Win/loss feels earned, not random (player agency)
   - No degenerate combos (if found, design fix)
   - Match duration variance < 3:1 (not too swingy)

---

### Deliverable 2: CONQUEST_IA_DIE_SPECIFICATION.md
**What it is**: Complete specification for the physical IA die object. Manufacturing-ready.

**What it must contain**:

1. **Physical spec**
   - Size (d20? d12? custom?): Choose based on gameplay
   - Material (plastic, wood, metal, resin): Cheap to manufacture (<$5 COGS)
   - Faces: 6, 8, 10, 12, or 20?
   - Art/branding: How is it visually distinct?

2. **Outcome mapping** (each face = what gameplay event?)
   - Face 1: Reroll
   - Face 2: Multiplicator (2x)
   - Face 3: Multiplicator (0.5x)
   - Face 4: Event injection
   - Face 5: Twist
   - Face 6: Penalty
   - Face 7+: Bonus (if d12+)

   **Key**: Each outcome must be reproducible and testable (not "magic").

3. **Probability calibration**
   - What % of games have die outcome change result?
   - Target: 25-35% (enough to matter, not too random)
   - This determines K-factor multiplier in Elo formula

4. **Manufacturing partner** (TBD, but specification should enable easy sourcing)
   - Dimensions for injection molding? 3D printing? CNC?
   - Cost targets: <$5 COGS at 10K units
   - Lead time: < 12 weeks for first batch

5. **Playtesting success criteria**
   - Players find it exciting, not gimmicky
   - Outcome feels fair (not "cheap wins")
   - Skill progression clear even with die variance
   - Die adds replayability (same matchup, different outcomes)

---

### Deliverable 3: CONQUEST_SCORING_FORMULAS_FINAL.md
**What it is**: Exact mathematical formulas, ready to implement. No ambiguity.

**What it must contain**:

#### Section 1: Elo Formula (Modified)

```
R_new = R_old + K(σ) × (Actual_Score - Expected_Score)

Where:
  K(σ) = Base_K × (1 + Die_Variance_Multiplier)
  Base_K = 24
  Die_Variance_Multiplier = X (to be determined via playtesting)

Expected_Score = 1 / (1 + 10^((R_opponent - R_player) / 400))

Actual_Score = 1.0 (if win), 0.5 (if draw), 0.0 (if loss)

ΔR_daily_max = 20 (daily gain cap)
```

**Decision needed**: What is `Die_Variance_Multiplier`?
- Conservative: 0.2 (die matters 20%)
- Moderate: 0.3 (die matters 30%)
- Aggressive: 0.4 (die matters 40%)
- **Recommendation**: Start at 0.3, calibrate via playtest

---

#### Section 2: Stability Index (Non-Manipulable)

```
Stability = 1 - (StdDev(R_last_20) / MaxAcceptableVariance)

Where:
  R_last_20 = ratings from last 20 games
  StdDev(R_last_20) = standard deviation of rating changes
  MaxAcceptableVariance = Y (to be determined, suggest: 60 rating points)

Stability_Score = min(max(Stability, 0.0), 1.0)  [clamp to 0–1]

Rating_Weight = Stability_Score × 0.8 + 0.2  [floor weight at 0.2x]
```

**Decision needed**: What is `MaxAcceptableVariance`?
- Conservative: 40 points (tight consistency required)
- Moderate: 60 points (normal variance ok)
- Aggressive: 80 points (high variance ok)
- **Recommendation**: 60 points, calibrate via playtest

---

#### Section 3: CIS Formula (Simplified for MVP, full in governance doc)

MVP has NO creator economy. CIS is calculated but not used for phase gates yet.

```
CIS = (Replay_Rate × 0.30)
    + (Retention_Delta × 0.25)
    + (Qualified_Vote × 0.30)
    + (Guild_Adoption × 0.15)

Scaled 0–100

[Full detail in CONQUEST_SCORING_MODEL.md]
```

**MVP approach**: Calculate CIS for data gathering. Don't use it for gates until Phase 1 (Month 6+).

---

#### Section 4: Session Verification (Bot Detection)

```
Session is valid IF:
  ✅ session_duration ≥ 2 minutes (minimum engagement)
  ✅ session_duration ≤ 60 minutes (sanity check)
  ✅ same_player_id replays same_session < 5x in 24h (farming detection)
  ✅ IP_address not flagged (VPN/proxy detection if needed)

Session is flagged IF:
  ⚠️ session_duration < 2 min (exclude from stats)
  ⚠️ same_player replays 5+ times (manual review)
  ⚠️ bot_score > 0.7 (automated ML detection)
```

---

## HOW TO APPROACH THIS (Methodology)

**DO**:
- ✅ Make specific design choices (win condition, die size, K-factor)
- ✅ Justify each choice with evidence (why HP-based vs. territory-based?)
- ✅ Make decisions explicit (no "we'll decide later")
- ✅ Write for engineers (formulas must be implementable)
- ✅ Include success criteria (how do we know if it worked?)

**DON'T**:
- ❌ Re-architect the product (4 layers are locked)
- ❌ Change monetization model (Option C is locked)
- ❌ Re-design governance (rules are in constitution)
- ❌ Skip playtest criteria (these are gating decisions)
- ❌ Leave ambiguities (formulas must be exact)

---

## DECISION FRAMEWORK (What's Still Open)

### Open Decision 1: Win Condition
**Options**:
- A) HP-based (first to 0 HP loses) — Simple, proven, clear
- B) Territory-based (control zones) — Strategic, complex, engaging
- C) Hybrid (HP + territory) — Best of both, requires tuning

**My recommendation**: B or C
**Why**: A is too simple (only 3-5 distinct deck archetypes). B/C support 8+ archetypes.
**Playtest criteria**: Players say "I tried 3+ different strategies and all worked."

---

### Open Decision 2: Die Size & Faces
**Options**:
- A) d6 (6 faces, 60% of games have variance)
- B) d10 (10 faces, 40% of games have variance)
- C) d12 (12 faces, 30% of games have variance)
- D) Custom (your choice of size/faces)

**My recommendation**: d12 (targets 30% variance, clean probability distribution)
**Why**: d6 too chaotic, d10 is awkward, d12 is elegant and feels special.
**Playtest criteria**: Players say "Die outcome feels fair, not cheesy."

---

### Open Decision 3: K-Factor Multiplier (Die Variance)
**Options**:
- A) 0.2 (die matters, but Elo still dominant)
- B) 0.3 (die and Elo both matter equally)
- C) 0.4 (die matters a lot, luck is 40%)

**My recommendation**: 0.3
**Why**: Balances agency (Elo) with excitement (variance). Precedent: Magic with shuffled deck ≈ 0.25–0.35.
**Playtest criteria**: Win rate swings <5% between top players (skill > luck) but still exciting.

---

### Open Decision 4: Base Game Loop Duration
**Target**: 12–15 minutes (including queue + setup + duel + cleanup)

**Options**:
- A) 3 turns per duel (9 min duel + 3 min overhead = 12 min total)
- B) 4 turns per duel (12 min duel + 3 min overhead = 15 min total)
- C) 5 turns per duel (15 min duel + 3 min overhead = 18 min total)

**My recommendation**: 4 turns
**Why**: 15 min is sweet spot (time for depth, not grinding). Matches Hearthstone (14–16 min).
**Playtest criteria**: Average match duration 14–16 min. Variance <2x.

---

## WHAT HAPPENS AFTER WEEK 1

**End of Week 1**:
- [ ] 3 documents finalized (duel, die, scoring)
- [ ] Investor GREEN LIGHT on design sprint (or feedback for iteration)
- [ ] Designer ready to hand off to engineering

**Month 1**:
- [ ] Alpha build starts (with your specs as PRD)
- [ ] 50 beta testers recruited
- [ ] Playtest begins (duel depth confirmed, die balance proven)

**Month 4 Beta Gate**:
- [ ] 30% J30 retention proven?
- [ ] Duel system holds up after 100+ playtests?
- [ ] Decision: GREEN → Open Beta, or RED → iterate

---

## CRITICAL SUCCESS FACTORS (Non-Negotiable)

1. **Duel must be learnable in 5 min, masterful in 100 hours**
   - If players understand rules but can't strategy → fail
   - If rules take >10 min to explain → fail

2. **Die must feel fair, not lucky**
   - If players say "That die roll was cheap" frequently → fail
   - If die is invisible (doesn't matter) → fail

3. **Depth must come from deck building + play skill, not RNG**
   - Luck should increase variance, not determine outcome
   - Top players should win 60%+ of games vs. casual players

4. **Scoring must be transparent and gameable-resistant**
   - If high-rated players sandbag → fail
   - If low-rated players smurf → fail
   - Stability Index + Activity Score should prevent this

---

## FILES YOU HAVE

**Reference** (read once):
- `CONQUEST_COMPLETE_PACKAGE.md` — Navigation
- `CONQUEST_SPECIFICATION_MVP.md` — Full spec
- `CONQUEST_GOVERNANCE_CONSTITUTION.md` — Sections I (Elo) + II (CIS)
- `CONQUEST_SCORING_MODEL.md` — Detailed formulas
- `CONQUEST_SELECT_SKEPTIC_REVIEW.md` — Risk assessment

**Authority** (check when making decisions):
- `CONQUEST_GOVERNANCE_CONSTITUTION.md` — If you're unsure whether a decision conflicts with locked rules

---

## OUTPUT FORMAT (Week 1 Documents)

Each of your 3 documents should follow this structure:

```markdown
# CONQUEST: [Title]
**Version**: 1.0
**Date**: 2026-02-18 (end of Week 1)
**Author**: [Designer name]
**Status**: Ready for engineering

## Executive Summary
[1 paragraph: what this doc does, why it matters]

## Section 1: [Topic]
[Details, formulas, justifications]

## Section 2: [Topic]
[Details, formulas, justifications]

## Decision Log
[Every ambiguity you resolved, with reasoning]

## Playtest Success Criteria
[How will we know this succeeded?]

## Next Steps
[What engineering needs from you next]
```

---

## HANDOFF PROTOCOL (From Design to Engineering)

At end of Week 1, you hand off to engineering with:

1. ✅ Duel mechanic spec (complete, no ambiguities)
2. ✅ IA die spec (manufacturing-ready)
3. ✅ Scoring formulas (exact math, implementable)
4. ✅ Playtest plan (how to validate your specs)
5. ✅ Decision log (why you chose A over B)

**Engineering uses these directly as PRD (Product Requirements Document).**

No "we'll discuss this later." It's all decided.

---

## FINAL NOTE

**You are not designing from scratch. You are detailing under constraints.**

Constraints are GOOD. They prevent scope creep and endless iteration.

Your job: Make the best decisions possible within the locked architecture.

Then hand off and let engineering build.

---

**Owner**: JMT (Design Authority)
**Version**: 1.0
**Date**: 2026-02-11
**Status**: Brief ready for Week 1 sprint

**Go detail. Then ship.**

🚀
