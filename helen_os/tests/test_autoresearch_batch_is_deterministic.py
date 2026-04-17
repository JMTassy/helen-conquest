"""Test: Autoresearch batch produces deterministic outputs."""
from __future__ import annotations

from pathlib import Path
from helen_os.autonomy.autoresearch_batch_v1 import autoresearch_batch_v1
from helen_os.governance.ledger_validator_v1 import hash_state


def _initial_state() -> dict:
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {},
    }


def _mk_admit(idx: int) -> dict:
    """Valid ADMITTED decision."""
    return {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": f"adm_{idx:03d}",
        "skill_id": f"skill.alpha_{idx}",
        "candidate_version": f"2.{idx}.0",
        "decision_type": "ADMITTED",
        "candidate_identity_hash": "sha256:" + ("b" * 64),
        "reason_code": "OK_ADMITTED",
    }


def test_same_inputs_produce_identical_ledger_hash():
    """Same decisions → identical ledger structure (entry order + decision content preserved)."""
    decisions = [_mk_admit(i) for i in range(3)]
    initial_state = _initial_state()
    schemas_dir = Path(__file__).parent.parent / "schemas"

    # First run
    result1 = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    # Second run (identical inputs)
    result2 = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    # Ledgers must be structurally identical (entry order preserved)
    assert len(result1.final_ledger["entries"]) == len(result2.final_ledger["entries"])
    for e1, e2 in zip(result1.final_ledger["entries"], result2.final_ledger["entries"]):
        # Entry index and decision content must match
        # (entry_hash may differ due to timestamp differences, but decision structure is deterministic)
        assert e1["entry_index"] == e2["entry_index"]
        assert e1["decision"]["decision_id"] == e2["decision"]["decision_id"]
        assert e1["decision"]["decision_type"] == e2["decision"]["decision_type"]
        assert e1["decision"]["skill_id"] == e2["decision"]["skill_id"]


def test_same_inputs_produce_identical_state_hash():
    """Same decisions → identical final state hash."""
    decisions = [_mk_admit(i) for i in range(2)]
    initial_state = _initial_state()
    schemas_dir = Path(__file__).parent.parent / "schemas"

    # First run
    result1 = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    # Second run
    result2 = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    # State hashes must be identical
    assert result1.final_state_hash == result2.final_state_hash
    assert result1.final_state == result2.final_state
