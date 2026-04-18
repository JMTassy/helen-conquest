# CONQUEST: Week 1 Design Sprint KICKOFF
**Mode**: EXECUTE (No debate. Decide and ship.)
**Duration**: 5 working days (40 hours)
**Deadline**: Friday EOD
**Deliverables**: 3 final specs (duel, die, scoring)

---

## GO GO GO PROTOCOL

This is **not a planning document**. This is **an execution checklist**.

You have **one job**: Turn ambiguities into decisions. Ship 3 specs ready for engineering.

**No endless iteration. No "let's workshop this." One decision per choice point. Move.**

---

## DAY 1 (Monday): DUEL MECHANIC SPEC

### Task 1: Choose Win Condition (90 min)
Read: `CONQUEST_SPECIFICATION_MVP.md` (core loop section)

**Make the call**: HP-based, territory-based, or hybrid?
- Write 200 words justifying your choice
- Include: Why this works, what decks it enables, depth ceiling

**Commit**: Once chosen, lock it. No reversions.

### Task 2: Define Turn Structure (90 min)
- Phase 1: Player A plays card OR activates ability OR passes
- Phase 2: Player B responds OR passes
- Phase 3: Resolve effects
- Phase 4: IA Die roll

Write 300 words detailing what "resolve effects" means. Card interactions. Simultaneous vs. sequential.

**Commit**: Lock the turn order. This is foundational.

### Task 3: Finalize Card Mechanics (120 min)
- What can cards do? (damage, defense, abilities, resources)
- Stat ranges: HP 3-8, Damage 1-5, Cost 1-7? Or different?
- Ability budget (max power per card)?

Write 400 words spec. Copy-paste ready for game designers.

**Commit**: Designers will use this verbatim.

### End of Day 1:
- [ ] Win condition decided
- [ ] Turn structure locked
- [ ] Card mechanics specified
- **Output**: Draft of CONQUEST_DUEL_MECHANIC_SPEC.md

---

## DAY 2 (Tuesday): IA DIE SPECIFICATION

### Task 1: Choose Physical Die (120 min)
**Decision**: d6, d10, d12, or custom?

Write 200 words including:
- Size (mm)
- Material (plastic, wood, resin)
- Manufacturing cost estimate
- Sourcing path (injection molding, 3D print, CNC)

**Commit**: Once chosen, this determines production timeline.

### Task 2: Map Outcomes to Faces (120 min)
- Face 1: Reroll
- Face 2: Multiplicator (2x)
- Face 3: Multiplicator (0.5x)
- Face 4: Event injection
- Face 5: Twist
- Face 6: Penalty
- Face 7+ (if d12+): Bonus

Write 300 words explaining: Why this face map? Probability distribution? Playtesting criteria?

**Commit**: This is how gameplay variance is introduced.

### Task 3: Probability Calibration (120 min)
Calculate: What % of games does die outcome change result?

- If d12: X% of rolls trigger variance
- Target: 25–35% (enough to matter, not dominating)

Recommend Die_Variance_Multiplier for Elo formula: 0.2, 0.3, or 0.4?

**Reasoning**: Write 200 words explaining your choice.

**Commit**: This directly impacts competitive integrity.

### End of Day 2:
- [ ] Die type finalized
- [ ] Outcome map locked
- [ ] Probability calibrated
- **Output**: Draft of CONQUEST_IA_DIE_SPECIFICATION.md

---

## DAY 3 (Wednesday): SCORING FORMULAS

### Task 1: Elo Specification (120 min)
Read: `CONQUEST_GOVERNANCE_CONSTITUTION.md` (Section I)

Write exact formula:
```
R_new = R_old + K(σ) × (Actual - Expected)
K(σ) = 24 × (1 + Die_Variance_Multiplier)
```

**Decision**: Die_Variance_Multiplier = 0.2, 0.3, or 0.4?
- Write 200 words justifying your choice
- Include: Precedent (Magic, chess), playtesting approach, risk

**Commit**: This is copy-paste for engineering.

### Task 2: Stability Index Specification (120 min)
Write exact formula:
```
Stability = 1 - (StdDev(R_last_20) / MaxAcceptableVariance)
Rating_Weight = Stability × 0.8 + 0.2
```

**Decision**: MaxAcceptableVariance = 40, 60, or 80 rating points?
- Write 200 words justifying
- Include: How this prevents gaming, calibration plan

**Commit**: This prevents sandbagging.

### Task 3: Bot Detection & Session Verification (120 min)
Write filters:
```
Valid IF:
  ✅ duration ≥ 2 min AND ≤ 60 min
  ✅ same_player replays < 5x in 24h
  ✅ IP not flagged (TBD)
```

Flagged IF:
```
  ⚠️ duration < 2 min
  ⚠️ bot_score > 0.7
```

Write 200 words explaining: Why these thresholds? Engineering implementation?

**Commit**: Engineering implements these checks immediately.

### End of Day 3:
- [ ] Elo formula finalized
- [ ] Stability Index locked
- [ ] Bot detection specified
- **Output**: Draft of CONQUEST_SCORING_FORMULAS_FINAL.md

---

## DAY 4 (Thursday): PLAYTEST CRITERIA & DECISION LOG

### Task 1: Duel Playtest Criteria (120 min)
For CONQUEST_DUEL_MECHANIC_SPEC.md, write playtest plan:

**Success = ALL of these must be true after 100 playtests**:
- [ ] Replay rate ≥ 60% (players want another game)
- [ ] Win feels earned (not random): players agree 80%+ of time
- [ ] No degenerate combos (if found, you fix it)
- [ ] Match duration 14-16 min (±30%)
- [ ] Players want to try 3+ strategies (depth exists)

Write 300 words detailing: How will we measure each? What threshold = pass/fail?

