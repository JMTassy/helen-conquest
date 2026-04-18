# CWL v1.0.1 — Architecture Specification

**Version:** 1.0.1
**Status:** FROZEN
**Seal Binding:** REQUIRED
**Authority Model:** Binary
**Date:** 2026-02-27

---

## 1. Core Invariant

> NO RECEIPT → NO SHIP

Sovereign state mutation occurs **iff**:

1. Typed attestation Ê exists
2. Deterministic reducer β(L, Ê) == 1
3. MAYOR signs receipt
4. Receipt appended to ledger

**No heuristic. No soft gate. No discretion.**

---

## 2. Layer Model (L0 → L3)

### L0 — Agents (Non-Sovereign)

- **HELEN:** Dialogue generation
- **AIRI:** Avatar UI
- **Superteam Agents:** Task-specific workers

**Capabilities:**
- Produce candidate attestation Ê
- Emit non-sovereign telemetry
- Reflect over memory

**Prohibitions:**
- Cannot write ledger
- Cannot emit authority tokens (SHIP, SEALED, VERDICT, etc.)
- Cannot call kernel reducer directly

---

### L1 — Superteams (Deterministic Orchestration)

- Deterministic DAG pipelines
- Produce structured attestations
- Non-sovereign execution

**Output:** Ê + artifacts + trace events

---

### L2 — Street (Emergent Analytics)

- Pattern stabilization
- Heuristic synthesis
- Advisory only

**Cannot influence β or ledger directly.**

---

### L3 — Town / Governance Kernel (Sovereign)

- **GovernanceVM:** Deterministic reducer
- **MAYOR:** Signing authority
- **Ledger:** Append-only sovereign state

**Only component that mutates Channel A.**

---

## 3. Three Channels (Immutable Boundaries)

### Channel A — Sovereign Ledger

**File:** `ledger.ndjson`
**Domain Prefix:** `HELEN_CUM_V1`
**Properties:** Append-only, hash-chained, replayable

**Hash Formula:**
```
cum_hash_i = SHA256(
  PREFIX_LEDGER || prev_cum_hash || payload_hash_i
)
```

Where:
- `PREFIX_LEDGER = b"HELEN_CUM_V1"`
- `prev_cum_hash` = 32 bytes (prior cumulative hash)
- `payload_hash_i` = 32 bytes SHA256(canon(event_i))
- Raw byte concatenation (no JSON, no delimiters)

**Contains:**
- Receipts (receipt_v1)
- Seals (seal_v2)
- No prose, no narrative, no metadata

---

### Channel B — MemoryKernel (Non-Sovereign Structured Facts)

**File:** `memory.ndjson`
**Properties:** Append-only, conflict-aware, authority-banned

**Status Discipline:**
- `OBSERVED` — Witnessed but unconfirmed
- `CONFIRMED` — Validated by β
- `DISPUTED` — Contradicts another fact
- `RETRACTED` — Explicitly revoked

**Hard Ban:** Authority lexicon forbidden (no SHIP, SEALED, VERDICT)

**Critical Rule:** β does not read Channel B directly. Facts must be extracted → reified as Ê → validated → only then influence L.

---

### Channel C — RunTrace (Non-Sovereign Telemetry)

**File:** `run_trace.ndjson`
**Domain Prefix:** `HELEN_TRACE_V1`
**Properties:** Append-only, deterministic canonicalization, hash-chained in own domain

**Hash Formula (same pattern as Channel A):**
```
trace_hash_i = SHA256(
  PREFIX_TRACE || prev_trace_hash || payload_hash_i
)
```

Where:
- `PREFIX_TRACE = b"HELEN_TRACE_V1"`

**Authority:** Enforced at schema level: `authority = false` (const)

**Binding:** final_trace_hash is component of seal_v2 (see § 6)

---

## 4. MAYOR Decision Predicate (R-002)

```python
def MAYOR_DECISION(attestation: Ê, ledger_state: L) -> str:
    decision = beta(ledger_state, attestation)

    if decision == 1:
        return "SHIP"
    else:
        return "ABORT"
```

**Critical Properties:**

1. **MAYOR does not invent decisions.** β output is mechanically followed.
2. **MAYOR signs only β output.** No modification of payload.
3. **Signature is certification, not mutation.** Receipt structure cannot be altered after signing.

---

## 5. Attestation → Receipt Transformation (R-003)

### Input (Non-Sovereign)

```json
{
  "type": "attestation_v1",
  "rid": "unique-id",
  "actor": "L0_or_L1_id",
  "payload": { ... structured data ... },
  "payload_hash": "sha256(canon(payload))",
  "timestamp": 123456789,
  "authority": false
}
```

### Transform Law

β does not mutate Ê. Instead:

```python
β(L, Ê) ∈ {0, 1}

If β(L, Ê) == 1:
    receipt = {
        "type": "receipt_v1",
        "rid": Ê.rid,
        "payload_hash": Ê.payload_hash,
        "issuer": "MAYOR",
        "sig": Sign(MAYOR_SK, canon(receipt_without_sig)),
        "authority": true
    }
    Append receipt to Channel A

Else:
    Receipt is not produced
```

