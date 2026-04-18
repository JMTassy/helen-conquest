"""
helen_os/claim_graph/graph.py — Directed argument graph for CLAIM_GRAPH_V1.

ClaimGraph manages:
  - DECISION root node (D0)
  - G-set  = all GROUND nodes (HELEN's supporting claims)
  - R-set  = all REBUTTAL nodes (HAL's objections)
  - CR-set = all COUNTER_REBUTTAL nodes (HELEN's responses)

Key predicates (used by DR2DecisionRule):
  unanswered_rebuttals:  R-set nodes with no CR pointing to them
  undefeated_grounds:    G-set nodes not targeted by any unanswered rebuttal

"A ground is defeated if there exists an unanswered rebuttal targeting it."
"A rebuttal is answered when a counter-rebuttal defeats it."
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .claim_node import ClaimNode, ClaimNodeType, ClaimSource


@dataclass
class ClaimGraph:
    """
    Directed argument graph for a HELEN↔HAL decision dialogue.

    Created with a decision_topic; automatically builds the D0 root node.

    Add nodes via:
      add_ground(claim_text)               → G{n}
      add_rebuttal(claim_text, parent_id)  → R{n}
      add_counter_rebuttal(text, parent)   → CR{n} (also marks parent.defeated=True)
    """
    decision_topic: str
    _nodes: List[ClaimNode] = field(default_factory=list)
    _node_ids: set = field(default_factory=set)

    def __post_init__(self):
        # DECISION root node
        root = ClaimNode(
            node_id    = "D0",
            node_type  = ClaimNodeType.DECISION,
            claim_text = self.decision_topic,
            source     = ClaimSource.SYSTEM,
        )
        self._nodes.append(root)
        self._node_ids.add("D0")

    # ── Node access ─────────────────────────────────────────────────────────

    @property
    def all_nodes(self) -> List[ClaimNode]:
        return list(self._nodes)

    @property
    def g_set(self) -> List[ClaimNode]:
        """All GROUND nodes."""
        return [n for n in self._nodes if n.node_type == ClaimNodeType.GROUND]

    @property
    def r_set(self) -> List[ClaimNode]:
        """All REBUTTAL nodes."""
        return [n for n in self._nodes if n.node_type == ClaimNodeType.REBUTTAL]

    @property
    def cr_set(self) -> List[ClaimNode]:
        """All COUNTER_REBUTTAL nodes."""
        return [n for n in self._nodes if n.node_type == ClaimNodeType.COUNTER_REBUTTAL]

    @property
    def unanswered_rebuttals(self) -> List[ClaimNode]:
        """
        REBUTTAL nodes that have no COUNTER_REBUTTAL pointing to them.

        A rebuttal is "answered" when any CR has parent_id == this rebuttal's node_id.
        """
        answered_ids = {n.parent_id for n in self.cr_set}
        return [r for r in self.r_set if r.node_id not in answered_ids]

    @property
    def undefeated_grounds(self) -> List[ClaimNode]:
        """
        GROUND nodes not targeted by any *unanswered* rebuttal.

        A ground is "defeated" only if there exists an unanswered rebuttal
        with parent_id == this ground's node_id.

        If all rebuttals targeting a ground are themselves defeated (via CRs),
        the ground is still undefeated.
        """
        unanswered_parents = {r.parent_id for r in self.unanswered_rebuttals}
        return [g for g in self.g_set if g.node_id not in unanswered_parents]

    def get_node(self, node_id: str) -> Optional[ClaimNode]:
        for n in self._nodes:
            if n.node_id == node_id:
                return n
        return None

    # ── Node addition ────────────────────────────────────────────────────────

    def _next_id(self, prefix: str) -> str:
        count = sum(1 for n in self._nodes if n.node_id.startswith(prefix))
        return f"{prefix}{count + 1}"

    def add_ground(
        self,
        claim_text: str,
        source: ClaimSource = ClaimSource.HELEN,
        receipt_id: Optional[str] = None,
    ) -> ClaimNode:
        """Add a GROUND node (G-set). Parent is always D0 (the decision root)."""
        node = ClaimNode(
            node_id             = self._next_id("G"),
            node_type           = ClaimNodeType.GROUND,
            claim_text          = claim_text,
            source              = source,
            parent_id           = "D0",
            evidence_receipt_id = receipt_id,
        )
        self._nodes.append(node)
        self._node_ids.add(node.node_id)
        return node

    def add_rebuttal(
        self,
        claim_text: str,
        parent_id: str,
        source: ClaimSource = ClaimSource.HAL,
        receipt_id: Optional[str] = None,
    ) -> ClaimNode:
        """
        Add a REBUTTAL node (R-set).

        Args:
            claim_text: The objection text.
            parent_id:  The G-node_id this rebuttal targets (must exist in graph).
            source:     Who raised the rebuttal (default: HAL).

        Raises:
            ValueError: If parent_id is not in the graph.
        """
        if parent_id not in self._node_ids:
            raise ValueError(
                f"ClaimGraph.add_rebuttal: parent_id={parent_id!r} not in graph. "
                f"Known IDs: {sorted(self._node_ids)}"
            )
        node = ClaimNode(
            node_id             = self._next_id("R"),
            node_type           = ClaimNodeType.REBUTTAL,
            claim_text          = claim_text,
            source              = source,
            parent_id           = parent_id,
            evidence_receipt_id = receipt_id,
        )
        self._nodes.append(node)
        self._node_ids.add(node.node_id)
        return node

    def add_counter_rebuttal(
        self,
        claim_text: str,
        parent_id: str,
        source: ClaimSource = ClaimSource.HELEN,
        receipt_id: Optional[str] = None,
    ) -> ClaimNode:
        """
        Add a COUNTER_REBUTTAL node (CR-set) and mark the parent rebuttal as defeated.

        Args:
            claim_text: The counter-argument text.
            parent_id:  The R-node_id this counter-rebuttal defeats (must be REBUTTAL).
            source:     Who authored the counter-rebuttal (default: HELEN).

        Raises:
            ValueError: If parent_id is not in graph or parent is not a REBUTTAL.

        Side effect:
            Sets parent.defeated = True.
        """
        if parent_id not in self._node_ids:
            raise ValueError(
                f"ClaimGraph.add_counter_rebuttal: parent_id={parent_id!r} not in graph. "
                f"Known IDs: {sorted(self._node_ids)}"
            )
        parent = self.get_node(parent_id)
        if parent is None or parent.node_type != ClaimNodeType.REBUTTAL:
            raise ValueError(
                f"ClaimGraph.add_counter_rebuttal: parent must be REBUTTAL. "
                f"Got node_type={parent.node_type.value if parent else None} "
                f"for parent_id={parent_id!r}"
            )
        node = ClaimNode(
            node_id             = self._next_id("CR"),
            node_type           = ClaimNodeType.COUNTER_REBUTTAL,
            claim_text          = claim_text,
            source              = source,
            parent_id           = parent_id,
            evidence_receipt_id = receipt_id,
        )
        parent.defeated = True      # rebuttal is now defeated
        self._nodes.append(node)
        self._node_ids.add(node.node_id)
        return node

    # ── Serialization ────────────────────────────────────────────────────────

    def to_payload(self) -> Dict[str, Any]:
        """Canonical serialization as CLAIM_GRAPH_V1 dict."""
        return {
            "type":                  "CLAIM_GRAPH_V1",
            "decision_topic":        self.decision_topic,
            "nodes":                 [n.to_payload() for n in self._nodes],
            "g_set_count":           len(self.g_set),
            "r_set_count":           len(self.r_set),
            "cr_set_count":          len(self.cr_set),
            "unanswered_rebuttals":  len(self.unanswered_rebuttals),
            "undefeated_grounds":    len(self.undefeated_grounds),
        }

    def content_hash(self) -> str:
        """SHA256 of canonical payload — used for artifact anchoring."""
        canon = json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()
