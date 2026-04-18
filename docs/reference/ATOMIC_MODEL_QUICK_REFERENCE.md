# Atomic Intelligence Model: Quick Reference Card

## The Four LEGO Levels (Build Upward)

```
┌─────────────────────────────────────────────────────┐
│ LEGO4: KERNEL (Scalable, Self-Enforcing)           │
│  └─ Constitutional rules, K-gates, Ledger          │
│     (Every layer enforces itself)                    │
└─────────────────────────────────────────────────────┘
          ↑
┌─────────────────────────────────────────────────────┐
│ LEGO3: DISTRICT (Expertise Cluster, Own Rhythm)    │
│  └─ Foundry, Creative, Science, Music, Uzik        │
│     (Specializes superteams + enforces rhythm)      │
└─────────────────────────────────────────────────────┘
          ↑
┌─────────────────────────────────────────────────────┐
│ LEGO2: SUPERTEAM (Functional Domain)               │
│  └─ Production, Governance, Knowledge, Creative    │
│     (Combines 2-6 roles for one clear purpose)      │
└─────────────────────────────────────────────────────┘
          ↑
┌─────────────────────────────────────────────────────┐
│ LEGO1: AGENT ROLE (Atomic Unit)                    │
│  └─ Researcher, Skeptic, Writer, Editor, Foreman  │
│     (Single responsibility, no overlap)             │
└─────────────────────────────────────────────────────┘
```

---

## LEGO1: Agent Roles (Atomic Units)

| Role | Responsibility | Does NOT Do |
|---|---|---|
| **Researcher** | Gather facts, cite sources | Interpret, decide, write |
| **Skeptic** | Attack claims, find holes | Provide solutions |
| **Structurer** | Design outline, organize | Write prose, invent content |
| **Writer** | Draft prose from claims | Invent facts, decide structure |
| **Synthesizer** | Merge overlapping claims | Add new ideas, rewrite |
| **Visualizer** | Create diagrams, tables | Interpret, add meaning |
| **Foreman** | Assign work, curate claims | Write final content, override Editor |
| **Editor** | Cut ruthlessly, finalize | Explore, debate, seek consensus |

**Test:** If role description needs an "or", it's not atomic. Split it.

---

## LEGO2: Superteams (2-6 Roles + One Purpose)

| Superteam | Roles | Purpose | Output |
|---|---|---|---|
| **Production** | Foreman + Editor + Writer + Synthesizer | Ideas → Deliverable | Document/Code |
| **Governance** | Skeptic + Mayor + Ledger | Safety + Proof | Decision Log |
| **Knowledge** | Researcher + Structurer + Visualizer | Explore + Map | Facts + Diagrams |
| **Creative** | Lateral Pattern + Music Rhythm | Lateral + Dopamine | Insights + Rhythm |
| **Execution** | Synthesizer + Scheduler + Registry | Timing + Coordination | Timeline |

**Test:** Can this team finish a task without other teams? If not, incomplete.

---

## LEGO3: Districts (Superteams + Own Rhythm)

| District | Superteams | Responsibility | Rhythm | When to Use |
|---|---|---|---|---|
| **FOUNDRY** | Production + Governance + Knowledge | Transform disagreement → artifact | 5-phase pipeline | Hard production work |
| **CREATIVE** | Creative + Lateral | Lateral exploration + pattern | Hyperfocus cycles | Lateral exploration, dopamine loop |
| **SCIENCE** | Knowledge + Governance | Evidence gathering + validation | Continuous | Building fact repository |
| **MUSIC** | Creative + Rhythm | Energy management + cycles | Weekly tracking | Prevent burnout, track mood |
| **UZIK** | Creative + Visualizer | Design systems + aesthetics | Per-sprint | Visual/card design work |

**Test:** Can you run this district independently? If not, needs parent district.

---

## LEGO4: Kernel (Constitutional Rules)

**What it enforces:**

| Rule | Why | Example |
|---|---|---|
| **No Self-Ratification** | Proposer ≠ Validator | Writer doesn't approve Writer's prose |
| **Role Boundaries Immutable** | LEGO1 cannot merge | Skeptic stays in lane; doesn't fix |
| **Authority Separation** | No blending | Foreman ≠ Editor (distinct powers) |
| **All Changes Logged** | Verifiable | Ledger records every decision |
| **Fail-Closed Default** | Safety first | Missing evidence → REJECT |
| **Deterministic Replay** | Reproducible | Same input → same output always |

