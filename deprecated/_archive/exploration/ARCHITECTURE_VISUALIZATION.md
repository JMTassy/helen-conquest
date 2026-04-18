# System Architecture Visualization (ASCII Art + Relationships)

## The Complete Stack (Zoom Out → Zoom In)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                              ┃
┃                    SCALABLE KERNEL (Layer 4)                               ┃
┃                  Self-Enforcing, Deterministic, Replicable                 ┃
┃                                                                              ┃
┃  ┌──────────────────────────────────────────────────────────────────────┐  ┃
┃  │ Constitutional Rules:                                                 │  ┃
┃  │  • No Self-Ratification (proposer ≠ validator)                       │  ┃
┃  │  • Role Boundaries Immutable (LEGO1 cannot merge)                   │  ┃
┃  │  • Authority Separation (Foreman ≠ Editor)                          │  ┃
┃  │  • All Changes Logged (Ledger, deterministic)                       │  ┃
┃  │  • Fail-Closed Default (missing evidence → reject)                  │  ┃
┃  └──────────────────────────────────────────────────────────────────────┘  ┃
┃                                 ↑                                           ┃
┃                          Enforces all layers below                          ┃
┃                                                                              ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        ↓
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                    DISTRICTS (Layer 3)                                      │
│              Specializes Superteams + Controls Rhythm                       │
│                                                                              │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   FOUNDRY       │  │    CREATIVE    │  │    SCIENCE   │  │   MUSIC   │ │
│  │   DISTRICT      │  │    DISTRICT    │  │   DISTRICT   │  │ DISTRICT  │ │
│  │                 │  │                │  │              │  │           │ │
│  │ Production +    │  │ Lateral +      │  │ Knowledge +  │  │ Rhythm +  │ │
│  │ Governance +    │  │ Creative       │  │ Governance   │  │ Creative  │ │
│  │ Knowledge       │  │                │  │              │  │           │ │
│  │                 │  │Hyperfocus:     │  │Continuous:   │  │Weekly:    │ │
│  │5-Phase Pipeline │  │4h on, 15m break│  │Evidence      │  │Energy     │ │
│  │                 │  │                │  │gathering     │  │tracking   │ │
│  │Output:          │  │Output:         │  │              │  │           │ │
│  │Documents,       │  │Insights,       │  │Output:       │  │Burnout    │ │
│  │Memos,           │  │Connections,    │  │Facts,        │  │prevention │ │
│  │Code             │  │Patterns        │  │Diagrams      │  │schedule   │ │
│  └─────────────────┘  └────────────────┘  └──────────────┘  └───────────┘ │
│  ┌──────────────┐                                                            │
│  │    UZIK      │                                                            │
│  │   DISTRICT   │                                                            │
│  │              │                                                            │
│  │Creative +    │                                                            │
│  │Visualizer    │                                                            │
│  │              │                                                            │
│  │Per-Sprint:   │                                                            │
│  │Design        │                                                            │
│  │Systems,      │                                                            │
│  │Cards, UI     │                                                            │
│  └──────────────┘                                                            │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
        ↓
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                    SUPERTEAMS (Layer 2)                                     │
│            2-6 Roles Combined for One Clear Purpose                         │
│                                                                              │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │   PRODUCTION        │  │    GOVERNANCE        │  │   KNOWLEDGE      │  │
│  │   SUPERTEAM         │  │    SUPERTEAM         │  │   SUPERTEAM      │  │
│  │                     │  │                      │  │                  │  │
│  │ Foreman             │  │ Skeptic              │  │ Researcher       │  │
│  │ Editor              │  │ Mayor                │  │ Structurer       │  │
│  │ Writer              │  │ Ledger               │  │ Visualizer       │  │
│  │ Synthesizer         │  │                      │  │                  │  │
│  │                     │  │ Purpose: Ensure      │  │ Purpose: Explore │  │
│  │ Purpose: Convert    │  │ safety, prevent      │  │ & map evidence   │  │
│  │ ideas → deliverable │  │ fraud, prove         │  │                  │  │
│  │                     │  │ decisions            │  │                  │  │
│  └─────────────────────┘  └──────────────────────┘  └──────────────────┘  │
│  ┌─────────────────────┐  ┌──────────────────────┐                          │
│  │   CREATIVE          │  │   EXECUTION          │                          │
│  │   SUPERTEAM         │  │   SUPERTEAM          │                          │
│  │                     │  │                      │                          │
│  │ Lateral Pattern     │  │ Synthesizer          │                          │
│  │ Music Rhythm        │  │ Scheduler            │                          │
│  │                     │  │ Registry             │                          │
│  │ Purpose: Lateral    │  │                      │                          │
│  │ exploration +       │  │ Purpose: Timing &    │                          │
│  │ dopamine loop       │  │ coordination         │                          │
│  └─────────────────────┘  └──────────────────────┘                          │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
        ↓
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                    AGENT ROLES (Layer 1)                                    │
│              Single Responsibility, Atomic Units                            │
│                                                                              │
│  OPERATIONAL ROLES (Do Work)                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Researcher   │  │ Writer       │  │ Structurer   │  │ Skeptic      │   │
│  │              │  │              │  │              │  │              │   │
│  │ Gather       │  │ Draft prose  │  │ Design       │  │ Attack       │   │
│  │ facts,       │  │ from         │  │ outline,     │  │ claims,      │   │
│  │ cite         │  │ accepted     │  │ organize,    │  │ find holes   │   │
│  │ sources      │  │ claims       │  │ flow         │  │ & gaps       │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │ Visualizer   │  │ Synthesizer  │                                        │
│  │              │  │              │                                        │
│  │ Create       │  │ Merge        │                                        │
│  │ diagrams,    │  │ overlapping  │                                        │
│  │ tables,      │  │ claims,      │                                        │
│  │ charts       │  │ eliminate    │                                        │
│  │              │  │ duplicates   │                                        │
│  └──────────────┘  └──────────────┘                                        │
│                                                                              │
│  COORDINATIVE ROLES (Orchestrate)                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Foreman      │  │ Editor       │  │ Mayor        │  │ Scheduler    │   │
│  │              │  │              │  │              │  │              │   │
│  │ Assign work, │  │ Cut          │  │ Governance   │  │ Track        │   │
│  │ curate       │  │ ruthlessly,  │  │ veto,        │  │ timing,      │   │
│  │ claims       │  │ finalize     │  │ freeze state │  │ deadlines    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  DATA ROLES (Immutable Record)                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │ Ledger       │  │ Registry     │  │ Claim Market │                     │
│  │              │  │              │  │              │                     │
│  │ Decision log,│  │ Agent        │  │ Pending /    │                     │
│  │ hashes,      │  │ manifest,    │  │ Accepted /   │                     │
│  │ signatures   │  │ signer list  │  │ Merged claims│                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Relationship Map (How Layers Connect)

