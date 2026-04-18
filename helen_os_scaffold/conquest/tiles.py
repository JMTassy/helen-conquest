"""
conquest/tiles.py — CONQUEST_TILES_V0_1 registry loader.

Loads and exposes the canonical tile registry.
No generation logic here — pure data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent

_TILES: dict[str, Any] = json.loads((_HERE / "conquest_tiles.json").read_text())

# Terrain
TERRAIN_REGISTRY: dict[str, Any] = _TILES["terrain_registry"]
VALID_TERRAINS: list[str]         = list(TERRAIN_REGISTRY.keys())
ALL_TERRAINS: set[str]            = set(VALID_TERRAINS)

# Structures
STRUCTURE_REGISTRY: dict[str, Any] = _TILES["structure_registry"]
VALID_STRUCTURES: list[str]         = list(STRUCTURE_REGISTRY.keys())

# Overlays
OVERLAY_REGISTRY: dict[str, Any]   = _TILES["overlay_registry"]
VALID_OVERLAYS: list[str]          = list(OVERLAY_REGISTRY.keys())

# Receipt-required overlays — CLAIMED, FORTIFIED, SEALED, etc.
RECEIPT_REQUIRED_OVERLAYS: frozenset[str] = frozenset(
    name for name, spec in OVERLAY_REGISTRY.items()
    if spec.get("requires_receipt", False)
)

# Sovereign overlays (NO_RECEIPT_NO_* invariants)
SOVEREIGN_OVERLAYS: frozenset[str] = frozenset({
    "CLAIMED", "FORTIFIED", "SEALED", "RESOURCE_LOCKED", "DUEL_PENDING"
})

# Resources
VALID_RESOURCES: frozenset[str] = frozenset(_TILES["resources"])

# Regions
REGIONS: list[str]             = _TILES["regions"]
REGION_BIAS: dict[str, Any]    = _TILES["region_bias"]

# Generation pipeline
GENERATION_ORDER: list[str]    = _TILES["generation_order"]
HARD_INVARIANTS: list[str]     = _TILES["hard_invariants"]
REPAIR_PROTOCOL: list[str]     = _TILES["repair_protocol"]

# Governing law (frozen)
GOVERNING_LAW: str = _TILES["governing_law"]
