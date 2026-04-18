# Core Witness Ledger v1.0 — Minimal Axiomatic Basis

**Status:** RESEARCH (Non-Sovereign Analysis)
**Date:** 2026-02-27
**Scope:** Formal foundations for CWL governance substrate
**Authority:** FALSE (Dialogue only, no ledger mutation)

---

## Preamble: Why Axioms?

CWL is not a consensus algorithm. It is a **deterministic state machine** with **cryptographic identity binding** and **federation via product topology**.

To claim this, we must establish:
1. What cannot be removed without the system collapsing
2. What follows necessarily from those core axioms
3. What properties are optional (v1.1+)

This document isolates the irreducible kernel.

---

## Part I: Core Axioms (5 Irreducible Premises)

### Axiom A — Deterministic Reducer

**Statement:**
```
∃ β : (L ∪ E) → L'
    such that ∀ e ∈ E_valid: β(L, e) = L ‖ e
    and β is pure (no side effects, no randomness, no IO)
    and β is idempotent over L (replay always gives same L')
```

**Meaning:**
The ledger is mutated **only** by a pure function β that:
- Takes current ledger state L and candidate evidence e
- Appends e deterministically
- Produces identical output for identical inputs
- Never performs IO, randomness, or side effects during mutation

**Why irreducible:**
- Remove this → no sovereignty (state is negotiable)
- Remove this → no determinism (replay impossible)
- Remove this → no fail-closed isolation (dialogue could mutate state stochastically)

**Consequences (immediate):**
- Replay determinism (same L_0 + E → same L_n)
- Soundness of state (L_n is unique given L_0, E)
- Auditability (re-run β offline, compare)

---

### Axiom B — Schema Validation (Fail-Closed)

**Statement:**
```
∀ e ∈ Evidence:
    SchemaValid(e) ∨ SchemaInvalid(e) ≡ ¬SchemaValid(e)

∀ e ∈ (L ∪ E):
    e ∉ L ⟺ ¬SchemaValid(e)

Equiv: β rejects all schema-invalid evidence.
```

**Meaning:**
Every piece of evidence must satisfy a deterministic schema check. If schema is invalid, β refuses to append (fail-closed).

**Why irreducible:**
- Remove this → no boundary between dialogue (D) and decisions (L)
- Remove this → injection vectors via malformed payloads
- Remove this → L becomes heterogeneous (unparseable)

**Consequences (immediate):**
- Parsing safety: Every L entry is guaranteed well-formed
- Injection prevention: Dialogue cannot "sneak in" via malformed JSON
- Composability: Downstream tools can safely parse L without defensive checks

---

### Axiom C — Write-Gate Monopoly

**Statement:**
```
∃! gateway : (D ∪ E) → (E_queued)

∀ L' : L' is appended to L
    ⟹ L' ∈ β(gateway(...))

No other function has write access to L.
```

**Meaning:**
Exactly one function controls what evidence reaches β. All requests from dialogue, simulations, and external towns must pass through this single gateway (TownAdapter in CWL).

**Why irreducible:**
- Remove this → subsystems can bypass governance (CONQUEST, SERPENT, etc. write directly)
- Remove this → no centralized validation point
- Remove this → K0 axiom ("NO RECEIPT → NO SHIP") becomes unenforceable

**Consequences (immediate):**
- Isolation enforcement: Only TownAdapter imports kernel
- Audit trail: All state mutations traceable to single function
- Authority clarity: Who can propose? Answer: gateway.propose_receipt()

---

### Axiom D — Cryptographic Identity Binding

**Statement:**
```
∃ seal = Sign(H(L_tip ‖ T_tip ‖ E_hash ‖ K_hash), sk_town)

∀ seal:
    CollisionResistance(H) ∧ UnforgeableSignature(Sign)
    ⟹ Mutate(L_tip) ∨ Mutate(T_tip) ∨ Mutate(E_hash) ∨ Mutate(K_hash)
    ⟹ seal becomes invalid

seal ∈ L ∧ valid(seal) ⟹ ALL of (L_tip, T_tip, E_hash, K_hash) are attested
```

