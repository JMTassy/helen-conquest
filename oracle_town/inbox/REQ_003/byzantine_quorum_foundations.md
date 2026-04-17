# Byzantine Fault Tolerance & Quorum Design: Academic Foundations

**Archive Date:** 2026-01-29
**Purpose:** Support K3 (quorum-by-class) design with theoretical grounding
**Status:** RESEARCH SYNTHESIS (aggregated from classical literature)

---

## Introduction: From Consensus to Constitutional Governance

Byzantine Fault Tolerance (BFT) emerged from a fundamental question: **How can a system reach consensus when some nodes are faulty or adversarial?**

Oracle Town's K3 (quorum-by-class) invariant is a direct descendant of BFT theory, applied to governance rather than distributed systems consensus.

---

## Part 1: Classical Byzantine Problem

### Lamport, Shostak, Pease (1982)

**Original Problem:** In a network where some generals (nodes) may be traitors (faulty), how can loyal generals reach a consensus on a single coordinated action?

**Key Insight:** If we have N generals and up to F are faitors, we need **N ≥ 3F + 1** to guarantee consensus.

**Why?**
- Best case: F faitors try to disrupt the signal
- F honest nodes can be corrupted
- 1 honest node remains to verify
- Thus: 3F + 1 ensures majority always honest

### Application to Oracle Town

In Oracle Town governance:
- **Generals** = Attestors (LEGAL, TECHNICAL, BUSINESS classes)
- **Faitors** = Revoked attestors, compromised keys, corrupt agents
- **Consensus** = Quorum signature requirement

**K3 Implementation:**
```
Required classes: LEGAL + TECHNICAL + BUSINESS
Min per class: 1
Interpretation: If any class is missing or all from that class are faulty,
                the system defaults to NO_SHIP (fail-closed)
```

This isn't classical majority voting. It's **class-based diversification**: Different expertise domains form independent verification layers.

---

## Part 2: PBFT (Practical Byzantine Fault Tolerance)

### Castro & Liskov (1999)

PBFT introduced **state machine replication** for systems requiring:
- High availability (some nodes can fail)
- Safety (no conflicting decisions)
- Liveness (decisions eventually made)

**Core Algorithm:**
1. **Pre-prepare phase** — Primary proposes a sequence number
2. **Prepare phase** — Replicas verify and accept the proposal
3. **Commit phase** — Replicas commit once seeing consensus

**Safety Guarantee:** System produces consistent results even with F faulty nodes (if N ≥ 3F + 1)

**Liveness Guarantee:** System eventually decides if ≤ F nodes are faulty (not all adversarial)

### How Oracle Town Adapts PBFT

