# CWL Conformance Checklist v1 (Epoch3)

**Version:** CWL v1.0.1
**Status:** NORMATIVE — FROZEN
**Date:** 2026-02-27
**Reference Spec:** `CWL_CONFORMANCE_V1.md`
**Test Vectors:** `CWL_TEST_VECTORS_V1.json`

This checklist is a mechanical pass/fail for CWL v1.0.1 conformance certification.
Each check cites the normative section from `CWL_CONFORMANCE_V1.md`.

---

## Level A — Canonicalization + Ledger Hash Chain

### A1. Canonical JSON (§1)

- [ ] **A1.1** CANON_JSON_V1 implemented: `sort_keys=true`, separators `(",",":")`, `ensure_ascii=false`, UTF-8
- [ ] **A1.2** Implementation produces byte-identical canonical JSON to Python reference for all test fixtures
- [ ] **A1.3** No JSON floats in sovereign payloads (integers only)
- [ ] **A1.4** Unicode above U+007F encoded as raw UTF-8 (not `\uXXXX`)

**Pass condition:** canonical JSON of each ledger event payload in `CWL_TEST_VECTORS_V1.json.ledger_vector.events[]` matches `expected_payload_hashes[]` when SHA256 is applied.

---

### A2. Ledger Payload Hash (§4.1)

- [ ] **A2.1** `payload_hash = SHA256(CANON_JSON_V1(payload))`
- [ ] **A2.2** Only the `payload` field is hashed (not the envelope: `seq`, `cum_hash`, `meta`, etc.)
- [ ] **A2.3** Result is a 64-character lowercase hex string

**Pass condition:** computed payload hashes match `ledger_vector.expected_payload_hashes` in test vectors.

---

### A3. Ledger Cumulative Hash (§4.2)

- [ ] **A3.1** `cum_hash = SHA256(b"HELEN_CUM_V1" || prev_cum_hash_bytes || payload_hash_bytes)`
- [ ] **A3.2** Prefix is `b"HELEN_CUM_V1"` (12 bytes, ASCII, no null terminator)
- [ ] **A3.3** `prev_cum_hash` for genesis (`seq=0`) is `"0" * 64` (32 zero bytes)
- [ ] **A3.4** Raw byte concatenation — no length prefixes, no delimiters

**Pass condition:** computed cumulative hashes match `ledger_vector.expected_cum_hashes`.

---

### A4. Hash Law Field (§4.3)

- [ ] **A4.1** Every Channel A event carries `"hash_law": "CWL_CUM_V1"`
- [ ] **A4.2** Validator detects hash_law at first event and routes to correct verifier
- [ ] **A4.3** `"CWL_CUM_V0"` events are accepted without verification (legacy archive)
- [ ] **A4.4** Unknown hash_law values cause fail-closed rejection

**Level A PASS:** All A1–A4 checks pass.

---

## Level B — RunTrace (S1) + Seal v2 (S2)

### B1. RunTrace Determinism — Spec Lock S1 (§3)

- [ ] **B1.1** Trace hash core includes only: `authority`, `event_type`, `metadata`, `payload`, `run_id`, `schema_version`, `seq`, `tick`
- [ ] **B1.2** `seq` is monotone starting at 0, incremented by exactly 1 per appended event
- [ ] **B1.3** `tick` is provided by a deterministic orchestrator (NOT wall-clock time)
- [ ] **B1.4** `authority` is always `false` (boolean) for all trace events
- [ ] **B1.5** Implementation raises an error if `authority: true` is supplied by caller
- [ ] **B1.6** Wall-time does NOT appear in any committed bytes (may appear in `meta.timestamp` only)

**Pass condition:** computed trace payload hashes match `trace_vector.expected_payload_hashes` in test vectors.

---

### B2. Trace Cumulative Hash (§3.2)

- [ ] **B2.1** `trace_hash = SHA256(b"HELEN_TRACE_V1" || prev_trace_hash_bytes || payload_hash_bytes)`
- [ ] **B2.2** Prefix is `b"HELEN_TRACE_V1"` (14 bytes, ASCII)
- [ ] **B2.3** `prev_trace_hash` for first event is `"0" * 64` (32 zero bytes)

**Pass condition:** computed trace cum hashes match `trace_vector.expected_cum_hashes`.

---

### B3. Seal v2 Identity Closure — Spec Lock S2 (§5)

- [ ] **B3.1** `seal_v2` payload includes: `final_cum_hash`, `final_trace_hash`, `env_hash`, `kernel_hash`
- [ ] **B3.2** `seal.final_cum_hash` equals ledger tip (cum_hash of last non-seal event)
- [ ] **B3.3** `seal.final_trace_hash` equals trace tip (cum_hash of last trace event)
- [ ] **B3.4** Seal payload does NOT contain machine-local fields (file paths, hostnames, PIDs, UIDs)
- [ ] **B3.5** Seal terminus semantics: hash chain stops AT seal; seal references state BEFORE itself
- [ ] **B3.6** Boot verification fails closed on any mismatch (no partial acceptance)

**Pass condition:** `seal_v2_fixture` in test vectors validates correctly against computed ledger + trace tips.

**Level B PASS:** Level A passes + all B1–B3 checks pass.

---

## Level C — Ledger-derived Anti-replay — Spec Lock S3 (§6)

