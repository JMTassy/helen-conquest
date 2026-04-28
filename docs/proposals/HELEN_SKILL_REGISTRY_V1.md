# HELEN_SKILL_REGISTRY_V1

**Status:** PROPOSAL · NON_SOVEREIGN · NO_SHIP · NOT_IMPLEMENTED
**Lifecycle:** PROPOSAL_UPDATE
**Implementation scope:** SKILL_REGISTRY_DOC_UPDATE_ONLY
**Date:** 2026-04-27

---

## Source

Apple Notes / TEMPLE — RAW_SOURCE capture, routed via the admissible bridge
(`tools/helen_say.py`) as a `TEMPLE_TRANSMUTATION_REQUEST_V1` candidate.

- Receipt: `R-20260427-0002`
- Gate: `GATE_FETCH_PASS`
- HAL verdict: `PASS` · certificates: `[KERNEL_ACCEPT]`
- `ledger_cum_hash`: `d71f301148860a63dda05b49afc8a4ebc89cde2704179a70b827848035234570`
- `kernel_hash`: `37a3c181929a43c706716dbb48688ee2909e5a61`
- `run_id`: `RUN_20260427`

This proposal records the bridge contract that the routed packet describes.
It does not promote that packet to canon. MAYOR review is still pending.

---

## Bridge Contract — `TEMPLE_TRANSMUTATION_REQUEST_V1`

### Classification

- `authority: NON_SOVEREIGN`
- `canon: NO_SHIP`
- `lifecycle: PROPOSAL`
- `implementation_status: NOT_IMPLEMENTED`

### Preserved canon-candidate (not yet canon)

> The Temple may transmute exploration into a packet,
> but only the Reducer may admit reality.

### Core rules

- Temple may explore.
- Temple may package.
- Temple may route to Mayor.
- Temple may not decide.

### Bridge path

```
TEMPLE_EXPLORATION_V1
    │
    ▼
temple_bridge_v1.py
    │
    ▼
TEMPLE_TRANSMUTATION_REQUEST_V1
    │
    ▼
Mayor review
    │
    ▼
Reducer decision
    │
    ▼
Ledger memory
```

### Rules to preserve

- `authority: NONE`
- `bridge_status: PENDING_MAYOR_REVIEW`
- `requires_second_witness: true` when risk / tension is present

---

## Skill Registry Entry

### `build_transmutation_request`

- **Layer:** `L1_COGNITIVE`
- **Purpose:** Transform `TEMPLE_EXPLORATION_V1` into `TEMPLE_TRANSMUTATION_REQUEST_V1`.
- **Authority class:** `PROPOSAL_ONLY`
- **Memory access class:** `SESSION_CONTEXT_READ`
- **Governed state access:** `NONE`
- **Receipt required:** `true` when routed beyond Temple
- **Reducer required:** `true` for admission

#### Allowed inputs

- `TEMPLE_EXPLORATION_V1`
- `doctrine_hash`
- `law_surface_hash`
- `source_exploration_hash`
- `proposal_kind`
- `risk` / `tension` markers

#### Allowed outputs

- `TEMPLE_TRANSMUTATION_REQUEST_V1`

#### Invalid if

- `authority` is not `NONE`
- `bridge_status` is not `PENDING_MAYOR_REVIEW`
- routes directly to ledger
- bypasses Mayor
- bypasses Reducer
- `requires_second_witness` is `false` while risk / tension is present

---

## Companion L1 Cognitive skills (referenced, not specified here)

- `temple_generate_artifact`
- `prepare_review_packet`
- `build_receipt`

These are named in the source capture but their full specifications are out of
scope for this proposal. Each remains `PROPOSAL_ONLY · NOT_IMPLEMENTED`.

---

## WULmoji Output Discipline

**Rule:** All non-sovereign HELEN skill outputs should include WULmoji color-grading by default.

### Constraints

- max 1 WULmoji per line
- WULmoji is metadata only
- WULmoji never carries a claim alone
- WULmoji never substitutes for receipt
- WULmoji never appears as sovereign authority
- `NO_RECEIPT = NO_CLAIM` applies to WULmoji
- Disable WULmoji on governed paths unless explicitly allowed:
  - reducer
  - ledger
  - MAYOR ruling
  - governance / canon files
  - schemas
  - kernel code

### Default mapping

| Symbol | Meaning |
|---|---|
| 🔴 | identity / canon / invariant |
| 🟠 | emotion / acting / intensity |
| 🟡 | cost / efficiency / budget |
| 🟢 | validation / pass / success |
| 🔵 | structure / equations / system |
| 🟣 | emergent / lateral / unusual |
| ⚪ | next step / instruction / clarity |
| ⚠️ | warning / drift / failure |
| 🎬 | direction / cinema / shot logic |
| 📦 | artifact / deliverable |
| 📊 | metrics / scoring |
| 🔁 | loop / iteration / retry |
| ✍️ | operator judgment / rating |
| 🚀 | execution / launch / run |

---

## Constraints on this proposal

- Do not implement.
- Do not mutate governed state.
- Do not promote to canon.
- Do not commit.
- Do not push.

---

## Seal

> The Temple may speak in fire.
> The Mayor tests the vessel.
> The Reducer admits reality.
> The Ledger remembers only what passed.

---

## Final receipt

```
authority:             NON_SOVEREIGN
canon:                 NO_SHIP
lifecycle:             PROPOSAL_UPDATE
implementation_scope:  WULMOJI_DISCIPLINE_DOC_UPDATE_ONLY
commit_status:         NO_COMMIT
push_status:           NO_PUSH
next_verb:             review WULmoji discipline
```
