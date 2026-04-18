"""
tests/test_world_validator.py — Phase C: constitutional world validator tests.

CONQUEST_WFC_SPEC_V1 — validate_world_constitutional() hard-fail suite.

Test IDs:
    WV01  valid world passes validation
    WV02  empty cells list fails (C12)
    WV03  missing world.seed fails (C10)
    WV04  missing world.solver_version fails (C11)
    WV05  missing hex_id fails (C1)
    WV06  empty hex_id fails (C1)
    WV07  duplicate hex_id fails (C1)
    WV08  unknown terrain fails (C2)
    WV09  illegal structure on terrain fails (C3)
    WV10  unknown structure fails (C3)
    WV11  CLAIMED overlay at generation fails (C4)
    WV12  FORTIFIED overlay at generation fails (C4)
    WV13  SEALED overlay at generation fails (C4)
    WV14  RESOURCE_LOCKED overlay at generation fails (C4)
    WV15  DUEL_PENDING overlay at generation fails (C4)
    WV16  CONTESTED overlay at generation fails (C4)
    WV17  owner_house_id set at generation fails (C5)
    WV18  HARBOR not on COAST fails (C6)
    WV19  HARBOR on COAST passes (C6 positive)
    WV20  FARM not on PLAIN/GRASS fails (C7)
    WV21  FARM on PLAIN passes (C7 positive)
    WV22  FARM on GRASS passes (C7 positive)
    WV23  missing generation_entropy fails (C8)
    WV24  missing epistemic_fog fails (C9)
    WV25  CLAIMABLE overlay is legal at generation (positive)
    WV26  UNCLAIMED overlay is legal at generation (positive)
    WV27  multiple cells — second cell error is caught
    WV28  overlay must be a list, not a string (C4)
    WV29  cells may be empty list only if None check — missing "cells" key fails (C12)
"""
from __future__ import annotations

import sys
import os
import pytest

# Add helen_os_scaffold root so that `conquest` is importable as a package.
_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, _SCAFFOLD_ROOT)

from conquest.world_validator import validate_world_constitutional, WorldValidationError


# ── Tiles spec (simplified for validator tests) ────────────────────────────────

TILES_V1 = {
    "layers": {
        "terrain": ["OCEAN", "COAST", "GRASS", "ROAD", "RIVER", "FOREST", "CITY", "MOUNTAIN"],
    },
    "structure_rules": {
        "HARBOR": ["COAST"],
        "FARM":   ["PLAIN", "GRASS"],
        "CASTLE": ["MOUNTAIN", "GRASS"],
        "CITY":   ["GRASS", "COAST"],
    },
}

# Also include V0_1 terrain names for backward-compat cases
TILES_V0_1 = {
    "layers": {
        "terrain": ["SEA", "COAST", "PLAIN", "FOREST", "HILL", "MOUNTAIN", "ROAD", "RIVER",
                    "MARSH", "DESERT", "LAKE", "BRIDGE", "GRASS"],
    },
    "structure_rules": {
        "HARBOR": ["COAST"],
        "FARM":   ["PLAIN", "GRASS"],
        "CASTLE": ["HILL", "PLAIN", "MOUNTAIN"],
    },
}


def _make_cell(
    hex_id: str = "H0_0",
    terrain: str = "GRASS",
    structure=None,
    overlay=None,
    owner_house_id=None,
    generation_entropy: float = 0.42,
    epistemic_fog: bool = True,
) -> dict:
    return {
        "hex_id":             hex_id,
        "terrain":            terrain,
        "structure":          structure,
        "overlay":            overlay if overlay is not None else ["UNCLAIMED"],
        "owner_house_id":     owner_house_id,
        "generation_entropy": generation_entropy,
        "epistemic_fog":      epistemic_fog,
    }


def _make_world(cells=None, seed=42, solver_version="WFC_SOLVER_V1") -> dict:
    if cells is None:
        cells = [_make_cell()]
    return {
        "seed":           seed,
        "solver_version": solver_version,
        "cells":          cells,
    }


# ── WV01: Valid world passes ───────────────────────────────────────────────────

