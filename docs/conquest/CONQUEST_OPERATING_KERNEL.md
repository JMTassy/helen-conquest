# CONQUEST Operating Kernel
**Framework for Product Development: Modular Tabletop + Digital Extension**

**Version**: 1.0 (EXPAND Phase Captured)
**Date**: 2026-02-11
**Status**: Raw synthesis, awaiting SELECT phase

---

## EXECUTIVE CLAIM
**CONQUEST is a modular competitive tabletop system with infinite digital world extension.**

Not narrative. Not simulation. **Mechanical depth + competitive loop + creative extension.**

---

## ARCHITECTURE: 4 LAYERS (Decoupled)

### LAYER 1: Core Tabletop (Autonomous)
**Principle**: Works without digital. Sellable tomorrow.

**Components**:
- Duel system (clear, competitive, deterministic)
- Manual ranking (analog)
- Card deck
- Die (IA companion, physical object)
- Simple but deep mechanics

**Success Metric**: Playable out-of-box. No app required.

**Risk**: If core is weak, everything collapses.

---

### LAYER 2: Duo Mode (Cards + IA Die)
**Principle**: Introduce controlled uncertainty through physical randomization.

**IA Die Functions**:
- Random events (reroll, swap, escalate)
- Multiplicators (2x reward, penalty, twist)
- Strategic twist injection
- Disadvantage application
- Bonus activation

**Effect on Play**:
- Replayability (same setup, different outcomes)
- Tension (agency vs. chaos)
- Narrative flavor (optional, not forced)

**Success Metric**: Players ask for replays. "What if we roll again?"

---

### LAYER 3: Digital Companion
**Principle**: Retention engine. Create persistent identity and progression.

**Components**:
- Avatar (persistent identity)
- Castle/territory (personal space)
- Digital territories (progression tree)
- Duel history (data layer)
- Elo-like ranking (transparent)
- Seasonal progression
- Achievements (unlockables)
- Visual progression (castle grows, avatar levels)

**Effect on Behavior**:
- Identity investment ("my castle")
- Long-term engagement (seasons)
- Social proof (ranking visibility)
- Completion motivation (achievements)

**Success Metric**: 30% retention Day 30. DAU/MAU > 20%.

---

### LAYER 4: Creator Studio
**Principle**: Infinite expansion through user-generated content. D&D model.

**Permissions**:
- Create custom cards (with template constraints)
- Create scenarios (preset duel challenges)
- Create challenges (seasonal, local)
- Customize castle (appearance, structure)
- Create guilds (teams, house rules)
- Publish decks (community library)

**Why This Works**:
- D&D survived because **players create content**.
- Shifts burden from studio to community.
- Unlock emergent gameplay.
- Creates micro-economies (trading decks, guild passes).

**Success Metric**: 10%+ content creators. Organic deck discovery.

---

## CORE LOOP (Competitive)

```
1. QUEUE (find opponent or AI)
2. SETUP (place pieces, draw cards)
3. DUEL (3-5 turns, clear win condition)
4. ROLL (IA die introduces twist)
5. RESOLVE (score, apply effects)
6. RANK (update Elo, castle progress)
7. ARCHIVE (duel recorded, repeatable)
8. REPEAT
```

**Design Principle**: Each loop is <15 minutes. Repeatable. Rewarding.

---

## MONETIZATION STACK (Future)

**NOT MVP.** Only after proof of 15,000+ users + 30% J30 retention.

1. **Cosmetics** (castle skins, avatar skins)
2. **Convenience** (fast-track seasons, card unlocks)
3. **Premium Content** (seasonal battle pass)
4. **Guild Economy** (guild pass, house rules)
5. **Creator Revenue Share** (card makers earn)

**Philosophy**: No pay-to-win. No energy gates. No pay-to-play.

---

## MVP CONSTRAINTS (Non-Negotiable)

### IN SCOPE:
- [ ] Core tabletop (duel, ranking, cards)
- [ ] Duo mode (IA die integration)
- [ ] Digital companion (avatar, castle, ranking)
- [ ] Minimal social (friend add, challenges, leaderboard)
- [ ] Closed-loop ECU (in-game credits, no cash-out)
- [ ] 2-3 starter decks
- [ ] Tutorial + onboarding

