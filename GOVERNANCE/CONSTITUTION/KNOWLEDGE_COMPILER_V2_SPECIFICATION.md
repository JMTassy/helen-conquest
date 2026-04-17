# KNOWLEDGE COMPILER V2 SPECIFICATION

**Version:** 2.0.0-DRAFT
**Status:** PROPOSAL (awaiting ratification)
**Date:** 2026-04-05
**Authority:** Builds on frozen LIFECYCLE_INVARIANTS_V1, SESSION_PERSISTENCE_SEMANTICS_V1, API_CONTRACT_DO_NEXT_V1
**Gate Prerequisite:** Step 4A audited (✅ PASS, zero violations)

---

## Executive Summary

**What:** Knowledge Compiler V2 adds intelligent **projection** to HELEN — the ability to propose bounded actions (write files, edit content, analyze data, route tasks) with complete receipt chains and deterministic replay.

**Why:** The frozen /do_next boundary now guarantees that:
- Sessions are replayable (state hash verified on resume)
- Decisions are auditable (complete receipt chains)
- Execution is deterministic (same state + request → same response)

With these guarantees, HELEN can safely propose actions without losing accountability.

**Scope:** Implement BoundedExecutor with 4 initial tool handlers (WRITE, EDIT, ANALYZE, ROUTE) + comprehensive tests. DELETE handler deferred to V2.1 (more risky, requires extended rollback testing).

**Success Criterion:** Stage B passes all tests with zero out-of-target mutations, zero silent duplicates, zero mutations without receipts.

---

## Problem Statement

**Current State (Step 4A):**
- HELEN answers queries through /do_next
- Client initiates every action
- No proactive suggestions
- No bounded execution framework

**Gap:**
- Cannot propose file writes, edits, analyses, routing decisions
- Cannot prove mutations are bounded to declared targets
- Cannot detect and skip duplicate executions
- Cannot guarantee replay safety for projections

**Solution:**
- Knowledge Compiler V2: Bounded execution with complete receipt instrumentation
- Tool handlers with deterministic side effects (mutations strictly within declared scope)
- Idempotence detection (skip duplicate executions via idempotence key)
- Full replay conformance (same state + plan → same result)

---

## Architecture: 5-Layer Execution Stack

### Layer 1: Request → ExecutionPlan (Frozen at /init)

**Entry Point:** `/init HELEN` or CLI
**Output:** `ExecutionPlan_v1` (frozen, immutable)

```json
{
  "plan_id": "plan_xyz_001",
  "session_id": "sess_123",
  "action_id": "write_file_001",
  "execution_type": "write",
  "target": "/tmp/output.txt",
  "tool": "file_writer_v1",
  "input_basis": {
    "source": ["knowledge_base_item_001", "query_result_002"],
    "data_hash": "sha256(...)"
  },
  "bounds": {
    "max_latency_ms": 5000,
    "max_bytes_written": 1048576,
    "fail_on_ambiguity": true,
    "rollback_on_error": true,
    "max_targets": 1
  },
  "idempotence_key": "hash_of_plan_content",
  "preconditions": [...],
  "postconditions": [...]
}
```

**Frozen Properties (per API_CONTRACT):**
- ✅ Single target (max_targets = 1)
- ✅ Explicit execution_type (closed enum: WRITE, EDIT, ANALYZE, ROUTE)
- ✅ Fail-on-ambiguity = true (never guess)
- ✅ Bounds enforced (latency timeout, byte limit)

---

### Layer 2: ExecutionPlan → Decision Receipt (Phase 1 of Bounded Execution)

**Handler:** BoundedExecutor._phase_1_decision()

**Operations:**
1. Validate plan structure (version, fields, enum values)
2. Check idempotence key (prior execution detection)
3. Emit PRE-EXECUTION DECISION receipt (what we will do)

**Decision Receipt Content:**
```json
{
  "receipt_type": "DECISION",
  "session_id": "sess_123",
  "action_id": "write_file_001",
  "decision_basis": "frozen_execution_plan",
  "decision_mode": "non_interpretive_execution",
  "confidence": null,  // NOT a prediction; execution is deterministic
  "target": "/tmp/output.txt",
  "execution_type": "write"
}
```

**Key Invariant:** Decision receipt emitted BEFORE any mutation (authorization receipt).

---

### Layer 3: Plan → Tool Handler Execution (Phase 2)

**Handlers (Stage B.1 - Initial Scope):**

