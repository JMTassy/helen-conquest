# CONQUEST: MVP SPECIFICATION
**Modular Competitive Tabletop + Digital Extension**

**Version**: 1.0 SHIP
**Date**: 2026-02-11
**Audience**: Investors, Design Team, Content Ops

---

## EXECUTIVE SUMMARY

**CONQUEST is a modular competitive tabletop system with infinite digital world extension.**

**Core thesis**: Mechanical depth (standalone tabletop) + digital retention (companion) + creative expansion (player studios).

**Target**: 15,000 MAU by Month 12. 30% J30 retention. Organic growth >40%.

**Investment required**: $500K—$1M (design, ops, marketing).

---

## PRODUCT ARCHITECTURE

### Layer 1: Standalone Tabletop
**Works without any digital component. Sellable on day one.**

- **Duel System**: 2-player competitive; 3-5 turns; clear win condition
- **Cards**: 50-100 starter cards (templated, learnable)
- **Physical Die**: Companion object; introduces events, multipliers, twists
- **Ranking**: Manual score tracking (can be written on paper)

**Why this works**: Magic: The Gathering, Chess, Poker all prove tabletop-first works.

---

### Layer 2: Duo Mode (Cards + IA Die)
**Tabletop enhanced with randomized game events.**

**IA Die Functions**:
- Reroll any outcome (retry a failed roll)
- Multiplicator (2x/0.5x reward scaling)
- Event injection (random card appears on board)
- Twist (swap opponent card with yours)
- Penalty (lose a resource, skip next turn)
- Bonus (gain extra action)

**Design Principle**: Die reintroduces variance without breaking skill progression.

**Replayability**: Same matchup produces different outcomes. Players hit "one more game."

---

### Layer 3: Digital Companion
**Persistent identity, progression, and ranking.**

**Player Avatar**:
- Name, image, cosmetic variations
- Level (unlocked through play)
- Seasonal prestige (resets each season)

**Castle**:
- Personal territory (visual, persistent)
- Grows with progression (more rooms, towers, defenses)
- **Unlocks gameplay features** (new card slots, deck variants)
- Defendable in challenges (other players can raid)

**Ranking**:
- Elo-like system (transparent, published)
- Separate ladders (casual, ranked, seasonal)
- Leaderboard (top 100 visible)

**Seasons**:
- 4-week rotation
- New card releases
- New challenges
- Ranked reset (everyone back to baseline)

**Achievements**:
- Milestone unlocks (10 wins, 100 duels, etc.)
- Badge cosmetics
- Seasonal challenges (win with X card, beat Y player, etc.)

---

### Layer 4: Creator Studio (Post-MVP)
**Launches at 10K DAU. Not in MVP.**

**Permissions** (Phase 2):
- Design custom card variants (within stat budgets)
- Create deck recipes (curated collections)
- Run seasonal challenges (guild tournaments)
- Customize castle (themes, cosmetics)
- Publish decks (community library, reputation gain)

**Design Constraint**: All UGC is **template-bound**. No freeform chaos.
- Card stat ranges locked (HP: 3-8, Damage: 1-5, Cost: 1-7)
- Ability budget capped (balance score per card)
- Rarity distribution enforced (10% epic, 30% rare, 60% common)

**Why template-bound**: Prevents power creep. Keeps balance tight. Enables fast QA.

---

## CORE GAME LOOP

```
1. QUEUE
   ├─ Find opponent (ranked ladder, casual, friend challenge)
   └─ Load player decks + castle stats

2. SETUP
   ├─ Draw opening hand (3-5 cards)
   ├─ Deploy castle defense (optional)
   └─ Opponent does same (simultaneous)

3. ROUND (repeat 3-5x)
   ├─ Player plays 1 card OR activates ability
   ├─ Opponent responds OR passes
   ├─ Resolve effects (HP changes, card triggers)
   └─ Check end conditions (someone died? Someone won?)

4. ROLL (end of each round)
   ├─ Die roll (determines next round event)
   ├─ Apply die effect (reroll, multiplicator, twist, penalty, bonus)
   └─ Announce outcome (both players see what happened)

5. RESOLVE
   ├─ Apply cumulative effects
   ├─ Check for win (first to 0 HP loses, or control condition met)
   └─ If not won, return to ROUND

6. RANK
   ├─ Calculate Elo delta (both players)
   ├─ Update castle progress (winner gains castle XP)
   ├─ Record duel history (archive for replay)
   └─ Award cosmetics if milestone hit

7. ARCHIVE
   ├─ Save duel replay (cards played, die rolls, turn order)
   ├─ Publish to leaderboard
   └─ Send to opponent's history

8. REPEAT
   └─ Player queues next duel

```

