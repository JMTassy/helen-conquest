# KNOWLEDGE COMPILER V2 — OVERVIEW & RATIFICATION REQUEST

**Version:** 2.0.0-DRAFT (awaiting ratification)
**Date:** 2026-04-05
**Status:** PROPOSAL

---

## What Is Knowledge Compiler V2?

A bounded execution framework that lets HELEN **propose and execute** limited actions (file writes, edits, analysis, routing) with complete receipt instrumentation and replay safety.

**Current State (Step 4A):**
- HELEN answers queries through /do_next
- Client initiates every action
- No proactive suggestions

**With V2:**
- HELEN proposes ExecutionPlans (frozen at /init)
- BoundedExecutor executes with strict phase order
- Complete receipt chain (DECISION → EXECUTION → ARTIFACT)
- Deterministic replay with idempotence detection
- All mutations auditable, bounded, fail-closed

---

## Why Now?

Step 4A established that /do_next is:
- ✅ Replayable (state hash verified)
- ✅ Auditable (complete receipt chains)
- ✅ Deterministic (same state + request → same response)

These guarantees enable safe bounded execution. V2 extends this from **reactive responses** (answering queries) to **proactive proposals** (suggesting actions).

---

## 5-Layer Architecture

```
Layer 1: Request → ExecutionPlan (frozen at /init)
  ↓
Layer 2: Plan → Decision Receipt (authorization)
  ↓
Layer 3: Plan → Tool Handler (execute action)
  ↓
Layer 4: Handler Output → Artifact + Receipts
  ↓
Layer 5: Idempotence Check → Response
```

Each layer emits receipts before mutation. Fail-closed everywhere.

---

## 4 Initial Handlers (Stage B.1)

| Handler | Type | Target | Risk | Status |
|---------|------|--------|------|--------|
| **WriteFileHandler** | write | New file | LOW | ✅ Included |
| **EditFileHandler** | edit | Existing file | LOW | ✅ Included |
| **AnalyzeHandler** | analyze | Data (read-only) | NONE | ✅ Included |
| **RouteHandler** | route | Service queue | LOW | ✅ Included |
| **DeleteHandler** | delete | File deletion | HIGH | ❌ Deferred to V2.1 |

**Why defer DELETE?** Highest-risk action (irreversible). Prove core 4 handlers first, then extend.

---

## Five Frozen Laws

1. **Fail-Closed Semantics** — Error always, never guess
2. **No Out-of-Target Mutations** — Side effects only within declared scope
3. **Receipt-Before-Write** — Authorization receipt before any mutation
4. **Deterministic Bounded Execution** — Same plan + state → identical result
5. **Idempotence Detection** — Skip duplicate executions via idempotence key

---

## Success Criteria

### Implementation
- ✅ 4 handlers (WRITE, EDIT, ANALYZE, ROUTE)
- ✅ 7-phase lifecycle (validate → idempotence → decide → execute → receipt → canonicalize → respond)
- ✅ Fail-closed enforcement
- ✅ No out-of-target mutations
- ✅ Receipt-before-write invariant
- ✅ Deterministic output (10 runs identical)
- ✅ Idempotence detection (skip duplicates)

### Testing
- ✅ 42 comprehensive tests (all passing)
- ✅ Unit + integration + CLI + interruption/replay
- ✅ Bounds enforcement verified
- ✅ Receipt chain integrity verified
- ✅ Determinism verified (10/10 runs)

### Audit (Step 5)
- ✅ Phase Trace conformance
- ✅ Receipt Lineage conformance
- ✅ Bounds Enforcement conformance
- ✅ Idempotence conformance
- ✅ Determinism conformance

**Gate:** Zero CRITICAL violations required

---

## Timeline

- **Design:** 2 hours (this spec)
- **Implementation:** 10-14 hours (handlers + executor + tests)
- **Audit:** 2-4 hours (Step 5 conformance passes)
- **Total:** ~16-20 hours across 3-4 days

---

## What It Enables (After V2)

1. **Autonomous Action Proposals**
   - HELEN: "I can write a summary to `/tmp/summary.md`"
   - Receipt: DECISION receipt (authorization before action)
   - Execution: WriteFileHandler writes file
   - Receipt: EXECUTION + ARTIFACT receipts (proof of completion)

2. **Bounded Failure Recovery**
   - If write fails: ToolResult.status="FAILED"
   - No partial state (fail-closed)
   - Receipt trail explains why

3. **Replay Auditing**
   - Same ExecutionPlan + same state → same result_hash
   - No "did it work last time?" ambiguity
   - Deterministic proof of what happened

4. **Idempotent Retries**
   - Client retries same request
   - Idempotence key detected
   - Server returns SKIPPED (no duplicate execution)
   - Safe recovery from network failures

---

## What It Does NOT Enable (Deferred)

❌ **DELETE Handler** — Too risky without rollback design (V2.1)
❌ **Multi-Step Workflows** — Single action per plan (Stage C)
❌ **Conditional Branching** — "If A succeeds, then B" (Stage C)
❌ **Long-Running Jobs** — Status polling, checkpoints (Stage C)

---

## Relationship to Constitutional Framework

**Frozen Layer:** /do_next boundary (API_CONTRACT_DO_NEXT_V1, SESSION_PERSISTENCE_SEMANTICS_V1, LIFECYCLE_INVARIANTS_V1) ✅ Audited Step 4A

**Building on That:** Knowledge Compiler V2 (ExecutionPlan_v1, BoundedExecutor, Tool Handlers) ← YOU ARE HERE

**Next Phase:** Stage C projection fabric (multi-step plans, autonomy loop) ← Future

---

## Ratification Request

**I propose to:**

1. **Ratify KNOWLEDGE_COMPILER_V2_SPECIFICATION.md** (v2.0.0)
   - Freeze ExecutionPlan_v1 schema
   - Freeze 7-phase BoundedExecutor lifecycle
   - Freeze 5 constitutional laws
   - Freeze Stage B.1 scope (4 handlers, 42 tests, Step 5 audit)

2. **Proceed with Stage B.1 Implementation**
   - Build all 4 handlers + executor + tests
   - Run Step 5 conformance (5 passes)
   - Report findings

3. **Gate Knowledge Compiler V2 at Zero Violations**
   - Stage C (projection fabric) unblocked only if Step 5 = PASS, zero critical violations

---

## Recommendation

✅ **PROCEED** — The frozen /do_next boundary provides sufficient guarantees. V2 design is sound. Stage B.1 is low-risk (WRITE, EDIT, ANALYZE, ROUTE are all bounded and testable).

**Key Safety Features:**
- ✅ Fail-closed everywhere (no silent failures)
- ✅ Receipt instrumentation (complete audit trail)
- ✅ Deterministic replay (provable correctness)
- ✅ Idempotence (safe retries)
- ✅ Bounds enforcement (latency, bytes, target count)

---

**Awaiting your approval to freeze this spec and begin Stage B.1 implementation.**
