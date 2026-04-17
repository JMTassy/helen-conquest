"""Test: State updater changes state only on ADMITTED decision."""
from __future__ import annotations

from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision


def _base_state():
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {},
    }


def _decision(kind: str):
    dec = {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": f"dec_{kind.lower()}",
        "skill_id": "skill.search",
        "candidate_version": "1.2.0",
        "decision_type": kind,
        "reason_code": "OK_ADMITTED" if kind == "ADMITTED" else "ERR_THRESHOLD_NOT_MET",
    }
    if kind == "ADMITTED":
        dec["candidate_identity_hash"] = "sha256:" + "c" * 64
    return dec


def test_skill_library_state_changes_only_on_admitted_decision():
    state = _base_state()

    # ADMITTED decision: skill added to active_skills
    admitted = apply_skill_promotion_decision(state, _decision("ADMITTED"))
    assert len(admitted["active_skills"]) == 1
    assert "skill.search" in admitted["active_skills"]
    assert admitted["active_skills"]["skill.search"]["active_version"] == "1.2.0"
    assert admitted["active_skills"]["skill.search"]["status"] == "ACTIVE"

    # Rejected decision: state unchanged (empty)
    rejected = apply_skill_promotion_decision(state, _decision("REJECTED"))
    assert rejected["active_skills"] == {}

    # Quarantined decision: state unchanged (empty)
    quarantined = apply_skill_promotion_decision(state, _decision("QUARANTINED"))
    assert quarantined["active_skills"] == {}

    # Rolled back decision: state unchanged (empty)
    rolled_back = apply_skill_promotion_decision(state, _decision("ROLLED_BACK"))
    assert rolled_back["active_skills"] == {}