#### 1. **WriteFileHandler** (execution_type = "write")
- Creates file at target path
- Constraints: `allow_create=true`, path is absolute, within bounds
- Side effects: File creation only (target path)
- Fail-closed: Path traversal → error, no write
- Returns: ToolResult with artifact_hash, bytes_written, status

#### 2. **EditFileHandler** (execution_type = "edit")
- Modifies existing file (append, replace, or partial edit)
- Constraints: `allow_edit=true`, target must exist, within bounds
- Side effects: File modification only (target path)
- Fail-closed: File locked or not found → error, no partial write
- Returns: ToolResult with artifact_hash, bytes_written, status

#### 3. **AnalyzeHandler** (execution_type = "analyze")
- Read-only analysis (code parsing, text summarization, data extraction)
- Constraints: `allow_analyze=true`
- Side effects: None (read-only)
- Fail-closed: Malformed input → error, no hallucination
- Returns: ToolResult with analysis_result_hash, tokens_used, status

#### 4. **RouteHandler** (execution_type = "route")
- Queue/forward work to service or queue (fire-and-forget)
- Constraints: `allow_route=true`, target service in allowlist
- Side effects: Queue entry creation only (remote service engagement)
- Fail-closed: Service unreachable → error, no silent drop
- Returns: ToolResult with queue_receipt_hash, artifact_type="queue_receipt"

**Critical:** ROUTE handler returns status=SUCCESS but artifact_type="queue_receipt" (non-authoritative). Status does NOT mean remote task executed.

---

### Layer 4: Handler Output → Artifact + Receipt (Phase 2 of Bounded Execution)

**Handler Returns:**
```python
@dataclass
class ToolResult:
    status: str  # "SUCCESS", "FAILED", "TIMEOUT"
    result_hash: Optional[str]  # sha256 of canonical result
    artifact_hash: Optional[str]  # sha256 of artifact (file, analysis, queue receipt)
    artifact_uri: Optional[str]  # path or identifier
    latency_ms: float
    bytes_written: Optional[int]
    tokens_used: Optional[int]
    error_code: Optional[str]  # e.g., "PRECONDITION_FAILED"
    error_detail: Optional[str]
```

**Execution Receipt Emission:**
```json
{
  "receipt_type": "EXECUTION",
  "session_id": "sess_123",
  "action_id": "write_file_001",
  "idempotence_key": "hash_of_plan",
  "execution_type": "write",
  "status": "SUCCESS",
  "decision_receipt_hash": "...",  // Binding to decision
  "result_hash": "sha256(...)",
  "artifact_hash": "sha256(...)",
  "artifact_uri": "/tmp/output.txt",
  "latency_ms": 234.5,
  "error_code": null
}
```

**Artifact Receipt Emission:**
```json
{
  "receipt_type": "ARTIFACT",
  "session_id": "sess_123",
  "action_id": "write_file_001",
  "execution_receipt_hash": "...",  // Binding to execution
  "artifact_hash": "sha256(...)",
  "artifact_type": "file",  // or "analysis_result", "queue_receipt"
  "artifact_uri": "/tmp/output.txt"
}
```

**Receipt Chain (Layer 4):**
```
DECISION (what we will do)
  ↓
EXECUTION (what happened)
  ↓
ARTIFACT (what was produced)
```

---

### Layer 5: Idempotence Check & Response (Phase 3 of Bounded Execution)

**Idempotence Logic:**

```python
def check_prior_execution(idempotence_key, session_id):
    """Return prior execution receipt if found, else None."""
    # Query receipt ledger for (session_id, idempotence_key) pair
    # If found: execution already happened; return skip status
    # If not found: new execution; proceed
```

**Skip Response (if idempotence detected):**
```python
ExecutionReceipt(
    status="SKIPPED",
    prior_execution_receipt_hash="...",
    reason="Duplicate execution detected"
)
```

**Success Response (normal execution):**
```python
ExecutionReceipt(
    status="SUCCESS",
    decision_receipt_hash="...",
    execution_receipt_hash="...",
    artifact_receipt_hash="...",
    result_hash="...",
    artifact_hash="...",
    artifact_uri="/tmp/output.txt"
)
```

---

## Frozen Laws (Knowledge Compiler V2)

### Law 1: Fail-Closed Semantics

**Principle:** Any error → stop, never guess or fallback.

**Enforcement:**
- Path traversal attempt → error, no write
- File not found → error, no partial edit
- Malformed input → error, no hallucination
- Service unreachable → error, no silent drop

