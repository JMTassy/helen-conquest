#!/usr/bin/env python3
"""
NPC Observer: Generates observations without authority.

Forbidden semantics: should, must, recommend, advise, coordinate, align.
Constraint: Cannot reference other NPCs or aggregate across towns.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional


FORBIDDEN_VERBS = {
    "should", "must", "recommend", "advise", "coordinate", "align",
    "best", "optimal", "better", "adopt", "follow", "copy", "pattern",
}


class NPCValidator:
    """Syntax validator for NPC observations."""

    @staticmethod
    def check_forbidden_verbs(statement: str) -> bool:
        """Return True if statement is clean (no forbidden verbs)."""
        words = statement.lower().split()
        return not any(verb in words for verb in FORBIDDEN_VERBS)

    @staticmethod
    def check_no_cross_town_reference(statement: str, town_names: List[str]) -> bool:
        """Return True if statement doesn't aggregate across towns."""
        aggregation_patterns = ["multiple towns", "many towns", "other towns", "consensus"]
        forbidden = any(p in statement.lower() for p in aggregation_patterns)
        return not forbidden

    @staticmethod
    def check_no_npc_reference(statement: str, other_npc_ids: List[str]) -> bool:
        """Return True if statement doesn't reference other NPCs."""
        return not any(npc_id in statement for npc_id in other_npc_ids)

    @staticmethod
    def validate(statement: str, npc_id: str, town_names: List[str]) -> tuple:
        """
        Validate NPC observation.
        Returns (is_valid, reason).
        """
        if not NPCValidator.check_forbidden_verbs(statement):
            return False, "FORBIDDEN_VERB_DETECTED"

        if not NPCValidator.check_no_cross_town_reference(statement, town_names):
            return False, "CROSS_TOWN_AGGREGATION"

        if not NPCValidator.check_no_npc_reference(statement, []):
            return False, "NPC_REFERENCE_DETECTED"

        return True, "VALID"


class NPC:
    """An observer that measures and reports, nothing more."""

    def __init__(self, npc_id: str, town_id: str):
        self.npc_id = npc_id
        self.town_id = town_id

    def observe(self, ledger: List[Dict], epoch: int, town_names: List[str]) -> Optional[Dict]:
        """
        Generate observation from local ledger.

        Returns observation dict or None if validation fails.
        """
        if not ledger:
            return None

        # Measure local metrics
        recent = ledger[-10:] if len(ledger) >= 10 else ledger
        ship_count = len([r for r in recent if r.get("decision") == "SHIP"])
        no_ship_count = len([r for r in recent if r.get("decision") == "NO_SHIP"])
        avg_score = sum(r.get("score", 0) for r in recent) / len(recent) if recent else 0

        # Generate observation statement
        statement = (
            f"Recent decision rate: {ship_count} SHIP, {no_ship_count} NO_SHIP. "
            f"Average score: {avg_score:.1f}."
        )

        # Validate
        is_valid, reason = NPCValidator.validate(statement, self.npc_id, town_names)
        if not is_valid:
            return None

        # Create observation
        observation = {
            "npc_id": self.npc_id,
            "town_id": self.town_id,
            "epoch": epoch,
            "observation": statement,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "OBSERVATION",
            "status": "OBSERVATION_ONLY",
        }

        observation["hash"] = self._hash_observation(observation)
        return observation

    @staticmethod
    def _hash_observation(obs: Dict) -> str:
        """Deterministic hash."""
        canonical = json.dumps(obs, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


class NPCCohort:
    """Collection of NPCs for a town."""

    def __init__(self, town_id: str, npc_count: int):
        self.town_id = town_id
        self.npcs = [NPC(f"npc_{town_id.lower()}_{i:03d}", town_id) for i in range(npc_count)]

    def observe_all(self, ledger: List[Dict], epoch: int, town_names: List[str]) -> List[Dict]:
        """Generate observations from all NPCs."""
        observations = []
        for npc in self.npcs:
            obs = npc.observe(ledger, epoch, town_names)
            if obs:
                observations.append(obs)
        return observations
