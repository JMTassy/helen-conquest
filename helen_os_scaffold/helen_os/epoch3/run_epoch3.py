"""
helen_os/epoch3/run_epoch3.py — EPOCH3 canonical orchestrator.

Image spec: "CONQUEST: HELEN Internal Sim Loop Spec"
  LOOP COMPLETES → INITIATE NEXT QUEST

Runs all 3 quests from QUEST_BANK (Q1→Q2→Q3) in sequence.
Each quest result (Output) seeds the context for the next (self-referential loop).

Output artifact: EPOCH3_RUN_V1 — all 3 loop results + evaluations + laws.

Gains & Learnings (image: "4. Output"):
  Cognitive Growth    = laws inscribed (LAW_V1 receipts)
  Temporal Awareness  = metrics deltas across W and W' runs
  Adaptive Strategies = sigma results + evaluation gates
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .quest_bank import QUEST_BANK, Quest
from .sim_loop   import SimLoop, SimLoopResult
from .evaluation import EvaluationGate, EvaluationResult


# ── Quest loop result (one quest) ─────────────────────────────────────────────

@dataclass
class QuestLoopResult:
    """
    Image: one complete loop iteration (Input → Phases → Eval → Output).
    """
    quest:            Quest
    sim_result:       SimLoopResult
    evaluation:       EvaluationResult

    def to_payload(self) -> Dict[str, Any]:
        return {
            "quest_id":   self.quest.id,
            "quest_type": self.quest.quest_type.value,
            "sim_loop":   self.sim_result.to_payload(),
            "evaluation": self.evaluation.to_payload(),
            "overall_pass": self.evaluation.overall_pass,
        }


# ── EPOCH3 run result ─────────────────────────────────────────────────────────

@dataclass
class Epoch3RunResult:
    """
    Complete EPOCH3 canonical run across all 3 quests.

    Fields (image "4. Output — GAINS & LEARNINGS"):
      cognitive_growth     = total laws inscribed
      temporal_awareness   = aggregated metrics across all runs
      adaptive_strategies  = sigma + evaluation summary per quest
    """
    seed:              int
    ticks:             int
    quest_results:     List[QuestLoopResult]
    laws_inscribed:    List[Dict[str, Any]]    # all LAW_V1 payloads
    law_receipts:      List[str]               # receipt IDs
    kernel_cum_hash:   str
    run_receipts_count:int
    run_at:            str

    @property
    def cognitive_growth(self) -> int:
        """Number of laws inscribed (image: Cognitive Growth)."""
        return len(self.laws_inscribed)

    @property
    def temporal_awareness(self) -> Dict[str, Any]:
        """Aggregated metrics across W and W' runs (image: Temporal Awareness)."""
        all_closures  = [qr.sim_result.phase_a.metrics.closure_success
                         for qr in self.quest_results]
        all_drifts    = [qr.sim_result.phase_a.metrics.sovereignty_drift_index
                         for qr in self.quest_results]
        all_admission = [qr.sim_result.phase_a.metrics.admissibility_rate
                         for qr in self.quest_results]
        return {
            "quests_run":           len(self.quest_results),
            "closures_achieved":    sum(1 for c in all_closures if c),
            "avg_admissibility":    sum(all_admission) / len(all_admission) if all_admission else 0,
            "avg_sovereignty_drift":sum(all_drifts) / len(all_drifts) if all_drifts else 0,
        }

    @property
    def adaptive_strategies(self) -> List[Dict[str, Any]]:
        """Per-quest sigma + evaluation (image: Adaptive Strategies)."""
        return [
            {
                "quest_id":               qr.quest.id,
                "quest_type":             qr.quest.quest_type.value,
                "sigma_passed":           qr.sim_result.phase_c.sigma_passed,
                "overall_eval_pass":      qr.evaluation.overall_pass,
                "contradiction_resolved": qr.evaluation.contradiction_resolved,
                "reality_transformed":    qr.evaluation.reality_transformed,
                "temporal_insights":      qr.evaluation.temporal_insights_gained,
            }
            for qr in self.quest_results
        ]

    def to_artifact(self) -> Dict[str, Any]:
        """Serialize as EPOCH3_RUN_V1 artifact dict (no sha256 yet)."""
        return {
            "type":              "EPOCH3_RUN_V1",
            "seed":              self.seed,
            "ticks":             self.ticks,
            "quest_results":     [qr.to_payload() for qr in self.quest_results],
            "laws_inscribed":    self.laws_inscribed,
            "law_receipts":      self.law_receipts,
            "kernel_cum_hash":   self.kernel_cum_hash,
            "run_receipts_count":self.run_receipts_count,
            "cognitive_growth":  self.cognitive_growth,
            "temporal_awareness":self.temporal_awareness,
            "adaptive_strategies":self.adaptive_strategies,
            "hypotheses": [
                {"id": q.quest.id, "text": q.quest.hypothesis, "type": q.quest.quest_type.value}
                for q in self.quest_results
            ],
            "run_at": self.run_at,
        }


