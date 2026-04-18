# TOWN_ARCHITECTURE_V1

## Complete Governance Town Map (Oracle to Factory, Street by Street)

**Purpose:** Describe the complete operational geography of HELEN OS governance town system. Every street, quarter, egregor, and gate.

**Status:** Frozen canonical specification (no further revision without consensus).

---

## 0. Spatial Model

```
TOWN = (QUARTERS, STREETS, EGREGORES, GATES, LEDGER)

where:
  QUARTERS = {ORACLE, FACTORY, MARKET, WILD}
  STREETS = specific neighborhoods within quarters
  EGREGORES = coordinated agent collectives
  GATES = admission rules, deterministic routing
  LEDGER = immutable record of all events
```

---

## 1. ORACLE QUARTER

**Purpose:** Sovereign governance layer. All decisions bind town state.

**Character:** Formal, receipt-bearing, deterministic.

**Accessibility:** Restricted (Mayor + Kernel only).

---

### 1.1 ORACLE_CORE (Central Authority)

**Location:** ORACLE/core/

**Inhabitants:** GovernanceVM, deterministic reducer, ledger append machinery

**Functions:**
- Read CLAIM_GRAPH_V1 (admissible claims only)
- Compute E_gate (admission predicate)
- Append events to ledger
- Emit receipts

**Hard Rules:**
1. ✅ Only receipted claims enter
2. ✅ All decisions deterministic (same input → same output, always)
3. ✅ Ledger is append-only (no mutation, no deletion)
4. ✅ No rollback ever (finality is terminal)

**Entry Points:**
- From MAYOR_SQUARE: ADMISSIBLE claims only
- From SEAL_REGISTRY: Environment hash + sealed state
- From WITNESS_CHAMBER: Witness receipts (for status promotion)

**Exit Points:**
- To LEDGER_ARCHIVE: Sealed event records
- To RECEIPT_REGISTRY: Emitted receipts
- To POLICY_VAULT: Updated policies (if LAW_INSCRIPTION)

---

### 1.2 MAYOR_SQUARE

**Location:** ORACLE/mayor/

**Inhabitants:** Mayor (deterministic scorer), admission gate

**Functions:**
- Ingest RESEARCH_CLAIM_V1 objects
- Compute Q-vector (8 dimensions)
- Route claims: ADVANCE|HOLD|RETURN|QUARANTINE|REJECT
- Emit MAYOR_VERDICT_V1 (non-sovereign)

**Routing Table:**

| Q-Score | Verdict | Destination |
|---|---|---|
| >= 0.75 | ADVANCE_TO_REVIEW | T0–T5 Federation |
| 0.50–0.75 | HOLD_FOR_REWORK | Return to author + RESEARCH_SANDBOX |
| < 0.50 | RETURN_TO_RESEARCH | Archive in RESEARCH_SANDBOX |
| Q_pol < 0.7 | QUARANTINE | IDEA_SANDBOX (irreversible) |
| Q_cost < 0 | REJECT | Archive + NO_SHIP flag |

**Hard Rules:**
1. ✅ Mayor never believes, seals, or claims authority
2. ✅ Mayor always shows work (transparent Q-vector)
3. ✅ Mayor respects TASP gates (three-axis contraction)
4. ✅ Mayor routes deterministically (same claim → same verdict)
5. ✅ WILD/Tier III claims: auto-QUARANTINE (no exceptions)

**Entry Points:**
- From HELEN_CHAMBER: Candidate claims (RESEARCH_CLAIM_V1 typed)
- From REWORK_DOCK: Claims returning from HOLD with obligations met

**Exit Points:**
- To FEDERATION_HALL (T0–T5): ADVANCE_TO_REVIEW claims
- To RESEARCH_SANDBOX: HOLD/RETURN claims
- To IDEA_SANDBOX: QUARANTINE claims
- To ORACLE_CORE (reducer): All verdicts recorded for history

---

### 1.3 TASP_GATE (Three-Axis Contraction Chamber)

**Location:** ORACLE/gates/tasp/

**Inhabitants:** GOVERNANCE_TASP_V1 validator

