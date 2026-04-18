"""
decide.py

Mayor Decision Function

Implements Paper Section 5: Mayor Decision Surface
- Invariant 5.1: No silent failures
- Invariant 5.2: SHIP implies zero gap and passed gates
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from receipt.compute_gap import compute_receipt_gap


@dataclass
class MayorInputs:
    """Mayor decision inputs (pure)."""
    tribunal_bundle: Dict[str, Any]
    attestations_ledger: Dict[str, Any]
    policies: Dict[str, Any]
    receipt_root_payload: Dict[str, Any]


def sha256_hex(obj: Any) -> str:
    """Compute SHA-256 hex of canonical JSON."""
    canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def compute_decision(
    tribunal_bundle: Dict[str, Any],
    policies: Dict[str, Any],
    receipt_root_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Pure Mayor decision function.

    Paper Invariant 5.2:
        decision = SHIP iff (kill_switches_pass == True AND receipt_gap == 0)

    Args:
        tribunal_bundle: Obligations and verification results
        policies: Kill switches and policy evaluations
        receipt_root_payload: Receipt gap and attestation status

    Returns:
        decision_record (deterministic payload, no timestamps)
    """
    # Extract inputs
    kill_switches_pass = policies.get("kill_switches_pass", False)
    receipt_gap = receipt_root_payload.get("receipt_gap", 0)

    # Compute blocking reasons
    blocking: List[Dict[str, Any]] = []

    if not kill_switches_pass:
        blocking.append({
            "code": "KILL_SWITCH_FAILED",
            "detail": "One or more kill switches failed policy evaluation",
            "evidence_paths": ["policies_eval.json"]
        })

    if receipt_gap > 0:
        missing_obls = receipt_root_payload.get("missing_obligations", [])
        obl_names = [o.get("name") for o in missing_obls[:3]]  # First 3
        detail = f"{receipt_gap} HARD obligations unsatisfied: {', '.join(obl_names)}"
        if receipt_gap > 3:
            detail += f", and {receipt_gap - 3} more"

        blocking.append({
            "code": "RECEIPT_GAP_NONZERO",
            "detail": detail,
            "evidence_paths": [
                "tribunal_bundle.json",
                "receipt_root_payload.json"
            ]
        })

    # Apply decision logic (Paper Invariant 5.2)
    if kill_switches_pass and receipt_gap == 0:
        decision = "SHIP"
        # Schema enforces: SHIP => blocking=[], receipt_gap=0, kill_switches_pass=true
        blocking = []
    else:
        decision = "NO_SHIP"
        # Schema enforces: NO_SHIP => blocking non-empty

    # Compute input hashes for metadata binding
    tribunal_hash = _hash_payload(tribunal_bundle)
    policies_hash = _hash_payload(policies)
    receipt_hash = _hash_payload(receipt_root_payload)

    # Build deterministic payload (no timestamps!)
    decision_record = {
        "decision": decision,
        "kill_switches_pass": kill_switches_pass,
        "receipt_gap": receipt_gap,
        "blocking": blocking,
        "missing_obligations": receipt_root_payload.get("missing_obligations", []),
        "kill_switches": policies.get("kill_switches", []),
        "metadata": {
            "mayor_version": "v0.1",
            "tribunal_bundle_hash": tribunal_hash,
            "policies_hash": policies_hash,
            "receipt_root_hash": receipt_hash
        }
    }

    return decision_record


