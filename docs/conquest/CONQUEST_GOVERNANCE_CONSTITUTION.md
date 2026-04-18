# CONQUEST: Governance Constitution
**Formal Rules. Zero Ambiguity. Non-Optional.**

**Version**: 1.0 SHIP
**Date**: 2026-02-11
**Status**: Ready for engineering + operations

---

## PREAMBLE

This constitution codifies how CONQUEST's two systems (Competitive Ladder + Creator Economy) work and remain separate.

**Core principle**: Integrity over growth. Clarity over flexibility.

**Philosophy**: "The system does not decide because it is intelligent. It decides because it is constrained."

---

---

## I. COMPETITIVE LAYER (Elo-Based Ladder)

### I.A. Rating System (Non-Negotiable)

**Foundation**: Modified Glicko-like Elo with variance accounting.

**Definition**:

```
R(t+1) = R(t) + K(σ) × (Actual_Score - Expected_Score)

Where:
  R(t) = player rating at time t
  K(σ) = K-factor adjusted for outcome variance
  σ = estimated volatility (Die roll introduces stochasticity)

K(σ) = Base_K × (1 + Die_Variance_Multiplier)

Where:
  Base_K = 24 (standard Elo K-factor)
  Die_Variance_Multiplier = 0.2 to 0.4 (calibrated per playtest)

Die_Variance_Multiplier reflects:
  - Probability of reroll (Die outcome changed match)
  - Magnitude of reroll impact (HP swing, card swap, etc.)

Calibration rule: If 30%+ of games have outcome changed by Die → higher multiplier.
```

**Rating bounds**:
- Minimum: 400 (newcomer baseline)
- Maximum: 2400 (elite)
- Active floor: Players unranked after 365 days inactivity

**Per-format ratings** (independent):
- `R_1v1` — one-on-one duels
- `R_team` — team battles (if added post-MVP)
- `R_casual` — non-ranked (optional, for learning)

Each format has independent rating pool (no transfer).

---

### I.B. Composite Metrics (Public Display)

**Every player's profile shows 5 metrics** (not just raw R):

| Metric | Formula | Purpose | Manipulation Resistance |
|--------|---------|---------|---|
| **Rating** | `R(t)` (as above) | Skill | K-factor already accounts for volatility |
| **Win Rate** | `W / (W + L)` | Consistency | Capped display (actual may be 72%, show 70% if <30 games) |
| **SoS** | `Avg(Opponent_R)` | Quality of opponents beaten | Transparent; low SoS → lower rating impact |
| **Activity** | `Decay(games_last_30d)` | Recency; prevents "rating locked" | Linear decay (3+ games/week = full; <1 = halved) |
| **Stability** | `1 - (StdDev(R_last_20) / MaxVar)` | Consistency over time | Non-manipulable window; capped 0.0–1.0 |

**Minimum thresholds for display**:
- Activity < 1 game/month → rating grayed out (marked "inactive")
- Win Rate shown only if W + L ≥ 10 games
- SoS calculated only if opponents' games ≥ 100

---

### I.C. Anti-Grind Caps

**Problem**: Toxic behavior (spam low-rank opponents for easy rating gains).

**Solution**:

```
Daily Gain Cap:
  ΔR_daily_max = 20 points/day
  If player earns 20+ → excess rolled to next day (not lost)

Win Streak Bonus Plateau:
  Base: ΔR per game = K × (Actual - Expected)
  Streaks 2–4: +2 bonus points per win
  Streaks 5+: +0 bonus (flat, no acceleration)

Diminishing Returns on Spam:
  If same_opponent_id > 3 matches in 30 days:
    K_factor_reduction = 0.5x for 4th+ match vs same opponent
    (protects from farming specific opponents)
```

**Rationale**: Rewards quality matches, punishes grinding.

---

### I.D. Seasonal Reset (Partial)

**Schedule**: Every 12 weeks (4 seasons/year)

**Formula**:

```
R_new_season = (R_old × 0.75) + Base_Season_Value

Where Base_Season_Value = 1200 (fresh start)

Interpretation:
  - If you ended Season N at R=1600
  - Season N+1 you start at: (1600 × 0.75) + 1200 = 2400 = 1,400
```

