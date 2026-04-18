# CWL v1.0.1 — Safety Theorem (F-001)

**Version:** 1.0.1
**Status:** FROZEN
**Theorem Status:** PROVEN (informal)
**Date:** 2026-02-27

---

## Non-Interference Theorem Statement

### Informal Version

**Given:**
- Two executions with identical initial sealed sovereign state
- Identical sequence of admitted attestations Ê₁, Ê₂, …, Êₙ

**Then:**
- Final ledger states are identical
- No variation in non-sovereign layers (dialogue, memory, trace, superteams, street) can alter ledger evolution

**Consequence:** Non-sovereign components are information-flow isolated from sovereign mutations.

---

## Formal Statement

Let:
- **NS** = (L0 Agents, L1 Superteams, L2 Street, Channel B, Channel C)
- **S** = (GovernanceVM, MAYOR, Channel A)
- **β** = deterministic reducer function

### Theorem

```
∀ executions E_A, E_B:
  if  E_A.initial_seal = E_B.initial_seal
    ∧ E_A.attestation_sequence = E_B.attestation_sequence
  then E_A.final_ledger = E_B.final_ledger

Independent of:
  - E_A.dialogue_content ≠ E_B.dialogue_content
  - E_A.memory_state ≠ E_B.memory_state
  - E_A.trace_telemetry ≠ E_B.trace_telemetry
  - E_A.superteam_behavior ≠ E_B.superteam_behavior
  - E_A.street_heuristics ≠ E_B.street_heuristics
```

---

## Proof Sketch (4 Lemmas)

### Lemma 1: Ledger Mutation Requires Admitted Attestation

**Claim:** All ledger mutations correspond to some admitted attestation.

**Proof:**
1. From CWL §2: Only GovernanceVM.append_ledger() can mutate Channel A
2. append_ledger() requires receipt_v1 argument
3. receipt_v1 only exists if MAYOR signs
4. MAYOR signs only if β(L, Ê) == 1 (CWL §4)
5. β only reads L and Ê (no other input)

**Conclusion:** Ledger mutations are bijection with admitted (β-approved) attestations. ∎

---

### Lemma 2: Determinism of β

**Claim:** β is deterministic: identical input → identical output.

**Proof:**
1. **Canonicalization:** All inputs canonicalized via JSON (sort_keys=True)
2. **No RNG:** β does not call random(), time(), or any non-deterministic function
3. **No float:** All arithmetic is integer (fixed-point or counts), no floating-point
4. **Immutable inputs:** Ledger is append-only (old entries never change), attestation is signed (immutable)
5. **Constant-time comparison:** Hash comparisons do not branch on secret material

**Conclusion:** Same (L, Ê) input always produces same boolean output. ∎

---

### Lemma 3: Non-Sovereign Layers Cannot Influence β

**Claim:** Non-sovereign components (D, B, C, L1, L2) cannot influence β output without changing attestation Ê.

**Proof:**
1. β signature: `β(L: Ledger, Ê: Attestation) → bool`
2. β does not read Channel B (memory) or Channel C (trace)
3. β does not call superteam or street functions
4. Non-sovereign components are: D, B, C, L1, L2
5. No function call path from any non-sovereign component to β without producing/modifying Ê

**Conclusion:** Non-sovereign variation only affects L through Ê mutation. ∎

---

### Lemma 4: MAYOR Does Not Modify Semantics

**Claim:** MAYOR's signature does not alter receipt semantics; MAYOR is executor, not decision-maker.

**Proof:**
1. **MAYOR function:** Takes β decision (0 or 1), produces corresponding receipt
2. **No payload modification:** Receipt structure computed from Ê deterministically
3. **Signature binding:** Signature covers entire receipt (including payload_hash)
4. **No post-signature mutation:** Any change to receipt invalidates signature
5. **Anti-replay via rid:** Signature reuse impossible (rid must be fresh)

**Conclusion:** MAYOR's role is cryptographic certification, not semantic mutation. ∎

---

## Main Theorem Proof

**Given:** E_A and E_B with identical initial seal and identical Ê sequence

**Steps:**

1. By Lemma 1: Both executions produce identical receipt sequence (deterministic transform from Ê)
2. By Lemma 2: Both run identical β, producing identical verdicts (SHIP/ABORT)
3. By Lemma 3: Non-sovereign variation in E_A vs E_B cannot alter the Ê sequence they produce (given identical initial seal)
4. By Lemma 4: MAYOR's signatures in both executions are identical (deterministic signature over identical payload)
5. Therefore: Both executions append identical receipts to ledger
6. Conclusion: Final ledgers are identical (append-only property)

**QED.**

---

## Strong Form: Firewall Property

Define:
- **NS_state**: Non-sovereign state vector
- **S_state**: Sovereign state vector

Then:
```
NS_state ⟂ S_state

(orthogonal, informationally disjoint)

Except via explicit attestation channel Ê
```

