"""
helen_os/claim_graph/run_claim_graph.py — Canonical CLAIM_GRAPH_V1 run.

Scenario: "INCLUDE Delayed Decay at 10M ticks/day"

HELEN proposes 4 grounds (G1–G4).
HAL raises 2 rebuttals (R1→G1, R2→G2).
HELEN counter-rebuts both (CR1→R1, CR2→R2).
DR2 evaluates: 4 undefeated grounds, 0 unanswered rebuttals → INCLUDE.

Q4 Hypotheses (T1–T4): structured tasks derived from the dialogue,
ready to seed the next sim loop (EPOCH4 quest bank).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .hal_dialogue import HALDialogue, HALDialogueResult
from .decision_rule import DR2Verdict


# ── Q4 Hypotheses (T1–T4) ────────────────────────────────────────────────────
# Derived from the Delayed Decay dialogue — ready to become EPOCH4 quests.

Q4_HYPOTHESES: List[Dict[str, Any]] = [
    {
        "id":             "T1",
        "role":           "ARCH",
        "text":           "Produce decay step formal insertion into tick order with no interleaving",
        "hypothesis":     "Decay step can be inserted as a single end-of-tick reducer "
                          "without introducing intra-tick cascades",
        "validation_gate":"REPLAY_IDENTITY && PARTITION_IDENTITY && ROLLBACK_IDENTITY",
        "metric":         "sovereignty_drift_index",
        "threshold":      0.0,
        "comparison":     "eq",
    },
    {
        "id":             "T2",
        "role":           "DEV",
        "text":           "Verify REPLAY_IDENTITY — same seed → same decay pattern",
        "hypothesis":     "Decay mechanism is replay-deterministic "
                          "(sovereignty_drift_index == 0 across seeds [42, 7, 99])",
        "validation_gate":"REPLAY_IDENTITY",
        "metric":         "determinism_coefficient",
        "threshold":      1.0,
        "comparison":     "eq",
    },
    {
        "id":             "T3",
        "role":           "QA",
        "text":           "Verify PARTITION_IDENTITY — decay does not alter non-decayed evidence partitions",
        "hypothesis":     "Evidence outside the decay window is unaffected "
                          "(counter-rebuttal closure before 20 turns)",
        "validation_gate":"PARTITION_IDENTITY",
        "metric":         "dialogue_turns",
        "threshold":      20,
        "comparison":     "lte",
    },
    {
        "id":             "T4",
        "role":           "QA",
        "text":           "Verify ROLLBACK_IDENTITY — restoring DORMANT evidence restores full admissibility",
        "hypothesis":     "DR2 INCLUDE verdict is receipt-anchored (non-trivial cum_hash)",
        "validation_gate":"ROLLBACK_IDENTITY",
        "metric":         "decision_receipt_hash",
        "threshold":      "non_zero",
        "comparison":     "non_zero",
    },
]

# ── Canonical scenario ────────────────────────────────────────────────────────

DECISION_TOPIC = (
    "INCLUDE Delayed Decay mechanism: evidence tagged DORMANT after 10M ticks "
    "of inactivity (reversible; chain integrity preserved)"
)

HELEN_GROUNDS = [
    # G1
    "10M ticks = ~100 days at 100K ticks/day — well beyond any active epoch "
    "(quest spec mandates max 1000 ticks)",
    # G2
    "Delayed decay is reversible: evidence stays in ledger as DORMANT, "
    "never deleted — chain integrity is preserved",
    # G3
    "Decay reduces sigma gate scan cost from O(n) to O(active_n), "
    "preventing ledger bloat in long-running simulations",
    # G4
    "Sovereignty drift_index remains 0 under decay at seeds [42, 7, 99] "
    "(tested across 3 invariant seeds)",
]

HAL_REBUTTALS = [
    # R1 → G1: challenges the threshold
    (
        "Decay threshold of 10M ticks is arbitrary — a quest running 15M ticks "
        "would incorrectly decay live evidence",
        "G1",
    ),
    # R2 → G2: challenges chain integrity
    (
        "DORMANT tags add complexity to evidence chain verification: "
        "verifiers must now handle two evidence states",
        "G2",
    ),
]

HELEN_COUNTER_REBUTTALS = [
    # CR1 → R1
    (
        "Quest spec enforces max 1000 ticks — 10M is 10,000× that margin. "
        "No conformant quest can produce live evidence after 10M ticks",
        "R1",
    ),
    # CR2 → R2
    (
        "DORMANT evidence is skipped during chain verification (flag-gated), "
        "not re-hashed — no additional complexity to the hash chain itself",
        "R2",
    ),
]


# ── Run result ────────────────────────────────────────────────────────────────

@dataclass
class ClaimGraphRunResult:
    """
    Output of run_claim_graph_canonical().

    Fields:
      dialogue_result:  Full HELEN↔HAL dialogue + DR2 verdict
      q4_hypotheses:    T1–T4 structured hypothesis specs (ready for EPOCH4)
      kernel_cum_hash:  Final cum_hash of the governance kernel
      receipts_count:   Total receipts emitted during the run
      run_at:           ISO8601 timestamp
    """
    dialogue_result: HALDialogueResult
    q4_hypotheses:   List[Dict[str, Any]]
    kernel_cum_hash: str
    receipts_count:  int
    run_at:          str

    @property
    def verdict(self) -> str:
        return self.dialogue_result.dr2_result.verdict.value

    @property
    def is_include(self) -> bool:
        return self.dialogue_result.dr2_result.verdict == DR2Verdict.INCLUDE

    def to_artifact(self) -> Dict[str, Any]:
        """Serialize as CLAIM_GRAPH_RUN_V1 artifact dict (for Pattern A sealing)."""
        return {
            "type":            "CLAIM_GRAPH_RUN_V1",
            "decision_topic":  DECISION_TOPIC,
            "verdict":         self.verdict,
            "is_include":      self.is_include,
            "q4_hypotheses":   self.q4_hypotheses,
            "dialogue":        self.dialogue_result.to_payload(),
            "kernel_cum_hash": self.kernel_cum_hash,
            "receipts_count":  self.receipts_count,
            "run_at":          self.run_at,
        }


# ── Canonical runner ──────────────────────────────────────────────────────────

def run_claim_graph_canonical(ledger_path: str = ":memory:") -> ClaimGraphRunResult:
    """
    Run the canonical HELEN↔HAL Delayed Decay decision dialogue.

    Scenario:
      Topic:             "INCLUDE Delayed Decay mechanism at 10M ticks inactivity"
      HELEN proposes:    4 grounds (G1–G4)
      HAL raises:        2 rebuttals (R1→G1, R2→G2)
      HELEN responds:    2 counter-rebuttals (CR1→R1, CR2→R2)
      DR2 evaluates:     4 undefeated grounds, 0 unanswered rebuttals → INCLUDE

    Receipt count:
      1 CLAIM_GRAPH_START
      1 DIALOGUE_START
      8 DIALOGUE_TURN (4G + 2R + 2CR)
      1 DR2_DECISION
      1 HAL_DIALOGUE_RESULT
      1 Q4_HYPOTHESES
      1 CLAIM_GRAPH_SUMMARY
      = 14 total receipts

    Args:
        ledger_path: Kernel path (default: :memory: — non-sovereign)

    Returns:
        ClaimGraphRunResult with dialogue + Q4 hypotheses + 14 receipts.
    """
    from ..kernel import GovernanceVM

    run_at = datetime.now(timezone.utc).isoformat()
    km = GovernanceVM(ledger_path=ledger_path)

    # Start receipt
    km.propose({
        "type":            "CLAIM_GRAPH_START_V1",
        "decision_topic":  DECISION_TOPIC,
        "grounds_count":   len(HELEN_GROUNDS),
        "rebuttals_count": len(HAL_REBUTTALS),
        "cr_count":        len(HELEN_COUNTER_REBUTTALS),
    })

    # Run HELEN↔HAL dialogue
    dialogue = HALDialogue(kernel=km, min_undefeated_grounds=2)
    result = dialogue.run(
        decision_topic    = DECISION_TOPIC,
        grounds           = HELEN_GROUNDS,
        rebuttals         = HAL_REBUTTALS,
        counter_rebuttals = HELEN_COUNTER_REBUTTALS,
    )

    # Q4 Hypotheses receipt
    km.propose({
        "type":       "Q4_HYPOTHESES_V1",
        "hypotheses": Q4_HYPOTHESES,
        "verdict":    result.dr2_result.verdict.value,
    })

    # Final summary receipt
    summary_r = km.propose({
        "type":         "CLAIM_GRAPH_SUMMARY_V1",
        "verdict":      result.dr2_result.verdict.value,
        "total_turns":  result.total_turns,
        "q4_count":     len(Q4_HYPOTHESES),
        "is_include":   result.is_resolved,
    })

    # Receipt count:
    # 1 CLAIM_GRAPH_START
    # 1 DIALOGUE_START          (from HALDialogue.run)
    # 8 DIALOGUE_TURN           (4G + 2R + 2CR)
    # 1 DR2_DECISION            (from DR2DecisionRule.evaluate)
    # 1 HAL_DIALOGUE_RESULT     (from HALDialogue.run)
    # 1 Q4_HYPOTHESES
    # 1 CLAIM_GRAPH_SUMMARY
    receipts_count = (
        1              # CLAIM_GRAPH_START
        + 1            # DIALOGUE_START
        + result.total_turns  # one per turn (8)
        + 1            # DR2_DECISION
        + 1            # HAL_DIALOGUE_RESULT
        + 1            # Q4_HYPOTHESES
        + 1            # CLAIM_GRAPH_SUMMARY
    )

    return ClaimGraphRunResult(
        dialogue_result = result,
        q4_hypotheses   = Q4_HYPOTHESES,
        kernel_cum_hash = summary_r.cum_hash,
        receipts_count  = receipts_count,
        run_at          = run_at,
    )
