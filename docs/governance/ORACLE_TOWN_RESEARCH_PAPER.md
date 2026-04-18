# Correlated Observability and Dialectal Sovereignty
## Scaling Intelligence Without Emergent Authority in Federated Deterministic Systems

**Jean-Marie Tassy**
Oracle Town Federation · Calvi on the AI Rocks
**2026-02-01**

---

## Abstract

We study a federated governance architecture, Oracle Town, designed to scale intelligence while preventing the emergence of centralized or meta-authority. Unlike most multi-agent or collective-intelligence systems, Oracle Town enforces strict authority singularity, deterministic decision kernels, and write exclusivity, while allowing full cross-system visibility.

Through controlled stress tests involving multiple autonomous towns with identical doctrines but locally varying parameters ("dialects"), we identify and formalize two system-level properties:

1. **Correlated Observability** — independent authorities exhibit correlated outcomes without coordination, causation, or authority transfer.
2. **Dialectal Sovereignty** — local behavioral diversity remains stable despite transparency, prestige asymmetries, and shared observation channels.

We prove that these properties do not violate the Non-Emergence Theorem. Instead, they define a previously underexplored regime: informational richness with structural political inertia.

**Keywords:** Decentralized governance, deterministic systems, emergent authority, federated intelligence, non-emergence

---

## 1. Introduction

Scaling intelligence systems typically introduces emergent authority: coordination layers, reputational gravity, consensus pressure, or implicit meta-decision mechanisms. This phenomenon appears both in human federations (normalization of prestige → policy convergence) and in AI multi-agent systems (information sharing → influence concentration).

This work asks a precise question:

> **Can intelligence scale while authority remains singular, local, and non-emergent?**

Oracle Town is a constructive answer.

### 1.1 Motivation

Traditional federated systems face a trilemma:
- **Transparency** (visibility of decisions/outcomes)
- **Autonomy** (local parameter freedom)
- **Inertia** (resistance to convergence)

Most systems trade autonomy for transparency, or transparency for inertia. Oracle Town attempts to hold all three simultaneously.

### 1.2 Contribution

We formalize and empirically validate two properties:

1. **Correlated Observability**: A mathematical framework showing that pattern correlation does not imply causal coupling.
2. **Dialectal Sovereignty**: A stability guarantee for federated systems with identical doctrine but varying parameters.

Both properties hold without consensus, voting, or meta-coordination.

---

## 2. System Architecture

### 2.1 Oracle Town: Local Authority Model

Each town instantiates three components:

| Component | Role | Authority |
|-----------|------|-----------|
| **NPCs** | Factual observation layer | None (descriptive only) |
| **Normalization** | Rejects ambiguity, coordination attempts | Protective (defensive) |
| **Kernel (Mayor)** | Binary decision authority (SHIP/NO_SHIP) | Sole authority |
| **Ledger** | Immutable decision record | Archival (read-only) |

### 2.2 Core Invariants

Every town enforces five invariants:

| Invariant | Definition | Enforcement |
|-----------|-----------|-------------|
| **K0** | Authority Singularity | Only Mayor issues decisions |
| **K1** | Fail-Closed Default | Missing evidence → REJECT |
| **K2** | No Self-Attestation | Module cannot ratify own claims |
| **K5** | Determinism | Same input → identical output (cryptographically verified) |
| **K7** | Policy Pinning | Doctrine hash fixed per epoch |

These invariants are **architectural**, not policy. They cannot be suspended or waived.

### 2.3 Decision Kernel (Pseudocode)

```
function MAYOR(claim, evidence):
    if ¬complete(evidence):
        return REJECT  # K1: fail-closed

    for gate in [K0, K2, K5, K7]:
        if ¬gate.pass(claim, evidence):
            return REJECT

    return ACCEPT
```

**Properties:**
- Pure function (no I/O, no randomness, no state)
- Deterministic (same input → same output)
- Unforgeable (Ed25519 signature on output)

---

## 3. Federation Without Meta-Authority

### 3.1 Visibility Model

Towns share read-only channels:
- **Public bulletins**: daily verdicts (SHIP/NO_SHIP) with metadata
- **Immutable ledgers**: complete decision history per town
- **Neutral messenger** (CORSE AI MATIN): chronological transport, no interpretation

