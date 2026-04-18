"""
conquest/structure_placement.py — Layer B: habitation and strongholds.

Places structures on legal terrain tiles.
Does not set ownership, overlays, or receipts.

Invariants:
  - Respects structure_registry.allowed_on.
  - Does not set owner_house_id.
  - Does not set CLAIMED or any sovereign overlay.
  - Deterministic: same seed → same structure positions.
"""
from __future__ import annotations

import random
from typing import Any

from conquest.tiles import STRUCTURE_REGISTRY


def place_structures(
    hex_map: dict[str, dict[str, Any]],
    seed: int,
) -> dict[str, dict[str, Any]]:
    """
    Place structures on legal terrain tiles.

    Each structure type is placed on 1–3 eligible tiles (seeded random).
    Tiles that already have a structure are skipped.

    Args:
        hex_map: Mutable {hex_id: cell_dict} with terrain resolved.
        seed:    Integer seed.

    Returns:
        Updated hex_map.
    """
    rng = random.Random(seed + 2001)

    # Build terrain → eligible tile index
    terrain_tiles: dict[str, list[str]] = {}
    for hid, cell in hex_map.items():
        t = cell.get("terrain", "PLAIN")
        terrain_tiles.setdefault(t, []).append(hid)

    for struct_name, spec in STRUCTURE_REGISTRY.items():
        candidates = [
            hid
            for t in spec["allowed_on"]
            for hid in terrain_tiles.get(t, [])
            if hex_map[hid].get("structure") is None
        ]
        if not candidates:
            continue

        count = rng.randint(1, 3)
        chosen = rng.sample(candidates, min(count, len(candidates)))
        for hid in chosen:
            hex_map[hid]["structure"] = struct_name

    return hex_map
