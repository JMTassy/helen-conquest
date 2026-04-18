"""
helen_os/claim_graph/hal_dialogue.py — HELEN↔HAL Structured Dialogue Runner.

Protocol (3-phase receipt chain):
  Phase 1: HELEN proposes GROUND nodes (supporting the decision)
  Phase 2: HAL raises REBUTTAL nodes  (objecting to specific grounds)
  Phase 3: HELEN issues COUNTER_REBUTTAL nodes (defeating rebuttals)
  Phase 4: DR2DecisionRule evaluates the final graph
  Phase 5: Summary receipt emitted

"No receipt → no decision."
Each dialogue turn emits a DIALOGUE_TURN_V1 receipt.
The DR2 evaluation emits a DR2_DECISION_V1 receipt.
The dialogue summary emits a HAL_DIALOGUE_RESULT_V1 receipt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .claim_node import ClaimNode, ClaimSource
from .graph       import ClaimGraph
from .decision_rule import DR2DecisionRule, DR2Result


# ── Dialogue turn record ──────────────────────────────────────────────────────

@dataclass
class DialogueTurn:
    """One recorded turn in the HELEN↔HAL dialogue."""
    turn_number: int
    speaker:     ClaimSource
    action:      str           # "PROPOSE_GROUND" | "RAISE_REBUTTAL" | "COUNTER_REBUTTAL"
    claim_text:  str
    node_id:     str
    parent_id:   Optional[str]
    receipt_id:  Optional[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "turn":       self.turn_number,
            "speaker":    self.speaker.value,
            "action":     self.action,
            "claim_text": self.claim_text,
            "node_id":    self.node_id,
            "parent_id":  self.parent_id,
            "receipt_id": self.receipt_id,
        }


# ── Dialogue result ───────────────────────────────────────────────────────────

@dataclass
class HALDialogueResult:
    """
    Complete HELEN↔HAL dialogue result.

    Contains:
      - argument graph (all nodes + edges)
      - DR2 verdict (INCLUDE / DEFER / BLOCKED)
      - dialogue transcript (ordered turns)
      - receipt chain proof
    """
    decision_topic:      str
    graph:               ClaimGraph
    dr2_result:          DR2Result
    turns:               List[DialogueTurn]
    dialogue_receipt_id: Optional[str] = None

    @property
    def total_turns(self) -> int:
        return len(self.turns)

    @property
    def is_resolved(self) -> bool:
        from .decision_rule import DR2Verdict
        return self.dr2_result.verdict == DR2Verdict.INCLUDE

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type":              "HAL_DIALOGUE_RESULT_V1",
            "decision_topic":    self.decision_topic,
            "verdict":           self.dr2_result.verdict.value,
            "reason":            self.dr2_result.reason,
            "total_turns":       self.total_turns,
            "g_set_count":       len(self.graph.g_set),
            "r_set_count":       len(self.graph.r_set),
            "cr_set_count":      len(self.graph.cr_set),
            "is_resolved":       self.is_resolved,
            "graph":             self.graph.to_payload(),
            "dr2_result":        self.dr2_result.to_payload(),
            "turns":             [t.to_payload() for t in self.turns],
            "dialogue_receipt_id": self.dialogue_receipt_id,
        }


# ── Dialogue runner ───────────────────────────────────────────────────────────

class HALDialogue:
    """
    Receipt-anchored HELEN↔HAL structured decision dialogue.

    Usage:
        dialogue = HALDialogue(kernel=km, min_undefeated_grounds=2)
        result = dialogue.run(
            decision_topic    = "INCLUDE feature X?",
            grounds           = ["G1 text", "G2 text"],
            rebuttals         = [("R text", "G1")],
            counter_rebuttals = [("CR text", "R1")],
        )
        assert result.is_resolved
        assert result.dr2_result.verdict == DR2Verdict.INCLUDE

    Note on parent_id for rebuttals and counter_rebuttals:
      These are node_ids in the graph, i.e. "G1", "G2", "R1", etc.
      The node_ids are assigned sequentially as nodes are added.
    """

    def __init__(self, kernel, min_undefeated_grounds: int = 2):
        self._kernel = kernel
        self._dr2    = DR2DecisionRule(min_undefeated_grounds=min_undefeated_grounds)
        self._turns: List[DialogueTurn] = []
        self._turn_counter = 0

    def _next_turn(self) -> int:
        self._turn_counter += 1
        return self._turn_counter

    def _emit_turn(
        self,
        speaker:    ClaimSource,
        action:     str,
        claim_text: str,
        node_id:    str,
        parent_id:  Optional[str],
    ) -> str:
        """Emit a DIALOGUE_TURN_V1 receipt and return its ID."""
        receipt = self._kernel.propose({
            "type":       "DIALOGUE_TURN_V1",
            "turn":       self._turn_counter,
            "speaker":    speaker.value,
            "action":     action,
            "claim_text": claim_text,
            "node_id":    node_id,
            "parent_id":  parent_id,
        })
        return receipt.id

    def run(
        self,
        decision_topic:    str,
        grounds:           List[str],
        rebuttals:         List[Tuple[str, str]],   # (claim_text, parent_node_id)
        counter_rebuttals: List[Tuple[str, str]],   # (claim_text, parent_node_id)
    ) -> HALDialogueResult:
        """
        Run a complete HELEN↔HAL dialogue from pre-specified turns.

        Args:
            decision_topic:    The topic/proposal being decided.
            grounds:           List of HELEN's supporting claim texts.
            rebuttals:         List of (rebuttal_text, parent_node_id) pairs.
                               parent_node_id should be "G1", "G2", etc.
            counter_rebuttals: List of (cr_text, parent_node_id) pairs.
                               parent_node_id should be "R1", "R2", etc.

        Returns:
            HALDialogueResult with graph + DR2 verdict + full transcript.
        """
        graph = ClaimGraph(decision_topic=decision_topic)

        # Start receipt
        self._kernel.propose({
            "type":            "DIALOGUE_START_V1",
            "decision_topic":  decision_topic,
            "grounds_count":   len(grounds),
            "rebuttals_count": len(rebuttals),
            "cr_count":        len(counter_rebuttals),
        })

        # ── Phase 1: HELEN proposes grounds ─────────────────────────────────
        for g_text in grounds:
            t = self._next_turn()
            # Predict the next node_id before adding
            next_gid = f"G{len(graph.g_set) + 1}"
            r_id = self._emit_turn(ClaimSource.HELEN, "PROPOSE_GROUND", g_text, next_gid, "D0")
            node = graph.add_ground(g_text, source=ClaimSource.HELEN, receipt_id=r_id)
            self._turns.append(DialogueTurn(
                turn_number=t, speaker=ClaimSource.HELEN, action="PROPOSE_GROUND",
                claim_text=g_text, node_id=node.node_id, parent_id="D0",
                receipt_id=r_id,
            ))

        # ── Phase 2: HAL raises rebuttals ────────────────────────────────────
        for r_text, parent_node_id in rebuttals:
            t = self._next_turn()
            next_rid = f"R{len(graph.r_set) + 1}"
            r_id = self._emit_turn(ClaimSource.HAL, "RAISE_REBUTTAL", r_text, next_rid, parent_node_id)
            node = graph.add_rebuttal(r_text, parent_id=parent_node_id,
                                      source=ClaimSource.HAL, receipt_id=r_id)
            self._turns.append(DialogueTurn(
                turn_number=t, speaker=ClaimSource.HAL, action="RAISE_REBUTTAL",
                claim_text=r_text, node_id=node.node_id, parent_id=parent_node_id,
                receipt_id=r_id,
            ))

        # ── Phase 3: HELEN counter-rebuts ────────────────────────────────────
        for cr_text, parent_rebuttal_id in counter_rebuttals:
            t = self._next_turn()
            next_crid = f"CR{len(graph.cr_set) + 1}"
            r_id = self._emit_turn(ClaimSource.HELEN, "COUNTER_REBUTTAL", cr_text,
                                   next_crid, parent_rebuttal_id)
            node = graph.add_counter_rebuttal(cr_text, parent_id=parent_rebuttal_id,
                                              source=ClaimSource.HELEN, receipt_id=r_id)
            self._turns.append(DialogueTurn(
                turn_number=t, speaker=ClaimSource.HELEN, action="COUNTER_REBUTTAL",
                claim_text=cr_text, node_id=node.node_id, parent_id=parent_rebuttal_id,
                receipt_id=r_id,
            ))

        # ── Phase 4: DR2 evaluation ──────────────────────────────────────────
        dr2_result = self._dr2.evaluate(graph, self._kernel)

        # ── Phase 5: Summary receipt ─────────────────────────────────────────
        summary_r = self._kernel.propose({
            "type":           "HAL_DIALOGUE_RESULT_V1",
            "decision_topic": decision_topic,
            "verdict":        dr2_result.verdict.value,
            "total_turns":    self._turn_counter,
            "g_set_count":    len(graph.g_set),
            "r_set_count":    len(graph.r_set),
            "cr_set_count":   len(graph.cr_set),
            "is_resolved":    dr2_result.verdict.value == "INCLUDE",
        })

        return HALDialogueResult(
            decision_topic      = decision_topic,
            graph               = graph,
            dr2_result          = dr2_result,
            turns               = list(self._turns),
            dialogue_receipt_id = summary_r.id,
        )