### OUT OF SCOPE:
- ❌ Love module
- ❌ Life module
- ❌ Open UGC (moderation hell)
- ❌ Real-time chat (content ops disaster)
- ❌ Open-world exploration (scope creep)
- ❌ Marketplace (economic complexity)
- ❌ Trading (fraud surface)

---

## CONTENT OPS (First-Order Risk + Advantage)

### Risk:
- Deck balance (broken card combos)
- Deck clarity (rules clarity)
- Seasonal churn (players bored)

### Advantage:
- **Template-bound creativity** (no chaos, deterministic outputs)
- **Tight QA** (small deck pool, easy to test)
- **Quick iteration** (new season every 4 weeks)

### Process (Minimal):
1. Design deck (template constraints)
2. Internal playtest (3-5 rounds, clear win/loss)
3. Beta audience (100 beta players)
4. Publish + monitor (Elo swings, ban cards as needed)
5. Iterate (next season)

---

## GAMING METRICS TARGET (12-Month)

| Metric | Target | Owner |
|--------|--------|-------|
| DAU | 5,000 | Product |
| MAU | 15,000 | Product |
| J30 Retention | 30% | Retention |
| DAU/MAU | 20%+ | Engagement |
| Avg. Session | 25 min | UX |
| Duels/Day/User | 3+ | Content |
| Share Rate | 15% | Social |
| Challenge Acceptance | 40%+ | Social |
| Creators | 10%+ of MAU | Community |
| Organic Growth | 40%+ | Marketing |

---

## ARCHITECTURE DEBT (Known Risks)

**MECHANICAL RISK**: If duel system lacks depth → no reboots → churn.

**SOCIAL RISK**: If leaderboard only → toxic → churn.

**CONTENT RISK**: If deck balance breaks → ranked unplayable → churn.

**CREATOR RISK**: If templates too restrictive → UGC dies → no extension.

---

## EVIDENCE-FIRST DISCIPLINE

Every claim must tie to:
1. **Precedent** (D&D, Magic, Hearthstone, etc.)
2. **Metric** (target retention, DAU, etc.)
3. **Test** (can we measure it in MVP?)

No unprovable claims:
- ❌ "Will be the next Fortnite"
- ❌ "Infinite monetization"
- ❌ "Everyone will want to play"

Yes to:
- ✅ "15,000 users by 12M based on X playtest"
- ✅ "30% J30 retention from closed-beta cohort"
- ✅ "Content ops sustainable with <5 FTE"

---

## PHASE GATES (Distribution Expansion)

| Gate | Proof Required | Entry |
|------|---|---|
| **Closed Beta** | Playable MVP | Now |
| **Open Beta** | 30% J30 retention + healthy Elo distribution | 4M |
| **D2C (Direct)** | 10,000 DAU + 40%+ organic growth | 8M |
| **Amazon/BGG** | 15,000 DAU + press coverage | 12M |
| **Retail** | 50,000 DAU + unit economics proven | 18M+ |

---

## STRATEGIC DECISIONS (Locked)

1. **Tabletop-first, Digital-second**: Core must work offline.
2. **Closed-loop MVP**: No open chat, no transfers, no marketplace.
3. **Competitive focus**: Ladder > narrative. Elo > story.
4. **Template-bound creativity**: UGC happens within guardrails.
5. **Content ops as moat**: Deck balance, seasonal rhythm, quality control.

---

## NEXT SPRINT (SELECT Phase)

**Deliverable**: CONQUEST MVP Specification

**Questions for Skeptic**:
1. Does duel system have enough depth for 30+ replays?
2. Can IA die be implemented as physical object (not digital gimmick)?
3. Is leaderboard enough for retention without narrative?
4. Can creator studio launch at 10k users (not MVP)?
5. Is 12-month path to retail realistic?

---

## WORKING NOTES

### Append as new insights emerge:

- [Pending: Duel mechanic deep dive]
- [Pending: Card balance framework]
- [Pending: Seasonal cadence spec]
- [Pending: Creator studio contract model]
- [Pending: Retail logistics (physical + digital sync)]

---

**EXPANSION PHASE COMPLETE**

Next: SELECT (Skeptic pressure test)
Then: SHIP (Specification deck)

---

**Owner**: JMT
**Last Updated**: 2026-02-11 (EXPAND captured)
**Status**: Awaiting SELECT review
