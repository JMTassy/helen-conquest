# CONQUEST: Executive Brief
**Complete Product + Governance + Scoring Locked**

**Date**: 2026-02-11
**Version**: 1.0 FINAL
**Audience**: Investors, Board, Leadership
**Read Time**: 5 minutes

---

## THE PRODUCT (60 seconds)

**CONQUEST**: Modular competitive tabletop game with infinite digital extension.

**What it is**:
- **Layer 1**: Standalone tabletop (duel system + cards + physical die) — works offline
- **Layer 2**: Duo mode (cards + IA die) — introduces controlled variance
- **Layer 3**: Digital companion (avatar, castle, Elo ladder, seasons) — drives retention
- **Layer 4**: Creator Studio (template-bound modules) — enables infinite expansion

**Why it works**: Each layer independent. Creator realm cannot pollute competitive ladder.

**Positioning**: "Competitive tabletop system with infinite digital world extension."

---

## THE THESIS

> Tabletop-first eliminates tech dependency.
> Competitive focus drives engagement.
> Creator economy enables 10-year lifespan.
> Governance + scoring keeps system pure.

**Precedent**: Magic: The Gathering (tabletop-first, balance-tight, creator-friendly, 30-year lifespan).

---

## THE NUMBERS (12-Month Target)

| Metric | Target | Why |
|--------|--------|-----|
| **MAU** | 15,000 | Proof of product-market fit |
| **J30 Retention** | 30% | Proof of engagement loop |
| **DAU/MAU** | 20%+ | Proof of stickiness |
| **Duels/User/Day** | 3+ | Proof of replayability |
| **Organic Growth** | 40%+ | Proof of virality |

**All metrics are gates. Miss = stay in phase, iterate.**

---

## THE ARCHITECTURE (Locked)

### 4 Independent Layers

**Layer 1: Tabletop**
- Duel system (clear win condition, 3-5 turns)
- Card pool (50-100 starter cards, templated)
- Physical die (introduces 25-35% variance in outcomes)
- Sellable standalone, zero digital required

**Layer 2: Duo Mode**
- Die triggers events: reroll, multiplicator, twist, penalty, bonus
- Same matchup → different outcomes → players want replays
- Replayability driver (why play again?)

**Layer 3: Digital Companion**
- Avatar + castle (persistent identity, progression)
- Elo-like ranking (transparent, SoS-aware, activity-scored)
- Seasonal resets (75% prestige carry-over, 25% fresh window)
- Duel history + achievements (engagement hooks)

**Layer 4: Creator Studio** (Post-MVP, gated at 10K DAU)
- Players create card modules (template-bound, no chaos)
- Modules progress: Draft → Labs → Guild Approved → Featured → Official
- Gaming group sees "creator ladder" (tiers, not marketplace)
- Revenue share only after proven quality (bridge gates)

---

## THE GOVERNANCE (Airtight)

### Two Orthogonal Systems (Never Mixed)

**Competitive Ladder**
- Modified Elo accounting for die variance (K-factor adjustment)
- Stability Index prevents sandbagging
- Behavior scoring prevents toxicity
- Seasonal reset enables newcomers without freezing top

**Creator Economy**
- Creative Impact Score (CIS): Replay rate + Retention delta + Qualified votes + Guild adoption
- Tier progression (automated: T1-4, manual audit: T5)
- Bridge gates (balance, IP, ops cost, exploit-check)
- Kill-switch + immutable receipts (audit trail)

**Critical rule**: Creator modules grant ZERO Elo bonus. Ladder formula identical regardless of module played.

---

## THE SCORING (Load-Bearing Layer)

### Competitive: Modified Elo

```
K = Base_K × (1 + Die_Variance_Multiplier × LuckIndex)
Base_K = 32
Die_Variance_Multiplier = 0.30 (tunable [0.20, 0.40])
LuckIndex = 0–1 based on die influence in match

ΔR = K × (Actual_Score - Expected_Score)
```

**Anti-grind caps**:
- Daily gain capped: +20 rating/day max
- Win streak plateau: 5+ wins = flat bonus (no acceleration)
- Farming prevention: 4th+ match vs same opponent = 0.5x K

**Seasonal reset**:
```
R_new = 0.75 × R_old + 0.25 × 1200
(preserves 75% prestige, enables 25% newcomer window)
```

---

### Creative: CIS Formula

```
CIS = (Replay Rate × 0.30)
    + (Retention Delta × 0.25)
    + (Qualified Vote × 0.30)
    + (Guild Adoption × 0.15)

Scaled 0–100
```

**Anti-fraud built-in**:
- Verified sessions only (min 4 min, collusion checks)
- Voter credibility weighting (reliability + rating)
- Adoption spike detection (3σ → manual review)
- Farming detection (same group replaying module)

---

## THE MONETIZATION (Option C: Hybrid Controlled)

### Phase 0 (MVP, Months 0–6)
**Reputation only** (no revenue)
- Creators earn: tiers, badges, visibility, creator tools
- Studio learns: CIS accuracy, balance, fraud patterns

### Phase 1 (Month 6+, if 15K MAU + zero exploits)
**Creator Program opens** (closed, contracts)
- Max 50 creators invited
- Revenue share: 30% net on Official Pack cosmetics
- Kill-switch: ban module → payouts freeze (no refunds)

### Phase 2 (Year 2+, if anti-fraud industrialized)
**Marketplace** (optional)
- Only if fraud false-positive <2%
- Otherwise: curated store forever (acceptable)

**Philosophy**: No pay-to-win. Revenue aligns with quality, not shortcuts.

---