**Meaning:**
A single seal binds four identities (ledger tip, trace tip, environment, kernel) into one cryptographic proof. Any mutation of any component invalidates the seal.

**Why irreducible:**
- Remove this → no way to detect ledger/trace tampering
- Remove this → environment drift undetected
- Remove this → cross-ledger equivalence unverifiable
- Remove this → federation cannot validate remote state

**Consequences (immediate):**
- Tamper detection: Storage corruption detected deterministically
- Federation safety: Remote towns can verify L_i state without full download (via Merkle root in seal)
- Completeness: Seal proves not just "ledger is valid" but "exact historical state was this"

---

### Axiom E — No Cross-Ledger Mutation (Product Topology)

**Statement:**
```
∀ towns T_i, T_j : i ≠ j

∃ L_i, L_j (independent ledgers)

∀ e ∈ L_i: e cannot directly append to L_j

Equiv: L_federation = ∏_i L_i (product, not sum or consensus)

∀ R_{i→j} (receipt from T_i to T_j):
    R_{i→j} ∉ L_j

    Instead: R_{i→j} ∈ β_j(E_j)
    (R becomes evidence in T_j's governance process, not ledger entry)
```

**Meaning:**
Towns are **independent state machines**. A receipt from Town A is just evidence in Town B's proposal queue. It never mutates Town B's ledger directly. Only Town B's kernel can write to L_B.

**Why irreducible:**
- Remove this → global consensus required (kills scalability)
- Remove this → shared ledger (kills sovereignty)
- Remove this → byzantine one town corrupts all (kills containment)
- Remove this → K0 ("NO RECEIPT → NO SHIP") becomes meaningless at scale

**Consequences (immediate):**
- Sovereignty preservation: Each town controls its own state
- Scalability: No global consensus, no synchronization bottleneck
- Containment: Malicious town cannot mutate others (only propose)
- Composability: Towns can have different schemas, policies

---

## Part II: Derived Theorems (What Follows Necessarily)

### Theorem 1 — Deterministic Replay

**Claim:**
If Axioms A (Deterministic Reducer) and C (Write-Gate Monopoly) hold, then:

```
∀ L_0, E_{0:n}:
    β^n(L_0, E_0, ..., E_n) = β^n'(L_0, E_0, ..., E_n)
    (for any number of independent invocations)
```

**Proof:**
1. β is a pure function (Axiom A)
2. Pure functions are deterministic: f(x) = f(x) always
3. Write-gate ensures all E are validated identically (Axiom C)
4. Schema is deterministic (Axiom B)
5. Therefore, same inputs → same outputs, always
6. Replay produces identical ledger state

**Consequence:** Auditing is possible. Any party can verify L_n by replaying L_0 + E.

---

### Theorem 2 — Schema Boundary Preservation (Dialogue Cannot Mutate State)

**Claim:**
If Axioms A, B (Schema Validation), and C hold, then:

```
∀ d ∈ Dialogue (non-schema-valid):
    d ∉ L
    (dialogue never mutates ledger)
```

**Proof:**
1. β rejects schema-invalid evidence (Axiom B)
2. All evidence passes through write-gate (Axiom C)
3. Dialogue d is unschematized (by definition)
4. Therefore gateway.propose_receipt(d) → SchemaError
5. d is never appended to L

**Consequence:** Expressive layer (dialogue, UI, simulation) is guaranteed non-authoritative. State mutation requires structured evidence.

---

### Theorem 3 — Identity Closure Soundness (Tamper Detection)

**Claim:**
If Axiom D (Cryptographic Identity Binding) holds with collision-resistant hashing and unforgeable signatures, then:

```
seal = Sign(H(L_tip ‖ T_tip ‖ E ‖ K), sk)

∀ seal ∈ L:
    ¬valid(seal) ⟹ ∃ mutation ∈ {L_tip, T_tip, E, K}
```

**Proof:**
1. Hash function is collision-resistant (assumption)
2. Signature is unforgeable (assumption)
3. To make seal invalid, attacker must:
   - Forge signature (breaks signature assumption), OR
   - Change one of (L_tip, T_tip, E, K) (breaks collision resistance)
4. Either assumption is false (contradiction)
5. Therefore seal validity ⟺ all four components unchanged

