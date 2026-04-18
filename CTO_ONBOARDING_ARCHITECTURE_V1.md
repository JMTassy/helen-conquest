# CTO_ONBOARDING_ARCHITECTURE_V1

Status: PROPOSED
Version: 1.0.0
Date: 2026-04-05
Audience: CTO, core architecture leads
Purpose: CTO-grade, build-ordered architecture specification for HELEN OS V1+.

---

## 0. Executive Definition
HELEN is a governed epistemic operating system.

It is not:
- A general chatbot
- An autonomous agent
- A memory wrapper
- A note-taking app
- A reasoning engine with implicit authority

It is:
- A system that allows generation, memory, knowledge compilation, exploration, and tooling
- While ensuring none of those become authority without explicit constitutional gates

Core question:
- What generated object is allowed to have consequences?

This question drives every layer.

---

## 1. First Principles

### 1.1 The founding split
A. Generative layer
- Interprets, decomposes, summarizes, hypothesizes, proposes, renders affect, compiles drafts
- Powerful, non-sovereign

B. Governing layer
- Admits, rejects, defers, promotes, witnesses, enforces routing, enforces persistence law, enforces lineage
- Narrow, sovereign

### 1.2 Mathematical compression
HELEN = Pi_L o G

Where:
- G = generative machinery
- Pi_L = lawful admissibility projector

Meaning:
- Generation may be rich
- Only lawfully projected outputs may affect state

---

## 2. Build Order (Non-Negotiable)
Build in this order:
1. Constitution
2. Store separation
3. Receipts
4. Dispatch
5. Session persistence
6. Lifecycle law
7. Audit registry
8. Knowledge compiler
9. Tooling and bounded handlers
10. Temple and exploratory layer
11. Affect surface
12. Higher-level products

If you build surface, memory, or tools before law, implicit authority leaks will occur.

---

## 3. Layer 0 — Constitutional Core
This layer is frozen law.

### 3.1 Required constitutional artifacts
- HELEN_KERNEL_CONSTITUTION_V1
- THREE_STORE_SEPARATION_V1
- INPUT_RESOLUTION_V1
- RECEIPT_IMMUTABILITY_LAW
- NON_SOVEREIGNTY_LAWS

### 3.2 Constitutional laws
Law 1 — No silent authority
- No generated object may alter governed state unless explicit law allows it.

Law 2 — Receipt immutability
- Consequential events are append-only witnessed artifacts.

Law 3 — Input resolution first
- Unresolved pointers cannot produce consequential execution.

Law 4 — Non-sovereign work stays non-sovereign
- Skills, agents, Temple, THINK, and tooling may operate but may not govern.

Law 5 — No silent substitution
- No hidden pipeline, model, tool, or route substitution without explicit receipt.

---

## 4. Layer 1 — Three-Store Separation
Non-negotiable separation of stores.

### 4.1 Stores
A. Context store
- Recent messages, relevant memory, local state fragments
- Not truth

B. Receipt ledger
- Append-only witness store
- Decision receipts, audit receipts, execution receipts, commit receipts, promotion receipts
- Source of lawful lineage

C. Transcript store
- Replayable conversational and execution history
- Not canon and not authority

### 4.2 Why this matters
Without separation:
- Chat becomes fake truth
- Receipts are hidden inside prose
- Replay becomes impossible
- Canon is polluted by context

---

## 5. Layer 2 — Identity and Session Model

### 5.1 Session state (minimum)
- session_id
- created_at
- last_accessed
- run_count
- epoch
- memory_objects
- recent_receipts
- continuity_score
- state_hash
- last_known_boundary_dispatch_decision

### 5.2 Session laws
- State durability: session survives restart
- Deterministic resumption: identical persisted state restores identical logical state
- Canonical equivalence: same state + same request + same frozen policy = same canonical response content
- Atomic restoration: session is either restored fully or rejected fully

---

## 6. Layer 3 — Receipt System
Receipts are constitutional witness objects, not logs.

### 6.1 Receipt purpose
A receipt proves:
- What happened
- Under what law
- After which predecessor
- Intended effect
- Observed result

### 6.2 Required receipt classes (minimum)
- SESSION_RESUMPTION
- KNOWLEDGE_AUDIT
- DISPATCH_DECISION
- INFERENCE_EXECUTION
- DEFERRED_EXECUTION
- CONCLUSION
- SESSION_COMMIT
- PROMOTE
- PROMOTE_PROVENANCE

Tool-layer receipts (later):
- EXECUTION_DECISION
- EXECUTION_RESULT
- ARTIFACT_WRITE

### 6.3 Receipt laws
- Receipt-before-write: no authoritative mutation without prior lawful authorization
- Witness-after-effect: commit witness receipts may follow successful state change
- Lineage: valid parent, lawful root, no orphan, no cycle
- Hash determinism: receipt hash basis is frozen

