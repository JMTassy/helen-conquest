"""
SeedWorldLoader — Registry and loader for HELEN OS seed worlds.

Usage:
  world = SeedWorldLoader.load("conquest_land", kernel=kernel, world_seed=42)
  receipts = world.tick(0)

To register a new seed world, add it to REGISTRY below.
"""

from typing import Any, Dict, List, Optional, Type
from .base_world import BaseWorld


class SeedWorldLoader:
    """
    Central registry for seed worlds.
    Each entry maps world_id → (WorldClass, metadata).
    Import is lazy — worlds are only loaded when requested.
    """

    # ── Registry ──────────────────────────────────────────────────────────────
    # Format: "world_id": ("module.path", "ClassName")
    # Module path is relative to helen_os.seeds.worlds
    REGISTRY: Dict[str, Dict[str, str]] = {
        "conquest_land": {
            "module": "helen_os.seeds.worlds.conquest_land",
            "class": "ConquestLandWorld",
            "version": "0.1.0",
            "description": "CONQUEST LAND — federation testbed with 10 factions and 6 sovereign towns.",
        },
        "wild_town": {
            "module": "helen_os.seeds.worlds.wild_town",
            "class": "WildTownWorld",
            "version": "0.1.0",
            "description": (
                "ORACLE CREATIVE WILD TOWN — ephemeral inspiration sandbox. "
                "All ideas shippable=False. HAL blocks 100%. Safe zone for lateral thinking."
            ),
        },
    }

    @classmethod
    def list_worlds(cls) -> List[Dict[str, str]]:
        """Return metadata for all registered seed worlds."""
        return [
            {
                "id": world_id,
                "version": meta["version"],
                "description": meta["description"],
            }
            for world_id, meta in cls.REGISTRY.items()
        ]

    @classmethod
    def load(
        cls,
        world_id: str,
        kernel: Any,
        world_seed: int = 42,
    ) -> BaseWorld:
        """
        Instantiate and return a seed world by ID.
        Raises KeyError if world_id is not registered.
        """
        if world_id not in cls.REGISTRY:
            raise KeyError(
                f"Unknown seed world: '{world_id}'. "
                f"Available: {list(cls.REGISTRY.keys())}"
            )

        entry = cls.REGISTRY[world_id]
        import importlib
        module = importlib.import_module(entry["module"])
        WorldClass: Type[BaseWorld] = getattr(module, entry["class"])
        return WorldClass(kernel=kernel, world_seed=world_seed)

    @classmethod
    def register(
        cls,
        world_id: str,
        module_path: str,
        class_name: str,
        version: str = "0.1.0",
        description: str = "",
    ) -> None:
        """
        Register a new seed world at runtime.
        Allows external plugins to add worlds without modifying this file.
        """
        cls.REGISTRY[world_id] = {
            "module": module_path,
            "class": class_name,
            "version": version,
            "description": description,
        }
