# CONQUESTmon-Gotchi: How to Play
**Status:** Ready to Play ✅

---

## Quick Start (5 Minutes)

### Step 1: Launch the Game

```bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'
python3 conquestmon_gotchi_cli.py
```

### Step 2: Read the Screen

When the game starts, you'll see:

```
Round 1 | Day 1
════════════════════════════════════════════════════════════
🏚️  Structural Margin: +6.6 [FLOURISHING]

PRIMARY METRICS
  Territory: ░░░░░░░░░░   1.0/20
  Stability: █████░░░░░   5.0/10
  Cohesion:  █████░░░░░   5.0/10
  Knowledge: ███░░░░░░░   3.0/10
  Entropy:   ██░░░░░░░░   2.0/10

MEMORY (Hysteresis)
  Debt:      ░░░░░░░░░░   0.0/10
  Inertia:   ░░░░░░░░░░   0.0/10
  Fatigue:   ░░░░░░░░░░   0.0/10

OPPOSITION
  Posture:    OBSERVE
  Aggression: ██░░░░░░░░  2.00
  Capability: ██░░░░░░░░  2.00
```

**What This Means:**
- 🏚️ = Your castle (starts as a hut)
- **Structural Margin: +6.6** = How healthy your castle is (higher is better)
- **[FLOURISHING]** = Your status (green zone)
- The bars show metrics from 0-10
- Opposition is currently OBSERVE (watching, not attacking)

### Step 3: Choose an Action

Every round, pick ONE action (1-5):

```
Your action?
  [1] EXPAND     (+Territory, +Entropy, +Debt) — Grow fast, pay later
  [2] FORTIFY    (+Stability, -Entropy, +Fatigue) — Survive attacks
  [3] CELEBRATE  (+Cohesion, +Fatigue) — Keep spirits up
  [4] STUDY      (+Knowledge, +Inertia) — Long-term resilience
  [5] REST       (-Fatigue, -Debt) — Recover

  [s] status  [l] ledger  [f] forecast  [q] quit

> _
```

Type a number (1-5) and press Enter.

---

## The 5 Actions Explained

### 1️⃣ EXPAND
**What it does:**
- Territory +1
- Entropy +0.3
- Debt +0.4

**When to use:** Early game, when stable
**Strategy:** Grow your land, but watch your debt and entropy

**Example:**
```
Territory: 1 → 2
Entropy:   2 → 2.3
Debt:      0 → 0.4
Margin:    6.6 → 5.98
Opposition will get slightly more aggressive
```

---

### 2️⃣ FORTIFY
**What it does:**
- Stability +1.5
- Entropy -0.2
- Fatigue +0.5

**When to use:** When opposition is attacking, or preparing for conflict
**Strategy:** Build strength, but get tired

**Example:**
```
Stability: 5 → 6.5
Entropy:   2 → 1.8
Fatigue:   0 → 0.5
Margin:    6.6 → 7.47
Better defense, less chaos
```

---

### 3️⃣ CELEBRATE
**What it does:**
- Cohesion +1.2
- Fatigue +0.3
- Entropy -0.1

**Restriction:** Can only use if Fatigue < 8

**When to use:** When morale is low, to boost unity
**Strategy:** Keep people happy, but you get tired

**Example:**
```
Cohesion: 5 → 6.2
Fatigue:  0 → 0.3
Entropy:  2 → 1.9
Margin:   6.6 → 7.5
People are happier
```

---

### 4️⃣ STUDY
**What it does:**
- Knowledge +1.0
- Inertia +0.2

**When to use:** Mid to late game, for long-term strength
**Strategy:** Learn for resilience, but get stuck

**Example:**
```
Knowledge: 3 → 4
Inertia:   0 → 0.2
Margin:    6.6 → 6.8
Higher knowledge helps control entropy
```

---

### 5️⃣ REST
**What it does:**
- Fatigue -1.0
- Debt -0.1

**When to use:** When exhausted, or managing debt
**Strategy:** Recover, but don't grow

**Example:**
```
Fatigue: 1 → 0
Debt:    1 → 0.9
Margin:  6.6 → 7.0
You're refreshed, debt shrinking
```

---

## Understanding Your Castle's Status

### Structural Margin (L)

This is the single most important number. It combines everything:

```
L = Stability + 0.5*Cohesion + 0.5*Knowledge
  - Entropy - 0.5*Debt - 0.5*Inertia - 0.3*Fatigue - 0.2*Opposition.Aggression
```

**Status Levels:**
- **L > 5:** 🟢 FLOURISHING (safe zone)
- **L 2-5:** 🟡 STABLE (proceed with caution)
- **L 0-2:** 🟠 STRUGGLING (danger zone)
- **L -3 to 0:** 🔴 CRITICAL (losing)
- **L ≤ -3:** ❌ COLLAPSE (game over)

---

### Opposition Posture

Opposition changes based on your weakness:

```
OBSERVE   = Safe (no threat)
PROBE     = Warning (testing your defenses)
SABOTAGE  = Serious (attacking your economy)
ATTACK    = Critical (direct assault)
```