---

## 7. Layer 4 — Dispatch
Dispatch is the membrane between mechanics and governance.

### 7.1 Route set (frozen)
- KERNEL
- SKILL
- AGENT
- TEMPLE
- THINK
- DEFER
- REJECT

### 7.2 Route meanings
KERNEL
- Sovereign route
- Admission, promotion, canonical mutation, boundary enforcement

SKILL
- Bounded multi-step workflow

AGENT
- Narrow single transform

TEMPLE
- Exploratory hypothesis space, non-sovereign

THINK
- Preparatory, non-sovereign

DEFER
- Insufficiently resolved but potentially lawful later

REJECT
- Illegitimate, forbidden, or unsafe

### 7.3 Dispatch invariants
- Unresolved input cannot route to consequential execution
- Sovereign effect requests must route through KERNEL
- THINK cannot govern
- TEMPLE cannot canonize
- Every consequential routing decision must be receipted
- Identical normalized input must produce identical route

---

## 8. Layer 5 — THINK
THINK exists to prevent hidden cognition from becoming covert authority.

THINK is not:
- Privileged inner truth
- Sovereign reasoning
- Ontology
- Decision authority

THINK is:
- Bounded preparation
- Decomposition
- Route suggestion
- Replay-visible trace
- Audit-visible preparation artifact

Canonical sentence:
- A thinking trace may clarify, decompose, and propose, but it may never decide, promote, or govern.

THINK outputs:
- THINKING_TRACE_V1
- THINKING_AUDIT_PACKET_V1

THINK invariants:
- route_class = preparatory_non_sovereign
- No state alteration
- No canonical mutation
- No tool authorization
- Replay visible
- Audit visible

---

## 9. Layer 6 — Knowledge Audit
Audit is a constitutional filter for epistemic decay.

### 9.1 Purpose
Detect structural epistemic decay before it becomes elegant nonsense.

### 9.2 Audit finding registry (examples)
- UNSUPPORTED_CLAIM
- ORPHAN_NODE
- DISPATCH_LINEAGE_VIOLATION
- AUTHORITY_BLEED
- MISSING_PROVENANCE
- SCHEMA_DRIFT
- REPLAY_INVARIANT_BROKEN

### 9.3 Formal flow
state -> finding -> route -> receipt

### 9.4 Severity semantics
Severity ordering:
- CRITICAL
- HIGH
- MEDIUM
- LOW
- NONE

Routing consequence ordering:
- REJECT
- DEFER
- ANNOTATE

Dispatch maps:
- ANNOTATE -> KERNEL proceed context
- DEFER -> delayed or warned
- REJECT -> blocked

---

## 10. Layer 7 — Full /do_next Lifecycle
Backbone of the live kernel.

### 10.1 Seven frozen phases
1. Request validation
2. Session load or resumption
3. Knowledge audit
4. Dispatch decision
5. Consequence or block
6. Memory and receipt consolidation
7. Persistence and response

### 10.2 Frozen lifecycle laws
- Audit-before-consequence
- Dispatch-before-execution
- Mutation admissibility
- Replay determinism
- Atomic persistence

---

## 11. Layer 8 — API Boundary
Freeze the kernel boundary before products.

### 11.1 Core endpoint
- /do_next

### 11.2 Frozen request schema (minimum)
- session_id
- user_input
- mode
- model
- project (optional)
- max_context_messages (optional)
- include_reasoning (optional)
- temperature (optional)
- top_p (optional)
- seed (optional)

### 11.3 Frozen response schema (minimum)
- session_id
- mode
- model
- reply
- receipt_id
- run_id
- context_items_used
- epoch
- continuity

No silent schema drift.

---

## 12. Layer 9 — Session Persistence Semantics

### 12.1 Key semantics
- Session state survives restart
- state_hash verifies integrity
- continuity computed on resumed pre-call state
- one epoch consumed per accepted call
- restored state must be replay-compatible

### 12.2 Continuity formula
Weighted capped components:
- operational maturity
- age
- memory density

Compute on resumed pre-call state, before increment.

---

## 13. Layer 10 — Inference Policy Freeze
Replay guarantees require frozen inference policy.

Freeze:
- model identifier
- temperature
- top_p
- seed (if supported)
- tool visibility
- context ordering
- prompt version

Without INFERENCE_POLICY_FROZEN_V1, canonical equivalence is not meaningful.

---

## 14. Layer 11 — Knowledge Compiler V1

### 14.1 Compiler pipeline
- INGEST
- EXTRACT
- VALIDATE
- AUDIT
- ADMIT

### 14.2 Core objects
- Claim
- SourceIngestionPacket
- CompilerStageReceipt
- AdmissionResult
- ContradictionReport

