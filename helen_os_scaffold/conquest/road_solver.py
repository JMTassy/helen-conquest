"""
conquest/road_solver.py — Layer B: infrastructure pass.

Connects major settlements (TOWN, CITY, CASTLE) with ROAD corridors.

Note: ROAD and BRIDGE are kept in Layer A (terrain) for V0_1.
V0_2 TODO: move to a separate infrastructure layer between terrain and
structure to enforce cleaner geology/infrastructure separation.

Invariants:
  - Only modifies terrain on passable non-water tiles.
  - Does not set structure, overlay, or owner.
  - Deterministic: same seed → same road network.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Any

from conquest.tiles import TERRAIN_REGISTRY
from conquest.hex_grid import axial_neighbors, hex_id as _hid


_ANCHOR_STRUCTURES = {"TOWN", "CITY", "CASTLE"}


def solve_roads(
    hex_map: dict[str, dict[str, Any]],
    seed: int,
) -> dict[str, dict[str, Any]]:
    """
    Connect pairs of major settlements with ROAD corridors.

    Args:
        hex_map: Mutable {hex_id: cell_dict} with structures placed.
        seed:    Integer seed.

    Returns:
        Updated hex_map.
    """
    rng = random.Random(seed + 3001)

    anchors = [
        hid for hid, c in hex_map.items()
        if c.get("structure") in _ANCHOR_STRUCTURES
    ]
    if len(anchors) < 2:
        return hex_map

    # Shuffle anchors and connect consecutive pairs
    rng.shuffle(anchors)
    for i in range(len(anchors) - 1):
        _road_between(anchors[i], anchors[i + 1], hex_map)

    return hex_map


def _road_between(
    src_id: str,
    dst_id: str,
    hex_map: dict[str, dict[str, Any]],
) -> None:
    """
    BFS from src_id to dst_id through passable tiles.
    Marks traversed tiles (excluding anchors) as ROAD.
    """
    visited: dict[str, str | None] = {src_id: None}
    queue: deque[str] = deque([src_id])

    while queue:
        current_id = queue.popleft()
        if current_id == dst_id:
            break

        cell = hex_map[current_id]
        for nq, nr in axial_neighbors(cell["q"], cell["r"]):
            nid = _hid(nq, nr)
            if nid in visited or nid not in hex_map:
                continue
            nc = hex_map[nid]
            info = TERRAIN_REGISTRY.get(nc.get("terrain", ""), {})
            if not info.get("passable", False):
                continue
            visited[nid] = current_id
            queue.append(nid)

    # Trace path back from dst to src
    path: list[str] = []
    cursor: str | None = dst_id
    while cursor and cursor in visited:
        path.append(cursor)
        cursor = visited[cursor]

    # Mark path as ROAD (skip src and dst anchors)
    for hid in path[1:-1]:
        cell = hex_map[hid]
        if cell.get("terrain") not in ("ROAD", "BRIDGE", "COAST", "RIVER"):
            cell["terrain"] = "ROAD"
