"""
helen_os/epoch2/town_birth.py — TOWN_BIRTH_PREDICATE_V1.

Without this predicate, the sim teaches: "power → sovereignty."
With it, HELEN learns: "sovereignty = ratified protocol."

Three conditions must ALL hold simultaneously for a faction to become a town:

  1. receipt_count >= MIN_RECEIPT_COUNT
     Proves governance activity.  A faction that never emits receipts has
     no evidence of operation — it cannot claim sovereignty.

  2. treaty_signature
     At least one existing town must have emitted a town_treaty_v1 receipt
     designating this faction.  Sovereignty is granted, not seized.

  3. closure_proof
     The faction must have participated in a run that reached Vault return
     (return_warrant_v1 in expedition_bundle) and emitted at least one
     receipt during that run.  Closure competence is required.

EPOCH2 NOTE:
  In the current v0.1.0 CONQUEST LAND world, no faction meets all three
  conditions:
    • receipt_count: several factions qualify (F7, F9, etc.)
    • treaty_signature: no town_treaty_v1 evidence type exists yet
    • closure_proof: depends on reaching Vault in the run

  This is BY DESIGN.  EPOCH2 proves the infrastructure for the predicate
  even before any town is born.  A future world version that adds
  town_treaty_v1 emission will produce eligible results automatically.
  HELEN observes: "sovereignty requires proof, not just receipts."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


# ── Constants ─────────────────────────────────────────────────────────────────

MIN_RECEIPT_COUNT = 5    # minimum receipts for condition 1

TREATY_EVIDENCE_TYPE = "town_treaty_v1"   # not yet emitted in v0.1.0 world


# ── Predicate bundle ──────────────────────────────────────────────────────────

@dataclass
class TownBirthBundle:
    """
    Proof bundle computed by TownBirthPredicateV1.evaluate().
    Records the evidence state for each condition.
    """
    faction_id: str
    receipt_count: int
    treaty_signature: bool   # True if town_treaty_v1 found for this faction
    closure_proof: bool      # True if faction emitted in a run with return_warrant_v1
    checked_at: str


@dataclass
class TownBirthResult:
    """
    Result of TOWN_BIRTH_PREDICATE_V1 evaluation for one faction.
    """
    faction_id: str
    eligible: bool
    bundle: TownBirthBundle
    missing: List[str]   # names of failed conditions
    reason: str

    def to_receipt_payload(self) -> Dict[str, Any]:
        """TOWN_BIRTH_PREDICATE_V1 ledger payload for kernel.propose()."""
        return {
            "type": "TOWN_BIRTH_PREDICATE_V1",
            "faction_id": self.faction_id,
            "eligible": self.eligible,
            "receipt_count": self.bundle.receipt_count,
            "treaty_signature": self.bundle.treaty_signature,
            "closure_proof": self.bundle.closure_proof,
            "missing": self.missing,
            "reason": self.reason,
            "checked_at": self.bundle.checked_at,
        }


# ── Predicate evaluator ───────────────────────────────────────────────────────

class TownBirthPredicateV1:
    """
    Evaluate TOWN_BIRTH_PREDICATE_V1 for one or all factions.

    Usage:
        result = TownBirthPredicateV1.evaluate("F7", receipts, world_summary)
        receipt = kernel.propose(result.to_receipt_payload())

        all_results = TownBirthPredicateV1.evaluate_all_factions(receipts, summary)
    """

    @classmethod
    def evaluate(
        cls,
        faction_id: str,
        receipts: List[Dict[str, Any]],
        world_summary: Dict[str, Any],
    ) -> TownBirthResult:
        """
        Check all three predicate conditions for faction_id.

        Condition 1 (receipt_count):
            Count receipts where payload["faction_id"] == faction_id.

        Condition 2 (treaty_signature):
            Any receipt with evidence_type == TREATY_EVIDENCE_TYPE
            AND payload["target_faction"] == faction_id.

        Condition 3 (closure_proof):
            "return_warrant_v1" in world_summary["expedition_bundle"]
            AND faction emitted at least one receipt in this run.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Condition 1: receipt count
        faction_receipts = [
            r for r in receipts
            if r and r.get("faction_id") == faction_id
        ]
        receipt_count = len(faction_receipts)
        cond1 = receipt_count >= MIN_RECEIPT_COUNT

        # Condition 2: treaty signature
        treaty_receipts = [
            r for r in receipts
            if (r
                and r.get("evidence_type") == TREATY_EVIDENCE_TYPE
                and r.get("target_faction") == faction_id)
        ]
        treaty_signature = len(treaty_receipts) > 0
        cond2 = treaty_signature

        # Condition 3: closure proof
        return_achieved = world_summary.get("return_achieved", False)
        closure_proof = return_achieved and receipt_count > 0
        cond3 = closure_proof

        # Aggregate
        missing = []
        if not cond1:
            missing.append(
                f"receipt_count={receipt_count} < MIN={MIN_RECEIPT_COUNT}"
            )
        if not cond2:
            missing.append(
                f"no {TREATY_EVIDENCE_TYPE!r} designating {faction_id}"
            )
        if not cond3:
            if not return_achieved:
                missing.append("expedition did not reach Vault (no closure_proof)")
            else:
                missing.append(f"{faction_id} emitted 0 receipts in this run")

        eligible = cond1 and cond2 and cond3

        if eligible:
            reason = (
                f"{faction_id} eligible: "
                f"receipts={receipt_count}, treaty=✓, closure=✓"
            )
        else:
            reason = (
                f"{faction_id} not eligible: missing [{', '.join(missing)}]"
            )

        bundle = TownBirthBundle(
            faction_id=faction_id,
            receipt_count=receipt_count,
            treaty_signature=treaty_signature,
            closure_proof=closure_proof,
            checked_at=now,
        )

        return TownBirthResult(
            faction_id=faction_id,
            eligible=eligible,
            bundle=bundle,
            missing=missing,
            reason=reason,
        )

    @classmethod
    def evaluate_all_factions(
        cls,
        receipts: List[Dict[str, Any]],
        world_summary: Dict[str, Any],
    ) -> List[TownBirthResult]:
        """
        Evaluate all 10 CONQUEST LAND factions.
        Returns list of TownBirthResult in FACTIONS insertion order.
        """
        from ..seeds.worlds.conquest_land import FACTIONS
        return [
            cls.evaluate(fid, receipts, world_summary)
            for fid in FACTIONS
        ]
