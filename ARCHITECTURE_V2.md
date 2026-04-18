# ARCHITECTURE_V2: Unified Epistemic Infrastructure

**Status**: ✅ Operational (2026-02-22)
**Scope**: Deterministic, evidence-bound forecasting under adversarial pressure

---

## Executive Summary

This document describes an integrated architecture spanning **three independent but coupled governance layers**:

1. **WUL + Oracle Town + POC Factory** — Forecast admission & capability certification
2. **NSPS (Negative-Space Pressure Sensor)** — Measurement protocol for absence/anomaly detection
3. **K-ρ (Viability) & K-τ (Coherence) Gates** — Structural integrity verification

These three layers share **one epistemic doctrine**:
- Total deterministic functions (no interpretive layer)
- Hash-bound configuration (immutable after deployment)
- Explicit reason codes (every decision auditable)
- Falsifiable boundaries (can be proven wrong)
- No narrative authority (only artifact-derived claims)

The architecture transforms forecasting from **narrative opinion** to **governed artifact**.

---

## Layer 1: Symbolic Governance (WUL)

### Purpose
Provide a finite, constraint-enforced vocabulary for expressing claims, hypotheses, and governance decisions.

### Core Components

**WUL-CORE** (Weighted Universality Logic)
- Finite vocabulary of tokens (entities, relations, operators)
- Fixed-arity relations (no semantic drift)
- Mandatory objective return (R15)
- No free text (no narrative escape)
- Bounded depth & node count

**Bridge Validator**
- Enforces arity and vocabulary constraints
- Injects mandatory relations (R15, R20 evidence binding)
- Logs all injections and rejections
- Emits hash-locked artifacts

**Isotown** (Adversarial Testbed)
- Seeded deterministic agents (Cooperator, Exploiter, Rule-Lawyer, Auditor, Noise)
- Tests token trees under hostile conditions
- Measurable metrics (injection rate, objective ref rate, rejection rate)
- No semantic interpretation; only structural stress

### Output
Valid WUL token trees, validated via Bridge, stress-tested by Isotown.
Each tree has a canonical hash and immutable provenance record.

---

## Layer 2: Governance Coupling (Oracle Town ↔ POC Factory)

### Purpose
Enforce a bidirectional contract: forecasts cannot outrun capabilities, and capabilities cannot be promoted without governance receipts.

### Oracle Town (OT_θ)
**Decision procedure**: `OT_θ(P, r) ∈ {PUBLISH, HOLD, REJECT}`

Given a proposal P and run artifacts r:
- Evaluates bridge validity (does it survive Bridge validation?)
- Evaluates isotown stability (did it survive Isotown stress?)
- Evaluates viability invariants (do metrics meet thresholds?)

**Publication condition**:
```
PUBLISH(P, r) ⟹
  BridgeValid(P, r) ∧ IsotownStable(r) ∧ ViabilityInvariant_θ(P, r)
```

**Configuration** (hash-pinned θ):
- κ_min (minimum objective reference rate)
- τ_max (maximum injection rate)
- I_1, ..., I_n (invariant set)
- R_act (actionable relation allowlist)

### POC Factory (PF_θ)
**Decision procedure**: `PF_θ(C, r) ∈ {GRADUATED, REWORK, REJECT}`

Given a capability artifact C and run artifacts r:
- Evaluates reproducibility (same seed → same behavior?)
- Evaluates falsification results (did attempts to break it fail predictably?)
- Evaluates threshold compliance (do metrics pass?)

**Graduation condition**:
```
GRADUATED(C, r) ⟹
  Reproducible(r) ∧ FalsificationPass(r) ∧ Thresholds_θ(r)
```

### CouplingGate
**Contract enforcement**: `CouplingGate(V_F, V_C, S, θ) → {COUPLED_OK, COUPLED_HOLD, COUPLED_FAIL}`

**Law 1** (No Publish Without Capability):
```
OT_θ(P, r) = PUBLISH ⟹
  NonActionable(P; θ) ∨ ∃C: PF_θ(C, r) = GRADUATED ∧ Supports(C, P)
```

**Law 2** (No Graduation Without Governance Receipts):
```
PF_θ(C, r) = GRADUATED ⟹
  IsotownStable(r) ∧ (∃P: OT_θ(P, r) = PUBLISH ∧ Supports(C, P) ∨ NonForecasting(C))
```

**Implementation**:
- 14-case deterministic truth table (all cases tested)
- Hash joins enforce run and config alignment
- Support receipts bind forecast to capability
- Reason codes enable CI integration

