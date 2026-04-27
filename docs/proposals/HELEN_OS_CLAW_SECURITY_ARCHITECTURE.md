# HELEN OS — CLAW Security Architecture

**Status:** PROPOSAL  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** PROPOSAL  
**Implementation status:** NOT_IMPLEMENTED  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  

> This document is a security architecture proposal.  
> It does not amend the kernel, the ledger, the schema registry, or any sovereign path.  
> It does not constitute a CLOSURE_RECEIPT or TRANCHE_SUB_RECEIPT.  
> It does not merge into or contaminate the interaction grammar or UX proposals.  
> Promotion to canon requires a separate KERNEL-gated dispatch.

---

## 1. Executive summary

HELEN governs intention and consequence.  
CLAW performs bounded side effects.  
SELinux confines the host execution surface.  
The ledger records consequence.  
The reducer reconstructs admitted reality from receipts.

These are five distinct layers. They do not collapse into each other.

| Layer | Governs | Emits |
|---|---|---|
| HELEN OS | Intention, proposal, confirmation | Receipts, proposals, gate verdicts |
| CLAW | Bounded execution of confirmed actions | Execution receipts |
| SELinux | Host confinement policy | Access decisions (kernel-level) |
| Ledger | Consequence record | Hash-chained NDJSON entries |
| Reducer | Admitted state reconstruction | Folded state from receipts |

**Product principle:** the user sees consequence (receipt), not mechanism (sandbox).  
Focus Mode exposes the loop. Witness Mode exposes the proof. Neither exposes CLAW or SELinux.

---

## 2. Layer model

```
┌─────────────────────────────────────────────────────────┐
│  FOCUS MODE                                             │
│  intent → proposal → confirmation → receipt → calm     │
├─────────────────────────────────────────────────────────┤
│  WITNESS MODE                                           │
│  gate verdicts · ledger tail · constitution · reducer   │
├─────────────────────────────────────────────────────────┤
│  HELEN KERNEL                                           │
│  oracle_town/kernel/  ·  gates A/B/C  ·  MAYOR         │
│  Sovereign: emits SHIP/NO_SHIP/BLOCK/PASS only          │
├─────────────────────────────────────────────────────────┤
│  CLAW (Confined Ledger-Authorised Workload)             │
│  Executes receipt-bearing, gate-authorised actions      │
│  Not a product surface — execution boundary only        │
├─────────────────────────────────────────────────────────┤
│  SELinux                                                │
│  Mandatory access control on the host                   │
│  Policy enforced at kernel level, independent of HELEN  │
├─────────────────────────────────────────────────────────┤
│  Host OS / hardware                                     │
└─────────────────────────────────────────────────────────┘
```

Layer separation is strict. Each layer communicates only with the layer immediately adjacent.  
HELEN does not call SELinux directly.  
CLAW does not bypass the ledger.  
SELinux does not know about HELEN semantics.

---

## 3. Core contracts

### 3.1 HELEN → CLAW contract

- HELEN issues a **receipt-bearing execution authorisation** for confirmed actions only.
- CLAW executes **only** from a valid, gate-authorised receipt.
- CLAW does not execute without a receipt. No receipt = no execution.
- CLAW appends an **execution receipt** to the ledger upon completion or failure.
- CLAW does not expose its internals to Focus Mode or Witness Mode.

```
confirmation → helen_say.py → ledger append (EXECUTION_REQUEST_V1)
             → LEGORACLE gate → SHIP or NO_SHIP verdict
             → [SHIP] → CLAW execution receipt → ledger append (EXECUTION_ENVELOPE_V1)
             → [NO_SHIP] → BLOCK → no execution → ledger append (FAILURE_REPORT_V1)
```

### 3.2 CLAW → SELinux contract

- CLAW operates within SELinux-defined domain confinement.
- SELinux enforces access decisions at the kernel level, independently of HELEN semantics.
- A valid HELEN receipt does not override SELinux policy. SELinux is a co-equal constraint.
- SELinux policy is not stored in or managed by the HELEN ledger.
- SELinux policy changes require host-level administrator action, not HELEN gate verdicts.

### 3.3 Ledger contract

- All execution events produce a ledger entry (EXECUTION_ENVELOPE_V1 or FAILURE_REPORT_V1).
- The ledger is append-only. No execution event can modify a prior entry.
- The cum_hash chain is maintained across all entries including execution receipts.
- The reducer folds only admitted entries. Rejected and blocked entries are recorded but not folded.

### 3.4 Reducer contract

- The reducer reconstructs admitted state from the ledger only.
- The reducer does not infer state from anything outside receipts.
- The reducer does not "remember" — it reconstructs.
- Reducer output is deterministic given the same receipt chain.
- Reducer output is non-sovereign — it proposes a state reconstruction; MAYOR validates.

---

## 4. Hard boundaries

These are architectural invariants, not guidelines.

| Boundary | Rule |
|---|---|
| Focus Mode | Must not expose execution internals by default |
| Witness Mode | May inspect execution proofs (receipts, verdicts) — not CLAW state or SELinux policy |
| CLAW | Must not execute without a receipt-bearing gate authorisation |
| CLAW | Must not bypass receipt discipline under any execution path |
| SELinux | Must not be represented as product UX or surfaced in Focus/Witness Mode |
| Reducer | Must not infer state from anything outside receipts |
| Ledger | Must not be written directly by any process other than the admitted path (helen_say.py → ndjson_writer.py) |
| HELEN kernel | Must not claim authority over host-level confinement |
| CLAW | Must not claim authority over HELEN receipt validity |

