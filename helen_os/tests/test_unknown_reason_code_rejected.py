"""Test: Unknown reason codes rejected. Reducer emits only registry codes."""
from __future__ import annotations

from helen_os.governance.reason_codes import ReasonCode
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.governance.canonical import sha256_prefixed


def _make_receipt():
    payload = {"receipt_id": "R1", "payload": {"k": "v"}}
    return {
        "receipt_id": "R1",
        "payload": {"k": "v"},
        "sha256": sha256_prefixed(payload),
    }


def _make_packet():
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
        "doctrine_surface": {"law_surface_version": "v1", "transfer_required": False},
        "evaluation": {
            "threshold_name": "accuracy",
            "threshold_value": 0.9,
            "observed_value": 0.95,
            "passed": True,
        },
        "receipts": [_make_receipt()],
    }


def _make_state():
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {
            "S0": {"active_version": "0.9.0", "status": "ACTIVE", "last_decision_id": "DEC0"}
        },
    }


REGISTRY = {c.value for c in ReasonCode}


def test_reducer_emits_only_registry_codes():
    """All reducer outputs use known codes."""
    result = reduce_promotion_packet(_make_packet(), _make_state())
    assert result.reason_code in REGISTRY, (
        f"Reducer emitted unregistered code: {result.reason_code!r}"
    )


def test_unknown_reason_code_not_in_registry():
    """Fabricated codes are not in the registry."""
    assert "ERR_MADE_UP" not in REGISTRY
    assert "OK_ARBITRARY" not in REGISTRY
    assert "CUSTOM_CODE" not in REGISTRY


def test_all_rejection_paths_emit_registry_codes():
    """Each gate failure emits a registered ERR_ code."""
    state = _make_state()

    # Gate 1 — schema invalid
    bad_schema = dict(_make_packet())
    bad_schema["schema_name"] = "WRONG"
    r = reduce_promotion_packet(bad_schema, state)
    assert r.reason_code in REGISTRY

    # Gate 2 — missing receipts
    no_receipt = dict(_make_packet())
    no_receipt["receipts"] = []
    r = reduce_promotion_packet(no_receipt, state)
    assert r.reason_code in REGISTRY

    # Gate 3 — hash mismatch
    bad_hash = dict(_make_packet())
    bad_hash["receipts"] = [{"receipt_id": "R1", "payload": {"k": "v"}, "sha256": "sha256:" + "0" * 64}]
    r = reduce_promotion_packet(bad_hash, state)
    assert r.reason_code in REGISTRY

    # Gate 4 — capability drift
    drift = dict(_make_packet())
    drift["lineage"] = dict(drift["lineage"])
    drift["lineage"]["parent_skill_id"] = "S_UNKNOWN"
    r = reduce_promotion_packet(drift, state)
    assert r.reason_code in REGISTRY

    # Gate 5 — doctrine conflict
    conflict = dict(_make_packet())
    conflict["doctrine_surface"] = {"law_surface_version": "v999", "transfer_required": False}
    r = reduce_promotion_packet(conflict, state)
    assert r.reason_code in REGISTRY

    # Gate 6 — threshold not met
    fail_eval = dict(_make_packet())
    fail_eval["evaluation"] = dict(fail_eval["evaluation"])
    fail_eval["evaluation"]["passed"] = False
    r = reduce_promotion_packet(fail_eval, state)
    assert r.reason_code in REGISTRY
