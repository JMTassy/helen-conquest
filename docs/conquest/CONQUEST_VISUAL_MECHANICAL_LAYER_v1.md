# CONQUEST Visual/Mechanical Layer v1.0

**Aesthetic:** Gothic, dark, video-game intense
**Accessibility:** ADHD (high contrast, strict symbol caps, rapid scanning)
**Factions:** ✝️ Templar / 🌹 Rosicrucian / 🌀 Chaos (mechanical, not decorative)
**Alchemical Layer:** 🜁🜂🜃🜄🜍 + ✝️⸸ as deterministic overlays

---

## I. ALCHEMICAL SYMBOLS — MECHANICAL MAPPING

### Five Alchemical States (Deterministic)

Each agent/territory has exactly ONE active alchemical state at any time. State changes only via explicit action or event.

| Symbol | Name | Meaning | Game Effect | Trigger |
|---|---|---|---|---|
| 🜁 | Sulfur (Volatility/Offense) | Aggression, heat, chaos-aligned | +1 POWER per tick, −1 STABILITY per conflict round | Agent chooses EXPAND or ATTACK |
| 🜂 | Mercury (Mobility/Transition) | Flow, adaptation, knowledge-aligned | +1 MOVEMENT range, +1 KNOWLEDGE per diplomacy | Agent chooses DIPLOMACY or RESEARCH |
| 🜃 | Salt (Crystallization/Order) | Solidity, structure, templar-aligned | +1 DEFENSE, +1 STABILITY, −1 POWER | Agent chooses REINFORCE or HOLD |
| 🜄 | Aqua Regia (Dissolution/Transformation) | Surrender, transformation, rosicrucian-aligned | Can transmute 1 territory → knowledge token, −1 POWER, +1 KNOWLEDGE | Agent chooses SEAL or TRANSFORM |
| 🜍 | Philosophical Stone (Equilibrium) | Mastery, balance (rare/earned) | All stats +1, but cannot act (static state) | Achieved only via rare alignment of three agents |

### Rules for Alchemical States

- **Mutually exclusive:** Only one active per agent per tick
- **Persist until changed:** State lasts until next deliberate action overrides it
- **No random drift:** Only change via explicit action (EXPAND, RESEARCH, REINFORCE, SEAL, or faction rules)
- **Visible in UI:** Always show as single symbol next to agent ID

**Example agent line:**
```
A ✝️🜁  (Templar, Sulfur — aggressive stance)
```

---

## II. FACTION SIGILS — MECHANICAL RULE SETS

### ✝️ TEMPLAR (Order / Crystallization)

**Theme:** Crusader discipline, fortress doctrine, structural integrity

**Core Stats Bias:**
- +1 STABILITY (natural)
- +1 DEFENSE (in fortified territory)
- −1 CHAOS events (immune to chaos RNG)

**Passive Rule:**
- Adjacent to 🏰 (fortress): +1 CONTROL (territory stays stable under pressure)
- If STABILITY < 2: Cannot initiate EXPAND (must stabilize first)

**Active Ability (once per epoch):**
- SEAL: Declare a territory immutable (⛓️ marker). Enemy cannot conquer it, but you cannot expand from it either. Costs 1 POWER.

**Faction Weakness:**
- Suffers −1 POWER during 🌀 CHAOS spikes (Templar discipline falters in chaos)
- Cannot use 🜁 (Sulfur) alchemical state (philosophically opposed to aggression)

---

### 🌹 ROSICRUCIAN (Knowledge / Transmutation)

**Theme:** Research cult, alchemy, strategic transformation

**Core Stats Bias:**
- +1 KNOWLEDGE (natural)
- +1 per RESEARCH action (multiplicative)
- −1 POWER (fragile, intellectual)

**Passive Rule:**
- Every 3 consecutive RESEARCH ticks: gain 1 free DIPLOMACY action (knowledge spreads)
- Territory with 🜄 (Aqua Regia) state: can TRANSMUTE it → 1 knowledge token (counts toward RESEARCH mult)

