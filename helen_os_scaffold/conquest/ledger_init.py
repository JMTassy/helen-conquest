"""
conquest/ledger_init.py — Layer C: initialize lawful non-sovereign overlays.

This module is the ONLY place that sets overlays during worldgen.
It ONLY assigns UNCLAIMED or CLAIMABLE.

Boundary invariant:
  - ledger_init.py knows nothing about WFC contradiction recovery.
  - CLAIMED, FORTIFIED, SEALED, RESOURCE_LOCKED, DUEL_PENDING
    are NEVER set here. They require receipts and appear only
    after player/faction actions.

Hard invariant (from HARD_INVARIANTS):
  NO_RECEIPT_NO_CLAIMED / NO_RECEIPT_NO_FORTIFIED / NO_RECEIPT_NO_SEALED
  NO_RECEIPT_NO_RESOURCE_LOCKED / NO_RECEIPT_NO_DUEL_PENDING
"""
from __future__ import annotations

from typing import Any

from conquest.tiles import SOVEREIGN_OVERLAYS


def init_ledger_overlays(
    hex_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Initialize overlays to UNCLAIMED or CLAIMABLE based on tile eligibility.

    Rules:
      VOID         → []           (no overlay — VOID is non-tile)
      SEA          → UNCLAIMED    (not claimable without special receipt)
      impassable   → UNCLAIMED    (passable=False land tiles)
      passable     → CLAIMABLE    (open to territory claims)

    Args:
        hex_map: Mutable {hex_id: cell_dict} with terrain resolved.

    Returns:
        Updated hex_map with overlay initialized on each cell.
    """
    from conquest.tiles import TERRAIN_REGISTRY

    for cell in hex_map.values():
        terrain = cell.get("terrain", "PLAIN")
        t_info  = TERRAIN_REGISTRY.get(terrain, {})

        if terrain == "VOID":
            overlay = []
        elif terrain == "SEA" or not t_info.get("passable", False):
            overlay = ["UNCLAIMED"]
        else:
            overlay = ["CLAIMABLE"]

        # Guard: never assign sovereign overlays during generation
        overlay = [o for o in overlay if o not in SOVEREIGN_OVERLAYS]

        cell["overlay"]        = overlay
        cell["owner_house_id"] = None      # always null at generation time
        cell["receipt_hash"]   = None      # null until a receipt operation

    return hex_map
