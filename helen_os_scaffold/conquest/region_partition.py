"""
conquest/region_partition.py — Geography metadata: 6 canonical regions.

Uses Voronoi-style seeded assignment from random centroids.
No sovereignty. No receipts.

Invariants:
  - Assigns region_id only; does not touch terrain, structure, overlay, or owner.
  - Deterministic: same seed → same region assignment.
"""
from __future__ import annotations

import random
from typing import Any

from conquest.tiles import REGIONS
from conquest.hex_grid import axial_distance


def assign_regions(
    hex_map: dict[str, dict[str, Any]],
    seed: int,
) -> dict[str, dict[str, Any]]:
    """
    Assign each hex to one of the 6 canonical regions.

    Picks one centroid per region from non-void, non-sea tiles,
    then assigns each cell to its nearest centroid.

    Args:
        hex_map: Mutable {hex_id: cell_dict}.
        seed:    Integer seed.

    Returns:
        Updated hex_map with region_id set on each cell.
    """
    rng = random.Random(seed + 4001)

    eligible = [
        (hid, c)
        for hid, c in hex_map.items()
        if c.get("terrain") not in ("VOID", "SEA")
    ]
    if not eligible:
        # Fallback: assign everything to first region
        for cell in hex_map.values():
            cell["region_id"] = REGIONS[0]
        return hex_map

    pool = list(eligible)
    rng.shuffle(pool)

    # One centroid per region
    centroids: dict[str, dict[str, Any]] = {}
    for region in REGIONS:
        if pool:
            _, centroid_cell = pool.pop()
            centroids[region] = centroid_cell

    # Assign nearest centroid
    for hid, cell in hex_map.items():
        if not centroids:
            cell["region_id"] = REGIONS[0]
            continue
        nearest = min(
            centroids.items(),
            key=lambda kv: axial_distance(
                cell["q"], cell["r"],
                kv[1]["q"], kv[1]["r"],
            ),
        )
        cell["region_id"] = nearest[0]

    return hex_map
