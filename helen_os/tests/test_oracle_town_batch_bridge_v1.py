"""Test: Oracle Town Batch Bridge — institutional receipt emission.

Bridge law: Bridge emits only receipts. Never mutates state, never writes ledger.

Tests:
1. Bridge emits three sealed artifacts (receipt, town, HAL)
2. Receipt is deterministic (same batch → same receipt_id)
3. Town artifact preserves full ledger for verification
4. HAL packet provides structured audit surface
5. Bridge never mutates state
6. Authority lineage respected
"""
import json
import pytest
from pathlib import Path

from helen_os.autonomy.autoresearch_batch_v1 import autoresearch_batch_v1, BatchResult
from helen_os.town.batch_bridge_v1 import (
    emit_batch_receipt_packet,
    BatchExecutionContext,
    compute_deterministic_receipt_id,
    extract_decision_type_breakdown,
)


@pytest.fixture
def schemas_dir():
    return Path(__file__).parent.parent / "schemas"


@pytest.fixture
def initial_state():
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "1.0.0",
        "active_skills": {},
    }


@pytest.fixture
def decisions_for_batch():
    return [
        {
            "decision_id": "dec_001",
            "decision_type": "ADMITTED",
            "skill_id": "skill.search",
            "candidate_version": "1.1.0",
            "candidate_identity_hash": "sha256:" + "a" * 64,
            "reason_code": "OK_ADMITTED",
        },
        {
            "decision_id": "dec_002",
            "decision_type": "REJECTED",
            "skill_id": "skill.rank",
            "reason_code": "ERR_THRESHOLD_NOT_MET",
        },
        {
            "decision_id": "dec_003",
            "decision_type": "ADMITTED",
            "skill_id": "skill.filter",
            "candidate_version": "1.0.0",
            "candidate_identity_hash": "sha256:" + "b" * 64,
            "reason_code": "OK_ADMITTED",
        },
    ]


def test_bridge_emits_three_artifacts(initial_state, decisions_for_batch, schemas_dir):
    """Bridge must emit three sealed artifacts."""
    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_test_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    receipt, town_artifact, hal_packet = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    # All three must be present
    assert receipt is not None
    assert town_artifact is not None
    assert hal_packet is not None

    # All must have correct schema names
    assert receipt["schema_name"] == "BATCH_RECEIPT_PACKET_V1"
    assert town_artifact["schema_name"] == "ORACLE_TOWN_BATCH_ARTIFACT_V1"
    assert hal_packet["schema_name"] == "HAL_REVIEW_PACKET_V1"


def test_bridge_receipt_is_deterministic(initial_state, decisions_for_batch, schemas_dir):
    """Same batch input → same receipt_id (idempotent)."""
    # Use fixed clock for determinism
    fixed_time = "2026-03-13T14:23:45Z"
    def fixed_now_fn():
        return fixed_time

    batch_context = BatchExecutionContext(
        batch_id="batch_det_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        now_fn=fixed_now_fn,
    )

    # Run batch twice with same input and same clock
    batch_result_1 = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
        now_fn=fixed_now_fn,
    )

    receipt_1, _, _ = emit_batch_receipt_packet(
        batch_result=batch_result_1.__dict__,
        batch_context=batch_context,
    )

    batch_result_2 = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
        now_fn=fixed_now_fn,
    )

    receipt_2, _, _ = emit_batch_receipt_packet(
        batch_result=batch_result_2.__dict__,
        batch_context=batch_context,
    )

    # receipt_id must be identical (deterministic)
    assert receipt_1["receipt_id"] == receipt_2["receipt_id"]
    # final state hash must be identical
    assert receipt_1["final_state_hash"] == receipt_2["final_state_hash"]
    # ledger hash must be identical
    assert receipt_1["ledger_hash"] == receipt_2["ledger_hash"]


