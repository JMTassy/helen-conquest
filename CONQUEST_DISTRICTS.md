# CONQUEST Districts & LEGO Hierarchy

## Overview

CONQUEST v0.1 is structured according to the **Atomic Intelligence Model** (LEGO hierarchy) from CLAUDE.md.

This document maps the game's 6 autonomous agents to the LEGO1-LEGO4 layers, showing how intelligence is composed from atomic units into scalable, self-enforcing systems.

---

## LEGO1: Atomic Roles (Single Responsibility)

Each LEGO1 role has **one bounded responsibility**. No overlaps. Clear accountability.

| Role | Agent Function | Responsibility | Cannot Do |
|------|---|---|---|
| **PLANNER** | `agent_planner()` | Design castle layout & adjacency bonuses | Cannot fortify, capture, research, or budget |
| **ECONOMIST** | `agent_economist()` | Balance resources (K/P/M) & prevent deficits | Cannot design, defend, explore, or research |
| **DEFENDER** | `agent_defender()` | Identify threats & recommend fortifications | Cannot expand, build, budget, or explore |
| **RESEARCHER** | `agent_researcher()` | Identify tech gaps & research paths | Cannot plan, defend, expand, or budget |
| **BUILDER** | `agent_builder()` | Schedule construction & manage queues | Cannot explore, fortify, research, or design |
| **EXPLORER** | `agent_explorer()` | Find expansion targets & map intelligence | Cannot build, defend, budget, or plan |

**Kernel constraint:** Each role proposes only within its boundary. A proposal violating this boundary is logged as a `[CONSTRAINT]` event.

---

## LEGO2: Superteams (Functional Domains)

2-6 LEGO1 roles grouped for a domain. Each team can finish a task independently.

### Superteam: PRODUCTION
- **Roles:** PLANNER + ECONOMIST + BUILDER
- **Purpose:** Convert resources into built structures
- **Output:** Build proposals, queue updates, cost estimates
- **Test:** "Can this team design and build a module?" YES

### Superteam: DEFENSE
- **Roles:** DEFENDER (+ parts of RESEARCHER for fortification tech)
- **Purpose:** Prevent raids, fortify frontier, research defensive techs
- **Output:** Fortification proposals, threat assessments, defense tech chains
- **Test:** "Can this team hold territory under raid escalation?" YES

### Superteam: EXPANSION
- **Roles:** EXPLORER + ECONOMIST (cost management)
- **Purpose:** Capture new tiles, scout threats, optimize territorial growth
- **Output:** Capture targets, expansion strategies, route planning
- **Test:** "Can this team grow territory without destabilizing economy?" YES

### Superteam: SCIENCE
- **Roles:** RESEARCHER (core)
- **Purpose:** Research technology, unlock bonuses, plan tech chains
- **Output:** Tech proposals, cost estimations, dependency analysis
- **Test:** "Can this team unlock a tech chain?" YES

---

## LEGO3: Districts (Expertise Clusters with Rhythm)

Superteams specialized for an environment with explicit activation rhythm.

### District: FOUNDRY
- **Superteams:** PRODUCTION (every turn) + SCIENCE (every 3 turns, for production-relevant techs)
- **Responsibility:** Transform resources into castle modules
- **Rhythm:** PRODUCTION activates every turn; SCIENCE every 3 turns
- **Output:** Build queue updates, module completions, construction schedules
- **Agents:** PLANNER, ECONOMIST, BUILDER, RESEARCHER (on turn % 3 == 0)
- **Boundary:** No direct combat decisions; only construction & resource conversion

### District: FRONTIER
- **Superteams:** EXPANSION (every turn) + DEFENSE (every turn)
- **Responsibility:** Expand territory, manage borders, defend against raids
- **Rhythm:** Both teams activate every turn (active defense needed)
- **Output:** Capture proposals, fortification, threat assessments, raid responses
- **Agents:** EXPLORER, ECONOMIST, DEFENDER
- **Boundary:** No resource hoarding; all captures must be affordable. Defense is reactive, not proactive terror.

### District: SCIENCE
- **Superteams:** RESEARCHER (pure)
- **Responsibility:** Identify tech gaps, propose research chains, unlock bonuses
- **Rhythm:** Every 3 turns (research is slow; less proposal spam)
- **Output:** Tech proposals, cost estimations, impact analysis
- **Agents:** RESEARCHER (on turn % 3 == 0)
- **Boundary:** No cycles (DAG enforced in tech tree). Cannot research A→B→A.

---

## LEGO4: Kernel (Constitutional Rules)

Immutable rules that all districts must obey. No exceptions.

### K1: Role Separation (LEGO1 Immutability)
- **Rule:** Agent cannot exceed its role boundary
- **Enforced by:** Proposal schema (agent field) + Kernel checks
- **Example:** EXPLORER cannot propose a build (violates PLANNER boundary)
- **Consequence:** Soft constraint logged as `[CONSTRAINT]` event; proposal still accepted but flagged