class TestWV01ValidWorldPasses:
    def test_wv01_valid_single_cell(self):
        """WV01a: single cell valid world passes without exception."""
        validate_world_constitutional(_make_world(), TILES_V1)

    def test_wv01_valid_multiple_cells(self):
        """WV01b: multi-cell valid world passes."""
        cells = [
            _make_cell("H0_0", "GRASS"),
            _make_cell("H1_0", "FOREST"),
            _make_cell("H0_1", "COAST"),
        ]
        validate_world_constitutional(_make_world(cells), TILES_V1)

    def test_wv01_ocean_cell_valid(self):
        """WV01c: OCEAN tile (passable=false, water) passes."""
        cells = [_make_cell("H0_0", "OCEAN")]
        validate_world_constitutional(_make_world(cells), TILES_V1)

    def test_wv01_mountain_cell_valid(self):
        """WV01d: MOUNTAIN tile passes."""
        cells = [_make_cell("H0_0", "MOUNTAIN")]
        validate_world_constitutional(_make_world(cells), TILES_V1)


# ── WV02–WV04: World-level field checks ───────────────────────────────────────

class TestWV02_04WorldLevelFields:
    def test_wv02_empty_cells_fails(self):
        """WV02 (C12): empty cells list raises WorldValidationError."""
        world = _make_world(cells=[])
        with pytest.raises(WorldValidationError, match="C12"):
            validate_world_constitutional(world, TILES_V1)

    def test_wv02_none_cells_fails(self):
        """WV02 (C12): None cells raises WorldValidationError."""
        world = {"seed": 1, "solver_version": "V1", "cells": None}
        with pytest.raises(WorldValidationError, match="C12"):
            validate_world_constitutional(world, TILES_V1)

    def test_wv02_missing_cells_key_fails(self):
        """WV02 (C12): missing 'cells' key raises WorldValidationError."""
        world = {"seed": 1, "solver_version": "V1"}
        with pytest.raises(WorldValidationError, match="C12"):
            validate_world_constitutional(world, TILES_V1)

    def test_wv03_missing_seed_fails(self):
        """WV03 (C10): missing world.seed raises WorldValidationError."""
        world = {"solver_version": "V1", "cells": [_make_cell()]}
        with pytest.raises(WorldValidationError, match="C10"):
            validate_world_constitutional(world, TILES_V1)

    def test_wv04_missing_solver_version_fails(self):
        """WV04 (C11): missing world.solver_version raises WorldValidationError."""
        world = {"seed": 1, "cells": [_make_cell()]}
        with pytest.raises(WorldValidationError, match="C11"):
            validate_world_constitutional(world, TILES_V1)


# ── WV05–WV07: hex_id invariants ──────────────────────────────────────────────

