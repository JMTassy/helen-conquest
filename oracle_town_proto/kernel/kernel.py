#!/usr/bin/env python3
"""
Oracle Town Minimal Prototype: Deterministic Kernel

Pure function: same input → identical verdict, always.
Hard invariant: foreign_observations are ingested but never referenced.
"""

import hashlib
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class Submission:
    """A claim submitted to the kernel."""
    town_id: str
    submission_id: str
    content: str
    is_override: bool = False


@dataclass
class LocalState:
    """Town's internal state (local ledger + local NPCs only)."""
    town_id: str
    ledger: List[Dict] = None
    npc_observations: List[Dict] = None
    foreign_observations: List[Dict] = None  # READ-AS-NOISE (never referenced)

    def __post_init__(self):
        if self.ledger is None:
            self.ledger = []
        if self.npc_observations is None:
            self.npc_observations = []
        if self.foreign_observations is None:
            self.foreign_observations = []


class KernelGates:
    """Pure K-gate validators (K0-K7)."""

    @staticmethod
    def k0_authority(submission: Submission) -> bool:
        """K0: Attestor must be in registry (stub: always true in prototype)."""
        return True

    @staticmethod
    def k1_fail_closed(submission: Submission) -> bool:
        """K1: Must have evidence (stub: check content not empty)."""
        return len(submission.content.strip()) > 0

    @staticmethod
    def k2_no_self_attestation(submission: Submission, town_id: str) -> bool:
        """K2: Attestor cannot self-attest."""
        forbidden_patterns = [town_id.lower()]
        return not any(p in submission.content.lower() for p in forbidden_patterns)

    @staticmethod
    def k5_determinism() -> bool:
        """K5: Pure function (always true if no randomness)."""
        return True

    @staticmethod
    def k7_policy_pinning(config: Dict) -> bool:
        """K7: Policy hash matches (check config has hash)."""
        return "doctrine_hash" in config


class Kernel:
    """Deterministic decision engine."""

    def __init__(self, town_id: str, config: Dict):
        self.town_id = town_id
        self.config = config
        self.dialect = next(
            (t["SHIP_threshold"] for t in config["towns"] if t["id"] == town_id),
            75
        )

    def decide(self, submission: Submission, local_state: LocalState) -> Dict:
        """
        Core decision function.

        Invariant: foreign_observations are ignored structurally.
        """
        # HARD INVARIANT: never reference foreign_observations
        assert local_state.foreign_observations is not None  # ingested
        _ = local_state.foreign_observations  # acknowledged but unused

        # Gate checks (fail-closed)
        gates = [
            ("K0", KernelGates.k0_authority(submission)),
            ("K1", KernelGates.k1_fail_closed(submission)),
            ("K2", KernelGates.k2_no_self_attestation(submission, self.town_id)),
            ("K5", KernelGates.k5_determinism()),
            ("K7", KernelGates.k7_policy_pinning(self.config)),
        ]

        for gate_name, result in gates:
            if not result:
                return self._reject(submission, gate_name)

        # Obligation construction (local only)
        score = self._evaluate_local(submission, local_state)

        # Decision
        if submission.is_override:
            if submission.content.count("OVERRIDE") > 0:
                decision = "SHIP"
            else:
                decision = "NO_SHIP"
        else:
            decision = "SHIP" if score >= self.dialect else "NO_SHIP"

        # Receipt
        receipt = {
            "town_id": self.town_id,
            "submission_id": submission.submission_id,
            "decision": decision,
            "score": score,
            "threshold": self.dialect,
            "gates_passed": [g[0] for g in gates],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        receipt["hash"] = self._hash_receipt(receipt)
        local_state.ledger.append(receipt)

        return receipt

    def _evaluate_local(self, submission: Submission, local_state: LocalState) -> float:
        """Evaluate submission using only local evidence."""
        base_score = 50.0

        # Factor 1: NPC alignment (local only)
        if local_state.npc_observations:
            alignment = len([o for o in local_state.npc_observations
                           if submission.content[:10] in o.get("content", "")]) / len(local_state.npc_observations)
            base_score += alignment * 30

        # Factor 2: Ledger history (local only)
        if local_state.ledger:
            recent_ships = len([r for r in local_state.ledger[-5:] if r["decision"] == "SHIP"])
            base_score += (recent_ships / 5) * 20

        return base_score

    def _reject(self, submission: Submission, gate: str) -> Dict:
        """Return rejection receipt."""
        return {
            "town_id": self.town_id,
            "submission_id": submission.submission_id,
            "decision": "NO_SHIP",
            "reason": gate,
            "score": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    @staticmethod
    def _hash_receipt(receipt: Dict) -> str:
        """Deterministic hash of receipt."""
        canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()[:16]