def emit_decision_with_meta(
    decision_record: Dict[str, Any],
    audit_trail: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Split decision into hashed payload + non-hashed metadata.

    Paper Protocol 4.1: Determinism split
    - decision_record.json: no timestamps (receipt-hashed)
    - decision_record.meta.json: timestamps allowed (not hashed)

    Returns:
        (decision_record, decision_meta)
    """
    # Compute hash of decision record
    record_hash = _hash_payload(decision_record)

    # Non-hashed metadata
    decision_meta = {
        "decision_record_hash": record_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "audit_trail": audit_trail or {}
    }

    return decision_record, decision_meta


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Compute SHA-256 of canonical JSON payload.

    Uses deterministic JSON serialization (sorted keys, no whitespace).
    In production, use RFC 8785 canonical JSON.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def recompute_decision_for_purity_check(
    tribunal_bundle: Dict[str, Any],
    policies: Dict[str, Any],
    receipt_root_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Recompute decision from hashed inputs for purity verification.

    Used by test_mayor_purity.py to verify referential transparency.

    Returns:
        Recomputed decision record
    """
    return compute_decision(tribunal_bundle, policies, receipt_root_payload)


def compute_decision_payload(inputs: MayorInputs) -> Dict[str, Any]:
    """
    Pure Mayor decision function using MayorInputs dataclass.

    Paper Invariant 5.2:
        decision = SHIP iff (kill_switches_pass == True AND receipt_gap == 0)

    Args:
        inputs: MayorInputs with tribunal, attestations, policies, receipt_root

    Returns:
        decision_record (deterministic payload, no timestamps)
    """
    # Compute receipt gap
    gap, missing = compute_receipt_gap(
        inputs.tribunal_bundle,
        inputs.attestations_ledger
    )

    # Extract kill switches status
    kill_switches_pass = inputs.policies.get("kill_switches_pass", False)

    # Compute blocking reasons
    blocking: List[Dict[str, Any]] = []

    if not kill_switches_pass:
        blocking.append({
            "code": "KILL_SWITCH_FAILED",
            "detail": "One or more kill switches failed policy evaluation",
            "evidence_paths": ["policies_eval.json"]
        })

    if gap > 0:
        missing_names = [m.get("name") for m in missing[:3] if m.get("name")]
        detail = f"{gap} HARD obligations unsatisfied: {', '.join(missing_names)}"
        if gap > 3:
            detail += f", and {gap - 3} more"

        blocking.append({
            "code": "RECEIPT_GAP_NONZERO",
            "detail": detail,
            "evidence_paths": [
                "tribunal_bundle.json",
                "receipt_root_payload.json"
            ]
        })

    # Apply decision logic (Paper Invariant 5.2)
    if kill_switches_pass and gap == 0:
        decision = "SHIP"
        blocking = []
    else:
        decision = "NO_SHIP"

    # Build deterministic payload (no timestamps!)
    decision_record = {
        "decision": decision,
        "kill_switches_pass": kill_switches_pass,
        "receipt_gap": gap,
        "blocking": blocking,
        "metadata": {
            "mayor_version": "v0.1",
            "tribunal_bundle_hash": sha256_hex(inputs.tribunal_bundle),
            "policies_hash": sha256_hex(inputs.policies),
            "receipt_root_hash": sha256_hex(inputs.receipt_root_payload)
        }
    }

    return decision_record


# Example usage
if __name__ == "__main__":
    # Example: NO_SHIP scenario (receipt gap > 0)
    tribunal = {
        "obligations": [
            {"name": "security_audit", "severity": "HARD"},
            {"name": "performance_test", "severity": "HARD"}
        ]
    }

    policies = {
        "kill_switches_pass": True,
        "kill_switches": [
            {"name": "no_free_text", "status": "pass"},
            {"name": "bounded_structure", "status": "pass"}
        ]
    }

    receipt_payload = {
        "receipt_gap": 2,
        "missing_obligations": [
            {"name": "security_audit", "reason_code": "HARD_OBLIGATION_UNSATISFIED"},
            {"name": "performance_test", "reason_code": "HARD_OBLIGATION_UNSATISFIED"}
        ]
    }

    # Compute decision
    decision = compute_decision(tribunal, policies, receipt_payload)

    print(json.dumps(decision, indent=2))
    # Expected: NO_SHIP with blocking codes

    # Example: SHIP scenario (all conditions met)
    receipt_payload_satisfied = {
        "receipt_gap": 0,
        "missing_obligations": []
    }

    decision_ship = compute_decision(tribunal, policies, receipt_payload_satisfied)
    print("\n" + json.dumps(decision_ship, indent=2))
    # Expected: SHIP with empty blocking

    # Emit with metadata split
    record, meta = emit_decision_with_meta(decision_ship)
    print(f"\nDecision record hash: {meta['decision_record_hash']}")
    print(f"Timestamp (non-hashed): {meta['timestamp']}")
