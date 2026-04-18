"""
helen_os/claim_graph/schemas.py — Pydantic models for CLAIM_GRAPH_V1.

These schemas define the canonical, typed, receipt-able claim graph artifact.

Design principles:
  - Every field is deterministic and schema-validated.
  - No LLM dependence: graph structure comes from a structured dialogue text
    parsed by dialogue_ingest.py, not from an LLM's JSON extraction.
  - DR2 is stored as a DecisionRuleV1 (a rule), NOT a decision token.
    There is no "INCLUDE" authority token in the graph itself.
  - source_digest = sha256(raw dialogue text) — links graph to its input.

Usage:
    from helen_os.claim_graph.schemas import (
        ClaimGraphV1, ClaimNodeV1, ClaimEdgeV1,
        DecisionRuleV1, TaskV1,
        Role, ClaimKind, EdgeType, Status
    )
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ── Enum-like literals ────────────────────────────────────────────────────────

Role      = Literal["HELEN", "HAL", "PM", "ARCH", "DEV", "QA"]
ClaimKind = Literal["CONSTRAINT", "RISK", "BENEFIT", "FACT", "PROPOSAL", "GATE", "DEFINITION"]
Status    = Literal["ACTIVE", "RETRACTED"]
EdgeType  = Literal["SUPPORTS", "OBJECTS_TO", "REFINES", "RETRACTS", "DEPENDS_ON"]


# ── Claim node ────────────────────────────────────────────────────────────────

class ClaimNodeV1(BaseModel):
    """
    A single atomic claim in the argument graph.

    node_id:          Stable identifier (H1, A4, QA7, PERF1, ARCH1, …)
    role:             Who authored this claim (HELEN / HAL / PM / ARCH / DEV / QA)
    kind:             Semantic type (BENEFIT / RISK / CONSTRAINT / GATE / …)
    text:             The atomic claim statement (one sentence)
    status:           ACTIVE (default) or RETRACTED
    tags:             Optional labels for filtering/routing
    evidence_receipts:Receipt IDs from GovernanceVM.propose() that evidence this claim
    """
    node_id:          str
    role:             Role
    kind:             ClaimKind
    text:             str
    status:           Status = "ACTIVE"
    tags:             List[str] = Field(default_factory=list)
    evidence_receipts:List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_text_non_empty(self) -> "ClaimNodeV1":
        if not self.text.strip():
            raise ValueError(f"ClaimNodeV1 {self.node_id!r}: text must not be empty")
        return self


# ── Claim edge ────────────────────────────────────────────────────────────────

class ClaimEdgeV1(BaseModel):
    """
    A directed relation between two claim nodes.

    edge_id:   Stable identifier (e.g. "E-H1->D", "E-QA3->A1")
    type:      One of SUPPORTS / OBJECTS_TO / REFINES / RETRACTS / DEPENDS_ON
    src:       Source node_id
    dst:       Destination node_id
    rationale: Optional human-readable explanation of the relation
    """
    edge_id:   str
    type:      EdgeType
    src:       str
    dst:       str
    rationale: Optional[str] = None


# ── Decision rule ─────────────────────────────────────────────────────────────

class DecisionRuleV1(BaseModel):
    """
    A named decision rule (e.g. DR2).

    Stored as a RULE OBJECT, never as a decision token.
    "INCLUDE" or "DEFER" are rule outputs, not authority tokens.

    rule_id:            "DR2", "DR3", etc.
    decision_variable:  "D" (the decision variable)
    domain:             ["INCLUDE_V0.1", "DEFER"]
    rule_text:          Human-readable predicate (the actual rule)
    depends_on:         node_ids that must be in G-set for the rule to fire

    Invariant enforced by validate_graph():
      All depends_on entries must be in the graph's node set
      AND must be either CONSTRAINT or GATE kind claims.
    """
    rule_id:            str
    decision_variable:  str
    domain:             List[str]
    rule_text:          str
    depends_on:         List[str] = Field(default_factory=list)


# ── Task (T1–T4 hooks) ────────────────────────────────────────────────────────

class TaskV1(BaseModel):
    """
    A structured task derived from the dialogue — ready to seed EPOCH4 quests.

    task_id:         "T1", "T2", etc.
    role:            Who owns this task (ARCH / DEV / QA)
    text:            Task description
    hypothesis:      Falsifiable claim to verify
    validation_gate: Gate names required (e.g. "REPLAY_IDENTITY && PARTITION_IDENTITY")
    """
    task_id:         str
    role:            Role
    text:            str
    hypothesis:      str
    validation_gate: str


# ── Claim graph (top-level artifact) ─────────────────────────────────────────

class ClaimGraphV1(BaseModel):
    """
    The canonical CLAIM_GRAPH_V1 artifact.

    This is a DATA ARTIFACT, not an engine. It is:
      - Parsed from a structured dialogue text (dialogue_ingest.py)
      - Validated (graph.py: validate_graph)
      - G/R sets computed mechanically (graph.py: compute_sets)
      - Proposed into GovernanceVM.propose() as a receipt

    Fields:
      type:           "CLAIM_GRAPH_V1" (constant)
      topic:          Short decision topic label
      scenario:       Long scenario description (from dialogue header)
      nodes:          All claim nodes (including RISK/HAL claims)
      edges:          All relations between nodes
      g_set:          Agreed claim IDs (computed or declared)
      r_set:          Residual disputed claim IDs (computed or declared)
      decision_rules: Named decision rules (DR2, etc.) — stored as rules, NOT decisions
      tasks:          Structured task hooks (T1–T4) for next sim loop
      source_digest:  SHA256(raw dialogue text) — anchors graph to input
      decision:       None (purposely excluded — no authority token in graph artifact)
    """
    type:            str = "CLAIM_GRAPH_V1"
    topic:           str
    scenario:        str
    nodes:           List[ClaimNodeV1]
    edges:           List[ClaimEdgeV1]
    g_set:           List[str] = Field(default_factory=list)
    r_set:           List[str] = Field(default_factory=list)
    decision_rules:  List[DecisionRuleV1] = Field(default_factory=list)
    tasks:           List[TaskV1] = Field(default_factory=list)
    source_digest:   Optional[str] = None
    # decision is intentionally absent — no authority token in artifact

    def node_ids(self) -> set:
        return {n.node_id for n in self.nodes}

    def to_receipt_payload(self) -> Dict[str, Any]:
        """Canonical dict for kernel.propose() — stripped of computed fields."""
        return {
            "type":           self.type,
            "topic":          self.topic,
            "scenario":       self.scenario,
            "node_count":     len(self.nodes),
            "edge_count":     len(self.edges),
            "g_set":          self.g_set,
            "r_set":          self.r_set,
            "g_set_count":    len(self.g_set),
            "r_set_count":    len(self.r_set),
            "dr_ids":         [dr.rule_id for dr in self.decision_rules],
            "task_ids":       [t.task_id for t in self.tasks],
            "source_digest":  self.source_digest,
        }