### K2: Superteam Authority (LEGO2 Coordination)
- **Rule:** Within a superteam, agents collaborate (proposer ≠ validator)
- **Enforced by:** Player (Foreman role) arbitrates all proposals
- **Example:** PLANNER proposes, ECONOMIST approves = valid; ECONOMIST approves own proposal = invalid
- **Consequence:** All proposals go to player for approval; no agent-to-agent voting

### K3: District Independence (LEGO3 Autonomy)
- **Rule:** Each district can operate solo (e.g., FOUNDRY works if FRONTIER is offline)
- **Enforced by:** Agents only read GameState (no inter-district dependencies)
- **Example:** FOUNDRY builds modules even if FRONTIER tiles are all enemy-owned
- **Consequence:** Districts coordinate through shared GameState only

### K4: Ledger Immutability (LEGO4 Proof)
- **Rule:** All actions logged immediately after turn; cannot be modified
- **Enforced by:** Turn hashes (turnhashes list) + Event log (write-once)
- **Example:** Turn 1 hash is computed after all actions; replay same seed = identical hash
- **Consequence:** Deterministic replay guaranteed; proof of game integrity

### K5: No Agent Self-Modification
- **Rule:** Agents cannot change their own proposals; cannot override Foreman; cannot modify rules
- **Enforced by:** Agent functions only produce proposals (pure functions)
- **Example:** Agent cannot approve its own proposal; cannot call `queue_build()` directly
- **Consequence:** All authority flows through player + Kernel

---

## Determinism & Replayability

**Same seed + same approvals = identical outcome.**

Evidence:
- **State hashing:** Every turn produces a state hash (from K, P, M, tile ownership, threat levels)
- **RNG seeding:** All randomness goes through `gs.rng` (seeded Random instance)
- **Pure proposal functions:** All agent functions are pure (no side effects)
- **Deterministic reducer:** `apply_actions()` is deterministic

**Verification:**
```bash
python3 conquest_v1.py 111 --replay
# Output: "Determinism check: replaying same seed… PASS"
```

---

## Example: How FOUNDRY + FRONTIER + SCIENCE Work Together

### Turn 1 (Startup)

**Active districts:** FOUNDRY (yes, 1%1==0), FRONTIER (yes, 1%1==0), SCIENCE (no, 1%3!=0)

**Agents activated:**
- PLANNER → "Library would help, K_tick is low" → FOUNDRY proposal
- ECONOMIST → "Resources balanced, but M is low" → FOUNDRY proposal
- BUILDER → "Queue is empty, suggest a build" → FOUNDRY proposal
- EXPLORER → "Capture these 3 tiles with good yields" → FRONTIER proposals
- DEFENDER → "No raids yet, but threat is rising" → (skips this turn)

**Proposals show in council:**
- `[FOUNDRY] PRODUCTION ...` (PLANNER, ECONOMIST, BUILDER proposals)
- `[FRONTIER] EXPANSION ...` (EXPLORER, ECONOMIST proposals)
- RESEARCHER skipped (SCIENCE inactive, turn 1 % 3 ≠ 0)

**Player approves 3 proposals → actions execute → turn advances.**

### Turn 2

Same as Turn 1: FOUNDRY, FRONTIER active; SCIENCE skipped.

**Proposals show in council:**
- `[FOUNDRY] PRODUCTION ...`
- `[FRONTIER] EXPANSION/DEFENSE ...`

### Turn 3 (SCIENCE Activates)

**Active districts:** FOUNDRY (yes, 3%1==0), FRONTIER (yes, 3%1==0), SCIENCE (yes, 3%3==0)

**Agents activated:** All 6 (RESEARCHER now active)

**Proposals show in council:**
- `[FOUNDRY] PRODUCTION ...`
- `[FRONTIER] EXPANSION/DEFENSE ...`
- `[SCIENCE] SCIENCE ...` ← **First RESEARCHER proposal** (e.g., "Writing tech available")

**Player now sees tech research options for the first time.**

---

## Council Output Format (With Districts)

```
═══ COUNCIL — 14 PROPOSALS ═══
[ 1] [FOUNDRY]    PRODUCTION   P5 ECONOMIST    build     granary@(0, 0)       (K:2 P:1 M:4) δ(stab:+2)
[ 2] [FRONTIER]   EXPANSION    P4 EXPLORER     capture   tile(2, 10)          (K:0 P:4 M:0) δ(K_tick:+3 P_tick:+1 M_tick:+0)
[ 3] [SCIENCE]    SCIENCE      P4 RESEARCHER   research  tech:writing         (K:15 P:0 M:0) δ(K_tick:+2)
```

**Columns:**
- `[FOUNDRY]` — District (LEGO3)
- `PRODUCTION` — Superteam (LEGO2)
- `P5` — Priority (1–5)
- `ECONOMIST` — Agent role (LEGO1)
- `build`, `capture`, `research` — Action type
- `granary@(0,0)` — Friendly target label
- Cost & delta — Resource impact

---

## Constraints Visualization

