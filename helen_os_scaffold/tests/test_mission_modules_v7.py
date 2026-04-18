"""
tests/test_mission_modules_v7.py — Move 7: validators, planner, executor, promotion

Tests:
  VM01–VM08: validators.py — structural invariant checks
  PL01–PL04: planner.py   — deterministic mission planning
  EX01–EX05: executor.py  — safe step execution with receipt issuance
  PR01–PR06: promotion.py — evaluate_proposal + update_mission_status
"""
import pytest
from helen_os.missions.validators import (
    validate_proposal,
    validate_mission,
    validate_step,
    validate_receipt,
    assert_valid_proposal,
    assert_valid_mission,
    assert_valid_step,
    assert_valid_receipt,
)
from helen_os.missions.planner import plan_mission, plan_mission_as_dicts
from helen_os.missions.executor import execute, execute_as_dict
from helen_os.missions.promotion import evaluate_proposal, update_mission_status


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _valid_proposal_dict(**overrides):
    base = {
        "artifact_type": "PROPOSAL_V1",
        "proposal_id":   "P-001",
        "source":        "dialogue",
        "title":         "Test proposal",
        "goal":          "Analyze artifact",
        "step_kinds":    ["analyze", "check"],
        "input_refs":    ["TRACE_EVENT_V1:abc"],
        "risk_tier":     "low",
        "status":        "pending",
        "reason_codes":  [],
    }
    base.update(overrides)
    return base


def _valid_mission_dict(**overrides):
    base = {
        "artifact_type":       "MISSION_V1",
        "mission_id":          "M-abc123",
        "source_proposal_id":  "P-001",
        "goal":                "Analyze artifact",
        "status":              "pending",
        "created_from":        "dialogue",
        "step_ids":            ["S-111", "S-222"],
    }
    base.update(overrides)
    return base


def _valid_step_dict(**overrides):
    base = {
        "artifact_type": "MISSION_STEP_V1",
        "step_id":       "S-111",
        "mission_id":    "M-abc123",
        "step_kind":     "analyze",
        "status":        "queued",
        "input_refs":    ["TRACE_EVENT_V1:abc"],
        "output_refs":   [],
        "receipt_refs":  [],
        "last_error":    None,
    }
    base.update(overrides)
    return base


def _valid_receipt_dict(**overrides):
    base = {
        "artifact_type": "EXECUTION_RECEIPT_V1",
        "receipt_id":    "R-xyz",
        "mission_id":    "M-abc123",
        "step_id":       "S-111",
        "worker_id":     "local",
        "status":        "ok",
        "input_hash":    "a" * 64,
        "output_hash":   "b" * 64,
        "trace_ref":     "TRACE:deadbeef",
        "created_at_tick": 0,
    }
    base.update(overrides)
    return base


# ── VM: validators ────────────────────────────────────────────────────────────

class TestValidators:
    def test_vm01_valid_proposal_no_violations(self):
        """VM01: A fully valid proposal returns empty violation list."""
        assert validate_proposal(_valid_proposal_dict()) == []

    def test_vm02_proposal_wrong_artifact_type(self):
        """VM02: Wrong artifact_type → violation."""
        viols = validate_proposal(_valid_proposal_dict(artifact_type="WRONG"))
        assert any("PROPOSAL_V1" in v for v in viols)

    def test_vm03_proposal_invalid_step_kind(self):
        """VM03: Unknown step_kind → violation."""
        viols = validate_proposal(_valid_proposal_dict(step_kinds=["teleport"]))
        assert any("step_kinds" in v for v in viols)

    def test_vm04_proposal_invalid_risk_tier(self):
        """VM04: Unknown risk_tier → violation."""
        viols = validate_proposal(_valid_proposal_dict(risk_tier="extreme"))
        assert any("risk_tier" in v for v in viols)

    def test_vm05_valid_mission_no_violations(self):
        """VM05: A fully valid mission returns empty violation list."""
        assert validate_mission(_valid_mission_dict()) == []

    def test_vm06_mission_empty_step_ids(self):
        """VM06: Empty step_ids → violation."""
        viols = validate_mission(_valid_mission_dict(step_ids=[]))
        assert any("step_ids" in v for v in viols)

    def test_vm07_valid_step_no_violations(self):
        """VM07: A fully valid step returns empty violation list."""
        assert validate_step(_valid_step_dict()) == []

    def test_vm08_valid_receipt_no_violations(self):
        """VM08: A fully valid receipt returns empty violation list."""
        assert validate_receipt(_valid_receipt_dict()) == []

    def test_vm09_receipt_bad_status(self):
        """VM09: Receipt status not in {ok, fail} → violation."""
        viols = validate_receipt(_valid_receipt_dict(status="running"))
        assert any("status" in v for v in viols)

    def test_vm10_assert_raises_on_invalid_proposal(self):
        """VM10: assert_valid_proposal raises ValueError for invalid proposal."""
        with pytest.raises(ValueError, match="PROPOSAL_V1"):
            assert_valid_proposal(_valid_proposal_dict(artifact_type="WRONG"))

    def test_vm11_assert_raises_on_invalid_receipt(self):
        """VM11: assert_valid_receipt raises ValueError for short hash."""
        with pytest.raises(ValueError, match="EXECUTION_RECEIPT_V1"):
            assert_valid_receipt(_valid_receipt_dict(input_hash="abc"))