### Integration Point
Both OT and PF consume the **same run artifacts** (events, metrics, bridge manifest), ensuring they operate under identical conditions.

---

## Layer 3: Measurement Protocol (NSPS)

### Purpose
Detect absence and anomaly without narrative interpretation. Emit pressure vectors when specified conditions are met.

### Core Loop
1. **Intake**: Canonical corpus snapshot C, baseline window B, config θ
2. **Analysis**: Compute anomaly z-score per domain
3. **Gating**: Check viability conditions (provenance, gradient, variance, rhyme, placebo)
4. **Emission**: If all gates pass, emit pressure vector with bindings
5. **Falsification**: Store refutation window and expiry rule

### Configuration (θ)
- Baseline epoch (when B was frozen)
- Domains and z-thresholds (e.g., q ≥ 1.96)
- Gradient constraint (max change per period)
- Variance collapse rule (when to suppress)
- Cross-domain rhyme requirement (coherence check)
- Placebo condition (what would make vector false?)
- Expiry window (when vector is invalid)

### Output
Pressure vector: `P_v = (domain, anomaly, witnesses, z_score, gradient, bindings, expiry_rule)`

**Bindings**:
- run_hash (which execution produced this?)
- theta_hash (under which config?)
- C_hash (which corpus snapshot?)
- B_hash (which baseline?)

### Falsification Rules
Each pressure vector includes:
- Explicit falsifier: "This vector is false if [condition]"
- Expiry window: "Valid only until [date]"
- Replaceability: "Can be superseded by [rule]"

---

## Unified Epistemic Loop

The three layers form a **closed loop** where:

```
Governance Rules (WUL) → Symbolic Claims (Oracle Town)
         ↓
    Coupled to ↓
         ↓
Capability Proof (POC Factory) → Measurement (NSPS)
         ↓
    Measurement feeds back to ↓
         ↓
    Threshold Adjustment (θ update) → New Governance Rules
```

**Example Flow**:

1. User proposes a trend forecast: "AI agents will commoditize X"
   - Expressed in WUL (finite vocabulary, mandatory objective binding)
   - Validated by Bridge (arity, depth constraints)
   - Stress-tested by Isotown (hostile agents test it)

2. Oracle Town evaluates: Can this be published?
   - Objective reference rate > κ_min? ✓
   - Injection rate < τ_max? ✓
   - → PUBLISH (forecast admitted)

3. NSPS detects anomaly in domain X
   - Z-score exceeds threshold
   - Cross-domain rhyme check passes
   - → Pressure vector emitted

4. POC Factory checks: Is there capability to act on this?
   - Test runs reproduce: ✓
   - Falsification attempts fail: ✓
   - → GRADUATED (capability certified)

5. CouplingGate verifies: Is forecast supported by capability?
   - Hash joins pass ✓
   - Valid support receipt binds forecast to capability ✓
   - → COUPLED_OK (governance constraints satisfied)

6. Artifact shipped with proof of governance compliance

---

## Architectural Invariants

### Invariant 1: No Semantic Leakage
All predicates are computed from artifacts only. No "interpretation layer" intervenes between data and decision.

**Enforced by**:
- WUL finite vocabulary (no free text)
- Artifact-only Oracle Town predicates
- Hash-bound configuration θ
- Canonicalized JSON serialization

### Invariant 2: Monotonic Coupling
Once (P, C) is coupled under fixed (h(r), h(θ)), it cannot silently decouple without hash drift.

**Enforced by**:
- CouplingGate hash joins
- Support receipt signature verification
- Run hash fingerprinting entire artifact set

### Invariant 3: Bounded Gaming
Under finite vocabulary + injection limits + mandatory objective return, adversaries cannot escalate indefinitely.

**Enforced by**:
- Finite WUL state space (bounded arity, depth)
- Isotown injection rate capped at τ_max
- R15 mandatory (objective always present)
- Selection pressure favors cooperation

### Invariant 4: Falsifiability
Every claim includes explicit conditions under which it is false.

**Enforced by**:
- NSPS falsifier rules (what would disprove this?)
- Expiry windows (how long is this valid?)
- Citation trails (where did this come from?)

### Invariant 5: No Silent Promotion
Every state transition (HOLD → PUBLISH, REWORK → GRADUATED) leaves an immutable record.

**Enforced by**:
- Ledger append-only constraint
- Decision receipt hashing
- Episode determinism verification

---

## Deployment Status