**Result:** System enforces its own rules. No one can cheat.

---

## How Lateral Thinking Fits

```
Your Brain          →    System Component    →    Output
──────────────────────────────────────────────────────────
Hyperfocus          →    LEGO1 + LEGO2       →    Atomic roles stay focused
Lateral jumping     →    Districts            →    Separate rhythms, no collision
Pattern matching    →    Creative District   →    Lateral exploration channel
Perfectionism       →    Editorial Authority →    Editor cuts; you can't revise
Context loss        →    Ledger              →    Everything logged; no scrambling
Dopamine loop       →    Music District      →    Rhythm tracked; breaks enforced
```

---

## CONQUEST: Where It All Comes Together

```
CONQUEST MVP Architecture
├─ LEGO1: NPC Agents (Defender, Claimer, Judge)
├─ LEGO2: Superteams (Combat, Governance, Energy)
├─ LEGO3: Districts (Foundry, Music, Science, Uzik)
├─ LEGO4: Kernel (K-gates prevent NPC self-modification)
└─ Output: Card duel game + Ledger log + Next steps

Why Test in CONQUEST?
├─ Validates atomic roles work in practice
├─ Proves superteams can coordinate without chat
├─ Tests district rhythms don't collide
├─ Checks K-gates hold under game pressure
└─ Generates Ledger for Science District to analyze
```

---

## Decision Tree: Which LEGO Level Am I Working On?

```
START: I have a task.

┌─ Is it a SINGLE, BOUNDED responsibility?
│  ├─ YES → LEGO1 (agent role). Define it in 2 sentences.
│  └─ NO  → Continue
│
├─ Does it combine 2-6 roles for ONE purpose?
│  ├─ YES → LEGO2 (superteam). Name the roles.
│  └─ NO  → Continue
│
├─ Does it specialize superteams + control rhythm?
│  ├─ YES → LEGO3 (district). Name the superteams.
│  └─ NO  → Continue
│
└─ Are you designing the kernel rules themselves?
   ├─ YES → LEGO4 (kernel). Update Constitutional rules.
   └─ NO  → You're missing a level. Decompose further.
```

---

## Dopamine Loop (Lateral Thinking Rhythm)

| Phase | Duration | Activity | Brain State | Output |
|---|---|---|---|---|
| **EXPAND** | 4h max | Hyperfocus, lateral exploration | Hyperfocus on | Raw claims |
| **BREAK** | 15 min | Away from keyboard | Reset | Energy restored |
| **SELECT** | 30-60 min | Prune beautiful distractions | Fresh eyes | Accepted claims |
| **SHIP** | Variable | Convert claims → deliverable | Flow state | Finished artifact |
| **REST** | 24h+ | No work, let brain process | Recovery | Next hyperfocus ready |

**Golden rule:** Don't skip BREAK. Hyperfocus >6h without break = burnout.

---

## Scaling Rule: LEGO1 → Kernel

**How to scale without redesigning:**

1. **Define a new LEGO1 role** (single responsibility)
2. **Combine into LEGO2 superteam** (2-6 roles)
3. **Specialize with LEGO3 district** (add rhythm)
4. **Kernel handles the rest** (constitutional rules apply automatically)

**Example: Adding "Mood Tracker" role**
- LEGO1: Mood Tracker (track energy, detect burnout)
- LEGO2: Music Superteam (Mood + Rhythm)
- LEGO3: Music District (enforces weekly cycles)
- LEGO4: Kernel automatically enforces no self-edit on mood state

**Result:** New capability, no kernel redesign.

---

## Memory Triggers (For Next Session)

**If you feel scattered:**
"Which district am I working in? Is my rhythm colliding with another?"

**If you revise endlessly:**
"Editor decided. SHIP. No more revision."

**If you're over-engineering:**
"What's the LEGO1 role? Am I merging roles that should stay separate?"

**If you lose context:**
"Check the Ledger. It logged why I made this decision."

**If you're getting tired:**
"Music District says break. Step away. Now."

---

**Last Updated:** 2026-02-12
**Print this.** Reference it. Live by it.