class TestWV05_07HexId:
    def test_wv05_missing_hex_id_fails(self):
        """WV05 (C1): cell without hex_id raises WorldValidationError."""
        cell = _make_cell()
        del cell["hex_id"]
        with pytest.raises(WorldValidationError, match="C1"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv06_empty_hex_id_fails(self):
        """WV06 (C1): empty string hex_id raises WorldValidationError."""
        cell = _make_cell(hex_id="")
        with pytest.raises(WorldValidationError, match="C1"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv07_duplicate_hex_id_fails(self):
        """WV07 (C1): duplicate hex_id raises WorldValidationError."""
        cells = [_make_cell("SAME"), _make_cell("SAME")]
        with pytest.raises(WorldValidationError, match="C1"):
            validate_world_constitutional(_make_world(cells), TILES_V1)

    def test_wv07_unique_ids_pass(self):
        """WV07 positive: unique hex_ids pass."""
        cells = [_make_cell("H0"), _make_cell("H1"), _make_cell("H2")]
        validate_world_constitutional(_make_world(cells), TILES_V1)


# ── WV08: Terrain invariant ───────────────────────────────────────────────────

class TestWV08Terrain:
    def test_wv08_unknown_terrain_fails(self):
        """WV08 (C2): terrain not in tile set raises WorldValidationError."""
        cell = _make_cell(terrain="LAVA")
        with pytest.raises(WorldValidationError, match="C2"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv08_none_terrain_fails(self):
        """WV08 (C2): None terrain raises WorldValidationError."""
        cell = _make_cell(terrain=None)
        with pytest.raises(WorldValidationError, match="C2"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv08_all_v1_terrains_pass(self):
        """WV08 positive: all 8 WFC V1 terrain types are accepted."""
        for i, t in enumerate(["OCEAN", "COAST", "GRASS", "ROAD",
                                "RIVER", "FOREST", "CITY", "MOUNTAIN"]):
            cells = [_make_cell(f"H{i}", terrain=t)]
            validate_world_constitutional(_make_world(cells), TILES_V1)


# ── WV09–WV10: Structure invariant ────────────────────────────────────────────

class TestWV09_10Structure:
    def test_wv09_illegal_structure_on_terrain_fails(self):
        """WV09 (C3): HARBOR on GRASS raises WorldValidationError."""
        cell = _make_cell(terrain="GRASS", structure="HARBOR")
        with pytest.raises(WorldValidationError, match="C3"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv09_castle_on_ocean_fails(self):
        """WV09 (C3): CASTLE on OCEAN raises WorldValidationError."""
        cell = _make_cell(terrain="OCEAN", structure="CASTLE")
        with pytest.raises(WorldValidationError, match="C3"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv10_unknown_structure_fails(self):
        """WV10 (C3): unknown structure name raises WorldValidationError."""
        cell = _make_cell(terrain="GRASS", structure="UNICORN_TOWER")
        with pytest.raises(WorldValidationError, match="C3"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv10_no_structure_passes(self):
        """WV10 positive: None structure passes."""
        cell = _make_cell(terrain="GRASS", structure=None)
        validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv09_castle_on_grass_passes(self):
        """WV09 positive: CASTLE on GRASS is legal."""
        cell = _make_cell(terrain="GRASS", structure="CASTLE")
        validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV11–WV16: Sovereign overlay invariant ───────────────────────────────────

class TestWV11_16SovereignOverlays:
    @pytest.mark.parametrize("illegal_overlay", [
        "CLAIMED", "FORTIFIED", "SEALED", "RESOURCE_LOCKED", "DUEL_PENDING", "CONTESTED"
    ])
    def test_illegal_sovereign_overlay_fails(self, illegal_overlay):
        """WV11–WV16 (C4): each illegal sovereign overlay raises WorldValidationError."""
        cell = _make_cell(overlay=[illegal_overlay])
        with pytest.raises(WorldValidationError, match="C4"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv28_overlay_not_list_fails(self):
        """WV28 (C4): overlay as string (not list) raises WorldValidationError."""
        cell = _make_cell()
        cell["overlay"] = "CLAIMED"    # string, not list
        with pytest.raises(WorldValidationError, match="C4"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV17: Ownership invariant ─────────────────────────────────────────────────

class TestWV17Ownership:
    def test_wv17_owner_house_id_set_fails(self):
        """WV17 (C5): owner_house_id assigned during generation raises WorldValidationError."""
        cell = _make_cell(owner_house_id="HOUSE-ALPHA")
        with pytest.raises(WorldValidationError, match="C5"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv17_owner_none_passes(self):
        """WV17 positive: owner_house_id=None passes."""
        cell = _make_cell(owner_house_id=None)
        validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV18–WV19: HARBOR invariant ──────────────────────────────────────────────

class TestWV18_19Harbor:
    def test_wv18_harbor_on_grass_fails(self):
        """WV18 (C6): HARBOR on GRASS raises WorldValidationError."""
        cell = _make_cell(terrain="GRASS", structure="HARBOR")
        with pytest.raises(WorldValidationError, match="C6|C3"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv18_harbor_on_mountain_fails(self):
        """WV18 (C6): HARBOR on MOUNTAIN raises WorldValidationError."""
        cell = _make_cell(terrain="MOUNTAIN", structure="HARBOR")
        with pytest.raises(WorldValidationError, match="C3|C6"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv19_harbor_on_coast_passes(self):
        """WV19 (C6 positive): HARBOR on COAST is legal."""
        cell = _make_cell(terrain="COAST", structure="HARBOR")
        validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV20–WV22: FARM invariant ─────────────────────────────────────────────────

class TestWV20_22Farm:
    def test_wv20_farm_on_mountain_fails(self):
        """WV20 (C7): FARM on MOUNTAIN raises WorldValidationError."""
        cell = _make_cell(terrain="MOUNTAIN", structure="FARM")
        with pytest.raises(WorldValidationError, match="C3|C7"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv20_farm_on_ocean_fails(self):
        """WV20 (C7): FARM on OCEAN raises WorldValidationError."""
        cell = _make_cell(terrain="OCEAN", structure="FARM")
        with pytest.raises(WorldValidationError, match="C3|C7"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv21_farm_on_plain_passes(self):
        """WV21 (C7 positive): FARM on PLAIN is legal."""
        tiles_with_plain = {
            "layers": {"terrain": ["PLAIN", "GRASS", "COAST"]},
            "structure_rules": {"FARM": ["PLAIN", "GRASS"]},
        }
        cell = _make_cell(terrain="PLAIN", structure="FARM")
        validate_world_constitutional(_make_world([cell]), tiles_with_plain)

    def test_wv22_farm_on_grass_passes(self):
        """WV22 (C7 positive): FARM on GRASS is legal."""
        cell = _make_cell(terrain="GRASS", structure="FARM")
        validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV23–WV24: Entropy/fog invariants ────────────────────────────────────────

class TestWV23_24EntropyFog:
    def test_wv23_missing_generation_entropy_fails(self):
        """WV23 (C8): missing generation_entropy raises WorldValidationError."""
        cell = _make_cell()
        del cell["generation_entropy"]
        with pytest.raises(WorldValidationError, match="C8"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv24_missing_epistemic_fog_fails(self):
        """WV24 (C9): missing epistemic_fog raises WorldValidationError."""
        cell = _make_cell()
        del cell["epistemic_fog"]
        with pytest.raises(WorldValidationError, match="C9"):
            validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv23_24_both_present_passes(self):
        """WV23/WV24 positive: both fields present passes."""
        cell = _make_cell(generation_entropy=0.123, epistemic_fog=False)
        validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV25–WV26: Legal overlays at generation ───────────────────────────────────

class TestWV25_26LegalOverlays:
    def test_wv25_claimable_overlay_is_legal(self):
        """WV25 positive: CLAIMABLE overlay is legal at generation time."""
        cell = _make_cell(overlay=["CLAIMABLE"])
        validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_wv26_unclaimed_overlay_is_legal(self):
        """WV26 positive: UNCLAIMED overlay is legal at generation time."""
        cell = _make_cell(overlay=["UNCLAIMED"])
        validate_world_constitutional(_make_world([cell]), TILES_V1)

    def test_empty_overlay_is_legal(self):
        """Positive: empty overlay list is legal."""
        cell = _make_cell(overlay=[])
        validate_world_constitutional(_make_world([cell]), TILES_V1)


# ── WV27: Multi-cell — second cell error caught ───────────────────────────────

class TestWV27MultiCell:
    def test_wv27_second_cell_error_caught(self):
        """WV27: error in second cell is caught (not just first cell)."""
        cells = [
            _make_cell("H0_0", "GRASS"),   # valid
            _make_cell("H0_1", "LAVA"),    # invalid terrain
        ]
        with pytest.raises(WorldValidationError, match="C2"):
            validate_world_constitutional(_make_world(cells), TILES_V1)

    def test_wv27_all_cells_must_be_valid(self):
        """WV27: validation fails on the first violation found, not just last."""
        cells = [
            _make_cell("H0", "GRASS"),
            _make_cell("H1", "FOREST"),
            _make_cell("H2", "FOREST", owner_house_id="HOUSE-Z"),  # C5 violation
        ]
        with pytest.raises(WorldValidationError, match="C5"):
            validate_world_constitutional(_make_world(cells), TILES_V1)
