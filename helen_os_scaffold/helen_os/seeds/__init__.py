"""
HELEN OS — Seed World Framework
================================
A seed world is a deterministic simulation that runs ON TOP of HELEN OS.
It uses the GovernanceVM kernel for receipts but is NOT the kernel itself.

Architecture:
  HELEN OS kernel  (sovereign — issues receipts)
      └── SeedWorld  (non-sovereign simulation — proposes evidence)
              └── Factions  (deterministic agents — produce observations)
              └── Towns     (local ledger reducers — admit receipts)

Seed worlds are pluggable. Register them in SeedWorldLoader.REGISTRY.
"""

from .base_world import BaseWorld
from .loader import SeedWorldLoader

__all__ = ["BaseWorld", "SeedWorldLoader"]
