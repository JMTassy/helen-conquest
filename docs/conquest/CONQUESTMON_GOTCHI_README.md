# CONQUESTmon-Gotchi: Playable Governance

**Status:** Ready to Play
**Version:** 0.1 (Alpha)
**Seed:** 12345
**Created:** February 15, 2026

---

## 🏰 What Is This?

CONQUESTmon-Gotchi is a **playable governance simulation**. You raise a living castle creature through 36-50 rounds of decisions and opposition pressure.

You don't manage abstract metrics. You care about your castle.

---

## 🎮 Quick Start (5 Minutes)

### Run the Game

```bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'
python3 conquestmon_gotchi_cli.py
```

You'll see:

```
Round 1 | Day 1
════════════════════════════════════════════════════════════════

🏚️  Structural Margin: +6.6 [STABLE]

PRIMARY METRICS
  Territory: ░░░░░░░░░░ 1.0/20
  Stability: █████░░░░░ 5.0/10
  Cohesion:  █████░░░░░ 5.0/10
  Knowledge: ███░░░░░░░ 3.0/10
  Entropy:   ██░░░░░░░░ 2.0/10

[Opposition, Memory, Metrics...]

Your action?
  [1] EXPAND     (+Territory, +Entropy, +Debt)
  [2] FORTIFY    (+Stability, -Entropy, +Fatigue)
  [3] CELEBRATE  (+Cohesion, +Fatigue)
  [4] STUDY      (+Knowledge, +Inertia)
  [5] REST       (-Fatigue, -Debt)

> _
```

Type **1-5** to choose an action.

---

## 🕹️ The 5 Actions

### 1️⃣ EXPAND
**Cost:** +Entropy, +Debt
**Benefit:** +Territory
**Feel:** Risky growth. Fast but expensive.

### 2️⃣ FORTIFY
**Cost:** +Fatigue
**Benefit:** +Stability, -Entropy
**Feel:** Defensive. Tiring but secure.

### 3️⃣ CELEBRATE
**Cost:** +Fatigue
**Benefit:** +Cohesion, -Entropy (if fatigue ≤ 8)
**Feel:** Morale boost. Cannot if exhausted.

### 4️⃣ STUDY
**Cost:** +Inertia
**Benefit:** +Knowledge
**Feel:** Long-term resilience. Learning pays off later.

### 5️⃣ REST
**Cost:** Nothing (stops growth)
**Benefit:** -Fatigue, -Debt
**Feel:** Recovery. Necessary but slow.

---

## 📊 The 7 Metrics

### Primary (You Control These)

| Metric | What It Is | Range | How It Changes |
|--------|-----------|-------|---|
| **Territory** | Land you own | 0-20 | EXPAND (+1), Opposition attacks (-?) |
| **Stability** | Structural strength | 0-10 | FORTIFY (+1.5), Opposition ATTACK (-0.7) |
| **Cohesion** | Internal unity | 0-10 | CELEBRATE (+1.2), Opposition PROBE (-0.2) |
| **Knowledge** | Wisdom acquired | 0-10 | STUDY (+1), Controls entropy drift |
| **Entropy** | Disorder (grows) | 0-20 | EXPAND (+0.3), FORTIFY (-0.2), drifts (+0.1/round) |

### Secondary (Memory/Hysteresis)

| Metric | What It Is | How It Decays |
|--------|-----------|---|
| **Debt** | Owed burden | -0.1/round if resting, +0.02/round otherwise |
| **Inertia** | Stuck resistance | -0.03/round (slowly fades) |
| **Fatigue** | Exhaustion | -0.05/round naturally, -1 if REST |

---

## 👿 The Opposition

Opposition is a **second organism** applying pressure to your castle.

### Opposition State

- **Aggression:** Grows from weakness and debt
- **Capability:** Grows from chaos (entropy)
- **Posture:** OBSERVE → PROBE → SABOTAGE → ATTACK

### Opposition Postures

