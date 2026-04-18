"""
conquest/hex_grid.py — Axial coordinate system + neighbor lookup.

Uses flat-top even-q offset layout → axial (q, r) internally.

Axial neighbor directions (cube coordinates):
  (+1,  0), (-1,  0)   — east / west
  ( 0, +1), ( 0, -1)   — north-east / south-west
  (+1, -1), (-1, +1)   — north-west / south-east
"""
from __future__ import annotations

from typing import Iterator

# 6 axial directions for flat-top hexagons
HEX_DIRECTIONS: list[tuple[int, int]] = [
    (1,  0), (-1,  0),
    (0,  1), ( 0, -1),
    (1, -1), (-1,  1),
]


def hex_id(q: int, r: int) -> str:
    """Canonical hex identifier from axial coordinates."""
    return f"H{q}_{r}"


def axial_neighbors(q: int, r: int) -> list[tuple[int, int]]:
    """Return the 6 axial neighbor coordinates of (q, r)."""
    return [(q + dq, r + dr) for dq, dr in HEX_DIRECTIONS]


def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """
    Hex distance in axial coordinates.
    distance = max(|dq|, |dr|, |dq + dr|) = (|dq| + |dr| + |dq + dr|) / 2
    """
    dq = q2 - q1
    dr = r2 - r1
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


def build_coord_map(width: int, height: int) -> dict[str, tuple[int, int]]:
    """
    Return mapping: hex_id → (q, r) for a width × height even-q grid.
    Uses even-q offset conversion to axial.
    """
    coords: dict[str, tuple[int, int]] = {}
    for col in range(width):
        for row in range(height):
            q = col
            r = row - (col - (col & 1)) // 2
            coords[hex_id(q, r)] = (q, r)
    return coords


def iter_grid(width: int, height: int) -> Iterator[tuple[int, int]]:
    """Yield (q, r) axial coordinates for all cells in a width × height even-q grid."""
    for col in range(width):
        for row in range(height):
            q = col
            r = row - (col - (col & 1)) // 2
            yield q, r


def neighbor_ids_in_bounds(
    q: int, r: int, coord_set: set[str]
) -> list[str]:
    """
    Return hex_ids of neighbors of (q, r) that exist in coord_set.
    """
    result = []
    for nq, nr in axial_neighbors(q, r):
        nid = hex_id(nq, nr)
        if nid in coord_set:
            result.append(nid)
    return result
