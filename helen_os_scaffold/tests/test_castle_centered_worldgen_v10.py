"""
tests/test_castle_centered_worldgen_v10.py — Move 10: Castle-Centered Worldgen

Tests:
    CC01  hex_ring yields correct count and distances
    CC02  build_radial_lattice sizes correctly for radius=2
    CC03  radial lattice dual-field invariant (generation_entropy ≠ epistemic_fog)
    CC04  domain template sets ring-0 to HILL + CASTLE
    CC05  domain template sets ring-1 hexes to preferred terrains
    CC06  domain template sets ring-3 quota (ROAD × 1, PLAIN × 2)
    CC07  WFC fills all unresolved cells (no terrain=None after generation)
    CC08  same seed → same world_hash  (determinism invariant)
    CC09  different seeds → different world_hashes
    CC10  castle tile preserved through full pipeline (terrain=HILL, structure=CASTLE)
    CC11  no SOVEREIGN overlays in generated world
    CC12  all terrain values are valid (in TERRAIN_REGISTRY)
    CC13  all hex_ids are unique
    CC14  survivability dict has correct schema
    CC15  validate_castle_start detects missing exits
    CC16  emit_world_generation_receipt returns correct artifact_type
    CC17  receipt world_hash matches re-computed hash
    CC18  receipt is deterministic for same world
    CC19  different radius → different hex count
    CC20  repair_events is a list (may be empty)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

# Add helen_os_scaffold root to sys.path
_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SCAFFOLD_ROOT))

import pytest

from conquest.castle_centered_generator import (
    CASTLE_DOMAIN_TEMPLATE,
    build_radial_lattice,
    emit_world_generation_receipt,
    generate_world_around_castle,
    hex_ring,
    validate_castle_start,
    _sub_seed,
)
from conquest.hex_grid import axial_distance, hex_id
from conquest.tiles import TERRAIN_REGISTRY, SOVEREIGN_OVERLAYS


# ── Helpers ─────────────────────────────────────────────────────────────────

_SMALL_RADIUS = 4   # fast for unit tests
_DEFAULT_SEED = 42


def _quick_world(seed: int = _DEFAULT_SEED, radius: int = _SMALL_RADIUS) -> dict:
    return generate_world_around_castle(
        world_seed=seed,
        castle_id="CASTLE_TEST_001",
        anchor_q=0,
        anchor_r=0,
        radius=radius,
    )


# ── CC01: hex_ring yields correct count and distances ──────────────────────

class TestHexRing:
    def test_cc01_ring0_is_single_center(self):
        result = hex_ring(0, 0, 0)
        assert result == [(0, 0)]

    def test_cc01_ring1_yields_six(self):
        result = hex_ring(0, 0, 1)
        assert len(result) == 6

    def test_cc01_ring2_yields_twelve(self):
        result = hex_ring(0, 0, 2)
        assert len(result) == 12

    def test_cc01_ring3_yields_eighteen(self):
        result = hex_ring(0, 0, 3)
        assert len(result) == 18

    def test_cc01_ring_n_yields_6n(self):
        for n in range(1, 6):
            assert len(hex_ring(0, 0, n)) == 6 * n

    def test_cc01_all_at_correct_axial_distance(self):
        for radius in range(1, 5):
            for q, r in hex_ring(0, 0, radius):
                d = axial_distance(0, 0, q, r)
                assert d == radius, f"ring {radius}: ({q},{r}) has distance {d}"


# ── CC02: build_radial_lattice sizes correctly ──────────────────────────────

class TestRadialLattice:
    def test_cc02_radius_2_has_19_hexes(self):
        # 1 + 6 + 12 = 19 hexes for radius=2
        lattice = build_radial_lattice(0, 0, 2)
        assert len(lattice) == 19

    def test_cc02_radius_0_has_1_hex(self):
        lattice = build_radial_lattice(0, 0, 0)
        assert len(lattice) == 1

    def test_cc02_anchor_present(self):
        lattice = build_radial_lattice(0, 0, 2)
        assert "H0_0" in lattice

    def test_cc02_all_hexes_have_ring_field(self):
        lattice = build_radial_lattice(0, 0, 3)
        for hid, cell in lattice.items():
            assert "ring" in cell, f"{hid} missing ring field"

    def test_cc02_ring_values_correct(self):
        lattice = build_radial_lattice(0, 0, 3)
        for hid, cell in lattice.items():
            expected_ring = axial_distance(0, 0, cell["q"], cell["r"])
            assert cell["ring"] == expected_ring, f"{hid}: ring={cell['ring']} expected {expected_ring}"


# ── CC03: dual-field invariant ──────────────────────────────────────────────

class TestDualFieldInvariant:
    def test_cc03_all_hexes_have_both_fields(self):
        world = _quick_world()
        for h in world["hexes"]:
            assert "generation_entropy" in h, f"{h['hex_id']} missing generation_entropy"
            assert "epistemic_fog" in h, f"{h['hex_id']} missing epistemic_fog"

    def test_cc03_fields_are_not_equal(self):
        """generation_entropy ≠ epistemic_fog on most tiles (not definitionally coupled)."""
        world = _quick_world()
        # At least 50% of tiles must have distinct values
        distinct = sum(
            1 for h in world["hexes"]
            if abs(h.get("generation_entropy", 0) - h.get("epistemic_fog", 0)) > 1e-9
        )
        assert distinct > len(world["hexes"]) * 0.5


# ── CC04: domain template ring-0 ───────────────────────────────────────────

class TestDomainTemplate:
    def test_cc04_ring0_terrain_is_hill(self):
        world = _quick_world()
        hid = hex_id(0, 0)
        h = next(h for h in world["hexes"] if h["hex_id"] == hid)
        assert h["terrain"] == "HILL", f"ring0 terrain={h['terrain']}, expected HILL"

    def test_cc04_ring0_structure_is_castle(self):
        world = _quick_world()
        hid = hex_id(0, 0)
        h = next(h for h in world["hexes"] if h["hex_id"] == hid)
        assert h["structure"] == "CASTLE", f"ring0 structure={h['structure']}, expected CASTLE"


# ── CC05: domain template ring-1 ───────────────────────────────────────────

    def test_cc05_ring1_terrains_are_preferred(self):
        world = _quick_world()
        preferred = set(CASTLE_DOMAIN_TEMPLATE[1]["preferred"])
        ring1 = [h for h in world["hexes"] if h.get("ring") == 1]
        assert ring1, "no ring-1 hexes found"
        for h in ring1:
            assert h["terrain"] in preferred, (
                f"{h['hex_id']} ring1 terrain={h['terrain']} not in preferred={preferred}"
            )

    def test_cc05_ring1_no_forbidden_terrains(self):
        world = _quick_world()
        forbidden = CASTLE_DOMAIN_TEMPLATE[1]["forbidden"]
        ring1 = [h for h in world["hexes"] if h.get("ring") == 1]
        for h in ring1:
            assert h["terrain"] not in forbidden, (
                f"{h['hex_id']} has forbidden terrain {h['terrain']!r}"
            )


# ── CC06: domain template ring-3 quota ─────────────────────────────────────

    def test_cc06_ring3_has_road_quota(self):
        world = _quick_world(radius=5)   # need ring 3 to exist
        ring3 = [h for h in world["hexes"] if h.get("ring") == 3]
        road_count = sum(1 for h in ring3 if h["terrain"] == "ROAD")
        # Quota = at least 1 ROAD pre-assigned; road_solver may add more
        assert road_count >= 1, f"ring3 ROAD count={road_count}, expected >= 1"

    def test_cc06_ring3_has_plain_quota(self):
        world = _quick_world(radius=5)
        ring3 = [h for h in world["hexes"] if h.get("ring") == 3]
        plain_count = sum(1 for h in ring3 if h["terrain"] == "PLAIN")
        assert plain_count >= 2, f"ring3 PLAIN count={plain_count}, expected >= 2"


# ── CC07: all cells resolved after generation ──────────────────────────────

class TestWFCCompletion:
    def test_cc07_no_null_terrain(self):
        world = _quick_world()
        nulls = [h["hex_id"] for h in world["hexes"] if h.get("terrain") is None]
        assert not nulls, f"unresolved terrain on: {nulls}"


# ── CC08–CC09: determinism ─────────────────────────────────────────────────

class TestDeterminism:
    def test_cc08_same_seed_same_world_hash(self):
        r1 = emit_world_generation_receipt(
            _quick_world(seed=777), 777, "CASTLE_TEST"
        )
        r2 = emit_world_generation_receipt(
            _quick_world(seed=777), 777, "CASTLE_TEST"
        )
        assert r1["world_hash"] == r2["world_hash"], (
            "Same seed produced different world_hash — determinism violated"
        )

    def test_cc09_different_seeds_different_hashes(self):
        r1 = emit_world_generation_receipt(
            _quick_world(seed=1), 1, "CASTLE_TEST"
        )
        r2 = emit_world_generation_receipt(
            _quick_world(seed=2), 2, "CASTLE_TEST"
        )
        assert r1["world_hash"] != r2["world_hash"]


# ── CC10: castle preserved ─────────────────────────────────────────────────

class TestCastlePreservation:
    def test_cc10_castle_tile_terrain_hill(self):
        world = _quick_world()
        anchor = next(
            h for h in world["hexes"] if h["hex_id"] == world["anchor"]["hex_id"]
        )
        assert anchor["terrain"] == "HILL"

    def test_cc10_castle_tile_structure_castle(self):
        world = _quick_world()
        anchor = next(
            h for h in world["hexes"] if h["hex_id"] == world["anchor"]["hex_id"]
        )
        assert anchor["structure"] == "CASTLE"

    def test_cc10_anchor_hex_id_matches(self):
        world = _quick_world()
        assert world["anchor"]["hex_id"] == hex_id(0, 0)


# ── CC11: no sovereign overlays ────────────────────────────────────────────

class TestSovereigntyInvariant:
    def test_cc11_no_sovereign_overlays(self):
        world = _quick_world()
        for h in world["hexes"]:
            for ovl in h.get("overlay", []):
                assert ovl not in SOVEREIGN_OVERLAYS, (
                    f"{h['hex_id']} has sovereign overlay {ovl!r} — forbidden at worldgen"
                )

    def test_cc11_no_owner_house_id(self):
        world = _quick_world()
        for h in world["hexes"]:
            assert h.get("owner_house_id") is None, (
                f"{h['hex_id']} has owner_house_id set — forbidden at worldgen"
            )


# ── CC12: valid terrains ────────────────────────────────────────────────────

class TestTerrainValidity:
    def test_cc12_all_terrains_in_registry(self):
        world = _quick_world()
        for h in world["hexes"]:
            assert h["terrain"] in TERRAIN_REGISTRY, (
                f"{h['hex_id']} terrain={h['terrain']!r} not in TERRAIN_REGISTRY"
            )


# ── CC13: unique hex_ids ────────────────────────────────────────────────────

class TestHexIdUniqueness:
    def test_cc13_all_hex_ids_unique(self):
        world = _quick_world()
        ids = [h["hex_id"] for h in world["hexes"]]
        assert len(ids) == len(set(ids)), "duplicate hex_ids found"


# ── CC14–CC15: survivability ────────────────────────────────────────────────

class TestSurvivability:
    def test_cc14_survivability_dict_schema(self):
        world = _quick_world()
        sv = world["survivability"]
        assert isinstance(sv, dict)
        assert "ok" in sv
        assert "violations" in sv
        assert isinstance(sv["ok"], bool)
        assert isinstance(sv["violations"], list)

    def test_cc15_validate_castle_start_detects_blocked_castle(self):
        """Artificially block all castle neighbors → traversable_exits < 2."""
        # Build minimal lattice and block all ring-1 hexes with MOUNTAIN
        lattice = build_radial_lattice(0, 0, 2)
        castle_hid = hex_id(0, 0)
        lattice[castle_hid]["terrain"] = "HILL"
        # Set all neighbors to non-passable MOUNTAIN
        from conquest.hex_grid import axial_neighbors
        for nq, nr in axial_neighbors(0, 0):
            nid = hex_id(nq, nr)
            if nid in lattice:
                lattice[nid]["terrain"] = "MOUNTAIN"
        # Set remaining hexes to PLAIN for resource check
        for hid, cell in lattice.items():
            if cell["terrain"] is None:
                cell["terrain"] = "PLAIN"
        result = validate_castle_start(lattice, castle_hid)
        assert not result["ok"]
        assert any("traversable_exits" in v for v in result["violations"])


# ── CC16–CC18: receipt integrity ────────────────────────────────────────────

class TestReceiptIntegrity:
    def test_cc16_receipt_artifact_type(self):
        world  = _quick_world()
        receipt = emit_world_generation_receipt(world, _DEFAULT_SEED, "CASTLE_TEST")
        assert receipt["artifact_type"] == "WORLD_GENERATION_RECEIPT_V1"

    def test_cc17_receipt_world_hash_is_sha256(self):
        world  = _quick_world()
        receipt = emit_world_generation_receipt(world, _DEFAULT_SEED, "CASTLE_TEST")
        assert receipt["world_hash"].startswith("sha256:")
        assert len(receipt["world_hash"]) == 7 + 64  # "sha256:" + 64 hex chars

    def test_cc17_world_hash_deterministic_from_hexes(self):
        """Verify world_hash matches manual re-computation from sorted hexes."""
        world   = _quick_world()
        receipt = emit_world_generation_receipt(world, _DEFAULT_SEED, "CASTLE_TEST")

        sorted_hexes = sorted(world["hexes"], key=lambda h: h["hex_id"])
        canon = json.dumps(sorted_hexes, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        expected = "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()
        assert receipt["world_hash"] == expected

    def test_cc18_receipt_is_deterministic(self):
        world1 = _quick_world(seed=99)
        world2 = _quick_world(seed=99)
        r1 = emit_world_generation_receipt(world1, 99, "CASTLE_X")
        r2 = emit_world_generation_receipt(world2, 99, "CASTLE_X")
        assert r1["world_hash"] == r2["world_hash"]
        assert r1["terrain_hash"] == r2["terrain_hash"]


# ── CC19: radius affects hex count ─────────────────────────────────────────

class TestRadiusEffect:
    def test_cc19_larger_radius_more_hexes(self):
        w4 = _quick_world(radius=4)
        w6 = _quick_world(radius=6)
        assert len(w6["hexes"]) > len(w4["hexes"])

    def test_cc19_hex_count_formula(self):
        """Total hexes for radius R = 1 + 6 + 12 + ... + 6R = 1 + 3R(R+1)."""
        for r in (1, 2, 3, 4, 5):
            world = generate_world_around_castle(
                world_seed=1, castle_id="TEST", radius=r
            )
            expected = 1 + 3 * r * (r + 1)
            assert len(world["hexes"]) == expected, (
                f"radius={r}: got {len(world['hexes'])}, expected {expected}"
            )


# ── CC20: repair_events ─────────────────────────────────────────────────────

class TestRepairEvents:
    def test_cc20_repair_events_is_list(self):
        world = _quick_world()
        assert isinstance(world["repair_events"], list)

    def test_cc20_repair_event_schema(self):
        world = _quick_world()
        for ev in world["repair_events"]:
            assert "hex_id" in ev
            assert "reason" in ev
            assert "resolved_to" in ev
