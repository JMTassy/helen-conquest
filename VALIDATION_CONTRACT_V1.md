# VALIDATION_CONTRACT_V1

## Schema Enforcement Contract for Path B Implementation

**Date:** 2026-03-08
**Status:** Frozen (no further changes without consensus)

---

## 0. Purpose

Define CI validation gates for the four JSON schemas (RESEARCH_CLAIM_V1, CLAIM_GRAPH_V1, MAYOR_CANDIDATE_PACKET_V1, TOWN_ROUTING_POLICY_V1). Ensures implementation cannot drift from specification.

---

## 1. Schema Inventory

| Schema | Purpose | Location | CI Gate |
|---|---|---|---|
| **research_claim_v1.schema.json** | Claim ingestion boundary (tier/admissibility/quarantine) | `/schemas/research_claim_v1.schema.json` | MUST validate all RESEARCH_CLAIM_V1 objects |
| **claim_graph_v1.schema.json** | Typed graph decomposition (nodes/edges) | `/schemas/claim_graph_v1.schema.json` | MUST validate all CLAIM_GRAPH_V1 artifacts |
| **mayor_candidate_packet_v1.schema.json** | Mayor scoring input packet | `/schemas/mayor_candidate_packet_v1.schema.json` | MUST validate all packets entering MAYOR_SQUARE |
| **town_routing_policy.schema.json** | Routing thresholds + hard invariants | `/schemas/town_routing_policy.schema.json` | MUST validate policy configuration at boot |

---

## 2. Validation Gates (CI Enforcement)

### Gate 1: Claim Ingestion

**When:** User/system creates RESEARCH_CLAIM_V1

**Schema:** `research_claim_v1.schema.json`

**Required Validations:**
1. ✅ `schema_version` == "RESEARCH_CLAIM_V1" (const check)
2. ✅ `claim_id` matches pattern `^RC-[A-Z0-9_-]{6,}$`
3. ✅ `tier` in [I, II, III] (no other values)
4. ✅ `admissibility` matches tier:
   - If `tier == III` → `admissibility` MUST be "QUARANTINED" (enforced by allOf conditional)
5. ✅ `origin.source_type` is one of: legacy_corpus, new_work, import, conversation
6. ✅ `quarantine_triggers` array contains only valid enum values (no duplicates)
7. ✅ `evidence_handles` array has at least one entry (if required by admissibility rules)

**CI Failure Conditions:**
- ❌ Schema validation fails → REJECT (do not ingest)
- ❌ Tier III with admissibility != QUARANTINED → REJECT
- ❌ Missing required fields → REJECT

**CI Success Condition:**
- ✅ All validations pass → claim enters RESEARCH_SANDBOX

---

### Gate 2: Graph Decomposition

**When:** CLAIM_GRAPH_V1 is created from unstructured material

**Schema:** `claim_graph_v1.schema.json`

**Required Validations:**
1. ✅ `spec.name` == "CLAIM_GRAPH_V1" (const check)
2. ✅ `graph_meta.environment_ref` matches pattern `^sha256:` (verifiable hash)
3. ✅ `graph_meta.policy_ref` matches pattern `^sha256:` (verifiable hash)
4. ✅ All nodes have valid `kind` values (enum: claim, evidence_handle, artifact, receipt, witness, policy, definition, wild_text)
5. ✅ All wild_text nodes have:
   - `admissibility == "QUARANTINED"` (enforced by allOf conditional)
   - `route_to_mayor == false` (enforced by allOf conditional)
6. ✅ All evidence_handle nodes have complete `handle` object with all 7 required fields
7. ✅ All edges have valid `type` values (enum: SUPPORTS, REFUTES, DEPENDS_ON, PRODUCES, BINDS, WITNESSES, GATES, QUARANTINES, ROUTES)
8. ✅ All edge `from` and `to` references point to existing nodes (backreference check)
9. ✅ Graph is acyclic (topological sort must succeed)

**CI Failure Conditions:**
- ❌ Schema validation fails → REJECT
- ❌ wild_text node is not QUARANTINED → REJECT
- ❌ wild_text node has `route_to_mayor == true` → REJECT
- ❌ Graph contains cycle → REJECT
- ❌ Edge references nonexistent node → REJECT

**CI Success Condition:**
- ✅ All validations pass → graph enters CLAIM_COMPOSITION_LAB

---

### Gate 3: Mayor Candidate Packet

**When:** Packet is routed to MAYOR_SQUARE

**Schema:** `mayor_candidate_packet_v1.schema.json`

