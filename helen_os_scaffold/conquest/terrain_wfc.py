"""
conquest/terrain_wfc.py — Layer A: terrain substrate solver.

Implements a seeded-random greedy WFC pass with neighbor-compatibility
checking. Returns deterministic terrain assignment and repair events.

Boundary invariants:
  - Knows nothing about claims, Houses, duels, or Senate.
  - Assigns only terrain; does not set structure, overlay, or owner.
  - Deterministic: same seed → same terrain output.
"""
from __future__ import annotations

import random
from typing import Any

from conquest.adjacency import legal_neighbors, TERRAIN_ADJACENCY
from conquest.tiles import TERRAIN_REGISTRY, VALID_TERRAINS

# Terrains available for the initial random collapse
# (VOID is map-border only; not placed during generation)
_PLACEABLE = [t for t in VALID_TERRAINS if t not in ("VOID",)]

# Terrains preferred for interior cells (not coast/sea)
_INTERIOR = [t for t in _PLACEABLE if t not in ("SEA", "COAST", "RIVER", "BRIDGE")]


def terrain_wfc(
    hex_map: dict[str, dict[str, Any]],
    seed: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """
    Deterministic terrain assignment via seeded greedy WFC.

    Args:
        hex_map: {hex_id: {q, r, ...}} — cells with unresolved terrain.
        seed:    Integer seed.

    Returns:
        (updated_hex_map, repair_events)
        updated_hex_map: same keys, terrain + generation_entropy set.
        repair_events:   list of {"hex_id", "reason", "resolved_to"} dicts.
    """
    rng = random.Random(seed)
    repair_events: list[dict[str, Any]] = []

    # Collapse in shuffled order (seeded)
    order = list(hex_map.keys())
    rng.shuffle(order)

    for hid in order:
        cell      = hex_map[hid]
        q, r      = cell["q"], cell["r"]

        # Collect neighbor terrains already solved
        solved_neighbor_terrains = _solved_neighbor_terrains(hid, hex_map)

        terrain, repaired = _choose_terrain(hid, solved_neighbor_terrains, rng)

        if repaired:
            repair_events.append({
                "hex_id":      hid,
                "reason":      "contradiction_recovery",
                "resolved_to": terrain,
            })

        cell["terrain"]             = terrain
        cell["generation_entropy"]  = rng.random()

    return hex_map, repair_events


def _solved_neighbor_terrains(
    hid: str,
    hex_map: dict[str, dict[str, Any]],
) -> list[str]:
    """Return terrain values of already-solved neighbors."""
    from conquest.hex_grid import axial_neighbors, hex_id as _hid
    cell = hex_map[hid]
    result = []
    for nq, nr in axial_neighbors(cell["q"], cell["r"]):
        nid = _hid(nq, nr)
        neighbor = hex_map.get(nid)
        if neighbor and neighbor.get("terrain"):
            result.append(neighbor["terrain"])
    return result


def _choose_terrain(
    hid: str,
    solved_neighbor_terrains: list[str],
    rng: random.Random,
) -> tuple[str, bool]:
    """
    Choose a terrain compatible with solved neighbors.

    Returns (terrain_str, repaired).
    repaired=True means no fully-compatible terrain existed and
    PLAIN was used as a neutral connector (Tier 2 repair).
    """
    if not solved_neighbor_terrains:
        # No solved neighbors: pick from interior pool
        return rng.choice(_INTERIOR), False

    # Intersect legal neighbors of each solved neighbor
    legal: set[str] = set(_PLACEABLE)
    for nt in solved_neighbor_terrains:
        allowed = legal_neighbors(nt)
        if allowed:
            legal &= allowed

    legal.discard("VOID")

    if not legal:
        # Contradiction: fall back to PLAIN (Tier 2 neutral connector)
        return "PLAIN", True

    return rng.choice(sorted(legal)), False
