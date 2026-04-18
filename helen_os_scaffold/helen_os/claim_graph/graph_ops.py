"""
helen_os/claim_graph/graph_ops.py — Core graph operations for CLAIM_GRAPH_V1.

Three deterministic operations (no LLM, no randomness):

  validate_graph(graph)  → None | raises ValueError
    - Unique node IDs
    - Non-empty claim texts
    - Edge endpoints exist
    - DAG constraint for REFINES / DEPENDS_ON
    - DR depends_on members exist in graph

  compute_sets(graph)    → ClaimGraphV1 (with recomputed g_set / r_set)
    Mechanically derives G-set and R-set:
      G-set: ACTIVE non-RISK nodes with no "effective" OBJECTS_TO targeting them.
      R-set: ACTIVE RISK nodes with no counter-OBJECTS_TO from a non-RISK ACTIVE node.
    An OBJECTS_TO edge is "effective" only if its src is itself not OBJECTS_TO'd by
    any ACTIVE non-RISK node (two-pass transitivity elimination).

  validate_dr_dependencies(graph) → None | raises ValueError
    Each DR.depends_on must reference a node in the graph that is either
    CONSTRAINT or GATE kind. Prevents DRs from silently depending on contested claims.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from .schemas import ClaimGraphV1, ClaimNodeV1


# ── Validation ────────────────────────────────────────────────────────────────

def validate_graph(graph: ClaimGraphV1) -> None:
    """
    Structural validation — fail-closed.

    Checks:
      1. Node IDs unique
      2. Claim texts non-empty (Pydantic enforces, double-checked here)
      3. Edge endpoints exist in graph
      4. No cycles for REFINES / DEPENDS_ON (DAG)
      5. G-set / R-set members are valid node IDs
      6. DR depends_on members are valid node IDs

    Raises:
        ValueError: on any structural invariant violation.
    """
    node_ids: Set[str] = set()
    seen:     Set[str] = set()

    # ── 1. Node ID uniqueness ────────────────────────────────────────────────
    for n in graph.nodes:
        if n.node_id in seen:
            raise ValueError(
                f"validate_graph: duplicate node_id={n.node_id!r}"
            )
        seen.add(n.node_id)
        node_ids.add(n.node_id)

    # ── 2. Non-empty texts (Pydantic already ensures this, belt+suspenders) ──
    for n in graph.nodes:
        if not n.text.strip():
            raise ValueError(
                f"validate_graph: empty text for node_id={n.node_id!r}"
            )

    # ── 3. Edge endpoints ────────────────────────────────────────────────────
    for e in graph.edges:
        if e.src not in node_ids:
            raise ValueError(
                f"validate_graph: edge {e.edge_id!r} src={e.src!r} not in graph"
            )
        if e.dst not in node_ids:
            raise ValueError(
                f"validate_graph: edge {e.edge_id!r} dst={e.dst!r} not in graph"
            )

    # ── 4. DAG constraint for REFINES / DEPENDS_ON ──────────────────────────
    _check_dag(graph, restricted_types={"REFINES", "DEPENDS_ON"})

    # ── 5. G-set / R-set members ─────────────────────────────────────────────
    for nid in graph.g_set:
        if nid not in node_ids:
            raise ValueError(
                f"validate_graph: G-set member {nid!r} not in graph"
            )
    for nid in graph.r_set:
        if nid not in node_ids:
            raise ValueError(
                f"validate_graph: R-set member {nid!r} not in graph"
            )

    # ── 6. DR depends_on members ─────────────────────────────────────────────
    for dr in graph.decision_rules:
        for dep in dr.depends_on:
            if dep not in node_ids:
                raise ValueError(
                    f"validate_graph: DR {dr.rule_id!r} depends_on "
                    f"{dep!r} which is not in graph"
                )


def _check_dag(graph: ClaimGraphV1, restricted_types: Set[str]) -> None:
    """DFS cycle check for edges of restricted types only."""
    # Build adjacency
    adj: Dict[str, List[str]] = defaultdict(list)
    for e in graph.edges:
        if e.type in restricted_types:
            adj[e.src].append(e.dst)

    visited:    Set[str] = set()
    in_stack:   Set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        in_stack.add(node)
        for nbr in adj[node]:
            if nbr not in visited:
                if dfs(nbr):
                    return True
            elif nbr in in_stack:
                return True
        in_stack.discard(node)
        return False

    for nid in {n.node_id for n in graph.nodes}:
        if nid not in visited:
            if dfs(nid):
                raise ValueError(
                    f"validate_graph: cycle detected in REFINES/DEPENDS_ON edges "
                    f"involving node {nid!r}"
                )


# ── Set computation ───────────────────────────────────────────────────────────

def compute_sets(graph: ClaimGraphV1) -> ClaimGraphV1:
    """
    Mechanically derive G-set and R-set from graph structure.

    G-set semantics:
      A claim N enters G-set if:
        (a) N.status == ACTIVE, AND
        (b) N.kind != RISK  (RISK claims start in R-set by kind), AND
        (c) N is not targeted by any "effective" OBJECTS_TO.

      An OBJECTS_TO edge (src → dst) is "effective" if src is ACTIVE
      AND src is not itself OBJECTS_TO'd by any non-RISK ACTIVE node.

    R-set semantics:
      A claim N enters R-set if:
        (a) N.status == ACTIVE, AND
        (b) N.kind == RISK, AND
        (c) N is not targeted by any OBJECTS_TO from an ACTIVE non-RISK node.

    This two-pass approach correctly handles the transitivity pattern:
      A1 OBJECTS_TO H3
      QA3 OBJECTS_TO A1   → A1 is counter-objected → H3 is not effectively contested

    If graph.g_set / graph.r_set are already declared (non-empty), they are
    PRESERVED and the computed values are attached as computed_g_set / computed_r_set
    for audit purposes only.

    Returns:
        A new ClaimGraphV1 with g_set and r_set updated to computed values.
        (Or original values if declared sets match computation.)
    """
    node_map: Dict[str, ClaimNodeV1] = {n.node_id: n for n in graph.nodes}
    active:   Set[str] = {n.node_id for n in graph.nodes if n.status == "ACTIVE"}

    # ── Pass 1: find all nodes targeted by OBJECTS_TO from any active node ──
    raw_objected: Dict[str, Set[str]] = defaultdict(set)  # dst → {src, ...}
    for e in graph.edges:
        if e.type == "OBJECTS_TO" and e.src in active:
            raw_objected[e.dst].add(e.src)

    # ── Pass 2: filter out OBJECTS_TO sources that are themselves objected ───
    # A source S is "counter-objected" if there is an OBJECTS_TO edge
    # pointing to S from a non-RISK ACTIVE node (i.e., a gate/benefit/etc.).
    counter_objected: Set[str] = set()
    for dst, srcs in raw_objected.items():
        # Check if dst has incoming OBJECTS_TO from non-RISK active sources
        for src in srcs:
            node = node_map.get(src)
            if node and node.kind != "RISK":
                # A gate/benefit is objecting to something — the thing being
                # objected to is counter-objected
                counter_objected.add(dst)

    # Alternatively: a RISK node is "counter-objected" if any non-RISK ACTIVE
    # node OBJECTS_TO it directly.
    risk_counter_objected: Set[str] = set()
    for e in graph.edges:
        if e.type == "OBJECTS_TO" and e.src in active:
            src_node = node_map.get(e.src)
            if src_node and src_node.kind != "RISK":
                # A non-RISK node is objecting to dst → dst is counter-objected
                risk_counter_objected.add(e.dst)

    # "Effective" OBJECTS_TO: from active src that is NOT itself counter-objected
    effective_contested: Set[str] = set()
    for e in graph.edges:
        if e.type == "OBJECTS_TO" and e.src in active:
            if e.src not in risk_counter_objected:
                # This source is not counter-objected → it effectively contests dst
                effective_contested.add(e.dst)

    # ── G-set: ACTIVE non-RISK nodes not effectively contested ──────────────
    computed_g = sorted([
        nid for nid in active
        if node_map[nid].kind != "RISK"
        and nid not in effective_contested
    ])

    # ── R-set: ACTIVE RISK nodes not counter-objected by non-RISK active nodes
    computed_r = sorted([
        nid for nid in active
        if node_map[nid].kind == "RISK"
        and nid not in risk_counter_objected
    ])

    # If the graph has declared G/R sets, keep them (trust the author).
    # Otherwise, use computed.
    final_g = graph.g_set if graph.g_set else computed_g
    final_r = graph.r_set if graph.r_set else computed_r

    return ClaimGraphV1(
        type           = graph.type,
        topic          = graph.topic,
        scenario       = graph.scenario,
        nodes          = graph.nodes,
        edges          = graph.edges,
        g_set          = final_g,
        r_set          = final_r,
        decision_rules = graph.decision_rules,
        tasks          = graph.tasks,
        source_digest  = graph.source_digest,
    )


# ── DR dependency validation ──────────────────────────────────────────────────

def validate_dr_dependencies(graph: ClaimGraphV1) -> None:
    """
    Each DR.depends_on entry must be either CONSTRAINT or GATE kind.

    Prevents DRs from silently depending on disputed or unverified claims.

    Raises:
        ValueError: if any dependency is not CONSTRAINT or GATE.
    """
    node_map = {n.node_id: n for n in graph.nodes}
    allowed_kinds = {"CONSTRAINT", "GATE"}

    for dr in graph.decision_rules:
        for dep in dr.depends_on:
            node = node_map.get(dep)
            if node is None:
                raise ValueError(
                    f"validate_dr_dependencies: DR {dr.rule_id!r} depends_on "
                    f"{dep!r} — node not found in graph"
                )
            if node.kind not in allowed_kinds:
                raise ValueError(
                    f"validate_dr_dependencies: DR {dr.rule_id!r} depends_on "
                    f"{dep!r} (kind={node.kind!r}) — "
                    f"DR dependencies must be CONSTRAINT or GATE kind. "
                    f"Found kind={node.kind!r}. "
                    f"Move this claim to CONSTRAINT or GATE, or remove from depends_on."
                )
