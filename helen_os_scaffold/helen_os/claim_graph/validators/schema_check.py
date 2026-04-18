"""
Schema validation for CLAIM_GRAPH_V1

Validates JSON structure against frozen schema.
"""

import json
from typing import Any, Dict, List, Tuple
from ..error_codes import ValidationError, SCHEMA_INVALID


def validate_schema(graph_dict: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate graph structure against CLAIM_GRAPH_V1 schema.

    Args:
        graph_dict: Parsed JSON graph object

    Returns:
        (is_valid, errors)
    """
    errors = []

    # Check root structure
    required_root = {"spec", "graph_meta", "nodes", "edges"}
    if not required_root.issubset(set(graph_dict.keys())):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="Missing required root fields: spec, graph_meta, nodes, edges"
        ))
        return False, errors

    # Validate spec
    spec = graph_dict.get("spec", {})
    if not isinstance(spec, dict):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="spec must be object"
        ))
        return False, errors

    if spec.get("name") != "CLAIM_GRAPH_V1":
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="spec.name must equal 'CLAIM_GRAPH_V1'"
        ))
        return False, errors

    # Validate graph_meta
    graph_meta = graph_dict.get("graph_meta", {})
    if not isinstance(graph_meta, dict):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="graph_meta must be object"
        ))
        return False, errors

    # Check sha256 pattern for hashes
    env_ref = graph_meta.get("environment_ref", "")
    policy_ref = graph_meta.get("policy_ref", "")

    if env_ref and not env_ref.startswith("sha256:"):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="environment_ref must match pattern ^sha256:"
        ))

    if policy_ref and not policy_ref.startswith("sha256:"):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="policy_ref must match pattern ^sha256:"
        ))

    # Validate nodes array
    nodes = graph_dict.get("nodes", [])
    if not isinstance(nodes, list):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="nodes must be array"
        ))
        return False, errors

    for idx, node in enumerate(nodes):
        node_errors = validate_node_schema(node, idx)
        errors.extend(node_errors)

    # Validate edges array
    edges = graph_dict.get("edges", [])
    if not isinstance(edges, list):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message="edges must be array"
        ))
        return False, errors

    for idx, edge in enumerate(edges):
        edge_errors = validate_edge_schema(edge, idx)
        errors.extend(edge_errors)

    return len(errors) == 0, errors


def validate_node_schema(node: Any, idx: int) -> List[ValidationError]:
    """Validate single node against schema"""
    errors = []

    if not isinstance(node, dict):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message=f"Node {idx} must be object"
        ))
        return errors

    # Required fields
    required = {"id", "kind", "epistemic_state", "admissibility"}
    if not required.issubset(set(node.keys())):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message=f"Node {idx} missing required fields: {required - set(node.keys())}"
        ))

    node_id = node.get("id")
    kind = node.get("kind")

    # Validate id pattern
    if node_id:
        if not isinstance(node_id, str) or not node_id.startswith("N-"):
            errors.append(ValidationError(
                code=SCHEMA_INVALID,
                node_id=str(node_id),
                message="Node id must match pattern ^N-[0-9A-Za-z_-]{4,}$"
            ))

    # Validate kind enum
    valid_kinds = {"claim", "evidence_handle", "artifact", "receipt", "witness", "policy", "definition", "wild_text"}
    if kind not in valid_kinds:
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            node_id=str(node_id),
            message=f"Node kind must be one of {valid_kinds}"
        ))

    # Validate epistemic_state enum
    epistemic = node.get("epistemic_state")
    valid_epistemic = {"STAGED", "WITNESSED", "VERIFIED", "FALSIFIED"}
    if epistemic not in valid_epistemic:
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            node_id=str(node_id),
            message=f"epistemic_state must be one of {valid_epistemic}"
        ))

    # Validate admissibility enum
    admissibility = node.get("admissibility")
    valid_admissibility = {"ADMISSIBLE", "QUARANTINED"}
    if admissibility not in valid_admissibility:
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            node_id=str(node_id),
            message=f"admissibility must be one of {valid_admissibility}"
        ))

    # Validate evidence_handle schema (7 required fields)
    if kind == "evidence_handle":
        handle = node.get("handle", {})
        if not isinstance(handle, dict):
            errors.append(ValidationError(
                code=SCHEMA_INVALID,
                node_id=str(node_id),
                message="evidence_handle node must have 'handle' object"
            ))
        else:
            required_handle_fields = {
                "repo_commit", "paths", "artifact_hash", "receipt_id",
                "receipt_hash", "replay_command", "expected_artifact_hashes"
            }
            if not required_handle_fields.issubset(set(handle.keys())):
                errors.append(ValidationError(
                    code=SCHEMA_INVALID,
                    node_id=str(node_id),
                    message=f"evidence_handle missing fields: {required_handle_fields - set(handle.keys())}"
                ))

    return errors


def validate_edge_schema(edge: Any, idx: int) -> List[ValidationError]:
    """Validate single edge against schema"""
    errors = []

    if not isinstance(edge, dict):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message=f"Edge {idx} must be object"
        ))
        return errors

    # Required fields
    required = {"id", "type", "from", "to"}
    if not required.issubset(set(edge.keys())):
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            message=f"Edge {idx} missing required fields: {required - set(edge.keys())}"
        ))

    edge_id = edge.get("id")
    edge_type = edge.get("type")

    # Validate id pattern
    if edge_id:
        if not isinstance(edge_id, str) or not edge_id.startswith("E-"):
            errors.append(ValidationError(
                code=SCHEMA_INVALID,
                edge_id=str(edge_id),
                message="Edge id must match pattern ^E-[0-9A-Za-z_-]{4,}$"
            ))

    # Validate type enum
    valid_types = {
        "SUPPORTS", "REFUTES", "DEPENDS_ON", "PRODUCES", "BINDS",
        "WITNESSES", "GATES", "QUARANTINES", "ROUTES"
    }
    if edge_type not in valid_types:
        errors.append(ValidationError(
            code=SCHEMA_INVALID,
            edge_id=str(edge_id),
            message=f"Edge type must be one of {valid_types}"
        ))

    return errors
