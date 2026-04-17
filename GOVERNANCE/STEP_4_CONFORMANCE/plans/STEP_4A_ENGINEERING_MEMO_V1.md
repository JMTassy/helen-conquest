# STEP_4A ENGINEERING MEMO V1

**To:** Implementation Team
**From:** Audit Phase
**Date:** 2026-04-05
**Subject:** Frozen Boundary Ready for Implementation; /do_next Endpoint Missing

---

## Status

The HELEN kernel boundary has been frozen as constitutional law:

- **API_CONTRACT_DO_NEXT_V1** — Request/response schema (frozen)
- **SESSION_PERSISTENCE_SEMANTICS_V1** — Session state semantics (frozen)
- **LIFECYCLE_INVARIANTS_V1** — 7-phase execution order (frozen)

**Blocker:** The /do_next HTTP endpoint defined by these documents does not exist in the codebase.

**Your task:** Build the auditable /do_next implementation so conformance audit can run.

---

## What Exists (Frozen Law)

Three constitutional documents lock the boundary. Read them in this order:

1. `GOVERNANCE/CONSTITUTION/LIFECYCLE_INVARIANTS_V1.md` — The 7-phase chain (§3)
2. `GOVERNANCE/CONSTITUTION/API_CONTRACT_DO_NEXT_V1.md` — Request/response schema
3. `GOVERNANCE/CONSTITUTION/SESSION_PERSISTENCE_SEMANTICS_V1.md` — Session semantics

Supporting registries:

- `GOVERNANCE/REGISTRIES/README.md` — Points to audit finding codes, receipt types, routing decisions
- `GOVERNANCE/CONSTITUTION/BOUNDARY_FREEZE_V1.md` — Ratification summary

**Key dependency:** These laws reference **INFERENCE_POLICY_FROZEN_V1** (not yet found; may need to create).

---

## What to Build (Minimum Auditable Path)

Implement only what the frozen boundary requires. No feature expansion.

### 1. HTTP /do_next Endpoint

**Location:** `helen_os_scaffold/server.py` or new `helen_os/api/do_next.py`

**Request schema** (API_CONTRACT_DO_NEXT_V1 §3):
```python
{
  "session_id": str,          # required
  "user_input": str,          # required
  "mode": enum,               # required: "deterministic" | "bounded" | "open"
  "model": str,               # required
  "project": str,             # optional
  "max_context_messages": int, # optional
  "include_reasoning": bool,   # optional
  "temperature": float,        # optional (0.0-2.0)
  "top_p": float,              # optional (0.0-1.0)
  "seed": int                  # optional
}
```

**Response schema** (API_CONTRACT_DO_NEXT_V1 §4):
```python
{
  "session_id": str,
  "mode": str,
  "model": str,
  "reply": str or null,
  "receipt_id": str or null,
  "run_id": int or null,
  "context_items_used": list[str] or null,
  "epoch": int or null,
  "continuity": float or null
}
```

**Status codes:**
- 200: Success (executed or deferred)
- 400: Validation error or audit block
- 401: Unauthorized
- 500: Server error

### 2. Seven Frozen Phases

Implement each phase in strict order (LIFECYCLE_INVARIANTS_V1 §3). Emit receipts at each step.

**Phase 1: Request Validation**
- Validate all required fields
- Type-check all fields
- Reject unknown fields
- Return 400 on validation fail
- No receipt emitted

**Phase 2: Session Load / Resumption**
- Load session from persistence by session_id, or create new
- Emit SESSION_RESUMPTION receipt if resumed
- Return 400 if session corrupted (hash mismatch)

**Phase 3: Knowledge Audit**
- Call audit_knowledge_state(session_id, memory_objects, recent_receipts)
- Get findings + routing_consequence (ANNOTATE|DEFER|REJECT)
- Emit KNOWLEDGE_AUDIT receipt
- Record findings

**Phase 4: Dispatch Decision**
- Map audit consequence to routing decision (KERNEL|DEFER|REJECT)
- Emit DISPATCH_DECISION receipt (unless REJECT)
- If REJECT: return 400 error

**Phase 5: Consequence or Block**
- If KERNEL: call LLM inference, get reply
- If DEFER: queue for later
- Emit INFERENCE_EXECUTION or DEFERRED_EXECUTION receipt

**Phase 6: Memory & Receipt Consolidation**
- Update session memory with findings, facts
- Finalize receipt chain (verify lineage, no orphans)
- Emit CONCLUSION receipt

**Phase 7: Persistence & Response**
- Hash updated session state
- Write to persistence atomically
- Emit SESSION_COMMIT receipt (after write succeeds)
- Build and return DoNextResponse

### 3. Receipt Emission Helpers

Create minimal receipt functions:

