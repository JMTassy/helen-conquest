# CONQUEST: Double Scoring Model
**Competitive + Creative (Integrated)**

**Version**: 1.0 EXPAND
**Date**: 2026-02-11
**Status**: Raw synthesis, architecture critical

---

## PREMISE

The scoring model is the **load-bearing wall**. If it collapses, everything collapses.

If it's weak:
- Semi-competitive becomes chaotic
- Creator economy becomes polluted
- Gaming group doesn't trust the system

If it's strong:
- Elo credible
- Creator paths clear
- Data-driven iterations possible
- Retention multiplies

---

## ARCHITECTURE: TWO INDEPENDENT SCORES

### Score 1: COMPETITIVE (Official Ladder)
Purpose: **Integrity, comparability, e-sport compatible**

### Score 2: CREATIVE (Impact Metric)
Purpose: **Valorize creators, measure quality, never pollute ladder**

**Bridge**: One module can become "Official" only via gated governance.

---

---

## I. COMPETITIVE SCORE (Official Ladder)

### 1A. Foundation: Modified Elo

**Each player has**:
- `R_global` — lifetime rating (public)
- `R_season` — current season rating
- `R_format` — per-format variant (1v1, teams, etc.)

**Standard Elo formula**, adjusted for:
- Variability of IA Die (higher K-factor for high-variance matches)
- Format differences (1v1 vs. team scaling)
- Experience gap (newcomer bonus)

**Why Elo**: Proven, transparent, understood by gaming communities.

**Why Modified**: IA Die adds controlled randomness; pure Elo doesn't account for "outcome variance."

---

### 1B. Anti-Grind Multiplicators

**Problem**: Toxic grind (spam low-rank opponents for easy wins).

**Solution**:
- Daily gain cap: Max +20 rating/day (prevents grinding)
- Win streak bonus plateau: 5+ consecutive wins = max bonus, then flat
- Diminishing returns on spam: Playing same opponent >3x/season = reduced K-factor

**Effect**: Players optimize for quality matches, not volume spam.

---

### 1C. Composite Rating Metrics

**Don't just publish raw R. Publish 5 metrics**:

| Metric | Definition | Why |
|--------|-----------|-----|
| **R_competitive** | Core Elo rating | Direct skill measure |
| **Win Rate** | Wins / (Wins + Losses) | Consistency signal |
| **SoS (Strength of Schedule)** | Avg opponent rating faced | Did you beat weak or strong players? |
| **Activity Score** | Decay-weighted game frequency | Prevents "rating locked" players ranking high |
| **Stability Index** | Variance of last 20 games | Did you play consistently or on a hot streak? |

**Public Display**:
```
Player: JMT
├─ Rating: 1650
├─ Win Rate: 56%
├─ Strength of Schedule: 1620
├─ Activity: High (12 games this week)
└─ Stability: Stable (+/- 30 rating variance)
```

**Effect**: Transparent, multi-dimensional, harder to game.

---

### 1D. Seasonal Reset (Partial, Not Wipe)

**Problem**: Locked ladder (good players always on top, newcomers discouraged).

**Solution**: Partial reset using formula:

```
R_new_season = (R_old × 0.75) + BaseSeasonValue

Where BaseSeasonValue = 1200 (fresh start point)
```

**Interpretation**: Keep 75% of previous prestige, reset 25%.

**Effect**:
- Seasons matter (not locked forever)
- Prestige preserved (not erased)
- Newcomers get fresh window (but face calibrated opponents)

---

---

## II. CREATIVE SCORE (Impact Metric)

**Separate from competitive ladder. Never pollutes Elo.**

### 2A. Creative Impact Score (CIS)

**Measures**: How much does a creator's work get **played, replayed, and valued**?

**Formula** (weighted combination):

```
CIS = (Replay Rate × Weight_replay)
    + (Retention Delta × Weight_retention)
    + (Qualified Vote Score × Weight_votes)
    + (Guild Adoption Depth × Weight_adoption)

Where weights sum to 1.0
```

**Components**:

| Component | Measurement | Weight | Why |
|-----------|-------------|--------|-----|
| **Replay Rate** | (Sessions replayed) / (Total sessions started) | 0.30 | Indicates replayability |
| **Retention Delta** | Cohort retention on creator content vs. baseline | 0.25 | Indicates engagement impact |
| **Qualified Vote Score** | Weighted votes (see 2B) | 0.30 | Indicates perceived quality |
| **Guild Adoption** | Guilds that adopt creator's module | 0.15 | Indicates community trust |

---

### 2B. Qualified Vote (Anti-Populism)