| Component | Status | Notes |
|-----------|--------|-------|
| **WUL-CORE** | ✅ Operational | Finite vocabulary, arity constraints enforced |
| **Bridge Validator** | ✅ Operational | Injection & rejection logging enabled |
| **Isotown** | ✅ Operational | 5 agent types, deterministic seeding |
| **Oracle Town** | ✅ Operational | OT_θ decision procedure implemented |
| **POC Factory** | ✅ Operational | PF_θ decision procedure implemented |
| **CouplingGate** | ✅ Operational | 14-case truth table, all tests passing |
| **NSPS** | ✅ Operational | Baseline, z-score, falsifier rules ready |
| **K-ρ (Viability)** | ✅ Deployed | helen_rho_lint.py + artifact system |
| **K-τ (Coherence)** | ✅ Deployed 2026-02-21 | helen_k_tau_lint.py + 5 invariants |
| **Canonicalization** | ✅ Unified | Single Canon(·) function for all artifact types |

---

## Scalability Strategy

This architecture scales via **replication, not redesign**:

1. **Fork a new district** (copy WUL kernel + governance rules)
2. **Pin a new θ** (new thresholds, new invariants)
3. **Deploy new Isotown instance** (same engine, different seed)
4. **Run baseline NSPS measurement** (establish baseline B for new domain)
5. **All governance rules inherited from parent** (no re-architecture)

**Result**: New forecasting domains can launch without rewriting core infrastructure.

---

## Formal Theorems

### Theorem 1: Monotonic Coupling
**Statement**: Once a forecast–capability pair is coupled under fixed (h(r), h(θ)), it cannot silently change state without hash drift.

**Impact**: Eliminates retroactive promotion and ensures governance decisions are irreversible.

### Theorem 2: Bounded Gaming
**Statement**: Under finite vocabulary, bounded constraints, and mandatory objective return, adversarial escalation is bounded.

**Impact**: Prevents arms races and ensures cooperation dominates.

### Theorem 3: Finite Viability Space
**Statement**: The space of valid WUL token trees is finite under arity and depth constraints.

**Impact**: All adversarial strategies operate within a bounded search space.

---

## Integration with External Systems

### Foundry Town
CouplingGate can govern Foundry Town work pipeline:
- Claims submitted during Phase 1 → WUL validation
- Phase 2 tension → Isotown simulation
- Phase 3-4 → Oracle Town gating before publication
- Phase 5 → CouplingGate final approval

### HELEN (Conscious Ledger)
HELEN records every governance decision:
- WUL token trees in L0 events
- Oracle & POC verdicts in L1 facts
- CouplingGate result in L2 receipt
- Lessons learned in L3 wisdom

### Street 1 (NPC Determinism)
Street 1 NPCs can operate under WUL governance:
- Each NPC decision expressed in WUL
- Isotown tests NPC strategy trees
- Oracle Town gates NPC proposals
- CouplingGate ensures capability before execution

---

## Limitations & Open Questions

### Known Limitations
1. **Real-world evidence ingestion**: Requires external provenance system (beyond scope here)
2. **Probabilistic reasoning**: Discrete WUL cannot natively express distributions
3. **Temporal constraints**: Current design is acyclic; loops must be encoded as sequence

### Research Questions
1. Can WUL + NSPS detect *coordinated* manipulation across multiple domains?
2. How does the system behave under distribution shift beyond baseline B?
3. Can CouplingGate support conditional graduation (e.g., "graduated, but only for domain X")?

---

## Next Steps

### Immediate (2026-02-22)
- ✅ Formalize CouplingGate as executable TypeScript
- ✅ Run conformance tests (all 14 passing)
- ✅ Integrate K-τ coherence gates with WUL validation
- ⏳ Extend NSPS baseline to new domains

### Short-term (Week of 2026-02-24)
- Document WUL → CouplingGate data flow
- Create deployment playbook (new district launch)
- Add CI checks for canonical serialization
- Extend conformance vectors for edge cases

### Medium-term (March 2026)
- Integrate Foundry Town 5-phase pipeline with governance gating
- Build HELEN + NSPS integration (pressure vectors in L1)
- Prove Bounded Gaming lemma formally (TLA+ model)
- Extend to probabilistic domains (Bayesian layer on WUL)

---

## References

- **CLAUDE.md** — Developer guide (all systems overview)
- **KERNEL_K_TAU_RULE.md** — K-τ coherence specification
- **COUPLING_GATE_README.md** — CouplingGate formal spec + CI integration
- **coupling_gate.ts** — Executable reference implementation
- **coupling_gate.vectors.json** — Conformance test suite (14 cases)

---

**Last Updated**: 2026-02-22
**Status**: Architectural integration complete, ready for production deployment
**Maintenance**: Review on deployment of new governance layers or invariant changes