**Active Ability (once per epoch):**
- CONVERT: Sacrifice 1 territory → all agents within 2 tiles gain +1 KNOWLEDGE for 2 ticks. Costs 2 KNOWLEDGE.

**Faction Weakness:**
- 🩸 War Intensity peaks (global stress): −1 KNOWLEDGE, −1 POWER (research halts in war)
- Cannot use 🜃 (Salt) alchemical state (rosicrucians reject rigid structures)

---

### 🌀 CHAOS (Volatility / Reality-Bending)

**Theme:** Unstable magic-tech, high variance, probabilistic effects

**Core Stats Bias:**
- +1 POWER (volatile surge)
- Random event roll each tick (seeded RNG from world state hash)
- −1 STABILITY naturally (chaos destabilizes)

**Passive Rule:**
- Each tick: deterministic glitch roll (seeded). One of:
  - 🔥 IGNITE adjacent tile (destroy 1 enemy control)
  - 🕳️ CORRUPT adjacent tile (entropy +0.1 locally)
  - ✨ SURGE: this agent +2 POWER this tick only
  - ⚠️ BACKLASH: this agent −1 STABILITY (chaos feedback)

**Active Ability (once per epoch):**
- REALITY BREAK: Negate one enemy action retroactively (reroll their last tick). Costs 2 STABILITY.

**Faction Weakness:**
- If 🕯️ Shadow Level is maxed (global entropy high): Chaos gets +1 EXPAND but +2 INSTABILITY risk (⚠️ marker)
- Cannot use 🜃 (Salt) alchemical state (chaos rejects crystallization)

---

## III. GLOBAL STATE MARKERS

### Top Bar (Always Visible)

Max 2 symbols shown, represents world pressure:

| Symbol | Meaning | Trigger | Effect |
|---|---|---|---|
| 🩸 | War Intensity | Any agent conflict | −1 KNOWLEDGE for Rosicrucian; +1 POWER for Chaos (temporary) |
| 🕯️ | Shadow Level | Entropy > 0.5 per territory | Chaos gets +1 EXPAND but +2 instability; Templar −1 POWER |

**Rendering:** `TICK 07   🩸🩸   🕯️🕯️🕯️` (number indicates level 1–3)

---

## IV. TILE MARKERS (Map Layer)

### Primary Markers (1 per tile, always visible)

| Symbol | Meaning | Effect |
|---|---|---|
| 🏰 | Fortress | +1 DEFENSE for owner; Templar +1 CONTROL here |
| 🔥 | Burning/Active Conflict | Entropy damage; anyone here loses 1 STABILITY per tick |
| 🕳️ | Corruption/Void | Entropy +0.1; cannot occupy; spreads slowly |
| ⛓️ | Sealed/Quarantined | Immutable (Templar SEAL ability); cannot conquer |

### Secondary Markers (Optional, max 1 additional per tile)

| Symbol | Meaning | Effect |
|---|---|---|
| ✨ | Blessed (Rosicrucian artifact) | +1 KNOWLEDGE to any agent occupying here |
| ☠️ | Doomed (Chaos instability) | −1 STABILITY to any agent; temporary (3 ticks) |

**Rendering rule:** Show primary + secondary (if present). Max 2 symbols per tile. Priority: 🏰 > 🔥 > 🕳️ > ⛓️ > (secondary).

---

## V. AGENT OVERLAY SYSTEM

### Strict Order (Always Same Sequence)

```
[ID] [Faction] [Alchemical State] [Status Badge]
```

Max 3 symbols per agent. No stacking, no randomization.

#### Position 1: Faction Sigil (Exactly 1)
- ✝️ TEMPLAR
- 🌹 ROSICRUCIAN
- 🌀 CHAOS

#### Position 2: Alchemical State (Exactly 1)
- 🜁 Sulfur (Offense)
- 🜂 Mercury (Mobility)
- 🜃 Salt (Defense)
- 🜄 Aqua Regia (Transmute)
- 🜍 Philosophical Stone (Equilibrium, rare)

