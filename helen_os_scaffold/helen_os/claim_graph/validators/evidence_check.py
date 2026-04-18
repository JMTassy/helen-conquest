"""
Evidence completeness validation for CLAIM_GRAPH_V1

Validates evidence handles and replay bundles.
"""

from typing import Any, Dict, List, Tuple
from ..error_codes import ValidationError, MISSING_EVIDENCE_HANDLE_FIELD


def validate_evidence(graph_dict: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate evidence handles:
    - 7 required fields present
    - Hash patterns valid
    - Replay commands valid

    Args:
        graph_dict: Parsed JSON graph object

    Returns:
        (is_valid, errors)
    """
    errors = []

    nodes = graph_dict.get("nodes", [])

    for node in nodes:
        node_id = node.get("id")
        kind = node.get("kind")

        if kind == "evidence_handle":
            handle = node.get("handle", {})

            # Check all 7 required fields
            required_fields = {
                "repo_commit",
                "paths",
                "artifact_hash",
                "receipt_id",
                "receipt_hash",
                "replay_command",
                "expected_artifact_hashes",
            }

            for field in required_fields:
                if field not in handle or handle[field] is None:
                    errors.append(ValidationError(
                        code=MISSING_EVIDENCE_HANDLE_FIELD,
                        node_id=node_id,
                        field=field,
                        message=f"Evidence handle missing required field: {field}"
                    ))

            # Validate field types and patterns
            if handle.get("artifact_hash"):
                if not str(handle["artifact_hash"]).startswith("sha256:"):
                    errors.append(ValidationError(
                        code=MISSING_EVIDENCE_HANDLE_FIELD,
                        node_id=node_id,
                        field="artifact_hash",
                        message="artifact_hash must match pattern ^sha256:"
                    ))

            if handle.get("receipt_hash"):
                if not str(handle["receipt_hash"]).startswith("sha256:"):
                    errors.append(ValidationError(
                        code=MISSING_EVIDENCE_HANDLE_FIELD,
                        node_id=node_id,
                        field="receipt_hash",
                        message="receipt_hash must match pattern ^sha256:"
                    ))

            if handle.get("replay_command"):
                if not isinstance(handle["replay_command"], str) or len(handle["replay_command"]) == 0:
                    errors.append(ValidationError(
                        code=MISSING_EVIDENCE_HANDLE_FIELD,
                        node_id=node_id,
                        field="replay_command",
                        message="replay_command must be non-empty string"
                    ))

            if handle.get("expected_artifact_hashes"):
                expected = handle["expected_artifact_hashes"]
                if not isinstance(expected, list) or len(expected) == 0:
                    errors.append(ValidationError(
                        code=MISSING_EVIDENCE_HANDLE_FIELD,
                        node_id=node_id,
                        field="expected_artifact_hashes",
                        message="expected_artifact_hashes must be non-empty array"
                    ))
                else:
                    for idx, hash_val in enumerate(expected):
                        if not str(hash_val).startswith("sha256:"):
                            errors.append(ValidationError(
                                code=MISSING_EVIDENCE_HANDLE_FIELD,
                                node_id=node_id,
                                field=f"expected_artifact_hashes[{idx}]",
                                message=f"Hash must match pattern ^sha256:"
                            ))

    return len(errors) == 0, errors