**Code Pattern:**
```python
def execute(plan: ExecutionPlan, bounds: Bounds) -> ToolResult:
    try:
        result = perform_action(...)
    except Exception as e:
        if bounds.fail_on_ambiguity:  # ALWAYS true
            return ToolResult(status="FAILED", error_code="...", error_detail=str(e))
```

### Law 2: No Out-of-Target Mutations

**Principle:** Mutations happen ONLY within declared scope (target path, target service).

**Enforcement:**
- WRITE: Only at target path (no side effects)
- EDIT: Only target file (no side effects)
- ANALYZE: Zero mutations (read-only)
- ROUTE: Only queue entry (no remote execution claimed)

**Verification:** Receipt includes artifact_uri (declared target). Audit compares declared ≠ actual = violation.

### Law 3: Receipt-Before-Write Invariant

**Principle:** No mutation without prior authorization receipt.

**Enforcement:**
1. Emit DECISION receipt (what we will do) — BEFORE execution
2. Execute handler (perform mutation)
3. Emit EXECUTION receipt (what happened) — AFTER execution
4. Emit ARTIFACT receipt (what was produced) — AFTER artifact verified

**Violation:** Missing DECISION receipt before mutation = constitutional breach.

### Law 4: Deterministic Bounded Execution

**Principle:** Same plan + same state + frozen handler = identical result (modulo metadata).

**Enforcement:**
- Handlers are pure-ish (no implicit dependencies)
- No randomness (seed frozen in plan)
- No time-dependent behavior (timestamps not compared in determinism checks)
- Canonical hashing (sort_keys=True for JSON)

**Verification:** Replay same plan on same state → identical result_hash, artifact_hash.

### Law 5: Idempotence Detection

**Principle:** Same idempotence_key → skip execution, return SKIPPED.

**Enforcement:**
- Compute idempotence_key = hash(plan_content)
- Query ledger for (session_id, idempotence_key)
- If found: return SKIPPED with prior_receipt_hash
- If not found: execute and record

**Implication:** Client can retry failed request without duplicating execution.

---

## Success Criteria (Stage B.1)

### Implementation Criteria

✅ All 4 handlers (WRITE, EDIT, ANALYZE, ROUTE) implemented
✅ All 7 phases execute in order:
  1. Plan validation (version, fields, enum)
  2. Idempotence check (prior execution detection)
  3. Pre-execution DECISION receipt
  4. Handler execution (with bounds enforcement)
  5. Execution receipt + artifact receipt
  6. Result canonicalization (hash verification)
  7. Ledger entry and response

✅ Fail-closed enforcement (errors never silent)
✅ No out-of-target mutations (artifact_uri matches target)
✅ Receipt-before-write invariant (DECISION before execution)
✅ Deterministic output (10 runs identical on canonical content)
✅ Idempotence detection (no silent duplicates)

### Testing Criteria

✅ Unit tests: 12 (3 per handler × 4 handlers)
✅ Integration tests: 15 (phase order, bounds, receipts, handlers)
✅ CLI tests: 5 (load boot summary, extract plan, execute, status)
✅ Interruption/Replay tests: 10 (normal execution, idempotence, bounds, determinism)
✅ Total: 42 tests, all passing

### Audit Criteria

✅ Zero CRITICAL violations
✅ Zero out-of-target mutations across all tests
✅ Zero mutations without receipt across all tests
✅ Zero silent duplicates (idempotence verified)
✅ 10/10 replay runs canonical-identical
✅ Receipt chain complete (no orphans) across all tests

---

## Scope: What IS Included (Stage B.1)

✅ **ExecutionPlan_v1** (frozen specification)
✅ **4 Tool Handlers:** WRITE, EDIT, ANALYZE, ROUTE
✅ **BoundedExecutor:** 7-phase execution lifecycle
✅ **ReceiptEmitter:** DECISION, EXECUTION, ARTIFACT receipt types
✅ **Idempotence:** Prior execution detection
✅ **Bounds Enforcement:** Latency timeout, byte limit, target count
✅ **Fail-Closed:** All error paths explicit
✅ **Tests:** 42 comprehensive tests

---

## Scope: What is DEFERRED (Stage B.2)

❌ **DELETE Handler** — Deferred to V2.1
- Reason: Highest-risk action (irreversible)
- Requires: Extended rollback/replay testing, audit trail design
- Gate: Stage B.1 complete (4 handlers proven) + all tests passing

