"""
tests/test_mission_spine_mvp.py — HELEN V3 mission spine end-to-end tests.

Tests:
  T01: Happy path — proposal → mission → steps → workers → receipts → SUCCEEDED
  T02: Worker failure — one step fails → mission FAILED
  T03: Missing receipt — step "succeeds" but no receipt_refs → mission FAILED
  T04: Empty input_refs → cap gate REJECTS proposal
  T05: Invalid step_kinds → proposal_service raises ValueError
  T06: Reaction engine generates review proposal on step failure
  T07: Reaction engine returns empty on success event
  T08: Deterministic IDs — same inputs → same mission_id
"""
import pytest
from helen_os.missions.proposal_service import create_proposal_and_maybe_promote
from helen_os.missions.worker_registry import WorkerRegistry
from helen_os.missions.step_executor import execute_step
from helen_os.missions.mission_reducer import apply_step_result, finalize_mission
from helen_os.missions.reaction_engine import proposals_from_event


def _base_payload(**overrides):
    base = {
        "proposal_id": "P-001",
        "source": "dialogue",
        "title": "Spine test",
        "goal": "Analyze trace",
        "step_kinds": ["analyze", "check"],
        "input_refs": ["TRACE_EVENT_V1:abc"],
        "risk_tier": "low",
    }
    base.update(overrides)
    return base


def _dummy_ok(inp):
    return {"status": "ok", "summary": "done"}

def _dummy_fail(inp):
    return {"status": "fail", "error": "worker_err"}


# ── T01: Happy path ───────────────────────────────────────────────────────────

def test_t01_happy_path_end_to_end():
    bundle = create_proposal_and_maybe_promote(_base_payload())
    assert bundle["promotion_class"] == "PROMOTABLE_TO_MISSION"
    assert bundle["mission"] is not None

    mission = bundle["mission"]
    steps = bundle["steps"]
    assert len(steps) == 2

    registry = WorkerRegistry()
    registry.register("analyze", _dummy_ok)
    registry.register("check", _dummy_ok)

    for step in steps:
        out_refs, receipt = execute_step(
            worker_id="local",
            mission_id=step["mission_id"],
            step_id=step["step_id"],
            step_kind=step["step_kind"],
            input_refs=step["input_refs"],
            worker_fn=registry.get(step["step_kind"]),
        )
        step_status = "succeeded" if receipt.status == "ok" else "failed"
        apply_step_result(
            step, status=step_status, output_refs=out_refs,
            receipt_refs=[receipt.receipt_id] if receipt.status == "ok" else [],
            last_error=None if receipt.status == "ok" else "worker_failed",
        )

    final = finalize_mission(mission, steps)
    assert final["status"] == "succeeded"


# ── T02: Worker failure ───────────────────────────────────────────────────────

def test_t02_worker_failure_fails_mission():
    bundle = create_proposal_and_maybe_promote(_base_payload())
    mission = bundle["mission"]
    steps = bundle["steps"]

    registry = WorkerRegistry()
    registry.register("analyze", _dummy_ok)
    registry.register("check", _dummy_fail)  # check step will fail

    for step in steps:
        out_refs, receipt = execute_step(
            worker_id="local",
            mission_id=step["mission_id"],
            step_id=step["step_id"],
            step_kind=step["step_kind"],
            input_refs=step["input_refs"],
            worker_fn=registry.get(step["step_kind"]),
        )
        step_status = "succeeded" if receipt.status == "ok" else "failed"
        apply_step_result(
            step, status=step_status, output_refs=out_refs,
            receipt_refs=[receipt.receipt_id] if receipt.status == "ok" else [],
            last_error=None if receipt.status == "ok" else "worker_failed",
        )

    final = finalize_mission(mission, steps)
    assert final["status"] == "failed"


# ── T03: Missing receipt ──────────────────────────────────────────────────────

def test_t03_missing_receipt_fails_mission():
    bundle = create_proposal_and_maybe_promote(_base_payload())
    mission = bundle["mission"]
    steps = bundle["steps"]

    # Mark all steps succeeded but give NO receipt_refs
    for step in steps:
        apply_step_result(step, status="succeeded", output_refs=[], receipt_refs=[])

    final = finalize_mission(mission, steps)
    assert final["status"] == "failed"


# ── T04: Cap gate rejects empty input_refs ────────────────────────────────────

def test_t04_cap_gate_rejects_empty_input_refs():
    bundle = create_proposal_and_maybe_promote(_base_payload(input_refs=[]))
    assert bundle["promotion_class"] == "REJECTED"
    assert "NO_INPUT_REFS" in bundle["reason_codes"]
    assert bundle["mission"] is None


# ── T05: Invalid step_kinds raise ValueError ──────────────────────────────────

def test_t05_invalid_step_kind_raises():
    with pytest.raises(ValueError):
        create_proposal_and_maybe_promote(_base_payload(step_kinds=["teleport"]))


# ── T06: Reaction engine → review proposal on failure ────────────────────────

def test_t06_reaction_engine_step_failed():
    event = {"event_id": "E-001", "event_kind": "step_failed", "step_id": "S-1"}
    proposals = proposals_from_event(event)
    assert len(proposals) == 1
    assert proposals[0]["source"] == "reaction"
    assert proposals[0]["step_kinds"] == ["review"]


# ── T07: Reaction engine → empty on success event ────────────────────────────

def test_t07_reaction_engine_no_output_on_success():
    event = {"event_id": "E-002", "event_kind": "step_succeeded"}
    assert proposals_from_event(event) == []


# ── T08: Deterministic IDs ────────────────────────────────────────────────────

def test_t08_deterministic_mission_ids():
    payload = _base_payload()
    b1 = create_proposal_and_maybe_promote(payload)
    b2 = create_proposal_and_maybe_promote(payload)
    assert b1["mission"]["mission_id"] == b2["mission"]["mission_id"]
    assert b1["steps"][0]["step_id"] == b2["steps"][0]["step_id"]
