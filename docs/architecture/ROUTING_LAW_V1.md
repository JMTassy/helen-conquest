# ROUTING_LAW_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07

---

## The Law

**Emergence is evidence, not authority.**

Simulation results — Houses, Egregors, regime classifications, metrics — are observation records. They describe what a population of agents did under 4 minimal rules. They do not decide anything. They do not authorize anything. They are inputs to interpretation, not outputs of judgment.

---

## Firewall Sentence

> Only typed, receipted, reducer-valid artifacts may cross from non-sovereign layers into sovereign judgment.

This sentence is the single most important constraint in the architecture. Every routing rule below is a consequence of it.

---

## Default Routing Path

```
CONQUEST LAND  →  HELEN  →  MAYOR  →  KERNEL
    L1              L2        L3a       L3b
```

Each `→` represents a typed artifact crossing. The artifact must:
1. Match its schema (validated against `schemas/*_v1.schema.json`, Draft 2020-12)
2. Carry a correct `bundle_hash` (RFC 8785 + SHA-256)
3. Not contain forbidden tokens in any field if originating from L1 or L2

---

## Routing Table

| Source | Destination | Artifact | Gate Required? |
|---|---|---|---|
| CONQUEST LAND (L1) | HELEN (L2) | `EvidenceBundle` | No gate — but HELEN marks it CORE |
| HELEN (L2) | HELEN (L2) internal | `IssueList`, `TaskList` | No gate — internal audit loop |
| HELEN (L2) | MAYOR (L3a) | `MayorPacket` | Yes — `GateReport` must be attached |
| MAYOR (L3a) | KERNEL (L3b) | `GateEvaluated` | Yes — all gates in GateReport must complete |
| KERNEL (L3b) | HELEN (L2) | Receipt + updated ledger tip | Automatic — GovernanceVM emits receipt |
| HELEN (L2) | HELEN (L2) memory | `MemoryKernel` updates | After receipt — never before |
| Any | Any | Forbidden tokens (`SHIP`, `SEALED`, `FINAL`, `APPROVED`) | BLOCK — authority bleed scan |

---

## Escalation Path (Exceptions)

The default path can be escalated in the following cases only:

### E-1: HAL BLOCK
**Trigger:** `HALVerdict.verdict = BLOCK`
**Routing:** `HELEN → HAL → (rewrite required) → HELEN`
**Rule:** A blocked proposal must be rewritten from scratch. HAL issues a minimal fix list. HELEN rewrites. HAL audits again. This loop continues until PASS or WARN, or until the session terminates with ABORT.

### E-2: MAYOR DEFER
**Trigger:** `GateEvaluated.verdict = DEFER`
**Routing:** `MAYOR → HELEN → (gather missing evidence) → MAYOR`
**Rule:** DEFER means insufficient evidence for a verdict. HELEN must return with a new `EvidenceBundle` that fills the gap. The original `MayorPacket` is closed; a new one is opened.

### E-3: Kernel Replay Failure
**Trigger:** `GovernanceVM` detects ledger integrity failure on init
**Routing:** `KERNEL → ABORT`
**Rule:** If the ledger hash chain fails validation, the system enters fail-closed mode. No new entries. No new proposals. Requires manual recovery (git checkout + re-validation).

### E-4: Cross-Town Federation
**Trigger:** `CrossReceiptV1` arrives from a foreign Town
**Routing:** `Foreign Town → Allowlist Gate → KERNEL (as E_adm candidate)`
**Rule:** Cross-receipts are not automatically admitted. They must pass `validate_cross_receipt_allowlist()`. Only allowlisted `source_town_id` values may contribute to E_adm.

---

## What May Never Be Routed Directly

The following are unconditional prohibitions. No exception exists.

| Forbidden Route | Reason |
|---|---|
| CONQUEST LAND → KERNEL (skipping HELEN + MAYOR) | Simulation output is never authority |
| `dialog.ndjson` → KERNEL (as SHIP authority) | Dialogue laundering — forbidden |
| HELEN output with forbidden tokens → MAYOR | Authority bleed — blocked before submission |
| Any artifact without a `bundle_hash` → MAYOR | Schema validation will reject it |
| Any artifact using a non-canonical JSON serialization → KERNEL | Hash mismatch — will fail chain validation |
| A `GateEvaluated` with `verdict=PASS` but failing gates | Contradiction — GovernanceVM will reject |

---

## Routing Receipt

Every time an artifact crosses a layer boundary, a routing receipt is generated:

```json
{
  "routing_receipt_id": "RR-<sha256[:8]>",
  "from_layer": "HELEN",
  "to_layer": "MAYOR",
  "artifact_type": "MayorPacket",
  "artifact_hash": "<sha256-hex>",
  "timestamp": "<iso8601>",
  "routing_receipt_hash": "<sha256 of this object>"
}
```

The `routing_receipt_hash` is included in the `MayorPacket.routing_receipt_hash` field, creating an audit trail of artifact movement.

---

## Proof Pack (Required for Regime Claims)

Any claim that the system reached a specific emergence regime (e.g., "POLITICS with 3 egregors at tick 80") requires a full proof pack:

```
proof_pack/
  evidence_bundle_v1.json        # EvidenceBundle (schema-validated)
  gate_report_v1.json            # GateReport (all gates complete)
  theta_v1.json                  # config/theta_v1.json (hash-pinned)
  schema_manifest_v1.json        # config/schema_manifest_v1.json
  routing_receipt.json           # routing receipt for this bundle
  simulation_seed.txt            # seed used for this run
```

Without a complete proof pack, a regime claim is a narrative claim only.

---

## Key Routings for HELEN OS Operations

### Standard CONQUEST run (evidence only):
```
CONQUEST.run(seed, theta_v1) → EvidenceBundle → HELEN.interpret() → IssueList + TaskList
```
No gate required. All outputs are CORE-mode.

### Full governance cycle (SHIP path):
```
CONQUEST.run() → EvidenceBundle →
HELEN.audit(bundle) → IssueList + GateReport →
HELEN.plan(bundle) → TaskList →
HELEN.package() → MayorPacket →
MAYOR.evaluate(packet) → GateEvaluated →
KERNEL.append(verdict) → Receipt
```
Each step produces a typed artifact. Each artifact carries its own hash. The kernel receipt closes the cycle.

---

**Frozen:** 2026-03-07