❌ **Advanced Routing** — Deferred to V3
- Multi-hop workflows (route A → route B → execute C)
- Conditional branching (if A succeeds, then B)
- Long-running jobs with status polling

❌ **Projection Fabric** — Deferred to Stage C
- HELEN proposing action sequences (not just single actions)
- Multi-step plans with contingencies
- Autonomous error recovery

---

## Conformance Gate

**Prerequisite:** Step 4A audited (✅ PASS)

**Next Phase:** Step 5 conformance audit

**Five Conformance Passes (will execute):**
1. **Phase Trace** — All 7 phases in order
2. **Receipt Lineage** — Complete, acyclic, witness receipt
3. **Bounds Enforcement** — Latency timeout, byte limit, target validation
4. **Idempotence** — Duplicate detection, skip on rerun
5. **Determinism** — 10 runs identical on canonical content

**Go/No-Go Gate:** Zero CRITICAL violations required to unblock Stage C.

---

## Implementation Timeline (Estimate)

- Phase 1: ExecutionType extension (1 hour)
- Phase 2: Tool handlers (3-4 hours)
- Phase 3: BoundedExecutor (2-3 hours)
- Phase 4: CLI integration (1-2 hours)
- Phase 5: Tests (2-3 hours)
- Buffer: 1.5-2 hours

**Total:** 10-14 hours across 2-3 days

**Milestone:** After Phase 3 + Phase 5, core executor is proven (WRITE/EDIT/ANALYZE/ROUTE).

---

## Risk Assessment

### Risk 1: Out-of-Target Mutations
**Likelihood:** Medium (careless handler implementation)
**Mitigation:** Audit receipt artifact_uri vs declared target; tests validate bounds

### Risk 2: Silent Duplicates
**Likelihood:** Low (idempotence key hashing is deterministic)
**Mitigation:** Idempotence test suite; ledger query on every call

### Risk 3: Mutation Without Receipt
**Likelihood:** Low (fail-closed enforcement)
**Mitigation:** Phase 2 always emits DECISION before handler execution

### Risk 4: Non-Deterministic Results
**Likelihood:** Low (no randomness, frozen parameters)
**Mitigation:** 10-run determinism test; canonical JSON hashing

### Risk 5: Bounds Bypass
**Likelihood:** Low (bounds checked before execution)
**Mitigation:** Timeout enforcement, byte limit validation, target count check

---

## Next Steps (Awaiting Ratification)

1. **Ratify this specification** — Freeze Knowledge Compiler V2 spec (2.0.0)
2. **Implement Stage B.1** — 4 handlers + 42 tests (10-14 hours)
3. **Run Step 5 conformance** — 5 audit passes
4. **Report findings** — Zero violations → Stage C unblocked

---

## Appendix: ExecutionPlan_v1 JSON Schema (Frozen)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExecutionPlan_v1",
  "type": "object",
  "required": [
    "plan_id",
    "session_id",
    "action_id",
    "execution_type",
    "target",
    "tool",
    "bounds",
    "idempotence_key"
  ],
  "properties": {
    "plan_id": {
      "type": "string",
      "pattern": "^plan_[a-z0-9_]{1,64}$"
    },
    "session_id": {
      "type": "string",
      "pattern": "^[a-z0-9_]{1,256}$"
    },
    "action_id": {
      "type": "string"
    },
    "execution_type": {
      "type": "string",
      "enum": ["write", "edit", "analyze", "route"]
    },
    "target": {
      "type": "string",
      "minLength": 1
    },
    "tool": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string" }
      }
    },
    "input_basis": {
      "type": "object",
      "properties": {
        "source": { "type": "array" },
        "data_hash": { "type": "string" }
      }
    },
    "bounds": {
      "type": "object",
      "required": ["fail_on_ambiguity", "max_targets"],
      "properties": {
        "max_latency_ms": { "type": "integer", "minimum": 100 },
        "max_bytes_written": { "type": "integer" },
        "fail_on_ambiguity": { "type": "boolean", "const": true },
        "max_targets": { "type": "integer", "const": 1 }
      }
    },
    "idempotence_key": {
      "type": "string"
    }
  }
}
```

---

**Status:** Ready for ratification
**Confidence:** HIGH (builds on proven /do_next boundary, applies known patterns)
**Next Action:** User approval to proceed with Stage B.1 implementation