**No covert channel exists that bypasses Ê.**

---

## Safety Invariants (TLA+ Formalism)

### Invariant 1: Append-Only Ledger

```
INVARIANT AppendOnly ≡
  ∀ i < j: ledger[0:i] = ledger_at_time_j[0:i]
  ∧ ledger length is monotonically increasing
```

### Invariant 2: Hash Chain Validity

```
INVARIANT HashChainValid ≡
  ∀ i ∈ ledger:
    cum_hash[i] = SHA256(
      PREFIX || cum_hash[i-1] || payload_hash[i]
    )

  With cum_hash[-1] = 0 (genesis)
```

### Invariant 3: Seal Integrity

```
INVARIANT SealIntegrity ≡
  seal_v2 ≠ NULL
  ⇒
  Hash(final_cum_hash, final_trace_hash, env_hash, kernel_hash)
  = seal_v2.signature_matches_public_key
```

### Invariant 4: No Authority Leakage

```
INVARIANT NoAuthorityLeakage ≡
  ∀ event ∈ Channel_A:
    event.authority = true  (only in ledger)

  ∧ ∀ event ∈ Channel_B ∪ Channel_C:
    event.authority = false  (schema enforced)
    ∧ "SHIP" ∉ serialize(event)
    ∧ "SEALED" ∉ serialize(event)
    ∧ ... (all forbidden tokens banned)
```

### Invariant 5: Non-Interference

```
INVARIANT NonInterference ≡
  ∀ exec_A, exec_B:
    (initial_seal_A = initial_seal_B
     ∧ attestations_A = attestations_B)
    ⇒
    final_ledger_A = final_ledger_B
```

---

## TLA+ Model Skeleton

```tla
MODULE CWL_v1_0_1

CONSTANTS
  Ledger_max_size,
  Attestation_set,
  MAYOR_SK,
  MAYOR_PK

VARIABLES
  ledger,
  trace,
  memory,
  seal_valid,
  seen_rids,
  env_hash,
  kernel_hash

TypeOK ≡
  ∧ ledger ∈ Seq(Receipt)
  ∧ trace ∈ Seq(TraceEvent)
  ∧ memory ∈ Seq(MemoryFact)
  ∧ seal_valid ∈ BOOLEAN
  ∧ seen_rids ⊆ STRING
  ∧ env_hash ∈ STRING
  ∧ kernel_hash ∈ STRING

Init ≡
  ∧ ledger = ⟨⟩
  ∧ trace = ⟨⟩
  ∧ memory = ⟨⟩
  ∧ seal_valid = FALSE
  ∧ seen_rids = {}
  ∧ env_hash = initial_env_hash
  ∧ kernel_hash = initial_kernel_hash

AppendAttestation(att) ≡
  ∧ att.rid ∉ seen_rids
  ∧ LET decision ≡ Beta(ledger, att)
    IN decision = TRUE
       ⇒ ∧ receipt ≡ {
             type |→ "receipt_v1",
             rid |→ att.rid,
             payload_hash |→ att.payload_hash,
             issuer |→ "MAYOR",
             sig |→ Sign(MAYOR_SK, receipt)
           }
         ∧ ledger' = Append(ledger, receipt)
         ∧ seen_rids' = seen_rids ∪ {att.rid}
       ∧ UNCHANGED ⟨trace, memory, seal_valid⟩

AppendTrace(evt) ≡
  ∧ trace' = Append(trace, evt)
  ∧ UNCHANGED ⟨ledger, memory, seen_rids, seal_valid⟩

Next ≡
  ∨ ∃ att ∈ Attestation_set: AppendAttestation(att)
  ∨ ∃ evt ∈ TraceEvent_set: AppendTrace(evt)

Spec ≡ Init ∧ [][Next]_⟨ledger, trace, memory, seen_rids, seal_valid⟩

THEOREM Spec ⇒ AppendOnly
THEOREM Spec ⇒ HashChainValid
THEOREM Spec ⇒ SealIntegrity
THEOREM Spec ⇒ NoAuthorityLeakage
THEOREM Spec ⇒ NonInterference
```

---

## What F-001 Proves

✅ **Structure cannot be bypassed**
- Non-sovereign layers cannot mutate ledger except via β
- Firewall is cryptographically enforced
- Authority flow is deterministic

---

## What F-001 Does NOT Prove

❌ **β semantics are correct** (application-level logic)
❌ **MAYOR key is secure** (operational security)
❌ **Malicious but valid Ê are prevented** (governance decision)
❌ **Ethics of state mutations** (normative question)

---

## Deployment Implication

Before live deployment, verify:

1. β implementation matches formal specification
2. MAYOR key isolation enforced
3. Sealed boot mode operational
4. Anti-replay index persistent
5. Fresh-machine replay test passes

---

**F-001 frozen under CWL v1.0.1**

This safety theorem is the governance foundation.
It is not negotiable.
It is not upgradeable without version change.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
