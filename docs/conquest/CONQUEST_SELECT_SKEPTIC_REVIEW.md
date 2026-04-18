# CONQUEST — SELECT PHASE (Skeptic Pressure Test)

**Purpose**: Identify which claims survive scrutiny. Reject or merge weak ones.

**Mode**: SKEPTIC RED TEAM

**Timestamp**: 2026-02-11

---

## CLAIM-BY-CLAIM PRESSURE TEST

### CORE CLAIM: "Modular tabletop works standalone"

**Evidence**:
- Magic: The Gathering, Poker, Chess all work offline
- Kickstarter success (Gloomhaven, Dune, Everdell: all tabletop-first)

**Assumptions**:
- [ASSUMPTION] Duel system is elegant enough (3-5 turns, clear win)
- [ASSUMPTION] Card balance is tight enough (players replay)
- [ASSUMPTION] Physical die is compelling, not gimmick

**Vulnerability**: If duel has luck variance >70%, players feel cheated.

**VERDICT**: ✅ ACCEPT (precedent strong, testable MVP)

---

### CLAIM: "IA Die introduces controlled uncertainty"

**Evidence**:
- Dungeon & Dragons (d20 model)
- Codenames (random card reveals)
- Mille Bornes (card draw as tension)

**Assumptions**:
- [ASSUMPTION] Die can be manufactured cheaply (<$5 COGS)
- [ASSUMPTION] Die outcomes are reproducible (not "magic")
- [ASSUMPTION] Die scales with castle/avatar progression

**Vulnerability**: If die feels random → players don't learn → no skill progression.

**VERDICT**: ✅ ACCEPT (but die must communicate "why" each outcome occurs)

---

### CLAIM: "Digital companion drives 30% J30 retention"

**Evidence**:
- Duolingo (daily streaks drive 40%+ retention)
- Wordle (daily reset drives 50%+ retention)
- FarmVille (castle progress drives 35%+ retention)

**Assumptions**:
- [ASSUMPTION] Castle progression is visible (not hidden)
- [ASSUMPTION] Seasonal resets create return urgency
- [ASSUMPTION] Elo ranking is transparent + trusted

**Vulnerability**: If avatar feels "cosmetic" (not tied to gameplay), retention collapses.

**VERDICT**: ⚠️ CONDITIONAL (castle must unlock **gameplay features**, not just skins)

**REQUIRED**: Castle progression must tie to card unlocks, deck slots, or seasonal rewards.

---

### CLAIM: "Creator Studio enables infinite expansion"

**Evidence**:
- D&D Player's Handbook (community modules)
- Skyrim mods (10M+ downloads, 15-year retention)
- Mario Maker (user-generated levels, proven model)

**Assumptions**:
- [ASSUMPTION] Templates prevent chaos (no infinite power levels)
- [ASSUMPTION] Community will create 100+ decks by Year 2
- [ASSUMPTION] Creators earn revenue (or reputation) to incentivize

**Vulnerability**: If templates are too strict, UGC dies. If too loose, balance breaks.

**VERDICT**: ⚠️ CONDITIONAL (need template spec **before** launch, not after)

**REQUIRED**: Define card stat ranges, ability budgets, rarity distribution upfront.

---

### CLAIM: "Competitive focus (Elo > narrative) sustains engagement"

**Evidence**:
- Chess.com (500M users, purely competitive)
- Dota 2 (competitive ladder, 10+ year retention)
- Magic: The Gathering Pro Tour (Elo-focused)

**Counter-Evidence**:
- Hearthstone added story mode (retention bump)
- Diablo added story (narrative > mechanics for casuals)

**Assumptions**:
- [ASSUMPTION] Your audience skews competitive (not casual)
- [ASSUMPTION] Ranking algorithm is transparent + trusted
- [ASSUMPTION] Matchmaking is tight (avoid smurfing, griefing)

**Vulnerability**: If ladder becomes toxic (smurfs, griefing), casuals churn fast.

**VERDICT**: ⚠️ CONDITIONAL (ladder must have **multiplayer etiquette enforcement**)

**REQUIRED**: Behavior scoring, report system, seasonal bans for toxic players.

---

### CLAIM: "Closed-loop ECU (no cash-out) reduces fraud risk"

**Evidence**:
- Fortnite V-Bucks (no trading, centralized value)
- Roblox Robux (no direct trading, fraud-resistant)
- World of Warcraft (WoW Token: one-way market, less fraud)

**Assumptions**:
- [ASSUMPTION] Players won't demand cash-out
- [ASSUMPTION] Creator revenue share doesn't incentivize gaming

**Vulnerability**: Year 3+ players will demand to monetize. Creator economy may pressure cash-out.

**VERDICT**: ✅ ACCEPT (MVP correct, but plan cash-out policy for Year 2 planning)

---

### CLAIM: "Content ops manageable with template-bound creativity"

**Evidence**:
- Magic Standard (rotates annually, ~1000 cards in format)
- Hearthstone (rotates annually, ~500 cards in format)
- Clash Royale (75 cards total, tight balance)

**Assumptions**:
- [ASSUMPTION] 2-3 people can balance 50-100 deck variants
- [ASSUMPTION] Seasonal rotation every 4 weeks is sustainable
- [ASSUMPTION] Beta audience catches broken combos before public

