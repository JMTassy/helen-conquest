# REASON_CODES.md

**Single Source of Truth for Failure Reason Codes**

This document defines the canonical machine-readable reason codes used throughout the WUL-CORE + Oracle Town + POC Factory system. All blocking conditions, validation failures, and NO_SHIP decisions MUST reference codes from this list.

---

## 1. Purpose

- **Determinism:** Same failure produces same code across runs
- **Auditability:** Codes are immutable identifiers for post-mortem analysis
- **Anti-ambiguity:** No free-text failure reasons; all failures map to typed codes
- **Falsification:** Tests can assert exact reason codes, not substring matches

---

## 2. Code Format

All reason codes follow this pattern:
```
^[A-Z0-9_]{3,64}$
```

Examples: `R15_INVALID`, `RECEIPT_GAP_NONZERO`, `PURITY_VIOLATION`

---

## 3. Canonical Reason Codes

### 3.1 WUL-CORE Validation Failures

#### R15_INVALID
The token tree does not contain a valid R15 (RETURNS_TO) relation at the canonical placement (root-level `objective_return` field), or the R15 arity is incorrect.

**Policy:** Bridge validator MUST reject with this code before any symbolic execution.

---

#### FREE_TEXT_DETECTED
The token tree contains a free-text node, violating the WUL-CORE no-free-text invariant (I2).

**Policy:** Validation MUST fail before bridge ingress.

---

#### DEPTH_EXCEEDED
Token tree depth exceeds `max_depth` threshold (default: 64).

**Policy:** Reject at validation stage to prevent stack overflow in symbolic execution.

---

#### NODE_COUNT_EXCEEDED
Token tree node count exceeds `max_nodes` threshold (default: 512).

**Policy:** Reject at validation stage to prevent DoS via graph explosion.

---

#### ARITY_MISMATCH
A relation in the token tree has incorrect arity compared to kernel definition.

**Policy:** Validation MUST fail before symbolic execution.

**Example:** R15 requires arity 2, but tree provides 1 or 3 arguments.

---

#### KERNEL_HASH_MISMATCH
The `kernel_hash` in the bridge receipt does not match SHA256(Canon8785(kernel_registry.json)).

**Policy:** Reject at bridge ingress; kernel version is pinned per run.

---

#### CANON_IMPL_ID_INVALID
The `canon_impl_id` is not recognized or does not match declared canonicalization implementation.

**Policy:** Cross-runtime determinism requires explicit canon implementation identity (e.g., "rfc8785:v1").

---

### 3.2 Bridge Validation Failures

#### AGENT_INPUT_HASH_MISSING
Bridge receipt does not include `agent_input_hash`.

**Policy:** All bridge receipts MUST bind agent input to prevent injection ambiguity.

---

#### TOKEN_TREE_HASH_MISSING
Bridge receipt does not include `token_tree_hash`.

**Policy:** Receipt MUST cryptographically bind the validated token tree.

---

#### BRIDGE_VERSION_HASH_MISSING
Bridge receipt does not include `bridge_version_hash`.

**Policy:** Auditability requires versioned bridge logic.

---

#### VALIDATOR_VERSION_HASH_MISSING
Bridge receipt does not include `validator_version_hash`.

**Policy:** Validation logic version MUST be recorded in receipt.

---

### 3.3 Receipt System Failures

#### RECEIPT_GAP_NONZERO
The `receipt_gap` (count of unsatisfied HARD obligations) is greater than zero.

**Policy:** Mayor decision MUST be NO_SHIP if receipt_gap > 0, per RIH core theorem.

---

#### RECEIPT_FINGERPRINT_SET_MISMATCH
The set `receipt_root_payload.valid_receipt_fingerprints` is not equal to the canonical set derived from verified attestations using format: `attestation_commit:<payload_hash>`.

**Policy:** F2 verification output MUST produce identical fingerprint set as receipt root.

**Enforcement:** `tests/test_receipt_fingerprints.py`

---

#### ATTESTATION_INVALID
An attestation in the verification output has `attestation_valid: false`.

**Policy:** Only attestations with `attestation_valid: true` AND `policy_match: 1` contribute to receipt gap reduction.

---

#### POLICY_MATCH_FAILED
An attestation has `policy_match: 0`, indicating it does not satisfy the obligation's policy requirements.

**Policy:** Receipt gap can only decrease via attestations with both attestation_valid AND policy_match.

---

### 3.4 Mayor Decision Purity Failures

#### PURITY_VIOLATION
Mayor output decision is not equal to the recomputed decision from receipt-hashed inputs (tribunal bundle + policies + receipt_root_payload) under the declared Mayor decision function.

**Policy:** Mayor MUST be a pure function:
```
decision = SHIP  iff  kill_switches_pass == True  AND  receipt_gap == 0
```

**Enforcement:** `tests/test_mayor_purity.py`

**Implication:** Any "hidden Mayor logic" or discretionary override is detectable via purity test.

---

### 3.5 Kill Switch Failures

#### KILL_SWITCH_FAILED
One or more kill switches in the policies evaluation returned `False`, setting `kill_switches_pass: false`.

**Policy:** Even if receipt_gap == 0, Mayor MUST emit NO_SHIP if any kill switch fails.

**Examples:**
- Tier-A metric below threshold
- Determinism test failure (cross-runtime hash mismatch)
- Ablation stability test failure
- Security audit flag

---

### 3.6 Ablation Matrix Failures

#### ABLATION_STABILITY_FAILED
The ablation matrix stability test failed to meet acceptance criteria:
- A0 baseline median runtime < T_min (default: 100ms)
- Fewer than 2 ablations satisfy: med(ablation) <= 0.5 * med(A0)

