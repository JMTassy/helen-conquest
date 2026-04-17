"""Test: Same packet + same state → same reducer decision."""
from __future__ import annotations

from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet


def _packet():
    return {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": "P1",
        "skill_id": "S1",
        "candidate_version": "1.0.0",
        "lineage": {
            "parent_skill_id": "S0",
            "parent_version": "0.9.0",
            "proposal_sha256": "sha256:" + "1" * 64,
        },
        "capability_manifest_sha256": "sha256:" + "2" * 64,
        "doctrine_surface": {
            "law_surface_version": "v1",
            "transfer_required": False,
        },
        "evaluation": {
            "threshold_name": "accuracy",
            "threshold_value": 0.9,
            "observed_value": 0.95,
            "passed": True,
        },
        "receipts": [
            {
                "receipt_id": "R1",
                "payload": {"k": "v"},
                "sha256": "sha256:1d5e6a1edddf2cb59b7bbc0218e03c305de6c11485cd6707f68d9d818196da8c"
            }
        ],
    }


def _state():
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {
            "S0": {
                "active_version": "0.9.0",
                "status": "ACTIVE",
                "last_decision_id": "DEC0",
            }
        },
    }


def test_same_packet_same_decision():
    """Same packet + same state → identical ReductionResult."""
    packet = _packet()
    state = _state()

    r1 = reduce_promotion_packet(packet, state)
    r2 = reduce_promotion_packet(packet, state)

    assert r1 == r2
    assert r1.decision == r2.decision
    assert r1.reason_code == r2.reason_code
