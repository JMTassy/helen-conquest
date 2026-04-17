"""Test: REPLAY_PROOF_V1 proves zero drift."""
from __future__ import annotations

from helen_os.replay_proof_v1 import replay_packet


def _packet():
    return {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": "P_REPLAY_TEST",
        "skill_id": "skill.test",
        "candidate_version": "1.0.0",
        "lineage": {
            "parent_skill_id": "skill.base",
            "parent_version": "0.9.0",
            "proposal_sha256": "sha256:" + "a" * 64,
        },
        "capability_manifest_sha256": "sha256:" + "b" * 64,
        "doctrine_surface": {"law_surface_version": "v1", "transfer_required": False},
        "evaluation": {
            "threshold_name": "accuracy",
            "threshold_value": 0.9,
            "observed_value": 0.95,
            "passed": True,
        },
        "receipts": [
            {
                "receipt_id": "R1",
                "payload": {"data": "test"},
                "sha256": "sha256:" + "c" * 64,
            }
        ],
    }


def _state():
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {
            "skill.base": {
                "active_version": "0.9.0",
                "status": "ACTIVE",
                "last_decision_id": "DEC0",
            }
        },
    }


def test_replay_proof_no_drift():
    """Replay produces zero drift across 20 runs."""
    result = replay_packet(_packet(), _state(), runs=20)

    assert result["all_decisions_identical"], (
        "Decisions must be identical across runs"
    )
    assert not result["drift_detected"], "No drift should be detected"
    assert len(result["decision_hashes"]) == 20


def test_replay_proof_identical_hashes():
    """All decision hashes are byte-for-byte identical."""
    result = replay_packet(_packet(), _state(), runs=10)

    hashes = result["decision_hashes"]
    first = hashes[0]

    for i, h in enumerate(hashes[1:], start=2):
        assert h == first, f"Run {i} hash differs: {h} != {first}"


def test_replay_proof_rejected_packet():
    """Rejected packet also produces identical decisions."""
    packet = _packet()
    packet["evaluation"]["passed"] = False  # Will be rejected

    result = replay_packet(packet, _state(), runs=5)

    assert result["all_decisions_identical"]
    assert not result["drift_detected"]
    assert all(
        h == result["decision_hashes"][0] for h in result["decision_hashes"]
    )
