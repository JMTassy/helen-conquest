# Core Witness Ledger v1.0 — Formal Architecture Specification

**Status:** FROZEN / BASELINE
**Date:** 2026-02-27
**Author:** Collective Governance Design
**Canonical Location:** `/helen_os_scaffold/CWL_V1_0_FORMAL_SPEC.md`

---

## Executive Summary

Core Witness Ledger (CWL) is a deterministic, cryptographically-bound governance substrate for autonomous agent collectives.

**Single Axiom:** `NO RECEIPT → NO SHIP`

Only cryptographically verified receipts authorize state mutations. Everything else proposes.

**Scope:**
* Single-town deterministic kernel ✅
* Multi-town federation (product topology) ✅
* Conflict-free channel separation ✅
* Ed25519 identity binding ✅
* Crash-safe append-only ledger ✅

**Non-scope (v1.1+):**
* Threshold signatures
* Byzantine fault tolerance
* Delegated authority
* Smart contract execution
* Real-time consensus

---

## Part I: Foundational Invariants (K0–K8)

These invariants are **normative** and constitute the TCB. All implementation must satisfy them.

### K0 — Axiom (Immutable)
```
Receipt ∈ Ledger ⟺ Mutation Authorized

∀ payload ∉ {Receipt} : payload cannot mutate sovereign state
```

**Implication:** Dialogue, simulation, memory, UI, federation candidates remain proposals until kernel receipts them.

**Test:** `test_kernel_isolation.py`

---

### K1 — Append-Only (Immutable)
```
Ledger = L₀ ∥ L₁ ∥ L₂ ∥ … ∥ Lₙ

∀ i,j : i < j ⟹ Lᵢ immutable
```

**Guarantee:** No in-place mutation. No deletion. Only append.

**Implementation:** `LedgerWriterV2` (file-lock atomic append, monotone sequence).

**Test:** `test_replay_determinism.py::test_ledger_replay_verification`

---

### K2 — Deterministic Canonicalization
```
canon(payload) = JSON(sort_keys=True, separators=(",", ":"), ensure_ascii=False)
hash(canon(payload)) = payload_hash (deterministic)
```

**Guarantee:** Same payload dict → same bytes → same hash, independent of key order or transport.

**Implementation:** `helen_os/kernel/canonical_json.py`

**Test:** `test_hash_spine.py::test_canonicalization_determinism`

---

### K3 — Domain-Separated Hash Chain
```
cum_hash₀ = 0x00...00 (64 zeros)
cum_hashₙ = SHA256("HELEN_CUM_V1::" ∥ cum_hashₙ₋₁ ∥ payload_hashₙ)

where ∥ = byte concatenation (not string concatenation)
```

**Guarantee:** Different domains cannot collide. Changing domain prefix changes all downstream cum_hashes.

**Domain Separator:** `HELEN_CUM_V1::` (locked in kernel.py, module-level constant)

**Implementation:** `helen_os/kernel/hash_scheme.py`

**Test:** `test_hash_spine.py::test_domain_separation_prevents_collision`

---

### K4 — Replay Determinism (Full Ledger)
```
Given: ledger.ndjson with n events
VM₁.replay(ledger) → tip_hash_A
VM₂.replay(ledger) → tip_hash_B

Guarantee: tip_hash_A = tip_hash_B (any machine, any time)
```

**Implication:** State recovery is deterministic. Ledger is the single source of truth.

**Implementation:** `GovernanceVM.verify_ledger()` (full replay verification).

**Test:** `test_replay_determinism.py::test_replay_invariance`

---

### K5 — No Self-Validation (Separation of Concern)
```
Cognition ⊥ Decision

Agent/HELEN → generates proposals (E)
Kernel → validates receipts (β)
Agent ≠ Kernel
```

**Guarantee:** No agent can seal its own output. No circular validation.

**Implication:** Proposals flow upward only via TownAdapter write-gate.

**Implementation:** `TownAdapter` (single import of `GovernanceVM`).

**Test:** `test_kernel_isolation.py`

---

### K6 — Hard-Ban Authority Tokens in Memory
```
memory.ndjson MUST NOT contain:
  {LEDGER, SEAL, VERDICT, SHIP, APPROVED, CERTIFICATE,
   GATE PASSED, IRREVERSIBLE, HAL_VERDICT, EPOCH OPENED, …}

Enforcement: check_memory_text_is_clean() raises ValueError ❌
```

**Guarantee:** Memory cannot be confused with sovereign decisions.