**Effect**:
- Prestige preserved (75% carry-over)
- Newcomer window (25% reset allows fresh climbing)
- Seasonal reward (cosmetics for top 10% per season)

**Volatile players (σ > high threshold)**:
  ```
  R_new = (R_old × 0.70) + 1200
  (More reset if inconsistent = fresh window encourages consistency)
  ```

---

### I.E. Behavior Scoring (Anti-Toxic)

**Separate from rating; gating for rewards.**

**Events logged** (server-side immutable):
- Report submitted (player X reports Y for griefing/chat abuse)
- Chat flagged (ML detector + human review)
- Quit mid-game (abandoned match)
- Timeout (AFK >60 sec during turn)

**Behavior Score** (0–100, private):

```
BS = 100 - (Reports_Substantiated × 5) - (Chat_Flags × 3) - (Quits × 2) - (Timeouts × 1)

Floored at 0; capped at 100
Reset seasonal (same as rating reset)
```

**Gates**:
- BS < 70 → cannot queue ranked (still can play casual)
- BS < 50 → 7-day ban from all queues
- BS < 30 → 30-day ban; requires appeal
- Reports_Substantiated > 5/season → seasonal rank stripped

**Appeal process**: Player can contest; manual review by mod team (72-hour response).

---

---

## II. CREATIVE LAYER (Creator Impact Score)

### II.A. Creative Impact Score (CIS)

**Purpose**: Measure how much a creator's work drives engagement (independent of Elo).

**Not tied to rating. Never pollutes ladder.**

**Formula** (weekly batch recalculation):

```
CIS = (Replay_Rate × 0.30)
    + (Retention_Delta × 0.25)
    + (Qualified_Vote × 0.30)
    + (Guild_Adoption × 0.15)

Scaled 0–100
```

**Components**:

---

#### II.A.1. Replay Rate (0.30 weight)

**Definition**: Percentage of players who replay a creator's module >1x.

```
Replay_Rate = (Sessions_Replayed) / (Total_Sessions_Launched)

Capped at 0.60 (avoid outliers skewing score)
Minimum: 20 sessions required (else not calculated)
```

**Anti-gaming**:
- Session < 2 min → doesn't count ("farming" detection)
- Same player replays same session 5x → flagged (human review, likely farming)

---

#### II.A.2. Retention Delta (0.25 weight)

**Definition**: Does playing this module increase player retention?

```
Retention_Delta = (Cohort_Retention_on_Module - Baseline_Retention) / Baseline

Where:
  Cohort = players who played this module at least once
  Cohort_Retention = % active 7 days later
  Baseline_Retention = % of all players active 7 days later

If Retention_Delta < 0 → scored as 0 (no penalty, but no credit)
Capped at +0.5 (avoid single-outlier modules skewing)
```

**Why this works**: Measures if module actually engages players (not just played once).

---

#### II.A.3. Qualified Vote (0.30 weight)

**Definition**: Community perception, weighted by voter credibility.

```
Qualified_Vote_Score = Sum(vote_direction × vote_weight) / Sum(vote_weight)

Scaled 0–100

Where:
  vote_direction = +1 (upvote) or -1 (downvote)

  vote_weight = Voter_Elo_Factor × Voter_Tenure_Factor × Voter_Accuracy_Factor

  Voter_Elo_Factor = min(voter_R / 1600, 1.0)  [max 1.0x at R=1600+]
  Voter_Tenure_Factor = min(voter_tenure_months / 12, 1.0)  [max 1.0x after 1 year]
  Voter_Accuracy_Factor = % of voter's votes that aligned with eventual modal vote ± 20%
                           [0.1x if unreliable, 1.0x if accurate]

Max vote_weight: 1.0x (high-rated, long tenure, accurate)
Min vote_weight: 0.1x (low-rated, new, inaccurate)
```

**Minimum votes required**: 30 qualified votes (else not calculated).

**Anti-gaming**:
- Votes from same IP address within 1 hour → flagged (bot detection)
- Voter accuracy < 40% → weight capped at 0.15x (unreliable voter)
- Vote spam (>20 votes/day on same module) → votes weighted at 0.05x (suspicious)

---

#### II.A.4. Guild Adoption Depth (0.15 weight)

**Definition**: How deeply guilds integrate this module into their play.