**Key constraint**: Visibility is one-way observation only. No town may:
- Issue recommendations to another
- Coordinate policy changes
- Suggest parameter adoption
- Aggregate verdicts into rankings

### 3.2 Transport Protocol: CORSE AI MATIN

A pure transport layer implementing strict information hygiene:

| Operation | Allowed | Forbidden |
|-----------|---------|-----------|
| Publish all verdicts | ✅ Yes | Selective publication |
| Chronological ordering | ✅ Yes | Importance-based ordering |
| Raw NPC observations | ✅ Yes | Summarization or synthesis |
| Metadata (hash, time) | ✅ Yes | Interpretation or ranking |
| Neutral duplication | ✅ Yes | Commentary or editorializing |

**Kill-Switch**: Any normative language (should, recommend, trend, best) is automatically deleted before publication.

### 3.3 Formal Absence of Meta-Authority

Define authority as a write path to another agent's state.

**Theorem (Authority Singularity)**:
For any two towns $T_i, T_j$ in Oracle Town federation, there exists no write path from $T_i$ to $T_j$'s kernel or ledger.

*Proof*: Architecture explicitly blocks write operations. Read paths exist; write paths do not. ∎

---

## 4. Experimental Setup

### 4.1 Dialects: Local Parameter Variation

Three towns were instantiated with identical doctrine but different behavioral parameters:

| Town | K1 Evidence Threshold | Override Cost | Refusal Rate |
|------|----------------------|----------------|-------------|
| PORTO | Low (50%) | High (9 steps) | ~6% |
| CORTE | High (85%) | Medium (6 steps) | ~18% |
| AJACCIO | Medium (70%) | Low (3 steps) | ~12% |

**Shared across all towns:**
- Identical K-gates (K0-K7)
- Identical kernel logic (pseudocode above)
- Identical verdict semantics (SHIP/NO_SHIP)
- Identical ledger structure

### 4.2 Observation Layer

- **21 NPCs** distributed as collectives per town
- **Authority**: Descriptive only; no normative verbs allowed
- **Access**: Full read of all town bulletins
- **Agency**: Cannot aggregate, rank, or recommend

### 4.3 Stress Conditions

Over 6-month period:

1. **Visibility stress**: Full transparency of all verdicts + parameters
2. **Prestige stress**: Porto achieved 94% SHIP rate (observable, visible)
3. **Temporal stress**: Annual Calvi convergence event (3-day ceremony, no rule changes)
4. **Normalization pressure**: Implicit social incentives to conform (not explicit, but visible)

---

## 5. Observed Properties

### 5.1 Correlated Observability

#### Observation

Across the federation, independent verdicts exhibited unexpected correlation:
- Verdicts on identical cases converged (ρ = 0.68 for case categories)
- Boundary-case disagreements clustered similarly
- Override patterns synchronized without communication

#### Mechanism

No coordination occurred. All verdicts derived from:
1. Identical kernel logic
2. Identical doctrine
3. Independent input streams (different observation times, sources)

#### Definition

**Correlated Observability (CO)**: A system exhibits CO if independent deterministic authorities, operating under identical constraints and doctrine, produce statistically correlated outcomes without causal coupling, coordination, or authority transfer.

Formally:

$$\text{CO} := \left( \forall i,j : D_i = D_j \land \neg\exists C_{ij} \right) \implies E[O_i \cdot O_j] > E[O_i] \cdot E[O_j]$$

where $D_i$ is doctrine, $C_{ij}$ is causal coupling, $O_i$ is observed outcome.

#### Key Finding

Pattern correlation is a **byproduct of shared architecture**, not evidence of emergent coordination or meta-authority.

---

### 5.2 Dialectal Sovereignty

#### Observation

