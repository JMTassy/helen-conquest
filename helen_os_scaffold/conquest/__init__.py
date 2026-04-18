"""
conquest/ — CONQUESTLAND_WORLDGEN_V0_1

Deterministic world generator for CONQUESTLAND.

Governing law: Terrain is solved, structures are placed, sovereignty is receipted.

Module topology (import order = stage order):
  tiles.py            — CONQUEST_TILES_V0_1 registry loader (no generation logic)
  adjacency.py        — terrain legality matrix + special constraints
  hex_grid.py         — axial coordinate system + neighbor lookup
  terrain_wfc.py      — Layer A: terrain substrate (geology + hydrology)
  river_carving.py    — Layer A: river/lake continuity
  structure_placement.py — Layer B: habitation and strongholds
  road_solver.py      — Layer B: infrastructure pass (roads and bridges)
  region_partition.py — geography metadata (6 regions)
  resource_assignment.py — resource profiles from terrain + structure grants
  ledger_init.py      — Layer C: UNCLAIMED / CLAIMABLE only (no receipted overlays)
  world_validator.py  — hard invariant enforcement
  world_receipt.py    — WORLD_GENERATION_RECEIPT_V1

Boundary invariants:
  terrain_wfc.py  knows nothing about claims, Houses, duels, or Senate.
  ledger_init.py  knows nothing about WFC contradiction recovery.
"""
from conquest.conquest_world_generator import (
    generate_world,
    world_generation_receipt,
    WorldV1,
    WorldGenerationReceiptV1,
    HexTile,
    TERRAIN_REGISTRY,
    STRUCTURE_REGISTRY,
)

__all__ = [
    "generate_world",
    "world_generation_receipt",
    "WorldV1",
    "WorldGenerationReceiptV1",
    "HexTile",
    "TERRAIN_REGISTRY",
    "STRUCTURE_REGISTRY",
]
