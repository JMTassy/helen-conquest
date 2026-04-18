"""
compute_gap.py

Receipt Gap Computation

Implements Paper Definition 4.3: Receipt Gap
receipt_gap = count of unsatisfied HARD obligations
"""

from typing import Dict, List, Any, Tuple, Optional


def compute_receipt_gap(
    tribunal_bundle: Dict[str, Any],
    attestations_ledger: Dict[str, Any]
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Compute receipt gap from tribunal bundle and attestations ledger.

    Paper Definition 4.3:
        RG ∈ ℕ is the count of unsatisfied HARD obligations

    Args:
        tribunal_bundle: Contains obligations list
        attestations_ledger: Contains verification results

    Returns:
        (receipt_gap, missing_obligations)
        - receipt_gap: integer count
        - missing_obligations: list of unsatisfied HARD obligations with details
    """
    obligations = tribunal_bundle.get("obligations", [])
    attestations = attestations_ledger.get("attestations", [])

    # Filter HARD obligations only
    hard_obligations = [
        obl for obl in obligations
        if obl.get("severity") == "HARD"
    ]

    # Build attestation map by obligation name
    attestation_map = {}
    for att in attestations:
        obl_name = att.get("obligation_name")
        if obl_name:
            attestation_map[obl_name] = att

    # Check satisfaction for each HARD obligation
    missing_obligations = []

    for obl in hard_obligations:
        obl_name = obl.get("name")

        if not is_obligation_satisfied(obl, attestation_map.get(obl_name)):
            # Build missing obligation entry
            att = attestation_map.get(obl_name, {})

            missing_obligations.append({
                "name": obl_name,
                "severity": "HARD",
                "expected_attestor": obl.get("expected_attestor"),
                "actual_attestor": att.get("attestor"),
                "attestation_valid": att.get("attestation_valid", False),
                "policy_match": att.get("policy_match", 0),
                "reason_code": _determine_reason_code(obl, att),
                "detail": _build_detail_message(obl, att)
            })

    receipt_gap = len(missing_obligations)

    return receipt_gap, missing_obligations


def is_obligation_satisfied(
    obligation: Dict[str, Any],
    attestation: Optional[Dict[str, Any]]
) -> bool:
    """
    Check if obligation is satisfied by attestation.

    Satisfaction criteria:
    - attestation exists
    - attestation_valid == True
    - policy_match == 1 (or truthy)
    - (optional) expected_attestor matches actual

    Returns:
        True if satisfied, False otherwise
    """
    if attestation is None:
        return False

    # Core criteria
    attestation_valid = attestation.get("attestation_valid", False)
    policy_match = attestation.get("policy_match", 0)

    if not attestation_valid:
        return False

    if not policy_match:
        return False

    # Optional attestor match check
    expected_attestor = obligation.get("expected_attestor")
    actual_attestor = attestation.get("attestor")

    if expected_attestor and actual_attestor:
        if expected_attestor != actual_attestor:
            # Attestor mismatch (policy may or may not enforce this)
            # For now, trust policy_match as the canonical signal
            pass

    return True


def _determine_reason_code(
    obligation: Dict[str, Any],
    attestation: Dict[str, Any]
) -> str:
    """Determine appropriate reason code for unsatisfied obligation."""
    if not attestation:
        return "HARD_OBLIGATION_UNSATISFIED"

    attestation_valid = attestation.get("attestation_valid", False)
    policy_match = attestation.get("policy_match", 0)

    if not attestation_valid:
        return "ATTESTATION_INVALID"

    if not policy_match:
        return "POLICY_MATCH_FAILED"

    return "HARD_OBLIGATION_UNSATISFIED"


def _build_detail_message(
    obligation: Dict[str, Any],
    attestation: Dict[str, Any]
) -> str:
    """Build human-readable detail message."""
    obl_name = obligation.get("name", "unknown")

    if not attestation:
        return f"No attestation found for {obl_name}"

    attestation_valid = attestation.get("attestation_valid", False)
    policy_match = attestation.get("policy_match", 0)
    attestor = attestation.get("attestor", "unknown")

    if not attestation_valid:
        return f"{obl_name}: attestation invalid from {attestor}"

    if not policy_match:
        return f"{obl_name}: policy mismatch from {attestor}"

    return f"{obl_name}: unsatisfied"


# Example usage
if __name__ == "__main__":
    # Example tribunal bundle
    tribunal = {
        "obligations": [
            {
                "name": "security_audit",
                "type": "audit",
                "severity": "HARD",
                "expected_attestor": "team_security"
            },
            {
                "name": "performance_benchmark",
                "type": "benchmark",
                "severity": "HARD",
                "expected_attestor": "team_performance"
            },
            {
                "name": "documentation",
                "type": "docs",
                "severity": "SOFT",
                "expected_attestor": "team_docs"
            }
        ]
    }

    # Example attestations ledger (partial satisfaction)
    ledger_partial = {
        "attestations": [
            {
                "obligation_name": "security_audit",
                "attestor": "team_security",
                "attestation_valid": True,
                "policy_match": 1,
                "payload_hash": "abc123"
            }
            # performance_benchmark missing
            # documentation missing (but SOFT, doesn't count)
        ]
    }

    # Compute gap
    gap, missing = compute_receipt_gap(tribunal, ledger_partial)

    print(f"Receipt Gap: {gap}")
    print(f"Missing HARD obligations: {len(missing)}")
    for m in missing:
        print(f"  - {m['name']}: {m['reason_code']} - {m['detail']}")

    # Expected output:
    # Receipt Gap: 1
    # Missing HARD obligations: 1
    #   - performance_benchmark: HARD_OBLIGATION_UNSATISFIED - No attestation found for performance_benchmark