#### Position 3: Status Badge (0–1, optional)
- ⚠️ UNSTABLE (Chaos backlash, temp)
- 🩸 WOUNDED (Health < 50%, faction-specific)
- ☠️ DOOMED (Will perish next tick unless action taken)
- ✨ BLESSED (Temporary buff, Rosicrucian artifact)
- (empty if none)

**Rendering Examples:**

```
A ✝️🜃           (Templar, Salt defensive state, no status)
B 🌹🜂✨         (Rosicrucian, Mercury mobility, Blessed)
C 🌀🜁⚠️         (Chaos, Sulfur offense, Unstable)
D ✝️🜍           (Templar, Philosophical Stone — rare equilibrium)
E 🌀🔥          (ERROR: 🔥 is tile marker, not agent status — not allowed)
```

---

## VI. DETERMINISTIC SEEDING FOR "GLITCH ROLL"

### Chaos Faction RNG (Seeded, Never Truly Random)

When a Chaos agent ticks, compute:

```
seed = world_tick XOR agent_id XOR entropy_hash
rng = xorshift32(seed)
outcome = rng % 4

if outcome == 0: IGNITE
if outcome == 1: CORRUPT
if outcome == 2: SURGE
if outcome == 3: BACKLASH
```

**Determinism guarantee:** Same (tick, agent, world state) always produces same outcome.

**Visualization in log:**
```
C🌀🜁   GLITCH[SURGE]  (Chaos agent C triggered Surge via seeded RNG)
```

---

## VII. FACTION INTERACTIONS (Tension Matrix)

### Templar vs Rosicrucian
- If adjacent and not in conflict: +1 STABILITY for Templar (order reinforces)
- If Templar SEALS a tile: Rosicrucian cannot TRANSMUTE it (knowledge blocked by stone)

### Rosicrucian vs Chaos
- If adjacent: Rosicrucian gains +1 KNOWLEDGE per tick (understanding chaos)
- If Chaos uses REALITY BREAK on Rosicrucian action: Rosicrucian can counter with CONVERT (chaos absorbed → knowledge)

### Chaos vs Templar
- If adjacent: −1 STABILITY for Templar per tick (chaos destabilizes)
- If Templar in 🏰 fortress: −1 effect (fortress resists chaos)
- If Chaos has 🕯️ Shadow Level maxed: can BREAK a Templar SEAL (chaos unmakes order)

---

## VIII. EXAMPLE TURN (Visual)

### Initial State

```
TICK 05   🩸   🕯️🕯️

MAP:
╔══════════════════════════════╗
║  A ✝️🜃    B 🌹🜂✨   🏰      ║
║         🔥              ⛓️   ║
║  C 🌀🜁⚠️           D ✝️🜍    ║
║        🕳️         🜍         ║
╚══════════════════════════════╝
```

### Agent Actions (This Tick)

**A (Templar, Salt):** HOLD (reinforces 🏰 fortress)
- Entropy tick: +0.10
- Templar passive: fortress +1 DEFENSE
- Alchemical: 🜃 (Salt) = +1 STABILITY
- **Result:** Fortress now +2 DEFENSE, A at max stability

**B (Rosicrucian, Mercury):** DIPLOMACY with D
- Entropy tick: −0.10 (knowledge action reduces)
- Rosicrucian passive: consecutive RESEARCH counter = 0 (not research)
- Alchemical: 🜂 (Mercury) = +1 MOVEMENT
- Status: ✨ (Blessed from artifact) persists
- **Result:** +1 alliance level, B moves 2 tiles

**C (Chaos, Sulfur):** EXPAND
- Entropy tick: +0.15 (expansion increases)
- Chaos glitch roll: xorshift32(5 XOR C_id XOR state_hash) = IGNITE
- Alchemical: 🜁 (Sulfur) = +1 POWER, −1 STABILITY per conflict
- Status: ⚠️ (Unstable) persists 1 more tick
- **Result:** C attacks 🔥 tile, gains +1 territory, Instability counter−1

