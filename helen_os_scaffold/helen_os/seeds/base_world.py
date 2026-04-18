"""
BaseWorld — Abstract seed world contract.

Every seed world MUST implement:
  - world_id: str          unique identifier
  - version: str           semver
  - description: str       one-line description
  - tick(t: int) -> list   advance world by one tick, return receipt dicts

The world receives a GovernanceVM kernel reference at load time.
It MAY propose payloads to the kernel (evidence → receipts).
It MUST NOT modify the kernel's ledger directly.
It MUST be deterministic given world_seed + t.
"""

import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseWorld(ABC):
    """
    Abstract base for all HELEN OS seed worlds.

    A seed world is a non-sovereign deterministic simulation.
    It proposes evidence to the HELEN OS kernel; the kernel issues receipts.
    The world never seals, never mints authority, never modifies the kernel directly.
    """

    world_id: str = "base_world"
    version: str = "0.0.0"
    description: str = "Abstract seed world."

    def __init__(self, kernel, world_seed: int = 42):
        self.kernel = kernel           # GovernanceVM — read receipts, propose payloads
        self.world_seed = world_seed   # Deterministic PRF root
        self.tick_count = 0

    # ── Deterministic PRF ────────────────────────────────────────────────────

    def prf(self, faction_id: str, t: int, context: str = "", k: Optional[int] = None) -> int:
        """
        Deterministic pseudo-random function.
        r = SHA256(world_seed || faction_id || t || context)
        If k is given, returns r mod k. Else returns the full int.
        """
        raw = f"{self.world_seed}|{faction_id}|{t}|{context}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        value = int(digest, 16)
        return value % k if k is not None else value

    # ── Kernel interface ─────────────────────────────────────────────────────

    def propose(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Propose a payload to the GovernanceVM kernel.
        Returns a dict summary of the receipt (id, cum_hash, timestamp).
        Non-sovereign: the kernel issues the receipt; the world only proposes.
        """
        receipt = self.kernel.propose(payload)
        return {
            "receipt_id": receipt.id,
            "cum_hash": receipt.cum_hash,
            "timestamp": receipt.timestamp,
            "payload_hash": receipt.payload_hash,
        }

    # ── Tick interface ────────────────────────────────────────────────────────

    @abstractmethod
    def tick(self, t: int) -> List[Dict[str, Any]]:
        """
        Advance world state by one tick.
        Returns list of receipt dicts emitted this tick.
        Must be deterministic: same world_seed + t → same receipts.
        """
        raise NotImplementedError

    # ── Info ─────────────────────────────────────────────────────────────────

    def info(self) -> Dict[str, Any]:
        return {
            "world_id": self.world_id,
            "version": self.version,
            "description": self.description,
            "world_seed": self.world_seed,
            "tick_count": self.tick_count,
        }
