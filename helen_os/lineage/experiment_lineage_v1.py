"""Experiment Lineage Graph (ELG) — append-only exploration memory.

Law:
  The ELG is NOT the sovereign ledger.
  It records every experiment — including rejected ones — as non-sovereign nodes.
  Its purpose is exploration memory, not governance authority.

Separation of concerns:
  DECISION_LEDGER_V1  ← sovereign: only ADMITTED decisions, governs state
  EXPERIMENT_LINEAGE_V1 ← exploration: ALL experiments, drives analysis layer

Single responsibility:
  make_empty_lineage()      → canonical empty ELG
  append_experiment_node()  → append one EXPERIMENT_NODE_V1 (append-only)
  get_admitted_nodes()      → filter ADMITTED nodes
  get_nodes_by_mutation_family() → filter by mutation class
  get_nodes_by_skill()      → filter by skill_id
  compute_lineage_hash()    → deterministic sha256 of full ELG

Invariants:
  I1. experiment_id is unique within a lineage.
  I2. parent_experiment_id (if not null) must refer to an existing node.
  I3. Existing nodes are never modified (append-only).
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.canonical import sha256_prefixed


# ── Factory ───────────────────────────────────────────────────────────────────

def make_empty_lineage(lineage_id: str) -> dict[str, Any]:
    """
    Return a canonical empty EXPERIMENT_LINEAGE_V1.
    Single source of truth for ELG construction.
    """
    return {
        "schema_name":    "EXPERIMENT_LINEAGE_V1",
        "schema_version": "1.0.0",
        "lineage_id":     lineage_id,
        "nodes":          [],
    }


# ── Append ────────────────────────────────────────────────────────────────────

def append_experiment_node(
    lineage: Mapping[str, Any],
    node: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Append one EXPERIMENT_NODE_V1 to the lineage.

    Rules:
      - lineage must be EXPERIMENT_LINEAGE_V1
      - node must be EXPERIMENT_NODE_V1
      - experiment_id must be unique (I1)
      - parent_experiment_id must exist in lineage if not null (I2)
      - prior nodes are copied unchanged (I3)

    Returns:
      New lineage dict with node appended.
      Returns lineage unchanged on any violation.
    """
    if not isinstance(lineage, dict):
        return dict(lineage) if isinstance(lineage, Mapping) else {}

    if lineage.get("schema_name") != "EXPERIMENT_LINEAGE_V1":
        return dict(lineage)

    if not isinstance(node, dict):
        return dict(lineage)

    if node.get("schema_name") != "EXPERIMENT_NODE_V1":
        return dict(lineage)

    existing_ids = {n["experiment_id"] for n in lineage.get("nodes", [])}

    # I1: uniqueness
    if node["experiment_id"] in existing_ids:
        return dict(lineage)

    # I2: parent must exist (if set)
    parent_id = node.get("parent_experiment_id")
    if parent_id is not None and parent_id not in existing_ids:
        return dict(lineage)

    new_lineage = {
        "schema_name":    lineage["schema_name"],
        "schema_version": lineage["schema_version"],
        "lineage_id":     lineage["lineage_id"],
        "nodes":          [dict(n) for n in lineage.get("nodes", [])] + [dict(node)],
    }
    return new_lineage


# ── Queries (pure, no mutation) ───────────────────────────────────────────────

def get_admitted_nodes(lineage: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return all EXPERIMENT_NODE_V1 nodes with reducer_decision == ADMITTED."""
    return [
        dict(n) for n in lineage.get("nodes", [])
        if n.get("reducer_decision") == "ADMITTED"
    ]


def get_rejected_nodes(lineage: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return all nodes with reducer_decision != ADMITTED (REJECTED or QUARANTINED)."""
    return [
        dict(n) for n in lineage.get("nodes", [])
        if n.get("reducer_decision") != "ADMITTED"
    ]


def get_nodes_by_mutation_family(
    lineage: Mapping[str, Any],
    family: str,
) -> list[dict[str, Any]]:
    """Return all nodes with the given mutation_family."""
    return [
        dict(n) for n in lineage.get("nodes", [])
        if n.get("mutation_family") == family
    ]


def get_nodes_by_skill(
    lineage: Mapping[str, Any],
    skill_id: str,
) -> list[dict[str, Any]]:
    """Return all nodes that target the given skill_id."""
    return [
        dict(n) for n in lineage.get("nodes", [])
        if n.get("skill_id") == skill_id
    ]


def get_node_by_id(
    lineage: Mapping[str, Any],
    experiment_id: str,
) -> dict[str, Any] | None:
    """Return node with given experiment_id, or None."""
    for n in lineage.get("nodes", []):
        if n.get("experiment_id") == experiment_id:
            return dict(n)
    return None


def compute_lineage_hash(lineage: Mapping[str, Any]) -> str:
    """
    Deterministic SHA-256 of the full lineage.
    Same nodes in same order → same hash.
    """
    return sha256_prefixed(dict(lineage))


# ── Node builder ─────────────────────────────────────────────────────────────

def build_experiment_node(
    experiment_id: str,
    skill_id: str,
    candidate_version: str,
    mutation_family: str,
    eval_receipt_hash: str,
    promotion_case_hash: str,
    reducer_decision: str,
    parent_experiment_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Construct a canonical EXPERIMENT_NODE_V1.

    experiment_hash is computed from (experiment_id + skill_id +
    candidate_version + mutation_family + eval_receipt_hash +
    promotion_case_hash) for determinism.
    """
    content = {
        "experiment_id":      experiment_id,
        "skill_id":           skill_id,
        "candidate_version":  candidate_version,
        "mutation_family":    mutation_family,
        "eval_receipt_hash":  eval_receipt_hash,
        "promotion_case_hash": promotion_case_hash,
    }
    node: dict[str, Any] = {
        "schema_name":          "EXPERIMENT_NODE_V1",
        "schema_version":       "1.0.0",
        "experiment_id":        experiment_id,
        "parent_experiment_id": parent_experiment_id,
        "skill_id":             skill_id,
        "candidate_version":    candidate_version,
        "mutation_family":      mutation_family,
        "eval_receipt_hash":    eval_receipt_hash,
        "promotion_case_hash":  promotion_case_hash,
        "experiment_hash":      sha256_prefixed(content),
        "reducer_decision":     reducer_decision,
    }
    if notes is not None:
        node["notes"] = notes
    return node
