# HELEN OS — Proven Membrane Claims

**Checkpoint:** `52b062c`
**Date:** 2026-03-13
**Test Status:** 28/28 passing ✅

---

## What is Legitimately Proven

At the current scope, we have cryptographic and operational evidence for:

### 1. **Deterministic Canonicalization**
- Same semantic JSON input → same byte sequence
- Same byte sequence → same SHA256 hash
- Tested: `test_execution_envelope_determinism.py`
- Tool: RFC 8785-style canonical ordering with `sort_keys=True`

### 2. **Frozen Reason-Code Surface**
- 9 codes only: 7 ERR_* + 2 OK_*
- No ad hoc string codes permitted
- All reducer output paths use registered codes
- Tested: `test_reducer_reason_codes_are_frozen.py` (5 tests)
- Tested: `test_unknown_reason_code_rejected.py` (3 tests)

### 3. **Schema-Validated Artifact Intake**
- 5 frozen schemas: packet, decision, state, envelope, failure
- Fail-closed on unknown schema
- Fail-closed on missing required fields
- Tested: `test_skill_promotion_requires_receipts.py` (9 tests)

### 4. **Typed Failure Routing**
- Only FAILURE_REPORT_V1 passes through bridge
- Untyped failures dropped (return None)
- Sovereign fields (decision, receipt_hash) rejected
- Tested: `test_failure_bridge_only_accepts_typed_failures.py` (4 tests)

### 5. **Promotion Reduction (6-Gate Decision)**
- Gate 1: Schema validity
- Gate 2: Receipt presence
- Gate 3: Receipt hash integrity
- Gate 4: Capability lineage (parent skill must be active)
- Gate 5: Doctrine match (law surface version)
- Gate 6: Evaluation threshold
- All gates enforce specific error codes
- Tested: `test_skill_promotion_requires_receipts.py` (9 tests)

### 6. **Admitted-Only State Mutation**
- Only ADMITTED decisions change active_skills
- REJECTED, QUARANTINED, ROLLED_BACK are no-ops
- State is immutable copy (new dict, not reference)
- active_skills is object/dict keyed by skill_id (per schema)
- Tested: `test_skill_library_state_changes_only_on_admitted.py` (1 test)

### 7. **Replay Stability (Zero-Drift Proof)**
- Same packet + same state → identical decision hash
- Same packet + same state → identical state hash
- 20 runs with REPLAY_PROOF_V1 → all hashes match
- Tested: `test_replay_proof_v1.py` (3 tests)
- Tested: `test_replay_same_packet_same_decision.py` (1 test)

---

## The Legitimate Statement

**HELEN now has an executable, replay-stable kernel membrane for skill promotion and governed state mutation.**

This is:
- ✅ Defensible (all proofs are in the tests)
- ✅ Measurable (28/28 passing, determinism proven)
- ✅ Reproducible (same input always produces same output)
- ✅ Schema-enforced (5 frozen schemas with validation)

---

## What is NOT Yet Proven

Do not claim:

- ❌ "Fully operational" — requires ledger history + replay mechanism
- ❌ "Institutional memory complete" — requires append-only ledger
- ❌ "Governance runtime complete" — requires multi-round orchestration
- ❌ "Autoresearch loop live" — requires decision loop + feedback
- ❌ "Federation ready" — requires cross-kernel routing

These require additional modules and tests.

---

## Schema Alignment Checkpoint

The state updater fix reveals an important property:

**SKILL_LIBRARY_STATE_V1 is now locked in shape:**

```json
{
  "schema_name": "SKILL_LIBRARY_STATE_V1",
  "schema_version": "1.0.0",
  "law_surface_version": "v1",
  "active_skills": {
    "skill_id_string": {
      "active_version": "string",
      "status": "string",
      "last_decision_id": "string"
    }
  }
}
```

**Canonical property:**
- `active_skills` is an object (dict), never a list
- Keys are skill_id strings
- Values are skill records with 3 required fields
- No extra fields allowed (additionalProperties: false)

Every module that touches this state must respect this shape. No exceptions.

---

## Test Breakdown (28 total)

**Core Gating Tests (25):**
- Determinism: 1
- Failure bridge: 4
- Reason codes: 8
- Reducer gates: 9
- State mutation: 1
- Verdict leakage: 1
- Unfrozen code paths: 1

**Determinism Certification (3):**
- No drift (20+ runs): 1
- Identical hashes: 1
- Rejected packets deterministic: 1

**Test Quality:**
- No flaking (all pass consistently)
- No isolation issues (tests independent)
- Full coverage of decision paths

---

## Commits (This Session)

| Commit | Message |
|--------|---------|
| `537c9d1` | Freeze HELEN executable membrane baseline with REPLAY_PROOF_V1 and 28/28 green |
| `42bc197` | Document frozen membrane baseline checkpoint (537c9d1) |
| `52b062c` | Fix skill library state updater to align with frozen state schema and keep 28/28 green |

---

## Authority Record

**Proven:**
- Deterministic decision reduction ✅
- Admitted-only state mutation ✅
- Typed error boundary ✅
- Frozen reason code registry ✅
- Replay stability across runs ✅

**Not yet proven (post-MVP):**
- Ledger append-only persistence
- Historical decision replay
- Cross-kernel federation
- Loop orchestration

**Next legitimate increment:**
- LEDGER_APPEND_V1 (decision history)

---

**Status:** Membrane baseline proven and defensible.
**Scope:** Skill promotion + state mutation only.
**Authority:** Constitutional kernel, not civilization runtime.