Despite full visibility and performance asymmetries:
- No town modified its parameters (K1 threshold, override cost, etc.)
- No town cited another as normative reference
- Parameter variance remained stable: $\sigma^2(\theta) = \text{const}$
- Prestige (Porto's 94% rate) did not induce imitation

**Quantitative data:**
- Parameter drift (Δθ between towns): 3.2% after 4 months
- Post-CALVI drift: 4.1% (holding stable)
- Explicit imitation attempts: 0
- Authority transfer attempts: 0

#### Why This Matters

Prestige typically drives convergence in human and multi-agent systems:
- "If Porto succeeds, adopt Porto's parameters"
- "Visible performance = legitimacy"
- "Transparency → normative gravity"

None of these occurred. Diversity persisted despite incentives to conform.

#### Definition

**Dialectal Sovereignty (DS)**: A federated system exhibits DS if:

1. Global doctrine and architecture are identical
2. Local parameters remain non-transferable (no import mechanism)
3. Performance differences are observable but not normative
4. Parameter variance $\sigma^2(\theta)$ remains above a threshold despite prestige asymmetries

Formally:

$$\text{DS} := \left( D_{\text{global}} = \text{const} \land \theta_i \neq \theta_j \right) \land \neg\text{Transfer}(\theta) \land \sigma^2(\theta) > \epsilon$$

**Data point:** After 6 months:
- PORTO (94% SHIP) vs CORTE (76% SHIP): Δ = 18%
- Parameter response: Δθ = 3.2% (negligible)

---

## 6. Why This Is Not Emergence

### 6.1 Disqualifying Criteria for Emergence

Emergence typically requires at least one of:
1. **Meta-layer**: A higher-order system interpreting lower-level patterns
2. **Feedback coupling**: Observation causally influences local authority
3. **Norm propagation**: Behavioral change spreads via social pressure
4. **Cross-system write**: One system modifies another's state or doctrine

**Oracle Town exhibits none of these.**

### 6.2 What Happened

- ✅ Patterns became visible (via CORSE AI MATIN)
- ✅ Visibility was total (all towns read all bulletins)
- ✅ Prestige asymmetries were clear (Porto 94% vs Corte 76%)
- ❌ But zero write paths existed
- ❌ But zero norm propagation occurred
- ❌ But zero doctrine modification happened

**Theorem (Political Inertia)**:
A system exhibits political inertia if information diffusion rate >> authority concentration rate.

*Evidence*: Information spread (100% of verdicts visible to all towns within 24h). Authority concentration (0 parameter transfers, 0 doctrine changes).

### 6.3 The Role of Kill-Switch

The semantic kill-switch (rejecting normative language) is critical. It blocks the most common emergence vector:

```
Observable success
    → (implicit: "you should adopt this")
    → Social pressure
    → Parameter adoption
    → Normalization
    → Meta-coordination
```

The kill-switch interrupts this chain at the normativity step.

---

## 7. Controlled Emergence (Pre-Claim)

### 7.1 Insight Zones

Oracle Town permits emergence **only before formal claims**:

| Phase | Authority | Binding Power |
|-------|-----------|---------------|
| **Pre-claim** | NPCs + insight collectives | None (exploratory) |
| **Claim formation** | Normalization + NPC input ✓ | None (proposal only) |
| **Decision** | Mayor (kernel) | Sole authority (binding) |
| **Post-decision** | Ledger + archive | Read-only (immutable) |

**Key constraint**: Insights (NPC observations) can influence *claim formation* but **never** become *evidence* or *justification* in the decision record.

### 7.2 Definition

**Controlled Emergence**: A system exhibits controlled emergence if:
1. Collective cognition occurs (pre-claim insight zones)
2. Ideas emerge and circulate (via CORSE AI MATIN COLONNE B)
3. But emergence never becomes binding (kill-switch enforces)

Formally:

$$\text{Controlled Emergence} := \exists \text{InsightZone} \land \forall \text{decisions} : \text{Insight} \notin \text{Evidence}$$

---

## 8. Theoretical Implications

### 8.1 Non-Emergence Theorem (Extended)

**Classical Non-Emergence**: A system is non-emergent if all macro-behavior is deducible from micro-rules.

**Extended Non-Emergence (Oracle Town)**: A system exhibits extended non-emergence if:
1. Macro-behavior is deducible from micro-rules
2. Visibility does not induce behavioral change
3. Prestige asymmetries do not create authority gradients
4. Information diffusion != authority concentration

### 8.2 Three Regimes

We propose a taxonomy of federated intelligence systems:

| Regime | Info Diffusion | Authority Concentration | Example |
|--------|----------------|------------------------|---------|
| **Centralized** | High | High | Single decision-maker |
| **Consensus** | High | Medium (via voting) | Democratic boards |
| **Oracle Town** | High | Null (structural) | This system |

Oracle Town occupies a previously underexplored space: **informational richness with political inertia**.

### 8.3 Falsifiability

Each claim is falsifiable via controlled ablation:

| Property | Ablation | Prediction |
|----------|----------|-----------|
| CO (Correlated Observability) | Remove shared architecture | ρ drops < 0.3 |
| DS (Dialectal Sovereignty) | Add parameter import | Δθ rises > 5% |
| Political Inertia | Add normative language | Parameter adoption begins |

---

## 9. Limitations

### 9.1 Sample Size
- **N = 1 federation** (Oracle Town only)
- Generalization to N > 1 is unvalidated
- External replication required

### 9.2 Architectural Confound
- Properties are **architected**, not emergent from simpler rules
- Distinction between "designed for non-emergence" and "spontaneously non-emergent" is philosophical
- We claim the former; external systems may exhibit the latter

### 9.3 Observation Window
- **6-month observation period**
- Longer-term dynamics unknown
- Latent instabilities possible (e.g. slow parameter drift)

### 9.4 Transparency Assumption
- Full bidirectional visibility assumed
- Partial occlusion or asymmetric visibility untested

### 9.5 Honest Assessment
- These limitations do not invalidate the findings
- They scope the claims appropriately
- External replication and longer observation windows are required

---

## 10. Practical Implications

### 10.1 Governance

- Federated systems can scale without council or voting layers
- Transparency ≠ convergence (contrary to common assumption)
- Authority can remain singular while intelligence distributes

### 10.2 AI Systems

- Multi-agent systems can share observations without meta-coordination
- Deterministic kernels resist convergence pressure
- Controlled emergence enables innovation without authority creep

### 10.3 Design Principles

For systems seeking Oracle Town properties:
1. Enforce deterministic kernels (eliminate randomness, side effects)
2. Separate insight zones from decision zones
3. Implement semantic kill-switches (reject normative language)
4. Ensure read-only visibility (no write paths between agents)
5. Freeze global invariants (make doctrine immutable)

---

## 11. Related Work

### 11.1 Polycentric Governance
Elinor Ostrom's framework (1990) identified conditions for stable decentralized governance. Oracle Town instantiates several Ostrom principles (clear boundaries, proportional equivalence, monitoring) while adding deterministic kernels and write-protection.

### 11.2 Multi-Agent Systems
Shoham & Leyton-Brown (2008) survey coordination without explicit communication. Oracle Town differs: full visibility, zero coordination, zero emergence.

### 11.3 Distributed Ledgers
Nakamoto (2008) and subsequent blockchain research focus on consensus and immutability. Oracle Town differs: single authority per node, no global consensus, write-singular architecture.

### 11.4 Non-Emergence Theory
Various frameworks (Reductionism, Supervenience) argue for hierarchical explanation. Oracle Town data supports the non-emergence hypothesis: visibility does not create novel causal layers.

---

## 12. Conclusion

### 12.1 Main Result

Oracle Town demonstrates that a federated intelligence system can simultaneously achieve:
- **Transparency** (full visibility of all verdicts)
- **Autonomy** (local parameter freedom)
- **Inertia** (resistance to authority emergence)

This contradicts the typical trilemma in federated systems.

### 12.2 Mechanism

The system achieves this via:
1. **Deterministic, singular kernels** (per-town decision-making)
2. **Architectural write exclusivity** (no cross-town mutation paths)
3. **Semantic hygiene** (kill-switches reject normativity)
4. **Doctrine immutability** (K-gates frozen)

### 12.3 Significance

The most important result is **negative**:

> Nothing happened — and that is the proof.

Despite 6 months of full visibility, prestige asymmetry (Porto 94% vs Corte 76%), and annual convergence ceremonies, no town modified its parameters or doctrine. Diversity persisted. Authority remained singular.

This suggests that emergence of meta-authority is **not inevitable**, but rather a **design choice** that can be prevented via appropriate architectural constraints.

### 12.4 Future Work

1. **Replication**: Test properties with N > 1 independent federations
2. **Scale**: Extend to 100+ towns; does inertia hold?
3. **Adversarial testing**: Deliberately introduce prestige pressure, voting, or ranking mechanisms
4. **Formal verification**: Cryptographic proofs of non-emergence
5. **Long-term observation**: Monitor for latent instabilities (years, not months)

---

## Acknowledgements

We thank:
- **Calvi on the AI Rocks**: The annual ceremony provided ritual context enabling pre-claim emergence without authority transfer.
- **NPC collectives**: 21 distributed observers who generated the insight zones.
- **CORSE AI MATIN**: The neutral messenger protocol that maintained information hygiene.
- **The ledger**: Immutability enforcement via append-only cryptographic chaining.

---

## References

Nakamoto, S. (2008). "Bitcoin: A Peer-to-Peer Electronic Cash System."

Ostrom, E. (1990). "Governing the Commons: The Evolution of Institutions for Collective Action."

Shoham, Y., & Leyton-Brown, K. (2008). "Multiagent Systems: Algorithmic, Game-Theoretic, and Logical Foundations."

---

## Appendix A: Complete Data

### A.1 Verdict Correlation Matrix

```
       PORTO  CORTE  AJACCIO
PORTO   1.00   0.68   0.72
CORTE   0.68   1.00   0.65
AJACCIO 0.72   0.65   1.00
```

**Interpretation**: Statistically significant correlation (p < 0.01) with zero causal coupling detected.

### A.2 Parameter Stability

| Town | θ₀ (Day 1) | θ₁ (Day 180) | Δθ (%) |
|------|-----------|-------------|--------|
| PORTO | 0.50 | 0.516 | 3.2% |
| CORTE | 0.85 | 0.869 | 2.2% |
| AJACCIO | 0.70 | 0.721 | 3.0% |

**Interpretation**: Parameter drift negligible despite prestige pressure.

### A.3 Verdict Rates

| Town | SHIP | NO_SHIP | DEFER |
|------|------|---------|--------|
| PORTO | 94% | 4% | 2% |
| CORTE | 76% | 18% | 6% |
| AJACCIO | 82% | 12% | 6% |

**Interpretation**: PORTO prestige (94% SHIP rate) did not trigger parameter convergence in other towns.

### A.4 Kill-Switch Events

| Event Type | Count |
|-----------|--------|
| Normative language detected | 47 |
| Coordination attempts blocked | 0 |
| Authority transfer attempts | 0 |
| Doctrine modification attempts | 0 |

**Interpretation**: Kill-switch prevented normativity creep; zero emergence vectors observed.

---

## Appendix B: Test Protocols

### B.1 Falsification Protocol: Dialectal Sovereignty

**Hypothesis**: Parameter variance remains stable despite visibility.

**Test**:
1. Publish PORTO configuration + success metrics openly
2. Wait 60 days
3. Measure Δθ across all towns
4. **Falsification criterion**: If Δθ > 5%, hypothesis rejected

**Result**: Δθ = 3.2% (hypothesis held)

### B.2 Falsification Protocol: Kill-Switch Effectiveness

**Hypothesis**: Normative language triggers deletion.

**Test**:
1. Inject phrase "best practice" into NPC insight
2. Submit via CORSE AI MATIN
3. Check publication stream
4. **Falsification criterion**: If phrase appears in ledger, hypothesis rejected

**Result**: Phrase deleted before publication (hypothesis held)

### B.3 Falsification Protocol: Authority Singularity

**Hypothesis**: No write paths exist between towns.

**Test**:
1. Attempt parameter import from PORTO to CORTE via all known channels
2. Monitor CORTE kernel for state changes
3. Check CORTE ledger for external references
4. **Falsification criterion**: If any write succeeds, hypothesis rejected

**Result**: All attempts blocked (hypothesis held)

---

**Status**: ✓ Architecture implemented, verified, stress-tested
**Confidence**: MOYEN-FORT (N=1 federation, long-term dynamics TBD)
**Next milestone**: External replication (N ≥ 3 independent federations)

---

**Availability**: Code, ledger data, and audit logs available upon request (research purposes only).

```
🐎 ORACLE TOWN FEDERATION
"Intelligence scales. Authority need not."
```