```
Your Work Session (Top → Bottom Flow)

1. YOU INITIATE
   ↓
2. CHOOSE A DISTRICT
   "I'm working in FOUNDRY" or "CREATIVE" or "MUSIC"?
   ↓
3. ASSIGN SUPERTEAM(S)
   "Which superteam does this task need?"
   Production? Governance? Knowledge? Creative?
   ↓
4. SPAWN AGENT ROLES
   "What LEGO1 roles does this superteam need?"
   ↓
5. ROLES PRODUCE CLAIMS
   "Claims are the coordination unit (not chat)"
   ↓
6. KERNEL ENFORCES
   "Constitutional rules apply automatically"
   ↓
7. ARTIFACT SHIPS (or aborts)
   "Editor decides. No revision loops."
   ↓
8. LEDGER RECORDS
   "Every decision logged, verifiable, deterministic"
```

---

## Bottom-Up Scaling (Build Complexity)

```
Start: Single role (Researcher)
  ↓
Combine: Researcher + Writer (Knowledge flow)
  ↓
Assemble: Researcher + Writer + Structurer = Knowledge Superteam
  ↓
Specialize: Knowledge Superteam → Science District (own rhythm)
  ↓
Scale: Add Governance superteam to Science District (rules enforced)
  ↓
Replicate: Clone Science District for new topic
  ↓
Kernel: All districts coordinate through constitutional rules
```

---

## CONQUEST Integration (Testing the Stack)

```
CONQUEST MVP

  WORLD MODEL (Plateau + Agents + Governance)
       ↓
  ┌────────────────────────────────────────────────┐
  │                                                │
  │  NPC Agents (LEGO1 roles)                     │
  │  ├─ Defender (hold territory)                 │
  │  ├─ Claimer (propose new territory)           │
  │  ├─ Judge (Editorial role)                    │
  │  └─ Mood Tracker (Music rhythm)               │
  │                                                │
  └────────────────────────────────────────────────┘
       ↓
  ┌────────────────────────────────────────────────┐
  │                                                │
  │  Superteams (LEGO2)                           │
  │  ├─ Combat (Claimer + Defender + Judge)      │
  │  ├─ Governance (K-gates + Ledger)             │
  │  └─ Energy (Mood Tracker + Food)              │
  │                                                │
  └────────────────────────────────────────────────┘
       ↓
  ┌────────────────────────────────────────────────┐
  │                                                │
  │  Districts (LEGO3)                            │
  │  ├─ FOUNDRY (territory claims, 5-phase)      │
  │  ├─ MUSIC (food/mood cycles, rhythm)         │
  │  ├─ SCIENCE (logging, Ledger, evaluation)    │
  │  └─ UZIK (card design, visual coherence)     │
  │                                                │
  └────────────────────────────────────────────────┘
       ↓
  ┌────────────────────────────────────────────────┐
  │                                                │
  │  Kernel (LEGO4)                               │
  │  ├─ K-gates (prevent NPC self-modification)  │
  │  ├─ Constitutional rules (NPCs cannot cheat)  │
  │  ├─ Ledger (every action logged)              │
  │  └─ Deterministic replay (same input → output)│
  │                                                │
  └────────────────────────────────────────────────┘
       ↓
  CARD DUEL (Game Loop)
  Card play = Claim
  Defense = Counter-claim
  Verdict = Editorial decision
```