```
Guild_Adoption = (Guilds_Using / Active_Guilds) × (Avg_Guild_Playtime_Module / Avg_Guild_Playtime_All)

Where:
  Guilds_Using = # of guilds that played module ≥1x
  Active_Guilds = guilds with ≥1 duel in last 30 days
  Avg_Guild_Playtime_Module = avg duel duration on this module (per guild)
  Avg_Guild_Playtime_All = avg duel duration across all modules (per guild)

Capped at 1.0 (avoid single-guild outliers)
Minimum: ≥1 guild adoption required (else not calculated)
```

**Why this works**: Guilds vote with their time. Deep adoption = real signal.

---

### II.B. Tier Progression (Automated Gates)

**Modules progress through tiers based on data, not opinion.**

| Tier | Entry Gate | Requirements | Automation | Visibility | Revenue Eligible |
|------|-----------|---|---|---|---|
| **1. Draft** | Creator publishes | None | Auto (5 min) | Private (creator + guild invite) | ❌ |
| **2. Community Tested** | 50+ verified sessions | 50+ unique players, 10+ distinct players | Auto (weekly check) | Search visible, low ranking | ❌ |
| **3. Guild Approved** | Guild adoption + votes | 1+ guild + 30+ qualified votes | Auto (weekly check) | Guild library featured | ❌ |
| **4. Community Featured** | CIS threshold + votes | CIS ≥ 65th %ile + 60%+ qualified vote | Auto (weekly check) | Public featured section | ❌ |
| **5. Official Candidate** | Manual balance audit | CIS ≥ 85th %ile + zero exploits + 200+ sessions + zero bans | **Manual (24h)** | Seasonal labs (testing) | ✅ (if Phase 1 active) |