```
┌─ KERNEL (LEGO4) ─────────────────────────────────┐
│  • Role Separation              K1                │
│  • Superteam Authority          K2                │
│  • District Independence        K3                │
│  • Ledger Immutability          K4                │
│  • No Self-Modification         K5                │
└──────────────────────────────────────────────────┘
   ↓                    ↓                    ↓
┌─ DISTRICTS (LEGO3) ──────────────────────────────┐
│  FOUNDRY (1t)    FRONTIER (1t)    SCIENCE (3t)    │
└──────────────────────────────────────────────────┘
   ↓                    ↓                    ↓
┌─ SUPERTEAMS (LEGO2) ──────────────────────────────┐
│  PRODUCTION    EXPANSION+DEFENSE    SCIENCE       │
└──────────────────────────────────────────────────┘
   ↓                    ↓                    ↓
┌─ AGENTS (LEGO1) ──────────────────────────────────┐
│  PLANNER   BUILDER     EXPLORER      RESEARCHER   │
│  ECONOMIST DEFENDER    ECONOMIST                  │
│           BUILDER                                 │
└──────────────────────────────────────────────────┘
```

---

## Testing the LEGO Hierarchy

### Test 1: Role Boundaries
**Verify:** EXPLORER never proposes a build; PLANNER never captures a tile.

```bash
python3 conquest_v1.py 111
council
# Check: EXPLORER rows show only "capture" actions
# Check: PLANNER rows show only "build" actions
```

### Test 2: Superteam Coordination
**Verify:** PRODUCTION proposals (PLANNER + BUILDER + ECONOMIST) flow together; no conflict.

```bash
# Run game, observe PRODUCTION team proposals
# All should be [FOUNDRY] PRODUCTION (same district/team)
```

### Test 3: District Rhythm
**Verify:** SCIENCE proposals appear only on turns where turn % 3 == 0.

```bash
python3 conquest_v1.py 111
council  # T1: no [SCIENCE]
next     # T2: no [SCIENCE]
next     # T3: YES [SCIENCE]
next     # T4: no [SCIENCE]
next     # T5: no [SCIENCE]
next     # T6: YES [SCIENCE]
```

### Test 4: Ledger Immutability
**Verify:** Same seed produces identical turn hashes.

```bash
python3 conquest_v1.py 111 --replay
# Output: "Determinism check: replaying same seed… PASS"
```

### Test 5: Kernel Constraint Enforcement
**Verify:** Soft constraint checks log violations as `[CONSTRAINT]` events (if implemented).

```bash
# (Future: add explicit role boundary violations to event log)
log  # Check for [CONSTRAINT] events
```

---

## Code Locations (Reference)

- **LEGO1 agent functions:** Lines 500–760 in `conquest_v1.py`
  - `agent_planner()`, `agent_economist()`, `agent_defender()`, `agent_researcher()`, `agent_builder()`, `agent_explorer()`

- **LEGO2 superteam configs:** Lines 775–785 in `conquest_v1.py`
  - `SUPERTEAMS = {...}`

- **LEGO3 district configs:** Lines 787–795 in `conquest_v1.py`
  - `DISTRICTS = {...}`

- **LEGO4 kernel constants:** Lines 1–150 in `conquest_v1.py`
  - `TERRAIN`, `MODULE_DEFS`, `TECH_TREE`, determinism enforcement

- **District-aware agent activation:** Lines 809–850 in `conquest_v1.py`
  - `AGENT_TO_DISTRICT = {...}` + `run_agents()` with rhythm checks

- **Proposal schema (with district/superteam):** Lines 78–95 in `conquest_v1.py`
  - `Proposal` dataclass includes `superteam` and `district` fields

---

## Future Extensions

### LEGO4+ Scaling
Once CONQUEST passes all LEGO tests, the architecture can be cloned:

1. **New world region:** Add a new District (e.g., "OUTPOST") with subset of superteams
2. **Clone superteams:** Same superteams work in new region (no redesign needed)
3. **Inherit kernel:** Constitutional rules (K1–K5) apply to all regions automatically

### Multi-Region Governance
- Region A has FOUNDRY + FRONTIER (no SCIENCE)
- Region B has FOUNDRY + SCIENCE (no FRONTIER — peaceful expansion)
- Both inherit kernel rules; cross-region trade via shared ledger

### Skill Integration
The entire CONQUEST architecture can become a Cowork skill:
- User: *"Run a CONQUEST game to test my decision-making under uncertainty"*
- Skill spawns a new game session with LEGO hierarchy enforced

---

## Conclusion

CONQUEST v0.1 demonstrates that **intelligence is composable**:

- **LEGO1 (Atomic):** 6 agents, each with one clear boundary
- **LEGO2 (Functional):** 4 superteams, each with one domain
- **LEGO3 (Specialized):** 3 districts, each with its own rhythm
- **LEGO4 (Kernel):** 5 constitutional rules that hold everything together

Add more agents → more superteams → more districts → scale to 100+ region game, same kernel.

*Le savoir mène au pouvoir.* ⚔️