# ── PL: planner ───────────────────────────────────────────────────────────────

def _make_proposal_obj():
    from helen_os.missions.schemas import ProposalV1
    return ProposalV1(
        artifact_type="PROPOSAL_V1",
        proposal_id="P-002",
        source="trigger",
        title="Planner test",
        goal="Compile + review",
        step_kinds=["compile", "review"],
        input_refs=["CLAIM_GRAPH_V1:abc"],
        risk_tier="medium",
        status="promotable",
        reason_codes=[],
    )


class TestPlanner:
    def test_pl01_plan_mission_returns_mission_and_steps(self):
        """PL01: plan_mission() returns (MissionV1, list[MissionStepV1])."""
        mission, steps = plan_mission(_make_proposal_obj())
        assert mission.artifact_type == "MISSION_V1"
        assert len(steps) == 2

    def test_pl02_step_kinds_match_proposal(self):
        """PL02: Step kinds in output match proposal.step_kinds."""
        mission, steps = plan_mission(_make_proposal_obj())
        assert [s.step_kind for s in steps] == ["compile", "review"]

    def test_pl03_deterministic_ids(self):
        """PL03: Same proposal → same mission_id and step_ids."""
        m1, s1 = plan_mission(_make_proposal_obj())
        m2, s2 = plan_mission(_make_proposal_obj())
        assert m1.mission_id == m2.mission_id
        assert [s.step_id for s in s1] == [s.step_id for s in s2]

    def test_pl04_plan_from_dict_works(self):
        """PL04: plan_mission_as_dicts() accepts dict and returns dicts."""
        from dataclasses import asdict
        p = _make_proposal_obj()
        m_dict, step_dicts = plan_mission_as_dicts(asdict(p))
        assert m_dict["artifact_type"] == "MISSION_V1"
        assert len(step_dicts) == 2

    def test_pl05_mission_step_ids_match_steps(self):
        """PL05: mission.step_ids matches actual step step_ids."""
        mission, steps = plan_mission(_make_proposal_obj())
        assert mission.step_ids == [s.step_id for s in steps]


# ── EX: executor ─────────────────────────────────────────────────────────────

def _ok_worker(inp):
    return {"status": "ok", "result": "done"}

def _fail_worker(inp):
    return {"status": "fail", "error": "intentional_failure"}

def _crash_worker(inp):
    raise RuntimeError("worker crashed")


class TestExecutor:
    def test_ex01_ok_worker_produces_succeeded_step(self):
        """EX01: ok worker → step status == succeeded, receipt status == ok."""
        step = _valid_step_dict()
        updated, receipt, out_refs = execute(
            step=step, worker_id="local", worker_fn=_ok_worker
        )
        assert updated["status"] == "succeeded"
        assert receipt.status == "ok"
        assert len(out_refs) == 1

    def test_ex02_fail_worker_produces_failed_step(self):
        """EX02: fail worker → step status == failed, receipt status == fail."""
        step = _valid_step_dict()
        updated, receipt, out_refs = execute(
            step=step, worker_id="local", worker_fn=_fail_worker
        )
        assert updated["status"] == "failed"
        assert receipt.status == "fail"

    def test_ex03_crash_worker_never_raises(self):
        """EX03: worker exception is caught; executor never raises."""
        step = _valid_step_dict()
        updated, receipt, _ = execute(
            step=step, worker_id="local", worker_fn=_crash_worker
        )
        assert updated["status"] == "failed"
        assert receipt.status == "fail"
        assert updated["last_error"] is not None
        assert "RuntimeError" in updated["last_error"]

    def test_ex04_ok_worker_receipt_refs_populated(self):
        """EX04: Successful step has receipt_refs containing receipt_id."""
        step = _valid_step_dict()
        updated, receipt, _ = execute(
            step=step, worker_id="local", worker_fn=_ok_worker
        )
        assert receipt.receipt_id in updated["receipt_refs"]

    def test_ex05_deterministic_receipt_id(self):
        """EX05: Same inputs → same receipt_id (deterministic)."""
        step = _valid_step_dict()
        _, r1, _ = execute(step=step, worker_id="local", worker_fn=_ok_worker, tick=5)
        _, r2, _ = execute(step=step, worker_id="local", worker_fn=_ok_worker, tick=5)
        assert r1.receipt_id == r2.receipt_id

    def test_ex06_execute_as_dict_returns_dicts(self):
        """EX06: execute_as_dict() returns plain dicts."""
        step = _valid_step_dict()
        updated, receipt_dict, out_refs = execute_as_dict(
            step=step, worker_id="local", worker_fn=_ok_worker
        )
        assert isinstance(receipt_dict, dict)
        assert receipt_dict["artifact_type"] == "EXECUTION_RECEIPT_V1"

    def test_ex07_original_step_not_mutated(self):
        """EX07: execute() does not mutate the caller's step dict."""
        step = _valid_step_dict()
        original_status = step["status"]
        execute(step=step, worker_id="local", worker_fn=_ok_worker)
        assert step["status"] == original_status  # original unchanged


