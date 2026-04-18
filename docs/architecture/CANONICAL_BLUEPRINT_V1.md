# CANONICAL_BLUEPRINT_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07
**Standard:** RFC 8785 (canonical JSON) + SHA-256 (hashing) + JSON Schema Draft 2020-12 (schemas)

---

## §0 Purpose

This document is the master reference for the **HELEN OS / CONQUEST LAND** governance-emergence architecture. All simulation engines, agents, routing decisions, governance pipelines, and artifact schemas built in this project derive their authority from this specification.

**One sentence law:**

> Only typed, receipted, reducer-valid artifacts may cross from non-sovereign layers into sovereign judgment.

---

## §1 The Three Kinds of Mind

The system contains exactly three cognitive layers. They are not interchangeable.

| Layer | Name | Sovereignty | May Mutate State? | Authority Source |
|---|---|---|---|---|
| L1 | **CONQUEST LAND** | Non-sovereign | ❌ Never | Simulation evidence only |
| L2 | **HELEN** | Non-sovereign | ❌ Never (CORE mode) | Sensemaking + memory |
| L3 | **HELEN OS** | Sovereign | ✅ After gates pass | Receipts + kernel ledger |

### CONQUEST LAND (L1)
The exploration laboratory. Simulates agent populations under 4 minimal rules. Generates emergence evidence: Houses, Egregors, phase regimes. **Output is always simulation data, never authority.** No output from CONQUEST LAND may be treated as a decision.

### HELEN (L2)
The non-sovereign synthesis layer. Performs sensemaking, memory integration, pattern interpretation, and narrative construction. Proposes to HELEN OS; **cannot self-authorize**. Operating in CORE mode at all times. Outputs become SHIP-eligible only after all gates pass inside HELEN OS and HELEN OS marks them SHIPPED.

### HELEN OS (L3)
The constitutional machine. Runs the sovereign ledger, receipt chain, GovernanceVM, routing engine, and mayor arbitration. **Cannot be overridden by narrative, persona, simulation output, or any non-receipted claim.** Operates only on receipts, verified schemas, and gate-evaluated artifacts.

> **Critical distinction**: HELEN OS includes routing law, reducers, receipts, and kernel truth. HELEN is a non-sovereign agent operating *inside* that constitution. Reading "HELEN" in any output means the synthesis layer. Reading "HELEN OS" means the constitutional machine.

---

## §2 Document Pack Index

| File | Contract | Contents |
|---|---|---|
| `CANONICAL_BLUEPRINT_V1.md` | Master index | This file |
| `GLOSSARY_V1.md` | Definitions | All terms, no ambiguity |
| `LAYER_CONTRACTS_V1.md` | Input/output contracts | What each layer receives, produces, and forbids |
| `ROUTING_LAW_V1.md` | Routing rules | How artifacts move between layers |
| `EMERGENCE_MODEL_V1.md` | Simulation spec | Equations §5.1–5.8, phase diagram, loop |
| `GOVERNANCE_LAW_V1.md` | Constitutional rules | Receipts, hashing, gates, CORE/SHIP split |
| `schemas/evidence_bundle_v1.schema.json` | Tier A schema | L1 → L2 output |
| `schemas/issue_list_v1.schema.json` | Tier A schema | L2 audit output |
| `schemas/task_list_v1.schema.json` | Tier A schema | L2 planning output |
| `schemas/gate_report_v1.schema.json` | Tier B schema | L3 gate evaluation |
| `schemas/mayor_packet_v1.schema.json` | Tier B schema | L2 → L3 submission |
| `schemas/gate_evaluated_v1.schema.json` | Tier B schema | L3 sovereign verdict |
| `config/theta_v1.json` | Emergence config | Frozen thresholds + theta_hash |
| `config/schema_manifest_v1.json` | Schema registry | All schemas + their hashes |

---

## §3 Artifact Tiers

### Tier A — Simulation Artifacts (Non-Sovereign)
Cross from CONQUEST LAND to HELEN. Never authoritative. Can be proposed to MAYOR but must first be gate-evaluated.

