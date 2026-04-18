# HELEN OS — Executable Membrane Baseline Checkpoint

**Commit:** `537c9d1`
**Date:** 2026-03-13
**Status:** ✅ Frozen — All 28 tests passing, determinism proven

---

## The Load-Bearing Invariant

```
same packet + same state → same decision → same updated state → same resulting hash
```

This is the first executable proof that HELEN governance is not theoretical.

---

## Core Membrane Modules (9 total)

### Governance Layer
1. **`helen_os/governance/canonical.py`**
   - Deterministic JSON canonicalization (RFC 8785-style)
   - Functions: `canonical_json_bytes()`, `sha256_hex()`, `compute_hash()`
   - Law: Same semantic input → same bytes → same hash

2. **`helen_os/governance/reason_codes.py`**
   - Frozen enum: 9 codes only (7 ERR_*, 2 OK_*)
   - No ad hoc string returns
   - Law: Reducer emits only registered codes

3. **`helen_os/governance/schema_registry.py`**
   - Load and resolve 5 frozen schemas
   - Fail-closed on unknown schema
   - Lazy load at module import

4. **`helen_os/governance/validators.py`**
   - Schema validation + cross-field invariant checking
   - Hash verification (excludes hash field itself)
   - Law: Schema-valid AND invariant-valid

5. **`helen_os/governance/skill_promotion_reducer.py`**
   - Deterministic decision gate: 6 sequential gates
   - Same packet + state → identical ReductionResult
   - Law: Only reducer-emitted decisions may change state

### Evolution Layer
6. **`helen_os/evolution/failure_bridge.py`**
   - Routes only FAILURE_REPORT_V1
   - Rejects untyped failures and leaked sovereign fields
   - Law: Type boundary enforcement

### Execution Layer
7. **`helen_os/executor/helen_executor_v1.py`**
   - Bounded fact recording
   - Emits EXECUTION_ENVELOPE_V1 only
   - Never emits verdicts
   - Law: Non-authoritative task recording

### State Layer
8. **`helen_os/state/skill_library_state_updater.py`**
   - Apply ledger-bound decisions to active skill state
   - Only ADMITTED decisions trigger mutation
   - Law: Mutation gate enforcement

### Proof Layer
9. **`helen_os/replay_proof_v1.py`**
   - Cryptographic determinism proof
   - replay_packet(packet, state, runs=N) → proof struct
   - Law: Zero-drift certification across runs

---

## Frozen Schemas (5 total)

1. **`skill_promotion_packet_v1.json`**
   - Additive schema (can add optional fields like transfer_evidence)
   - Required: schema_name, schema_version, packet_id, skill_id, candidate_version, lineage, capability_manifest_sha256, doctrine_surface, evaluation, receipts

2. **`skill_promotion_decision_v1.json`**
   - Fixed schema (additionalProperties: false)
   - Output of reducer
   - Required: decision_id, skill_id, candidate_version, decision (enum), reason_code

3. **`skill_library_state_v1.json`**
   - Additive schema
   - active_skills: object (key → skill record)
   - Required: schema_name, schema_version, law_surface_version, active_skills

4. **`execution_envelope_v1.json`**
   - Additive schema (output fields extensible)
   - Task execution record with resource usage, exit code, artifact refs

5. **`failure_report_v1.json`**
   - Fixed schema (additionalProperties: false)
   - Typed failure container
   - Blocks leakage of sovereign fields (decision, receipt_hash, verdict)

---

## Core Proof Surface (5 Invariants)

### T1: Reducer Determinism
- **Test:** `test_execution_envelope_determinism.py`
- **Proof:** Same input → same bytes → same hash
- **Mechanism:** Canonical JSON hashing with sorted keys

### T2: Typed Failure Routing
- **Test:** `test_failure_bridge_only_accepts_typed_failures.py`
- **Proof:** Only FAILURE_REPORT_V1 passes; untyped dropped; sovereign fields rejected
- **Mechanism:** Schema validation + field block list

### T3: Admitted-Only State Mutation
- **Test:** `test_skill_library_state_changes_only_on_admitted.py`
- **Proof:** Only ADMITTED decisions change state; other decisions are no-ops
- **Mechanism:** Decision enum gate in state updater

### T4: Frozen Reason Code Registry
- **Test:** `test_reducer_reason_codes_are_frozen.py` + `test_unknown_reason_code_rejected.py`
- **Proof:** 9 codes only; all rejection paths use registered codes
- **Mechanism:** ReasonCode enum + exhaustive path testing

### T5: Replay Proof Stability
- **Test:** `test_replay_proof_v1.py` (3 tests)
- **Proof:** 20+ runs produce identical decision hashes and state hashes
- **Mechanism:** replay_packet() function with hash comparison across runs

---

## Non-Core Wrapper (Explicitly Out of Scope)

**`helen_os/cli/helen_dialog.py`**
- Interactive shell over kernel membrane
- Respects membrane: validators → reducer → state updater
- Non-sovereign: no authority claims
- **Status:** Optional enhancement, not part of core baseline

---

## Test Summary

**Core Gating Tests (25 total):**
- T1: 1 test (determinism)
- T2: 4 tests (failure bridge)
- T3: 1 test (state mutation gate)
- T4: 5 + 3 tests (reason codes frozen + unknown codes rejected)
- T5: 1 test (admitted-only)
- T6: 1 test (replay same packet)
- T7: 1 test (verdict leakage blocked)
- T8: 8 tests (cross-module invariants)

**Determinism Certification (3 tests):**
- RP1: No drift (20+ runs)
- RP2: Identical hashes
- RP3: Rejected packets deterministic

**Total: 28/28 passing** ✅

---

## What This Baseline Does NOT Include

❌ Ledger persistence (append-only historical trace)
❌ Federation (cross-kernel routing)
❌ Visualization (zone state matrix UI)
❌ Autoresearch loop (self-improving system)
❌ Advanced CLI features

These are explicitly post-MVP enhancements.

---

## The Next Smallest Increment

After this checkpoint is frozen, the next admitted delta is:

**LEDGER_APPEND_V1**
- Module: `helen_os/state/decision_ledger_v1.py`
- Single responsibility: Append reducer-emitted decisions as immutable entries
- Single test: `test_decision_ledger_appends_only_reducer_decisions.py`
- Single law: Only reducer-emitted, append-only decision records may extend governed history
- Why: Bridges kernel baseline to institutional memory (decisions → ledger → replayable history)

But this is explicitly deferred. The current checkpoint is complete and locked.

---

## Authority Record

This baseline represents the first executable, determinism-proven constitutional membrane for HELEN OS.

- **Specification:** Frozen (MVP_IMPLEMENTATION_V1)
- **Implementation:** Complete (9 modules, 5 schemas)
- **Testing:** 28/28 green
- **Determinism:** Cryptographically proven (REPLAY_PROOF_V1)
- **Authority:** Constitutional membrane locked

**No further features should be added to this baseline.**

---

**Checkpoint Commit:** `537c9d1`
**CLAUDE.md Updated:** 2026-03-13
**Next Step:** Freeze, then LEDGER_APPEND_V1
