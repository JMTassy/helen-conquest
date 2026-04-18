# System Architecture Treemap: LEGO Hierarchy → Scalable Kernel

## Visual Map (Text-Based Treemap)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCALABLE KERNEL (Top Layer)                         │
│                     Self-Enforcing, Modular, Replicable                     │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────────┐
         │                         │                             │
    ┌────▼────┐          ┌────────▼────────┐         ┌──────────▼──────┐
    │DISTRICTS│          │ EXPERTISE LAYER │         │  GOVERNANCE     │
    │ (LEGO3) │          │   (Built from    │         │   BOUNDARY      │
    └────┬────┘          │    Superteams)   │         │   (Oracle Town)  │
         │               └────────┬────────┘         └──────────┬──────┘
         │                        │                             │
    ┌────▼─────────────┐    ┌─────▼──────────┐         ┌───────▼──────┐
    │FOUNDRY DISTRICT  │    │CREATIVE DISTRICT│        │K-GATES CHECK  │
    │(Production)      │    │(Lateral Sync)   │        │Authority Sep. │
    │                  │    │                 │        │No Self-Edit   │
    │·Production flow  │    │·Pattern Match   │        │Determinism    │
    │·Claim market     │    │·Lateral explore │        │Fail-closed    │
    │·Agent pipeline   │    │·Hyperfocus     │        │               │
    │·Editorial cut    │    │                 │        └───────────────┘
    │                  │    │MUSIC DISTRICT   │
    │SCIENCE DISTRICT  │    │(Dopamine Loop)  │
    │(Evidence)        │    │                 │
    │                  │    │·Rhythm Cycles  │
    │·Researcher       │    │·Mood tracking  │
    │·Data gathering   │    │·Energy mapping │
    │·Sources          │    │                 │
    │                  │    │UZIK DISTRICT   │
    │GOVERNANCE        │    │(Aesthetic Sync)│
    │(Constitutional)  │    │                 │
    │                  │    │·Visual flow    │
    │·Skeptic testing  │    │·Card design    │
    │·K-gate checks    │    │·UI patterns    │
    │·Authority log    │    │                 │
    │                  │    └─────────────────┘
    └──────────────────┘
         │
    ┌────▼──────────────────────────────────────────────┐
    │         SUPERTEAMS (LEGO2 - Functional Units)     │
    │     Combines agent roles for specific domains     │
    │                                                   │
    │  ┌────────────┐  ┌─────────────┐ ┌────────────┐ │
    │  │Production  │  │Governance   │ │Knowledge  │ │
    │  │Superteam  │  │Superteam    │ │Superteam  │ │
    │  │            │  │              │ │            │ │
    │  │Foreman     │  │Skeptic      │ │Researcher │ │
    │  │Editor      │  │Mayor        │ │Structurer │ │
    │  │Writer      │  │Ledger       │ │Visualizer │ │
    │  └────────────┘  └─────────────┘ └────────────┘ │
    │                                                   │
    │  ┌────────────┐  ┌─────────────┐                │
    │  │Creative    │  │Execution    │                │
    │  │Superteam   │  │Superteam    │                │
    │  │            │  │              │                │
    │  │Lateral     │  │Synthesizer  │                │
    │  │Pattern     │  │Scheduler    │                │
    │  │Music       │  │Registry     │                │
    │  └────────────┘  └─────────────┘                │
    │                                                   │
    └────┬──────────────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────────────────┐
    │      AGENT ROLES (LEGO1 - Atomic Units)          │
    │      Single responsibility, provable capability  │
    │                                                   │
    │  OPERATIONAL (Do Work)                            │
    │  ├─ Researcher (gather evidence)                 │
    │  ├─ Writer (prose, narrative)                    │
    │  ├─ Structurer (outline, flow)                   │
    │  ├─ Skeptic (adversarial test)                   │
    │  ├─ Visualizer (diagrams, charts)                │
    │  └─ Synthesizer (merge, consolidate)             │
    │                                                   │
    │  COORDINATIVE (Orchestrate)                      │
    │  ├─ Foreman (phase, assign, curate)             │
    │  ├─ Editor (unilateral cut, finalize)           │
    │  ├─ Mayor (governance veto, freeze)             │
    │  └─ Scheduler (timing, deadlines)                │
    │                                                   │
    │  DATA (Immutable Record)                         │
    │  ├─ Ledger (decision log, hashes)               │
    │  ├─ Registry (agent manifest, signer list)      │
    │  └─ Claim Market (pending/accepted/merged)      │
    │                                                   │
    └────────────────────────────────────────────────────┘
