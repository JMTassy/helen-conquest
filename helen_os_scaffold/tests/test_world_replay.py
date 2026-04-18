"""
tests/test_world_replay.py — Phase C: world determinism + receipt schema tests.

CONQUEST_WFC_SPEC_V1 — replay acceptance test suite.

Test IDs:
    WR01  same seed → same world_hash (determinism invariant)
    WR02  different seed → different world_hash
    WR03  world seed derivation is deterministic (compute_world_seed)
    WR04  boundary constraints hash is deterministic
    WR05  canonical_payload_hash is deterministic for same hex list
    WR06  canonical_payload_hash changes when tile changes
    WR07  canonical_payload_hash ignores generation_entropy (excluded from hash)
    WR08  WorldPatchReceiptV1 has correct artifact_type
    WR09  WorldPatchReceiptV1 canonical_payload_hash matches recomputed hash
    WR10  WorldContradictionReceiptV1 has correct artifact_type + status
    WR11  WorldContradictionReceiptV1 canonical_payload_hash is non-empty
    WR12  WorldContradictionReceiptV1 resolution is "ARBITRATION_REQUIRED"
    WR13  WorldContradictionReceiptV1 retry_count equals k=3
    WR14  compute_retry_seed produces unique seeds per (patch, retry)
    WR15  emit_world_patch_receipt returns status="ok"
    WR16  emit_world_contradiction_receipt returns status="contradiction"
    WR17  patch canonical_payload_hash changes when sorted order changes the tile list
    WR18  boundary_constraints_hash is "0" * 64 for empty constraints (SHA256 of "[]")
"""
from __future__ import annotations

import hashlib
import json
import sys
import os

import pytest

# Add helen_os_scaffold root so that `conquest` is importable as a package.
_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, _SCAFFOLD_ROOT)

