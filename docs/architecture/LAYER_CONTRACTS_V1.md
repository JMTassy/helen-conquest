# LAYER_CONTRACTS_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07

Precise input/output contracts for each layer in the HELEN OS / CONQUEST LAND architecture. Every layer has an invariant that cannot be violated.

---

## Contract Format

Each contract specifies:
- **Receives** — what inputs the layer accepts
- **Produces** — what outputs the layer generates, with schema
- **May not** — actions permanently forbidden for this layer
- **Gate requirement** — what receipts are required before output is consumed by the next layer

---

## L1: CONQUEST LAND

### Role
Exploration laboratory. Generates emergence evidence from multi-agent simulation. Never authoritative.

### Receives
| Input | Format | Required? |
|---|---|---|
| Seed | Integer | Yes — for determinism |
| n_ticks | Integer | Yes |
| theta_v1 config | `config/theta_v1.json` | Yes — pinned parameters |
| n_agents | Integer | Optional (default: 12) |

### Produces
| Output | Schema | Tier |
|---|---|---|
| `EvidenceBundle` | `schemas/evidence_bundle_v1.schema.json` | A (simulation) |
| `artifacts/emergence_metrics.json` | Unschema'd time series | Internal |
| `artifacts/emergence_summary.json` | Unschema'd summary | Internal |
| Ledger (simulation-internal) | `conquest_tick_v1.schema.json` | Internal |

### May Not
- Produce outputs marked `SHIP`, `SEALED`, `APPROVED`, or `FINAL`
- Self-promote simulation results to governance decisions
- Call `GovernanceVM` or read the sovereign ledger
- Generate receipts (simulation ticks are not governance receipts)
- Skip determinism: every run with the same seed and theta_v1 must produce the same output

### Gate Requirement
Output is consumed by HELEN with no gate — but HELEN must not treat it as authoritative until a `GateReport` passes. An `EvidenceBundle` without a corresponding `GateReport` is a draft only.

### Key Invariant
**Simulation output is always evidence. It is never authority.**

---

## L2: HELEN (Synthesis + Audit)

### Role
Non-sovereign sensemaking layer. Interprets CONQUEST LAND evidence, audits for issues, plans tasks. Packages everything for MAYOR submission. Always operates in CORE mode until HELEN OS marks SHIPPED.

### HELEN vs HELEN OS Distinction
HELEN is the cognitive agent that operates *inside* HELEN OS's constitution. HELEN proposes; HELEN OS decides. Writing "HELEN" in any output refers to this synthesis layer, never to the constitutional machine.

### Receives
| Input | Format | Required? |
|---|---|---|
| `EvidenceBundle` | `schemas/evidence_bundle_v1.schema.json` | Yes |
| Prior ledger state | HELEN OS provides on session init | Yes |
| User directives | Natural language | Yes |

### Produces
| Output | Schema | Tier |
|---|---|---|
| `IssueList` | `schemas/issue_list_v1.schema.json` | A (simulation) |
| `TaskList` | `schemas/task_list_v1.schema.json` | A (simulation) |
| `GateReport` | `schemas/gate_report_v1.schema.json` | A (simulation) |
| `MayorPacket` | `schemas/mayor_packet_v1.schema.json` | B (governance) |
| HER output blocks | `HEROutput` (two-block format) | CORE only |
| HAL verdict blocks | `HALVerdict` | Audit only |