# ── PR: promotion ─────────────────────────────────────────────────────────────

class TestPromotion:
    def test_pr01_evaluate_valid_proposal_passes(self):
        """PR01: Valid low-risk proposal → PASS verdict."""
        result = evaluate_proposal(_valid_proposal_dict())
        assert result.verdict == "PASS"
        assert result.score == 0.0
        assert result.reason_codes == []

    def test_pr02_evaluate_no_input_refs_blocks(self):
        """PR02: Missing input_refs → BLOCK verdict."""
        result = evaluate_proposal(_valid_proposal_dict(input_refs=[]))
        assert result.verdict == "BLOCK"
        assert "NO_INPUT_REFS" in result.reason_codes

    def test_pr03_evaluate_invalid_step_kind_blocks(self):
        """PR03: Invalid step_kind → BLOCK verdict."""
        result = evaluate_proposal(_valid_proposal_dict(step_kinds=["teleport"]))
        assert result.verdict == "BLOCK"
        assert any("INVALID_STEP_KIND" in c for c in result.reason_codes)

    def test_pr04_evaluate_high_risk_warns(self):
        """PR04: High risk_tier → WARN verdict (not BLOCK)."""
        result = evaluate_proposal(_valid_proposal_dict(risk_tier="high"))
        assert result.verdict == "WARN"
        assert result.score == 0.5

    def test_pr05_update_mission_all_succeeded_with_receipts(self):
        """PR05: All steps succeeded + receipts → mission succeeded."""
        mission = _valid_mission_dict(status="running")
        steps = [
            _valid_step_dict(status="succeeded", receipt_refs=["R-001"]),
            _valid_step_dict(step_id="S-222", status="succeeded", receipt_refs=["R-002"]),
        ]
        updated = update_mission_status(mission, steps)
        assert updated["status"] == "succeeded"

    def test_pr06_update_mission_one_failed_step(self):
        """PR06: One failed step → mission failed."""
        mission = _valid_mission_dict(status="running")
        steps = [
            _valid_step_dict(status="succeeded", receipt_refs=["R-001"]),
            _valid_step_dict(step_id="S-222", status="failed", receipt_refs=[]),
        ]
        updated = update_mission_status(mission, steps)
        assert updated["status"] == "failed"

    def test_pr07_update_mission_succeeded_without_receipt_fails(self):
        """PR07: Step marked succeeded but no receipt_refs → mission failed."""
        mission = _valid_mission_dict(status="running")
        steps = [
            _valid_step_dict(status="succeeded", receipt_refs=[]),
        ]
        updated = update_mission_status(mission, steps)
        assert updated["status"] == "failed"

    def test_pr08_update_mission_still_running(self):
        """PR08: Some steps still queued → mission running."""
        mission = _valid_mission_dict(status="pending")
        steps = [
            _valid_step_dict(status="succeeded", receipt_refs=["R-001"]),
            _valid_step_dict(step_id="S-222", status="queued", receipt_refs=[]),
        ]
        updated = update_mission_status(mission, steps)
        assert updated["status"] == "running"

    def test_pr09_update_mission_does_not_mutate_input(self):
        """PR09: update_mission_status returns new dict, original unchanged."""
        mission = _valid_mission_dict(status="pending")
        steps = [_valid_step_dict(status="succeeded", receipt_refs=["R-001"])]
        original_status = mission["status"]
        _ = update_mission_status(mission, steps)
        assert mission["status"] == original_status

    def test_pr10_as_dict_roundtrip(self):
        """PR10: EvaluationResult.as_dict() produces JSON-serializable dict."""
        import json
        result = evaluate_proposal(_valid_proposal_dict())
        d = result.as_dict()
        assert json.dumps(d)  # must not raise
        assert d["verdict"] == "PASS"