**Vulnerability**: If balance breaks, competitive players rage-quit. If seasons are boring, churn.

**VERDICT**: ⚠️ CONDITIONAL (need **balance council** structure + public telemetry)

**REQUIRED**: Win rate targets, ban/restrict mechanisms, transparent balance updates.

---

### CLAIM: "Phase gates (Beta → D2C → Amazon → Retail) are realistic"

**Evidence**:
- Gloomhaven (Kickstarter → Gen Con → Amazon → Retail: 8 years)
- Catan (indie → Gen Con → Retail: 5 years)
- Codenames (Czech indie → Retail: 3 years)

**Assumptions**:
- [ASSUMPTION] Press picks up physical + digital hybrid (novel category)
- [ASSUMPTION] Logistics partner handles physical + digital sync
- [ASSUMPTION] Retail buyers take 10k DAU as proof point

**Vulnerability**: Retail requires 6-12M physical inventory. Capital intensive. Partnership-dependent.

**VERDICT**: ⚠️ CONDITIONAL (retail gate requires separate capitalization + distribution partner)

**REQUIRED**: Identify retailer partner by Month 8 (not Month 18).

---

## REJECTED CLAIMS (Beautiful but Cruft)

### ❌ "Will become next Fortnite"
- **Why rejected**: Unprovable. No mechanism. Distraction.
- **Better claim**: "Target 15,000 MAU by Month 12 based on X playtest data."

### ❌ "CHRONOS/MATHFARM as retention multipliers"
- **Why rejected**: Out of scope MVP. Complicates content ops. Adds platform dependency.
- **Better claim**: "Companion tutor launches only after 30% J30 retention proof."

### ❌ "Creator economy self-funds moderation"
- **Why rejected**: Creator economy ≠ community management. Still requires moderation.
- **Better claim**: "Creator tools empower community; studio maintains conduct standards."

---

## MERGED CLAIMS (Combined Insights)

### M-001: Competitive + Creator Economy Tension
**Merged from**: Elo focus claim + Creator studio claim

**Insight**: Leaderboard can't privilege all players equally. Balance:
- **Top 1%**: Competitive Elo (skill-only)
- **Top 10%**: Seasonal tournaments (skill + deck innovation)
- **Top 50%**: Creator showcases (deck design recognition)
- **Bottom 50%**: Achievements (progress, not rank)

**Effect**: All players have "meta" path (not just Elo chasing).

---

### M-002: Retail Logistics + Digital Sync
**Merged from**: Phase gates claim + Closed-loop ECU claim

**Insight**: Physical + Digital version mismatch is a problem.
- **Option A**: One global card pool (synced across regions)
- **Option B**: Regional card variations (local content)

**Decision needed**: Option A (simpler, global appeal) vs. Option B (local flavor).

---

## OPEN QUESTIONS FOR DESIGNER

**Q1**: Duel system — is win condition based on **Territory Control** or **Resource Depletion**?

**Q2**: IA Die — does it have a **theme** (prophecy, chaos, fate) or is it purely mechanical?

**Q3**: Castle progression — does it unlock **gameplay** (new cards, deck slots) or only **cosmetics**?

**Q4**: Creator studio — do template constraints allow for **novel strategies** or just **visual variation**?

**Q5**: Retail phase — is physical + digital one product or two separate SKUs?

---

## VERDICT SUMMARY

| Claim | Status | Risk | Next Action |
|-------|--------|------|-------------|
| Standalone tabletop | ✅ ACCEPT | Low | Detail duel mechanics |
| IA Die mechanism | ✅ ACCEPT | Medium | Prototype + playtest |
| Digital companion retention | ⚠️ CONDITIONAL | Medium | Define castle feature unlocks |
| Creator studio | ⚠️ CONDITIONAL | High | Spec template constraints |
| Competitive focus | ⚠️ CONDITIONAL | High | Design behavior scoring |
| Closed-loop ECU | ✅ ACCEPT | Low | Plan Year 2 monetization |
| Content ops | ⚠️ CONDITIONAL | High | Hire/contract balance council |
| Retail gates | ⚠️ CONDITIONAL | High | Identify logistics partner |

---

## SCORECARD: This Architecture Survives Skepticism?

**Score**: 7/10 ✅ (Solid core, risky execution)

**Strengths**:
- ✅ Tabletop-first prevents tech dependency
- ✅ Precedent strong (D&D, Magic, Chess models)
- ✅ Metrics are testable (retention, DAU, Elo distribution)

**Weaknesses**:
- ⚠️ Creator economy needs upfront spec (not post-launch)
- ⚠️ Competitive focus requires behavior enforcement (hard problem)
- ⚠️ Content ops demands deep game design expertise (expensive hire)
- ⚠️ Retail phase is capital-intensive (needs partner by M8)

**Recommendation**: PROCEED TO SHIP with conditional flags.

---

**SELECT PHASE COMPLETE**

**Next: SHIP** (Specification deck with risk mitigation)

---

**Skeptic**: Claude (ADHD lateral thinking pressure test)
**Owner**: JMT
**Last Updated**: 2026-02-11
**Status**: Ready for SHIP phase
