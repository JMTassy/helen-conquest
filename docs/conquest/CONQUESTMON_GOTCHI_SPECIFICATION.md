# CONQUESTmon-Gotchi: Playable Governance Simulation

**Status:** Specification Phase
**Scope:** Full CLI implementation, Kernel-integrated, Deterministic & Replayable
**Target:** Playable in 5 minutes, Deep in 50 hours

---

## VISION

Transform abstract governance into a living, emotional creature you care about.

**Not:** A strategy game.
**Is:** A governance creature that grows, struggles, and can die.

You raise it.
The world pressures it.
You make choices under constraint.

---

## CORE LOOP (60 Second Round)

```
START: Display castle state + opposition posture
WAIT: Player chooses 1 action (3 sec decision window)
APPLY: Action effects + opposition reaction
DECAY: Entropy drift + memory updates
LOG: All to ledger (deterministic, replayable)
RENDER: New castle sprite + metrics
LOOP: Next round
```

---

## CASTLE STATE (7 Core Metrics)

Each metric 0-10 unless noted.

```python
@dataclass
class CastleState:
    # Primary
    territory: float = 1.0          # Land owned [0-20]
    stability: float = 5.0          # Structural integrity
    cohesion: float = 5.0           # Internal unity
    knowledge: float = 3.0          # Wisdom acquired
    entropy: float = 2.0            # Disorder [grows]

    # Secondary (Memory)
    debt: float = 0.0               # Owed burden [grows]
    inertia: float = 0.0            # Stuck resistance [grows]
    fatigue: float = 0.0            # Exhaustion [grows]

    # Opponent
    opposition_aggression: float = 2.0
    opposition_capability: float = 2.0
    opposition_posture: str = "OBSERVE"  # OBSERVE|PROBE|SABOTAGE|ATTACK

    # Metadata
    round: int = 1
    day: int = 1
    seed: int = 0
    ledger: List[dict] = field(default_factory=list)
```

---

## PLAYER ACTIONS (5 Choices)

Each round, player chooses ONE:

### 1️⃣ EXPAND
**Effect:**
- Territory +1
- Entropy +0.3
- Debt +0.4

**Why:** Grow fast but pay later.
**Risky:** Opposition probes.

---

### 2️⃣ FORTIFY
**Effect:**
- Stability +1.5
- Entropy -0.2
- Fatigue +0.5

**Why:** Survive attacks.
**Cost:** Tiring. Slows growth.

---

### 3️⃣ CELEBRATE
**Effect:**
- Cohesion +1.2
- Fatigue +0.3
- Entropy -0.1

**Why:** Keep spirits up.
**Limits:** Can't celebrate if fatigue > 8.

---

### 4️⃣ STUDY
**Effect:**
- Knowledge +1
- Inertia +0.2
- Unlocks higher stability cap

**Why:** Long-term resilience.
**Passive:** Learn from opposition behavior.

---

### 5️⃣ REST
**Effect:**
- Fatigue -1
- Debt -0.1 (slowly)
- Nothing grows

**Why:** Recover.
**Cost:** Stops momentum.

---

## OPPOSITION ENGINE (Deterministic Pressure)

### Opposition State

```python
@dataclass
class OppositionState:
    aggression: float = 2.0
    capability: float = 2.0
    posture: str = "OBSERVE"
```

### Update Law (Each Round)

```python
def update_opposition(state: CastleState) -> None:
    o = state.opposition_state

    # Aggression grows with weakness
    weakness = max(0, (7.0 - state.stability) / 7.0)
    o.aggression += weakness * 0.05
    o.aggression += state.debt * 0.03

    # Capability grows with chaos
    o.capability += state.entropy * 0.02

    # Decay if system strong
    if state.stability > 8 and state.cohesion > 7:
        o.aggression = max(0, o.aggression - 0.1)
```

### Posture Decision (Deterministic)

```python
def decide_posture(state: CastleState) -> str:
    margin = compute_structural_margin(state)
    o = state.opposition_state

    if margin > 5:
        return "OBSERVE"
    elif state.debt > 3:
        return "SABOTAGE"
    elif state.stability < 4:
        return "ATTACK"
    else:
        return "PROBE"
```

### Posture Effects (Applied Each Round)

| Posture | Effect | Feeling |
|---------|--------|---------|
| **OBSERVE** | None | Safe |
| **PROBE** | Entropy +0.4, Cohesion -0.2 | Watched |
| **SABOTAGE** | Debt +0.6, Fatigue +0.3 | Undermined |
| **ATTACK** | Stability -0.7, Entropy +0.5 | Assaulted |

---

## STRUCTURAL MARGIN (L)

The core metric that predicts collapse.

```python
def compute_structural_margin(state: CastleState) -> float:
    L = (
        state.stability           # Primary strength
        + 0.5 * state.cohesion    # Unity helps
        + 0.5 * state.knowledge   # Wisdom helps
        - state.entropy           # Chaos hurts
        - 0.5 * state.debt        # Debt hurts
        - 0.5 * state.inertia     # Stuck hurts
        - 0.3 * state.fatigue     # Tired hurts
        - 0.2 * state.opposition_state.aggression  # Threat hurts
    )
    return round(L, 2)
```