### Task 2: Die Playtest Criteria (120 min)
For CONQUEST_IA_DIE_SPECIFICATION.md, write playtest plan:

**Success = ALL must be true**:
- [ ] Die outcome feels fair, not cheap
- [ ] Top players win 60%+ vs. casuals (skill dominates luck)
- [ ] Excitement level high (players engage)
- [ ] Manufacturing <$5 COGS proven

Write 300 words: How do we test each? Metrics?

### Task 3: Decision Log (120 min)
For all 3 specs, write 100-word summary per decision:

Example:
```
DECISION: HP-based win condition
CHOSEN OVER: Territory, hybrid
REASONING: Simpler, proven in Magic/Hearthstone,
          enables 8+ deck archetypes
RISK: May be "solved" (meta too narrow)
PLAYTEST: Measure deck archetype diversity
POINT OF NO RETURN: Too late to change after alpha build
```

Do this for every major choice in Week 1.

### End of Day 4:
- [ ] Playtest criteria written
- [ ] Decision log complete
- [ ] All 3 specs ready for final review
- **Output**: Complete drafts, ready for final pass

---

## DAY 5 (Friday): FINAL PASS & SHIP

### Task 1: Self-Review (120 min)
Read your own specs like you're engineering:
- [ ] Are formulas exact? (Can I code this?)
- [ ] Are decisions justified? (Why this over that?)
- [ ] Are playtest criteria measurable? (Pass/fail clear?)
- [ ] Are there any ambiguities? (None allowed)

Fix anything unclear. **Add one paragraph per major decision: "Why this choice?"**

### Task 2: Format & Finalize (120 min)
Each of 3 docs should have:
- [ ] Title + version + date + author
- [ ] Executive summary (1 para)
- [ ] Main content (sections)
- [ ] Decision log (every choice)
- [ ] Playtest success criteria
- [ ] Next steps (handoff to engineering)

**Format**: Markdown, clean, copy-paste ready.

### Task 3: Ship (60 min)
- [ ] Save all 3 docs to folder
- [ ] Create index: 3-line summary of each
- [ ] One email to stakeholder: "Week 1 specs complete, ready for engineering"
- [ ] Done.

### End of Day 5:
- [ ] CONQUEST_DUEL_MECHANIC_SPEC.md — FINAL
- [ ] CONQUEST_IA_DIE_SPECIFICATION.md — FINAL
- [ ] CONQUEST_SCORING_FORMULAS_FINAL.md — FINAL
- **Status**: ✅ SHIPPED (ready for engineering Monday)

---

## DECISION TEMPLATE (Use This For Every Choice)

```markdown
## DECISION: [What you decided]

**Options considered**:
- Option A: ...
- Option B: ...
- Option C: ...

**Chosen**: Option X

**Reasoning** (200 words):
[Why A over B and C? What evidence? What precedent?]

**Risk if wrong**:
[What happens if this decision is bad?]

**Point of no return**:
[When is it too late to change this?]

**Playtest validation**:
[How will we know this was right?]
```

Use this for EVERY decision. Consistency matters.

---

## TIME ALLOCATION (40 hours)

**Day 1**: 6 hours (duel)
**Day 2**: 6 hours (die)
**Day 3**: 6 hours (scoring)
**Day 4**: 6 hours (playtest + decisions)
**Day 5**: 6 hours (final pass + ship)

**Buffer**: 10 hours (unexpected deep dives, iteration)

**Total**: 40 hours (5 days × 8 hours)

---

## CONSTRAINTS (Non-Negotiable)

✅ **DO**:
- Make specific decisions (no "we'll discuss later")
- Justify with evidence (precedent, math, logic)
- Write for engineers (formulas must be copy-paste-able)
- Include playtest criteria (how do we validate?)
- Lock decisions (once chosen, move forward)

❌ **DON'T**:
- Re-architect product (4 layers locked)
- Change monetization (Option C locked)
- Question governance (constitution locked)
- Leave ambiguities (formulas must be exact)
- Iterate endlessly (one decision per choice, move)

---

## SUCCESS CRITERIA (Week 1 Complete)

**Friday EOD, you have**:
- ✅ 3 complete specs (duel, die, scoring)
- ✅ 1 decision log per spec (100 words each)
- ✅ Playtest criteria written (measurable)
- ✅ Engineering can start Monday
- ✅ No ambiguities remaining

**If ANY of above missing**: Fail. Don't ship until complete.

---

## ESCALATION PATH (If You Get Stuck)

**Stuck on duel win condition?**
→ Choose: HP-based (safe) or territory (risky)
→ If unsure: Pick HP-based (proven pattern)
→ Move forward

**Stuck on die size?**
→ Choose: d12 (elegant) or d10 (standard)
→ If unsure: Pick d12 (cleaner math)
→ Move forward

**Stuck on K-factor?**
→ Choose: 0.3 (balanced)
→ If unsure: Default to 0.3
→ Playtest will calibrate
→ Move forward

**Don't second-guess. Decide. Commit. Ship.**

---

## FINAL CHECKLIST

- [ ] Day 1: Duel spec drafted
- [ ] Day 2: Die spec drafted
- [ ] Day 3: Scoring spec drafted
- [ ] Day 4: Playtest criteria + decision log complete
- [ ] Day 5: Final pass, specs shipped
- [ ] No ambiguities in any doc
- [ ] All formulas exact (copy-paste ready)
- [ ] Engineering can code from this Monday

---

## GO.

**You have 5 days. 3 specs. One goal: Detail under constraints.**

Start now. Finish Friday.

Engineering is waiting.

🚀

---

**Brief owner**: JMT
**Status**: LIVE (execute immediately)
**Deadline**: 2026-02-14 Friday EOD
**Next**: Hand off to engineering Monday 2026-02-17