---

## 5. Execution flow

### 5.1 Normal path (action confirmed, gate passes, execution succeeds)

```
1.  Operator confirms action (Focus Mode confirmation beat)
2.  helen_say.py emits EXECUTION_REQUEST_V1 → ledger append (seq N)
3.  LEGORACLE gate evaluates: SHIP
4.  CLAW receives authorisation
5.  SELinux validates domain access
6.  CLAW executes action
7.  CLAW emits EXECUTION_ENVELOPE_V1 → ledger append (seq N+1)
8.  Reducer folds N+1 into admitted state
9.  Focus Mode shows: "◆ Receipt appended · seq=N+1"
```

### 5.2 Gate block path (gate issues NO_SHIP)

```
1.  Operator confirms action
2.  helen_say.py emits EXECUTION_REQUEST_V1 → ledger append (seq N)
3.  LEGORACLE gate evaluates: NO_SHIP
4.  CLAW does not execute
5.  FAILURE_REPORT_V1 → ledger append (seq N+1)
6.  Reducer records N+1 as REJECTED
7.  Focus Mode shows: "◆ Action blocked · Gate did not authorise"
8.  Witness Mode shows: full gate verdict with reason code
```

### 5.3 SELinux block path (gate passes, SELinux denies access)

```
1.  Operator confirms action
2.  Gate: SHIP
3.  CLAW receives authorisation
4.  SELinux: access denied
5.  CLAW catches the denial and emits FAILURE_REPORT_V1 → ledger append
6.  Reducer records as BLOCKED (execution boundary, not gate boundary)
7.  Focus Mode: "◆ Action could not complete · logged"
8.  Witness Mode: receipt shows BLOCKED with class SELINUX_DENY
```

---

## 6. Threat model

| Threat | Class | Mitigation |
|---|---|---|
| **Role bleed** | Architecture | Hard mode separation — Focus/Witness/CLAW/SELinux are distinct namespaces. CLAW internals never surface in product modes. |
| **Silent mutation** | Ledger | Append-only cum_hash chain. Any modification breaks the chain and is detected by K8 gate (μ_NDLEDGER). |
| **Unauthorised execution** | Receipt discipline | CLAW requires a gate-authorised receipt. No receipt = no execution path. |
| **Sandbox escape** | SELinux | Co-equal enforcement at host kernel level. A valid HELEN receipt does not override SELinux. |
| **Receipt/ledger tampering** | Cryptography | sha256(canon(payload)) links every entry. Replay gate (LEGORACLE CI) detects divergence. |
| **Replay divergence** | Determinism | K8 gate (μ_NDWRAP, μ_NDARTIFACT) enforces deterministic output. Same input → identical output hash. |
| **Privilege escalation via intent** | Gate | LEGORACLE obligation check: all required fields must be attested before SHIP is issued. |
| **Receipt spoofing** | Chain integrity | cum_hash = sha256(prev_cum_hash + payload_hash). Cannot be constructed without the full prior chain. |

---

## 7. Non-goals

This proposal does not:

- Implement CLAW (execution boundary not yet built)
- Implement SELinux policy for HELEN (host-level, not in this proposal)
- Merge CLAW or SELinux details into the interaction grammar or UX proposals
- Promote to canon (requires KERNEL-gated dispatch)
- Replace or modify `helen_os/governance/`, `oracle_town/kernel/`, or `town/ledger_v1.ndjson`
- Describe the AMP terminal module (separate proposal)
- Describe sandboxing of individual skill executions (out of scope for this document)

---

## 8. Relation to other proposals

| Document | Relation |
|---|---|
| `HELEN_OS_V2_USER_CENTRIC_UX.md` | Upstream — defines Focus/Witness mode surfaces. This doc must not contaminate those surfaces. |
| `HELEN_OS_V2_INTERACTION_GRAMMAR.md` | Upstream — defines vocabulary. This doc provides the execution layer that the grammar deliberately hides from product modes. |
| `AUTORESEARCH_TRANCHE_E13_E18.json` | Parallel — AUTORESEARCH operating on non-sovereign layers. CLAW is an execution boundary not yet in scope for autoresearch. |
| `DOCTRINE_ADMISSION_PROTOCOL_V1` | Downstream — when CLAW is built, it will require doctrine admission before promotion. |

---

## 9. Vocabulary lock

| Term | Canonical meaning |
|---|---|
| **CLAW** | Confined Ledger-Authorised Workload — the execution boundary layer |
| **SELinux** | Mandatory access control on the host — co-equal with but independent of HELEN |
| **Ledger** | Append-only hash-chained memory of consequence |
| **Reducer** | Reconstructs admitted state from receipts — does not remember, does not infer |
| **Focus Mode** | Experience — the product loop, not the machinery |
| **Witness Mode** | Proof — receipts and verdicts, not execution internals |
| **Receipt** | The ledger's record of a confirmed, executed action |
| **Gate** | LEGORACLE — proposes SHIP or NO_SHIP; MAYOR authorises |

---

## Closing statement

HELEN governs the loop between intention and consequence.  
CLAW performs the side effect at the boundary.  
SELinux confines the host.  
The ledger records what happened.  
The reducer knows only what the ledger admits.

These five things are the operating system.  
They are not five features.  
They are five distinct planes of authority — and they must never collapse into each other.