**Policy:** POC Factory gate MUST block shipment if ablation does not demonstrate non-trivial stability advantage.

---

#### ABLATION_KILL_TEST_PASSED
An ablation kill test (A1-A6) did NOT fail as expected, indicating the invariant is not enforced.

**Policy:** Kill tests MUST fail within specified step limits to prove invariant enforcement.

**Example:** A1 (remove R15) completes without error, proving R15 is not actually required.

---

#### ABLATION_BASELINE_MISSING
Ablation matrix does not include A0 baseline configuration.

**Policy:** All ablation tests MUST be compared against pinned A0 baseline.

---

### 3.7 Cross-Runtime Determinism Failures

#### GOLDEN_HASH_MISMATCH
A hash (kernel_hash, run_spec_hash, trace_hash, artifact_root_hash, or receipt_root_hash) does not match the golden reference in `ci/golden_hashes_v0.json`.

**Policy:** Cross-runtime determinism requires ALL hashes to match across Python 3.10/3.11/3.12.

---

#### REPLAY_NONDETERMINISM
Two runs with identical pinned fields (claim_id, inputs_hash, config_hash, kernel_hash, canon_impl_id) produced different output hashes.

**Policy:** Replay-equivalence class MUST produce identical hashes.

---

### 3.8 Schema Validation Failures

#### SCHEMA_VALIDATION_FAILED
A JSON document failed validation against its declared JSON Schema.

**Policy:** All serialized payloads MUST validate against their schema before hashing or transmission.

---

#### REQUIRED_FIELD_MISSING
A required field in a JSON schema is missing from the document.

**Policy:** Schema-required fields are non-negotiable; missing fields cause immediate rejection.

---

### 3.9 Tribunal Obligation Failures

#### HARD_OBLIGATION_UNSATISFIED
A HARD obligation in the tribunal bundle has no valid attestation satisfying its policy.

**Policy:** Receipt gap increments by 1 for each unsatisfied HARD obligation; Mayor MUST emit NO_SHIP.

---

#### SOFT_OBLIGATION_UNSATISFIED
A SOFT obligation has no valid attestation, but this does NOT block shipment (does not increment receipt_gap).

**Policy:** SOFT obligations generate warnings but do not prevent SHIP decision.

---

### 3.10 Mayor Invariant Violations

#### NO_SHIP_WITHOUT_BLOCKING_CODES
Decision record has `decision: "NO_SHIP"` but the `blocking` array is empty.

**Policy:** NO_SHIP decision MUST include at least one typed reason code in blocking array to prevent silent failures.

**Enforcement:** `tests/test_mayor_no_ship_invariant.py`

---

#### SHIP_WITH_BLOCKING_CODES
Decision record has `decision: "SHIP"` but the `blocking` array is non-empty.

**Policy:** SHIP decision MUST have empty blocking array; presence of blocking codes contradicts SHIP verdict.

---

#### SHIP_WITH_NONZERO_RECEIPT_GAP
Decision record has `decision: "SHIP"` but `receipt_gap > 0`.

**Policy:** SHIP is only valid when receipt_gap == 0 per RIH core theorem.

---

#### SHIP_WITH_KILL_SWITCH_FAILURE
Decision record has `decision: "SHIP"` but `kill_switches_pass: false`.

**Policy:** SHIP requires ALL kill switches to pass; any single kill switch failure forces NO_SHIP.

---

## 4. Code Lifecycle

### 4.1 Adding New Codes

**Process:**
1. Identify failure mode requiring new code
2. Add entry to this document with description and policy
3. Update `decision_record.schema.json` if needed
4. Create test asserting the new code is emitted under failure condition
5. Version-tag the addition (e.g., "Added in v0.2")

### 4.2 Deprecating Codes

**Process:**
1. Mark code as `[DEPRECATED]` in this document
2. Document replacement code or migration path
3. Maintain backward compatibility for 2 minor versions
4. Remove from schema only after deprecation period

### 4.3 Immutability

**Rule:** Existing code semantics MUST NOT change. If failure semantics change, introduce new code.

**Example:** If `RECEIPT_GAP_NONZERO` needs to distinguish "missing attestation" from "invalid attestation", create two new codes rather than redefining the existing one.

---

## 5. Enforcement

### 5.1 CI Integration

All reason codes MUST be tested in CI:
- `tests/test_reason_codes_coverage.py` asserts all codes in this document are covered by at least one test
- `tests/test_decision_record_schema.py` validates decision records against schema
- `tests/test_mayor_no_ship_invariant.py` enforces NO_SHIP implies non-empty blocking array

### 5.2 Code Review Requirement

Any PR adding a new reason code MUST:
1. Update this document
2. Provide test demonstrating the code is emitted
3. Document which component emits the code
4. Explain why existing codes are insufficient

---

## 6. Current Code Count

**Total Canonical Codes:** 30

**By Category:**
- WUL-CORE Validation: 7
- Bridge Validation: 4
- Receipt System: 4
- Mayor Purity: 1
- Kill Switches: 1
- Ablation Matrix: 3
- Cross-Runtime Determinism: 2
- Schema Validation: 2
- Tribunal Obligations: 2
- Mayor Invariant Violations: 4

---

## 7. Version History

- **v0.1** (2026-01-16): Initial canonical list with 30 reason codes
  - Includes receipt fingerprint and mayor purity codes from hardening phase
  - Adds NO_SHIP invariant codes for blocking array enforcement

---

**END OF REASON_CODES.md**