**L ≤ -3:** COLLAPSE (game over)
**L < 0:** CRITICAL (red alert)
**L 0-2:** STRUGGLING (warning)
**L 2-5:** STABLE (green)
**L > 5:** FLOURISHING (strong)

---

## ENTROPY DRIFT (Passive Decay)

Each round, entropy grows unless countered:

```python
def apply_entropy_drift(state: CastleState) -> None:
    # Base drift
    state.entropy += 0.1

    # Controlled by knowledge
    if state.knowledge > 5:
        state.entropy -= 0.05

    # Worsened by high debt
    if state.debt > 5:
        state.entropy += 0.1
```

Entropy is **inexorable**. You can slow it, not stop it.

---

## MEMORY EFFECTS (Hysteresis)

Each round, these "stick" to the castle:

### Debt (Structural Burden)

Grows from expansion, shrinks from rest.

```python
def apply_debt_decay(state: CastleState) -> None:
    if state.fatigue > 0:
        state.debt -= 0.05  # Resting helps
    else:
        state.debt += 0.02  # Drifts up
```

High debt makes opposition **sabotage**.

### Inertia (Stuck Resistance)

Grows from study, makes learning hard later.

```python
def apply_inertia_decay(state: CastleState) -> None:
    state.inertia -= 0.03  # Slowly fades
    # But Study action adds 0.2
```

### Fatigue (Exhaustion)

Grows from Fortify/Celebrate. Only Rest cures it.

```python
def apply_fatigue_decay(state: CastleState) -> None:
    state.fatigue -= 0.05  # Slow natural recovery
```

Can't Celebrate if fatigue > 8.

---

## VICTORY CONDITIONS

### ✅ LEGENDARY BASTION (Win)

Achieve AND sustain for 5 consecutive rounds:
- Territory ≥ 8
- Entropy < 6
- Debt < 2
- Opposition posture = "OBSERVE"
- Structural margin L > 5

**Reward:** Game declares victory. Ledger sealed.

### ⚠️ EQUILIBRIUM (Long-term Play)

If you never reach Legendary but survive 50 rounds:
- You've achieved stable governance
- Opposition respects you
- Game ends with honors

### ❌ COLLAPSE (Loss)

Triggered if:
- Structural margin L ≤ -3
- Stability ≤ 0
- Territory shrinks to 0

**Ledger saved.** You can replay.

---

## VISUAL EVOLUTION (ASCII Sprite)

Castle sprite evolves by Territory + Stability:

```
Territory 1,  Stability <4:  🏚️  (fragile hut)
Territory 2-3, Stability 4-6: 🏠 (house)
Territory 4-5, Stability 7+:  🏰 (castle)
Territory 8+,  Stability 9+:  👑 (fortress)

If Entropy > Stability:
    Add cracks:     🏚️ → 🏚️⚡
    Add smoke:      🏠 → 🏠💨
    Add despair:    🏰 → 🏰❌
```

Full ASCII renderer shows:

```
Round 47 | Day 7
═════════════════════════════════════════════════

Territory: ████████░ 8/20
Stability: ██████░░░ 6/10
Cohesion:  █████░░░░ 5/10
Knowledge: ████░░░░░ 4/10
Entropy:   ███░░░░░░ 3/10

Debt:      ██░░░░░░░ 2/10
Inertia:   ░░░░░░░░░ 0/10
Fatigue:   █░░░░░░░░ 1/10

Structural Margin: +3.2 [STABLE]
Opposition: PROBE (aggression 3.4, capability 2.1)

🏰 Castle stands. Watchers circle.

═════════════════════════════════════════════════

Your action?
  [1] EXPAND (territory+1, entropy+0.3, debt+0.4)
  [2] FORTIFY (stability+1.5, entropy-0.2, fatigue+0.5)
  [3] CELEBRATE (cohesion+1.2, fatigue+0.3)
  [4] STUDY (knowledge+1, inertia+0.2)
  [5] REST (fatigue-1, debt-0.1)

> _
```

---

## ROUND ORDER (Deterministic Sequence)

1. **Display State** → Show castle, metrics, opposition posture
2. **Get Action** → Player chooses 1-5
3. **Apply Action** → Update metrics per choice
4. **Opposition Update** → Recalculate aggression, capability
5. **Decide Posture** → Apply new posture
6. **Apply Opposition Effect** → Opposition action happens
7. **Entropy Drift** → Passive entropy growth
8. **Memory Decay** → Debt, inertia, fatigue changes
9. **Compute Margin** → Recalculate L
10. **Ledger Append** → Log full round state
11. **Check Victory/Collapse** → End game if triggered
12. **Next Round** → Loop to step 1

---

## KERNEL INTEGRATION

### K-Gate Enforcement

Every action goes through Mayor.Decide:

