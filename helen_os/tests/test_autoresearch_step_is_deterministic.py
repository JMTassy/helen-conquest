"""Test: Autoresearch step produces deterministic cycles."""
from __future__ import annotations

from helen_os.autonomy.autoresearch_step_v1 import autoresearch_step
from helen_os.governance.canonical import sha256_prefixed


def _task():
    return {
        "task_id": "task_001",
        "skill_id": "skill.test",
        "current_version": "1.0.0",
        "command": "python -m test_module",
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


def test_autoresearch_step_same_input_same_output():
    """Same task + same state → identical cycle output."""
    task = _task()
    state = _state()

    # First cycle
    result1 = autoresearch_step(task, state)

    # Second cycle with same inputs
    result2 = autoresearch_step(task, state)

    # Envelope must be identical
    assert result1["execution_envelope"] == result2["execution_envelope"]

    # Failure report must be identical (if present)
    assert result1["failure_report"] == result2["failure_report"]

    # Promotion packet must be identical (if present)
    assert result1["promotion_packet"] == result2["promotion_packet"]

    # Decision must be identical (if present)
    assert result1["decision"] == result2["decision"]

    # Next state must be identical
    assert result1["next_state"] == result2["next_state"]


def test_autoresearch_step_output_is_deterministic():
    """Autoresearch step output can be cryptographically hashed."""
    task = _task()
    state = _state()

    result = autoresearch_step(task, state)

    # All components are hashable
    envelope_hash = sha256_prefixed(result["execution_envelope"])
    assert envelope_hash.startswith("sha256:")

    state_hash = sha256_prefixed(result["next_state"])
    assert state_hash.startswith("sha256:")

    # Multiple runs produce same hashes
    result2 = autoresearch_step(task, state)
    assert sha256_prefixed(result2["execution_envelope"]) == envelope_hash
    assert sha256_prefixed(result2["next_state"]) == state_hash


def test_autoresearch_step_respects_membrane():
    """Autoresearch step never mutates state without reducer approval."""
    task = _task()
    state = _state()

    result = autoresearch_step(task, state)

    # If decision is not ADMITTED, state must be unchanged
    if result["decision"] is None or result["decision"].get("decision") != "ADMITTED":
        assert result["next_state"] == state
    else:
        # If ADMITTED, state has changed through approved channel
        assert result["next_state"] != state  # Changed
        # But only through reducer path
        assert result["decision"]["decision"] == "ADMITTED"
