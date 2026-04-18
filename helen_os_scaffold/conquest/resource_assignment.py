"""
conquest/resource_assignment.py — Resource profiles from terrain + structure grants.

Invariants:
  - Only sets resource_profile; does not touch terrain, structure, overlay, or owner.
  - Does not assign sovereignty.
  - Deterministic.
"""
from __future__ import annotations

from typing import Any

from conquest.tiles import TERRAIN_REGISTRY, STRUCTURE_REGISTRY


def assign_resources(
    hex_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Assign resource_profile to each hex from terrain base_resources
    plus any structure grants_resources.

    Args:
        hex_map: Mutable {hex_id: cell_dict} with terrain + structures resolved.

    Returns:
        Updated hex_map.
    """
    for cell in hex_map.values():
        terrain   = cell.get("terrain", "PLAIN")
        structure = cell.get("structure")

        base = list(TERRAIN_REGISTRY.get(terrain, {}).get("base_resources", []))

        if structure and structure in STRUCTURE_REGISTRY:
            base += STRUCTURE_REGISTRY[structure].get("grants_resources", [])

        # Deduplicate and sort for determinism
        cell["resource_profile"] = sorted(set(base))

    return hex_map