**Channel Separation:**
* `memory.ndjson` → facts/preferences/summaries (non-sovereign)
* `storage/run_trace.ndjson` → telemetry/style (non-sovereign, authority=false)
* `ledger.ndjson` → receipts/seals (sovereign)

**Implementation:** `helen_os/utils/memory_safety.py`

**Test:** `test_serpent_mode_v1.py::test_memory_hard_ban_detects_violations`

---

### K7 — Fail-Closed on Schema Violation
```
payload not validated by schema ⟹ reject (no default/permissive mode)

∀ event in ledger: JSON schema ✓ (v1.0 frozen)
```

**Guarantee:** No ambiguous events. No "optional" or "future-compat" fields in stored receipts.

**Schemas Locked (v1.0):**
* `schemas/receipt_v1.schema.json`
* `schemas/serpent_mode_v1.schema.json`
* `schemas/conquest_tick_v1.schema.json`
* `schemas/cross_receipt_v2.schema.json`

**Implementation:** JSON Schema validators (fail-closed in bootstrap).

**Test:** `test_serpent_mode_v1.py::test_memory_hard_ban_detects_violations`

---

### K8 — Ledger Chain Integrity (Replay Verification)
```
∀ receipt in ledger:
  payload_hash = SHA256(canon(payload)) ✓
  cum_hash = SHA256("HELEN_CUM_V1::" ∥ prev_cum ∥ payload_hash) ✓
  seq strictly monotone ✓

replay() recomputes all and matches stored → ledger intact
```

**Guarantee:** No tampering possible. Any change is detected.

**Implementation:** `GovernanceVM.verify_ledger()` (full chain replay).

**Test:** `test_replay_determinism.py::test_ledger_replay_verification`

---

## Part II: Trusted Computing Base (TCB)

**Size: 5 modules. Everything else is replaceable.**

### TCB Components (Locked)

| Component | Lines | Purpose | Test |
|-----------|-------|---------|------|
| `canonical_json.py` | 20 | Deterministic JSON encoding | K2 |
| `hash_scheme.py` | 25 | HELEN_CUM_V1:: domain separation | K3 |
| `governance_vm.py` | 150 | Append-only ledger, replay, verify | K1, K4, K8 |
| `memory_safety.py` | 45 | Hard-ban FORBIDDEN_TOKENS | K6 |
| `json schemas/*.schema.json` | 300 | Schema validation (frozen v1.0) | K7 |

**Total TCB: ~540 lines + schemas**

### Non-TCB (Replaceable)

* `helen_os/serpent/` (UI/style)
* `helen_os/conquest/` (simulation engine)
* `helen_os/integrations/airi_bridge.py` (avatar)
* `helen_os/extractors/` (memory extraction policy)
* CLI commands
* Visualization

**Principle:** If it doesn't control mutation authority, it can be modified without invalidating the kernel.

---

## Part III: Threat Model

### Threat 1: Direct Ledger Mutation (No Receipt)
**Attack:** Agent writes to `ledger.ndjson` directly, bypassing kernel.
**Defense:** File permissions + audit on boot. TownAdapter is sole write-gate.
**Mitigation:** K0 (axiom), `test_kernel_isolation.py`

### Threat 2: Authority Token Leakage into Memory
**Attack:** Authority lexemes (SEAL, VERDICT, SHIP) appear in `memory.ndjson`, causing confusion about what's decided vs. proposed.
**Defense:** Hard-ban + sanitizer. `check_memory_text_is_clean()` on every write.
**Mitigation:** K6, `test_memory_hard_ban_detects_violations`

### Threat 3: Hash Collision (Domain)
**Attack:** Attacker finds two payloads with same cum_hash by exploiting weak domain separator.
**Defense:** Domain prefix `HELEN_CUM_V1::` is bytes-level, not string-level. Collision requires breaking SHA256.
**Mitigation:** K3, impossible under SHA256 (2^-256 probability)

### Threat 4: Ledger Tampering
**Attack:** Adversary modifies old events in ledger, recomputing hashes.
**Defense:** Final cum_hash is cryptographically bound. Any change invalidates entire chain.
**Mitigation:** K8, `verify_ledger()` detects any mutation

### Threat 5: Replay Attack (Cross-Receipt)
**Attack:** Attacker submits same cross-receipt twice, getting double-effect.
**Defense:** Receipt ID (rid_*) is unique. Anti-replay index blocks duplicates.
**Mitigation:** Federation contract, `cross_index` (v1.1+)

