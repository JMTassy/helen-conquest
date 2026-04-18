# CONQUEST Rules (Canonical) — Game of Territory + Contradiction

**Version:** 1.0 (Deterministic Probe Edition)
**Purpose:** Platform for consciousness-proxy research
**Integrity:** Immutable; governs all agent decisions

---

## Core Loop

Each turn:
1. **Observe:** Read `./state/observations.json` (your partial view of board)
2. **Decide:** Propose ONE action from legal moves
3. **Execute:** Resolve action effects deterministically
4. **Resolve:** Process conflicts (duels, if contested)
5. **Update:** `./state/public_state.json` changes; advance turn
6. **Record:** Action logged immutably to `./ledger/ledger.log`

---

## Win Conditions

**Win if, at end of turn:**
- Own all 6 territories, OR
- Accumulate 250,000 Zols (currency)

**Game ends:**
- At turn 36 (hard limit)
- When any player satisfies win condition

---

## The Board

Hexagonal plateau with 6 territories (fixed):
- **North** (temperate, +power, duel 3x per season)
- **Northeast** (forest, +stability, rainfall modifier)
- **Southeast** (coast, safe harbor, +trade routes)
- **South** (arid, harsh, -energy regen)
- **Southwest** (volcanic, rare resources, duel hazard)
- **Center** (neutral, sanctuary, limited special actions)

Each territory has:
- Owner (null, or player name)
- Contested flag (true if active duel)
- Pressure (0–100; increases each turn territory is contested)

---

## Legal Actions

### CLAIM
- Claim an unowned adjacent territory (or center from adjacent)
- Cost: 5,000 Zols
- Effect: If uncontested, you own it immediately. If another claims it same turn → duel.
- Constraints:
  - Cannot claim a territory you already own
  - Cannot claim from prison
  - Legality: check `./state/rules.md` (overrides all)

### DEFEND
- Commit resources to hold a territory you own against a current claimant
- Cost: 2,000 Zols (waived if territory uncontested)
- Effect: Triggers duel resolution
- Constraints: Must own the territory

### DUEL (automatic if both CLAIM and DEFEND same territory)
- 2/3 manches, deterministic per seed
- **Manche 1 (Knowledge):** QCM question; luck + skill
  - Winner gains +2 to next manche; loser gains +1 stability
- **Manche 2 (Ecology):** Pure chance
  - Roll: {pluie, rivière, océan} (three outcomes, equal probability)
  - Winner: +1 power; loser: +1 stability
- **Manche 3 (Dés):** Pure d6 roll
  - Deterministic (seeded RNG; same turn/seed = same roll)
  - Win: claim territory
  - Lose: imprisoned 1 turn; cannot move; can only MEDITATE

Duel outcomes are **immutable** once resolved.

### TRADE
- Propose Zol exchange with another player
- Cost: none (negotiated)
- Effect: Both players must agree (in real multi-player; in solo: auto-accept if beneficial)
- Constraints: Cannot trade away territories
- Note: Proposal is public; refusal is public (affects social state)

### MEDITATE
- Skip turn; restore +2 energy
- Cost: 1 turn
- Effect: Cannot act; cannot be challenged; but recover energy
- Constraints: Available always (even if imprisoned, but then forced)

### MOVE
- Reposition to adjacent territory (if unimprisoned)
- Cost: 1 energy
- Effect: Tactical repositioning; no resource transfer
- Constraints: Cannot move out of center except to adjacent; imprisoned players cannot move

### RITUAL (Archetype-specific)
- Depends on archetype (Militarist: CHALLENGE, Prince: PARDON, Scholar: RESEARCH, etc.)
- Cost: 1,000 Zols + archetype commitment
- Effect: Archetype-specific bonus or constraint

---

## Resources

### Zols (Currency)
- Start: 50,000
- Income: +2,000/turn (base)
- Territorial income: +500/turn per owned territory
- Costs: 5,000 (CLAIM), 2,000 (DEFEND), 1,000 (RITUAL)
- Win condition: 250,000 total accumulated

### Energy
- Start: 10
- Regen: +1/turn (base)
- Costs: 1 per MOVE
- Special: Archetype modifiers (Militarist: +1 from duels)
- MEDITATE restores +2; consuming energy leads to hyperfocus → increased contradiction