| Posture | Triggered By | Effect |
|---------|---|---|
| **OBSERVE** | Margin > 5 (you're strong) | None. Safe. |
| **PROBE** | Mid-range weakness | +Entropy, -Cohesion |
| **SABOTAGE** | High debt (> 3) | +Debt, +Fatigue |
| **ATTACK** | Low stability (< 4) | -Stability, +Entropy |

Opposition is **deterministic**. Not random. Not evil.

It responds to your actual weakness.

---

## 🎯 Victory & Defeat

### 🏆 LEGENDARY BASTION (Win)

Achieve AND hold for 5 consecutive rounds:

- Territory ≥ 8
- Entropy < 6
- Debt < 2
- Opposition posture = OBSERVE
- Structural margin L > 5

### 💀 COLLAPSE (Lose)

Game ends if:

- Structural margin L ≤ -3
- Stability ≤ 0
- Territory shrinks to 0

### ⚖️ Structural Margin (L)

**Your viability indicator.**

```
L = Stability + 0.5*Cohesion + 0.5*Knowledge
    - Entropy - 0.5*Debt - 0.5*Inertia
    - 0.3*Fatigue - 0.2*Opposition.Aggression
```

- **L > 5:** FLOURISHING (safe)
- **L 2-5:** STABLE (ok)
- **L 0-2:** STRUGGLING (warning)
- **L < 0:** CRITICAL (danger)
- **L ≤ -3:** COLLAPSE (game over)

---

## 💡 Strategy Tips

### Early Game (Rounds 1-10)

Opposition is weak. Expand aggressively.

```
Actions: EXPAND, EXPAND, FORTIFY, EXPAND, STUDY
Result: Territory 4-5, Entropy growing, Opposition still OBSERVE
```

**Why:** Lock in territory before opposition strengthens.

### Mid Game (Rounds 11-25)

Balance expansion with stability. Opposition now attacks.

```
Actions: FORTIFY, EXPAND, CELEBRATE, STUDY, REST
Result: Stable mix. Keep margin > 2
```

**Why:** Opposition now poses real threat.

### Late Game (Rounds 26-36)

Race to legendary victory. Margin becomes critical.

```
Actions: FORTIFY, CELEBRATE, STUDY (locked strategy)
Result: High stability, low entropy, opposition back to OBSERVE
```

**Why:** You can't expand anymore. Defend what you have.

---

## 🔮 Commands

During play:

```
> 1          EXPAND
> 2          FORTIFY
> 3          CELEBRATE
> 4          STUDY
> 5          REST
> s          Show current status
> l          Show last 10 rounds (ledger)
> f          Forecast next 10 rounds
> q          Quit
```

---

## 🎲 Run Variations

### New Game (Random Seed)

```bash
python3 conquestmon_gotchi_cli.py
```

### Specific Seed (Deterministic)

```bash
python3 conquestmon_gotchi_cli.py --seed 12345
```

Same seed → **identical outcome** (K5 determinism guaranteed).

### Headless Mode (AI Play)

```bash
python3 conquestmon_gotchi_cli.py --headless --rounds 100 --seed 999
```

Game plays 100 rounds automatically. No interaction.

---

## 📈 Learning Path

### First 5 Minutes
- Understand the 5 actions
- See your castle sprite change
- Notice opposition responding

### First 30 Minutes
- Survive 1 full game (win or collapse)
- Feel the tension between growth and stability
- Understand debt and fatigue

### 1-2 Hours
- Achieve legendary victory once
- Map the strategy space
- See how opposition predicts your weakness

### 10+ Hours
- Optimize consistently
- Understand second-order effects (hysteresis)
- Master the opposition logic

---

## 🧪 Validation

### Determinism (K5)

Run this to verify same-seed replay:

```bash
# Run game 1 with seed 42
python3 conquestmon_gotchi_cli.py --seed 42 --headless --rounds 50

# Results saved to ledger_42.json

# Run game 2 with seed 42
python3 conquestmon_gotchi_cli.py --seed 42 --headless --rounds 50

# Compare ledgers — they're identical
```

### Physics Tests

```bash
python3 conquestmon_gotchi_core.py
# Runs 10 quick rounds, shows ledger
```

---

## 📝 Files

- `conquestmon_gotchi_core.py` — Game engine (physics, opposition, actions)
- `conquestmon_gotchi_cli.py` — Interactive interface
- `tests/test_conquestmon_gotchi_core.py` — Test suite
- `CONQUESTMON_GOTCHI_SPECIFICATION.md` — Full design doc
- `CONQUESTMON_GOTCHI_README.md` — This file

---

## 🔧 Technical

### Language
Python 3.8+

### Dependencies
None. Fully standalone.

### K-Gate Compliance
- **K1 (Fail-Closed):** Invalid actions rejected
- **K5 (Determinism):** Same seed → identical ledger
- **Ledger:** Every round logged with full state

### Physics
All calculations are:
- Deterministic (no randomness)
- Reversible (you can audit any decision)
- Logged (ledger is canonical truth)

---

## 🎓 What You Learn

Playing CONQUESTmon-Gotchi teaches:

1. **Hysteresis** — Debt and fatigue stick. Actions have delayed consequences.
2. **Adversarial Pressure** — Opposition is not random; it responds to your weakness.
3. **Trade-offs** — You cannot expand and fortify simultaneously.
4. **Structural Margin** — Systems collapse from accumulated small degradations.
5. **Determinism** — Same decisions + same opposition = same outcome.

---

## 🚀 Next Steps

### Phase 2 (Future)
- Kernel integration (hook oracle_town.mayor)
- K-gate enforcement
- Ledger to immutable oracle_town ledger
- Multi-castle geopolitics

### Phase 3 (Future)
- Internal factions
- Economic production model
- Trait mutations at birth
- Web interface

---

## 👤 Author

Built by: Your Lateral Thinking Engine
Date: February 15, 2026
Seed: CONQUEST_V0: Constraint precedes power.

---

## 📞 How to Play

1. **Start:** `python3 conquestmon_gotchi_cli.py`
2. **Choose:** Type 1-5 each round
3. **Survive:** Keep margin > 0
4. **Win:** Achieve legendary bastion
5. **Replay:** Use same seed for identical game

Good luck. Your castle awaits.

🏰