# ── Canonical EPOCH3 run ───────────────────────────────────────────────────────

def run_epoch3_canonical(
    seed:        int = 42,
    ticks:       int = 20,
    ledger_path: str = ":memory:",
) -> Epoch3RunResult:
    """
    Run the canonical EPOCH3 learning loop (all 3 quests, A→B→C + Evaluation).

    Image: "LOOP COMPLETES → INITIATE NEXT QUEST"

    Each quest is:
      1. Input:      select quest from QUEST_BANK
      2. Simulation: SimLoop.run(quest, seed, ticks)
      3. Evaluation: EvaluationGate.assess(sim_result)
      4. Output:     QuestLoopResult → feeds context for next quest

    Args:
        seed:         Base world PRF seed (default: 42).
        ticks:        Base tick count (default: 20).
        ledger_path:  Kernel path (default: :memory: — non-sovereign).

    Returns:
        Epoch3RunResult with all quest results + laws + evaluations.
    """
    from ..kernel import GovernanceVM
    from ..epoch2.law_ledger import LawLedger

    run_at = datetime.now(timezone.utc).isoformat()

    # Shared ephemeral kernel — all quest receipts share one hash chain
    km = GovernanceVM(ledger_path=ledger_path)

    # Emit EPOCH3 start receipt
    km.propose({
        "type":  "EPOCH3_START_V1",
        "seed":  seed,
        "ticks": ticks,
        "quests":[q.id for q in QUEST_BANK],
    })

    loop     = SimLoop(kernel=km)
    ledger   = LawLedger(kernel=km)

    quest_results: List[QuestLoopResult] = []

    # Image: "LOOP COMPLETES → INITIATE NEXT QUEST"
    # Execute Q1 → Q2 → Q3 in sequence
    for quest in QUEST_BANK:

        # ── Input: select quest ───────────────────────────────────────────────
        # Each quest type maps to its quest from QUEST_BANK.
        # (Future: next quest could be chosen dynamically based on prior output.)

        # ── Simulation: A→B→C ────────────────────────────────────────────────
        sim_result = loop.run(
            quest      = quest,
            seed       = seed,
            ticks      = ticks,
            law_ledger = ledger,
        )

        # ── Evaluation ────────────────────────────────────────────────────────
        evaluation = EvaluationGate.assess(sim_result, kernel=km)

        quest_results.append(QuestLoopResult(
            quest      = quest,
            sim_result = sim_result,
            evaluation = evaluation,
        ))

    # Collect inscribed laws
    laws         = ledger.list_laws()
    law_receipts = [
        law.inscription_receipt_id
        for law in laws
        if law.inscription_receipt_id
    ]

    # Emit EPOCH3 summary receipt
    summary_receipt = km.propose({
        "type":              "EPOCH3_SUMMARY_V1",
        "seed":              seed,
        "ticks":             ticks,
        "quests_completed":  len(quest_results),
        "laws_inscribed":    len(laws),
        "overall_pass_count":sum(1 for qr in quest_results if qr.evaluation.overall_pass),
    })

    return Epoch3RunResult(
        seed              = seed,
        ticks             = ticks,
        quest_results     = quest_results,
        laws_inscribed    = [law.to_ledger_payload() for law in laws],
        law_receipts      = law_receipts,
        kernel_cum_hash   = summary_receipt.cum_hash,
        run_receipts_count= (
            1                          # EPOCH3_START
            + len(quest_results) * 6   # per quest: start + A + B + C + sigma + eval
            + len(laws)                # law inscriptions
            + 1                        # EPOCH3_SUMMARY
        ),
        run_at = run_at,
    )
