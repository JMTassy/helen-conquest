"""
helen_os/claim_graph/claim_node.py — Typed argument nodes for CLAIM_GRAPH_V1.

Node types:
  DECISION        — Root node: the topic being decided (exactly one per graph)
  GROUND          — G: HELEN's supporting claim for the decision
  REBUTTAL        — R: HAL's objection to a specific ground (has parent_id)
  COUNTER_REBUTTAL— CR: HELEN's response defeating a rebuttal (has parent_id)

Edge semantics:
  GROUND          → SUPPORTS decision      (parent_id = "D0")
  REBUTTAL        → REBUTS a ground        (parent_id = "G{n}")
  COUNTER_REBUTTAL→ DEFEATS a rebuttal     (parent_id = "R{n}", sets rebuttal.defeated=True)

Sources:
  HELEN  — cognitive OS (proposer / counter-rebuttal author)
  HAL    — adversarial layer (rebuttal author)
  SYSTEM — kernel-generated (DECISION root)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


# ── Node types ────────────────────────────────────────────────────────────────

class ClaimNodeType(str, Enum):
    DECISION         = "DECISION"          # Root: the topic being decided
    GROUND           = "GROUND"            # G-set: supporting argument
    REBUTTAL         = "REBUTTAL"          # R-set: objection/counter-claim
    COUNTER_REBUTTAL = "COUNTER_REBUTTAL"  # CR-set: response to a rebuttal


class ClaimSource(str, Enum):
    HELEN  = "HELEN"
    HAL    = "HAL"
    SYSTEM = "SYSTEM"


# ── Claim node ────────────────────────────────────────────────────────────────

@dataclass
class ClaimNode:
    """
    A single node in the argument graph.

    Fields:
      node_id:             Unique identifier (D0, G1, G2, R1, CR1, etc.)
      node_type:           One of ClaimNodeType
      claim_text:          The argument or claim text
      source:              Who authored this node (HELEN / HAL / SYSTEM)
      parent_id:           ID of the node this responds to (required for R / CR)
      evidence_receipt_id: Receipt ID from GovernanceVM.propose() (set after emission)
      defeated:            True if a COUNTER_REBUTTAL was added with parent_id == this node_id
                           (only meaningful for REBUTTAL nodes)

    Invariants:
      - REBUTTAL        requires parent_id (points to a GROUND or DECISION)
      - COUNTER_REBUTTAL requires parent_id (must point to a REBUTTAL)
      - DECISION        has no parent (parent_id = None)
      - GROUND          has parent_id = "D0" (set automatically by ClaimGraph.add_ground)
    """
    node_id:             str
    node_type:           ClaimNodeType
    claim_text:          str
    source:              ClaimSource
    parent_id:           Optional[str] = None
    evidence_receipt_id: Optional[str] = None
    defeated:            bool = False

    ALLOWED_TYPES = frozenset(ClaimNodeType)

    def __post_init__(self):
        # Validate node_type
        if self.node_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"ClaimNode: node_type={self.node_type!r} not in allowed set "
                f"{[t.value for t in ClaimNodeType]}"
            )
        # REBUTTAL and COUNTER_REBUTTAL require parent_id
        if self.node_type in (ClaimNodeType.REBUTTAL, ClaimNodeType.COUNTER_REBUTTAL):
            if self.parent_id is None:
                raise ValueError(
                    f"ClaimNode: node_type={self.node_type.value} requires parent_id "
                    f"(node_id={self.node_id!r})"
                )

    def to_payload(self) -> Dict[str, Any]:
        """Canonical serialization for receipt emission and artifact storage."""
        return {
            "node_id":             self.node_id,
            "node_type":           self.node_type.value,
            "claim_text":          self.claim_text,
            "source":              self.source.value,
            "parent_id":           self.parent_id,
            "evidence_receipt_id": self.evidence_receipt_id,
            "defeated":            self.defeated,
        }