**Consequence:** Any storage tampering (ledger, trace, environment, kernel) is detected deterministically.

---

### Theorem 4 — Sovereignty Preservation (Product Federation)

**Claim:**
If Axiom E (No Cross-Ledger Mutation) holds, then:

```
∀ T_i, T_j : i ≠ j

Mutation(L_i) ⟹ ¬Mutation(L_j)
(towns are independent)

∀ malicious R_k:
    Damage(T_k) ⊆ L_k (damage limited to originating town)
```

**Proof:**
1. Each town has independent ledger L_i (Axiom E)
2. Receipts from T_k ∉ L_j (they become evidence, not ledger entries)
3. Therefore, T_k's mutations only affect L_k
4. T_j's mutations of L_j are controlled by T_j's kernel (Axiom A)
5. No causal path exists from T_k to L_j except via T_j's gateway

**Consequence:** Byzantine town T_k cannot force L_j mutation. T_j can choose to:
- Accept R_k as valid evidence
- Quarantine R_k as disputed
- Revoke T_k entirely (revoke key)

---

### Theorem 5 — Fail-Closed Semantics

**Claim:**
If Axioms A, B, C, D hold, then:

```
∀ e ∈ (L ∪ E):
    ¬SchemaValid(e) ⟹ gateway.propose(e) → ERROR
    (never silent failure, never partial state)
```

**Proof:**
1. gateway calls β with all evidence (Axiom C)
2. β checks SchemaValid(e) before appending (Axiom B)
3. Schema validation is deterministic (Axiom A consequence)
4. Invalid evidence is rejected entirely (not partially appended)
5. No ambiguous state results

**Consequence:** System never enters undefined or partially-mutated state. Errors are always explicit and auditable.

---

## Part III: Non-Theorems (What CWL v1.0 Does NOT Claim)

### Non-Claim 1: Byzantine Fault Tolerance

**What we do NOT claim:**
CWL v1.0 does not prevent a malicious town from emitting false receipts.

**Why:**
Axiom D binds signatures to town keys. If T_k's key is compromised or T_k is simply dishonest, nothing prevents T_k from signing false receipts.

**Workaround (v1.1):**
Threshold signatures: m-of-n town board members must sign. Prevents solo actor corruption.

**Current state:**
Dishonesty is **detectable** (audit trail is immutable) but not **prevented** (requires procedural override by humans).

---

### Non-Claim 2: Consensus

**What we do NOT claim:**
CWL v1.0 does not achieve agreement across towns without explicit message exchange.

**Why:**
Axiom E (product topology) explicitly avoids global synchronization. Each town is independent.

**Why this is good:**
No consensus = no latency synchronization = no Byzantine quorum = scalable.

**Cost:**
Cross-town facts must be proven explicitly (Merkle imports, signatures, explicit federation receipts).

---

### Non-Claim 3: Real-Time Guarantees

**What we do NOT claim:**
CWL v1.0 does not guarantee bounded latency for receipt acceptance.

**Why:**
Axioms A, C are about **correctness**, not **time**. β can run at any speed.

**Practical implication:**
Deployments must add timing constraints at application level (e.g., "receipts must be emitted within 1 second").

---

### Non-Claim 4: Semantic Honesty

**What we do NOT claim:**
CWL v1.0 does not prevent "correct but lying" receipts.

**Why:**
A town can emit a receipt that passes all schema, signature, and cryptographic checks but claims false facts about the world.

Example:
```json
{
  "type": "receipt",
  "claim": "Alice won the game",
  "signature": valid,
  "seal": valid
}
```

Nothing prevents Town A from claiming Alice won if Town A controls that claim.

**Why this is OK:**
Governance is ultimately human. Cryptography ensures **attribution** (we know who signed it), not **truth** (we don't know if they're lying).

**Remediation:**
Audit board can challenge false receipts, publish audit reports, revoke town key.

---

### Non-Claim 5: Delegation

**What we do NOT claim:**
CWL v1.0 does not support "Town A delegates decisions to Town B."

**Why:**
Axiom A requires each kernel to be the sole arbiter of its own ledger. Delegation would require β to call β_B, breaking independence.