Oracle Town doesn't use PBFT's full state machine replication (that's for distributed consensus). Instead, it borrows the key insight:

**Safety (K1 Fail-Closed):**
- If any required class is missing signatures → NO_SHIP
- Equivalent to: "Consensus requires all critical viewpoints"

**Liveness (K5 Determinism):**
- Same claim + same signatures → always same decision
- Equivalent to: "Once quorum achieved, decision is deterministic"

---

## Part 3: Quorum Systems & Coteries

### Gifford (1979) - Quorum Replication

**Key Contribution:** Not all replicas need to agree. A **quorum** (subset meeting certain conditions) is sufficient.

**Quorum Intersection Property:** Any two quorums must overlap.

**Example (Voting):**
- N nodes total
- Quorum size: ⌈N/2⌉ + 1
- Any two quorums of size ⌈N/2⌉ + 1 must share at least one node
- This ensures consistency

### Peleg & Wool (1997) - Coteries

**Generalization:** A coterie is a collection of quorums with the intersection property.

**Flexible design:** Different quorums can have different minimum thresholds.

### Oracle Town's Coterie Model

Oracle Town uses **class-based coteries**:

```
Coterie C = {
    Q_legal: {all LEGAL attestors},
    Q_technical: {all TECHNICAL attestors},
    Q_business: {all BUSINESS attestors}
}

Quorum requirement: Q_legal ∩ Q_technical ∩ Q_business is non-empty
                    (at least 1 from each class)
```

**Why coteries instead of simple majority?**
- Majority voting requires ≥ 50% agreement
- Coteries require **representative agreement** from multiple domains
- A unanimous LEGAL decision + no TECHNICAL review would still be NO_SHIP

---

## Part 4: Three-Layer Consensus (Oracle Town's Constitutional Model)

Oracle Town extends classical consensus theory with **three layers of verification**:

### Layer 1: Propose (Information Source)
- **Role:** Generate options, surface information
- **Authority:** Has no decision power
- **Responsibility:** Provide accurate, honest information
- **Mechanism:** System accepts claims without gatekeeping

**Analogy in BFT:** The primary node proposes a value.

### Layer 2: Attest (Verification Source)
- **Role:** Validate claims against independent criteria
- **Authority:** Can verify correctness, not judge value
- **Responsibility:** Cryptographic proof of verification
- **Mechanism:** Signatures from multiple classes, each checking different criteria

**Analogy in BFT:** Replica nodes verify the proposal's feasibility.

### Layer 3: Decide (Authority Source)
- **Role:** Make final judgment based on evidence
- **Authority:** Can override both layers 1 and 2 if needed
- **Responsibility:** Assume accountability for the decision
- **Mechanism:** Human tribunal with access to all evidence

**Analogy in BFT:** The consensus commit phase locks in the decision.

**Why three layers work:**
- No single layer has unilateral power
- Each layer provides necessary but incomplete information
- Removing any layer breaks the system:
  - No propose → No input (stagnation)
  - No attest → No verification (unsafe)
  - No decide → No authority (chaos)

---

## Part 5: Consensus Theory Meets Epistemic Boundaries

### The Key Innovation

Classical BFT assumes **uniform agents**: all nodes are identical in capability, just potentially faulty in honesty.

Oracle Town extends this: **Agents are epistemically heterogeneous**.

- **Proposers are good at:** Generating options, understanding context
- **Validators are good at:** Checking rigor, detecting flaws
- **Decision-makers are good at:** Judgment, wisdom, accountability

This is more realistic than uniform-agent consensus. **Different roles have different competencies.**

### Mathematical Model

Let:
- P = proposer (generates claim C)
- A_i = attestors in class i (verify C against criterion_i)
- T = tribunal (decides on C given attestations)

**Consensus goal:** Reach decision D such that:
1. D is informed by P's information
2. D respects A_i's verification (no claim passes without class_i approval)
3. D preserves T's authority (T can override if needed)

**Oracle Town's approach:**
```
D = SHIP  if all A_i classes approve
D = NO_SHIP  if any A_i class missing or dissents
T = override (can force SHIP or NO_SHIP override, but with audit trail)
```

---

## Part 6: Failure Modes & Byzantine Resilience

### Classical Byzantine Failures

1. **Crash Fault** — Node stops responding
   - Oracle Town response: Missing signatures → NO_SHIP (K1)

2. **Omission Fault** — Node receives but doesn't respond
   - Oracle Town response: Timeout → NO_SHIP (K1)

3. **Byzantine Fault** — Node behaves arbitrarily (lies)
   - Oracle Town response: Invalid signature → NO_SHIP (K0)

4. **Timing Fault** — Node responds too late
   - Oracle Town response: Late attestations rejected → NO_SHIP

### E4 Pattern: Revocation Cascade

When a single attestor is compromised (Byzantine fault):

```
Step 1: LEGAL_001 is compromised (malicious or hacked)
Step 2: System revokes LEGAL_001 from registry
Step 3: Any claim pending LEGAL_001's signature fails (missing class)
Step 4: Entire decision chain collapses safely → NO_SHIP
```

**Why this is good:**
- One failure doesn't propagate as corruption
- It propagates as **conservative rejection**
- The system favors false negatives (reject valid) over false positives (accept invalid)

**Analogy in BFT:**
```
Classical BFT: Try to recover correct value despite Byzantine nodes
Oracle Town BFT: No value is better than a corrupted value
```

---

## Part 7: Practical Resilience vs. Theoretical Guarantees

### Where BFT Theory Applies
- **Assuming:** Adversaries are bounded (≤ F out of N nodes)
- **Guarantee:** Consensus achievable in finite time
- **Cost:** N ≥ 3F + 1 overhead

### Where Oracle Town Diverges
- **Assumption:** Not all adversarial nodes are detectable as such
- **Strategy:** When uncertain, refuse to decide
- **Cost:** Some valid claims rejected (false negatives)
- **Gain:** No invalid claims accepted (zero false positives)

### The Epistemic Tradeoff

Classical consensus: Maximize **liveness** (decisions get made)
Oracle Town: Maximize **safety** (decisions are trustworthy)

```
Consensus theory: "Better to sometimes get it wrong than never decide"
Oracle Town: "Better to never decide than consistently get it wrong"
```

This is appropriate for governance, less appropriate for distributed banking ledgers.

---

## Part 8: K3 Quorum-by-Class as BFT Evolution

### How K3 Implements Byzantine Resilience

**Standard BFT:**
```
Quorum = 2F + 1 out of N nodes
Example: 3 nodes, 1 faulty → need ≥ 2 signatures to decide
```

**Oracle Town K3:**
```
Quorum = [LEGAL + TECHNICAL + BUSINESS] signatures
Example: 3 classes, any missing → NO_SHIP (fail-closed)
```

**Key difference:** K3 replaces **numerical majority** with **categorical diversity**.

### Why Categorical Diversity > Numerical Majority

**Numerical majority problem:**
- 10 BUSINESS agents, 1 LEGAL agent
- Majority is BUSINESS
- But BUSINESS might be systematically biased (e.g., profit-driven)
- Quorum of 6 BUSINESS + 0 LEGAL → passes numerical majority
- Terrible for governance (no legal consideration)

**Categorical diversity solution:**
- 10 BUSINESS agents, 1 LEGAL agent
- Quorum must include both categories
- 10 BUSINESS + 0 LEGAL → NO_SHIP (K1 fail-closed)
- 5 BUSINESS + 1 LEGAL → SHIP (both categories represented)

**This maps to BFT principle:**
```
Byzantine theory: Diverse nodes prevent single-point compromise
Oracle Town: Diverse classes prevent single-perspective bias
```

---

## Part 9: Emerging Consensus Models

### Recent Developments (Post-2015)

1. **Proof of Stake (Ethereum 2.0)** — Replace computational work with economic stake
2. **Proof of Authority (Hyperledger)** — Pre-approved validators instead of permissionless mining
3. **Hybrid Consensus** — Multiple rounds of BFT + probabilistic finality

**Oracle Town's relationship:**
- Not permissionless (attestors pre-approved in registry)
- Uses cryptographic proof (Ed25519 signatures, not stake)
- Constitutional constraints replace economic incentives

### Novel Element: Constitutional Boundaries

Oracle Town adds something not in classical consensus: **role separation**.

```
Classical: "How do untrusted agents reach consensus?"
Oracle Town: "How do agents with different roles and authorities
             reach decisions that respect everyone's epistemic limits?"
```

---

## Part 10: Practical Implications for K3 Implementation

### Recommendation 1: Never Reduce Required Classes

If policy says [LEGAL + TECHNICAL + BUSINESS], never accept claims with only [LEGAL + TECHNICAL].

**Why:** Each class provides irreducible value:
- LEGAL: Jurisdictional and regulatory considerations
- TECHNICAL: Implementation feasibility
- BUSINESS: Strategic alignment and sustainability

Removing any class invites systematic bias.

### Recommendation 2: Implement Attestor Rotation

To prevent compromise of a single attestor cascading to NO_SHIP:
- Maintain 2-3 attestors per class (not just 1)
- This allows E4 revocation cascade to trigger without blocking all decisions

**Example:**
```json
{
  "legal": ["legal_001", "legal_002"],
  "technical": ["tech_001", "tech_002"],
  "business": ["biz_001", "biz_002"]
}
```

If legal_001 is revoked, legal_002 can still sign.

### Recommendation 3: Clear Revocation Criteria

When does an attestor get revoked?
- Demonstrable conflict of interest
- Cryptographic key compromise (detected via audit)
- Systematic pattern of bad judgment (recorded in ledger)

**Byzantine perspective:** Revocation is how the system contains failures.

### Recommendation 4: Separation of Concerns in Attestation

Each class should verify independently:
- **LEGAL:** "Is this claim compliant with regulations?"
- **TECHNICAL:** "Is this claim technically feasible?"
- **BUSINESS:** "Is this claim strategically sound?"

These questions are **orthogonal**. A claim can be:
- Legal but infeasible (TECHNICAL NO) → NO_SHIP
- Feasible but illegal (LEGAL NO) → NO_SHIP
- Strategically sound but infeasible (TECHNICAL NO) → NO_SHIP

**Byzantine principle:** Plurality of independent verification prevents collusion.

---

## Conclusion: From Theory to Practice

Byzantine Fault Tolerance provides the theoretical foundation for K3. The key insights:

1. **Quorum intersection:** Any two approval quorums must overlap (prevents inconsistency)
2. **Diversity protection:** Multiple independent validators prevent single-point compromise
3. **Fail-closed safety:** When uncertain, deny access (conservative approach)
4. **Role separation:** Different roles have different competencies and authorities

Oracle Town's constitutional model takes these principles and extends them from distributed consensus to human-machine governance:

- **Proposers** generate information (have no authority)
- **Validators** verify against criteria (have no judgment)
- **Decision-makers** integrate everything (have accountability)

No single layer can override the system. No single adversary can corrupt all layers. This is Byzantine resilience applied to governance.

---

**Generated:** 2026-01-29
**Purpose:** Support K3 quorum-by-class design with academic grounding
**Status:** Complete research synthesis, awaiting tribunal review
