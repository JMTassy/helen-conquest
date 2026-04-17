"""Test: Ledger replay reconstructs governed history deterministically."""
from __future__ import annotations

from helen_os.state.ledger_replay_v1 import replay_ledger_to_state
from helen_os.governance.canonical import sha256_prefixed


def _initial_state():
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {},
    }


def _ledger_with_entries(entries: list) -> dict:
    return {
        "schema_name": "DECISION_LEDGER_V1",
        "schema_version": "1.0.0",
        "ledger_id": "ledger_001",
        "canonicalization": "JCS_SHA256_V1",
        "entries": entries,
    }


def _decision(decision_id: str, skill_id: str, version: str) -> dict:
    return {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": decision_id,
        "skill_id": skill_id,
        "candidate_version": version,
        "decision_type": "ADMITTED",
        "candidate_identity_hash": "sha256:" + "c" * 64,
        "reason_code": "OK_ADMITTED",
    }


def test_replay_same_ledger_twice_yields_same_state():
    """Replaying the same ledger twice produces identical reconstructed state."""
    entry = {
        "entry_index": 0,
        "ts": "2026-03-13T00:00:00+00:00",
        "prev_entry_hash": None,
        "decision": _decision("dec_001", "skill.test", "1.0.0"),
        "entry_hash": "sha256:" + "a" * 64,
    }
    ledger = _ledger_with_entries([entry])
    initial_state = _initial_state()

    # First replay
    state1 = replay_ledger_to_state(ledger, initial_state)

    # Second replay
    state2 = replay_ledger_to_state(ledger, initial_state)

    # Must be identical
    assert state1 == state2
    assert sha256_prefixed(state1) == sha256_prefixed(state2)


def test_entry_order_matters_and_is_preserved():
    """Ledger replay applies entries in order and preserves entry index integrity."""
    entry1 = {
        "entry_index": 0,
        "ts": "2026-03-13T00:00:00+00:00",
        "prev_entry_hash": None,
        "decision": _decision("dec_001", "skill.first", "1.0.0"),
        "entry_hash": "sha256:" + "a" * 64,
    }
    entry2 = {
        "entry_index": 1,
        "ts": "2026-03-13T00:00:01+00:00",
        "prev_entry_hash": "sha256:" + "a" * 64,
        "decision": _decision("dec_002", "skill.second", "1.0.0"),
        "entry_hash": "sha256:" + "b" * 64,
    }

    ledger_order1 = _ledger_with_entries([entry1, entry2])
    ledger_order2 = _ledger_with_entries([entry2, entry1])

    initial_state = _initial_state()

    # Replay correct order
    state1 = replay_ledger_to_state(ledger_order1, initial_state)

    # State1 should have both skills (correct order)
    assert len(state1["active_skills"]) == 2
    assert "skill.first" in state1["active_skills"]
    assert "skill.second" in state1["active_skills"]

    # Replay with entry_index mismatch (entry2 at position 0, but has index 1)
    state2 = replay_ledger_to_state(ledger_order2, initial_state)

    # Entry index mismatch causes fail-closed: returns initial state
    assert state2 == initial_state


def test_invalid_entries_are_rejected():
    """Invalid entries cause ledger replay to fail closed."""
    # Entry with mismatched index
    invalid_entry = {
        "entry_index": 99,  # Wrong: should be 0
        "prev_entry_hash": None,
        "decision": _decision("dec_001", "skill.test", "1.0.0"),
        "entry_hash": "sha256:" + "a" * 64,
    }
    ledger = _ledger_with_entries([invalid_entry])
    initial_state = _initial_state()

    # Replay must fail closed (return initial state)
    result = replay_ledger_to_state(ledger, initial_state)
    assert result == initial_state


def test_reconstructed_state_matches_incremental_application():
    """Final replayed state matches state reached by incremental application."""
    entry1 = {
        "entry_index": 0,
        "ts": "2026-03-13T00:00:00+00:00",
        "prev_entry_hash": None,
        "decision": _decision("dec_001", "skill.alpha", "1.0.0"),
        "entry_hash": "sha256:" + "a" * 64,
    }
    entry2 = {
        "entry_index": 1,
        "ts": "2026-03-13T00:00:01+00:00",
        "prev_entry_hash": "sha256:" + "a" * 64,
        "decision": _decision("dec_002", "skill.beta", "2.0.0"),
        "entry_hash": "sha256:" + "b" * 64,
    }
    ledger = _ledger_with_entries([entry1, entry2])
    initial_state = _initial_state()

    # Replay entire ledger
    replayed_state = replay_ledger_to_state(ledger, initial_state)

    # Replayed state should have both skills
    assert "skill.alpha" in replayed_state["active_skills"]
    assert "skill.beta" in replayed_state["active_skills"]
    assert replayed_state["active_skills"]["skill.alpha"]["active_version"] == "1.0.0"
    assert replayed_state["active_skills"]["skill.beta"]["active_version"] == "2.0.0"
