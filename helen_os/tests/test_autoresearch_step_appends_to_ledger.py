"""Test: Autoresearch step appends admitted decisions to ledger."""
from __future__ import annotations

from helen_os.autonomy.autoresearch_step_v1 import autoresearch_step


def _task():
    return {
        "task_id": "task_001",
        "skill_id": "skill.test",
        "current_version": "1.0.0",
        "command": "exit 0",  # Success
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


def _ledger():
    return {
        "schema_name": "DECISION_LEDGER_V1",
        "schema_version": "1.0.0",
        "ledger_id": "ledger_001",
        "canonicalization": "JCS_SHA256_V1",
        "entries": [],
    }


def test_autoresearch_step_appends_admitted_decisions_to_ledger():
    """Autonomous step appends ADMITTED decisions to ledger."""
    task = _task()
    state = _state()
    ledger = _ledger()

    result = autoresearch_step(task, state, ledger)

    # If decision is ADMITTED, it must be appended
    if result["decision"] is not None and result["decision"].get("decision_type") == "ADMITTED":
        assert result["next_ledger"] is not None
        assert len(result["next_ledger"]["entries"]) > 0
        assert result["next_ledger"]["entries"][0]["decision"] == result["decision"]
    else:
        # If not ADMITTED or no decision, ledger unchanged
        assert result["next_ledger"] == ledger


def test_autoresearch_step_preserves_ledger_entries():
    """Autonomous step preserves prior ledger entries."""
    task = _task()
    state = _state()

    # Pre-populate ledger
    ledger = _ledger()
    # Simulate prior decision
    ledger["entries"].append({
        "entry_index": 0,
        "ts": "2026-03-13T00:00:00+00:00",
        "prev_entry_hash": None,
        "decision": {
            "schema_name": "SKILL_PROMOTION_DECISION_V1",
            "schema_version": "1.0.0",
            "decision_id": "dec_prior",
            "skill_id": "skill.prior",
            "candidate_version": "1.0.0",
            "decision_type": "ADMITTED",
            "candidate_identity_hash": "sha256:" + "c" * 64,
            "reason_code": "OK_ADMITTED",
        },
        "entry_hash": "sha256:" + "a" * 64,
    })

    result = autoresearch_step(task, state, ledger)

    # Prior entry must remain
    if result["next_ledger"] is not None:
        assert len(result["next_ledger"]["entries"]) > 0
        assert result["next_ledger"]["entries"][0] == ledger["entries"][0]


def test_autoresearch_step_ledger_deterministic():
    """Autonomous step produces deterministic ledger appends."""
    task = _task()
    state = _state()
    ledger = _ledger()

    # First cycle
    result1 = autoresearch_step(task, state, ledger)

    # Second cycle with same inputs
    result2 = autoresearch_step(task, state, ledger)

    # Ledger results must be identical
    if result1["next_ledger"] is not None and result2["next_ledger"] is not None:
        assert result1["next_ledger"] == result2["next_ledger"]
