"""
conquest/world_validator.py — CONQUESTLAND world invariant validator.

Two validation APIs:

1. validate_world(hexes) -> ValidationReport         [EXISTING, soft, backward-compat]
   Checks structural invariants against CONQUEST_TILES_V0_1 registries.
   Returns a ValidationReport with violations (hard) and warnings (soft).

2. validate_world_constitutional(world, tiles) -> None  [PHASE C, hard-fail]
   Constitutional validator per CONQUEST_WFC_SPEC_V1.
   Takes world dict {"seed", "solver_version", "cells": [...]} and
   tiles dict {"layers": {"terrain": [...]}, "structure_rules": {...}}.
   Raises WorldValidationError on first hard violation (fail-closed).

Rules enforced by validate_world() [legacy]:
  V1  every hex has valid terrain (in terrain_registry)
  V2  every structure is legal for that hex's terrain
  V3  receipt-requiring overlays must have receipt_hash
  V4  no ownership is assigned during generation
      (owner_house_id must be null for UNCLAIMED/CLAIMABLE hexes)
  V5  river continuity: RIVER tiles must connect to water
  V6  HARBOR only on COAST
  V7  FARM only on PLAIN
  V8  no CLAIMED/FORTIFIED/SEALED/RESOURCE_LOCKED/DUEL_PENDING without receipts
  V9  generation_entropy and epistemic_fog are both present and distinct

HARD_INVARIANTS for validate_world_constitutional() [Phase C]:
  C1  all hex ids unique
  C2  all terrain values in allowed set
  C3  all structures legal for terrain
  C4  no sovereign overlays at generation time
  C5  no ownership assigned during generation
  C6  HARBOR only on COAST
  C7  FARM only on legal terrain
  C8  generation_entropy present on every cell
  C9  epistemic_fog present on every cell
  C10 world.seed present
  C11 world.solver_version present
  C12 world.cells non-empty list
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    # Package import (preferred): conquest is a package in the Python path
    from conquest.tiles import (
        TERRAIN_REGISTRY,
        STRUCTURE_REGISTRY,
        RECEIPT_REQUIRED_OVERLAYS,
        SOVEREIGN_OVERLAYS,
    )
    from conquest.hex_grid import axial_neighbors, hex_id as _hid
    _USE_CANONICAL = True
except ImportError:
    # Fallback: direct JSON load (when conquest/ is on sys.path directly)
    import json
    from pathlib import Path
    _HERE = Path(__file__).parent
    _TILES = json.loads((_HERE / "conquest_tiles.json").read_text())
    TERRAIN_REGISTRY   = _TILES["terrain_registry"]
    STRUCTURE_REGISTRY = _TILES["structure_registry"]
    _OVERLAY_REGISTRY  = _TILES["overlay_registry"]
    RECEIPT_REQUIRED_OVERLAYS = frozenset(
        n for n, s in _OVERLAY_REGISTRY.items() if s.get("requires_receipt", False)
    )
    SOVEREIGN_OVERLAYS = frozenset({
        "CLAIMED", "FORTIFIED", "SEALED", "RESOURCE_LOCKED", "DUEL_PENDING"
    })
    _HEX_DIRECTIONS = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
    def axial_neighbors(q, r):
        return [(q+dq, r+dr) for dq, dr in _HEX_DIRECTIONS]
    def _hid(q, r):
        return f"H{q}_{r}"
    _USE_CANONICAL = False


@dataclass
class ValidationReport:
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok":         self.ok,
            "violations": self.violations,
            "warnings":   self.warnings,
        }


def validate_world(hexes: list[dict[str, Any]]) -> ValidationReport:
    """
    Validate a list of hex dicts (WorldV1.hexes serialized with to_dict()).

    Returns a ValidationReport with violations (hard errors) and warnings (soft).
    """
    report = ValidationReport()
    hex_map: dict[str, dict[str, Any]] = {h["hex_id"]: h for h in hexes}

    for tile in hexes:
        hex_id  = tile.get("hex_id", "??")
        terrain = tile.get("terrain")
        struct  = tile.get("structure")
        overlay = tile.get("overlay", [])
        receipt = tile.get("receipt_hash")
        owner   = tile.get("owner_house_id")

        # V1: valid terrain
        if terrain not in TERRAIN_REGISTRY:
            report.violations.append(f"[{hex_id}] unknown terrain: {terrain!r}")
            continue  # cannot validate further without valid terrain

        # V2: structure legal for terrain
        if struct is not None:
            if struct not in STRUCTURE_REGISTRY:
                report.violations.append(f"[{hex_id}] unknown structure: {struct!r}")
            elif terrain not in STRUCTURE_REGISTRY[struct]["allowed_on"]:
                report.violations.append(
                    f"[{hex_id}] structure {struct!r} not allowed on {terrain!r}"
                )

        # V3 + V8: receipt-requiring overlays must have receipt_hash
        for ovl in overlay:
            if ovl in RECEIPT_REQUIRED_OVERLAYS and not receipt:
                report.violations.append(
                    f"[{hex_id}] overlay {ovl!r} requires receipt but receipt_hash is null"
                )

        # V4: no ownership on UNCLAIMED/CLAIMABLE
        if owner is not None and any(o in ("UNCLAIMED", "CLAIMABLE") for o in overlay):
            report.violations.append(
                f"[{hex_id}] owner_house_id set but tile is {overlay} (should be null at generation)"
            )

        # V6: HARBOR only on COAST
        if struct == "HARBOR" and terrain != "COAST":
            report.violations.append(f"[{hex_id}] HARBOR requires COAST, got {terrain!r}")

        # V7: FARM only on PLAIN
        if struct == "FARM" and terrain != "PLAIN":
            report.violations.append(f"[{hex_id}] FARM requires PLAIN, got {terrain!r}")

        # V9: generation_entropy and epistemic_fog both present
        if "generation_entropy" not in tile:
            report.warnings.append(f"[{hex_id}] missing generation_entropy field")
        if "epistemic_fog" not in tile:
            report.warnings.append(f"[{hex_id}] missing epistemic_fog field")

    # V5: river continuity (basic — each RIVER must have at least one water neighbor)
    _check_river_continuity(hexes, hex_map, report)

    return report


_WATER_TERRAINS = frozenset({"RIVER", "LAKE", "COAST", "SEA", "BRIDGE"})


# ── Phase C: Constitutional validator (CONQUEST_WFC_SPEC_V1) ──────────────────

class WorldValidationError(Exception):
    """Hard-fail error for constitutional world validation (Phase C)."""


# Sovereign overlays that must NEVER appear at generation time.
# Any of these on a cell means ownership was pre-assigned without a receipt.
ILLEGAL_GENERATION_OVERLAYS: frozenset[str] = frozenset({
    "CLAIMED",
    "CONTESTED",
    "FORTIFIED",
    "SEALED",
    "RESOURCE_LOCKED",
    "DUEL_PENDING",
})

# Terrain types that FARM is legal on (V1 names and V0_1 names both accepted)
_FARM_LEGAL_TERRAINS: frozenset[str] = frozenset({"PLAIN", "GRASS"})


def validate_world_constitutional(world: dict, tiles: dict) -> None:
    """
    Phase C constitutional validator (CONQUEST_WFC_SPEC_V1).

    Args:
        world:  {"seed": <any>, "solver_version": <str>, "cells": [<cell>, ...]}
        tiles:  {"layers": {"terrain": [<tile_id>, ...]},
                 "structure_rules": {<struct>: [<legal_terrain>, ...]}}

    Raises WorldValidationError on the first hard invariant violation.

    Invariants checked (C1–C12):
        C1   all hex_ids are unique and non-empty strings
        C2   all terrain values are in the allowed set
        C3   all structures are legal for their terrain
        C4   no ILLEGAL_GENERATION_OVERLAYS present at generation time
        C5   no ownership (owner_house_id) assigned during generation
        C6   HARBOR only on COAST
        C7   FARM only on PLAIN or GRASS
        C8   generation_entropy present on every cell
        C9   epistemic_fog present on every cell
        C10  world.seed present
        C11  world.solver_version present
        C12  world.cells is a non-empty list
    """
    # ── C10: world.seed ────────────────────────────────────────────────────────
    if "seed" not in world:
        raise WorldValidationError("C10: world.seed missing")

    # ── C11: world.solver_version ──────────────────────────────────────────────
    if "solver_version" not in world:
        raise WorldValidationError("C11: world.solver_version missing")

    # ── C12: world.cells ──────────────────────────────────────────────────────
    cells = world.get("cells")
    if not isinstance(cells, list) or len(cells) == 0:
        raise WorldValidationError("C12: world.cells must be a non-empty list")

    # ── Build lookup structures ────────────────────────────────────────────────
    allowed_terrain: set[str]        = set(tiles["layers"]["terrain"])
    structure_rules: dict[str, list] = tiles.get("structure_rules", {})
    seen_ids:        set[str]        = set()

    # ── Per-cell invariants ────────────────────────────────────────────────────
    for cell in cells:
        # C1: unique, non-empty hex_id
        hex_id = cell.get("hex_id")
        if not isinstance(hex_id, str) or not hex_id:
            raise WorldValidationError(
                f"C1: hex_id missing or invalid: {hex_id!r}"
            )
        if hex_id in seen_ids:
            raise WorldValidationError(
                f"C1: duplicate hex_id: {hex_id!r}"
            )
        seen_ids.add(hex_id)

        terrain = cell.get("terrain")

        # C2: terrain in allowed set
        if terrain not in allowed_terrain:
            raise WorldValidationError(
                f"C2: [{hex_id}] invalid terrain {terrain!r} "
                f"(not in {sorted(allowed_terrain)})"
            )

        # C3: structure legal for terrain
        structure = cell.get("structure")
        if structure is not None:
            legal_terrains = structure_rules.get(structure)
            if legal_terrains is None:
                raise WorldValidationError(
                    f"C3: [{hex_id}] unknown structure {structure!r}"
                )
            if terrain not in legal_terrains:
                raise WorldValidationError(
                    f"C3: [{hex_id}] structure {structure!r} illegal on terrain {terrain!r}; "
                    f"allowed on: {legal_terrains}"
                )

        # C4: no illegal generation overlays
        overlays = cell.get("overlay", [])
        if not isinstance(overlays, list):
            raise WorldValidationError(
                f"C4: [{hex_id}] overlay must be a list, got {type(overlays).__name__}"
            )
        illegal = ILLEGAL_GENERATION_OVERLAYS.intersection(overlays)
        if illegal:
            raise WorldValidationError(
                f"C4: [{hex_id}] illegal sovereign overlays at generation time: "
                f"{sorted(illegal)}"
            )

        # C5: no ownership at generation
        if cell.get("owner_house_id") is not None:
            raise WorldValidationError(
                f"C5: [{hex_id}] owner_house_id assigned during generation "
                f"(must be null): {cell['owner_house_id']!r}"
            )

        # C6: HARBOR only on COAST
        if structure == "HARBOR" and terrain != "COAST":
            raise WorldValidationError(
                f"C6: [{hex_id}] HARBOR must be on COAST, got {terrain!r}"
            )

        # C7: FARM only on PLAIN or GRASS
        if structure == "FARM" and terrain not in _FARM_LEGAL_TERRAINS:
            raise WorldValidationError(
                f"C7: [{hex_id}] FARM must be on PLAIN or GRASS, got {terrain!r}"
            )

        # C8: generation_entropy present
        if "generation_entropy" not in cell:
            raise WorldValidationError(
                f"C8: [{hex_id}] generation_entropy field missing"
            )

        # C9: epistemic_fog present
        if "epistemic_fog" not in cell:
            raise WorldValidationError(
                f"C9: [{hex_id}] epistemic_fog field missing"
            )


def _check_river_continuity(
    hexes: list[dict[str, Any]],
    hex_map: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    """V5: RIVER tiles should connect to water neighbors."""
    river_tiles = [h for h in hexes if h.get("terrain") == "RIVER"]

    for tile in river_tiles:
        q, r = tile["q"], tile["r"]
        water_found = any(
            hex_map.get(_hid(nq, nr), {}).get("terrain") in _WATER_TERRAINS
            for nq, nr in axial_neighbors(q, r)
        )
        if not water_found:
            report.warnings.append(
                f"[{tile['hex_id']}] RIVER tile has no water neighbors (continuity warning)"
            )
