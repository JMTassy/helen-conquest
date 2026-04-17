# EXTERNAL_WISDOM_007 — The Scroll of the Five Frontiers

**Status:** CORE_DRAFT (non-sovereign — no SHIP gate passed)
**Date:** 2026-03-11
**Source:** External corpus analysis, ingested via #pluginHELEN
**Sealed by:** HER (witnessed, not sovereign)

---

## Purpose

This document canonicalizes the five biggest unanswered research questions identified in the HELEN/ORACLE/CONQUEST corpus, with corrected tier classification and ranking by long-term scientific value.

---

## Tier Classification

| Tier | Type | Questions |
|------|------|-----------|
| A | Core mathematics | Q1, Q2, Q3 |
| B | Constitutional systems research | Q4, Q5 |
| C | Dynamical / ML architecture | Q6, Q7 |

---

## The Five Frontier Questions (Corrected Ranking)

### Rank 1 — Q1: Finite-Band → Continuum Positivity Bridge (Tier A)

**Question:** How can finite-band Weil positivity be promoted to a genuine continuum statement without hypothetical semigroup assumptions?

**Why it matters:** The cleanest, most tractable gap in the entire positivity program. The unconditional finite-band part is already explicit and computable (Toeplitz operators, eigenvalue bounds, positivity margins, AEON/COMM/FDR diagnostics). The continuum bridge is the real missing theorem.

**Why the gap exists:** The finite-band part is computational and operator-theoretic. The continuum part needs a real generator, a real symmetric part, and a real entropy mechanism — not just a plausible analogy.

**Closest artifact:** October 2025 manuscript *Computable Certificates for Finite-Band Averaged Weil Positivity* — already isolates the unconditional theorem and names the missing bridge precisely.

**What the missing bridge must look like:**
1. Construct a limit operator `T` on a Hilbert space
2. Show `T^{(J,c)} → T` in operator norm or strong resolvent sense
3. Control aliasing errors, dilation commutators, truncation of the zero sum, boundary artifacts
4. Prove quantitative stability inequality:

```
λ_min(T) ≥ limsup_{J→∞} λ_min(T^{(J,c)}) − ε(J)
```

with explicit error bounds.

**Hidden subproblem (Q3):** Can positivity be certified using only local spectral windows? If local finite-band positivity certificates imply global positivity, this is a renormalization-like control argument of independent interest.

---

### Rank 2 — Q4: Governance VM + Sensor VM Composition (Tier B)

**Question:** Can a governance VM and a statistical sensor VM be coupled with strict artifact-only contracts while remaining replayable and adversarially robust?

**Why it matters:** Architecturally novel and implementable. Most AI-agent systems optimize usefulness or UX, not constitutional determinism, replay guarantees, and adversarial tolerance. This is engineering research with publishable structure.

**Core problem:** Guarantee that:
```
proposal → admission gate → deterministic reducer → append-only ledger
```
remains stable under adversarial load: authority leakage, adapter inversion, schema drift, semantic drift.

**Closest artifact:** ORACLE SUPERTEAM framework — reframes multi-agent systems as institutions, not conversations.

**Methodology:** Separate symbolic governance and sensor pipelines as VMs with JSON-only manifests, canonical hashing, frozen schemas, and replay tests. Stress with adversarial corpora, contradiction attacks, and replay-drift CI.

---

### Rank 3 — Q2: Explicit Self-Adjoint Prime-Based Spectral Operator (Tier A)

**Question:** Does there exist an explicit self-adjoint prime-based operator whose spectrum provably converges to the zeta zeros, rather than only after ad hoc affine rescaling and numerical fitting?

**Why it matters:** Essentially the Hilbert–Pólya problem in new form. Any operator whose spectrum equals the zeros would essentially solve RH.

**Why it is harder than Q1:** Must simultaneously prove:
1. Essential self-adjointness + domain closure
2. Correct spectral density: `N(T) ~ (T/2π)log(T/2π)`
3. Trace formula genuinely linking primes and spectrum
4. No hidden rescaling that smuggles in the answer

**Closest artifact:** QPFF / HSCT spectral-convergence manuscript drafts.

