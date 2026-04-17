"""Skill Evolution Graph (SEG) — capability lineage memory.

Law:
  The SEG records every skill version node — admitted and rejected.
  It is the capability counterpart to the ELG: while ELG tracks experiments,
  SEG tracks how skill capabilities evolved over time.

Separation of concerns:
  DECISION_LEDGER_V1   ← sovereign: only ADMITTED decisions, governs active_skills
  SKILL_LINEAGE_V1     ← exploration: ALL skill version proposals (admitted + rejected)

Single responsibility:
  make_empty_skill_lineage()    → canonical empty SEG
  append_skill_node()           → append one SKILL_NODE_V1 (append-only)
  get_admitted_skill_nodes()    → filter ADMITTED nodes
  get_nodes_by_skill_id()       → filter by skill_id (version history)
  get_skill_ancestry()          → return chain from node to root
  compute_skill_lineage_hash()  → deterministic sha256

Invariants:
  I1. (skill_id, skill_version) pair is unique within a SEG.
  I2. parent_skill_id / parent_version (if not null) must refer to existing node.
  I3. Prior nodes are never modified (append-only).
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.canonical import sha256_prefixed


# ── Factory ───────────────────────────────────────────────────────────────────

def make_empty_skill_lineage(lineage_id: str) -> dict[str, Any]:
    """Return a canonical empty SKILL_LINEAGE_V1."""
    return {
        "schema_name":    "SKILL_LINEAGE_V1",
        "schema_version": "1.0.0",
        "lineage_id":     lineage_id,
        "nodes":          [],
    }


# ── Append ────────────────────────────────────────────────────────────────────

def append_skill_node(
    lineage: Mapping[str, Any],
    node: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Append one SKILL_NODE_V1 to the skill lineage.

    Rules:
      - (skill_id, skill_version) must be unique (I1)
      - parent must exist if set (I2)
      - prior nodes copied unchanged (I3)

    Returns new lineage dict.
    """
    if not isinstance(lineage, dict):
        return {}

    if lineage.get("schema_name") != "SKILL_LINEAGE_V1":
        return dict(lineage)

    if not isinstance(node, dict):
        return dict(lineage)

    if node.get("schema_name") != "SKILL_NODE_V1":
        return dict(lineage)

    existing_keys = {
        (n["skill_id"], n["skill_version"])
        for n in lineage.get("nodes", [])
    }

    # I1: unique (skill_id, skill_version)
    key = (node.get("skill_id"), node.get("skill_version"))
    if key in existing_keys:
        return dict(lineage)

    # I2: parent must exist
    parent_id = node.get("parent_skill_id")
    parent_ver = node.get("parent_version")
    if parent_id is not None:
        if (parent_id, parent_ver) not in existing_keys:
            return dict(lineage)

    return {
        "schema_name":    lineage["schema_name"],
        "schema_version": lineage["schema_version"],
        "lineage_id":     lineage["lineage_id"],
        "nodes":          [dict(n) for n in lineage.get("nodes", [])] + [dict(node)],
    }


# ── Queries ───────────────────────────────────────────────────────────────────

def get_admitted_skill_nodes(lineage: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return all SKILL_NODE_V1 nodes with reducer_decision == ADMITTED."""
    return [
        dict(n) for n in lineage.get("nodes", [])
        if n.get("reducer_decision") == "ADMITTED"
    ]


def get_nodes_by_skill_id(
    lineage: Mapping[str, Any],
    skill_id: str,
) -> list[dict[str, Any]]:
    """Return all versions of a skill (all reducer outcomes)."""
    return [
        dict(n) for n in lineage.get("nodes", [])
        if n.get("skill_id") == skill_id
    ]


def get_skill_ancestry(
    lineage: Mapping[str, Any],
    skill_id: str,
    skill_version: str,
) -> list[dict[str, Any]]:
    """
    Return the lineage chain from the given node back to the root.

    Result is ordered root → target (oldest to newest).
    Returns empty list if node not found.
    """
    # Build a lookup
    lookup: dict[tuple[str, str | None], dict[str, Any]] = {}
    for n in lineage.get("nodes", []):
        lookup[(n["skill_id"], n["skill_version"])] = n

    chain = []
    current = lookup.get((skill_id, skill_version))
    while current is not None:
        chain.append(dict(current))
        p_id = current.get("parent_skill_id")
        p_ver = current.get("parent_version")
        if p_id is None:
            break
        current = lookup.get((p_id, p_ver))

    chain.reverse()
    return chain


def compute_skill_lineage_hash(lineage: Mapping[str, Any]) -> str:
    """Deterministic SHA-256 of the full skill lineage."""
    return sha256_prefixed(dict(lineage))


# ── Node builder ─────────────────────────────────────────────────────────────

def build_skill_node(
    skill_id: str,
    skill_version: str,
    origin_experiments: list[str],
    promotion_case_hash: str,
    reducer_decision: str,
    parent_skill_id: str | None = None,
    parent_version: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Construct a canonical SKILL_NODE_V1."""
    node: dict[str, Any] = {
        "schema_name":          "SKILL_NODE_V1",
        "schema_version":       "1.0.0",
        "skill_id":             skill_id,
        "skill_version":        skill_version,
        "parent_skill_id":      parent_skill_id,
        "parent_version":       parent_version,
        "origin_experiments":   list(origin_experiments),
        "promotion_case_hash":  promotion_case_hash,
        "reducer_decision":     reducer_decision,
    }
    if notes is not None:
        node["notes"] = notes
    return node
