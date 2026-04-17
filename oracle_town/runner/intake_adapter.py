"""
Intake Adapter: Wraps real IntakeGuard and normalizes output for runner.

This adapter converts IntakeGuard.evaluate() results into a consistent format
that runner modules can use. It preserves all information but normalizes structure.

Invariant: IntakeGuard is the source of truth for proposal validation.
Runner only normalizes the output, never overrides decisions.
"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from oracle_town.core.intake_guard import IntakeGuard, RejectionCode


class IntakeAdapterCode(Enum):
    """Adapter-specific codes (map from IntakeGuard codes)."""
    INTAKE_ACCEPT = "INTAKE_ACCEPT"
    INTAKE_REJECT_FORBIDDEN_FIELDS = "INTAKE_REJECT_FORBIDDEN_FIELDS"
    INTAKE_REJECT_SCHEMA_INVALID = "INTAKE_REJECT_SCHEMA_INVALID"
    INTAKE_REJECT_BUDGET_VIOLATION = "INTAKE_REJECT_BUDGET_VIOLATION"
    INTAKE_REJECT_MALFORMED_JSON = "INTAKE_REJECT_MALFORMED_JSON"


@dataclass
class IntakeAdapterDecision:
    """Normalized intake decision for runner use."""
    decision: str  # "ACCEPT" or "REJECT"
    adapter_code: IntakeAdapterCode
    kernel_code: Optional[RejectionCode] = None
    detail: str = ""
    briefcase: Optional[Dict[str, Any]] = None
    ct_boundary_digest: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "decision": self.decision,
            "adapter_code": self.adapter_code.value,
            "kernel_code": self.kernel_code.value if self.kernel_code else None,
            "detail": self.detail,
            "briefcase": self.briefcase,
            "ct_boundary_digest": self.ct_boundary_digest,
        }


class IntakeAdapter:
    """Wraps IntakeGuard and provides stable interface for runner."""

    def __init__(self, **kwargs):
        """
        Initialize adapter with IntakeGuard config.

        Args:
            **kwargs: Passed to IntakeGuard (max_proposals, max_obligations, etc.)
        """
        self.intake_guard = IntakeGuard(**kwargs)

    def evaluate(
        self,
        proposal_bundle: Dict[str, Any],
        ct_run_manifest: Optional[Dict[str, Any]] = None
    ) -> IntakeAdapterDecision:
        """
        Evaluate CT output using IntakeGuard.

        Args:
            proposal_bundle: CT proposal bundle
            ct_run_manifest: CT provenance metadata (optional)

        Returns:
            IntakeAdapterDecision (stable format for runner use)
        """
        if ct_run_manifest is None:
            ct_run_manifest = {}

        try:
            # Call real IntakeGuard
            kernel_decision = self.intake_guard.evaluate(
                proposal_bundle=proposal_bundle,
                ct_run_manifest=ct_run_manifest
            )

            # Convert to adapter format
            if kernel_decision.decision == "ACCEPT":
                return IntakeAdapterDecision(
                    decision="ACCEPT",
                    adapter_code=IntakeAdapterCode.INTAKE_ACCEPT,
                    kernel_code=None,
                    detail="Proposal bundle accepted by IntakeGuard",
                    briefcase=kernel_decision.briefcase,
                    ct_boundary_digest=kernel_decision.ct_boundary_digest,
                )

            else:  # REJECT
                # Map rejection codes
                kernel_code = kernel_decision.rejection_code
                adapter_code = self._map_rejection_code(kernel_code)

                detail = self._build_rejection_detail(
                    kernel_code,
                    kernel_decision.forbidden_fields_found
                )

                return IntakeAdapterDecision(
                    decision="REJECT",
                    adapter_code=adapter_code,
                    kernel_code=kernel_code,
                    detail=detail,
                    briefcase=None,
                    ct_boundary_digest=kernel_decision.ct_boundary_digest,
                )

        except json.JSONDecodeError as e:
            return IntakeAdapterDecision(
                decision="REJECT",
                adapter_code=IntakeAdapterCode.INTAKE_REJECT_MALFORMED_JSON,
                detail=f"JSON decode error: {e}",
                ct_boundary_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            )

        except Exception as e:
            # Fail closed
            return IntakeAdapterDecision(
                decision="REJECT",
                adapter_code=IntakeAdapterCode.INTAKE_REJECT_MALFORMED_JSON,
                detail=f"Unexpected error: {e}",
                ct_boundary_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            )

    @staticmethod
    def _map_rejection_code(kernel_code: RejectionCode) -> IntakeAdapterCode:
        """Map IntakeGuard rejection code to adapter code."""
        mapping = {
            RejectionCode.CT_REJECTED_FORBIDDEN_FIELDS: IntakeAdapterCode.INTAKE_REJECT_FORBIDDEN_FIELDS,
            RejectionCode.CT_REJECTED_SCHEMA_INVALID: IntakeAdapterCode.INTAKE_REJECT_SCHEMA_INVALID,
            RejectionCode.CT_REJECTED_BUDGET_VIOLATION: IntakeAdapterCode.INTAKE_REJECT_BUDGET_VIOLATION,
            RejectionCode.CT_REJECTED_MALFORMED_JSON: IntakeAdapterCode.INTAKE_REJECT_MALFORMED_JSON,
        }
        return mapping.get(kernel_code, IntakeAdapterCode.INTAKE_REJECT_SCHEMA_INVALID)

    @staticmethod
    def _build_rejection_detail(
        kernel_code: RejectionCode,
        forbidden_fields: list
    ) -> str:
        """Build human-readable rejection detail."""
        if kernel_code == RejectionCode.CT_REJECTED_FORBIDDEN_FIELDS:
            return f"Forbidden fields found: {', '.join(forbidden_fields)}"
        elif kernel_code == RejectionCode.CT_REJECTED_SCHEMA_INVALID:
            return "Proposal bundle does not match expected schema"
        elif kernel_code == RejectionCode.CT_REJECTED_BUDGET_VIOLATION:
            return f"Budget violation: {', '.join(forbidden_fields)}"
        elif kernel_code == RejectionCode.CT_REJECTED_MALFORMED_JSON:
            return "Proposal bundle is not valid JSON"
        else:
            return f"Rejection: {kernel_code.value}"


if __name__ == "__main__":
    """Test intake adapter."""
    import json

    adapter = IntakeAdapter()

    # Test 1: Accept clean bundle
    print("Test 1: Accept clean bundle...")
    clean_bundle = {
        "proposals": [
            {
                "name": "test_idea",
                "description_hash": "sha256:abc123",
            }
        ]
    }
    result = adapter.evaluate(clean_bundle)
    assert result.decision == "ACCEPT", f"Expected ACCEPT, got {result.decision}"
    assert result.adapter_code == IntakeAdapterCode.INTAKE_ACCEPT
    assert result.briefcase is not None
    print("✓ Clean bundle accepted")

    # Test 2: Reject forbidden fields
    print("\nTest 2: Reject forbidden fields...")
    forbidden_bundle = {
        "proposals": [
            {
                "name": "test",
                "description_hash": "sha256:abc",
                "priority": "high",  # forbidden
            }
        ]
    }
    result = adapter.evaluate(forbidden_bundle)
    assert result.decision == "REJECT", f"Expected REJECT, got {result.decision}"
    assert result.kernel_code == RejectionCode.CT_REJECTED_FORBIDDEN_FIELDS
    print("✓ Forbidden fields rejected")

    # Test 3: Reject budget violation
    print("\nTest 3: Reject budget violation...")
    oversized_bundle = {
        "proposals": [{"name": f"proposal_{i}", "description_hash": f"sha256:{i}"} for i in range(150)]
    }
    result = adapter.evaluate(oversized_bundle)
    assert result.decision == "REJECT", f"Expected REJECT, got {result.decision}"
    assert result.kernel_code == RejectionCode.CT_REJECTED_BUDGET_VIOLATION
    print("✓ Budget violation rejected")

    # Test 4: Serialization
    print("\nTest 4: Serialization...")
    result_dict = result.to_dict()
    assert isinstance(result_dict["decision"], str)
    assert isinstance(result_dict["adapter_code"], str)
    assert json.dumps(result_dict)  # Should be JSON-serializable
    print("✓ Serialization works")

    print("\n✓ All intake adapter tests passed")