**Required Validations:**
1. ✅ `schema_version` == "MAYOR_CANDIDATE_PACKET_V1" (const check)
2. ✅ `packet_id` matches pattern `^PKT-[A-Z0-9_-]{6,}$`
3. ✅ `claim_graph_ref` matches pattern `^sha256:` (verifiable hash pointing to CLAIM_GRAPH_V1)
4. ✅ `primary_claim_id` matches pattern `^N-` (references node in graph)
5. ✅ `evidence_bundle.receipts` is non-empty array of sha256 hashes
6. ✅ `evidence_bundle.artifacts` is non-empty array of sha256 hashes
7. ✅ `evidence_bundle.replay.command` is non-empty string
8. ✅ `evidence_bundle.replay.expected_hashes` is non-empty array of sha256 hashes
9. ✅ `tasp_report_ref` matches pattern `^sha256:` (verifiable hash pointing to TASP_GATE report)

**CI Failure Conditions:**
- ❌ Schema validation fails → REJECT (do not route to Mayor)
- ❌ Evidence bundle is empty → REJECT
- ❌ Referenced claim_graph_ref or tasp_report_ref not found → REJECT

**CI Success Condition:**
- ✅ All validations pass → packet enters MAYOR_SQUARE for scoring

---

### Gate 4: Town Routing Policy

**When:** System boots or policy is updated

**Schema:** `town_routing_policy.schema.json`

**Required Validations:**
1. ✅ `schema_version` == "TOWN_ROUTING_POLICY_V1" (const check)
2. ✅ `thresholds.ADVANCE` is number in [0.0, 1.0]
3. ✅ `thresholds.HOLD.min` < `thresholds.HOLD.max` (sanity check)
4. ✅ `thresholds.RETURN` is number in [0.0, 1.0]
5. ✅ Threshold ordering: RETURN < HOLD.min < HOLD.max < ADVANCE (monotone check)
6. ✅ `hard_invariants` is non-empty array (at least one hard law)
7. ✅ All `quarantine_rules` have valid `action` values (enum: QUARANTINE, RETURN, HOLD)

**CI Failure Conditions:**
- ❌ Schema validation fails → BOOT FAIL (system cannot start)
- ❌ Thresholds are not monotone → BOOT FAIL
- ❌ No hard invariants defined → BOOT FAIL

**CI Success Condition:**
- ✅ All validations pass → policy is loaded at boot time

---

## 3. Cross-Schema Validation (Referential Integrity)

Beyond single-schema validation, CI must enforce:

### 3.1 Claim → Graph Reference

**Rule:** Every RESEARCH_CLAIM_V1 referenced in CLAIM_GRAPH_V1 must exist and be valid.

**Check:**
```
For each edge where type == GATES or QUARANTINES:
  if target_node.kind == "policy":
    assert target policy object validates against town_routing_policy.schema.json
```

### 3.2 Graph → Packet Reference

**Rule:** Every CLAIM_GRAPH_V1 referenced in MAYOR_CANDIDATE_PACKET_V1 must be valid.

**Check:**
```
For each packet:
  claim_graph = load(claim_graph_ref)
  assert claim_graph validates against claim_graph_v1.schema.json
  assert primary_claim_id is a node in claim_graph
```

### 3.3 Packet → TASP Report Reference

**Rule:** Every TASP report referenced in a packet must exist and be accessible.

**Check:**
```
For each packet:
  tasp_report = load(tasp_report_ref)
  assert tasp_report.verdict in [ADMISSIBLE, QUARANTINE]
  assert tasp_report.axes_contracted == [A, B, C] for ADMISSIBLE
```

---

## 4. Hard Invariants (Non-Negotiable Laws)

All CI gates must enforce these invariants:

```
I-TIER-III-QUARANTINE:
  if tier == III:
    then admissibility == QUARANTINED (always)
    and quarantine_triggers != empty

I-WILD-TEXT-QUARANTINE:
  if kind == wild_text:
    then admissibility == QUARANTINED (always)
    and route_to_mayor == false (always)

I-NO-ROUTING-FROM-QUARANTINE:
  if admissibility == QUARANTINED:
    then no edge with type == ROUTES from this node

I-ACYCLIC-GRAPH:
  graph must be DAG (topological sort must succeed)

I-THRESHOLD-MONOTONE:
  RETURN < HOLD.min < HOLD.max < ADVANCE

I-EVIDENCE-COMPLETENESS:
  every evidence_handle node must have complete handle object
  every replay object must have command + expected_hashes

I-HASH-PATTERN:
  all artifact hashes must match pattern ^sha256:
  all receipt hashes must match pattern ^sha256:
```

---

## 5. Validation Failure Modes

### Mode 1: Schema Validation Failure

**Action:** Reject the object, log schema mismatch, return error to user.

**Example:**
```
ERROR: research_claim_v1 validation failed
  Path: $.claim_id
  Reason: "RC-123" does not match pattern ^RC-[A-Z0-9_-]{6,}$
  Action: REJECT (object not ingested)
```