**Progression is one-way forward** (can't demote tiers, but can be removed entirely if exploit found).

---

### II.C. Anti-Fraud Checks (Automated)

**Run every module calculation (weekly)**:

```
Session Verification:
  IF session_duration < 2 min → exclude (too short)
  IF session_duration > 60 min → flag (anomaly, check if real)
  IF same_player_id replays same session > 5x in 24h → flag (farming)
  IF session_win_rate of creator's module > 85% → flag (balance check)

Voter Verification:
  IF voter_accuracy_history < 40% → weight vote at 0.1x (unreliable)
  IF votes_same_day > 20 on same module → weight at 0.05x (spam)
  IF votes_same_IP within 1h > 3 → flag (bot detection, manual review)

Guild Adoption Verification:
  IF guild_adoption_spike > 3σ in 24h → flag (possible collusion, manual review)
  IF guild members all vote same direction (100%) → flag (coordinated, reduced weight)
```

**Manual review triggers** (human checks):
- Module with 85%+ win rate (balance)
- Vote spike >3σ (collusion)
- Bot detection (same IP, rapid votes)

**Owner**: Content Ops team (balance designer + 1 moderator).

---

---

## III. THE BRIDGE: From Creator to Official

### III.A. Bridge Criteria (Non-Negotiable)

**A module becomes "Official Candidate" (Tier 5) ONLY if ALL pass**:

1. ✅ **CIS ≥ 85th percentile** (top 15% of all creators)
2. ✅ **60%+ qualified vote positive** (not just majority; credible majority)
3. ✅ **Zero balance exploits detected** (automated + manual audit)
4. ✅ **200+ verified sessions minimum** (from 50+ distinct players)
5. ✅ **Zero creator bans** (no toxic behavior from creator)
6. ✅ **Zero module bans** (no previous removal for exploit)

**All criteria checked weekly; module promoted automatically once threshold met.**

---

### III.B. Seasonal Labs (Official Testing)

**What it is**: Official testing lane where Tier 5 modules are evaluated.

**Duration**: 2-week window (announced in-game).

**Mechanics**:
- Module plays in ranked, tracked separately
- Full telemetry visible to balance team
- Community feedback encouraged (separate vote)

**Outcome**:
- If balance OK + ≥70% community feedback positive → goes to "Official Pack" next season
- If balance broken → module withdrawn, creator gets feedback, can resubmit after fixes

**Timeline**:
```
Tier 5 (Candidate) → Seasonal Labs (Week 1-2 of new season)
  → Balance review (Weeks 2-3)
  → Decision (Week 4) → Official Pack or Reverted
```

---

### III.C. Official Pack (Revenue Eligible, Phase 1+)

**Only after MVP proves 15K MAU + zero balance exploits.**

**What it is**: Module published by studio, cosmetics tied to it.

**Creator gets**: 30% revenue share on cosmetics sales (monthly).

**Studio keeps**: 70% (ops, balance, support).

**Contract**:
- 12-month term, auto-renew unless either party opts out
- Creator must maintain module (fix balance issues if flagged)
- Creator must follow conduct rules (no toxicity)
- If creator bans → revenue stops immediately (no refunds)
- If module exploited → studio can ban; creator's revenue on that module stops

**Payment**: Monthly via Stripe, minimum $50 threshold (batches under $50 to next month).

---

---

## IV. SEPARATION OF CONCERNS (Walls Between Systems)

### IV.A. Ladder Cannot Be Polluted by Creative Content

**Rule**: Creator modules grant ZERO Elo directly.

```
Player plays Creator Module A, wins → gains standard Elo (calculated via normal formula)
NOT: "Wins on Module A = +1.5x Elo" (no multiplier)

Exception: Seasonal "tournament modules" may grant cosmetics, but NOT rating multipliers.
```

**Enforcement**: Elo calculation audited quarterly (check for hidden multipliers).

---

### IV.B. Creator Economy Cannot Become Pay-to-Win

**Rule**: Official Packs have zero gameplay advantage.

```
Module features are balanced (same K-factor as non-official modules).
Creator cosmetics never grant stat bonuses or card advantages.
```

**Enforcement**: All Official Packs pass balance gate before release.

---

### IV.C. Behavior Scoring Cannot Affect Creator Score

**Rule**: Behavior BS is ladder-only; does not affect CIS.

```
If creator has BS < 70 → blocked from ranked queue
But: CIS continues to accumulate (creator can still design great modules)
```

**Rationale**: Separates conduct issues from creative quality.

---

---

## V. PHASING (Monetization)

### V.A. Phase 0 (MVP, Months 0-6): Reputation Only

**In MVP**:
- ✅ Competitive ladder (Elo + SoS + Stability)
- ✅ Behavior scoring
- ✅ Creator tiers (Draft → Community Featured)
- ✅ Qualified voting
- ✅ CIS calculation (for data)
- ❌ NO revenue share
- ❌ NO Official Packs

**Creators get**:
- Tier badges + visibility
- Leaderboard position (CIS ranking)
- Adoption stats (guilds using module)

**Goal**: Prove reputation model works. Learn balance. Build data.

---

### V.B. Phase 1 (Month 6+): Creator Program Closed

**Gate**: 15K MAU + zero balance exploits in MVP

**Unlock**:
- ✅ Official Packs (Tier 5 modules)
- ✅ Revenue share (30% to creator)
- ✅ Creator Pro Tools (advanced design, analytics)

**Creators selected** (closed program):
- Top 50 creators by CIS
- Invitation-only (studio controls quality)
- Contract + verification

**Revenue split**: 30% creator, 70% studio.

**Duration**: 12-month terms, renewable.

---

### V.C. Phase 2 (Year 2+): Marketplace (Optional)

**Gate**: Creator Program stable + anti-fraud hardened

**Unlock** (only if both gates met):
- Open marketplace (creators can publish without invite)
- Revenue share stays 30/70 (or adjust per negotiation)

**If gates NOT met**: Stay curated (safer, simpler).

---

---

## VI. DECISION AUTHORITY

### VI.A. Who Decides What

| Domain | Authority | Process | Appeal |
|--------|-----------|---------|--------|
| **Tier progression** | Automated rules + weekly batch | Data-driven, no opinion | NA (rules-based) |
| **Balance** | Balance designer (game design) | Playtest + telemetry | Director of game design |
| **Conduct** | Moderation team | Reports + review | Player can contest (72h) |
| **Creator contracts** | Studio legal + product | Negotiation | Arbitration clause in contract |
| **Official Pack removal** | Product + balance team | Exploit confirmation | Director of product |

**No committee. No consensus. One owner per domain.**

---

### VI.B. Disputes

**Creator contests balance decision?**
- Escalate to Director of Game Design
- 5-day review window
- Decision final

**Player contests behavior ban?**
- Escalate to Moderation Lead
- 72-hour review window
- Decision final

**No appeals process beyond this.** Finality prevents endless litigation.

---

---

## VII. METRICS & ACCOUNTABILITY

### VII.A. Public Dashboards (Transparency)

**Studio publishes weekly**:
- Total modules by tier (breakdown)
- Top 20 creators by CIS (with scores)
- Elo distribution (median, 50th, 95th percentile)
- Behavior incident rate (reports/1000 players)
- Balance status (modules flagged for exploit, % resolved)

**Goal**: Community sees system is fair, not gamed.

---

### VII.B. Audit Log (Immutable)

**All state changes logged** (server-side, immutable):
- Module promoted to tier X (timestamp, criteria met)
- Creator banned (reason, appeal resolution)
- Balance change (reroll window adjusted, reason)
- Revenue payout (creator, amount, invoice)

**Accessed by**: Studio audit team (monthly), external auditor (yearly for financials).

---

---

## VIII. EXCEPTIONS & EDGE CASES

### VIII.A. What Happens If Creator Becomes Toxic?

```
Step 1: Behavior reports flagged
Step 2: BS < 70 → ranked queue blocked
Step 3: Continues if BS < 30 → 30-day ban
Step 4: If ban sustained → Creator Program contract terminated

Result:
  - Rating stays (historical)
  - Modules revert to "Community Featured" (delisted from Official)
  - Revenue stops immediately
  - Modules can be rehabilitated if creator appeals + reforms
```

---

### VIII.B. What Happens If Module Has Game-Breaking Exploit?

```
Step 1: Auto-flag detected (win rate > 90% OR balance test fails)
Step 2: Manual audit by balance designer (48h)
Step 3: If confirmed → Module moved to "Disabled" tier (hidden from search, grayed out)
Step 4: Creator notified, given feedback + 2-week window to fix
Step 5: Creator resubmits fix; re-audited; if OK → re-enabled

Revenue:
  - Stops on exploit day (capped payout)
  - Resumes on re-enable (if re-enabled)
  - Creator does not receive refund for disabled period
```

---

### VIII.C. What If Creator Wants to Quit?

```
Tier 5 (Official Candidate):
  - Can withdraw module (become private/deleted)
  - Data archived (stats preserved for analytics)

Phase 1 (Official Pack + revenue):
  - Creator can end contract (30-day notice)
  - Final revenue paid next month
  - Module can be delisted or transferred (studio decides)
```

---

---

## IX. TIMELINE (Implementation)

### Before Alpha (Week 1):
- [ ] Finalize Elo formula (K-factor for Die variance)
- [ ] Finalize Stability Index calculation (non-manipulable)
- [ ] Finalize CIS formula (with anti-fraud checks)
- [ ] Code session verification (bot detection)
- [ ] Code voter credibility weighting

### Before Beta (Month 4):
- [ ] Tier progression automated (Tiers 1-4)
- [ ] Balance detection (automated win-rate flags)
- [ ] Behavior scoring (reports, timeouts, quits)
- [ ] Manual audit process (Tier 5 gate)

### Month 6 (Phase 1 Gate):
- [ ] Verify 15K MAU proof
- [ ] Verify zero exploits in wild
- [ ] If both ✅ → Creator Program opens
- [ ] If either ❌ → stay in Phase 0 (reputation only)

---

---

## X. GOVERNANCE IMMUTABILITY

**This constitution is locked** until:
- Studio decision to change (documented, versioned)
- Community vote (if governance evolves)

**NO silent changes. All edits logged + announced.**

**Changes require**:
- Version bump (1.0 → 1.1)
- Changelog (what changed, why)
- 2-week notice to community
- Player feedback window (optional)

---

---

## FINAL AUTHORITY

This constitution is the source of truth.

**If engineering asks "What should happen in case X?"** → Answer is here.

**If disputes arise** → Resolve via authority matrix (Section VI.A).

**If ambiguity found** → Escalate to Director of Game Design (final call).

---

**Constitution Owner**: JMT (Design + Product)
**Version**: 1.0 SHIP
**Date**: 2026-02-11
**Status**: APPROVED FOR ENGINEERING

**Next step**: Integrate into CONQUEST_SPECIFICATION_MVP.md + reference from all other docs.
