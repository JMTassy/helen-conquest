"""
conquest/adjacency.py — Terrain legality matrix + special constraints.

Sources: conquest_adjacency_matrix.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent
_ADJACENCY: dict[str, Any] = json.loads((_HERE / "conquest_adjacency_matrix.json").read_text())

# terrain → list of allowed adjacent terrains
TERRAIN_ADJACENCY: dict[str, list[str]] = _ADJACENCY["terrain_adjacency"]

# Special constraints (as spec objects, for validators)
SPECIAL_CONSTRAINTS: list[dict[str, str]] = _ADJACENCY["special_constraints"]


def legal_neighbors(terrain: str) -> set[str]:
    """Return the set of terrain types that may be adjacent to `terrain`."""
    return set(TERRAIN_ADJACENCY.get(terrain, []))


def is_legal_adjacency(terrain_a: str, terrain_b: str) -> bool:
    """Return True if terrain_b may appear adjacent to terrain_a."""
    return terrain_b in legal_neighbors(terrain_a)