**Loop Duration**: 12-15 minutes (including queue + setup).

**Replayability**: Same decks, different die rolls → different outcomes.

---

## MVP SCOPE (In / Out)

### ✅ IN SCOPE
- [ ] Core duel mechanics (card play, damage, win condition)
- [ ] IA Die (physical object + game mechanics)
- [ ] Avatar system (customization, cosmetics)
- [ ] Castle progression (visual + gameplay unlocks)
- [ ] Elo ranking (transparent, published)
- [ ] 3 starter decks (tutorial, intermediate, advanced)
- [ ] Seasonal progression (4-week rotation, new cards, challenges)
- [ ] Leaderboard (top 100)
- [ ] Minimal social (friend add, friend challenges, shared replays)
- [ ] Closed-loop ECU (in-game credits only, no cash-out, no transfer)
- [ ] Tutorial + onboarding (15 min to first duel)

### ❌ OUT OF SCOPE (Post-MVP)
- ❌ Creator Studio (Phase 2, 10K DAU gate)
- ❌ Open community chat (moderation hell)
- ❌ Trading or marketplace (fraud risk, economic complexity)
- ❌ Love/Life modules (scope creep)
- ❌ AI tutor (platform dependency, cost)
- ❌ Real-time multiplayer (latency problems, complexity)
- ❌ Open UGC (chaos, balance breaks)

---

## GOVERNANCE & SCORING SYSTEMS

**This section summarizes scoring architecture. Full technical specs in referenced documents.**

### Competitive Ladder (Elo-Based)

**Foundation**: Modified Glicko-like Elo accounting for IA Die variance.

**Key metrics**:
- **Rating (R)**: Core Elo, modified by K-factor = `Base_K × (1 + Die_Variance_Multiplier)`
- **Win Rate**: Consistency signal (capped display to avoid outliers)
- **Strength of Schedule (SoS)**: Avg opponent rating (resists sandbagging)
- **Activity Score**: Decay-weighted recent play (prevents "rating locked" players)
- **Stability Index**: Variance over last 20 games (rewards consistency)

**Anti-grind rules**:
- Daily gain cap: +20 rating/day max
- Win streak bonus plateau: 5+ consecutive wins = flat bonus (no acceleration)
- Diminishing returns on same opponent: 4th+ match vs same opponent = 0.5x K-factor

**Seasonal reset (every 12 weeks)**:
```
R_new = (R_old × 0.75) + 1200
(Preserves 75% prestige, enables newcomer window)
```

**Behavior scoring** (separate from Elo):
- Blocks ranked if BS < 70 (conduct issues)
- 7-day ban if BS < 50; 30-day if BS < 30
- Can be appealed (72-hour manual review)

**Full spec**: See `CONQUEST_GOVERNANCE_CONSTITUTION.md` (Section I)

---

### Creator Economy (CIS-Based, Post-MVP)

**Note**: MVP has no creator economy. This launches at Phase 1 (Month 6+, if 15K MAU gate met).

**Creative Impact Score (CIS)** measures creator engagement:
- **Replay Rate** (0.30 weight): % of players who replay module
- **Retention Delta** (0.25 weight): Does module increase player retention?
- **Qualified Vote** (0.30 weight): Weighted community perception (voter credibility scoring)
- **Guild Adoption** (0.15 weight): How many guilds use this module?

**Anti-gaming**: Session verification (bot detection), voter accuracy weighting, adoption spike flags.

**Tier progression** (automated gates):
1. **Draft** → Private (creator only)
2. **Community Tested** → 50+ verified sessions
3. **Guild Approved** → 1+ guild adoption
4. **Community Featured** → CIS ≥ 65th %ile
5. **Official Candidate** → CIS ≥ 85th %ile + manual audit (24h)

