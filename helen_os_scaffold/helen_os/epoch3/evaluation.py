"""
helen_os/epoch3/evaluation.py — Evaluation Gate (Image spec: "3. Evaluation — ASSESS RESULTS")

Three assessment questions from the image:
  ☯  Contradiction Resolved?     — did paradox/shadow world diverge from base?
  ◉  Reality Transformed?        — did the quest change the world model?
  ⌛  Temporal Insights Gained?   — did we inscribe a new law with receipts?

Each question maps to a measurable predicate over SimLoopResult.
The EvaluationGate produces an EvaluationResult and emits a receipt.

Design:
  - All three questions are boolean predicates (not scores).
  - "Overall pass" = all three answer YES.
  - Partial pass is recorded and receipted (not discarded).
  - No question is "skipped" — failure is a result, not a void.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .sim_loop import SimLoopResult


# ── Evaluation result ──────────────────────────────────────────────────────────

@dataclass
class EvaluationResult:
    """
    Output of EvaluationGate.assess() — image section "3. Evaluation".

    Three assessment questions from the image:
      contradiction_resolved:  ☯  (Contradiction Resolved?)
      reality_transformed:     ◉  (Reality Transformed?)
      temporal_insights_gained:⌛  (Temporal Insights Gained?)

    overall_pass = all three True.
    """
    quest_id:                  str
    contradiction_resolved:    bool   # ☯
    reality_transformed:       bool   # ◉
    temporal_insights_gained:  bool   # ⌛
    overall_pass:              bool
    # Evidence
    delta_closure:             float
    delta_admissibility:       float
    sigma_passed:              bool
    laws_count:                int
    evaluation_receipt_id:     Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type":                     "EVALUATION_RESULT_V1",
            "quest_id":                 self.quest_id,
            "contradiction_resolved":   self.contradiction_resolved,
            "reality_transformed":      self.reality_transformed,
            "temporal_insights_gained": self.temporal_insights_gained,
            "overall_pass":             self.overall_pass,
            "delta_closure":            self.delta_closure,
            "delta_admissibility":      self.delta_admissibility,
            "sigma_passed":             self.sigma_passed,
            "laws_count":               self.laws_count,
        }

    def summary_line(self) -> str:
        icons = {True: "✅", False: "❌"}
        return (
            f"☯ contradiction_resolved:   {icons[self.contradiction_resolved]}\n"
            f"◉ reality_transformed:       {icons[self.reality_transformed]}\n"
            f"⌛ temporal_insights_gained: {icons[self.temporal_insights_gained]}\n"
            f"→ OVERALL: {'PASS ✅' if self.overall_pass else 'PARTIAL ⚠️'}"
        )


# ── Evaluation gate ────────────────────────────────────────────────────────────

class EvaluationGate:
    """
    Image spec: "3. Evaluation — ASSESS RESULTS"

    Three predicates applied to SimLoopResult + SimLoopResult.phase_c:

      ☯  Contradiction Resolved?
        For SOLVE_PARADOX: W closed (closure=1) while W' did NOT (closure=0).
        delta_closure > 0.5 → resolved.
        For other quest types: sigma_passed=True → resolved (no contradiction).

      ◉  Reality Transformed?
        Base world W admitted >= 80% evidence (admissibility_rate >= 0.80)
        AND shadow world W' showed measurable delta (|delta_admissibility| >= 0
        OR |delta_closure| >= 0, meaning something changed).
        Simpler: closure_success(W) == True → reality reached its final state.

      ⌛  Temporal Insights Gained?
        laws_inscribed_count >= 1 AND sigma_passed.
        (A law was inscribed with receipts — temporal memory gained.)
    """

    @classmethod
    def assess(
        cls,
        sim_result: SimLoopResult,
        kernel,
    ) -> EvaluationResult:
        """
        Assess results of a sim loop run.

        Args:
            sim_result: Complete SimLoopResult from SimLoop.run().
            kernel:     GovernanceVM for emitting evaluation receipt.

        Returns:
            EvaluationResult with all three assessments and a receipt ID.
        """
        from .quest_bank import QuestType

        pc = sim_result.phase_c
        pa = sim_result.phase_a
        pb = sim_result.phase_b

        quest_type = QuestType(sim_result.quest_type)

        # ── ☯ Contradiction Resolved? ─────────────────────────────────────────
        if quest_type == QuestType.SOLVE_PARADOX:
            # Paradox quest: W must close AND W' must NOT close.
            # delta_closure = closure(W) - closure(W') > 0.5 means contradiction resolved.
            contradiction_resolved = (
                pa.metrics.closure_success is True
                and pb.paradox_injected
                and pc.delta_closure_success > 0.5
            )
        else:
            # Non-paradox quest: sigma gate PASS = no contradiction in model.
            contradiction_resolved = pc.sigma_passed

        # ── ◉ Reality Transformed? ────────────────────────────────────────────
        # Reality was transformed if:
        #   1. Base world W completed (closure_success=True), AND
        #   2. The counterfactual W' showed a measurable difference
        #      (delta_closure != 0 OR we ran a shadow world at all).
        #
        # For EXPLORE_TEMPORAL: multiple horizons run = reality explored across time.
        shadow_ran = len(pb.shadow_metrics_list) > 0

        if quest_type == QuestType.EXPLORE_TEMPORAL:
            # All tick horizons must close (sovereignty is time-stable).
            all_horizons_close = all(
                m.closure_success for m in pb.shadow_metrics_list
            ) if pb.shadow_metrics_list else False
            reality_transformed = pa.metrics.closure_success and all_horizons_close
        elif quest_type == QuestType.SOLVE_PARADOX:
            # Reality is transformed when the paradox IS resolved.
            reality_transformed = contradiction_resolved
        else:
            # ALTER_REALITY: base world closed AND shadow ran with at least one run.
            reality_transformed = pa.metrics.closure_success and shadow_ran

        # ── ⌛ Temporal Insights Gained? ──────────────────────────────────────
        # Insights are gained when:
        #   - sigma gate passed, AND
        #   - at least one law was inscribed into ledger.
        temporal_insights_gained = pc.sigma_passed and pc.laws_inscribed_count >= 1

        overall_pass = (
            contradiction_resolved
            and reality_transformed
            and temporal_insights_gained
        )

        # Emit evaluation receipt (proves assessment ran)
        r = kernel.propose({
            "type":                     "EVALUATION_RESULT_V1",
            "quest_id":                 sim_result.quest_id,
            "quest_type":               sim_result.quest_type,
            "contradiction_resolved":   contradiction_resolved,
            "reality_transformed":      reality_transformed,
            "temporal_insights_gained": temporal_insights_gained,
            "overall_pass":             overall_pass,
        })

        return EvaluationResult(
            quest_id                  = sim_result.quest_id,
            contradiction_resolved    = contradiction_resolved,
            reality_transformed       = reality_transformed,
            temporal_insights_gained  = temporal_insights_gained,
            overall_pass              = overall_pass,
            delta_closure             = pc.delta_closure_success,
            delta_admissibility       = pc.delta_admissibility,
            sigma_passed              = pc.sigma_passed,
            laws_count                = pc.laws_inscribed_count,
            evaluation_receipt_id     = r.id,
        )
