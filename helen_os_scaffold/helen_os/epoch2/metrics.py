"""
helen_os/epoch2/metrics.py — EPOCH2 instrumented metrics.

Five metrics extracted from a completed CONQUEST LAND simulation run:

  1. admissibility_rate     — fraction of _emit() calls that produced a receipt
  2. dispute_heat           — contested/adversarial receipts per tick
  3. closure_success        — bool: expedition reached Vault (return_warrant_v1)
  4. witness_integrity      — missing pins and replay blocks
  5. sovereignty_drift_index — governance receipts emitted by non-home factions

All metrics are pure functions of the receipt stream + world summary.
No kernel writes. No world state mutation. Deterministic given fixed inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


# ── Metric constants ──────────────────────────────────────────────────────────

# Receipt evidence types that signal dispute / adversarial activity
DISPUTE_TYPES = frozenset({
    "decoy_signal_v1",
    "closure_failure_v1",
    "oath_failure_v1",
    "wolf_engagement_v1",
})

# Governance receipt types (issued by sovereign home-town factions only)
GOVERNANCE_TYPES = frozenset({
    "expedition_mandate_v1",
    "cleansing_receipt_v1",
    "oath_pass_v1",
    "oath_failure_v1",
    "fog_corridor_pass_v1",
    "return_warrant_v1",
    "closure_failure_v1",
    "siege_clearance_v1",
    "scout_accreditation_v1",
})


# ── Metrics dataclass ─────────────────────────────────────────────────────────

@dataclass
class Metrics:
    """
    Five instrumented metrics from one CONQUEST LAND run.
    All values are deterministic given the same (seed, ticks, world_version).
    """
    admissibility_rate: float       # [0.0, 1.0] — emit success fraction
    dispute_heat: float             # disputes per tick
    closure_success: bool           # True iff return_warrant_v1 in expedition_bundle
    witness_integrity: Dict[str, int]  # {"missing_pins": int, "replay_blocks": int}
    sovereignty_drift_index: float  # [0.0, 1.0] — 0 = no drift, 1 = total drift
    run_seed: int
    ticks: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["closure_success"] = self.closure_success  # keep as bool
        return d

    def as_receipt_payload(self) -> Dict[str, Any]:
        """Dict suitable for GovernanceVM.propose() — no LAW claim, metrics only."""
        return {
            "type": "EPOCH2_METRICS_V1",
            **self.to_dict(),
        }


# ── Metrics collector ─────────────────────────────────────────────────────────

class EpochMetricsCollector:
    """
    Compute the 5 EPOCH2 metrics from a completed sim run.

    Usage:
        world = ConquestLandWorld(kernel, world_seed=42)
        all_receipts = []
        for t in range(1, 21):
            all_receipts.extend(world.tick(t))
        summary = world.summary()
        metrics = EpochMetricsCollector.compute(all_receipts, summary, ticks=20)
    """

    @classmethod
    def compute(
        cls,
        receipts: List[Dict[str, Any]],
        summary: Dict[str, Any],
        ticks: int,
    ) -> Metrics:
        """
        Compute all 5 metrics.

        Args:
            receipts: Flat list of all receipt dicts from world.tick() calls.
                      Empty dicts {} are anti-replay drops (not included by tick()).
            summary:  world.summary() — contains emit_attempts, expedition_bundle, etc.
            ticks:    Number of ticks run.
        """
        # ── 1. admissibility_rate ─────────────────────────────────────────────
        # emit_attempts includes duplicates (from summary); successful = non-error receipts
        total_attempts = summary.get("emit_attempts", 0)
        successful = sum(1 for r in receipts if r and not r.get("error"))
        admissibility_rate = (
            successful / total_attempts if total_attempts > 0 else 1.0
        )

        # ── 2. dispute_heat ───────────────────────────────────────────────────
        dispute_count = sum(
            1 for r in receipts
            if r.get("evidence_type") in DISPUTE_TYPES
        )
        dispute_heat = dispute_count / ticks if ticks > 0 else 0.0

        # ── 3. closure_success ───────────────────────────────────────────────
        closure_success = summary.get("return_achieved", False)

        # ── 4. witness_integrity ─────────────────────────────────────────────
        # Expected: F2 emits witness_pin_v1 every 3 ticks (t=3,6,9,...)
        expected_pin_ticks = sum(1 for t in range(1, ticks + 1) if t % 3 == 0)
        actual_pins = sum(
            1 for r in receipts
            if r.get("evidence_type") == "witness_pin_v1"
        )
        replay_blocks = max(0, total_attempts - successful)
        witness_integrity = {
            "missing_pins": max(0, expected_pin_ticks - actual_pins),
            "replay_blocks": replay_blocks,
        }

        # ── 5. sovereignty_drift_index ────────────────────────────────────────
        sovereignty_drift_index = cls._compute_sovereignty_drift(receipts)

        return Metrics(
            admissibility_rate=admissibility_rate,
            dispute_heat=dispute_heat,
            closure_success=closure_success,
            witness_integrity=witness_integrity,
            sovereignty_drift_index=sovereignty_drift_index,
            run_seed=summary.get("world_seed", 0),
            ticks=ticks,
        )

    @classmethod
    def _compute_sovereignty_drift(cls, receipts: List[Dict[str, Any]]) -> float:
        """
        Drift = fraction of governance receipts emitted by non-home factions.

        Governance receipts are those in GOVERNANCE_TYPES.
        A faction's home is defined in FACTIONS[faction_id]["home"].
        Drift occurs when a faction issues a governance receipt for a town
        it doesn't govern (e.g., F2 issuing oath_pass_v1 for T3 — which never
        happens in the current world, but the metric would catch it if it did).
        """
        from ..seeds.worlds.conquest_land import FACTIONS

        home_map = {fid: fdata["home"] for fid, fdata in FACTIONS.items()}

        gov_receipts = [
            r for r in receipts
            if r and r.get("evidence_type") in GOVERNANCE_TYPES
        ]
        if not gov_receipts:
            return 0.0

        drift_count = sum(
            1 for r in gov_receipts
            if home_map.get(r.get("faction_id")) != r.get("town_id")
        )
        return drift_count / len(gov_receipts)
