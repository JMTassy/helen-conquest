"""
helen_os/claim_graph — HELEN↔HAL Structured Decision Dialogue (CLAIM_GRAPH_V1)

Spec: "CONQUEST: HELEN↔HAL Hard Mode — 10M ticks/day Delayed Decay Decision"

Architecture:
  1. ClaimNode        — typed argument node (GROUND / REBUTTAL / COUNTER_REBUTTAL)
  2. ClaimGraph       — directed argument graph (G-set / R-set / CR-set)
  3. DR2DecisionRule  — decision predicate: INCLUDE / DEFER / BLOCKED
  4. HALDialogue      — receipt-anchored HELEN↔HAL dialogue runner
  5. run_claim_graph  — canonical 10M ticks/day scenario + Q4 hypotheses (T1–T4)

"No receipt → no decision."
Non-sovereign: all computation in :memory: kernels.
"""

from .claim_node   import ClaimNode, ClaimNodeType, ClaimSource
from .graph        import ClaimGraph
from .decision_rule import DR2DecisionRule, DR2Verdict, DR2Result
from .hal_dialogue  import HALDialogue, HALDialogueResult, DialogueTurn
from .run_claim_graph import run_claim_graph_canonical, ClaimGraphRunResult, Q4_HYPOTHESES

__all__ = [
    "ClaimNode", "ClaimNodeType", "ClaimSource",
    "ClaimGraph",
    "DR2DecisionRule", "DR2Verdict", "DR2Result",
    "HALDialogue", "HALDialogueResult", "DialogueTurn",
    "run_claim_graph_canonical", "ClaimGraphRunResult", "Q4_HYPOTHESES",
]
