"""
Comprehensive test suite for graph_validator.py

10 acceptance tests + extended coverage
"""

import pytest
import json
from .graph_validator import validate, validate_json, GraphValidator
from .error_codes import (
    DUPLICATE_NODE_ID, DUPLICATE_EDGE_ID, UNKNOWN_EDGE_ENDPOINT,
    ILLEGAL_EDGE_TYPE, ILLEGAL_DEPENDENCY_CYCLE, WILD_ROUTING_VIOLATION,
    TIER_PROMOTION_VIOLATION, MISSING_EVIDENCE_HANDLE_FIELD,
    UNRESOLVED_REFERENCE, POLICY_QUARANTINE_ACTIVE, SCHEMA_INVALID
)


class TestGraphValidatorAcceptance:
    """10 minimal deterministic acceptance tests"""

    def test_01_valid_graph_passes(self):
        """Valid graph passes all gates"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {
                "id": "CG-0001",
                "environment_ref": "sha256:abc123",
                "policy_ref": "sha256:def456",
            },
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "claim",
                    "tier": "I",
                    "epistemic_state": "WITNESSED",
                    "admissibility": "ADMISSIBLE",
                    "content": "Test claim",
                },
                {
                    "id": "N-0002",
                    "kind": "evidence_handle",
                    "epistemic_state": "WITNESSED",
                    "admissibility": "ADMISSIBLE",
                    "handle": {
                        "repo_commit": "abc123def456",
                        "paths": ["test/path.py"],
                        "artifact_hash": "sha256:artifact123",
                        "receipt_id": "R-001",
                        "receipt_hash": "sha256:receipt123",
                        "replay_command": "python test/path.py",
                        "expected_artifact_hashes": ["sha256:expected123"],
                    },
                },
            ],
            "edges": [
                {
                    "id": "E-0001",
                    "type": "SUPPORTS",
                    "from": "N-0002",
                    "to": "N-0001",
                },
            ],
        }

        result = validate(graph)
        assert result.status == "PASS"
        assert len(result.errors) == 0

    def test_02_duplicate_node_id_fails(self):
        """Duplicate node ID causes validation failure"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0002"},
            "nodes": [
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == DUPLICATE_NODE_ID for e in result.errors)

    def test_03_edge_to_missing_node_fails(self):
        """Edge referencing non-existent node fails"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0003"},
            "nodes": [
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
            ],
            "edges": [
                {"id": "E-0001", "type": "SUPPORTS", "from": "N-0001", "to": "N-9999"},
            ],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == UNKNOWN_EDGE_ENDPOINT for e in result.errors)

    def test_04_wild_text_routed_to_mayor_fails(self):
        """wild_text node routed to Mayor fails"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0004"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "wild_text",
                    "epistemic_state": "STAGED",
                    "admissibility": "ADMISSIBLE",  # Violates structure
                    "route_to_mayor": True,
                },
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] in [TIER_PROMOTION_VIOLATION, WILD_ROUTING_VIOLATION] for e in result.errors)

    def test_05_tier_iii_not_quarantined_fails(self):
        """Tier III marked ADMISSIBLE fails"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0005"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "claim",
                    "tier": "III",
                    "epistemic_state": "STAGED",
                    "admissibility": "ADMISSIBLE",  # Violates rule
                },
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == TIER_PROMOTION_VIOLATION for e in result.errors)

    def test_06_missing_evidence_handle_field_fails(self):
        """Missing evidence handle field fails"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0006"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "evidence_handle",
                    "epistemic_state": "STAGED",
                    "admissibility": "ADMISSIBLE",
                    "handle": {
                        "repo_commit": "abc123",
                        "paths": ["test.py"],
                        "artifact_hash": "sha256:abc",
                        # Missing receipt_id, receipt_hash, replay_command, expected_artifact_hashes
                    },
                },
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == MISSING_EVIDENCE_HANDLE_FIELD for e in result.errors)

    def test_07_missing_tasp_report_reference_fails(self):
        """Unresolved TASP report reference fails"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0007"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "claim",
                    "epistemic_state": "STAGED",
                    "admissibility": "ADMISSIBLE",
                    "tasp_report_ref": "sha256:missing_report",
                },
            ],
            "edges": [],
        }

        # Without providing the referenced bundle, validation should catch this
        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == UNRESOLVED_REFERENCE for e in result.errors)

    def test_08_dependency_cycle_fails(self):
        """Cyclic dependency detected and rejected"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0008"},
            "nodes": [
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
                {"id": "N-0002", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
                {"id": "N-0003", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
            ],
            "edges": [
                {"id": "E-0001", "type": "DEPENDS_ON", "from": "N-0001", "to": "N-0002"},
                {"id": "E-0002", "type": "DEPENDS_ON", "from": "N-0002", "to": "N-0003"},
                {"id": "E-0003", "type": "DEPENDS_ON", "from": "N-0003", "to": "N-0001"},  # Cycle
            ],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == ILLEGAL_DEPENDENCY_CYCLE for e in result.errors)

    def test_09_same_input_twice_gives_identical_result(self):
        """Determinism: identical input produces byte-identical result"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0009"},
            "nodes": [
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
            ],
            "edges": [],
        }

        result1 = validate(graph)
        result2 = validate(graph)

        json1 = json.dumps(result1.to_dict(), sort_keys=True)
        json2 = json.dumps(result2.to_dict(), sort_keys=True)

        assert json1 == json2, "Determinism violation: same input gave different results"

    def test_10_quarantined_claim_never_routable(self):
        """Quarantined claim cannot appear in routable set"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-0010"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "claim",
                    "epistemic_state": "STAGED",
                    "admissibility": "QUARANTINED",
                },
            ],
            "edges": [],
        }

        result = validate(graph)
        # Quarantined nodes are not errors, but summary should show them
        assert result.summary["quarantined_nodes"] == 1
        assert result.summary["admissible_nodes"] == 0


