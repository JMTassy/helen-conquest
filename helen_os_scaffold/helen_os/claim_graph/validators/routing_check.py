"""
Routing preconditions validation for CLAIM_GRAPH_V1

Validates that nodes are routable to Mayor only if conditions are met.
"""

from typing import Any, Dict, List, Set, Tuple
from ..error_codes import (
    ValidationError,
    UNRESOLVED_REFERENCE,
    POLICY_QUARANTINE_ACTIVE,
    WILD_ROUTING_VIOLATION,
)


def validate_routing(graph_dict: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate routing preconditions:
    - Node admissibility = ADMISSIBLE
    - Not wild_text
    - All required evidence edges exist
    - No quarantine edges applied
    - No policy violations

    Args:
        graph_dict: Parsed JSON graph object

    Returns:
        (is_valid, errors)
    """
    errors = []

    nodes = graph_dict.get("nodes", [])
    edges = graph_dict.get("edges", [])

    # Build node map
    node_map = {node.get("id"): node for node in nodes}

    # Build edge map for quick lookup
    edges_from = {}  # Map from_id -> list of edges
    edges_to = {}    # Map to_id -> list of edges
    for edge in edges:
        from_id = edge.get("from")
        to_id = edge.get("to")

        if from_id not in edges_from:
            edges_from[from_id] = []
        edges_from[from_id].append(edge)

        if to_id not in edges_to:
            edges_to[to_id] = []
        edges_to[to_id].append(edge)

    # Pre-pass: check all wild_text nodes have route_to_mayor=false (TEMPLE_SANDBOX_POLICY_V1)
    for node in nodes:
        node_id = node.get("id")
        kind = node.get("kind")

        if kind == "wild_text":
            route_to_mayor = node.get("route_to_mayor")
            # Must be explicitly false or null (missing is treated as false)
            if route_to_mayor is True:
                errors.append(ValidationError(
                    code=WILD_ROUTING_VIOLATION,
                    node_id=node_id,
                    message="wild_text node has route_to_mayor=true, violating TEMPLE_SANDBOX_POLICY_V1 §C"
                ))

    for node in nodes:
        node_id = node.get("id")
        kind = node.get("kind")
        admissibility = node.get("admissibility")

        # Rule 1: Check admissibility
        if admissibility != "ADMISSIBLE":
            # Not routable; log as informational, not error
            continue

        # Rule 2: wild_text cannot be routable even if marked admissible
        # Structural bar by TEMPLE_SANDBOX_POLICY_V1: default classification prevents routing
        if kind == "wild_text":
            # wild_text nodes are never routable to Mayor, even if marked ADMISSIBLE
            # This enforces the policy requirement that all Temple artifacts remain in quarantine
            continue

        # Rule 3: Check for required evidence edges
        if kind == "claim":
            # Claims should have at least one SUPPORTS or DEPENDS_ON edge
            # from an evidence_handle or receipt
            incoming = edges_to.get(node_id, [])
            has_evidence = any(
                edge.get("type") in {"SUPPORTS", "BINDS"}
                for edge in incoming
            )

            if not has_evidence:
                # Check if evidence_handle nodes are present in graph
                evidence_nodes = [n for n in nodes if n.get("kind") == "evidence_handle"]
                if evidence_nodes:
                    # We have evidence nodes but claim doesn't reference them
                    errors.append(ValidationError(
                        code=UNRESOLVED_REFERENCE,
                        node_id=node_id,
                        message="Claim has no incoming SUPPORTS or BINDS edges from evidence"
                    ))

        # Rule 4: Check for quarantine edges pointing to this node
        incoming = edges_to.get(node_id, [])
        for edge in incoming:
            if edge.get("type") == "QUARANTINES":
                errors.append(ValidationError(
                    code=POLICY_QUARANTINE_ACTIVE,
                    node_id=node_id,
                    edge_id=edge.get("id"),
                    message="Node is quarantined by policy and cannot route to Mayor"
                ))

    return len(errors) == 0, errors


def validate_references(
    graph_dict: Dict[str, Any],
    additional_bundles: Dict[str, Any] = None
) -> Tuple[bool, List[ValidationError]]:
    """
    Validate that all referenced external objects exist.

    Args:
        graph_dict: Parsed JSON graph object
        additional_bundles: Optional dict of {claim_graph_ref: obj, tasp_report_ref: obj, ...}

    Returns:
        (is_valid, errors)
    """
    errors = []
    bundles = additional_bundles or {}

    nodes = graph_dict.get("nodes", [])

    for node in nodes:
        node_id = node.get("id")

        # Check for external references
        for ref_field in ["claim_graph_ref", "tasp_report_ref", "score_vector_ref", "federation_receipt_ref"]:
            ref_value = node.get(ref_field)
            if ref_value and ref_value not in bundles:
                errors.append(ValidationError(
                    code=UNRESOLVED_REFERENCE,
                    node_id=node_id,
                    field=ref_field,
                    message=f"Reference not found: {ref_value}"
                ))

    return len(errors) == 0, errors