---

## Your Brain ↔ System Alignment

```
ADHD Trait              System Component       Function
────────────────────────────────────────────────────────
Hyperfocus              LEGO1 + LEGO2          Roles stay atomic (no drift)
Lateral jumping         Districts              Separate rhythms (no collision)
Pattern matching        Creative District      Lateral channel
Perfectionism           Editorial Authority    Editor cuts; you ship
Context loss            Ledger                 Everything logged (searchable)
Dopamine loop           Music District         Rhythm enforced
Endless revision        Phase 4 Boundary       FINAL (no loops)
Authority blending      Role Separation        No merging responsibilities
```

---

## Decision Tree (Which Level Am I On?)

```
I have a task.

├─ Is it a single, bounded responsibility?
│  ├─ YES → LEGO1 (agent role). Describe in 2 sentences.
│  └─ NO  → Continue.
│
├─ Does it combine 2-6 roles for ONE purpose?
│  ├─ YES → LEGO2 (superteam). List the roles.
│  └─ NO  → Continue.
│
├─ Does it specialize superteams + control rhythm?
│  ├─ YES → LEGO3 (district). Name superteams.
│  └─ NO  → Continue.
│
└─ Am I designing kernel rules themselves?
   ├─ YES → LEGO4 (kernel). Update Constitutional rules.
   └─ NO  → You're missing a level. Decompose further.
```

---

## The Full Cycle (Session → Artifact → Ledger)

```
SESSION START
  │
  ├─ Declare subject + duration + district
  │  ↓
  ├─ EXPANSION PHASE (hyperfocus, produce claims)
  │  │ Roles: all produce claims (no gatekeeping)
  │  │ Output: Pending claims in Claim Market
  │  ↓
  ├─ BREAK (15 min mandatory, micro-rest)
  │  ↓
  ├─ SELECTION PHASE (Skeptic challenges, select accepts)
  │  │ Roles: Foreman curates, Skeptic attacks
  │  │ Output: Accepted claims
  │  ↓
  ├─ DRAFTING PHASE (Writer + Structurer produce prose)
  │  │ Roles: Writer drafts, Structurer flows, Synthesizer merges
  │  │ Output: v1_draft
  │  ↓
  ├─ EDITORIAL COLLAPSE (Editor cuts 30-50%)
  │  │ Roles: Editor only (unilateral authority)
  │  │ Output: v2_editorial (final)
  │  ↓
  ├─ TERMINATION (Editor decides)
  │  │ Outcome: ✅ SHIP (artifact ready)
  │  │ Outcome: ❌ ABORT (insufficient; replan)
  │  ↓
  ├─ LEDGER RECORD (log every decision)
  │  │ "Who, What, Why, When, Outcome"
  │  │ Hash: deterministic verification
  │  ↓
  SESSION END
```

---

## Scaling Example: Add "Mood Tracker" Role

**Step 1: Define LEGO1 (Atomic Role)**
```
Role: Mood Tracker
Responsibility: Track energy level, detect burnout risk
Does NOT: Schedule, make decisions, override authority
Test: 2-sentence description? ✓
```

**Step 2: Combine into LEGO2 (Superteam)**
```
Superteam: Music
Roles: Mood Tracker + Rhythm Coordinator
Purpose: Energy management + cycle enforcement
```

**Step 3: Specialize into LEGO3 (District)**
```
District: Music District
Superteams: Music + Creative
Responsibility: Track weekly energy cycles, enforce breaks
Rhythm: Weekly review (Monday 9am)
```

**Step 4: Kernel Applies Automatically**
```
Constitutional Rule: Mood Tracker cannot self-modify state
K-gate: Energy level change requires Scheduler approval
Ledger: Every mood entry logged with timestamp
Result: Burnout prevention is now enforced, not optional
```

---

## What NOT to Do

| Anti-Pattern | Why It Fails | System Fix |
|---|---|---|
| **Role Creep** | Skeptic also writes prose | LEGO1 boundaries immutable |
| **Authority Blending** | Foreman also finalizes | Editor has sole power |
| **Sprawl** | Working on 7 topics | Hard scope at start |
| **Endless Revision** | Phase 3 → Phase 2 → Phase 1 | Phase 4 (Editorial) is final |
| **Context Loss** | Restart, forget why | Ledger is searchable |
| **Burnout** | Hyperfocus >8h no break | Music District enforces breaks |
| **Silent Failure** | Work disappears | Ledger records everything |
| **Consensus Loop** | Debating forever | Editor decides unilaterally |

---

**Last Updated:** 2026-02-12
**Status:** Full visualization complete; all 4 LEGO levels integrated; CONQUEST seed project validated against stack