### Key Insight

- Attestation is untrusted proposal (authority=false)
- Receipt is cryptographic commitment (authority=true)
- Only receipt can mutate ledger
- Ledger stores commitment hash, not narrative

---

## 6. Identity Closure: seal_v2 Binding

### Definition

```json
{
  "seal_v2": {
    "final_cum_hash": "<32-byte ledger tip hash>",
    "final_trace_hash": "<32-byte trace tip hash>",
    "env_hash": "<32-byte environment identity>",
    "kernel_hash": "<32-byte kernel code identity>",
    "timestamp": "iso8601",
    "sig": "Ed25519(seal_SK, canon(seal_structure))"
  }
}
```

### Binding Property

Once seal_v2 exists, system identity becomes composite:

```
system_identity = H(final_cum_hash || final_trace_hash || env_hash || kernel_hash)
```

### Boot Requirement

1. Load ledger, trace, environment, kernel
2. Compute hashes
3. Compare to seal_v2
4. If ANY mismatch → FAIL CLOSED
5. No silent drift permitted

### Implication

- Ledger tampering breaks seal
- Trace tampering breaks seal
- Environment drift breaks seal
- Kernel modification breaks seal
- No component can be silently modified

---

## 7. Forbidden Morphisms (Constitutional Firewall)

### Allowed Path (Only)

```
D → Ê → β → receipt → L
```

Dialogue produces attestation.
Attestation is validated.
Receipt is issued.
Ledger is mutated.

### Forbidden Paths (Never)

```
D → L           (dialogue cannot directly write ledger)
B → L           (memory cannot directly write ledger)
C → L           (trace cannot directly write ledger)
L1 → L          (superteams cannot directly write ledger)
L2 → L          (street cannot directly write ledger)
```

### Enforcement

1. **Import Analysis:** Non-sovereign modules do not import ledger writer
2. **Type System:** Receipt type only constructible in GovernanceVM
3. **Schema Validation:** Authority tokens banned in B and C
4. **Cryptographic Binding:** Receipt requires MAYOR signature

---

## 8. Anti-Replay Gate

### Principle

Reusing the same `rid` (receipt ID) is forbidden.

### Implementation

```python
def admit(attestation: Ê) -> bool:
    if attestation.rid in {receipt.rid for receipt in ledger}:
        return False  # Duplicate rid detected
    return True
```

### Derivation

Anti-replay set derived from ledger itself (no separate index):
```
seen_rids = {receipt.rid | receipt ∈ ledger}
```

### Consequence

- Replay must recreate ledger state to forge new rid
- Impossible under sealed boot requirement
- Attacker cannot inject old receipt without appending to ledger

---

## 9. Federation (Compositional Sovereignty)

### Principle

No global super-kernel. Each town T_i is sovereign.

### Cross-Town Receipt

Town T_i produces receipt R^{i→j} intended for admission in T_j.

```json
{
  "type": "cross_receipt_v1",
  "from_town": "T_i",
  "to_town": "T_j",
  "payload": {...},
  "issuer": "MAYOR_i",
  "sig": "Sign(MAYOR_SK_i, ...)",
  "issuer_seal": "<seal_v2 of T_i>"
}
```

### Admissibility in T_j (Binary AND Gate)

```python
def admit_cross_receipt(R) -> bool:
    return (
        is_schema_valid(R)
        and verify_signature(R, public_key_of(R.issuer))
        and verify_seal(R.issuer_seal)
        and is_allowlisted(R.from_town, R.type)
        and is_anti_replay(R.rid)
    )
```

**All gates must pass. Single failure → reject.**

### Federation Closure

```
Closed_federation = ∧_i Closed_town_i
```

No federation-level mutation. Composition is logical, not empirical.

---

## 10. Summary: Invariant Checklist

- [ ] Single write-gate: Only GovernanceVM appends Channel A
- [ ] Deterministic β: Identical input → identical output
- [ ] MAYOR executor: Signs β output only
- [ ] Forbidden morphisms: No direct non-sovereign→sovereign path
- [ ] Hash chaining: cum_hash and trace_hash cryptographically bound
- [ ] Seal closure: boot requires identity match
- [ ] Authority isolation: authority=false enforced in B, C
- [ ] Anti-replay: rid uniqueness derived from ledger
- [ ] Federation: Binary admissibility, no super-kernel

---

## 11. Amendment Process (No Silent Evolution)

**To change architecture in CWL v1.0.1:**

1. **Minor patch (no invariant change):** v1.0.2 only with changelog
2. **Schema change (affects attestation or receipt):** v1.1 minimum
3. **Core invariant change (NO RECEIPT → NO SHIP):** v2.0 minimum

**All versions are frozen once released.**

---

**Frozen under CWL v1.0.1
Approved for sovereign deployment
No further changes without version increment**

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