## THE RISK REGISTER (Mitigated)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Duel system shallow** | 🔴 Critical | Playtest 100+ players before beta |
| **Balance breaks** | 🔴 Critical | Hire balance designer + council + gates |
| **Creator economy gamed** | 🟠 High | Verified sessions + qualified voting + receipts |
| **Competitive alienates casuals** | 🟠 High | Achievement paths + cosmetics + seasons |
| **Content ops unsustainable** | 🟠 High | Contract balance council (3-5 external) |

**All other risks**: Medium (manageable).

**Confidence level**: 8/10 (solid architecture, execution-dependent).

---

## THE INVESTMENT

**Total Budget**: $500K–$1M (12 months)

**Allocation**:
- Design + Engineering: 60% ($300–600K)
- Content Ops: 20% ($100–200K)
- Marketing: 15% ($75–150K)
- Reserve: 5% ($25–50K)

**Team** (5 FTE):
1. Game Designer (mechanics, balance, seasons)
2. Lead Backend Engineer (ranking, leaderboard, economy)
3. Frontend Engineer (avatar, castle, UI/UX)
4. Content Ops (QA, seasonal planning, balance council)
5. Product Manager (metrics, roadmap, comms)

**Payroll**: $250–350K (salaries + benefits)
**Tools + Infrastructure**: $50–100K
**Playtest + QA**: $50–100K
**Marketing**: $75–150K

---

## THE TIMELINE

| Milestone | Gate | Proof Required | Month |
|-----------|------|---|---|
| **Alpha** | Playable MVP | Duel + avatar + Elo | 0 |
| **Beta** | 30% J30 retention | 1000 beta players, healthy Elo | 4 |
| **D2C Launch** | 10K DAU + organic | Press, community momentum | 8 |
| **Creator Program** | 15K MAU + zero exploits | Program gates met | 6 |
| **Amazon/BGG** | 15K MAU proved | Retail logistics partner | 12 |

**All gates are binary**: Miss = stay in phase, iterate. No soft deadlines.

---

## THE DECISION GATES (Go/No-Go)

### GREEN LIGHT to proceed if:
1. ✅ Duel mechanic playtest confirms depth (5+ archetypes viable)
2. ✅ Investor commits $500K+ (capital secured)
3. ✅ Core team assembled (all 5 roles hired)

### RED LIGHT to pause if:
1. 🔴 Duel mechanic playtest <3 replayability score
2. 🔴 Team attrition >1 person before Alpha
3. 🔴 Balance breaks in beta (cannot fix before D2C)

---

## WHAT'S DECIDED (Non-Debatable)

✅ **4-layer architecture** (tabletop → duo → digital → creator) — locked

✅ **Monetization**: Option C (reputation MVP → creator program M6 → marketplace Y2) — locked

✅ **Governance**: Two orthogonal systems (ladder never polluted by creative) — locked

✅ **Scoring**: Modified Elo + Stability Index + CIS (anti-fraud, anti-gaming) — locked

✅ **MVP scope**: Strict IN/OUT (creator studio deferred, no open chat, no marketplace) — locked

✅ **Phase gates**: Measurable, gating (beta @ 30% J30, D2C @ 10K DAU) — locked

---

## WHAT'S READY NOW

✅ **Complete product specification** (11 documents, 25,000 words)
✅ **Complete governance constitution** (rules, zero ambiguity)
✅ **Complete scoring system** (formulas, anti-fraud, receipts)
✅ **Risk assessment** (8 real risks, mitigations credible)
✅ **Budget + timeline** (conservative, realistic)
✅ **Week 1 design sprint brief** (ready for designer to execute)

---

## WHAT'S NEXT (In Order)

### IMMEDIATE (Today)
- [ ] Investor decision: GREEN LIGHT or request more info?
- [ ] If GREEN: Begin team assembly
- [ ] If REQUEST: Provide `CONQUEST_SELECT_SKEPTIC_REVIEW.md` (risk details)

### WEEK 1 (Monday–Friday)
- [ ] Designer executes sprint (duel, die, scoring specs)
- [ ] Get investor commitment (if not already secured)
- [ ] Begin team hiring (game designer + engineers)

### MONTH 1
- [ ] Team assembled (5 FTE)
- [ ] Alpha build starts (duel + avatar + Elo)
- [ ] Recruit 50 beta testers
- [ ] Playtest begins

### MONTH 4
- [ ] Beta gate decision (30% J30 retention proven?)
- [ ] If GREEN → Open Beta
- [ ] If RED → Debug retention, rebalance, re-playtest

---

## SUPPORTING DOCUMENTS (Complete)

**For investors**: `CONQUEST_SHIP_SUMMARY.md` (1 page), `CONQUEST_SPECIFICATION_MVP.md` (full spec), `CONQUEST_SELECT_SKEPTIC_REVIEW.md` (risks)

**For engineers**: `CONQUEST_SPECIFICATION_MVP.md` + `CONQUEST_GOVERNANCE_CONSTITUTION.md` (sections I–V) + `CONQUEST_SCORING_MODEL.md`

**For designers**: `CONQUEST_WEEK1_DESIGN_SPRINT_BRIEF.md` + `CONQUEST_SPRINT_KICKOFF.md`

**For navigation**: `CONQUEST_COMPLETE_PACKAGE.md` (decision tree by role)

---

## ONE-SENTENCE SUMMARY

**CONQUEST is a tabletop-first, competitive, scalable game system with airtight governance and infinite creator expansion, designed for 15K MAU and 30% retention within 12 months.**

---

## FINAL AUTHORITY

This brief is the source of truth.

All decisions above are **locked** and non-debatable.

Any changes require versioning (v1.1, etc.) and stakeholder approval.

---

**Owner**: JMT
**Status**: ✅ FINAL (ready to distribute)
**Confidence**: 8/10 (architecture solid, execution-dependent)

**Next step**: Investor decision. Then build.

🚀
