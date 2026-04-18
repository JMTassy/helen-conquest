"""
conquest/resource_flow/resource_kinds.py — Frozen resource kind vocabulary.

RESOURCE_FLOW_V1 — Constitutional Freeze (RESOURCE_FLOW_LAW_V1.md)

Three canonical resource kinds:
    ESSENCE  — agricultural output  (FARM extractor)
    MATTER   — mineral output       (MINE extractor)
    VITALITY — water / movement     (future extractor; vocabulary reserved)

Two canonical extractor kinds:
    FARM — operates on PLAIN / COAST
    MINE — operates on HILL / MOUNTAIN

Six lot status kinds (LOT_STATUS_V1):
    ACTIVE, RESERVED, IN_TRANSIT, CONSUMED, EXHAUSTED, VOID

Three receipt status kinds (RECEIPT_STATUS_V1):
    SEALED, REJECTED, VOID

Invariants:
    - All vocabulary sets are frozen (never mutated at runtime).
    - EXTRACTOR_TERRAIN_V1 maps each extractor to its legal terrain set.
    - EXTRACTOR_YIELD_V1 maps (extractor, terrain) → integer lot quantity.
    - EXTRACTOR_OUTPUT_KIND maps each extractor → its output resource_kind.
    - ADJACENCY_BONUS_V1 maps (extractor, adjacency_flag) → bonus quantity.
    - No extraction on VOID, SEA, ROAD, BRIDGE, MARSH, DESERT, RIVER, LAKE, FOREST.
    - FOREST is reserved for VITALITY (Path 3); not yet active.
"""
from __future__ import annotations

# ── Resource vocabulary ──────────────────────────────────────────────────────

RESOURCE_KIND_V1: frozenset[str] = frozenset({"ESSENCE", "MATTER", "VITALITY"})

EXTRACTOR_KIND_V1: frozenset[str] = frozenset({"FARM", "MINE"})

# ── Lot and receipt status vocabularies ─────────────────────────────────────

LOT_STATUS_V1: frozenset[str] = frozenset({
    "ACTIVE",      # lot exists and is available
    "RESERVED",    # locked for pending transaction
    "IN_TRANSIT",  # being moved between hexes
    "CONSUMED",    # used by a structure or process
    "EXHAUSTED",   # fully spent, no quantity remaining
    "VOID",        # invalidated, never entered ledger
})

RECEIPT_STATUS_V1: frozenset[str] = frozenset({
    "SEALED",    # admitted to sovereign ledger, immutable
    "REJECTED",  # failed legality check, no lots minted
    "VOID",      # cancelled before sealing
})

# ── Terrain legality ─────────────────────────────────────────────────────────
# Per RESOURCE_FLOW_LAW_V1 §II:
#   FARM → { PLAIN, COAST }          (FOREST removed; reserved for VITALITY)
#   MINE → { HILL, MOUNTAIN }

EXTRACTOR_TERRAIN_V1: dict[str, frozenset[str]] = {
    "FARM": frozenset({"PLAIN", "COAST"}),
    "MINE": frozenset({"HILL", "MOUNTAIN"}),
}

# ── Output resource kind ─────────────────────────────────────────────────────

EXTRACTOR_OUTPUT_KIND: dict[str, str] = {
    "FARM": "ESSENCE",
    "MINE": "MATTER",
}

# ── Base yield per (extractor, terrain) ─────────────────────────────────────
# Per RESOURCE_FLOW_LAW_V1 §III — Yield Formula (base component only):
#
#   FARM / PLAIN    = 3  (grain heartland — primary)
#   FARM / COAST    = 2  (coastal fishing / salt marsh — secondary, +1 vs Move 11)
#   MINE / HILL     = 3  (surface ore seam — primary, +1 vs Move 11)
#   MINE / MOUNTAIN = 4  (deep vein, high risk, high yield — primary)

EXTRACTOR_YIELD_V1: dict[str, dict[str, int]] = {
    "FARM": {
        "PLAIN": 3,
        "COAST": 2,
    },
    "MINE": {
        "HILL":     3,
        "MOUNTAIN": 4,
    },
}

# ── Adjacency bonuses ────────────────────────────────────────────────────────
# Per RESOURCE_FLOW_LAW_V1 §IV:
#   (FARM, river_adjacent=True) → +1 ESSENCE
#   All other combinations      → +0
#
# Keyed as (extractor_kind, adjacency_flag_name) → bonus quantity.

ADJACENCY_BONUS_V1: dict[tuple[str, str], int] = {
    ("FARM", "river_adjacent"): 1,
}