**Bridge to revenue** (Phase 1 only):
- Creator must reach Tier 5 (Official Candidate)
- Studio invites to "Creator Program" (closed, contracts)
- Creator earns 30% of cosmetic sales tied to their module
- Studio retains 70% (ops, balance, support)

**Governance**: Creator modules cannot pollute competitive ladder. Elo earned on any module = standard formula (no multipliers).

**Full spec**: See `CONQUEST_SCORING_MODEL.md` (all sections) + `CONQUEST_GOVERNANCE_CONSTITUTION.md` (Section III)

---

### Separation of Concerns (Walls Between Systems)

**Core principle**: Ladder integrity ≥ creator freedom.

**Enforcement**:
1. **Creator modules grant zero Elo directly** (standard formula only)
2. **Official Packs have zero gameplay advantage** (balance gate before release)
3. **Behavior scoring is ladder-only** (doesn't affect CIS)

**Full governance rules**: See `CONQUEST_GOVERNANCE_CONSTITUTION.md` (Section IV)

---

## CONTENT OPS (Risk + Advantage)

### First-Order Risk
- **Deck balance**: Broken combos tank ranked integrity
- **Clarity**: Unclear card text creates support load
- **Churn**: Boring seasons → players leave

### First-Order Advantage
- **Template constraints**: Content is deterministic, easy to QA
- **Small card pool**: Fast to playtest (1000 combos, not 100K)
- **Tight feedback loop**: Telemetry shows win rates in real-time

### Operations Model
1. **Design** (1-2 designers) — new cards, seasonal themes, balance changes
2. **Playtest** (internal, 50 games/card) — identify broken combos
3. **Beta** (100 external players) — community feedback, edge cases
4. **Publish** (go live, monitor Elo swings)
5. **Iterate** (ban/restrict cards, release hotfixes, plan next season)

**Sustainability**: 2 FTE can manage 50-100 cards + seasonal rotation indefinitely.

---

## MONETIZATION (Post-MVP)

**MVP is free-to-play.** Money is generated only post-proof-of-concept.

**Phase 2 Monetization** (only after 30% J30 retention achieved):
1. **Cosmetics** (castle skins, avatar skins, card backs) — 5-10% conversion
2. **Convenience** (fast-track season, instant card unlocks) — 2-5% conversion
3. **Premium Content** (seasonal battle pass, tier unlocks) — 3-7% conversion
4. **Guild Economy** (guild pass, house rules, private tournaments) — 1-3% conversion
5. **Creator Revenue Share** (deck authors earn 30% of cosmetic sales) — incentive

**Philosophy**: No pay-to-win. No energy gates. No time walls. Pure optional cosmetics.

**Target**: 15% of MAU in premium tiers. ARPU $5-10/month by Year 2.

---

## SUCCESS METRICS (12-Month Target)

| Metric | Target | Owner | Measure |
|--------|--------|-------|---------|
| **DAU** | 5,000 | Product | Monthly active players, daily logins |
| **MAU** | 15,000 | Product | Monthly unique players |
| **J30 Retention** | 30% | Retention | Players active Day 30 / Day 1 |
| **DAU/MAU Ratio** | 20%+ | Engagement | Frequency of play |
| **Avg. Session** | 25 min | UX | Time per play session |
| **Duels/Day/User** | 3+ | Content | Duel volume, replayability |
| **Share Rate** | 15% | Social | Replay shares, deck shares, friend invites |
| **Challenge Acceptance** | 40%+ | Social | Accepted friend challenges / sent |
| **Content Creators** | 10%+ of MAU | Community | Players with published content (Phase 2) |
| **Organic Growth** | 40%+ | Marketing | Growth via word-of-mouth / virality |

---

## PHASE GATES (Distribution Expansion)

| Phase | Gate | Proof Required | Entry Month |
|-------|------|---|---|
| **Closed Alpha** | Playable MVP | Duel system + avatar complete | Month 0 |
| **Open Beta** | 30% J30 retention + healthy Elo distribution | 1,000 beta players, no balance breaks | Month 4 |
| **D2C Launch** | 10,000 DAU + 40%+ organic growth | Press coverage, community momentum | Month 8 |
| **Amazon/BGG** | 15,000 DAU + retail logistics partner | Board game databases, online marketplace | Month 12 |
| **Physical Retail** | 50,000 DAU + unit economics proven | Retail distributor signed, 6-month forecast | Month 18+ |

---

## KNOWN RISKS + MITIGATION

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Duel system lacks depth** | 🔴 Critical | Playtest with 100+ players before beta. Target 5+ replays per player. |
| **Balance breaks (broken combos)** | 🔴 Critical | Hire game balance designer. Weekly telemetry review. Ban/restrict authority. |
| **Creator economy pressure (cash-out demand)** | 🟠 High | Clarify Year 2 monetization. Make UGC non-monetary in MVP. |
| **Competitive focus alienates casuals** | 🟠 High | Add achievement paths, seasonal cosmetics, non-ranked modes. |
| **Content ops unsustainable** | 🟠 High | Contract balance council (3-5 external designers). Shared responsibility. |
| **Retail logistics complexity** | 🟠 High | Identify logistics partner by Month 8 (not Month 18). Physical + digital sync. |
| **Toxic leaderboard (smurfs, griefing)** | 🟡 Medium | Behavior scoring, seasonal bans, report system. Enforce code of conduct. |
| **Seasonal churn (boring content)** | 🟡 Medium | 4-week cadence forces novelty. Community feedback loop on card design. |

---

## TEAM + INVESTMENT

### Core Team (MVP)
- **1 Game Designer** (duel mechanics, card balance, seasons)
- **1 Lead Engineer** (backend, ranking, leaderboard)
- **1 Frontend Engineer** (avatar, castle, UI)
- **1 Content Ops** (card QA, seasonal planning, balance council coordination)
- **1 Product Manager** (metrics, phase gates, communications)

**Budget**: $500K—$1M (12 months, all-in: salaries, tools, ops, marketing).

### Growth Hires (Months 6+)
- **Community Manager** (Discord, moderation, feedback)
- **Marketing** (press, influencer, social)
- **Customer Support** (balance questions, bug reports)

---

## DECISION GATES (Go/No-Go)

### ✅ GREEN LIGHT to proceed?
**Depends on**:
1. Duel system playtest confirms 5+ replayability score (before Alpha)
2. Investor commits $500K+ (before engineering start)
3. Core team assembled (all 5 roles filled before Month 1)

### 🔴 RED LIGHT to pause?
**Pauses if**:
1. Duel system playtests <3 replayability (go back to design)
2. Team attrition >2 people (rebuild before launch)
3. Balance breaks in beta (cannot progress to D2C)

---

## APPENDIX: COMPETITIVE LANDSCAPE

### Comps (What Works)
- **Magic: The Gathering** (tabletop-first, card pools, balance-tight)
- **Catan** (simple rules, high replay, social, scaled to digital)
- **Wordle** (daily reset, retention, simplicity, share-friendly)
- **Duolingo** (streaks drive retention, visible progress)

### Warnings (What Fails)
- **Hearthstone** (initially tabletop-unfriendly, then corrected)
- **Yu-Gi-Oh** (power creep, unbalanced, alienates casuals)
- **Diablo Immortal** (pay-to-win, toxic reception)

### CONQUEST Advantage
- Tabletop-first eliminates platform dependency
- Closed-loop economy avoids fraud/RMT issues
- Template-bound UGC prevents chaos
- Competitive focus aligns with gaming audience

---

## NEXT STEPS

**Immediate (Week 1)**:
- [ ] Finalize duel mechanic (win condition, card interaction rules)
- [ ] Prototype IA Die (manufacturing, gameplay impact)
- [ ] Assemble core team
- [ ] Secure funding commitment

**Short-term (Month 1-2)**:
- [ ] Build Alpha (duel + avatar + Elo)
- [ ] Recruit 50 beta testers
- [ ] Define seasonal cadence

**Medium-term (Month 3-4)**:
- [ ] Playtest 100+ games
- [ ] Balance card pool
- [ ] Prepare Open Beta

---

## APPROVAL

**This specification is ready for**:
- ✅ Investor review
- ✅ Design team kickoff
- ✅ Engineering planning
- ✅ Content ops planning

**Decision required**: GREEN LIGHT to engineering start?

---

**Specification Owner**: JMT (Design + Product)
**Version**: 1.0 SHIP
**Date**: 2026-02-11
**Status**: READY FOR APPROVAL
