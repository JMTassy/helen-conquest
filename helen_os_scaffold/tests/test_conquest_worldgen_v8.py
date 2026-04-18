"""
tests/test_conquest_worldgen_v8.py — Move 8: CONQUESTLAND_WORLDGEN_V0_1

Tests:
  CW01: same seed → same world_hash (determinism)
  CW02: different seeds → different world_hash
  CW03: all hexes have valid terrain
  CW04: all structures are legal for terrain
  CW05: no CLAIMED/FORTIFIED/SEALED overlays at generation time
  CW06: no owner_house_id assigned at generation time
  CW07: receipt is emitted with correct fields
  CW08: world_hash matches across receipt fields
  CW09: tile count equals width × height
  CW10: generation_entropy and epistemic_fog are distinct fields
  CW11: world validator passes with no violations
  CW12: resource profiles contain only valid resource names
"""
import sys
import os

# Add helen_os_scaffold root so that `conquest` is importable as a package.
_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, _SCAFFOLD_ROOT)

import pytest
from conquest.conquest_world_generator import (
    generate_world,
    world_generation_receipt,
    TERRAIN_REGISTRY,
    STRUCTURE_REGISTRY,
)
from conquest.world_validator import validate_world

_VALID_RESOURCES = {
    "STONE", "WOOD", "GRAIN", "IRON", "WATER", "SALT", "GOLD", "KNOWLEDGE"
}

SEED_A = 912733
SEED_B = 42

# Use small world for speed
WIDTH, HEIGHT = 16, 16


@pytest.fixture(scope="module")
def world_a():
    return generate_world(SEED_A, WIDTH, HEIGHT)

@pytest.fixture(scope="module")
def world_b():
    return generate_world(SEED_B, WIDTH, HEIGHT)

@pytest.fixture(scope="module")
def world_a2():
    """Second generation of SEED_A — must match world_a."""
    return generate_world(SEED_A, WIDTH, HEIGHT)


# ── CW01: Determinism ─────────────────────────────────────────────────────────

def test_cw01_same_seed_same_world_hash(world_a, world_a2):
    """CW01: same seed → same world_hash."""
    r1 = world_generation_receipt(world_a,  SEED_A)
    r2 = world_generation_receipt(world_a2, SEED_A)
    assert r1.world_hash == r2.world_hash, "World hash must be deterministic"


def test_cw02_different_seeds_different_hashes(world_a, world_b):
    """CW02: different seeds → different world_hash."""
    r_a = world_generation_receipt(world_a, SEED_A)
    r_b = world_generation_receipt(world_b, SEED_B)
    assert r_a.world_hash != r_b.world_hash


# ── CW03–CW06: World invariants ───────────────────────────────────────────────

def test_cw03_all_hexes_have_valid_terrain(world_a):
    """CW03: every hex has a terrain from terrain_registry."""
    for tile in world_a.hexes:
        assert tile.terrain in TERRAIN_REGISTRY, f"{tile.hex_id}: unknown terrain {tile.terrain!r}"


def test_cw04_all_structures_legal_for_terrain(world_a):
    """CW04: every placed structure is allowed on its tile's terrain."""
    for tile in world_a.hexes:
        if tile.structure is None:
            continue
        assert tile.structure in STRUCTURE_REGISTRY, f"Unknown structure: {tile.structure}"
        allowed = STRUCTURE_REGISTRY[tile.structure]["allowed_on"]
        assert tile.terrain in allowed, (
            f"{tile.hex_id}: structure {tile.structure!r} not allowed on {tile.terrain!r}"
        )


def test_cw05_no_receipt_required_overlays_at_generation(world_a):
    """CW05: no CLAIMED/FORTIFIED/SEALED/RESOURCE_LOCKED/DUEL_PENDING at generation."""
    FORBIDDEN = {"CLAIMED", "FORTIFIED", "SEALED", "RESOURCE_LOCKED", "DUEL_PENDING"}
    for tile in world_a.hexes:
        bad = FORBIDDEN & set(tile.overlay)
        assert not bad, f"{tile.hex_id}: forbidden overlays at generation: {bad}"


def test_cw06_no_owner_house_id_at_generation(world_a):
    """CW06: owner_house_id is null for all tiles at generation time."""
    for tile in world_a.hexes:
        assert tile.owner_house_id is None, (
            f"{tile.hex_id}: owner_house_id must be null at generation, got {tile.owner_house_id!r}"
        )


# ── CW07–CW08: Receipt ────────────────────────────────────────────────────────

def test_cw07_receipt_has_required_fields(world_a):
    """CW07: receipt has all required fields."""
    r = world_generation_receipt(world_a, SEED_A)
    assert r.seed == SEED_A
    assert r.world_hash.startswith("sha256:")
    assert r.terrain_hash.startswith("sha256:")
    assert r.structure_hash.startswith("sha256:")
    assert r.region_hash.startswith("sha256:")
    assert r.status == "ok"
    assert "CONQUEST_TILES_V0_1" in r.generator_version
    assert str(SEED_A) in r.replay_command


def test_cw08_receipt_world_hash_matches_world(world_a):
    """CW08: receipt world_hash is consistent across two receipt calls."""
    r1 = world_generation_receipt(world_a, SEED_A)
    r2 = world_generation_receipt(world_a, SEED_A)
    assert r1.world_hash == r2.world_hash


# ── CW09: Grid size ───────────────────────────────────────────────────────────

def test_cw09_tile_count(world_a):
    """CW09: tile count equals width × height."""
    assert len(world_a.hexes) == WIDTH * HEIGHT


# ── CW10: Entropy / fog distinction ──────────────────────────────────────────

def test_cw10_entropy_and_fog_are_separate(world_a):
    """CW10: generation_entropy and epistemic_fog are distinct fields."""
    for tile in world_a.hexes:
        assert isinstance(tile.generation_entropy, float), (
            f"{tile.hex_id}: generation_entropy must be float"
        )
        assert isinstance(tile.epistemic_fog, bool), (
            f"{tile.hex_id}: epistemic_fog must be bool"
        )


# ── CW11: Validator ───────────────────────────────────────────────────────────

def test_cw11_world_validator_no_violations(world_a):
    """CW11: world_validator reports no violations for a generated world."""
    hexes = [tile.to_dict() for tile in world_a.hexes]
    report = validate_world(hexes)
    assert report.ok, f"Validator violations: {report.violations}"


# ── CW12: Resources ───────────────────────────────────────────────────────────

def test_cw12_resource_profiles_contain_valid_resources(world_a):
    """CW12: resource profiles contain only canonical resource names."""
    for tile in world_a.hexes:
        bad = set(tile.resource_profile) - _VALID_RESOURCES
        assert not bad, f"{tile.hex_id}: unknown resources: {bad}"