### Threat 6: Divergent Kernel State (Ghost Drift)
**Attack:** Two instances of kernel propose different cum_hashes for same payload.
**Defense:** SEAL_V2 pins environment hash. Boot fails if mismatch.
**Mitigation:** K4 (determinism), environment pinning (v1.0 readiness)

### Out-of-Scope (v1.1+)
* Byzantine faults (threshold signatures needed)
* Denial-of-service (rate limiting orthogonal)
* Side-channel attacks (timing, power)
* Quantum breaks SHA256 (post-quantum migration)

---

## Part IV: Governance Contract

### Channel Assignments (Normative)

| Channel | File | Authority | Writes | Reads | Conflict Policy |
|---------|------|-----------|--------|-------|-----------------|
| **Sovereign Ledger** | `ledger.ndjson` | YES | TownAdapter only | All (audit) | N/A (append-only) |
| **Memory** | `memory.ndjson` | NO | MemoryKernel + Extractors | HELEN, agents | Ask-Confirm (human-in-loop) |
| **Run Trace** | `run_trace.ndjson` | NO | TraceLogger | UI/dashboards | None (telemetry) |

**Invariant:** No cross-channel mutation. Writer per channel.

---

### Mutation Authority Flow

```
User Input
    ↓
HELEN / Agent (proposes, does NOT decide)
    ↓
Evidence (E) — structured proposals
    ↓
TownAdapter.propose_receipt(E)
    ↓
GovernanceVM.propose(payload)
    ↓
Receipt → Ledger (SHIP or NO_SHIP)
    ↓
[State mutation happens ONLY here]
```

**No shortcuts. No side channels.**

---

### Memory Conflict Policy

When MemoryKernel detects conflicting observations:

1. Flag as DISPUTED
2. Request human confirmation: "Which is true?"
3. User chooses
4. Append both versions with resolution timestamp
5. Future queries see both + resolution

**Guarantee:** No lossy compression. History is complete.

---

## Part V: Federation Contract

### Multi-Town Topology

```
Town_A (ledger_A, kernel_A, seal_A)
     ↓ (cross_receipt_v2, signed)
Town_B (ledger_B, kernel_B, seal_B)
     ↓ (acceptance decision)
Town_C, Town_D, …
```

**Closure:** No central authority. Each town seals independently.

### Cross-Receipt v2 (Cryptographic)

**Schema:** `schemas/cross_receipt_v2.schema.json`

```json
{
  "rid": "rid_unique_16hex",
  "issuer_town": "town_alpha",
  "issuer_vk": "public_key_64hex",
  "issuer_tip": "64hex (ledger tip)",
  "payload": { /* arbitrary */ },
  "signature": "128hex (Ed25519 signature of canon(payload) ∥ issuer_tip)"
}
```

**Signing Law:**
```
message = canon(payload) ∥ issuer_tip (bytes, not strings)
signature = Ed25519.sign(private_key, message)
```

**Verification:**
```
verified = Ed25519.verify(issuer_vk, signature, message)
if not verified: reject receipt
```

### Anti-Replay

**Index:** `ledger.cross_index`

```
{
  "rid_abc...": { "imported_seq": 42, "timestamp": "..." }
}
```

**Rule:** If rid exists in index, reject (second submit fails).

---

## Part VI: Replay Protocol (Fresh-Machine Validation)

### Scenario
Fresh machine. No prior state. Only `ledger.ndjson` file.

### Steps

1. **Boot Verify**
   ```
   a. Read last SEAL event (if exists)
   b. Compute current env_hash
   c. Compare to pinned env_hash
   d. If mismatch → FAIL_CLOSED (exit, no mutations)
   ```

2. **Replay Ledger**
   ```
   a. Initialize cum_hash = 0x00...00
   b. For each event in ledger:
      - Recompute payload_hash = SHA256(canon(payload))
      - Recompute cum_hash = SHA256("HELEN_CUM_V1::" ∥ prev ∥ payload_hash)
      - Assert cum_hash matches stored
   c. Final cum_hash = tip_hash
   ```

3. **State Reconstruction**
   ```
   a. For each event: apply reducer (deterministic)
   b. Result: identical to original
   ```

4. **Verification Report**
   ```
   ✅ Boot verified
   ✅ Ledger chain intact
   ✅ Tip hash: 0xabc...
   ✅ Ready for new proposals
   ```

---

## Part VII: Upgrade & Version Discipline

### Versioning Scheme

`CWL_v{MAJOR}.{MINOR}`