### Mode 2: Referential Integrity Failure

**Action:** Reject the object, log missing reference.

**Example:**
```
ERROR: mayor_candidate_packet_v1 validation failed
  Path: $.claim_graph_ref
  Reason: sha256:abc123... not found
  Action: REJECT (packet not routed to Mayor)
```

### Mode 3: Invariant Violation

**Action:** Reject the object, log invariant type, prevent state change.

**Example:**
```
ERROR: hard invariant violation
  Invariant: I-TIER-III-QUARANTINE
  Reason: tier==III but admissibility==ADMISSIBLE
  Action: REJECT (claim not ingested)
```

### Mode 4: Boot Failure

**Action:** Do not start system. Log policy failure.

**Example:**
```
FATAL: town_routing_policy validation failed
  Threshold: HOLD.min >= HOLD.max
  Action: BOOT FAIL (restart required)
```

---

## 6. CI Enforcement Points

| Tool | Stage | Gate | Command |
|---|---|---|---|
| **Schema Validator** | Pre-ingestion | Claims + Graphs | `jsonschema validate -i <obj> -s research_claim_v1.schema.json` |
| **Graph Validator** | Post-decomposition | Cycles + references | `python3 graph_validator.py --check-cycles <graph.json>` |
| **Policy Validator** | Boot-time | Routing policy | `python3 policy_validator.py --check-invariants <policy.json>` |
| **Integration Test** | CI pipeline | All schemas together | `pytest tests/test_schema_integration.py -v` |

---

## 7. Validation Success Criteria

**CI Pipeline Passes If:**

1. ✅ All RESEARCH_CLAIM_V1 objects pass schema validation
2. ✅ All CLAIM_GRAPH_V1 artifacts pass schema + acyclicity checks
3. ✅ All MAYOR_CANDIDATE_PACKET_V1 objects pass schema + reference checks
4. ✅ TOWN_ROUTING_POLICY loads without error + invariants satisfied
5. ✅ All hard invariants are enforced at every gate
6. ✅ All cross-schema references resolve correctly

**CI Pipeline Fails If:**

- ❌ Any schema validation fails
- ❌ Any hard invariant is violated
- ❌ Any reference cannot be resolved
- ❌ Any cycle is detected in graph
- ❌ Policy thresholds are not monotone

---

## 8. Example: Complete Validation Flow

```
User submits RESEARCH_CLAIM_V1:
  ↓
[Gate 1: Claim Ingestion]
  ├─ validate against research_claim_v1.schema.json
  ├─ check: if tier==III then admissibility==QUARANTINED
  └─ PASS → claim enters RESEARCH_SANDBOX
  ↓
[Decomposition to CLAIM_GRAPH_V1]
  ↓
[Gate 2: Graph Decomposition]
  ├─ validate against claim_graph_v1.schema.json
  ├─ check: if kind==wild_text then QUARANTINED + no routing
  ├─ check: graph is acyclic (topological sort)
  └─ PASS → graph ready for Mayor
  ↓
[Packet Creation: MAYOR_CANDIDATE_PACKET_V1]
  ↓
[Gate 3: Mayor Candidate Packet]
  ├─ validate against mayor_candidate_packet_v1.schema.json
  ├─ check: claim_graph_ref resolves to valid graph
  ├─ check: tasp_report_ref resolves to ADMISSIBLE verdict
  └─ PASS → packet routed to MAYOR_SQUARE
  ↓
[Mayor Scoring (uses TOWN_ROUTING_POLICY)]
  ↓
[Gate 4: Town Routing Policy]
  ├─ validate against town_routing_policy.schema.json
  ├─ check: thresholds are monotone
  ├─ check: hard invariants enforced
  └─ PASS → policy applied, routing decision deterministic
  ↓
DECISION: Route to ADVANCE|HOLD|RETURN|QUARANTINE
```

---

## 9. Summary: Validation Contract

**These schemas are frozen. CI gates are non-negotiable.**

**Implementation (Path B) must:**
1. Use these schemas (no modifications)
2. Validate at every gate (no skipping)
3. Enforce all hard invariants (no exceptions)
4. Reject violations immediately (fail fast)

**Result:**
- ✅ No implementation drift (schemas enforce boundaries)
- ✅ Deterministic validation (same input → same verdict)
- ✅ Auditable decisions (every gate is logged)
- ✅ Safe composition (references verified, cycles prevented)

---

**Document Version:** VALIDATION_CONTRACT_V1
**Status:** LOCKED (Path A Formalization Complete)
**Next:** Path B — Minimal validator code (claim_graph_ingestion.py + graph_validator.py)

