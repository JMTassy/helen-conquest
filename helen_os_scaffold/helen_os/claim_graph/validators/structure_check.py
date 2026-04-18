"""
Structural validation for CLAIM_GRAPH_V1

Checks uniqueness, references, edge legality, and acyclicity.
"""

from typing import Any, Dict, List, Set, Tuple
from ..error_codes import (
    ValidationError, DUPLICATE_NODE_ID, DUPLICATE_EDGE_ID,
    UNKNOWN_EDGE_ENDPOINT, ILLEGAL_EDGE_TYPE, ILLEGAL_DEPENDENCY_CYCLE
)
from ..edge_rules import is_edge_legal


def validate_structure(graph_dict: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate graph structure: IDs, references, edge legality, acyclicity.

    Args:
        graph_dict: Parsed JSON graph object

    Returns:
        (is_valid, errors)
    """
    errors = []

    nodes = graph_dict.get("nodes", [])
    edges = graph_dict.get("edges", [])

    # Check duplicate node IDs
    node_ids = set()
    node_kinds = {}  # Map id -> kind
    for node in nodes:
        node_id = node.get("id")
        if node_id in node_ids:
            errors.append(ValidationError(
                code=DUPLICATE_NODE_ID,
                node_id=node_id,
                message=f"Duplicate node ID: {node_id}"
            ))
        node_ids.add(node_id)
        node_kinds[node_id] = node.get("kind")

    # Check duplicate edge IDs
    edge_ids = set()
    for edge in edges:
        edge_id = edge.get("id")
        if edge_id in edge_ids:
            errors.append(ValidationError(
                code=DUPLICATE_EDGE_ID,
                edge_id=edge_id,
                message=f"Duplicate edge ID: {edge_id}"
            ))
        edge_ids.add(edge_id)

    # Check edge endpoints exist and edge types are legal
    for edge in edges:
        edge_id = edge.get("id")
        from_id = edge.get("from")
        to_id = edge.get("to")
        edge_type = edge.get("type")

        # Check source exists
        if from_id not in node_ids:
            errors.append(ValidationError(
                code=UNKNOWN_EDGE_ENDPOINT,
                edge_id=edge_id,
                message=f"Edge source not found: {from_id}"
            ))
            continue

        # Check target exists
        if to_id not in node_ids:
            errors.append(ValidationError(
                code=UNKNOWN_EDGE_ENDPOINT,
                edge_id=edge_id,
                message=f"Edge target not found: {to_id}"
            ))
            continue

        # Check edge legality
        source_kind = node_kinds.get(from_id)
        target_kind = node_kinds.get(to_id)

        if not is_edge_legal(source_kind, target_kind, edge_type):
            errors.append(ValidationError(
                code=ILLEGAL_EDGE_TYPE,
                edge_id=edge_id,
                message=f"Illegal edge {edge_type} from {source_kind} to {target_kind}"
            ))

    # Check for cycles
    cycle_errors = check_acyclicity(edges)
    errors.extend(cycle_errors)

    return len(errors) == 0, errors


def check_acyclicity(edges: List[Dict[str, Any]]) -> List[ValidationError]:
    """
    Detect cycles in claim dependency graph using topological sort.

    Args:
        edges: List of edge objects

    Returns:
        List of errors if cycles detected
    """
    errors = []

    # Build adjacency list
    graph = {}
    in_degree = {}
    all_nodes = set()

    for edge in edges:
        from_id = edge.get("from")
        to_id = edge.get("to")
        edge_type = edge.get("type")

        # Only dependency-based edges count for cycle detection
        if edge_type in {"DEPENDS_ON", "SUPPORTS", "REFUTES"}:
            if from_id not in graph:
                graph[from_id] = []
            graph[from_id].append(to_id)

            if to_id not in in_degree:
                in_degree[to_id] = 0
            in_degree[to_id] += 1

            all_nodes.add(from_id)
            all_nodes.add(to_id)

    # Initialize in_degree for all nodes
    for node_id in all_nodes:
        if node_id not in in_degree:
            in_degree[node_id] = 0

    # Kahn's algorithm for topological sort
    queue = [node for node in all_nodes if in_degree[node] == 0]
    processed = 0

    while queue:
        current = queue.pop(0)
        processed += 1

        if current in graph:
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    # If not all nodes were processed, there's a cycle
    if processed < len(all_nodes):
        # Find nodes in cycle
        cycle_nodes = [node for node in all_nodes if in_degree[node] > 0]
        errors.append(ValidationError(
            code=ILLEGAL_DEPENDENCY_CYCLE,
            message=f"Circular dependency detected in nodes: {cycle_nodes}"
        ))

    return errors


def build_node_map(nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build map of node ID -> node object"""
    return {node.get("id"): node for node in nodes}


def build_adjacency_list(edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build adjacency list from edges"""
    graph = {}
    for edge in edges:
        from_id = edge.get("from")
        to_id = edge.get("to")
        if from_id not in graph:
            graph[from_id] = []
        graph[from_id].append(to_id)
    return graph