```

---

## How This Scales (From LEGO1 to Kernel)

### LEGO1: Agent Role (Atomic Intelligence)

**What it is:** Single, bounded responsibility. One agent = one capability.

**Examples:**
- Researcher: "I gather facts and cite sources. That's all."
- Skeptic: "I attack claims. I find holes. I don't fix."
- Writer: "I draft prose from accepted claims. I don't invent."

**Why it matters:**
- Clear accountability (this person did this task)
- Testable (did they stay in their lane?)
- Composable (many LEGO1s make LEGO2)
- Replaceable (swap agent, keep role)

---

### LEGO2: Superteam (Functional Domain)

**What it is:** 2-6 agent roles combined for a specific purpose.

**Examples:**

#### Production Superteam
- Foreman (assign work, curate claims)
- Editor (cut, merge, finalize)
- Writer (draft prose)
- Synthesizer (merge overlapping ideas)
- **Purpose:** Convert ideas → deliverables

#### Governance Superteam
- Skeptic (test claims, find contradictions)
- Mayor (veto authority, freeze decisions)
- Ledger (immutable record, signature)
- **Purpose:** Ensure safety, prevent fraud, prove decisions

#### Knowledge Superteam
- Researcher (gather facts)
- Structurer (organize, outline)
- Visualizer (make diagrams, charts)
- **Purpose:** Explore, map, surface evidence

#### Creative Superteam
- Lateral Pattern (find connections across domains)
- Music Rhythm (track cycles, mood, energy)
- **Purpose:** Lateral exploration, dopamine loop maintenance

---

### LEGO3: District (Expertise Cluster)

**What it is:** Superteams specialized for a domain or rhythm.

**Examples:**

#### FOUNDRY DISTRICT
**Responsibility:** Transform disagreement → deliverables.
**Superteams:** Production, Governance, Knowledge
**Output:** Finished artifacts (memos, docs, code)
**Rhythm:** 5-phase pipeline (Exploration → Tension → Draft → Collapse → Terminate)

#### CREATIVE DISTRICT
**Responsibility:** Lateral exploration, pattern synthesis, dopamine loop.
**Superteams:** Creative, Music
**Output:** Connected insights, mapped relationships
**Rhythm:** Hyperfocus cycles (4h on, 15m break, select, ship)

#### SCIENCE DISTRICT
**Responsibility:** Evidence gathering, data validation, source management.
**Superteams:** Knowledge, Governance
**Output:** Fact repositories, decision records
**Rhythm:** Continuous (sources updated, facts validated)

#### MUSIC DISTRICT
**Responsibility:** Rhythm cycling, mood tracking, energy management.
**Superteams:** Creative, Rhythm
**Output:** Work schedules, energy maps, burnout prevention
**Rhythm:** Weekly cycles (hyperfocus windows, rest, reset)

#### UZIK DISTRICT
**Responsibility:** Aesthetic alignment, card design, visual coherence.
**Superteams:** Creative, Visualizer
**Output:** Design systems, card hierarchies, UI patterns
**Rhythm:** Per-sprint (design → build → validate)

---

### LEGO4+: Kernel (Scalable, Self-Enforcing System)

**What it is:** The entire architecture compressed into replicable rules.

**Core principle:** Every layer enforces itself through immutable records (Ledger, K-gates, Constitutional rules).

**Why it scales:**
1. **No central authority** — Each district can fork/replicate
2. **Self-enforcing rules** — K-gates are deterministic (same input → same output)
3. **Modular replacement** — Swap a superteam, keep the kernel
4. **Verifiable** — Ledger proves every decision was made, not guessed

**How CONQUEST uses it:**
- **World Model:** Town (plateau) + NPC agents (LEGO1) + governance (Oracle Town kernel)
- **Game Loop:** Card duel (Production) + Activation (Music) + Learning (Science)
- **Scaling:** Clone districts per region, federate through Constitutional boundary

---

## CONQUEST: The Seed Project

**Mission:** Test the Kernel in a world model (avatar + land + agents).

### MVP Architecture

```
CONQUEST GAME (Eduverse)
│
├─ WORLD MODEL
│  ├─ Plateau (grid, locations, resources)
│  ├─ Agents (NPCs with roles, governed by Oracle Town)
│  └─ Land (territory, governance, claims)
│
├─ GAME LOOP
│  ├─ CARD DUEL (Production Superteam applies)
│  │  └─ Combat: Claim + Defense = Verdict (like Foundry tension phase)
│  │
│  ├─ FOOD ACTIVATION (Music District applies)
│  │  └─ Rhythm: Eating triggers mood, mood triggers action
│  │
│  └─ SIMPLE MVP WEB (Uzik District applies)
│     └─ Design: Card display, turn flow, score (minimal aesthetic)
│
├─ LEARNING LAYER
│  ├─ What worked? (Science District evaluates)
│  ├─ Why? (Researcher gathers facts)
│  └─ Next? (Foreman schedules improvement)
│
└─ GOVERNANCE BOUNDARY
   ├─ K-gates enforce NPC rules (no self-modification)
   ├─ Ledger logs every decision
   └─ Mayor can freeze state (permanent archive)
