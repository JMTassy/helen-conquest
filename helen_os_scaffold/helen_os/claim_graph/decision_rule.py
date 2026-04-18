"""
helen_os/claim_graph/decision_rule.py — DR2 Decision Rule for CLAIM_GRAPH_V1.

DR2 Predicate (formal):
  Let G* = {g ∈ G-set | g is not targeted by any unanswered rebuttal}
  Let R* = {r ∈ R-set | r has no counter-rebuttal}

  INCLUDE  ⟺  |G*| >= min_undefeated_grounds  ∧  |R*| == 0
  BLOCKED  ⟺  |G-set| == 0   (no grounds at all)
  DEFER    ⟺  otherwise      (open objections or insufficient grounds)

"No receipt → no decision."
DR2.evaluate() always emits a DR2_DECISION_V1 receipt via kernel.propose().
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from .graph import ClaimGraph


# ── DR2 verdict ───────────────────────────────────────────────────────────────

class DR2Verdict(str, Enum):
    INCLUDE = "INCLUDE"   # Decision stands — proceed with proposal
    DEFER   = "DEFER"     # Hold — unresolved objections or insufficient grounds
    BLOCKED = "BLOCKED"   # Hard block — zero grounds or system veto


# ── DR2 result ────────────────────────────────────────────────────────────────

@dataclass
class DR2Result:
    """
    Output of DR2DecisionRule.evaluate().

    Fields:
      verdict:                    INCLUDE / DEFER / BLOCKED
      undefeated_grounds_count:   |G*| (grounds not targeted by unanswered rebuttals)
      unanswered_rebuttals_count: |R*| (rebuttals with no counter-rebuttal)
      min_undefeated_grounds:     The threshold used
      reason:                     Human-readable rationale string
      decision_receipt_id:        Receipt ID from kernel.propose() (set after emission)
    """
    verdict:                    DR2Verdict
    undefeated_grounds_count:   int
    unanswered_rebuttals_count: int
    min_undefeated_grounds:     int
    reason:                     str
    decision_receipt_id:        Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type":                       "DR2_RESULT_V1",
            "verdict":                    self.verdict.value,
            "undefeated_grounds_count":   self.undefeated_grounds_count,
            "unanswered_rebuttals_count": self.unanswered_rebuttals_count,
            "min_undefeated_grounds":     self.min_undefeated_grounds,
            "reason":                     self.reason,
            "decision_receipt_id":        self.decision_receipt_id,
        }


# ── DR2 decision rule ─────────────────────────────────────────────────────────

class DR2DecisionRule:
    """
    Decision Rule 2 (DR2): Structured argument-based decision predicate.

    Evaluates a ClaimGraph and emits a receipt-anchored decision.

    DR2 predicate:
      BLOCKED  if |G-set| == 0
      DEFER    if |R*| > 0   (any rebuttal unanswered)
      DEFER    if |G*| < min_undefeated_grounds
      INCLUDE  otherwise

    Args:
        min_undefeated_grounds: Minimum undefeated grounds required for INCLUDE.
                                Default: 2. Canonical scenario uses 2.
    """

    def __init__(self, min_undefeated_grounds: int = 2):
        self.min_undefeated_grounds = min_undefeated_grounds

    def evaluate(self, graph: ClaimGraph, kernel) -> DR2Result:
        """
        Evaluate the claim graph under DR2 and emit a decision receipt.

        Args:
            graph:  ClaimGraph to evaluate.
            kernel: GovernanceVM for emitting the DR2_DECISION_V1 receipt.

        Returns:
            DR2Result with verdict and receipt ID.

        Receipt schema (DR2_DECISION_V1):
          type, decision_topic, verdict, reason, graph_hash,
          undefeated_grounds_count, unanswered_rebuttals_count,
          min_undefeated_grounds
        """
        g_count  = len(graph.g_set)
        ug_count = len(graph.undefeated_grounds)
        ur_count = len(graph.unanswered_rebuttals)

        # Determine verdict
        if g_count == 0:
            verdict = DR2Verdict.BLOCKED
            reason  = "DR2_BLOCKED: No grounds provided"
        elif ur_count > 0:
            verdict = DR2Verdict.DEFER
            reason  = (
                f"DR2_DEFER: {ur_count} unanswered rebuttal(s) — "
                f"objections must be defeated before INCLUDE"
            )
        elif ug_count < self.min_undefeated_grounds:
            verdict = DR2Verdict.DEFER
            reason  = (
                f"DR2_DEFER: undefeated_grounds={ug_count} "
                f"< min={self.min_undefeated_grounds}"
            )
        else:
            verdict = DR2Verdict.INCLUDE
            reason  = (
                f"DR2_INCLUDE: {ug_count} undefeated grounds >= "
                f"min={self.min_undefeated_grounds}, "
                f"0 unanswered rebuttals"
            )

        result = DR2Result(
            verdict                   = verdict,
            undefeated_grounds_count  = ug_count,
            unanswered_rebuttals_count= ur_count,
            min_undefeated_grounds    = self.min_undefeated_grounds,
            reason                    = reason,
        )

        # Emit decision receipt — "no receipt → no decision"
        receipt = kernel.propose({
            "type":                       "DR2_DECISION_V1",
            "decision_topic":             graph.decision_topic,
            "verdict":                    verdict.value,
            "reason":                     reason,
            "graph_hash":                 graph.content_hash(),
            "undefeated_grounds_count":   ug_count,
            "unanswered_rebuttals_count": ur_count,
            "min_undefeated_grounds":     self.min_undefeated_grounds,
        })
        result.decision_receipt_id = receipt.id

        return result