### May Not
- Mark any output as `SHIP`, `SEALED`, `APPROVED`, or `FINAL` (forbidden tokens — blocked by `authority_bleed_scan()`)
- Self-authorize state mutations
- Skip the two-block HER/HAL format for proposals
- Treat `dialog.ndjson` as SHIP authority (dialogue laundering — forbidden)
- Submit a `MayorPacket` without a valid `GateReport` attached
- Produce a `GateEvaluated` verdict (that is MAYOR's role)

### Gate Requirement
`MayorPacket` submission requires:
1. Valid `EvidenceBundle` with `bundle_hash` verified
2. `IssueList` with `issue_list_id` matching the bundle
3. `GateReport` with all gate IDs completed (PASS or FAIL — no nulls)
4. Routing receipt hash (from prior HELEN OS interaction)

### Key Invariant
**HELEN can only make shipping undeniable. She cannot ship herself.**

---

## L3a: MAYOR (Routing + Arbitration)

### Role
The arbitration function inside HELEN OS. Receives `MayorPacket`, evaluates all gates, issues the `GateEvaluated` verdict. Mayor is a pure function: same packet → same verdict (Canyon Law).

### Receives
| Input | Format | Required? |
|---|---|---|
| `MayorPacket` | `schemas/mayor_packet_v1.schema.json` | Yes |
| Sovereign ledger state | Via GovernanceVM | Yes |
| Gate policies | `action_policy.json` | Yes |

### Produces
| Output | Schema | Tier |
|---|---|---|
| `GateEvaluated` | `schemas/gate_evaluated_v1.schema.json` | B (governance) |
| Gate receipts | `Receipt` objects | Sovereign |
| `HAL_VERDICT_RECEIPT_V1` or `BLOCK_RECEIPT_V1` | Per Channel A policy | Sovereign |

### May Not
- Modify its own gate policies (only `PatchProposalV1` + `POLICY_UPDATE_RECEIPT_V1` may do that)
- Issue a `GateEvaluated` with `verdict=PASS` if any required gate has `status=FAIL`
- Produce narrative without HAL audit
- Accept a `MayorPacket` with a missing or unverified `gate_report_ref`

### Gate Requirement
All internal gates must complete synchronously. No gate may be deferred without producing a `DEFER` verdict with a reason.

### Key Invariant
**MAYOR is a pure function. Same evidence in → same verdict out. No narrative can alter it.**

---

## L3b: KERNEL (Sovereign Ledger)

### Role
The append-only hash chain that is the ultimate source of truth. Every sovereign decision produces a ledger entry with `payload_hash` and `cum_hash`. The chain is never rewritten.

### Receives
| Input | Format | Required? |
|---|---|---|
| `GateEvaluated` with all receipts | `schemas/gate_evaluated_v1.schema.json` | Yes |
| GovernanceVM `propose()` call | Via GovernanceVM API | Yes |

### Produces
| Output | Format |
|---|---|
| Ledger entry | NDJSON with `payload_hash` + `cum_hash` |
| Receipt | `{payload_hash, cum_hash, timestamp}` |

### May Not
- Accept any entry without a valid `payload_hash`
- Rewrite or delete any ledger entry
- Accept a `GovernanceVM.propose()` call that has not passed `_check_dialogue_laundering()`
- Accept entries with duplicate `event_id` (IdempotenceManager blocks these)

### Hash Chain Rule
```
payload_hash = SHA256(RFC8785_canonical(payload))
cum_hash = SHA256(bytes.fromhex(prev_cum_hash) || bytes.fromhex(payload_hash))
Domain prefix: "HELEN_CUM_V1::"
```

### Key Invariant
**The ledger is the only truth. Every other layer's output is a proposal until the ledger accepts it.**

---

## Cross-Layer Constraints

### Tier Crossing Rule
Tier A artifacts (EvidenceBundle, IssueList, TaskList, GateReport) may be passed to MAYOR inside a MayorPacket — but they cannot directly update the sovereign ledger. Only Tier B artifacts (MayorPacket, GateEvaluated) result in ledger entries.

### Skipping Prohibition
No layer may skip a tier. `CONQUEST LAND → KERNEL` directly is forbidden. Simulation output must always pass through HELEN's sensemaking + MAYOR's gate evaluation first.

### Authority Bleed Rule
Any output containing forbidden tokens (`SHIP`, `SEALED`, `APPROVED`, `FINAL`) from L1 or L2 is automatically escalated to WARN or BLOCK by `authority_bleed_scan()`. This is enforced at the boundary between L2 and L3.

---

**Frozen:** 2026-03-07