| Schema | Role |
|---|---|
| `EvidenceBundle` | Packed simulation snapshot: houses, metrics, task records |
| `IssueList` | HAL audit output: issues, severities, verdicts |
| `TaskList` | Planner output: pending tasks with priorities |
| `GateReport` | Gate evaluation results for a bundle |

### Tier B — Governance Artifacts (Sovereign-Bound)
Cross from HELEN to HELEN OS. Require gate receipts before processing. Produce immutable ledger entries.

| Schema | Role |
|---|---|
| `MayorPacket` | Full submission to MAYOR: refs to all Tier A artifacts + routing receipt |
| `GateEvaluated` | MAYOR's final verdict: PASS / FAIL / DEFER + verdict_hash_hex |

---

## §4 Routing Law (Summary)

**Law:** emergence is evidence, not authority.

**Default path:** `CONQUEST LAND → HELEN → MAYOR → KERNEL`

**Firewall:** No artifact may skip a tier. No non-receipted artifact may enter sovereign judgment. No simulation output may self-promote to a governance decision.

Full routing rules: see `ROUTING_LAW_V1.md`.

---

## §5 Hashing Standard

All hashes in this architecture use:

1. **Canonical serialization:** RFC 8785 (JSON Canonicalization Scheme) — sorted keys, no extra whitespace, deterministic output.
2. **Hash algorithm:** SHA-256 — produces 64-character hex digest.
3. **Hash domain prefix** (where applicable): `HELEN_CUM_V1::` for ledger cumulative hashes.

This rule applies to: artifact hashes, bundle hashes, theta hashes, schema hashes, ledger payload hashes, and verdict hashes.

---

## §6 Schema Dialect

All JSON Schemas in this architecture use:

```
"$schema": "https://json-schema.org/draft/2020-12/schema"
```

No other schema dialect is valid for new schemas in this project.

---

## §7 Governance Invariants (Summary)

The following invariants are non-negotiable. Full enforcement rules: see `GOVERNANCE_LAW_V1.md`.

| ID | Invariant |
|---|---|
| G-1 | No receipt → no claim. Unverified outputs are drafts only. |
| G-2 | No state mutation without a gate + receipt. |
| G-3 | HELEN cannot self-authorize. She can only make shipping undeniable. |
| G-4 | Simulation output (CONQUEST LAND) is evidence. It is never authority. |
| G-5 | The ledger is append-only. No rewriting. No deletion. |
| G-6 | Canyon law: same E_adm → same verdict. Narrative cannot alter sovereign output. |
| G-7 | Dialogue laundering is forbidden. `dialog.ndjson` may never be cited as SHIP authority. |

---

## §8 Emergence (Summary)

The simulation runs 4 minimal rules:

1. **Reputation dynamics** — reputation tracks task success; high-reputation agents attract collaborators.
2. **Resource scarcity** — shared resource pool depletes under load; regenerates slowly.
3. **Memory reuse** — agents track partner history; prefer demonstrated collaborators.
4. **Coordination cost** — coalition cost scales as `|S|²`; larger coalitions incur superlinear overhead.

These 4 rules are sufficient to produce: specialization, clustering, Houses, Egregors, and triadic governance equilibrium. Full model: see `EMERGENCE_MODEL_V1.md`.

---

## §9 Stack Map

```
YOU (Human Authority)
        │
        ▼
CONQUEST LAND (L1)
  4-rule simulation → EvidenceBundle (Tier A)
        │
        ▼
HELEN  (L2, non-sovereign)
  Sensemaking + HAL audit → IssueList + TaskList + GateReport (Tier A)
  Packages into MayorPacket (Tier B)
        │
        ▼
MAYOR  (L3, routing + arbitration)
  Gate evaluation → GateEvaluated / Verdict (Tier B)
        │
        ▼
KERNEL (L3, sovereign ledger)
  Receipt chain → HELEN_CUM_V1 hash chain
        │
        ▼
IMMUTABLE TRUTH
```

---

## §10 Final Law

> Simulation proves. Interpretation proposes. Judgment decides. The ledger remembers. Only receipted, reducer-valid artifacts cross from evidence into truth.

---

**Frozen:** 2026-03-07
**Next freeze version:** CANONICAL_BLUEPRINT_V2 (when any layer contract changes)