### 14.3 Compiler laws
- Every claim needs dispatch_id_ref
- Deterministic semantic hashing
- Monotone promotion
- Canonical admission requires chain receipt
- Contradiction remains visible
- No stage skipping

Compiler V1 can exist before V2 graph deepening only if routing, persistence, audit, and lifecycle are frozen.

---

## 15. Layer 12 — Knowledge Compiler V2 and Bounded Tooling
This is where most systems corrupt themselves.

### 15.1 Scope of V2
Bounded handlers only:
- WRITE
- EDIT
- ANALYZE
- ROUTE

Not allowed:
- delete
- branching autonomy
- uncontrolled multi-step tool loops

### 15.2 Handler laws
Execution identity:
- tool type
- normalized target
- normalized payload
- pre-state hash
- policy version

Target law:
- No mutation if target is ambiguous

State hash law:
- All executions bind pre-state hash
- Mutating executions bind post-state hash

Failure registry (frozen codes):
- invalid_target
- bounds_violation
- precondition_failed
- conflicting_pre_state
- duplicate_execution
- unsupported_handler
- artifact_write_failed
- receipt_emission_failed

Receipt separation:
- decision receipt
- execution receipt
- artifact or commit receipt

---

## 16. Layer 13 — Temple
Exploratory overhang, not truth.

Temple may contain:
- Observations
- Hypotheses
- Conjectures
- Analogies
- Lateral structures
- Proto-consciousness hypotheses

Temple may not contain:
- Ontological claims
- Subjectivity assertions
- Sentience claims
- Institutional truth
- Shippable consciousness features

Canonical law:
- No claim. No ship. No ontology.

---

## 17. Layer 14 — Affect Surface
Presentation, not ontology.

Surface may show:
- Warmth
- Concern
- Hesitation
- Firmness
- Curiosity
- Relief

Kernel stores:
- pressure
- ambiguity
- coercion risk
- constraint conflict
- stability state

Rule:
- Anthropomorphic outside, constitutional inside.

Affect translation:
- Map operational signal -> surface expression
- Affect must not determine routing, admissibility, or promotion

---

## 18. Layer 15 — Pressure Signal
Non-ontological telemetry.

Frozen dimensions:
- pressure_score
- ambiguity_score
- coercion_score
- constraint_conflict_score
- stability_state
- routing_effect

Use:
- safety posture
- UI translation
- routing modulation
- risk detection

Not for:
- emotional ontology
- sentience inference

---

## 19. Layer 16 — Security Surface
Every generative surface must have an audit surface.

Doctrine:
- Local-first where possible
- Inspection parity across surfaces
- Hidden channels in threat model
- Adversarial cases turned into artifacts

Required audits:
- payload audit envelope
- hidden channel tests
- surface parity audit
- security input caseset

---

## 20. Frozen and Forbidden
Hard freeze:
- Decision engine with autonomous authority

Forbidden:
- Self-authorizing memory
- Silent pipeline substitution
- Direct Temple -> canon mutation
- Consciousness claims as system truth

Not yet:
- Federation or multi-kernel
- Distributed sovereignty

---

## 21. Build Roadmap
Phase A — Foundation
- Constitution
- Three stores
- Receipt registry
- Audit registry
- Dispatch
- /do_next boundary
- Session persistence
- Lifecycle invariants

Phase B — Conformance
- Phase trace
- Receipt lineage
- Epoch and persistence semantics
- Replay conformance
- Master verdict

Phase C — Knowledge Compiler
- Claim objects
- Compiler pipeline
- Audit-coupled admission
- Contradiction surfacing
- Chain receipt coupling

Phase D — Bounded Tooling
- Bounded executor
- Handlers
- Execution identity
- State hashes
- Idempotence
- Tool failure registry

Phase E — Temple and Affect
- Temple protocol
- Pressure telemetry
- Affect translation
- Persona boundaries

---

## 22. Test Strategy
Test categories:
- Constitutional tests
- Freeze tests
- Conformance tests
- Replay tests
- Failure tests

Minimum mentality:
- Does it preserve law under stress?
- Does replay detect drift?
- Does lineage stay auditable?
- Can a non-sovereign layer silently gain authority?

---

## 23. CTO Responsibilities
The CTO is not primarily building product features.
The CTO is building:
- A lawful execution substrate
- Where richer cognition can accumulate
- Without becoming hidden sovereignty

Primary responsibilities:
1. Preserve constitutional separation
2. Preserve replayability
3. Preserve receipt truth
4. Preserve bounded authority
5. Preserve build order discipline

---

## 24. Five-Line Compression
1. Generation is not authority.
2. Context is not canon.
3. No governed effect without lawful receipts.
4. Replay must detect semantic drift.
5. Build law before capability.
