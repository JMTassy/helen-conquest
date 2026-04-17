"""
oracle_town/federation/fed_sim_minimal_v1.py

FederationSimMinimalV1 — Self-contained, zero-side-effect deterministic federation sim.

Design constraints:
  - No print statements (pure function)
  - No wall-clock time
  - No os.urandom / global random state
  - All randomness seeded from (base_seed, round_id, prev_hash) deterministically
  - Returns a single tip_hash (SHA256 chain) reproducible under any replay

GOSSIP_MSG_V1 contract enforced:
  - pattern_vector: aggregate floats only (no raw dialogue)
  - stats: integer counts only
  - Absolute bans checked before emit: raw_dialogue, prompt_text, claim_spans, user_identifier

This module is used by test_federation_determinism.py to prove:
  same scenario JSON → same tip_hash across independent runs.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional


# ── Canonical JSON / Hash helpers ─────────────────────────────────────────────

ABSOLUTE_BANS: List[str] = [
    "raw_dialogue",
    "prompt_text",
    "claim_spans",
    "user_identifier",
]


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def derive_round_seed(base_seed: int, round_id: int, prev_hash: str) -> int:
    """Deterministic per-round seed from (base_seed, round_id, prev_hash)."""
    payload = f"{base_seed}:{round_id}:{prev_hash}"
    return int(sha256_hex(payload)[:8], 16)


# ── GOSSIP_MSG_V1 ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GossipMsgV1:
    """
    Minimal gossip message. Absolute bans enforced on construction.

    Fields:
      peer_id:         source peer
      round_id:        monotonic round counter
      pattern_vector:  aggregate floats only (no raw dialogue, no spans)
      stats:           integer counts only
      prev_round_hash: for chain integrity (optional at round 0)
    """
    peer_id: str
    round_id: int
    pattern_vector: Dict[str, float]
    stats: Dict[str, int]
    prev_round_hash: Optional[str] = None

    def __post_init__(self):
        # Enforce absolute bans
        all_keys = list(self.pattern_vector.keys()) + list(self.stats.keys())
        for banned in ABSOLUTE_BANS:
            for key in all_keys:
                if banned in key.lower():
                    raise ValueError(
                        f"GOSSIP_MSG_V1 violation: field '{key}' matches "
                        f"absolute ban '{banned}'. "
                        "Only aggregate pattern vectors and integer stats allowed."
                    )

    def to_canonical(self) -> str:
        return canonical_json({
            "peer_id": self.peer_id,
            "round_id": self.round_id,
            "pattern_vector": self.pattern_vector,
            "stats": self.stats,
            "prev_round_hash": self.prev_round_hash,
        })

    def msg_hash(self) -> str:
        return sha256_hex(self.to_canonical())


# ── FedRoundResult ─────────────────────────────────────────────────────────────

@dataclass
class FedRoundResult:
    round_id: int
    messages: List[Dict[str, Any]]
    round_hash: str


# ── FederationSimMinimalV1 ─────────────────────────────────────────────────────

class FederationSimMinimalV1:
    """
    Deterministic federation simulation.

    run(scenario) → tip_hash (str)

    The tip_hash is SHA256 of the cumulative round chain.
    Same scenario JSON → same tip_hash on every run, in any environment.
    """

    def run(self, scenario: Dict[str, Any]) -> str:
        """
        Run all rounds from scenario. Return tip_hash (chain of round hashes).

        Args:
            scenario: dict matching FED_SIM_SCENARIO_V1 schema
                      (load from scenarios/baseline_round.json)

        Returns:
            tip_hash: SHA256 of the final cumulative state. Stable under replay.
        """
        base_seed = int(scenario["seed"])
        rounds = int(scenario["rounds"])
        peers = scenario["peers"]
        prev_hash = "0" * 64

        for r in range(rounds):
            round_seed = derive_round_seed(base_seed, r, prev_hash)
            result = self._run_round(peers, r, round_seed, prev_hash)
            prev_hash = result.round_hash

        return prev_hash

    def _run_round(
        self,
        peers: List[Dict[str, Any]],
        round_id: int,
        seed: int,
        prev_hash: str,
    ) -> FedRoundResult:
        rng = random.Random(seed)
        messages = []

        for p in sorted(peers, key=lambda x: x["peer_id"]):  # canonical order
            v = p["initial_vector"]
            delta = rng.uniform(-0.01, 0.01)

            msg = GossipMsgV1(
                peer_id=p["peer_id"],
                round_id=round_id,
                pattern_vector={
                    "c": round(float(v["c"]) + delta, 6),
                    "r": round(float(v["r"]) - delta, 6),
                },
                stats={
                    "messages_sent": rng.randint(1, 10),
                    "rounds_participated": round_id + 1,
                },
                prev_round_hash=prev_hash,
            )
            messages.append(json.loads(msg.to_canonical()))

        # Round hash = SHA256 of canonical list of messages
        round_hash = sha256_hex(canonical_json(messages))
        return FedRoundResult(round_id=round_id, messages=messages, round_hash=round_hash)