**Problem**: Open voting = mob rule. Bad creators get boosted by friends.

**Solution**: Weight each vote by voter credibility.

**Vote Weight Formula**:

```
Vote_weight = (Voter_Elo_multiplier)
            × (Voter_Tenure_multiplier)
            × (Voter_Accuracy_History)

Max vote power: 1.0x (high-rated, long tenure, accurate)
Min vote power: 0.2x (low-rated, new, inaccurate history)
```

**Interpretation**:
- A professional game designer's vote (R: 1800, tenure: 2 years, 85% accuracy) = 1.0x weight
- A newcomer's vote (R: 1200, tenure: 1 month, no history) = 0.3x weight
- A known troll's vote (low accuracy) = 0.1x weight

**Effect**: Quality reviews from credible sources matter more.

---

### 2C. Creative Tiers (Progression Path)

**Each creator's module progresses through gates**:

| Tier | Entry Gate | Visibility | Badge |
|------|-----------|-----------|-------|
| **1. Draft** | Creator publishes | Private (creator + guild) | None |
| **2. Community Tested** | 50+ public sessions | Search visible, low ranking | 🔵 Blue |
| **3. Guild Approved** | Adopted by 1+ guild + positive votes | Guild library featured | 🟣 Purple |
| **4. Community Featured** | CIS > threshold + 60%+ qualified votes | Public featured section | 🟡 Gold |
| **5. Official Candidate** | CIS max + zero exploits detected | Seasonal testing lane | 🔴 Red (Elite) |

**Progression is not automatic.** Each tier gate requires specific proof:
1. Usage data (50+ players)
2. Quality votes (60% positive from credible voters)
3. Balance verification (no exploit detection)
4. Adoption proof (guilds using it consistently)

---

---

## III. THE BRIDGE: Becoming "Official"

**Strategic question**: When does a creator module become **Official Pack** (published by studio, eligible for revenue share)?

### 3A. Gate Criteria

A module can become "Seasonal Labs" (official testing) if:

1. ✅ **CIS exceeds minimum threshold** (e.g., CIS > 75th percentile)
2. ✅ **60%+ qualified vote is positive** (not just majority, credible majority)
3. ✅ **Zero balance exploits detected** (automated + manual audit)
4. ✅ **Minimum verified play sessions** (e.g., 500+ sessions from diverse players)

### 3B. Testing Path

```
Creator Module
    ↓
Community Tested (Tier 2)
    ↓
Guild Approved (Tier 3)
    ↓
Community Featured (Tier 4)
    ↓ [IF meets bridge criteria]
Seasonal Labs (Official Testing)
    ↓ [IF no balance issues in live]
Official Pack (Revenue Share)
```

---

---

## IV. DOUBLE PLAYER PROFILE

**Each player has TWO distinct profiles**:

### Profile A: Competitive
```
Player: JMT
├─ Rating: 1650
├─ Wins: 245
├─ Losses: 189
├─ Achievements: [Undefeated Streak, Guild Champion, ...]
├─ Ladder Rank: #127 (Global)
└─ Seasonal Prestige: Gold (2024 S1)
```

### Profile B: Creative
```
Creator: JMT
├─ Modules Published: 3
├─ Creative Impact Score: 82
├─ Top Module: "Blaze Deck" (Tier 4, 340 sessions, 71% replay)
├─ Revenue (Month): $240 (creator share)
└─ Adoption: Featured in 12 guilds
```

**Key insight**: A player can have:
- High rating, low CIS (competitive player, not creator)
- Low rating, high CIS (creative player, not competitive)
- High + High (full player, rare, valued)

**Effect**: Creates multiple statuses, multiple incentive paths.

---

---

## V. WHY THIS WORKS FOR GAMING GROUPS

Gaming communities evaluate products on:

| Criterion | CONQUEST Proof |
|-----------|---|
| **Elo integrity** | Modified Elo + SoS + Stability Index = transparent, gameable-resistant |
| **Creator viability** | CIS + qualified votes + revenue share = professional creators attract |
| **Governance credibility** | Bridge gates prevent chaos, automated checks prevent exploits |
| **Behavioral data** | Replay rate, retention delta, adoption depth = rich telemetry for iterations |
| **Monetization path** | Dual economy (competitive battle pass + creative revenue share) = sustainable |

**Conclusion**: "This isn't a gimmick. This is a real system."

---

---

## VI. MONETIZATION TIED TO SCORING

### Competitive Revenue
- **Seasonal Battle Pass**: Cosmetics + ranked rewards (Elo-based)
- **Tournaments**: Premium bracket with Elo gate (e.g., R > 1400 only)
- **Seasonal Prestige**: Cosmetics for top 10% (by Elo + activity)