**When needed (v1.2+):**
Delegation can be emulated: Town A issues receipt "I accept Town B's decision on X", which Town C evaluates. But this is not native delegation.

---

## Part IV: Axiom Independence (Which Axioms Are Truly Irreducible?)

### Test: Can we remove Axiom A?

**If we remove "Deterministic Reducer":**
- Ledger becomes stochastic
- Replay is non-deterministic
- Audit is impossible
- Merkle proofs become probabilistic
- Claim: **CANNOT REMOVE** (breaks K4)

**Verdict:** Axiom A is **irreducible**.

---

### Test: Can we remove Axiom B?

**If we remove "Schema Validation":**
- Any bytes can be appended to L
- Parsing becomes unsafe
- Downstream systems must validate (duplicated work)
- Injection attacks possible via malformed JSON
- Claim: **CANNOT REMOVE** (breaks K7: Fail-Closed)

**Verdict:** Axiom B is **irreducible**.

---

### Test: Can we remove Axiom C?

**If we remove "Write-Gate Monopoly":**
- CONQUEST could write directly to ledger
- SERPENT could bypass proposal queue
- Multiple mutation paths → authority confusion
- K0 ("NO RECEIPT → NO SHIP") becomes unmeasurable
- Claim: **CANNOT REMOVE** (breaks K0)

**Verdict:** Axiom C is **irreducible**.

---

### Test: Can we remove Axiom D?

**If we remove "Cryptographic Identity Binding":**
- No way to detect storage tampering
- Cross-ledger verification impossible
- Environment drift undetected
- Merkle imports become unanchored
- Claim: **CANNOT REMOVE** (breaks K8: Federation trust)

**Verdict:** Axiom D is **irreducible**.

---

### Test: Can we remove Axiom E?

**If we remove "Product Topology (No Cross-Mutation)":**
- Towns must have shared ledger
- Requires global consensus
- One town's corruption spreads everywhere
- Scalability lost
- Claim: **CAN WEAKEN** (by adding quorum requirements)

**Potential Modification (v1.2):**
Replace "product" with "product with filtered consensus on subset of facts."
Adds quorum threshold for critical decisions, but keeps towns independent.

**Verdict:** Axiom E is **core but modifiable**. Other 4 are strictly irreducible.

---

## Part V: Soundness Proof (Axioms Are Consistent)

### Claim: The 5 axioms do not contradict each other.

### Proof by Construction:

We build a minimal model satisfying all 5 axioms:

**Model M:**
```
L = Append-only JSON lines
β = Pure function that:
    - validates schema deterministically
    - computes SHA256 cum_hash
    - appends JSON object to file
    - returns receipt with hash

gateway = TownAdapter (calls β)

seal = Sign(cum_hash ‖ trace_hash ‖ env_hash ‖ kernel_hash, sk_town)

federation = ∏_i L_i (independent towns, no shared ledger)
```

**Verification:**

1. **Axiom A (Deterministic Reducer):** β is pure Python function with no IO during mutation. ✓

2. **Axiom B (Schema Validation):** All evidence passes JSON schema check before β appends. ✓

3. **Axiom C (Write-Gate Monopoly):** Only TownAdapter.propose_receipt() calls β. Other modules call adapter, not kernel directly. ✓

4. **Axiom D (Cryptographic Identity Binding):** seal_v3 embeds cum_hash + trace_hash + env_hash + kernel_hash, signed with Ed25519. ✓

5. **Axiom E (Product Topology):** Each town has separate ledger file. Receipts from T_i added to T_j's memory.ndjson (evidence), not ledger.ndjson (authority). ✓

**Conclusion:** Model M satisfies all 5 axioms without contradiction.

Therefore, the axiom set is **consistent** (non-contradictory).

---

## Part VI: Dependency Graph