**v1.0** (current, frozen):
* Single kernel determinism
* Domain-separated cum_hash
* Memory hard-ban
* Basic federation (Ed25519)

**v1.1** (roadmap, not yet spec'd):
* Multi-signature mayors (quorum)
* Merkle import proofs
* Snapshot + compaction
* Federated closure audit engine

**v2.0** (future research):
* Threshold fault tolerance
* Delegated authority
* Consensus protocols
* Smart contract execution

### Migration Rule

No v1.0 ledger can automatically import v2.0 events.

Upgrades MUST:
1. Declare new schema version
2. Describe transformation (old → new)
3. Test on non-prod instance
4. Seal new kernel separately
5. Create migration audit report

**Implication:** Version lock is permanent. Backwards compatibility is optional.

---

## Part VIII: Compliance Checklist (v1.0 Release)

### Kernel
- [x] Canonical JSON deterministic
- [x] Hash chain with domain separation
- [x] Append-only with monotone seq
- [x] Crash-safe (fsync, lock)
- [x] Full ledger replay verification
- [x] SEAL_V2 env pinning

### Memory
- [x] Append-only observations
- [x] Hard-ban authority tokens
- [x] Conflict-aware (ask-confirm)
- [x] Status field (OBSERVED/CONFIRMED/DISPUTED/RETRACTED)
- [x] Sanitization on write

### Federation
- [x] Cross-receipt v2 (Ed25519)
- [x] Anti-replay index
- [x] No cross-ledger mutation
- [x] Independent seals per town

### Tests
- [x] K0 (axiom) — test_kernel_isolation.py
- [x] K1 (append-only) — test_replay_determinism.py
- [x] K2 (canon) — test_hash_spine.py
- [x] K3 (domain sep) — test_hash_spine.py
- [x] K4 (replay) — test_replay_determinism.py
- [x] K5 (no self-valid) — test_kernel_isolation.py
- [x] K6 (hard-ban) — test_serpent_mode_v1.py
- [x] K7 (fail-closed) — multiple schema tests
- [x] K8 (chain integrity) — test_replay_determinism.py

### Documentation
- [x] Formal spec (this document)
- [x] Threat model
- [x] TCB definition
- [x] Replay protocol
- [x] Upgrade discipline

---

## Part IX: How to Use This Spec

### For Implementers
1. Read Part I (Invariants). Satisfy K0–K8.
2. Implement TCB (Part II).
3. Test against threat model (Part III).
4. Validate replay protocol (Part VI).
5. Tag release as `CWL_v1.0`.

### For Auditors
1. Verify each K invariant in code.
2. Run tests: all must pass.
3. Replay ledger on fresh machine.
4. Validate schema conformance.
5. Sign off on TCB scope.

### For Users
1. Trust the kernel for decisions only.
2. Treat memory as revisable proposals.
3. Treat run_trace as informational only.
4. Requests for state mutations go through TownAdapter.
5. Never assume a change is real until it appears in ledger.

---

## Part X: Conclusion

Core Witness Ledger v1.0 is a **minimal, deterministic, cryptographically sound** governance substrate.

**It is NOT:**
* A consensus protocol
* A smart contract platform
* A general-purpose database
* A real-time system

**It IS:**
* A single source of truth for mutations
* Infinitely replayable
* Cryptographically bound
* Conflict-aware
* Ready for single-town and multi-town deployment

**Stability Guarantee:** This spec is frozen. No changes until v1.1 planning phase.

---

## Appendix: Invariant Index

| Invariant | Name | Type | Status | Test |
|-----------|------|------|--------|------|
| K0 | Axiom (Receipt→Mutation) | Normative | ✅ | test_kernel_isolation.py |
| K1 | Append-Only | Normative | ✅ | test_replay_determinism.py |
| K2 | Deterministic Canon | Normative | ✅ | test_hash_spine.py |
| K3 | Domain Separation | Normative | ✅ | test_hash_spine.py |
| K4 | Replay Determinism | Normative | ✅ | test_replay_determinism.py |
| K5 | No Self-Validation | Normative | ✅ | test_kernel_isolation.py |
| K6 | Hard-Ban Tokens | Normative | ✅ | test_serpent_mode_v1.py |
| K7 | Fail-Closed Schema | Normative | ✅ | multiple |
| K8 | Chain Integrity | Normative | ✅ | test_replay_determinism.py |

---

**End of Spec**

`git tag -a v1.0 -m "CWL v1.0 — Formal Spec Frozen"`

