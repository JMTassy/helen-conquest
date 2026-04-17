"""Test: Autoresearch batch is bounded and ordered."""
from __future__ import annotations

from pathlib import Path
from helen_os.autonomy.autoresearch_batch_v1 import autoresearch_batch_v1


def _initial_state() -> dict:
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {},
    }


def _mk_decision(idx: int, decision_type: str = "ADMITTED") -> dict:
    """Minimal valid decision."""
    dec = {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": f"dec_{idx:03d}",
        "skill_id": f"skill.test_{idx}",
        "candidate_version": f"1.{idx}.0",
        "decision_type": decision_type,
        "reason_code": "OK_ADMITTED" if decision_type == "ADMITTED" else "ERR_THRESHOLD_NOT_MET",
    }
    if decision_type == "ADMITTED":
        dec["candidate_identity_hash"] = "sha256:" + ("a" * 64)
    return dec


def test_batch_processes_only_up_to_max_items():
    """Batch respects max_items bound."""
    decisions = [_mk_decision(i) for i in range(10)]
    max_items = 5

    result = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=_initial_state(),
        schemas_dir=Path(__file__).parent.parent / "schemas",
        max_items=max_items,
    )

    # Only 5 decisions should be processed
    assert result.processed == 5
    assert len(result.final_ledger["entries"]) <= 5


def test_batch_preserves_task_order():
    """Batch appends decisions in order."""
    decisions = [_mk_decision(i) for i in range(3)]

    result = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=_initial_state(),
        schemas_dir=Path(__file__).parent.parent / "schemas",
        max_items=10,
    )

    # Entries must be in order (entry_index == decision order)
    assert len(result.final_ledger["entries"]) == 3
    for i, entry in enumerate(result.final_ledger["entries"]):
        assert entry["entry_index"] == i
        assert entry["decision"]["decision_id"] == f"dec_{i:03d}"


def test_batch_skips_invalid_decision_types():
    """Batch skips decisions with unknown decision_type."""
    decisions = [
        _mk_decision(0),
        {"schema_name": "SKILL_PROMOTION_DECISION_V1", "decision_type": "UNKNOWN_TYPE"},  # Invalid
        _mk_decision(1),
    ]

    result = autoresearch_batch_v1(
        decisions=decisions,
        initial_ledger=None,
        initial_state=_initial_state(),
        schemas_dir=Path(__file__).parent.parent / "schemas",
        max_items=10,
    )

    # Only valid decisions appended
    assert result.appended == 2
    assert len(result.final_ledger["entries"]) == 2
