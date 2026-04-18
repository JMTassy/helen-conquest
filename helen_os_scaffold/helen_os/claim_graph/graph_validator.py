"""
CLAIM_GRAPH_V1 Constitutional Membrane Validator

The narrowest point in the pipeline:
if validation is weak, every later layer lies cleanly.

This validator is the choke-point between free symbolic generation
and governed processing.
"""

import json
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, asdict

from .error_codes import ValidationError, ValidationWarning
from .validators import (
    validate_schema,
    validate_structure,
    validate_epistemic,
    validate_evidence,
    validate_routing,
    validate_references,
)


@dataclass
class ValidationResult:
    """Deterministic validation result"""
    status: str  # "PASS" or "FAIL"
    spec: str   # "CLAIM_GRAPH_V1"
    graph_id: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    summary: Dict[str, Any] = None

    def to_dict(self):
        """Convert to JSON-serializable dict"""
        return {
            "status": self.status,
            "spec": self.spec,
            "graph_id": self.graph_id,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self.summary or {},
        }

    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class GraphValidator:
    """Constitutional membrane between free generation and governed processing"""

    def __init__(self):
        self.validators = [
            ("schema", validate_schema),
            ("structure", validate_structure),
            ("epistemic", validate_epistemic),
            ("evidence", validate_evidence),
            ("routing", validate_routing),
        ]

    def validate(
        self,
        graph_dict: Dict[str, Any],
        additional_bundles: Dict[str, Any] = None,
    ) -> ValidationResult:
        """
        Validate CLAIM_GRAPH_V1 against all constitutional rules.

        Args:
            graph_dict: Parsed JSON graph object
            additional_bundles: Optional external referenced objects

        Returns:
            ValidationResult with status PASS or FAIL
        """
        all_errors = []
        all_warnings = []

        graph_id = graph_dict.get("graph_meta", {}).get("id", "CG-UNKNOWN")

        # Run all validators in sequence
        for validator_name, validator_func in self.validators:
            is_valid, errors = validator_func(graph_dict)

            if not is_valid:
                all_errors.extend(errors)

                # Fail fast: stop on first major error category
                if validator_name == "schema":
                    # Schema errors are fatal
                    break

        # Validate references if no fatal errors
        if not all_errors or all_errors[0].code != "SCHEMA_INVALID":
            is_valid, ref_errors = validate_references(graph_dict, additional_bundles)
            all_errors.extend(ref_errors)

        # Build summary
        summary = self._build_summary(graph_dict)

        # Create result
        result = ValidationResult(
            status="FAIL" if all_errors else "PASS",
            spec="CLAIM_GRAPH_V1",
            graph_id=graph_id,
            errors=[error.to_dict() for error in all_errors],
            warnings=[],
            summary=summary,
        )

        return result

    def _build_summary(self, graph_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build validation summary statistics"""
        nodes = graph_dict.get("nodes", [])
        edges = graph_dict.get("edges", [])

        summary = {
            "nodes": len(nodes),
            "edges": len(edges),
        }

        # Count node types
        node_kinds = {}
        for node in nodes:
            kind = node.get("kind")
            node_kinds[kind] = node_kinds.get(kind, 0) + 1

        summary["node_kinds"] = node_kinds

        # Count admissibility
        admissible_count = sum(1 for n in nodes if n.get("admissibility") == "ADMISSIBLE")
        quarantined_count = sum(1 for n in nodes if n.get("admissibility") == "QUARANTINED")
        summary["admissible_nodes"] = admissible_count
        summary["quarantined_nodes"] = quarantined_count

        # Count wild_text nodes (should be quarantined)
        wild_text_count = sum(1 for n in nodes if n.get("kind") == "wild_text")
        summary["wild_text_nodes"] = wild_text_count

        # Count claims
        claim_count = sum(1 for n in nodes if n.get("kind") == "claim")
        summary["claims"] = claim_count

        # Count edge types
        edge_types = {}
        for edge in edges:
            edge_type = edge.get("type")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        summary["edge_types"] = edge_types

        return summary

    def validate_json_string(self, json_str: str) -> ValidationResult:
        """
        Validate from JSON string.

        Args:
            json_str: JSON string containing graph

        Returns:
            ValidationResult
        """
        try:
            graph_dict = json.loads(json_str)
            return self.validate(graph_dict)
        except json.JSONDecodeError as e:
            result = ValidationResult(
                status="FAIL",
                spec="CLAIM_GRAPH_V1",
                graph_id="CG-INVALID",
                errors=[{
                    "code": "SCHEMA_INVALID",
                    "message": f"Invalid JSON: {str(e)}"
                }],
                warnings=[],
            )
            return result

    def validate_file(self, filepath: str) -> ValidationResult:
        """
        Validate from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            ValidationResult
        """
        try:
            with open(filepath, "r") as f:
                json_str = f.read()
            return self.validate_json_string(json_str)
        except Exception as e:
            result = ValidationResult(
                status="FAIL",
                spec="CLAIM_GRAPH_V1",
                graph_id="CG-UNKNOWN",
                errors=[{
                    "code": "SCHEMA_INVALID",
                    "message": f"File error: {str(e)}"
                }],
                warnings=[],
            )
            return result


# Singleton instance
_validator = GraphValidator()


def validate(graph_dict: Dict[str, Any]) -> ValidationResult:
    """Convenience function: validate graph dict"""
    return _validator.validate(graph_dict)


def validate_json(json_str: str) -> ValidationResult:
    """Convenience function: validate JSON string"""
    return _validator.validate_json_string(json_str)


def validate_file(filepath: str) -> ValidationResult:
    """Convenience function: validate JSON file"""
    return _validator.validate_file(filepath)