- [ ] **C1** `RID(L) = { e.rid | e ∈ L and e has field "rid" }` is computed from ledger replay alone
- [ ] **C2** Receipt admissibility check: `reject if rid ∈ RID(L_current)`, `admit if rid ∉ RID(L_current)`
- [ ] **C3** No mutable external state (database, index, cache) is required for correctness
- [ ] **C4** Derived in-memory cache (for performance) is reconstructible from ledger alone

**Pass condition:**
- `anti_replay_vector.admissible_test` → `RID-008` is admitted (not in ledger)
- `anti_replay_vector.inadmissible_test` → `RID-003` is rejected (present in ledger)

**Level C PASS:** Level B passes + all C1–C4 checks pass.

---

## Level D — Merkle Import Proof Semantics — Spec Lock S4 (§7)

### D1. Leaf and Node Hashing

- [ ] **D1.1** `leaf_s = SHA256(b"CWL_LEDGER_LEAF_V1" || payload_hash_s_bytes)`
- [ ] **D1.2** Prefix `b"CWL_LEDGER_LEAF_V1"` is 18 bytes (ASCII)
- [ ] **D1.3** `node = SHA256(b"CWL_MERKLE_NODE_V1" || left_bytes || right_bytes)`
- [ ] **D1.4** Prefix `b"CWL_MERKLE_NODE_V1"` is 18 bytes (ASCII)

**Pass condition:** computed leaf hashes match `merkle_vector.leaf_hashes` in test vectors.

---

### D2. Padding Rule

- [ ] **D2.1** Duplicate-last padding: if level has odd nodes, duplicate the last node before pairing
- [ ] **D2.2** Padding applies at every level up to the root
- [ ] **D2.3** Root of the 8-leaf tree matches `merkle_vector.root` in test vectors

**Pass condition:** computed Merkle root matches `merkle_vector.root`.

---

### D3. Inclusion Proof Verification

- [ ] **D3.1** Proof steps include sibling side (`"L"` or `"R"`)
- [ ] **D3.2** Verification: for each step, if `side="R"` → `node(current, sibling)`; if `side="L"` → `node(sibling, current)`
- [ ] **D3.3** All three inclusion proofs (index 0, 3, 7) verify to the frozen root

**Pass condition:** proofs in `merkle_vector.inclusion_proofs` all verify to `merkle_vector.root`.

---

### D4. Root Anchoring

- [ ] **D4.1** Any Merkle root used for cross-town import MUST be anchored in a valid `seal_v2` or equivalent
- [ ] **D4.2** Unanchored Merkle roots are treated as inadmissible

**Level D PASS:** Level C passes + all D1–D4 checks pass.

---

## S5 — kernel_hash + env_hash Precision

*These checks are independent of Level A–D but SHOULD be satisfied for production deployment.*

- [ ] **S5.1** `TCB_FILESET` is an explicit, versioned, enumerated list (no glob patterns)
- [ ] **S5.2** `kernel_hash = SHA256(deterministic_tarball_bytes(TCB_FILESET))` where tarball is sorted lexicographically by path
- [ ] **S5.3** `env_hash = SHA256(CANON_JSON_V1(env_descriptor))`
- [ ] **S5.4** `env_descriptor` includes: language/runtime version, lockfile digest, platform tag (if platform-sensitive)
- [ ] **S5.5** Identical TCB + identical environment → identical `kernel_hash` and `env_hash` on any compliant machine

**Pass condition:** cross-machine run with identical TCB + env produces identical `kernel_hash` and `env_hash`.

---

## Summary Table

| Check ID | Section | Level | Description | Status |
|----------|---------|-------|-------------|--------|
| A1.1–A1.4 | §1 | A | CANON_JSON_V1 implementation | ☐ |
| A2.1–A2.3 | §4.1 | A | Payload hash formula | ☐ |
| A3.1–A3.4 | §4.2 | A | Cumulative hash formula | ☐ |
| A4.1–A4.4 | §4.3 | A | Hash law versioning | ☐ |
| B1.1–B1.6 | §3 | B | RunTrace S1 determinism | ☐ |
| B2.1–B2.3 | §3.2 | B | Trace chain formula | ☐ |
| B3.1–B3.6 | §5 | B | Seal v2 identity closure S2 | ☐ |
| C1–C4 | §6 | C | Anti-replay S3 | ☐ |
| D1.1–D1.4 | §7.1–7.2 | D | Merkle leaf/node S4 | ☐ |
| D2.1–D2.3 | §7.3 | D | Padding rule | ☐ |
| D3.1–D3.3 | §7.4 | D | Inclusion proofs | ☐ |
| D4.1–D4.2 | §7.5 | D | Root anchoring | ☐ |
| S5.1–S5.5 | §9 | S5 | env_hash + kernel_hash precision | ☐ |

---

## Final Certification

A system is **CWL v1.0.1 conformant at Level X** if and only if:

1. All checks for Level X and all levels below it are marked PASS
2. All check results were produced against the frozen `CWL_TEST_VECTORS_V1.json`
3. No check was marked PASS without a corresponding automated test

**Signature fields (for implementation audit log):**

```
Implementation: _______________
Language/Runtime: _______________
Date Tested: _______________
Level Claimed: [ A ] [ B ] [ C ] [ D ]
S5 Satisfied: [ YES ] [ NO ]
Auditor: _______________
```

---

*Generated: 2026-02-27*
*Epoch: EPOCH3 Standard Artifacts*
*Normative reference: CWL_CONFORMANCE_V1.md*
*Test fixture: CWL_TEST_VECTORS_V1.json*