```python
def emit_session_resumption(session_id, prior_run_count, prior_epoch, prior_continuity, new_continuity):
    # Return receipt dict with required fields
    # parent_receipt_id = null (root)
    pass

def emit_knowledge_audit(session_id, findings, routing_consequence, parent_receipt_id=None):
    # Return receipt dict
    # registry_version = "1.0.0"
    pass

def emit_dispatch_decision(session_id, routing_decision, parent_receipt_id, epoch):
    # Return receipt dict
    # Only emit if routing_decision != REJECT
    pass

def emit_inference_execution(session_id, reply_length, context_count, parent_receipt_id):
    # Return receipt dict if LLM executed
    pass

def emit_deferred_execution(session_id, queue_position, parent_receipt_id):
    # Return receipt dict if deferred
    pass

def emit_conclusion(session_id, receipt_chain_hash, parent_receipt_id):
    # Return receipt dict
    # Only if not blocked
    pass

def emit_session_commit(session_id, state_hash, run_count, parent_receipt_id):
    # Return receipt dict (after successful persistence write)
    pass
```

### 4. Session Persistence Integration

Use SESSION_PERSISTENCE_SEMANTICS_V1 semantics:

- **Session load:** Resume from persistence, verify state_hash, emit SESSION_RESUMPTION
- **Continuity computation:** Compute on pre-call state (before run_count increment)
- **Epoch:** Consume one epoch per accepted call
- **Persistence:** Write atomically with SESSION_COMMIT receipt
- **Resumption atomicity:** Full restore or fail; no partial state

### 5. Phase Markers for Audit Tracing

For Step 4A conformance to work, make each phase traceable:

Option A: Add logging at each phase entry/exit
```python
logger.info(f"PHASE_1_REQUEST_VALIDATION: {session_id}")
logger.info(f"PHASE_2_SESSION_LOAD: {session_id}")
# ... etc
```

Option B: Return phase trace in response (internal field, not exposed to client)

Either way, Step 4A audit will need to trace the phases in the actual code execution.

---

## What NOT to Build (Exclusion List)

❌ Do not implement Knowledge Compiler V2 features
❌ Do not add Temple exploration logic
❌ Do not implement AQO or spectral reasoning
❌ Do not build advanced memory reasoning
❌ Do not add custom routing policies

**Focus:** Minimum auditable boundary only.

---

## Dependencies

Your implementation may need:

1. **audit_knowledge_state()** — Audit subsystem (Phase 3)
   - Should emit findings per AUDIT_FINDING_REGISTRY_V1
   - Should compute routing_consequence (ANNOTATE|DEFER|REJECT)
   - May already exist; verify location

2. **LLM inference call** — (Phase 5)
   - Should support frozen model, temperature, top_p, seed
   - INFERENCE_POLICY_FROZEN_V1 must define these; locate or create

3. **Session persistence** — (Phase 2, 7)
   - Load/save session state
   - Compute/verify state_hash
   - Manage recent_receipts horizon (capped at 100)

4. **Epoch management** — (Phase 7)
   - One epoch per call
   - Monotonic across all sessions
   - Source from single authoritative location

5. **Receipt emission** — (All phases)
   - UUID generation
   - Lineage tracking (parent_receipt_id)
   - Canonical JSON hashing for receipt chain

---

## Conformance Gate

Once you build /do_next:

**Step 4A will run five conformance passes:**

1. **Phase Trace** — Map live code to frozen 7-phase chain
2. **Receipt Lineage** — Verify parent/root/commit-witness semantics
3. **Epoch & Persistence** — Verify single increment, atomic commit
4. **Replay Conformance** — Same state + request = same response (except IDs)
5. **Master Verdict** — PASS/FAIL/AMBIGUOUS classification per constitutional clause

**Hard gate:** Zero CRITICAL violations required for Knowledge Compiler V2 unblock.

---

## Success Criteria

Your /do_next implementation is complete when:

- ✅ All 7 phases execute in strict order (no skip, no reorder)
- ✅ Session load/resumption works (SESSION_RESUMPTION receipt emitted)
- ✅ Audit is called (KNOWLEDGE_AUDIT receipt emitted)
- ✅ Dispatch maps to routing (DISPATCH_DECISION or REJECT)
- ✅ Consequence executes (INFERENCE_EXECUTION or DEFERRED)
- ✅ Memory is updated (CONCLUSION receipt)
- ✅ Session is persisted atomically (SESSION_COMMIT receipt)
- ✅ Response returns per API_CONTRACT schema
- ✅ All receipts have correct parent_receipt_id (no orphans)
- ✅ Epoch increments exactly once per accepted call

---

## No Meta-Docs After This

This memo seals the frozen boundary documentation.

**Going forward:** Build code, not more governance docs. The law is locked.

---

**Next step: Implement /do_next endpoint. Then Step 4A audit runs.**