def test_bridge_town_artifact_preserves_full_ledger(initial_state, decisions_for_batch, schemas_dir):
    """Town artifact must embed full ledger for independent verification."""
    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_town_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    _, town_artifact, _ = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    # Town artifact must contain full ledger
    assert "ledger" in town_artifact
    assert "entries" in town_artifact["ledger"]

    # Ledger entries must be identical to batch ledger
    batch_ledger = batch_result.final_ledger
    town_ledger = town_artifact["ledger"]

    assert len(town_ledger["entries"]) == len(batch_ledger["entries"])
    for i, town_entry in enumerate(town_ledger["entries"]):
        batch_entry = batch_ledger["entries"][i]
        assert town_entry["entry_index"] == batch_entry["entry_index"]
        assert town_entry["entry_hash"] == batch_entry["entry_hash"]
        assert town_entry["prev_entry_hash"] == batch_entry["prev_entry_hash"]


def test_bridge_hal_packet_is_structured(initial_state, decisions_for_batch, schemas_dir):
    """HAL packet must provide structured audit surface (no narrative)."""
    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_hal_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    _, _, hal_packet = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    # Must have structured sections
    assert "batch_summary" in hal_packet
    assert "governance_checks" in hal_packet
    assert "flags_for_hal" in hal_packet

    # Governance checks must be boolean
    checks = hal_packet["governance_checks"]
    assert isinstance(checks["all_decisions_validated"], bool)
    assert isinstance(checks["ledger_integrity_verified"], bool)
    assert isinstance(checks["replay_determinism_proven"], bool)
    assert isinstance(checks["authority_boundaries_respected"], bool)

    # Flags must be typed (not narrative)
    for flag in hal_packet["flags_for_hal"]:
        assert "flag_category" in flag
        assert flag["flag_category"] in ("INFO", "WARN", "BLOCK")
        assert "reason_code" in flag
        assert "interpretation" in flag


def test_bridge_authority_lineage_is_correct(initial_state, decisions_for_batch, schemas_dir):
    """Authority lineage must show CORE status initially."""
    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_auth_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    receipt, _, _ = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    lineage = receipt["authority_lineage"]

    # Must show CORE visibility (kernel-level, not yet approved by HAL)
    assert lineage["visibility_level"] == "CORE"
    assert lineage["approved_by"] is None
    assert lineage["ready_for_hal"] is True
    assert lineage["ready_for_mayor"] is False


def test_bridge_never_mutates_state(initial_state, decisions_for_batch, schemas_dir):
    """Bridge must not modify the state or ledger."""
    initial_state_copy = json.loads(json.dumps(initial_state))

    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_nomut_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    receipt, town_artifact, hal_packet = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    # initial_state must not have changed
    assert initial_state == initial_state_copy

    # batch_result must not have changed
    assert len(batch_result.final_ledger["entries"]) > 0  # had entries before
    # (bridge only reads, doesn't mutate)


def test_bridge_admission_summary_extraction(initial_state, decisions_for_batch, schemas_dir):
    """Town artifact must extract admission summary correctly."""
    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_adm_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    _, town_artifact, _ = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    admission_summary = town_artifact["admission_summary"]

    # Should have 2 ADMITTED decisions
    assert len(admission_summary) == 2
    assert admission_summary[0]["skill_id"] == "skill.search"
    assert admission_summary[0]["candidate_version"] == "1.1.0"
    assert admission_summary[1]["skill_id"] == "skill.filter"
    assert admission_summary[1]["candidate_version"] == "1.0.0"


def test_bridge_rejection_summary_extraction(initial_state, decisions_for_batch, schemas_dir):
    """Town artifact must extract rejection summary correctly."""
    batch_result = autoresearch_batch_v1(
        decisions=decisions_for_batch,
        initial_ledger=None,
        initial_state=initial_state,
        schemas_dir=schemas_dir,
        max_items=10,
    )

    batch_context = BatchExecutionContext(
        batch_id="batch_rej_001",
        executor_id="helen_os_kernel_v1",
        run_id="run_2026-03-13T14:23:45Z",
        initial_state=initial_state,
        schemas_dir=schemas_dir,
    )

    _, town_artifact, _ = emit_batch_receipt_packet(
        batch_result=batch_result.__dict__,
        batch_context=batch_context,
    )

    rejection_summary = town_artifact["rejection_summary"]

    # Should have 1 REJECTED decision
    assert len(rejection_summary) == 1
    assert rejection_summary[0]["decision_type"] == "REJECTED"
    assert rejection_summary[0]["skill_id"] == "skill.rank"
    assert rejection_summary[0]["reason_code"] == "ERR_THRESHOLD_NOT_MET"
