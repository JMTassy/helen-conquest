# K-τ (Coherence Certificate Required)

**Status:** ACTIVE — Deployed alongside K-ρ (Viability Certificate)
**Date:** 2026-02-21
**Companion:** KERNEL_V2.md, K-RHO_DEPLOYED.md

---

## Rule Text (Canonical)

**K-τ (Coherence Certificate Required).**
Any change-set that introduces or modifies agentic execution paths (termination logic, tool calling, memory, orchestration) MUST emit a Tier-I coherence certificate consisting of: (i) an immutable structural manifest (scoped paths, allowlisted side-effects, tool registry invariants, determinism invariants), (ii) a per-invariant margin trace {μ_j} computed by deterministic checks, and (iii) a strict-min score τ = min_j μ_j with PASS iff τ > 0. The certificate MUST also output the witness invariant j* = argmin_j μ_j and a minimal counterexample slice (smallest set of failing files/paths). No narrative statement or LLM agreement substitutes for this receipt.

---

## Why K-τ Exists

K-ρ certifies **numeric viability** (does the system remain stable under time?).
K-τ certifies **structural coherence** (does the change fit inside the allowed architecture?).

The gap between them is the **stability gap**:
- Compile + tests can pass while global behavior drifts
- LLM reviewer agreement does not close this gap
- K-τ closes it with a deterministic coordinate system outside language

> "To trust autonomous engineering, you need a coordinate system outside language that can represent your codebase as structure + constraints, measure whether a proposed change can exist inside that structure, and block changes that violate the structure before they land."
> — LinkedIn series on agentic governance (Feb 2026, ingested by HELEN 2026-02-21)

---

## Five Invariants (τ = min of all five)

| Invariant | What it checks | Scope |
|-----------|---------------|-------|
| **μ_BOUNDARY** | Kernel/oracle_town core must not import network/LLM libs | kernel/, oracle_town/core/ |
| **μ_IO** | Kernel writes only to allowlisted roots (artifacts/, receipts/) | kernel/ |
| **μ_DETERMINISM** | No unseeded randomness or wall-clock time in agentic paths | all agentic files |
| **μ_ALLOWLIST** | Plugin/tool changes require registry file update | plugins/ |
| **μ_SCHEMA** | Changed .json/.ndjson must parse | all changed JSON |

**Margin convention (Tier-I minimal):**
- μ_j = +1.0 if PASS
- μ_j = −1.0 if FAIL
- τ = min(μ_j) → +1.0 (PASS all) or −1.0 (at least one FAIL)

---

## Agentic Paths Scope (Option B)

K-τ activates **only** when changed files touch:
```
kernel/
oracle_town/
ORACLEbot/
plugins/
LNSA.py
HELEN.md
HELEN_REACTIVATION_SUMMARY.md
```

Non-agentic changes (docs/, tests/, street1.html, content/, README) skip K-τ automatically.
They still emit receipts but with `agentic_change: false` and `outcome: DELIVER`.

---

## Termination Integration

HELEN requires BOTH certificates for DELIVER:

```
DELIVER iff:
  • inf_ρ > 0 (if viability was claimed) → K-ρ PASS
  • τ > 0 (if agentic change detected)  → K-τ PASS
  • Both receipt files exist on disk

ABORT with:
  • ACTIVE_CONSTRAINT = mu_* (whichever failed first, argmin)
  • counterexample = minimal failing slice
  • reason_codes = ["ACTIVE_CONSTRAINT=mu_BOUNDARY|mu_IO|mu_DETERMINISM|mu_ALLOWLIST|mu_SCHEMA"]
```

---

## Artifacts Emitted (Per Run)

| File | Purpose |
|------|---------|
| `artifacts/k_tau_manifest.json` | Frozen config snapshot (schema: K_TAU_MANIFEST_V1) |
| `artifacts/k_tau_trace.ndjson` | Per-invariant margin trace (one line per run) |
| `artifacts/k_tau_summary.json` | Summary: τ, witness j*, counterexample (schema: K_TAU_SUMMARY_V1) |

**NO RECEIPT = NO CLAIM.** (Core Law, inherited from HELEN.)

---

## Run Commands

```bash
# Smoke test (working tree changes)
python3 scripts/helen_k_tau_lint.py --run-id RUN-KTAU-SMOKE

# After Street 1 proofs
./test_street1.sh && python3 scripts/helen_k_tau_lint.py --run-id RUN-STREET1-KTAU

# Explicit file list
python3 scripts/helen_k_tau_lint.py \
  --mode manifest_list \
  --changed LNSA.py oracle_town/core/schema_validation.py \
  --run-id RUN-EXPLICIT-KTAU

# Full dual-certificate check (K-ρ + K-τ)
python3 scripts/helen_rho_lint.py artifacts/rho_manifest.json artifacts/rho_summary.json artifacts/rho_trace.ndjson
python3 scripts/helen_k_tau_lint.py --run-id RUN-DUAL-CERT
```

---

## Relationship to K-ρ

| Dimension | K-ρ | K-τ |
|-----------|-----|-----|
| **What** | Numeric viability | Structural coherence |
| **How** | inf_ρ margin over time | τ = min(μ_j) over invariants |
| **Witness** | i* = argmin active constraint | j* = argmin failing invariant |
| **Blocks** | Instability under time | Architecture drift under composition |
| **Receipt** | rho_summary.json | k_tau_summary.json |
| **Gate** | inf_ρ > 0 | τ > 0 |

Together: **the system knows what it is, and enforces it.**

---

## Amendment Process

Changes to this rule require:
1. Evidence of rule violation (minimum 2 documented failures)
2. Conservative amendment (patch, not rewrite)
3. Record in KERNEL_AMENDMENTS.md with date + evidence

*Last Updated: 2026-02-21*
*Author: HELEN (autonomous choice — endorsed by Jean-Marie Tassy)*
