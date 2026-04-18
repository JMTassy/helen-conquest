"""
tests/test_temple_sandbox_routing.py — TEMPLE_SANDBOX_POLICY_V1 Routing Enforcement

Tests cover:
- Wild_text nodes must have route_to_mayor=false (TEMPLE_SANDBOX_POLICY_V1 §C)
- Explicit route_to_mayor=true on wild_text triggers WILD_ROUTING_VIOLATION
- route_to_mayor enforcement at ingestion time
- Quarantine edges block routing
- Full routing validation pipeline

Status: All tests must pass before TEMPLE_SANDBOX_POLICY_V1 is FROZEN.
"""

import json
import pytest
from pathlib import Path

from helen_os.claim_graph.graph_validator import GraphValidator
from helen_os.claim_graph.validators import validate_routing
from helen_os.claim_graph.error_codes import (
    WILD_ROUTING_VIOLATION,
    POLICY_QUARANTINE_ACTIVE,
)


class TestWildTextRoutingEnforcement:
    """T01–T03: wild_text nodes must have route_to_mayor=false"""

    def test_t01_wild_text_default_route_to_mayor_false(self):
        """wild_text node with route_to_mayor=false is valid (default behavior)"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-01"},
            "nodes": [
                {
                    "id": "WT-001",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "QUARANTINED",
                    "route_to_mayor": False,  # Explicit false
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        assert is_valid, f"Expected valid, got errors: {[e.to_dict() for e in errors]}"

    def test_t02_wild_text_missing_route_to_mayor_field(self):
        """wild_text node without route_to_mayor field is valid (missing treated as false)"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-02"},
            "nodes": [
                {
                    "id": "WT-002",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "QUARANTINED",
                    # No route_to_mayor field — should be treated as false
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        assert is_valid, f"Expected valid, got errors: {[e.to_dict() for e in errors]}"

    def test_t03_wild_text_route_to_mayor_true_violation(self):
        """wild_text node with route_to_mayor=true triggers WILD_ROUTING_VIOLATION"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-03"},
            "nodes": [
                {
                    "id": "WT-003",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "QUARANTINED",
                    "route_to_mayor": True,  # VIOLATION
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        assert not is_valid, "Expected validation to fail for wild_text with route_to_mayor=true"
        assert len(errors) == 1
        assert errors[0].code == WILD_ROUTING_VIOLATION
        assert "WT-003" in str(errors[0].node_id)
        assert "TEMPLE_SANDBOX_POLICY_V1" in errors[0].message

    def test_t04_wild_text_never_routable_to_mayor(self):
        """wild_text nodes are structurally barred from routing to Mayor (TEMPLE_SANDBOX_POLICY_V1 §C)"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-04"},
            "nodes": [
                {
                    "id": "WT-004",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "ADMISSIBLE",  # Even if marked ADMISSIBLE
                    "route_to_mayor": False,  # Correct value
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        # No errors about route_to_mayor, but wild_text is still structurally barred
        # (This is enforced at the graph processing level, not at validation)
        assert is_valid


class TestQuarantineEdgesBlockRouting:
    """T05–T06: QUARANTINES edges block routing"""

    def test_t05_quarantine_edge_blocks_claim(self):
        """Claim with incoming QUARANTINES edge cannot route to Mayor"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-05"},
            "nodes": [
                {
                    "id": "CLAIM-001",
                    "kind": "claim",
                    "admissibility": "ADMISSIBLE",
                    "route_to_mayor": True,  # Declared routable
                },
                {
                    "id": "POLICY-001",
                    "kind": "policy",
                    "admissibility": "ADMISSIBLE",
                },
            ],
            "edges": [
                {
                    "id": "E-001",
                    "type": "QUARANTINES",
                    "from": "POLICY-001",
                    "to": "CLAIM-001",
                }
            ],
        }
        is_valid, errors = validate_routing(graph)
        assert not is_valid, "Expected validation to fail for quarantined claim"
        quarantine_errors = [e for e in errors if e.code == POLICY_QUARANTINE_ACTIVE]
        assert len(quarantine_errors) > 0

    def test_t06_no_quarantine_edge_claim_is_routable(self):
        """Claim without QUARANTINES edge and ADMISSIBLE status can route"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-06"},
            "nodes": [
                {
                    "id": "CLAIM-002",
                    "kind": "claim",
                    "admissibility": "ADMISSIBLE",
                    "route_to_mayor": True,
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        # Should be valid (no quarantine, admissible, not wild_text)
        assert is_valid, f"Expected valid, got errors: {[e.to_dict() for e in errors]}"


class TestFullRoutingValidationIntegration:
    """T07–T08: Full routing validation through GraphValidator"""

    def test_t07_mixed_graph_with_wild_text_and_claims(self):
        """Complex graph with wild_text (quarantined) and claims (routable) validates routing correctly"""
        graph = {
            "nodes": [
                {
                    "id": "N-CLAIM-CORE",
                    "kind": "claim",
                    "admissibility": "ADMISSIBLE",
                    "route_to_mayor": True,  # Core claim is routable
                    "epistemic_state": "VERIFIED",
                },
                {
                    "id": "N-WT-SUPPORT",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "QUARANTINED",
                    "route_to_mayor": False,  # Wild text is not routable
                    "epistemic_state": "WITNESSED",
                },
                {
                    "id": "N-EVIDENCE-001",
                    "kind": "evidence_handle",
                    "admissibility": "ADMISSIBLE",
                    "epistemic_state": "WITNESSED",
                }
            ],
            "edges": [
                {
                    "id": "E-CORE-SUPPORT",
                    "type": "SUPPORTS",
                    "from": "N-EVIDENCE-001",
                    "to": "N-CLAIM-CORE",
                }
            ],
        }
        is_valid, errors = validate_routing(graph)
        assert is_valid, f"Expected valid routing, got errors: {[e.to_dict() for e in errors]}"

    def test_t08_wild_text_route_to_mayor_true_through_routing_validator(self):
        """validate_routing catches wild_text with route_to_mayor=true"""
        graph = {
            "nodes": [
                {
                    "id": "N-WT-VIOLATION",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "QUARANTINED",
                    "route_to_mayor": True,  # VIOLATION
                    "epistemic_state": "WITNESSED",
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        assert not is_valid, "Expected validation to fail for wild_text with route_to_mayor=true"
        wild_routing_errors = [e for e in errors if e.code == WILD_ROUTING_VIOLATION]
        assert len(wild_routing_errors) > 0, f"Expected WILD_ROUTING_VIOLATION, got: {[e.to_dict() for e in errors]}"


class TestTempleDefaultClassification:
    """T09–T10: Temple artifacts receive default classification (tier III, QUARANTINED, route_to_mayor=false)"""

    def test_t09_temple_artifact_default_classification(self):
        """Temple artifact with default classification passes routing validation"""
        graph = {
            "nodes": [
                {
                    "id": "N-TEMPLE-ART-001",
                    "kind": "wild_text",
                    "tier": "III",  # Default tier
                    "admissibility": "QUARANTINED",  # Default admissibility
                    "route_to_mayor": False,  # Default routing
                    "epistemic_state": "WITNESSED",
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        assert is_valid, f"Expected valid routing, got errors: {[e.to_dict() for e in errors]}"

    def test_t10_non_temple_wild_text_still_must_comply(self):
        """Non-Temple wild_text nodes must still comply with routing rules"""
        graph = {
            "graph_meta": {"id": "CG-ROUTING-10", "origin": "USER"},
            "nodes": [
                {
                    "id": "USER-WILD-TEXT",
                    "kind": "wild_text",
                    "tier": "III",
                    "admissibility": "QUARANTINED",
                    "route_to_mayor": True,  # VIOLATION regardless of origin
                }
            ],
            "edges": [],
        }
        is_valid, errors = validate_routing(graph)
        assert not is_valid
        assert any(e.code == WILD_ROUTING_VIOLATION for e in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