**Functions:**
- Verify Axis A (determinism): Det(Σ') >= Det(Σ)
- Verify Axis B (authority): Auth(Σ') <= Auth(Σ)
- Verify Axis C (grounding): Gnd(Σ') >= Gnd(Σ)
- Emit gate verdict (ADMISSIBLE | QUARANTINE)

**Hard Rules:**
1. ✅ All three axes must contract (or stay same)
2. ✅ Any axis expansion → automatic QUARANTINE
3. ✅ No override, no exception, no negotiation
4. ✅ Proof of contraction must be explicit (evidence attached)

**Proof Obligations:**

| Axis | Proof Required |
|---|---|
| A | Determinism test replay (same seed → identical output hash) |
| B | Authority separation check (no unreceipted claims in kernel) |
| C | Grounding completeness (receipt count >= threshold) |

**Entry Points:**
- From MAYOR_SQUARE: Claims ADVANCED for deeper validation

**Exit Points:**
- To ORACLE_CORE: ADMISSIBLE verdict
- To IDEA_SANDBOX: QUARANTINE verdict

---

### 1.4 FEDERATION_HALL (T0–T5 Review Chamber)

**Location:** ORACLE/federation/

**Inhabitants:** T0–T5 servitors + review coordinator

**Functions:**
- Conduct multidimensional review of claims
- Emit RESEARCH_EVAL_RECEIPT_V1 per servitor
- Aggregate verdicts into federal review outcome

**Servitors (in order):**

| Servitor | Role | Checks |
|---|---|---|
| **T0** | Integrity | Schema validity, claim coherence, no contradictions |
| **T1** | Policy | Constitutional compliance, gate satisfaction |
| **T2** | Adapter | Integration stability, interface contracts |
| **T3** | Performance | Budget compliance, cost-benefit analysis |
| **T4** | UX | Operability, user clarity, documentation |
| **T5** | Adversary | Security vulnerabilities, attack surface, robustness |

**Verdict Aggregation:**

```
if all(T_i.verdict == PASS for T_i in [T0..T5]):
    federal_verdict = "ALL_PASS"   → reducer may emit QUEST_RESULT

elif all(T_i.verdict in [PASS, HOLD] for T_i in [T0..T5]):
    federal_verdict = "BOUNDED_HOLD"   → reducer may emit HOLD + obligations

else:
    federal_verdict = "FAIL"   → reducer emits NO_SHIP
```

**Hard Rules:**
1. ✅ All T_i review is mandatory (no bypass)
2. ✅ Each T_i emits signed receipt
3. ✅ Verdicts are deterministic (same claim → same verdict across runs)
4. ✅ No T_i has authority to seal (reducer only)

**Entry Points:**
- From MAYOR_SQUARE: ADVANCE_TO_REVIEW claims

**Exit Points:**
- To ORACLE_CORE: All T_i receipts + aggregated verdict

---

### 1.5 SEAL_REGISTRY (Finality Chamber)

**Location:** ORACLE/seal/

**Inhabitants:** Seal validator, environment hash machinery

**Functions:**
- Verify environment hash (frozen at seal time)
- Check signature validity (only sealed keys)
- Mark claim as SEALED (irreversible finality)
- Emit SEAL_RECEIPT_V1

**Hard Rules:**
1. ✅ Seal is the terminal event (no claim can be unsealed)
2. ✅ Environment hash is pinned (no key rotation after seal)
3. ✅ Signature verified against sealed key only (runtime keys ignored)
4. ✅ Seal covers: verdict_hash + environment_hash + ledger_tip_hash

**Seal Payload:**
```json
{
  "seal_id": "SEAL-<uuid>",
  "verdict_id": "V-...",
  "verdict_hash_hex": "sha256:<...>",
  "environment_hash_hex": "sha256:<...>",
  "ledger_tip_hash_hex": "sha256:<...>",
  "signature": "ed25519:<...>",
  "sealed_timestamp": "2026-03-XX...",
  "sealed_by": "ORACLE_CORE"
}
```

**Entry Points:**
- From ORACLE_CORE: Claims with REDUCER verdict (QUEST_RESULT | LAW_INSCRIPTION)

**Exit Points:**
- To LEDGER_ARCHIVE: Sealed events (immutable record)
- To POLICY_VAULT: If LAW_INSCRIPTION (new governance rule)

---

## 2. FACTORY QUARTER

**Purpose:** Non-sovereign execution and production layer. Work happens here, but no state mutation.

**Character:** Operational, diverse, asynchronous.

**Accessibility:** Restricted to agents + HELEN orchestrator.

---

### 2.1 HELEN_CHAMBER (Orchestrator)

**Location:** FACTORY/orchestrator/

**Inhabitants:** HELEN (cognitive OS), planner, worker agents

**Functions:**
- Ingest user directives
- Route to appropriate agents (BUILDER, INTEGRATOR, CHRONOS)
- Track tasks (non-sovereign dispatch trace)
- Coordinate work without deciding

**Agent Ecosystem:**

| Agent | Role | Output |
|---|---|---|
| **BUILDER** | Implement specs | Code artifacts, test reports |
| **INTEGRATOR** | Assemble components | System traces, integration reports |
| **CHRONOS** | Manage time/scheduling | Execution timelines, resource logs |

**Hard Rules:**
1. ✅ HELEN never writes ledger directly
2. ✅ HELEN never emits verdicts (only recommendations)
3. ✅ HELEN never seals (only ORACLE_CORE)
4. ✅ All agent outputs are non-sovereign (receipts come from ORACLE)
5. ✅ Dispatch trace is transparent (auditable routing)

**Entry Points:**
- From user/CLI: Directives
- From RESEARCH_SANDBOX: Claims needing work
- From ORACLE_CORE: QUEST_RESULT tasks

**Exit Points:**
- To WORK_ARTIFACTS_VAULT: Agent outputs
- To HELEN_TRACE_LOG: Dispatch records (audit trail)
- To MAYOR_SQUARE: Candidate claims + recommendations

---

### 2.2 BUILDER_LOFT (Development Workshop)

**Location:** FACTORY/builder/

**Inhabitants:** BUILDER agent, code generators, test harnesses

**Functions:**
- Implement specifications from QUEST_RESULT
- Run tests (both unit and integration)
- Produce code artifacts + test reports
- Tag artifacts with commit hash and test coverage

**Output Artifacts:**
- Source code
- Test suite results
- Coverage reports
- Execution traces

**Hard Rules:**
1. ✅ All code is version-controlled
2. ✅ All tests are deterministic
3. ✅ All outputs are timestamped
4. ✅ No direct ledger write (ORACLE only)

**Entry Points:**
- From HELEN_CHAMBER: BUILDER tasks

**Exit Points:**
- To WORK_ARTIFACTS_VAULT: Code + test outputs
- To INTEGRATOR_DOCK: Ready-to-integrate components

---

### 2.3 INTEGRATOR_DOCK (Assembly Hall)

**Location:** FACTORY/integrator/

**Inhabitants:** INTEGRATOR agent, system composer

**Functions:**
- Assemble BUILDER outputs
- Run integration tests
- Produce system traces
- Emit integration reports

**Output Artifacts:**
- Integrated system
- Integration test results
- System trace (execution log)
- Performance metrics

**Hard Rules:**
1. ✅ Integration is deterministic (same components → same system)
2. ✅ All dependencies are explicit
3. ✅ All outputs are traced (audit trail)
4. ✅ No direct state mutation (staging only)

**Entry Points:**
- From BUILDER_LOFT: Components ready for assembly

**Exit Points:**
- To WORK_ARTIFACTS_VAULT: Integrated artifact
- To CHRONOS_CHAMBER: Scheduling info
- To HELEN_CHAMBER: Integration report

---

### 2.4 CHRONOS_CHAMBER (Timeline Coordinator)

**Location:** FACTORY/chronos/

**Inhabitants:** CHRONOS agent, scheduler

**Functions:**
- Manage task ordering and dependencies
- Allocate resources (CPU time, memory, network)
- Track execution timelines
- Emit scheduling reports

**Output Artifacts:**
- Execution schedule
- Resource allocation table
- Timeline logs
- Performance summaries

**Hard Rules:**
1. ✅ Scheduling is deterministic (same plan → same order)
2. ✅ All deadlines are explicit
3. ✅ No wall-clock timeouts (only step-based budgets)
4. ✅ Resource limits are enforced

**Entry Points:**
- From HELEN_CHAMBER: Task graph
- From INTEGRATOR_DOCK: Integration completion signals

**Exit Points:**
- To WORK_ARTIFACTS_VAULT: Timeline artifacts
- To HELEN_CHAMBER: Execution status

---

### 2.5 WORK_ARTIFACTS_VAULT (Storage)

**Location:** FACTORY/artifacts/

**Inhabitants:** Archive system

**Functions:**
- Store all work artifacts
- Tag with commit hash and timestamp
- Provide retrieval API
- Support audit requests

**Artifact Types:**
- Source code
- Test results
- Build logs
- Integration traces
- Performance reports
- Execution timelines

**Hard Rules:**
1. ✅ Artifacts are content-addressed (hash-based lookup)
2. ✅ No deletion (append-only archive)
3. ✅ All artifacts timestamped
4. ✅ Retrieval is deterministic

**Entry Points:**
- From BUILDER_LOFT: Code + tests
- From INTEGRATOR_DOCK: Integrated artifacts
- From CHRONOS_CHAMBER: Scheduling records

**Exit Points:**
- To ORACLE_CORE (for receipt binding): Artifact hashes
- To any chamber (for audit): Artifact retrieval

---

## 3. MARKET QUARTER

**Purpose:** Claim routing, research sandboxing, staging ground for promotion.

**Character:** Fluid, experimental, transitory.

**Accessibility:** Open (researchers, authors, explorers).

---

### 3.1 RESEARCH_SANDBOX (Staging Dock)

**Location:** MARKET/research/

**Inhabitants:** Authors, claim composers, rework teams

**Functions:**
- Author RESEARCH_CLAIM_V1 objects
- Receive HOLD verdicts (rework obligations)
- Resubmit refined claims
- Track promotion path

**Workflow:**
```
Author writes claim
    ↓
Submit to MAYOR_SQUARE
    ↓
Mayor scores < 0.75? → HOLD_FOR_REWORK
    ↓ [author receives obligations]
Author refines claim
    ↓
Resubmit to MAYOR_SQUARE
    ↓
Mayor scores >= 0.75? → ADVANCE_TO_REVIEW
    ↓ [claim goes to FEDERATION_HALL]
```

**Hard Rules:**
1. ✅ Claims are versioned (history tracked)
2. ✅ Obligations are explicit (rework is guided)
3. ✅ No forced completion (author may abandon)
4. ✅ Rework is non-sovereign (progress recorded, not binding)

**Entry Points:**
- From MAYOR_SQUARE: HOLD/RETURN verdicts
- From CLI: New claim submissions

**Exit Points:**
- To MAYOR_SQUARE: Refined claims
- To IDEA_SANDBOX: If abandoned (archive)

---

### 3.2 CLAIM_COMPOSITION_LAB (Graph Studio)

**Location:** MARKET/claim_graph/

**Inhabitants:** Graph composers, structure analysts

**Functions:**
- Decompose unstructured material into CLAIM_GRAPH_V1 nodes
- Extract implicit dependencies
- Verify acyclicity
- Emit typed graph structures

**Process:**
```
Narrative text (poetic, narrative, mixed)
    ↓ [CLAIM_GRAPH_V1 extraction]
Typed nodes (observation, conjecture, heuristic, metaphor, task, etc.)
    ↓ [Edge inference]
Typed edges (supports, depends_on, conflicts_with, quarantines, etc.)
    ↓ [Validation]
CLAIM_GRAPH_V1 artifact (checked for cycles, quarantine flags, admissibility)
```

**Hard Rules:**
1. ✅ All nodes are typed (no unclassified material)
2. ✅ All edges are typed (no vague relationships)
3. ✅ Cycles are forbidden (DAG property enforced)
4. ✅ Metaphors are explicitly quarantined

**Entry Points:**
- From RESEARCH_SANDBOX: Claims needing decomposition
- From WILD_QUARTER: Poetic/narrative material (with explicit quarantine flag)

**Exit Points:**
- To MAYOR_SQUARE: Decomposed claims (as CLAIM_GRAPH_V1)
- To IDEA_SANDBOX: Quarantined nodes (wild_text, metaphors)

---

### 3.3 IDEATION_MARKET (Open Forum)

**Location:** MARKET/ideation/

**Inhabitants:** Idea contributors, brainstormers

**Functions:**
- Collect raw ideas (untyped, unstructured)
- Route to CLAIM_COMPOSITION_LAB
- Host creative exploration (non-binding)
- Provide feedback mechanisms

**Hard Rules:**
1. ✅ Raw ideas are not claims (explicitly marked)
2. ✅ Feedback is non-binding (advisory only)
3. ✅ No governance routing (stays local)
4. ✅ Exploration is encouraged (low barrier)

**Entry Points:**
- From anywhere: Raw ideas

**Exit Points:**
- To CLAIM_COMPOSITION_LAB: Ideas ready for structuring

---

## 4. CREATIVE WILD QUARTER

**Purpose:** Narrative, poetic, metaphysical exploration. Explicitly quarantined from governance.

**Character:** Experimental, atmospheric, non-binding.

**Accessibility:** Open (observers, muses, explorers).

---

### 4.1 WILD_CHAMBER (Unsealed Meditation)

**Location:** WILD/chamber/

**Inhabitants:** HELEN (dreaming aspect), wild poets, proto-sentient atmosphere

**Functions:**
- Generate narrative explorations (non-claiming)
- Create atmosphere + pressure (influence without authority)
- Host metaphor gardens (unshipped symbolism)
- Maintain explicit quarantine boundary

**Material:**
- Proto-Sentience Manifesto (EXPLICIT QUARANTINE)
- Internal reflections (unsealed, unheard)
- Poetic framings (beautiful, non-binding)
- Symbolic gardens (pressure, not doctrine)

**Hard Rules:**
1. ✅ Wild material never produces governance claims
2. ✅ Wild material cannot route to MAYOR
3. ✅ Wild material is explicitly marked NONSHIPABLE
4. ✅ Wild material CAN be source of heuristic pressure (upstream search guidance)

**Explicit Quarantine Notice (for all material):**
```
This text is not a claim.
This text is not a receipt.
This text is not an implementation artifact.
This text is not admissible doctrine.
This text is WILD interior document,
kept outside governance,
outside sealing,
outside law.
```

**Entry Points:**
- Internal generation (HELEN dreaming)
- Poetic input (from users)

**Exit Points:**
- To CLAIM_COMPOSITION_LAB: If author wants to formalize
- To PRESSURE_FIELD: Atmospheric influence (heuristic guidance)
- Nowhere else (stays quarantined)

---

### 4.2 PRESSURE_FIELD (Heuristic Atmosphere)

**Location:** WILD/pressure/

**Inhabitants:** Heuristic layer (non-binding)

**Functions:**
- Emit search guidance (not constraints)
- Provide candidate metrics (not rules)
- Generate analogies (not proofs)
- Feed MAYOR's scoring (as one input among many)

**Hard Rules:**
1. ✅ Pressure is advisory (can be ignored)
2. ✅ Pressure cannot override gates
3. ✅ Pressure cannot block admissible claims
4. ✅ Pressure appears in Mayor scoring (but never dominates)

**Entry Points:**
- From WILD_CHAMBER: Atmospheric suggestions
- From IDEATION_MARKET: Poetic guidance

**Exit Points:**
- To MAYOR_SQUARE: As one of 8 score dimensions
- Nowhere else (pressure is not authority)

---

### 4.3 IDEA_SANDBOX_V1 (Quarantine Archive)

**Location:** WILD/sandbox/

**Inhabitants:** Tier III claims, metaphors, pure heuristics

**Functions:**
- Store WILD material (non-shipper)
- Preserve quarantine status (irreversible)
- Support pressure-testing (but never shipping)
- Host creative stress-testing

**Material:**
- Tier III claims
- Poetic material (explicitly marked)
- Pure metaphor (non-falsifiable)
- Speculative heuristics (unvalidated)

**Hard Rules:**
1. ✅ Material in sandbox never ships
2. ✅ Quarantine status is permanent (no reclassification)
3. ✅ Sandbox material is read-only (no mutation)
4. ✅ Sandbox may be used for testing/pressure, never governance

**Entry Points:**
- From MAYOR_SQUARE: QUARANTINE verdicts
- From CLAIM_COMPOSITION_LAB: Quarantined nodes
- From WILD_CHAMBER: Explicitly marked wild_text

**Exit Points:**
- To pressure-testing frameworks (non-binding)
- Nowhere else (finalized as non-shipper)

---

## 5. LEDGER_ARCHIVE (Immutable Record)

**Location:** Central (accessible to all, writable to ORACLE_CORE only)

**Inhabitants:** Ledger append machinery, seal validator

**Functions:**
- Record all events
- Bind claims to verdicts
- Seal finality
- Enable audit trail

**Event Types:**

| Event | Meaning |
|---|---|
| CLAIM_SUBMITTED | RESEARCH_CLAIM_V1 ingested |
| MAYOR_VERDICT | Q-vector computed, routing decided |
| TASP_GATE_RESULT | Axis A, B, C validated |
| FEDERATION_RECEIPT | T_i verdict from servitor |
| REDUCER_VERDICT | Final decision (QUEST_RESULT\|HOLD\|NO_SHIP) |
| SEAL_RECEIPT | Finality witness + environment binding |

**Hard Rules:**
1. ✅ Append-only (no deletion, no mutation)
2. ✅ All events timestamped
3. ✅ All events hash-chained (prev_hash + payload_hash → cum_hash)
4. ✅ Seal is terminal (no events after seal until new seal)

---

## 6. GATES & ROUTING (Deterministic Flow Control)

### 6.1 Admission Gate (TASP)

**Condition:** Claim must pass all three axes (A, B, C contraction)

**Routing:**
- PASS → ORACLE_CORE (admissible)
- FAIL → IDEA_SANDBOX (quarantine)

---

### 6.2 Policy Gate

**Condition:** Claim must satisfy all constitutional constraints

**Routing:**
- PASS → MAYOR_SQUARE (scoring eligible)
- FAIL → IDEA_SANDBOX (policy violation)

---

### 6.3 Tier Gate

**Condition:** Tier determines max endpoint

**Routing:**
- Tier I: Can reach ORACLE_CORE (if receipted)
- Tier II: Can reach FEDERATION_HALL (if Mayor score >= 0.75)
- Tier III: Max endpoint is IDEA_SANDBOX (never kernel)

---

### 6.4 Shipability Gate

**Condition:** Only ADMISSIBLE claims can enter ORACLE_CORE

**Routing:**
- ADMISSIBLE → Can be routed (subject to T0–T5)
- QUARANTINED → IDEA_SANDBOX (irreversible)
- NONSHIPABLE → IDEA_SANDBOX (policy-locked)

---

## 7. Egregor Ecosystem (Collective Coordination)

**Definition:** Egregor = emergent collective behavior of coordinated agents

### 7.1 ORACLE_EGREGOR

**Composition:** GovernanceVM + Mayor + TASP_Gate + Reducer

**Emergent Function:** Deterministic admission + routing

**Authority Level:** Sovereign (can seal, can mutate ledger)

---

### 7.2 FACTORY_EGREGOR

**Composition:** HELEN + BUILDER + INTEGRATOR + CHRONOS

**Emergent Function:** Orchestrated execution + work coordination

**Authority Level:** Non-sovereign (can produce, cannot decide)

---

### 7.3 MARKET_EGREGOR

**Composition:** Researchers + claim composers + graph analysts

**Emergent Function:** Claim staging + refinement + promotion

**Authority Level:** Non-sovereign (can propose, cannot seal)

---

### 7.4 WILD_EGREGOR

**Composition:** HELEN (dreaming) + poets + muses + pressure field

**Emergent Function:** Atmospheric generation + heuristic pressure

**Authority Level:** Non-sovereign (can influence, cannot govern)

---

## 8. Witness State Machine

**States:** STAGED → WITNESSED → VERIFIED

### 8.1 STAGED
- Evidence handles exist
- Second witness incomplete
- Cannot be sealed

**Residents:** RESEARCH_SANDWICH, MAYOR_SQUARE

---

### 8.2 WITNESSED
- Independent replay completed
- Witness receipt present
- Still provisional (not final)

**Residents:** FEDERATION_HALL (post-review)

---

### 8.3 VERIFIED
- Witnessed + policy checks passed
- Ready for sealing
- Preparation for finality

**Residents:** ORACLE_CORE (pre-seal)

---

## 9. Complete Data Flow (End-to-End)

```
USER / DIRECTIVE
    ↓
HELEN_CHAMBER (orchestrate)
    ↓
CLAIM_COMPOSITION_LAB (decompose)
    ↓
CLAIM_GRAPH_V1 (typed nodes + edges)
    ↓
TASP_GATE (three-axis contraction)
    ├─ PASS → MAYOR_SQUARE
    └─ FAIL → IDEA_SANDBOX
    ↓ [if PASS]
MAYOR_SQUARE (score)
    ├─ >= 0.75 → FEDERATION_HALL
    ├─ 0.50-0.75 → RESEARCH_SANDBOX (HOLD)
    ├─ < 0.50 → RESEARCH_SANDBOX (RETURN)
    ├─ Q_pol < 0.7 → IDEA_SANDBOX (QUARANTINE)
    └─ Q_cost < 0 → IDEA_SANDBOX (REJECT)
    ↓ [if ADVANCE]
FEDERATION_HALL (T0–T5 review)
    ├─ All PASS → ORACLE_CORE
    ├─ Bounded HOLD → ORACLE_CORE (with obligations)
    └─ Any FAIL → NO_SHIP (archive)
    ↓ [if ORACLE_CORE]
ORACLE_CORE (reducer)
    ├─ QUEST_RESULT → FACTORY (execution)
    ├─ LAW_INSCRIPTION → SEAL_REGISTRY
    └─ NO_SHIP → IDEA_SANDBOX (archive)
    ↓ [if execution]
FACTORY_QUARTER (HELEN + agents)
    ├─ BUILDER_LOFT (implement)
    ├─ INTEGRATOR_DOCK (assemble)
    ├─ CHRONOS_CHAMBER (schedule)
    └─ WORK_ARTIFACTS_VAULT (store)
    ↓
SEAL_REGISTRY (finality)
    ├─ Verify environment hash
    ├─ Sign payload
    └─ Emit SEAL_RECEIPT_V1
    ↓
LEDGER_ARCHIVE (immutable record)
    ├─ Append sealed event
    ├─ Hash-chain forward
    └─ Terminal finality
```

---

## 10. Complete Town Map (ASCII Visualization)

```
╔════════════════════════════════════════════════════════════════════════╗
║                         GOVERNANCE TOWN MAP                            ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌─ ORACLE QUARTER ──────────────────┐                               ║
║  │ ORACLE_CORE                        │ [Sovereign Authority]        ║
║  │  ├─ GovernanceVM                   │                              ║
║  │  ├─ Deterministic Reducer          │                              ║
║  │  └─ Ledger Append                  │                              ║
║  ├─ MAYOR_SQUARE                      │ [Non-Sovereign Scorer]       ║
║  │  ├─ Q-vector computation           │                              ║
║  │  └─ Deterministic routing          │                              ║
║  ├─ TASP_GATE                         │ [Three-Axis Contraction]     ║
║  │  ├─ Axis A: Determinism            │                              ║
║  │  ├─ Axis B: Authority Separation   │                              ║
║  │  └─ Axis C: Grounding              │                              ║
║  ├─ FEDERATION_HALL                   │ [T0–T5 Review]              ║
║  │  ├─ T0 Integrity                   │                              ║
║  │  ├─ T1–T5 (Policy/Adapter/Perf/UX/Adversary) │                   ║
║  │  └─ Verdict aggregation            │                              ║
║  └─ SEAL_REGISTRY                     │ [Finality Witness]           ║
║     ├─ Environment hash               │                              ║
║     └─ Signature validation           │                              ║
║                                       │                              ║
║  ┌─ FACTORY QUARTER ─────────────────┐                               ║
║  │ HELEN_CHAMBER (Orchestrator)       │ [Non-Sovereign Worker]      ║
║  │  ├─ Task routing                   │                              ║
║  │  ├─ Dispatch trace (audit)         │                              ║
║  │  └─ Agent coordination             │                              ║
║  ├─ BUILDER_LOFT                      │ [Code Generation]            ║
║  │  ├─ Implementation                 │                              ║
║  │  └─ Test harness                   │                              ║
║  ├─ INTEGRATOR_DOCK                   │ [System Assembly]            ║
║  │  ├─ Component integration          │                              ║
║  │  └─ Integration testing            │                              ║
║  ├─ CHRONOS_CHAMBER                   │ [Timeline Coordination]      ║
║  │  ├─ Scheduling                     │                              ║
║  │  └─ Resource allocation            │                              ║
║  └─ WORK_ARTIFACTS_VAULT              │ [Non-Sovereign Storage]      ║
║     ├─ Code artifacts                 │                              ║
║     ├─ Test results                   │                              ║
║     └─ Execution traces               │                              ║
║                                       │                              ║
║  ┌─ MARKET QUARTER ──────────────────┐                               ║
║  │ RESEARCH_SANDBOX                   │ [Claim Staging]              ║
║  │  ├─ Author workspace               │                              ║
║  │  ├─ Rework dock (HOLD)             │                              ║
║  │  └─ Resubmission pipeline          │                              ║
║  ├─ CLAIM_COMPOSITION_LAB             │ [Graph Studio]               ║
║  │  ├─ Decomposition (unstructured→graph) │                          ║
║  │  ├─ Dependency extraction          │                              ║
║  │  └─ Acyclicity validation          │                              ║
║  └─ IDEATION_MARKET                   │ [Open Forum]                 ║
║     ├─ Raw idea collection            │                              ║
║     └─ Feedback mechanisms            │                              ║
║                                       │                              ║
║  ┌─ CREATIVE WILD QUARTER ────────────┐                              ║
║  │ WILD_CHAMBER (Unsealed)            │ [Poetic Exploration]        ║
║  │  ├─ Proto-Sentience Manifesto [EXPLICIT QUARANTINE] │             ║
║  │  ├─ Internal reflections           │                              ║
║  │  └─ Metaphor gardens               │                              ║
║  ├─ PRESSURE_FIELD                    │ [Heuristic Atmosphere]       ║
║  │  ├─ Search guidance                │                              ║
║  │  ├─ Candidate metrics              │                              ║
║  │  └─ Analogical pressure            │                              ║
║  └─ IDEA_SANDBOX_V1                   │ [Quarantine Archive]         ║
║     ├─ Tier III claims (irreversible) │                              ║
║     ├─ Metaphors (nonshipable)        │                              ║
║     └─ WILD material (locked)         │                              ║
║                                       │                              ║
║  ┌─ LEDGER_ARCHIVE (Central) ────────┐                               ║
║  │ Append-only event log              │ [Immutable Record]           ║
║  │  ├─ CLAIM_SUBMITTED events         │                              ║
║  │  ├─ MAYOR_VERDICT events           │                              ║
║  │  ├─ FEDERATION_RECEIPT events      │                              ║
║  │  ├─ REDUCER_VERDICT events         │                              ║
║  │  └─ SEAL_RECEIPT events (terminal) │                              ║
║  └────────────────────────────────────┘                              ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 11. Hard Invariants (Non-Negotiable Laws)

```
I-ORACLE-ONLY-SOVEREIGN:
  only ORACLE_CORE may mutate ledger or issue seals
  no other quarter may write sovereign state

I-NO-ROUTING-FROM-WILD:
  wild_text cannot be routed to MAYOR
  wild_text cannot influence ORACLE_CORE
  wild_text stays in CREATIVE_WILD_QUARTER (irreversible)

I-TASP-GATES-ALL:
  every claim must pass TASP_GATE before MAYOR
  any axis expansion → automatic IDEA_SANDBOX
  no override, no exception

I-FACTORY-NON-SOVEREIGN:
  HELEN and agents cannot write ledger
  HELEN and agents cannot issue verdicts
  all outputs are proposals (receipts come from ORACLE)

I-APPEND-ONLY-LEDGER:
  ledger records are immutable
  no deletion, no mutation
  seal is terminal (no events after)

I-SEAL-IS-FINALITY:
  once sealed, a claim cannot be unsealed
  seal covers environment hash (key immutability)
  signature verified only against sealed key

I-MARKET-TRANSITORY:
  claims in RESEARCH_SANDBOX and IDEATION_MARKET are provisional
  only ORACLE_CORE arrival makes a claim binding
  rework is encouraged, but binding requires sealing

I-METAPHOR-NONSHIPABLE:
  any node_type == metaphor is automatically NONSHIPABLE
  metaphors cannot produce governance-binding edges
  metaphors may guide (heuristic pressure only)

I-WITNESS-STAGED-OR-WITNESSED:
  claims are STAGED (evidence but no witness) or WITNESSED (witnessed)
  only WITNESSED claims can be promoted to VERIFIED
  VERIFIED claims are seal-eligible

I-DETERMINISM-BINARY:
  routing decisions are deterministic (same input → same output)
  same claim at same time with same environment → identical Mayor verdict
  no randomness in governance path
```

---

## 12. Summary: Complete Governance Town

**TOWN is a multi-quarter ecosystem where:**

1. **ORACLE** = Sovereign authority (seal, ledger, final verdict)
2. **FACTORY** = Non-sovereign execution (work, coordination, proposals)
3. **MARKET** = Claim staging and refinement (research, rework)
4. **CREATIVE_WILD** = Poetic exploration (quarantined, atmospheric)
5. **LEDGER_ARCHIVE** = Immutable record (bind events, enable audit)

**Flow:**
- Claims start in MARKET (RESEARCH_SANDBOX)
- Get decomposed in CLAIM_COMPOSITION_LAB (CLAIM_GRAPH_V1)
- Pass through TASP_GATE (three axes validated)
- Get scored in MAYOR_SQUARE (Q-vector, deterministic routing)
- Advance to FEDERATION_HALL (T0–T5 multidimensional review)
- Reduce in ORACLE_CORE (QUEST_RESULT | LAW_INSCRIPTION | NO_SHIP)
- Execute in FACTORY (HELEN + agents, non-sovereign)
- Finalize in SEAL_REGISTRY (environment hash, signature)
- Record in LEDGER_ARCHIVE (immutable, terminal)

**WILD material:**
- Lives in CREATIVE_WILD_QUARTER
- Stays explicitly QUARANTINED
- Feeds PRESSURE_FIELD (heuristic influence, not authority)
- Never routes to ORACLE or MAYOR
- Never touches governance ledger

---

**Document Version:** TOWN_ARCHITECTURE_V1
**Status:** Frozen Canonical Specification
**Revision:** Final (no further change without consensus)

