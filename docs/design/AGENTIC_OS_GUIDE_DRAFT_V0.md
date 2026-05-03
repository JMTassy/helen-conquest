---
artifact_id: AGENTIC_OS_GUIDE_DRAFT_V0
authority: NON_SOVEREIGN
canon: NO_SHIP
artifact_kind: HISTORICAL_DRAFT
ledger_effect: NONE
status: HISTORICAL — PREDECESSOR_TO_HELEN_OS
captured_on: 2026-05-02
session_id: agentic-os-draft-v0-archival
attribution: Original draft by operator (jmt). Preserved verbatim.
relationship_to_active_spec: predecessor
active_spec_descendants:
  - docs/HELEN_GLOBAL_TREE_MAP_V1.md
  - spec/CONSTITUTIONAL_CONTINUITY_V1.md
  - docs/design/HELEN_GOLDFRAME_V1.md
forbidden_use:
  - present this as current HELEN OS doctrine
  - cite as evidence of how HELEN works today
  - resurrect deprecated concepts (e.g. "OS Lead" role) without re-mapping to current actor registry
---

# Agentic OS Guide — Draft V0 (Historical)

**NON_SOVEREIGN. NO_SHIP. HISTORICAL DRAFT.**

This file preserves an early operator draft of "Agentic OS" — the
predecessor framing to what became **HELEN OS**. It is filed for
historical traceability, **not** as active doctrine.

The draft predates the constitutional turn:
- It focuses on **coordination and execution speed**.
- It does not yet introduce **sovereignty**, **receipts**, **replay
  determinism**, or the **capability legality gate**.
