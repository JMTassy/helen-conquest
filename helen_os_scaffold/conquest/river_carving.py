"""
conquest/river_carving.py — Layer A: river/lake continuity.

Carves river corridors from high-elevation source tiles down to water.
Operates on the mutable hex_map dict.

Invariants:
  - Only modifies terrain field (to RIVER).
  - Does not set structure, overlay, owner, or receipt.
  - Deterministic: same seed → same river paths.
"""
from __future__ import annotations

import random
from typing import Any

from conquest.tiles import TERRAIN_REGISTRY
from conquest.hex_grid import axial_neighbors, hex_id as _hid


def carve_rivers(
    hex_map: dict[str, dict[str, Any]],
    seed: int,
    num_rivers: int | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Carve 1–3 river corridors from source tiles to coast/lake/sea.

    Args:
        hex_map:    Mutable {hex_id: cell_dict}.
        seed:       Seeded RNG.
        num_rivers: Override number of rivers (default: 1–3 seeded random).

    Returns:
        Updated hex_map.
    """
    rng = random.Random(seed + 1001)  # offset from terrain seed

    sources = [
        hid for hid, c in hex_map.items()
        if c.get("terrain") in ("HILL", "MOUNTAIN")
    ]
    if not sources:
        return hex_map

    n = num_rivers if num_rivers is not None else rng.randint(1, 3)
    n = min(n, len(sources))
    chosen = rng.sample(sources, n)

    for src_id in chosen:
        _flow_river(src_id, hex_map, rng)

    return hex_map


def _flow_river(
    start_id: str,
    hex_map: dict[str, dict[str, Any]],
    rng: random.Random,
    max_steps: int = 24,
) -> None:
    """
    Flow a river from start_id toward water.
    Marks each traversed cell as RIVER.
    """
    WATER_TERMINATION = {"COAST", "LAKE", "SEA"}
    current_id = start_id
    visited: set[str] = set()

    for _ in range(max_steps):
        if current_id in visited:
            break
        visited.add(current_id)

        cell = hex_map[current_id]
        cell["terrain"] = "RIVER"

        q, r = cell["q"], cell["r"]
        neighbors = []
        for nq, nr in axial_neighbors(q, r):
            nid = _hid(nq, nr)
            neighbor = hex_map.get(nid)
            if neighbor:
                neighbors.append((nid, neighbor))

        # Reached water — stop
        water = [n for n in neighbors if n[1].get("terrain") in WATER_TERMINATION]
        if water:
            break

        # Flow toward lower or equal elevation
        current_elev = TERRAIN_REGISTRY.get(cell["terrain"], {}).get("elevation", 0)
        candidates = []
        for nid, nc in neighbors:
            if nid in visited:
                continue
            nt = nc.get("terrain", "PLAIN")
            ne = TERRAIN_REGISTRY.get(nt, {}).get("elevation", 1)
            if ne <= current_elev:
                candidates.append(nid)

        if not candidates:
            break
        current_id = rng.choice(candidates)