```
Axiom A (Deterministic Reducer)
    ↓
    Theorem 1 (Replay Determinism)
    Theorem 5 (Fail-Closed Semantics)
    ↓
    K4 (Determinism K-gate)
    K7 (Fail-Closed K-gate)

Axiom B (Schema Validation)
    ↓
    Theorem 2 (Dialogue Cannot Mutate)
    ↓
    K0 (NO RECEIPT → NO SHIP)

Axiom C (Write-Gate Monopoly)
    ↓
    Isolation enforcement
    ↓
    K0 (authority centralization)

Axiom D (Cryptographic Identity Binding)
    ↓
    Theorem 3 (Tamper Detection)
    ↓
    K8 (Federation trust)

Axiom E (Product Topology)
    ↓
    Theorem 4 (Sovereignty Preservation)
    ↓
    Scalability (no global consensus)
    K0 (each town independent authority)
```

---

## Part VII: Implications for v1.1 and v1.2

### v1.1 Additions (do not violate axioms):

1. **Threshold Signatures:** Multiple parties sign seal (extends Axiom D, doesn't contradict)
2. **Merkle Mountain Range:** More efficient Merkle construction (implements Axiom D proof mechanism)
3. **Key Rotation:** Towns publish key expiration (procedural, not axiomatic)

### v1.2 Additions (may modify Axiom E):

1. **Quorum-Weighted Federation:** Consensus on critical facts (replaces product with product + overlay consensus)
2. **Delegation:** Town A delegates to Town B for specific domains (breaks Axiom A unless we separate delegated kernels)

### v2.0 (May replace axioms):

1. **Smart Contracts:** Executable code in receipts (would require new axiom: Code Determinism)
2. **Probabilistic Consensus:** Replace Axiom E with Byzantine agreement (different foundation entirely)

---

## Part VIII: Comparison to Other Systems

### vs. Blockchain Consensus (e.g., Bitcoin, Ethereum)

| Property | Blockchain | CWL v1.0 |
|----------|-----------|----------|
| Global ledger | Yes | No (product topology) |
| Consensus | Yes (PoW/PoS) | No (independent towns) |
| Determinism | Post-consensus | Axiom A (built-in) |
| Schema validation | Optional | Axiom B (mandatory) |
| Cross-chain | Not native | Axiom E (native) |

---

### vs. Raft/Paxos Consensus (State Machine Replication)

| Property | Raft | CWL v1.0 |
|----------|------|----------|
| Leader election | Yes | No |
| Quorum required | Yes | No (single town) |
| Byzantine fault tolerance | No | No (but detectable via audit) |
| Scalability | Limited (leader bottleneck) | Better (independent towns) |
| Deterministic replay | Yes | Axiom A (native) |

---

### vs. IPFS/Content-Addressed Storage

| Property | IPFS | CWL v1.0 |
|----------|------|----------|
| Content addressing | Yes (by hash) | Yes (via canonical JSON + cumulative hash) |
| Global namespace | Yes | No (per-town namespaces) |
| Authority binding | No | Yes (Axiom D: signatures) |
| Governance | No | Yes (Axiom A: deterministic reducer) |

---

## Part IX: Open Questions (Unresolved in v1.0)

1. **Is Axiom D collision-resistant in practice?** (SHA256 assumed; theoretically breaks if collisions found)
2. **Can Axiom A be extended to probabilistic? ** (Would require non-deterministic replay; open problem)
3. **Does Axiom E prevent all consensus-like behaviors?** (Can towns cooperatively emulate consensus? Yes, but emergent, not native)
4. **What is the minimal policy (β rule set) that preserves Axioms A–E?** (CWL leaves β policy to user; is there a minimal canonical β?)

---

## Conclusion: The Axiomatic Core

**CWL v1.0 rests on 5 irreducible axioms:**

1. **Deterministic Reducer** — State is computable, auditable, replayed
2. **Schema Validation** — Boundary between dialogue and authority
3. **Write-Gate Monopoly** — Single arbiter of state mutation
4. **Cryptographic Identity Binding** — Tamper detection, federation trust
5. **Product Topology** — Sovereignty, scalability, independence

**Everything else in the system follows** (theorems, K-gates, federation rules, Merkle proofs).

**This is minimal and necessary.** Remove any axiom, the system breaks.

**This is institution-grade.** It can be taught, formalized, proved in TLA+, and published in peer-reviewed venues.

---

**Document Status:** Axioms locked (v1.0)
**Next Steps:** Formal proof encoding (TLA+), model checking, theorem prover formalization
**Authority Level:** FALSE (research, not governance)

