"""
helen_os/epoch4 — CLAIM_GRAPH_V1 artifact pipeline.

Spec: "CONQUEST: HELEN↔HAL Hard Mode — Structured Argument → Receipt Artifact"

Input:  Structured dialogue text (fixtures/decay_dialogue_v1.txt)
Output: CLAIM_GRAPH_V1 receipt anchored in GovernanceVM

Pipeline:
  1. ingest_dialogue(text)  → ClaimGraphV1 (parse)
  2. validate_graph(graph)  → None | IngestError (validate)
  3. compute_sets(graph)    → ClaimGraphV1 (recompute G/R)
  4. kernel.propose(...)    → Receipt (anchor in chain)

Non-sovereign: :memory: kernels only.
No authority tokens. DR2 is stored as a rule, not a decision.
"""

from .run_epoch4 import run_epoch4, Epoch4Result

__all__ = ["run_epoch4", "Epoch4Result"]
