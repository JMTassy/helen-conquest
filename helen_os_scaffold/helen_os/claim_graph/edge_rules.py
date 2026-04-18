"""
Edge legality rules for CLAIM_GRAPH_V1

Defines which edge types are permitted between which node kinds.
"""

# Node kinds (8 canonical types)
NODE_KINDS = {
    "claim",
    "evidence_handle",
    "artifact",
    "receipt",
    "witness",
    "policy",
    "definition",
    "wild_text",
}

# Edge types (9 canonical types)
EDGE_TYPES = {
    "SUPPORTS",      # source supports target
    "REFUTES",       # source refutes target
    "DEPENDS_ON",    # source depends on target
    "PRODUCES",      # source produces target (e.g., claim→artifact)
    "BINDS",         # source binds target (e.g., receipt binds evidence)
    "WITNESSES",     # source witnesses target
    "GATES",         # source gates target (policy gates claim)
    "QUARANTINES",   # source quarantines target
    "ROUTES",        # source routes to target (governance routing)
}

# Edge legality matrix: (source_kind, target_kind) -> set of allowed edge types
EDGE_LEGALITY = {
    # claim edges
    ("claim", "claim"): {"SUPPORTS", "REFUTES", "DEPENDS_ON"},
    ("claim", "evidence_handle"): {"SUPPORTS", "DEPENDS_ON"},
    ("claim", "artifact"): {"PRODUCES", "SUPPORTS"},
    ("claim", "receipt"): {"BINDS"},
    ("claim", "witness"): {"DEPENDS_ON"},
    ("claim", "policy"): {"GATES", "DEPENDS_ON"},
    ("claim", "definition"): {"DEPENDS_ON"},
    ("claim", "wild_text"): {"REFUTES"},

    # evidence_handle edges
    ("evidence_handle", "artifact"): {"PRODUCES"},
    ("evidence_handle", "receipt"): {"BINDS"},
    ("evidence_handle", "claim"): {"SUPPORTS"},

    # artifact edges
    ("artifact", "artifact"): {"DEPENDS_ON"},
    ("artifact", "receipt"): {"BINDS"},

    # receipt edges
    ("receipt", "claim"): {"BINDS"},
    ("receipt", "evidence_handle"): {"BINDS"},
    ("receipt", "artifact"): {"BINDS"},

    # witness edges
    ("witness", "claim"): {"WITNESSES"},
    ("witness", "evidence_handle"): {"WITNESSES"},
    ("witness", "artifact"): {"WITNESSES"},

    # policy edges
    ("policy", "claim"): {"GATES", "QUARANTINES"},
    ("policy", "evidence_handle"): {"GATES"},
    ("policy", "wild_text"): {"QUARANTINES"},

    # definition edges
    ("definition", "claim"): {"SUPPORTS"},
    ("definition", "evidence_handle"): {"SUPPORTS"},

    # wild_text edges (severely restricted)
    ("wild_text", "wild_text"): {"DEPENDS_ON"},
    ("wild_text", "definition"): {"DEPENDS_ON"},
}


def is_edge_legal(source_kind: str, target_kind: str, edge_type: str) -> bool:
    """
    Check if an edge type is legal for given source/target node kinds.

    Args:
        source_kind: Kind of source node
        target_kind: Kind of target node
        edge_type: Type of edge

    Returns:
        True if edge is legal, False otherwise
    """
    key = (source_kind, target_kind)
    if key not in EDGE_LEGALITY:
        return False
    return edge_type in EDGE_LEGALITY[key]


def get_illegal_routing_edge_types(admissibility: str) -> set:
    """
    Get edge types that are illegal from a quarantined node.

    Args:
        admissibility: Either "ADMISSIBLE" or "QUARANTINED"

    Returns:
        Set of edge types that cannot originate from this node
    """
    if admissibility == "QUARANTINED":
        return {"ROUTES"}  # No routing from quarantined nodes
    return set()


# Self-loop rules: which node kinds can have self-edges
SELF_LOOP_ALLOWED = {
    # Generally disallowed; only explicit cases permitted
}


def allows_self_loop(node_kind: str) -> bool:
    """Check if a node kind can have self-edges"""
    return node_kind in SELF_LOOP_ALLOWED