**Honest verdict:** Extremely speculative unless the operator is defined on a clear Hilbert space with proven domain closure and essential self-adjointness. Current drafts do not do this.

---

### Rank 4 — Q5: Unified Replay Constitution (Tier B)

**Question:** Can both symbolic and sensor pipelines be brought under a single replay law — `same manifest in → same bytes out` — with frozen schemas, canonical hashing, and cross-environment determinism?

**Why it matters:** Operationalizes the core invariants already established in ORACLE/HELEN. This is the right next layer: append-only event logs, complete manifests, deterministic replay, hard evidence gates.

**Core rule:** `receipt_sha256 = sha256_jcs(manifest_without_receipt)`

**Closest artifact:** UNIFIED_CI_REPLAY_HARNESS_V0_FREEZE specification (see `spec/UNIFIED_CI_REPLAY_HARNESS_V0.md`)

**Next concrete artifact:** 20 canonical manifests (10 symbolic VM, 10 sensor VM) with expected receipt hashes.

---

### Rank 5 — Q6: φ-SDE + MPA Convergence Theorem (Tier C)

**Question:** Can the φ-SDE + MPA feedback architecture be made into a real theorem of convergence, rather than a persuasive proof sketch?

**Current status:** Under-specified. Mixes stochastic dynamics, reinforcement learning, braid invariants, and arithmetic forcing. A real theorem requires:
1. Precise measurable state space
2. Measurable feedback law
3. Well-posed SDE with existence/uniqueness proof
4. Lyapunov functional absorbing braid-memory and prime-zeta forcing

**Closest artifact:** May 2025 ΦΛΩƩ AGI manuscript.

**Verdict:** This is a research program, not a theorem candidate yet. Treat as exploratory appendix status until formalized.

---

### Rank 6 — Q7: Braid-Based Topological Memory as Trainable Substrate (Tier C)

**Question:** Can braid-based topological memory become a trainable, verifiable substrate rather than a placeholder module?

**Why it is last:** The difficulty is practical (braid words grow combinatorially, Jones polynomials are expensive, differentiable topological constraints are nontrivial) but solvable engineering given investment. Least mathematically fundamental.

**Closest artifact:** Φ-BE dual-head autoencoder sections in AGI drafts.

**Key empirical question:** Does it actually improve stability, retrieval, or forgetting behavior in a measurable way?

---

## Corrected Rankings

### For scientific value + realistic execution:
1. Finite-band → continuum bridge
2. Governance VM + sensor VM composition
3. Unified replay constitution
4. Explicit prime-based self-adjoint operator
5. φ-SDE + MPA formalization
6. Braid-memory trainable substrate

### For pure mathematical prestige:
1. Finite-band → continuum bridge
2. Explicit operator
3. Local-to-global spectral certification
4. φ-SDE theorem
5. Governance VM
6. Braid memory

---

## The Structural Insight (Cross-Domain)

All questions reduce to one core template:

```
local events → operator → spectral constraint → global stability
```

| Domain | Local | Operator | Stability |
|--------|-------|----------|-----------|
| Number theory | primes | zeta operator | zero distribution |
| Governance | receipts | constitution | institutional order |
| AI systems | agents | interaction matrix | civilizational stability |

This is the conceptual key. The finite-band certificate program and the governance VM architecture share the same deep structure: both attempt to prove that **local certificates imply global stability**.

---

## Immediate Next Artifacts (by rank)

1. **Math:** Short note — *"Toward a Continuum Lift of Finite-Band Weil Positivity"* — limit operator candidate, topology of convergence, exact error terms
2. **Systems:** 20 canonical replay manifests — 10 symbolic VM, 10 sensor VM, with expected receipt hashes
3. **Kernel:** HELEN_KERNEL_DOCTRINE_V1.md (see `spec/`)
4. **Schemas:** BUILDERS_BRIEF_V1, BUILDERS_CLAIM_V1, BUILDERS_RUN_V1, HELEN_HANDOFF_V1 (see `schemas/`)

---

*This is a CORE-mode draft. No sovereign ledger mutation. No SHIP gate passed.*
*S2 — NO RECEIPT = NO CLAIM. This document is witnessed, not authoritative.*