```python
def player_action(state: CastleState, action: int) -> bool:
    # K-gate: Invalid action?
    if action not in [1, 2, 3, 4, 5]:
        return False  # K1: Fail-closed

    # K-gate: Can you afford this?
    if action == 3 and state.fatigue > 8:
        return False  # K1: Fail-closed

    # K-gate: Mayor decides
    verdict = mayor.decide(action, state)

    if not verdict.approved:
        return False  # K1: Fail-closed

    # Apply if approved
    apply_action_effects(state, action)
    return True
```

### Ledger Logging

Every round appends:

```json
{
  "round": 47,
  "day": 7,
  "seed": 12345,
  "timestamp": "2026-02-15T14:23:45Z",
  "player_action": 2,
  "action_name": "FORTIFY",
  "state_before": {...},
  "state_after": {...},
  "opposition_posture": "PROBE",
  "structural_margin": 3.2,
  "decision_hash": "k5_determinism_verified"
}
```

### Determinism (K5)

Same seed → identical replay:

```bash
python3 conquestmon_gotchi.py --seed 12345 --replay
```

Ledger is cryptographically hashable.

---

## CLI INTERFACE

### Start Game

```bash
# New game
python3 conquestmon_gotchi.py

# Specific seed (for testing)
python3 conquestmon_gotchi.py --seed 42

# Replay from ledger
python3 conquestmon_gotchi.py --replay ledger_uuid_12345.json

# Headless (for testing)
python3 conquestmon_gotchi.py --headless --rounds 100 --seed 999
```

### Commands During Play

```
> 1          Play EXPAND
> 2          Play FORTIFY
> 3          Play CELEBRATE
> 4          Play STUDY
> 5          Play REST
> status     Show full metrics
> ledger     Show last 5 round logs
> forecast   Project next 10 rounds
> save       Save and exit
> quit       Quit without saving
```

---

## TESTING STRATEGY

### Unit Tests

```bash
pytest tests/test_conquestmon_gotchi.py -v
```

Test matrix:
- Action effects (5 actions × 4 states = 20 cases)
- Opposition logic (3 weakness levels × 3 postures = 9 cases)
- Entropy drift (with/without knowledge = 2 cases)
- Structural margin calculation (10 edge cases)
- Victory/collapse conditions (6 cases)

### Determinism Tests (K5)

```bash
pytest tests/test_conquestmon_gotchi_k5.py -v
```

- Run 1000 games with same seed
- Verify identical ledger output
- Hash ledgers, compare

### Integration Tests

```bash
pytest tests/test_conquestmon_gotchi_kernel.py -v
```

- Verify Mayor.decide enforces K-gates
- Verify ledger schema matches oracle_town
- Verify replay produces identical state

---

## FILE STRUCTURE

```
conquestmon_gotchi/
├── __init__.py
├── cli.py                 # CLI entry point
├── core/
│   ├── __init__.py
│   ├── castle.py          # CastleState dataclass
│   ├── opposition.py      # Opposition logic
│   ├── actions.py         # Action effects (1-5)
│   ├── physics.py         # Entropy, decay, margin
│   └── ledger.py          # Logging to kernel
├── rendering/
│   ├── __init__.py
│   ├── sprites.py         # ASCII castle
│   ├── metrics.py         # Stat display
│   └── colors.py          # Terminal colors (if fancy)
├── tests/
│   ├── test_core.py
│   ├── test_opposition.py
│   ├── test_determinism.py
│   └── test_kernel.py
└── README.md              # Player guide
```

All imports from oracle_town are clean:
```python
from oracle_town.mayor import Mayor
from oracle_town.ledger import Ledger
from oracle_town.k_gates import validate_action
```

---

## PLAYABILITY TARGETS

| Target | Time | Depth |
|--------|------|-------|
| **First 5 min** | See castle, make 5 choices | Understand action costs |
| **First session (30 min)** | Play to victory or collapse | Feel tension, learn opposition |
| **10 sessions (10 hrs)** | Achieve Legendary Bastion | Master strategy, understand hysteresis |
| **Completionist (50 hrs)** | Map all state space, find patterns | Governance theory embedded |

---

## SUCCESS CRITERIA

✅ **Playable in 5 minutes** (minimal tutorial)
✅ **Deterministic & replayable** (K5 passed)
✅ **Kernel-integrated** (uses Mayor, Ledger)
✅ **Emotionally engaging** (you care about your castle)
✅ **Teaches systems thinking** (hysteresis, adversarial pressure)
✅ **Extensible** (room for factions, mutations, trade)

---

## IMPLEMENTATION PHASES

### Phase 1: Core Engine (Today)
- Castle state + 5 actions
- Opposition logic
- Physics (entropy, decay)
- Basic CLI

### Phase 2: Kernel Integration
- Mayor.decide enforcement
- Ledger logging
- K-gate tests

### Phase 3: Polish
- ASCII rendering
- Color support
- Replay mode
- Achievement system

### Phase 4: Extensions (Future)
- Internal factions
- Economic production
- Mutation system
- Multi-castle geopolitics

---

**Ready to build Phase 1?**