**When you're strong:** Opposition OBSERVE (backs off)
**When you're weak:** Opposition escalates (PROBE → SABOTAGE → ATTACK)

---

## Example Game Strategy

### Early Game (Rounds 1-5)
**Goal:** Build a strong base

```
Round 1: FORTIFY  → Stability up to 6.5
Round 2: FORTIFY  → Stability up to 8.0
Round 3: FORTIFY  → Stability up to 9.5
Round 4: FORTIFY  → Stability maxed at 10
Round 5: FORTIFY  → Entropy down, margin strong
```

Opposition stays OBSERVE because you're strong.

### Mid Game (Rounds 6-15)
**Goal:** Expand territory

```
Round 6: EXPAND   → Territory 2
Round 7: EXPAND   → Territory 3
Round 8: EXPAND   → Territory 4
Round 9: EXPAND   → Territory 5
Round 10: EXPAND  → Territory 6
```

Entropy grows, debt grows. Opposition maybe goes to PROBE.

### Late Game (Rounds 16+)
**Goal:** Reach victory

```
Round 16: STUDY   → Knowledge up
Round 17: STUDY   → Knowledge up more
Round 18: REST    → Fatigue down, debt down
Round 19: REST    → Clean up
Round 20: EXPAND  → Territory 7
Round 21: EXPAND  → Territory 8
Round 22: FORTIFY → Stabilize
```

If all metrics hit victory conditions (territory ≥ 8, entropy < 6, debt < 2, margin > 5, opposition = OBSERVE), you WIN.

---

## Special Commands

While playing, you can use:

- **[1-5]** = Perform action
- **[s]** = Show full status
- **[l]** = Show last 10 rounds (ledger)
- **[f]** = Forecast next 10 rounds
- **[?]** = Show help
- **[q]** = Quit game

---

## Win Condition: LEGENDARY BASTION

To achieve victory, sustain ALL of these for 5 consecutive rounds:

- **Territory ≥ 8** (must own enough land)
- **Entropy < 6** (must control chaos)
- **Debt < 2** (must be solvent)
- **Opposition = OBSERVE** (opposition must be calm)
- **Margin > 5** (overall health is strong)

When all 5 are met for 5 rounds in a row:

```
🏆 VICTORY: LEGENDARY BASTION ACHIEVED!
Your castle stands eternal. Opposition bows.
```

---

## Lose Condition: COLLAPSE

Game ends if ANY of these happen:

- **Margin ≤ -3** (total viability failure)
- **Stability ≤ 0** (castle crumbles)
- **Territory ≤ 0** (lost all land)

When collapse happens:

```
💀 YOUR CASTLE HAS COLLAPSED!
The realm falls to chaos. Opposition consumes all.
```

---

## Advanced: Understanding Hysteresis

Three metrics "stick" to your castle and decay slowly:

- **Debt:** Grows from EXPAND, shrinks from REST
- **Inertia:** Grows from STUDY, naturally fades
- **Fatigue:** Grows from FORTIFY/CELEBRATE, only REST cures it

These create **momentum** — you can't instantly change direction. You're managing momentum, not just raw stats.

---

## Tips for Success

### Early Game Tips
1. Start with FORTIFY (build stability first)
2. Get to stability 10 (max) before expanding
3. Opposition stays calm when you're strong

### Mid Game Tips
4. EXPAND when stable (grow territory)
5. Watch entropy (it grows every round)
6. High knowledge helps slow entropy

### Late Game Tips
7. REST to manage debt and fatigue
8. STUDY for long-term resilience
9. Balance growth with recovery

### General Tips
10. Margin is your lifeline (keep it > 0)
11. Opposition is deterministic (same seed = same behavior)
12. Ledger is forever (all decisions recorded)

---

## How to Play Headless (Testing)

If you want to run automated games:

```bash
# Play 50 rounds automatically
python3 conquestmon_gotchi_cli.py --headless --rounds 50

# Play with specific seed (deterministic)
python3 conquestmon_gotchi_cli.py --seed 12345 --headless --rounds 50

# Play two games with same seed (should be identical)
python3 conquestmon_gotchi_cli.py --seed 42 --headless --rounds 30
python3 conquestmon_gotchi_cli.py --seed 42 --headless --rounds 30
# Both will have identical results
```

---

## Quick Reference

| Action | Territory | Stability | Entropy | Debt | Fatigue | Best For |
|--------|-----------|-----------|---------|------|---------|----------|
| EXPAND | +1 | - | +0.3 | +0.4 | - | Growth |
| FORTIFY | - | +1.5 | -0.2 | - | +0.5 | Defense |
| CELEBRATE | - | - | -0.1 | - | +0.3 | Morale |
| STUDY | - | - | - | - | - | Knowledge |
| REST | - | - | - | -0.1 | -1.0 | Recovery |

---

## Ready to Play?

```bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'
python3 conquestmon_gotchi_cli.py
```

**Have fun raising your castle! 🏰**

---

**Pro Tip:** Try playing two games with the same seed:
```bash
python3 conquestmon_gotchi_cli.py --seed 111
python3 conquestmon_gotchi_cli.py --seed 111
```

Both will be **identical** (same choices, same outcomes). That's determinism! 🎮