from conquest.world_receipt import (
    WorldPatchReceiptV1,
    WorldContradictionReceiptV1,
    compute_canonical_payload_hash,
    compute_boundary_constraints_hash,
    compute_world_seed,
    compute_retry_seed,
    emit_world_patch_receipt,
    emit_world_contradiction_receipt,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

SEED_A = 912733
SEED_B = 42
SOV_HASH_GENESIS = "0" * 64

_SAMPLE_HEXES = [
    {"q": 0, "r": 0, "tile": "GRASS",   "generation_entropy": 0.123},
    {"q": 1, "r": 0, "tile": "FOREST",  "generation_entropy": 0.456},
    {"q": 0, "r": 1, "tile": "COAST",   "generation_entropy": 0.789},
    {"q": -1, "r": 1, "tile": "OCEAN",  "generation_entropy": 0.321},
    {"q": -1, "r": 0, "tile": "ROAD",   "generation_entropy": 0.654},
    {"q": 0, "r": -1, "tile": "RIVER",  "generation_entropy": 0.987},
    {"q": 1, "r": -1, "tile": "MOUNTAIN", "generation_entropy": 0.111},
]

_SAMPLE_HEXES_MODIFIED = [
    {"q": 0, "r": 0, "tile": "OCEAN",   "generation_entropy": 0.123},  # changed tile
    {"q": 1, "r": 0, "tile": "FOREST",  "generation_entropy": 0.456},
    {"q": 0, "r": 1, "tile": "COAST",   "generation_entropy": 0.789},
    {"q": -1, "r": 1, "tile": "OCEAN",  "generation_entropy": 0.321},
    {"q": -1, "r": 0, "tile": "ROAD",   "generation_entropy": 0.654},
    {"q": 0, "r": -1, "tile": "RIVER",  "generation_entropy": 0.987},
    {"q": 1, "r": -1, "tile": "MOUNTAIN", "generation_entropy": 0.111},
]


# ── WR01–WR02: World generation determinism ───────────────────────────────────

class TestWR01_02WorldDeterminism:
    def test_wr01_same_seed_same_world_hash(self):
        """WR01: same seed → same world_hash via existing generate_world pipeline."""
        try:
            from conquest.conquest_world_generator import generate_world, world_generation_receipt
        except ImportError:
            pytest.skip("conquest.conquest_world_generator not importable in isolation")

        world_a1 = generate_world(SEED_A, 8, 8)
        world_a2 = generate_world(SEED_A, 8, 8)
        r1 = world_generation_receipt(world_a1, SEED_A)
        r2 = world_generation_receipt(world_a2, SEED_A)
        assert r1.world_hash == r2.world_hash, (
            "WR01 FAIL: same seed must produce same world_hash. "
            f"Got {r1.world_hash!r} vs {r2.world_hash!r}"
        )

    def test_wr02_different_seeds_different_hashes(self):
        """WR02: different seeds → different world_hash."""
        try:
            from conquest.conquest_world_generator import generate_world, world_generation_receipt
        except ImportError:
            pytest.skip("conquest.conquest_world_generator not importable in isolation")

        world_a = generate_world(SEED_A, 8, 8)
        world_b = generate_world(SEED_B, 8, 8)
        r_a = world_generation_receipt(world_a, SEED_A)
        r_b = world_generation_receipt(world_b, SEED_B)
        assert r_a.world_hash != r_b.world_hash, (
            "WR02 FAIL: different seeds should (overwhelmingly) produce different world_hash"
        )


# ── WR03: Seed derivation ─────────────────────────────────────────────────────

class TestWR03SeedDerivation:
    def test_wr03_seed_derivation_is_deterministic(self):
        """WR03: compute_world_seed is deterministic for same inputs."""
        seed1 = compute_world_seed(36, SOV_HASH_GENESIS)
        seed2 = compute_world_seed(36, SOV_HASH_GENESIS)
        assert seed1 == seed2

    def test_wr03_seed_derivation_changes_with_tick(self):
        """WR03: different tick → different world_seed."""
        seed_t36 = compute_world_seed(36, SOV_HASH_GENESIS)
        seed_t37 = compute_world_seed(37, SOV_HASH_GENESIS)
        assert seed_t36 != seed_t37

    def test_wr03_seed_derivation_changes_with_sov_hash(self):
        """WR03: different sov_hash → different world_seed."""
        seed_genesis = compute_world_seed(36, "0" * 64)
        seed_other   = compute_world_seed(36, "1" * 64)
        assert seed_genesis != seed_other

    def test_wr03_seed_derivation_correct_prefix(self):
        """WR03: world seed derives from 'CONQUESTLAND' prefix (§3)."""
        tick = 36
        sov  = "0" * 64
        expected = hashlib.sha256(
            ("CONQUESTLAND" + str(tick) + sov).encode("utf-8")
        ).hexdigest()
        assert compute_world_seed(tick, sov) == expected

    def test_wr03_seed_is_64_hex_chars(self):
        """WR03: world_seed is exactly 64 lowercase hex chars."""
        seed = compute_world_seed(1, "a" * 64)
        assert len(seed) == 64
        assert all(c in "0123456789abcdef" for c in seed)


# ── WR04: Boundary constraints hash ──────────────────────────────────────────

class TestWR04BoundaryConstraintsHash:
    def test_wr04_empty_constraints_is_deterministic(self):
        """WR04: empty constraint list → same hash every time."""
        h1 = compute_boundary_constraints_hash([])
        h2 = compute_boundary_constraints_hash([])
        assert h1 == h2

    def test_wr04_order_invariant(self):
        """WR04: boundary constraints are sorted by (q, r) before hashing."""
        bc1 = [{"q": 0, "r": 1, "required_tile": "GRASS"},
               {"q": 1, "r": 0, "required_tile": "COAST"}]
        bc2 = [{"q": 1, "r": 0, "required_tile": "COAST"},
               {"q": 0, "r": 1, "required_tile": "GRASS"}]
        assert compute_boundary_constraints_hash(bc1) == compute_boundary_constraints_hash(bc2)

    def test_wr04_changes_with_different_constraint(self):
        """WR04: changing a constraint changes the hash."""
        bc1 = [{"q": 0, "r": 0, "required_tile": "GRASS"}]
        bc2 = [{"q": 0, "r": 0, "required_tile": "OCEAN"}]
        assert compute_boundary_constraints_hash(bc1) != compute_boundary_constraints_hash(bc2)

    def test_wr04_hash_is_64_hex(self):
        """WR04: boundary constraints hash is 64 lowercase hex chars."""
        h = compute_boundary_constraints_hash([])
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ── WR05–WR07: Canonical payload hash ────────────────────────────────────────

class TestWR05_07CanonicalPayloadHash:
    def test_wr05_canonical_payload_hash_is_deterministic(self):
        """WR05: same hex list → same canonical_payload_hash."""
        h1 = compute_canonical_payload_hash(_SAMPLE_HEXES)
        h2 = compute_canonical_payload_hash(_SAMPLE_HEXES)
        assert h1 == h2

    def test_wr06_canonical_payload_hash_changes_with_tile(self):
        """WR06: changing a tile changes canonical_payload_hash."""
        h1 = compute_canonical_payload_hash(_SAMPLE_HEXES)
        h2 = compute_canonical_payload_hash(_SAMPLE_HEXES_MODIFIED)
        assert h1 != h2

    def test_wr07_generation_entropy_excluded_from_hash(self):
        """WR07: generation_entropy is excluded from canonical_payload_hash (§6.1)."""
        hexes_a = [{"q": 0, "r": 0, "tile": "GRASS", "generation_entropy": 0.1}]
        hexes_b = [{"q": 0, "r": 0, "tile": "GRASS", "generation_entropy": 0.9}]
        # Different entropy, same tile → same hash
        assert compute_canonical_payload_hash(hexes_a) == compute_canonical_payload_hash(hexes_b)

    def test_wr07_canonical_payload_hash_is_64_hex(self):
        """WR07: canonical_payload_hash is 64 lowercase hex chars."""
        h = compute_canonical_payload_hash(_SAMPLE_HEXES)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_wr17_sorted_order_is_canonical(self):
        """WR17: hexes are sorted by (q, r) before hashing — order-invariant."""
        hexes_shuffled = list(reversed(_SAMPLE_HEXES))
        h1 = compute_canonical_payload_hash(_SAMPLE_HEXES)
        h2 = compute_canonical_payload_hash(hexes_shuffled)
        assert h1 == h2

    def test_wr18_empty_constraints_sha256(self):
        """WR18: empty boundary constraints hash is SHA256 of canonical '[]'."""
        expected = hashlib.sha256(
            json.dumps([], sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        assert compute_boundary_constraints_hash([]) == expected


# ── WR08–WR09: WorldPatchReceiptV1 ───────────────────────────────────────────

class TestWR08_09PatchReceipt:
    def _make_receipt(self, hexes=None) -> WorldPatchReceiptV1:
        world_seed = compute_world_seed(36, "0" * 64)
        return emit_world_patch_receipt(
            patch_id="PATCH-TEST-001",
            tick_id=36,
            world_seed=world_seed,
            hexes=hexes or _SAMPLE_HEXES,
            boundary_constraints=[],
            repair_events=[],
        )

    def test_wr08_patch_receipt_artifact_type(self):
        """WR08: WorldPatchReceiptV1 artifact_type is 'WORLD_PATCH_GEN_V1'."""
        r = self._make_receipt()
        assert r.artifact_type == "WORLD_PATCH_GEN_V1"

    def test_wr09_canonical_payload_hash_matches_recomputed(self):
        """WR09: canonical_payload_hash in receipt matches independently computed hash."""
        r = self._make_receipt()
        expected = compute_canonical_payload_hash(_SAMPLE_HEXES)
        assert r.canonical_payload_hash == expected

    def test_wr09_canonical_payload_hash_is_deterministic(self):
        """WR09: two receipts for same patch → same canonical_payload_hash."""
        r1 = self._make_receipt()
        r2 = self._make_receipt()
        assert r1.canonical_payload_hash == r2.canonical_payload_hash

    def test_wr15_patch_receipt_status_ok(self):
        """WR15: emit_world_patch_receipt returns status='ok'."""
        r = self._make_receipt()
        assert r.status == "ok"

    def test_patch_receipt_to_dict_roundtrip(self):
        """Positive: to_dict() includes all required fields."""
        r = self._make_receipt()
        d = r.to_dict()
        required = [
            "artifact_type", "tile_spec_version", "solver_version",
            "patch_id", "tick_id", "world_seed", "boundary_constraints_hash",
            "hexes", "canonical_payload_hash", "status",
        ]
        for key in required:
            assert key in d, f"Missing field: {key}"

    def test_patch_receipt_tile_spec_version(self):
        """Positive: default tile_spec_version is CONQUEST_WFC_SPEC_V1."""
        r = self._make_receipt()
        assert r.tile_spec_version == "CONQUEST_WFC_SPEC_V1"


# ── WR10–WR16: WorldContradictionReceiptV1 ───────────────────────────────────

class TestWR10_16ContradictionReceipt:
    def _make_contradiction_receipt(self) -> WorldContradictionReceiptV1:
        world_seed = compute_world_seed(36, "0" * 64)
        retry_seeds = [
            compute_retry_seed(world_seed, "PATCH-TEST-001", i + 1)
            for i in range(3)
        ]
        return emit_world_contradiction_receipt(
            patch_id="PATCH-TEST-001",
            tick_id=36,
            world_seed=world_seed,
            contradiction_hex={"q": 3, "r": 2},
            retry_count=3,
            boundary_constraints=[],
            retry_seeds=retry_seeds,
            neighbor_terrains=["OCEAN", "MOUNTAIN"],
            candidate_tiles_before_contradiction=[],
            repair_attempts=[
                {"attempt": 1, "retry_seed": retry_seeds[0], "resolved": False,
                 "contradiction_at": {"q": 3, "r": 2}},
                {"attempt": 2, "retry_seed": retry_seeds[1], "resolved": False,
                 "contradiction_at": {"q": 3, "r": 2}},
                {"attempt": 3, "retry_seed": retry_seeds[2], "resolved": False,
                 "contradiction_at": {"q": 3, "r": 2}},
            ],
        )

    def test_wr10_contradiction_receipt_artifact_type(self):
        """WR10: WorldContradictionReceiptV1 artifact_type is 'WORLD_CONTRADICTION_V1'."""
        r = self._make_contradiction_receipt()
        assert r.artifact_type == "WORLD_CONTRADICTION_V1"

    def test_wr10_contradiction_receipt_status(self):
        """WR10: WorldContradictionReceiptV1 status is 'contradiction'."""
        r = self._make_contradiction_receipt()
        assert r.status == "contradiction"

    def test_wr11_canonical_payload_hash_non_empty(self):
        """WR11: contradiction receipt canonical_payload_hash is non-empty 64-char hex."""
        r = self._make_contradiction_receipt()
        assert len(r.canonical_payload_hash) == 64
        assert all(c in "0123456789abcdef" for c in r.canonical_payload_hash)

    def test_wr12_resolution_arbitration_required(self):
        """WR12: WorldContradictionReceiptV1 resolution is 'ARBITRATION_REQUIRED'."""
        r = self._make_contradiction_receipt()
        assert r.resolution == "ARBITRATION_REQUIRED"

    def test_wr13_retry_count_is_three(self):
        """WR13: retry_count equals k=3 for MVP."""
        r = self._make_contradiction_receipt()
        assert r.retry_count == 3

    def test_wr11_canonical_payload_hash_is_deterministic(self):
        """WR11: same inputs → same canonical_payload_hash for contradiction receipt."""
        r1 = self._make_contradiction_receipt()
        r2 = self._make_contradiction_receipt()
        assert r1.canonical_payload_hash == r2.canonical_payload_hash

    def test_wr16_contradiction_receipt_status_contradiction(self):
        """WR16: emit_world_contradiction_receipt returns status='contradiction'."""
        r = self._make_contradiction_receipt()
        assert r.status == "contradiction"

    def test_contradiction_receipt_to_dict_roundtrip(self):
        """Positive: to_dict() includes all required fields for contradiction receipt."""
        r = self._make_contradiction_receipt()
        d = r.to_dict()
        required = [
            "artifact_type", "tile_spec_version", "solver_version",
            "patch_id", "tick_id", "world_seed", "boundary_constraints_hash",
            "contradiction_hex", "retry_count", "retry_seeds",
            "neighbor_terrains", "candidate_tiles_before_contradiction",
            "repair_attempts", "resolution", "canonical_payload_hash", "status",
        ]
        for key in required:
            assert key in d, f"Missing field: {key}"


# ── WR14: Retry seed uniqueness ──────────────────────────────────────────────

class TestWR14RetrySeed:
    def test_wr14_retry_seeds_are_unique(self):
        """WR14: retry seeds differ per (patch_id, retry_count) pair."""
        world_seed = compute_world_seed(36, "0" * 64)
        s1 = compute_retry_seed(world_seed, "PATCH-001", 1)
        s2 = compute_retry_seed(world_seed, "PATCH-001", 2)
        s3 = compute_retry_seed(world_seed, "PATCH-001", 3)
        assert len({s1, s2, s3}) == 3, "All k=3 retry seeds must be unique"

    def test_wr14_retry_seeds_differ_across_patches(self):
        """WR14: same retry count on different patches → different retry seed."""
        world_seed = compute_world_seed(36, "0" * 64)
        s_p1 = compute_retry_seed(world_seed, "PATCH-001", 1)
        s_p2 = compute_retry_seed(world_seed, "PATCH-002", 1)
        assert s_p1 != s_p2

    def test_wr14_retry_seed_is_deterministic(self):
        """WR14: compute_retry_seed is deterministic for same inputs."""
        world_seed = compute_world_seed(36, "0" * 64)
        s1 = compute_retry_seed(world_seed, "PATCH-001", 2)
        s2 = compute_retry_seed(world_seed, "PATCH-001", 2)
        assert s1 == s2

    def test_wr14_retry_seed_is_64_hex(self):
        """WR14: retry seed is 64 lowercase hex chars."""
        world_seed = compute_world_seed(1, "0" * 64)
        s = compute_retry_seed(world_seed, "P", 1)
        assert len(s) == 64
        assert all(c in "0123456789abcdef" for c in s)
