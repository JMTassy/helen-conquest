# RESOURCE_FLOW_LAW_V1 — Constitutional Freeze

**Status:** FROZEN
**Inscription:** RESOURCE_FLOW_V1
**Path:** conquest/resource_flow/
**Freeze Date:** 2026-03-10

---

## Preamble

This document freezes the resource extraction law for CONQUESTLAND.
No pathing, decay, or maintenance logic may be defined until this law is sealed.
The two invariants below are constitutional: any receipt or lot that violates them
is void by definition and must never enter the sovereign ledger.

---

## I. Frozen Vocabulary

### Resource Kinds
```
RESOURCE_KIND_V1 = { ESSENCE, MATTER, VITALITY }
  ESSENCE  — agricultural output  (FARM extractor)
  MATTER   — mineral output       (MINE extractor)
  VITALITY — reserved for water/movement (Path 3)
```

### Extractor Kinds
```
EXTRACTOR_KIND_V1 = { FARM, MINE }
```

### Lot Status
```
LOT_STATUS_V1 = { ACTIVE, RESERVED, IN_TRANSIT, CONSUMED, EXHAUSTED, VOID }
  ACTIVE    — lot exists and is available
  RESERVED  — locked for pending transaction
  IN_TRANSIT — being moved between hexes
  CONSUMED  — used by a structure or process
  EXHAUSTED — fully spent, no quantity remaining
  VOID      — invalidated, never entered ledger
```

### Receipt Status
```
RECEIPT_STATUS_V1 = { SEALED, REJECTED, VOID }
  SEALED   — admitted to sovereign ledger, immutable
  REJECTED — failed legality check, no lots minted
  VOID     — cancelled before sealing
```

---

## II. Terrain Compatibility Law

Each extractor is legal only on its declared terrain set.
Any extraction attempt on an incompatible terrain MUST raise ExtractionError
before any lot is minted. No lot may exist without a SEALED receipt.

```
EXTRACTOR_TERRAIN_V1:
  FARM → { PLAIN, COAST }
  MINE → { HILL, MOUNTAIN }

Illegal (raise ExtractionError):
  FARM on FOREST, HILL, MOUNTAIN, VOID, SEA, ROAD, BRIDGE,
        MARSH, DESERT, RIVER, LAKE, or any unlisted terrain
  MINE on PLAIN, COAST, FOREST, VOID, SEA, ROAD, BRIDGE,
        MARSH, DESERT, RIVER, LAKE, or any unlisted terrain
```

---

## III. Yield Formula — Frozen

```
Y(h, e, t) = Y0(e, τ(h)) + B_adj(h, e) + B_policy(e, t)

Where:
  h            = hex cell
  e            = extractor kind ∈ EXTRACTOR_KIND_V1
  t            = game tick
  τ(h)         = terrain_kind of hex h
  Y0(e, τ)     = base yield from EXTRACTOR_YIELD_V1[e][τ]
  B_adj(h, e)  = adjacency bonus (see §IV)
  B_policy     = 0 (MVP; reserved for future governance)

EXTRACTOR_YIELD_V1 (base yield):
  FARM / PLAIN    = 3
  FARM / COAST    = 2
  MINE / HILL     = 3
  MINE / MOUNTAIN = 4
```

---

## IV. Adjacency Bonus — Frozen

```
ADJACENCY_BONUS_V1:
  (FARM, river_adjacent=True)  → +1 ESSENCE lot

All other (extractor, adjacency) combinations → +0

MVP: coast_adjacent has no bonus (reserved for future sea-lane law).
```

Adjacency facts are frozen into the receipt at extraction time.
They cannot be altered post-sealing.

---

## V. Constitutional Invariants

### I-1: No Lot Without Receipt

> Every ResourceLotV1 that enters the sovereign ledger MUST reference
> exactly one ExtractionReceiptV1 whose `status == "SEALED"`.
> A lot with a missing, REJECTED, or VOID `source_receipt_id` is void
> and MUST NOT be admitted.

**Formal statement:**
```
∀ lot ∈ Ledger:
  ∃! receipt ∈ Ledger such that
    receipt.receipt_id == lot.source_receipt_id
    ∧ receipt.status == "SEALED"
```

### I-2: Quantity Conservation

> The total quantity of lots minted by a SEALED receipt MUST equal
> the `quantity` field of that receipt.
> For MVP: exactly one lot is minted per receipt,
> and that lot's quantity equals the receipt's total_yield.

**Formal statement (MVP):**
```
∀ receipt ∈ Ledger with receipt.status == "SEALED":
  len(receipt.output_token_ids) == 1
  ∧ receipt.lots[0].quantity == receipt.quantity
  ∧ receipt.quantity == receipt.yield_breakdown["total_yield"]
```

---

## VI. Receipt Validity Rule

A receipt is valid (SEALED) if and only if all legality checks pass:

```python
legality = {
    "terrain_compatible": terrain_kind in EXTRACTOR_TERRAIN_V1[extractor_kind],
    "control_compatible": True,   # MVP: always True (no control check yet)
    "extractor_present":  True,   # MVP: always True (no structure check yet)
}

receipt.status = "SEALED" iff all(legality.values()) == True
                 "REJECTED" otherwise
```

---

## VII. Receipt Identifier — Canonical Form

```
receipt_id = "EX-" + SHA256(canonical_json({
    "extractor_kind":  extractor_kind,
    "hex_id":          hex_id,
    "house_id":        house_id,
    "river_adjacent":  river_adjacent,
    "terrain_kind":    terrain_kind,
    "tick":            tick,
}))[: 24]

canonical_json: sort_keys=True, separators=(",", ":"), ensure_ascii=False
```

Including adjacency in the hash ensures that a FARM receipt on a river-adjacent
hex is distinguishable from the same hex without river adjacency.

---

## VIII. Lot Identifier — Canonical Form

```
lot_id = "LOT-" + SHA256(f"{source_receipt_id}:{index:06d}")[: 16]

MVP: index is always 0 (one lot per receipt).
```

---

## IX. Immutability Guarantee

Once a receipt is SEALED and admitted to the sovereign ledger:
- No field may be modified.
- No lot minted from it may be re-minted.
- The receipt_id and all lot_ids are permanent.

This is enforced by `@dataclass(frozen=True)` on both `ExtractionReceiptV1`
and `ResourceLotV1`, and by the sovereign ledger's append-only policy.

---

## X. What This Law Does NOT Govern (Reserved)

The following are explicitly deferred to future inscription paths:

- FOREST extraction (Path 3: VITALITY / water / movement)
- Pathing and transit receipts (LOGISTICS_RECEIPT_V1)
- Structure decay and maintenance (MAINTENANCE_RECEIPT_V1)
- Policy bonuses (B_policy ≠ 0)
- Coast adjacency bonus
- Control checks (who may extract from which hex)
- Structure presence checks (extractor_present)
- Multi-lot receipts (quantity > 1 lot per receipt)

---

*This document is the sole canonical source of truth for RESOURCE_FLOW_V1.*
*No implementation detail may contradict it.*
*Amendment requires a new inscription path, not an edit to this file.*