class TestGraphValidatorExtended:
    """Extended test coverage"""

    def test_schema_invalid_missing_root_fields(self):
        """Invalid schema: missing root fields"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1"},
            # Missing graph_meta, nodes, edges
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == SCHEMA_INVALID for e in result.errors)

    def test_schema_invalid_wrong_spec_name(self):
        """Invalid schema: spec.name must be CLAIM_GRAPH_V1"""
        graph = {
            "spec": {"name": "WRONG_SPEC", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == SCHEMA_INVALID for e in result.errors)

    def test_invalid_node_id_pattern(self):
        """Node ID must match pattern ^N-"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [
                {"id": "BADID", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == SCHEMA_INVALID for e in result.errors)

    def test_invalid_edge_id_pattern(self):
        """Edge ID must match pattern ^E-"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
            ],
            "edges": [
                {"id": "BADID", "type": "SUPPORTS", "from": "N-0001", "to": "N-0001"},
            ],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == SCHEMA_INVALID for e in result.errors)

    def test_wild_text_must_be_quarantined(self):
        """wild_text node must be QUARANTINED"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "wild_text",
                    "epistemic_state": "STAGED",
                    "admissibility": "ADMISSIBLE",  # Violates rule
                },
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] in [TIER_PROMOTION_VIOLATION, WILD_ROUTING_VIOLATION] for e in result.errors)

    def test_wild_text_route_to_mayor_must_be_false(self):
        """wild_text route_to_mayor must be false"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "wild_text",
                    "epistemic_state": "STAGED",
                    "admissibility": "QUARANTINED",
                    "route_to_mayor": True,  # Violates rule
                },
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == WILD_ROUTING_VIOLATION for e in result.errors)

    def test_quarantined_cannot_have_routes_edge(self):
        """QUARANTINED node cannot have ROUTES edge"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [
                {
                    "id": "N-0001",
                    "kind": "claim",
                    "epistemic_state": "STAGED",
                    "admissibility": "QUARANTINED",
                },
                {
                    "id": "N-0002",
                    "kind": "claim",
                    "epistemic_state": "STAGED",
                    "admissibility": "ADMISSIBLE",
                },
            ],
            "edges": [
                {"id": "E-0001", "type": "ROUTES", "from": "N-0001", "to": "N-0002"},
            ],
        }

        result = validate(graph)
        assert result.status == "FAIL"
        assert any(e["code"] == WILD_ROUTING_VIOLATION for e in result.errors)

    def test_validate_json_string(self):
        """Can validate from JSON string"""
        json_str = json.dumps({
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [],
            "edges": [],
        })

        result = validate_json(json_str)
        assert result.status == "PASS"

    def test_validate_invalid_json_string(self):
        """Invalid JSON string is caught"""
        result = validate_json("{ invalid json }")
        assert result.status == "FAIL"
        assert any(e["code"] == SCHEMA_INVALID for e in result.errors)

    def test_summary_counts_node_kinds(self):
        """Summary correctly counts node kinds"""
        graph = {
            "spec": {"name": "CLAIM_GRAPH_V1", "version": "1.0"},
            "graph_meta": {"id": "CG-X"},
            "nodes": [
                {"id": "N-0001", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
                {"id": "N-0002", "kind": "claim", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
                {"id": "N-0003", "kind": "evidence_handle", "epistemic_state": "STAGED", "admissibility": "ADMISSIBLE"},
                {"id": "N-0004", "kind": "wild_text", "epistemic_state": "STAGED", "admissibility": "QUARANTINED"},
            ],
            "edges": [],
        }

        result = validate(graph)
        assert result.status == "PASS"
        assert result.summary["claims"] == 2
        assert result.summary["wild_text_nodes"] == 1
        assert result.summary["node_kinds"]["claim"] == 2


class TestGraphValidatorErrorClasses:
    """Test that error codes are properly frozen and used"""

    def test_all_error_codes_present(self):
        """All expected error codes are defined"""
        from .error_codes import (
            SCHEMA_INVALID, DUPLICATE_NODE_ID, DUPLICATE_EDGE_ID,
            UNKNOWN_EDGE_ENDPOINT, ILLEGAL_EDGE_TYPE, ILLEGAL_DEPENDENCY_CYCLE,
            WILD_ROUTING_VIOLATION, TIER_PROMOTION_VIOLATION,
            MISSING_EVIDENCE_HANDLE_FIELD, MISSING_REQUIRED_SUPPORT,
            UNRESOLVED_REFERENCE, POLICY_QUARANTINE_ACTIVE
        )

        codes = {
            SCHEMA_INVALID, DUPLICATE_NODE_ID, DUPLICATE_EDGE_ID,
            UNKNOWN_EDGE_ENDPOINT, ILLEGAL_EDGE_TYPE, ILLEGAL_DEPENDENCY_CYCLE,
            WILD_ROUTING_VIOLATION, TIER_PROMOTION_VIOLATION,
            MISSING_EVIDENCE_HANDLE_FIELD, MISSING_REQUIRED_SUPPORT,
            UNRESOLVED_REFERENCE, POLICY_QUARANTINE_ACTIVE
        }

        assert len(codes) == 12, "Expected 12 distinct error codes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
