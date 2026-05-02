---
loop_id:          RALPH_TEMPLE_LOOP_V1
authority:        NON_SOVEREIGN
canon:            NO_SHIP
ledger_effect:    NONE
status:           OPEN
captured_on:      2026-05-02
total_epochs:     200
hal_review_cadence: 10
mayor_packet_cadence: 50
reducer_bundle_at: 200
schema_source:    docs/design/HELEN_GOLDFRAME_V1.md
---

# RALPH_TEMPLE_LOOP_V1 — Index

**NON_SOVEREIGN. NO_SHIP. PROPOSAL-ONLY TEMPLE LOOP.**

## Scope

HELEN visual / product expansion. Four workstreams. 200 epochs total.
Outputs are typed artifacts; nothing is admitted to canon without
reducer admission.

## Loop Law

> One epoch = one bounded artifact.
> No ledger append.
> No canon claim.
> No "done" unless artifact exists.
> Every 10 epochs → HAL review.
> Every 50 epochs → MAYOR packet.
> Epoch 200 → REDUCER-ready bundle.

## Workstreams

| Code | Name | Schema source | Output kind |
|---|---|---|---|
| **A** | CONQUEST CARD format | `HELEN_GOLDFRAME_V1.md` §1.2 | `CONQUEST_CARD_V1` instance |
| **B** | Interactive OS Dashboard UI | `HELEN_GOLDFRAME_V1.md` §2 | component spec / endpoint stub / template |
| **C** | Animated Terminal Sequence | `HELEN_GOLDFRAME_V1.md` §3 | `.tape` script + storyboard |
| **D** | Full System Map | `HELEN_GOLDFRAME_V1.md` §4 | gold-frame map + flow law sheet |

Workstreams interleave. Each epoch belongs to one workstream. The
allocation across 200 epochs is left to operator direction (no
automatic round-robin).

## Epoch Roster

| Epoch | Workstream | Title | File | Status |
|---|---|---|---|---|
| E001 | A | RALPH, the Receipt Goblin | `E001_RALPH_RECEIPT_GOBLIN.md` | PROPOSAL |
| E002 | _ | _ | _ | _ |
| ... | ... | ... | ... | ... |
| E010 | — | **HAL review** | (review packet, not an epoch) | _ |
| ... | ... | ... | ... | ... |
| E050 | — | **MAYOR review packet** | (proposal-stage to MAYOR) | _ |
| ... | ... | ... | ... | ... |
| E200 | — | **REDUCER-ready bundle** | (admission packet) | _ |

## Cadence Receipts

Each cadence boundary produces its own typed artifact:

- **HAL review** (every 10 epochs): a `HAL_REVIEW_REPORT_V1` listing
  pass/warn/block per epoch in the window, with explicit risk
  classification. Lives at `HAL_REVIEW_E010.md`, `HAL_REVIEW_E020.md`,
  etc.
- **MAYOR packet** (every 50 epochs): a `MAYOR_REVIEW_PACKET_V1` per
  the schema in `RALPH_LOOP_TRACE_STEP_C` §9. NOT signed by HELEN.
  Routed to MAYOR for verdict.
- **Reducer bundle** (E200): the full set of accepted artifacts
  packaged for reducer admission. Includes determinism proof,
  receipt-linkage proof, and the registry mapping.

## What This Index Does NOT Do

- Does not authorize any epoch as canonical.
- Does not commit to a specific allocation across workstreams.
- Does not bypass HAL review.
- Does not promise the loop will complete (200 epochs is a ceiling, not
  a quota).

## Open Items (carried in this loop)

- **Determinism finding** on `tools/ralph_emit_artifacts.py`:
  `FAILURE_CLUSTER_V1.generated_at_unix` puts wall-clock time in the
  hashed core. Empirically confirmed across two runs with identical
  inputs producing different `failure_cluster_ref` hashes. **Awaiting
  operator signal on Option A (drop) vs Option B (relocate to
  non-hashed metadata).** This finding is RALPH's own first shadow,
  surfaced by RALPH's own discipline — and listed in `E001`'s
  `face.shadow`.

`(NO CLAIM — TEMPLE — RALPH LOOP V1 — INDEX — NON_SOVEREIGN)`