```

### Why This Works (Tests the Kernel)

| Kernel Element | CONQUEST Test | What It Validates |
|---|---|---|
| **Agent Roles** | NPC agents have fixed roles | Roles are truly atomic |
| **Superteams** | Card duel combines roles | Superteams coordinate without chat |
| **Districts** | Game loops follow district rhythms | Districts are truly independent |
| **K-gates** | NPCs cannot self-modify | Constitutional rules hold under pressure |
| **Ledger** | Every action logged | Decisions are verifiable |
| **Scalability** | Clone districts for new regions | Kernel replicates without redesign |

---

## Memory: Key Principles (For Next Session)

### The Atomic Model (Never Break These)

1. **LEGO1 = Agent Role**
   - One responsibility per agent
   - Clear boundary (this agent does X, not Y)
   - Provable (did they stay in their lane?)

2. **LEGO2 = Superteam**
   - 2-6 roles combined
   - One clear purpose (Production, Governance, Knowledge, Creative)
   - No role overlap (Structurer ≠ Writer)

3. **LEGO3 = District**
   - Superteams specialized for domain
   - Own rhythm and termination
   - Can fork/replicate independently

4. **LEGO4+ = Kernel**
   - Self-enforcing rules (K-gates, Constitutional)
   - Immutable records (Ledger)
   - Provably scalable

### The Dopamine Loop (Lateral Thinking)

- **EXPAND** (Hyperfocus): Lateral exploration, no filtering
- **BREAK** (15min): Micro-rest, context reset
- **SELECT** (Fresh eyes): Prune beautiful distractions
- **SHIP** (Editor decides): Unilateral cut, move on

**Key insight:** Music District tracks energy to prevent burnout without guilt.

### CONQUEST as Proof

- **World Model:** Town simulation (plateau, agents, governance)
- **Game Loop:** Card duel (tension phase IRL), Food (mood activation), Web MVP
- **Learning:** Every run updates the Ledger (Science District evaluates)
- **Scalability:** Clone districts per region, federate through Kernel

---

## Connections (Lateral Map)

```
Oracle Town (frozen)
    ↓ (governance kernel)
Foundry Town (production system)
    ↓ (applies atomic model)
LEGO1→2→3 Hierarchy
    ↓ (scales to)
CONQUEST (world simulation proof)
    ↓ (learns from)
Science District (evaluation)
    ↓ (feeds back to)
Kernel Improvements
```

**The point:** Every layer is built from the layer below, and every layer reinforces the whole.

---

**Last Updated:** 2026-02-12
**Status:** Treemap complete; Kernel validated through CONQUEST MVP design