**D (Templar, Philosophical Stone):** (Static, rare state; cannot act, +all stats)
- Counts as "holding" position
- **Result:** No action, but all defenses +1 this tick

### End-of-Tick State

```
TICK 06   🩸   🕯️🕯️

MAP:
╔══════════════════════════════╗
║  A ✝️🜃    B 🌹🜂      🏰      ║
║              (moved)    ⛓️   ║
║  C 🌀🜁           D ✝️🜍    ║
║        🕳️         🜍         ║
╚══════════════════════════════╝

LEDGER:
🏰 A HOLD: Fortress +2 DEFENSE, stability max
🌹 B DIPLOMACY: Alliance +1, Mercury mobility +1
🌀 C EXPAND: GLITCH[IGNITE], +1 territory, Unstable−1
✝️ D STATIC: Philosophical Stone, +all stats
```

---

## IX. COLOR/CONTRAST DISCIPLINE (ADHD-Safe)

### Terminal Rendering (Monochrome)

- Agent IDs: BOLD WHITE
- Faction sigils: BRIGHT (faction color inferred by reader)
- Alchemical symbols: NORMAL (good contrast on dark)
- Status badges: RED (⚠️ stands out)
- Tile markers: BRIGHT YELLOW for 🔥, DIM for 🕳️

**Example (styled):**
```
**A** ✝️🜃    **B** 🌹🜂✨    🏰
       🔥               ⛓️
**C** 🌀🜁⚠️           **D** ✝️🜍
      🕳️
```

### Web/GUI Rendering (If Needed Later)

- Templar: #CC0000 (dark red) background
- Rosicrucian: #333399 (deep blue) background
- Chaos: #FF6600 (orange) background
- Symbols: white on colored background for contrast
- Status badges: bright red or gold

---

## X. MECHANICAL CONSTRAINTS (Non-Negotiable)

1. **Max 3 overlays per agent:** Faction + Alchemical + Status (0–1). Never more.
2. **Max 2 markers per tile:** Primary (always) + Secondary (optional). Never more.
3. **One alchemical state at a time:** Mutual exclusivity enforced.
4. **Seeded RNG only:** No true randomness. All Chaos glitch rolls derive from tick + agent + state hash.
5. **Deterministic replay:** Any saved (tick, agents, tiles) can replay identically.
6. **No hidden state:** All symbols visible. No fog of war in symbol layer.

---

## XI. INTEGRATION WITH AVALON KERNEL

### Existing State → Visual Mapping

**Avalon's entropy (0.963) → Global markers:**
- If entropy > 0.5: Show 🕯️ Shadow Level (at 2)
- If any conflict detected: Show 🩸 War Intensity (at 1–2)

**Avalon's cohesion (9/10) → Agent status:**
- Cohesion 9/10 = no ⚠️ badges visible
- Cohesion 6/10 = some agents show ⚠️ (temporary instability)

**Avalon's territory (3) → Tile layout:**
- Each of Avalon's 3 territories = 🏰 fortress tile
- Strategic weak points = potential 🕳️ (corruption) or 🔥 (conflict)

**Avalon's knowledge_efficiency (0.225) → Rosicrucian passive:**
- If Sovereign has Rosicrucian faction: knowledge scaling applies
- RESEARCH actions gain multiplicative bonus based on efficiency

---

## XII. NEXT STEPS

Once this layer is approved:

1. **Integrate into EPOCH 3 simulation:** Assign faction sigils to Warden/Archivist/Steward agents
2. **Generate visual panels:** Each day shows map + agent states + global markers
3. **Log with symbols:** Ledger entries include alchemical state transitions
4. **Validate contrast:** Ensure ADHD-readable (high contrast, strict symbol caps)

---

**Status:** ✅ VISUAL/MECHANICAL LAYER v1.0 DESIGNED
**Domains Covered:** Alchemical mechanics, faction rule sets, deterministic chaos, ADHD accessibility
**Ready for:** Integration into Epoch 3 simulator and live gameplay

