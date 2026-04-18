"""
Epistemic legality validation for CLAIM_GRAPH_V1

Enforces tier/admissibility rules and structural quarantine.
"""

from typing import Any, Dict, List, Tuple
from ..error_codes import (
    ValidationError, TIER_PROMOTION_VIOLATION, WILD_ROUTING_VIOLATION
)


def validate_epistemic(graph_dict: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate epistemic constraints:
    - Tier III must be QUARANTINED
    - wild_text must be QUARANTINED and route_to_mayor=false
    - Tier promotion rules

    Args:
        graph_dict: Parsed JSON graph object

    Returns:
        (is_valid, errors)
    """
    errors = []

    nodes = graph_dict.get("nodes", [])
    edges = graph_dict.get("edges", [])

    # Build node map for reference
    node_map = {node.get("id"): node for node in nodes}

    for node in nodes:
        node_id = node.get("id")
        kind = node.get("kind")
        tier = node.get("tier")
        admissibility = node.get("admissibility")

        # Rule 1: Tier III must be QUARANTINED
        if kind != "wild_text" and tier == "III":
            if admissibility != "QUARANTINED":
                errors.append(ValidationError(
                    code=TIER_PROMOTION_VIOLATION,
                    node_id=node_id,
                    message="Tier III must have admissibility=QUARANTINED"
                ))

        # Rule 2: wild_text must be QUARANTINED
        if kind == "wild_text":
            if admissibility != "QUARANTINED":
                errors.append(ValidationError(
                    code=TIER_PROMOTION_VIOLATION,
                    node_id=node_id,
                    message="wild_text node must be QUARANTINED"
                ))

            # Rule 3: wild_text cannot route to Mayor
            route_to_mayor = node.get("route_to_mayor", True)
            if route_to_mayor is not False:
                errors.append(ValidationError(
                    code=WILD_ROUTING_VIOLATION,
                    node_id=node_id,
                    message="wild_text node cannot route to Mayor (route_to_mayor must be false)"
                ))

        # Rule 4: No ROUTES edge from QUARANTINED nodes
        if admissibility == "QUARANTINED":
            for edge in edges:
                if edge.get("from") == node_id and edge.get("type") == "ROUTES":
                    errors.append(ValidationError(
                        code=WILD_ROUTING_VIOLATION,
                        node_id=node_id,
                        edge_id=edge.get("id"),
                        message="QUARANTINED node cannot have ROUTES edge"
                    ))

    return len(errors) == 0, errors