**Price**: $9.99/month or $24.99/season.

### Creative Revenue
- **Creator Pro Tools**: Advanced module design tools, analytics ($4.99/month)
- **Revenue Share on Official Packs**: Creator earns 30% of cosmetic sales tied to their module
- **Visibility Boost**: Paid promotion in creator library ($2.99/boost, 4-week feature)

**Price Model**: Hybrid (subscription + transaction).

---

---

## VII. RISK GUARDRAILS

**What to NEVER allow**:

| Risk | Guard |
|------|-------|
| **Creative pollutes ladder** | CIS is orthogonal; no Elo gained for creating |
| **Vote manipulation** | Weighted voting prevents bots/astroturfing |
| **Infinite score inflation** | Daily caps, seasonal resets, decay-weighted activity |
| **Algorithm gaming** | Qualified voters + exploit detection + guild adoption (human verification) |
| **Creator pay-to-win** | Official packs must pass balance gate |
| **Toxic competitive** | Behavior score gating (report system, bans, rating loss for griefing) |

---

---

## VIII. INVESTOR SUMMARY (1-Sentence)

> **CONQUEST combines a transparent, multi-metric Elo ladder with a gated creator economy, ensuring competitive integrity while enabling infinite content expansion through qualified community governance.**

---

---

## IX. CRITICAL DECISION: Creator Monetization Model

**The Strategic Question**:

### Option A: Revenue Share (Hybrid)
Creators earn direct money from their modules being adopted.
- **Pros**: Incentivizes quality creators, builds professional scene
- **Cons**: Potential pay-to-win pressure, economic complexity
- **Sustainability**: Only for Tier 4+ (Official Candidate) modules

### Option B: Purely Reputational (Status Only)
Creators earn cosmetics, badges, visibility, no direct revenue.
- **Pros**: Simpler economy, no fraud risk, no pay-to-win
- **Cons**: Doesn't attract professional designers, UGC may be amateur
- **Sustainability**: Works for niche communities, not mainstream gaming

### Option C: Hybrid Controlled (Recommended)
- Creators earn visibility + cosmetics in MVP
- Revenue share enabled **only after** 15K MAU + balance proof
- Strict governance (bridge gates must pass before revenue eligible)

**JMT Decision Required**: A, B, or C?

---

---

## X. DATA ARCHITECTURE (For Product Team)

**Events to log** (for CIS calculation):

```
session_created
├─ creator_id
├─ module_id
├─ player_id
├─ start_time
└─ end_time

session_replayed
├─ creator_id
├─ module_id
├─ original_session_id
├─ replay_time

vote_submitted
├─ voter_id
├─ voter_rating
├─ voter_tenure
├─ voter_accuracy_history
├─ module_id
├─ vote_direction (up / down)
└─ weighted_vote_power

module_adopted_guild
├─ creator_id
├─ module_id
├─ guild_id
├─ adoption_date
└─ guild_size
```

**CIS recalculated** weekly (not real-time) to prevent gaming.

---

---

## NEXT STEPS

### For Designer:
1. **Validate** Elo formula (modified for IA Die variance)
2. **Define** SoS + Stability Index calculations precisely
3. **Spec** seasonal reset calendar (when do resets happen?)

### For Product:
1. **Decide** creator monetization (A, B, or C?)
2. **Spec** voting UI (how do players vote on creator modules?)
3. **Plan** automated balance detection (how do we catch exploits?)

### For Engineering:
1. **DB schema** for dual scoring (competitive + creative)
2. **API contracts** for Elo updates, CIS calculations, vote weighting
3. **Telemetry** infrastructure for replay rate, retention delta, adoption depth

---

---

## VALIDATION QUESTIONS (Skeptic Pressure)

**Q1**: Is modified Elo + SoS sufficient to prevent smurfing?
**Q2**: Can qualified voting avoid vote manipulation?
**Q3**: Does CIS avoid incentivizing bad creators?
**Q4**: Can bridge gates be automated, or do they require manual review?
**Q5**: What happens if creator module gets exploited after going Official?

---

**EXPANSION PHASE COMPLETE (Scoring Model)**

**Next**: SELECT phase (Skeptic tests this model)

Then: SHIP phase (Integrate into CONQUEST_SPECIFICATION_MVP.md)

---

**Owner**: JMT
**Last Updated**: 2026-02-11 (EXPAND captured)
**Status**: Ready for SELECT review

**Decision Gate**: Monetization model (A, B, C)?