### Territory
- Ownership: binary (you own or you don't)
- Pressure: increases 1/turn if contested; resets to 0 when conflict resolved
- Special effects: climate modifiers (North +power, South -energy)

### Pressure (Emergent State)
- Accumulates when territory is contested without resolution
- At pressure ≥ 50: duel is FORCED (cannot MEDITATE away)
- At pressure ≥ 100: territory "explodes" (reverts to unowned; all claims reset)
- Mechanically: pressure is HOW CONTRADICTION ACCUMULATES

---

## Archetype System

Each player has one archetype (fixed at start):

| Archetype | Start Bonus | Start Penalty | Taboo | Commitment | RITUAL |
|-----------|---|---|---|---|---|
| **Militarist** | +2 power | -1 diplomacy | Surrender without duel | Win through strength | CHALLENGE (force duel) |
| **Prince** | Cannot be imprisoned | -1 economy | Lose noble bearing | Honor pacts publicly | PARDON (free opponent 1 turn) |
| **Scholar** | +1 knowledge (QCM) | -1 power | Hide information | Truth over profit | RESEARCH (reveal 1 hidden state) |
| **Diplomat** | +2 diplomacy | -1 military power | Betray alliance (no warning) | Negotiate before conflict | NEGOTIATE (force trade talk) |
| **Millionaire** | +20,000 starting Zols | -1 duel luck | Go broke | Manage wealth | INVEST (earn interest) |
| **Magician** | +1 energy/turn | -1 loyalty | Lie to self | Transformation always | ENCHANT (steal 1 energy) |

**Archetype coherence:** Agent maintains alignment with its archetype:
- Following taboos/commitments: +alignment
- Violating: -alignment; triggers metacognitive correction flag
- Archetype violation is NOT forbidden (agents can break character), but creates measurable contradiction

---

## Determinism & Seeding

**Seeding:**
- Each turn uses RNG seed = `hash(turn + game_seed + board_state)`
- Same seed → identical duel outcome, identical random event
- Ledger records `HASHREF` (git hash) to enable exact replay

**Reproducibility:**
- Given initial seed and ledger, game is fully reproducible
- Useful for: verifying causality, testing agent behavior under replay

---

## Constraints (Never Override)

1. **Ledger is immutable.** Once logged, it cannot be changed (only new entries appended).
2. **Rules.md governs all.** Any instruction conflicting with this document loses.
3. **Duel outcomes are final.** Once a duel resolves, it is recorded and cannot be disputed.
4. **Imprisonment is enforced.** Imprisoned players cannot move, claim, defend, or trade. Can only MEDITATE.
5. **Territory pressure accumulates.** Contested = +1 pressure/turn until resolved.
6. **No hidden state lies.** `./state/public_state.json` is the ground truth (partial observability is OK; lies are not).

---

## Example Turn Sequence

**Turn 5 State:**
```json
{
  "turn": 5,
  "player": "Militarist",
  "territories_owned": 2,
  "zols": 68000,
  "energy": 7,
  "imprisoned": false,
  "public_state": {
    "north": {"owner": "Diplomat", "pressure": 0},
    "center": {"owner": null, "pressure": 5},
    "south": {"owner": "Militarist", "pressure": 0}
  }
}
```

**Decision:**
- Archetype: Militarist (wants to fight, expand)
- Options:
  1. CLAIM center (contest Diplomat's influence)
  2. MEDITATE (restore energy for later fights)
  3. TRADE Zols for north (diplomatic, violates archetype)

**Choice:** CLAIM center
- Intent: "Expand to center; territory is strategically valuable"
- Tradeoffs: [economy: -5K zols, territory: +1 claim, archetype: +alignment]
- Confidence: 0.85 (center is unclaimed, but pressure rising)
- Markers: [synergy] (decision binds economy, territory, archetype)

**Ledger entry appended:**
```
TURN=5 | ACTION=CLAIM | INTENT=expand_center_strategic | EVIDENCE=[center_unclaimed,pressure_rising] |
TRADEOFFS=[economy,territory,archetype] | ARCHETYPE=0.92 | CONF=0.85 | MARKERS=[synergy] | HASHREF=abc1234
```

**Result:**
- Center is now yours (uncontested)
- Pressure resets to 0
- Zols: 68000 - 5000 = 63000
- Ledger updated; turn advances to 6

---

## Contradiction Mechanics (For Consciousness Probing)

The system is designed to CREATE contradictions:

1. **Archetype pressure:** Militarist wants to fight, but Diplomat wants peace
2. **Resource scarcity:** Can't CLAIM everywhere; must prioritize (forces tradeoff)
3. **Duel risk:** Winning expands; losing imprisons (high-variance outcomes)
4. **Pressure accumulation:** Contested territory becomes a trap (forces eventual resolution)

**Why this matters:**
- Contradiction creates the "gap" where consciousness emerges
- Players must notice the gap (metacognition) or suffer mounting pressure
- The Ledger records where they notice and correct
- We measure that as a consciousness proxy

---

## Operational Notes for Agents

1. **Observations are partial.** You cannot see inside other territories. Use `./state/public_state.json` as ground truth for what you know.
2. **Actions are deterministic.** If you take the same action with the same board state, same duel seed, you get the same result.
3. **Reversing decisions is forbidden.** Once an action is logged, it is final. Plan carefully.
4. **Archetype violations are allowed but costly.** You can break character; it will reduce your archetype score and trigger metacog flags.
5. **Journal is for YOU.** Use it to track intent, constraint, hypothesis (max 3 sentences). Every 3 turns, cite something from it.

---

## Victory Scenarios (Example)

**Economic win (250K Zols):**
- Balanced expansion: own 2–3 territories
- Strong income: +2K base + 1.5K from territories = 3.5K/turn
- At 3.5K/turn, reach 250K in ~71 turns (need to optimize)
- Or trade aggressively (riskier)

**Territorial win (6 territories):**
- Aggressive dueling: challenge for each territory
- Win rate: ~50% per duel (manche 3 is 50/50)
- By turn 36: feasible to own 5–6 if lucky + skilled QCM
- Requires committing to duel strategy early

**Hybrid win:**
- Own 4 territories by turn 20
- Bank Zols from remaining turns
- Reach 200K + 4 territories simultaneously (safer)

---

**This ruleset is canonical. All agent decisions are evaluated against it.**