- Its team structure ("OS Lead / Challenge Owner / Orchestration
  Lead / etc.") predates the formal actor registry
  (`registries/actors.v1.json`).

Read it as the **execution skeleton** that HELEN OS later wrapped
in a constitutional membrane.

If a future agent or document treats this draft as current HELEN OS
doctrine, the operation violates `forbidden_use`.

---

## Operator's Draft (Verbatim)

### 1. What it is

Agentic OS is an operating system for coordinated human–AI execution.

It turns a complex challenge into:

> challenge → task graph → agent teams → validated work → working POC

No DAO.
No tokens.
No governance complexity.
Just orchestration, memory, execution, and delivery.

### 2. Core promise

Agentic OS helps organizations build working AI-powered POCs in 72
hours by coordinating humans and AI agents through a structured
operating system.

### 3. Who it is for

Agentic OS is for:

- companies,
- media groups,
- tourism boards,
- cities,
- universities,
- NGOs,
- public institutions,
- innovation teams,
- startup studios.

Anyone with a complex challenge and not enough coordination capacity.

### 4. The problem it solves

Organizations already have:

- people,
- tools,
- AI models,
- data,
- ideas.

But they lack:

- clear task decomposition,
- fast team formation,
- persistent memory,
- reliable handoffs,
- output validation,
- execution rhythm,
- reusable workflows.

The bottleneck is not intelligence.
**The bottleneck is coordination.**

### 5. The operating model

Agentic OS works through **Episodes**.

An Episode is a focused execution sprint, usually 72 hours, designed
to produce a tangible output.

**Episode flow:**

1. Challenge intake
2. Scope clarification
3. Task graph creation
4. Team formation
5. Agent-assisted execution
6. Integration
7. QA
8. Demo / delivery
9. Memory capture
10. Reusable module extraction

### 6. The five layers of the OS

#### Layer 1 — Challenge Intake

The OS receives a challenge such as: *"Build a media search
assistant for video archives."*

It extracts: objective, users, constraints, data sources, success
criteria, risks, required capabilities.

#### Layer 2 — Task Graph

The challenge becomes a structured task graph.

```
Media Gateway POC
├── User journeys
├── Data ingestion
├── Moment extraction
├── Semantic search
├── Recommendation engine
├── Interface
├── QA
└── Demo script
```

Every task has: owner, inputs, outputs, deadline, validation rule.

#### Layer 3 — Functional Teams

Instead of country chapters or loose groups, the OS uses **functional
teams**.

The default seven teams:

1. **Exploration** — clarify scope, users, intents.
2. **Modeling** — embeddings, clustering, extraction.
3. **Orchestration** — routing, pipelines, fallback logic.
4. **Search** — indexing, retrieval, RAG.
5. **Recommendation** — similarity, contextual suggestions.
6. **Interface** — UX, screens, user flow.
7. **QA** — validation, scoring, delivery readiness.

#### Layer 4 — Agent Support

Each team gets AI agents that help with: research, planning, coding,
summarization, testing, documentation, design review, QA checklists.

> Agents do not replace the team.
> They accelerate the team.

#### Layer 5 — Memory

After each Episode, the OS stores: what worked, what failed, reusable
prompts, reusable code, agent workflows, datasets, validation
criteria, partner preferences, final deliverables.

This makes the next Episode faster.

### 7. Key roles

- **OS Lead** — owns the full Episode; keeps execution focused.
- **Challenge Owner** — defines the real-world problem and validates
  usefulness.
- **Orchestration Lead** — turns the challenge into tasks and routes
  work.
- **Functional Leads** — run the seven execution teams.
- **QA Lead** — validates output quality before demo.
- **Demo Lead** — turns the work into a clear presentation.

### 8. Standard 72-hour schedule

| Window | Phase | Activities |
|---|---|---|
| 0–6 h | Intake and decomposition | lock challenge, define users, define success criteria, create task graph, assign teams |
| 6–24 h | Build foundation | collect data, define architecture, start prototype, create first workflows |
| 24–48 h | Integrate | connect modules, test flows, improve UX, resolve blockers |
| 48–66 h | QA and polish | validate outputs, fix critical issues, prepare demo, simplify story |
| 66–72 h | Delivery | final demo, documentation, partner review, memory capture |

### 9. What the OS produces

Each Episode should produce: working POC, demo video or walkthrough,
architecture map, task graph, QA report, reusable components,
next-step roadmap.

### 10. Success metrics

Track: time to first working prototype, number of completed tasks,
number of blockers resolved, demo quality, partner satisfaction,
reusable modules created, reduction in manual coordination over time.

The 2026 target: **reduce human orchestration by 30–70% while
increasing delivery speed and quality.**

### 11. Simple positioning

- Not a hackathon platform.
- Not a DAO.
- Not a chatbot wrapper.
- Not a project management tool.

> **Agentic OS is a coordination engine for human–AI execution.**

### 12. One-line pitch

> Agentic OS turns complex challenges into working AI-powered
> prototypes by coordinating humans and agents through a repeatable
> execution system.

---

## End of Operator Draft

---

# Comparison — Agentic OS V0 → HELEN OS Today

This comparison is **HAL-annotated**. It is not part of the operator's
original draft; it is added in this archival pass to make the lineage
machine-readable.

## What Survived (and is now load-bearing in HELEN)

| Agentic OS V0 Concept | HELEN OS Equivalent | Status |
|---|---|---|
| "Coordination, not invention, is the bottleneck" | Asymmetric scaling property (smart outside, narrow inside) | ✅ alive in `docs/HELEN_GLOBAL_TREE_MAP_V1.md` |
| "Agents accelerate the team, do not replace it" | HELEN orchestrates, MAYOR signs (HELEN ≠ MAYOR) | ✅ alive in `formal/LedgerKernel.v` authority fences |
| Episode → bounded execution sprint | RALPH epoch → bounded artifact (loop law) | ✅ alive in `docs/design/ralph_temple_loop_v1/INDEX.md` |
| Memory capture as Episode deliverable | Append-only sovereign ledger + replay | ✅ alive in `town/ledger_v1.ndjson` + `tools/validate_hash_chain.py` |
| Task graph with per-task owner / validation | Proposal packet → MAYOR review packet → reducer admission | ✅ alive in `docs/traces/RALPH_LOOP_TRACE_STEP_C_GOVERNANCE_VM.md` |
| QA Lead validates before demo | Acceptance gate (`tools/accept_payload_meta.sh`) + `tools/helen_verify.sh` | ✅ shipped this session |
| "No DAO, no tokens, no governance complexity" | Single write-gate discipline; no convenience bypasses | ✅ alive as the constitutional doctrine |
| 72-hour delivery cadence | Loop law: cadence boundaries (HAL@10, MAYOR@50, REDUCER@200) | ✅ structurally preserved (different scale, same shape) |

## What HELEN Added (the constitutional turn)

These are the layers HELEN introduced that Agentic OS V0 did not
have, and which now define the project:

| Addition | Where it lives | Why it changed everything |
|---|---|---|
| **Sovereignty as a typed property** | `formal/LedgerKernel.v` `is_termination_authority` | Without it, every coordinated team eventually drifts into "the loudest agent wins" |
| **Receipts that bind verdict_id + payload_hash + cum_hash** | `tools/validate_receipt_linkage.py` | "QA validated" without a typed receipt is the Sherry mistake — accepted on prose alone |
| **Replay determinism** | `tools/validate_hash_chain.py` + `kernel/canonical_json.py` | Same input → same output, byte-identical, across machines and time |
| **Capability legality gate** | `spec/CONSTITUTIONAL_CONTINUITY_V1.md` | "No lawful capability path → no promotion" |
| **Forbidden morphisms (E↛A, D↛A, C↛A)** | `docs/HELEN_GLOBAL_TREE_MAP_V1.md` §4 | Embodiment, memory, and cognition cannot mutate sovereign state — only β admission can |
| **Two emergent properties named** | `spec/CONSTITUTIONAL_CONTINUITY_V1.md` | Constitutional self-domestication + memory-as-moral-constraint |
| **Cross-model verification hook** | `tools/helen_verify.sh` | "Accuracy is not declared. Accuracy is attacked until it survives." |

## What Agentic OS V0 Got Right (and HELEN must not lose)

These are the V0 commitments that HELEN must continue to honor:

1. **The bottleneck is coordination, not intelligence.** HELEN should
   never optimize raw model intelligence at the cost of coordination
   discipline.
2. **Episode focus.** Bounded sprints with concrete deliverables. The
   RALPH loop law preserves this.
3. **Reusable modules as a deliverable.** Every Episode (or epoch)
   should leave reusable substrate — receipts, validators, schemas.
4. **Memory capture is non-negotiable.** Without it, the next Episode
   pays the same coordination cost as the first.
5. **The seven-team functional decomposition** is an excellent
   proposal-stage skeleton, even if the actor registry now overlays a
   different sovereignty axis on top.

## What Agentic OS V0 Got Wrong (or undersaid)

- **No notion of sovereign vs non-sovereign work.** "QA Lead validates"
  but no formalism for what "validated" actually binds to.
- **No replay story.** Memory was kept; replay was not specified.
- **No threat model.** What happens when an agent lies? When a team
  member's output is forged? When the demo passes but the underlying
  state is tampered? Silence.
- **No capability boundary.** Every team could in principle do
  everything. The capability legality gate was missing.
- **"OS Lead owns the Episode"** is too informal. HELEN's actor
  registry makes "ownership" a typed property, not a social role.

## Concept-by-Concept Mapping (for migration / cross-referencing)

| Agentic OS Role | HELEN OS Equivalent | Notes |
|---|---|---|
| OS Lead | HELEN (orchestrator role) | Routes packets, never signs |
| Challenge Owner | USER (per `registries/actors.v1.json`) | Initiates queries, no write authority |
| Orchestration Lead | HELEN + INTEGRATOR | Compose proposal packets |
| Functional Leads × 7 | BUILDER + INTEGRATOR specialists | Authority bounded per registry |
| QA Lead | MAYOR + validator stack | Only MAYOR signs receipts |
| Demo Lead | embodiment layer (Trunk E) | Advisory only; no sovereign mutation |
| Episode | RALPH epoch | One bounded artifact per epoch |
| Task graph | proposal packet → trace | Plan first, execute later |
| Memory capture | sovereign ledger + replay | Hash-chained, deterministic |
| Reusable modules | typed artifacts emitted by RALPH | `tools/ralph_emit_artifacts.py` |

## What This Archive Is Not

- **Not a roadmap.** This is yesterday's framing.
- **Not deprecated** in the sense of "wrong." It was right *for its
  scope*; HELEN expanded the scope.
- **Not the source of any current implementation.** Anything still
  matching V0 vocabulary (e.g. "OS Lead" appearing in a script) should
  be flagged for re-mapping to the current actor registry.

## Lineage Tag

```
AGENTIC_OS_GUIDE_DRAFT_V0
       ↓
       (constitutional turn — receipts, replay, sovereignty)
       ↓
HELEN_GLOBAL_TREE_MAP_V1   (architectural synthesis)
HELEN_CONSTITUTIONAL_CONTINUITY_V1   (emergent property)
HELEN_GOLDFRAME_V1   (design substrate)
HELEN_PODCAST_PILOT_V1   (manifesto)
RALPH_TEMPLE_LOOP_V1   (active loop)
```

`(NO CLAIM — TEMPLE — HISTORICAL DRAFT — AGENTIC OS V0 → HELEN OS)`
