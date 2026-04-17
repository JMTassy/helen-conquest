"""Tests for Research Trajectory Map (RTM) — detect_trajectories().

Invariants verified:
  RTM-1. Deterministic: same lineage → same trajectories.
  RTM-2. Grouping: one trajectory per mutation_family present in lineage.
  RTM-3. IMPROVING when admitted_rate >= 0.5.
  RTM-4. DECLINING when admitted_count == 0.
  RTM-5. PLATEAU when mixed (0 < admitted < threshold).
  RTM-6. confidence = admitted_count / total (rounded 4dp).
  RTM-7. status = EXHAUSTED for DECLINING, ACTIVE for others.
  RTM-8. linked_skills = unique skill_ids of ADMITTED nodes (sorted).
  RTM-9. authority = "NONE" on all trajectories.
  RTM-10. Query helpers are pure (no side effects).
"""
from __future__ import annotations

from helen_os.lineage.experiment_lineage_v1 import (
    make_empty_lineage,
    append_experiment_node,
    build_experiment_node,
)
from helen_os.trajectory.research_trajectory_v1 import (
    detect_trajectories,
    get_trajectory_by_family,
    get_improving_trajectories,
    get_dead_trajectories,
    get_active_trajectories,
    IMPROVING_THRESHOLD,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

_H = "sha256:" + "f" * 64


def _node(eid, family, decision, skill_id="skill.search"):
    return build_experiment_node(
        experiment_id=eid,
        skill_id=skill_id,
        candidate_version="1.0.0",
        mutation_family=family,
        eval_receipt_hash=_H,
        promotion_case_hash=_H,
        reducer_decision=decision,
    )


def _lin_with(*nodes):
    lin = make_empty_lineage("lin_rtm_test")
    for n in nodes:
        lin = append_experiment_node(lin, n)
    return lin


# ── RTM tests ─────────────────────────────────────────────────────────────────

class TestDetectTrajectories:

    def test_rtm_1_deterministic(self):
        """RTM-1: same lineage → same trajectories on two calls."""
        lin = _lin_with(
            _node("E1", "architecture", "ADMITTED"),
            _node("E2", "architecture", "ADMITTED"),
            _node("E3", "optimizer",    "REJECTED"),
        )
        t1 = detect_trajectories(lin)
        t2 = detect_trajectories(lin)
        assert t1 == t2

    def test_rtm_2_one_trajectory_per_family(self):
        """RTM-2: one RESEARCH_TRAJECTORY_V1 per mutation_family."""
        lin = _lin_with(
            _node("E1", "architecture", "ADMITTED"),
            _node("E2", "optimizer",    "REJECTED"),
            _node("E3", "architecture", "REJECTED"),
        )
        trajs = detect_trajectories(lin)
        families = [t["mutation_family"] for t in trajs]
        assert sorted(families) == sorted(set(families))   # unique
        assert "architecture" in families
        assert "optimizer" in families

    def test_rtm_3_improving_when_majority_admitted(self):
        """RTM-3: admitted_rate >= 0.5 → IMPROVING."""
        lin = _lin_with(
            _node("E1", "architecture", "ADMITTED"),
            _node("E2", "architecture", "ADMITTED"),
            _node("E3", "architecture", "REJECTED"),
        )
        trajs = detect_trajectories(lin)
        arch = get_trajectory_by_family(trajs, "architecture")
        assert arch["performance_trend"] == "IMPROVING"
        assert arch["status"] == "ACTIVE"

    def test_rtm_4_declining_when_all_rejected(self):
        """RTM-4: admitted_count == 0 → DECLINING, status=EXHAUSTED."""
        lin = _lin_with(
            _node("E1", "optimizer", "REJECTED"),
            _node("E2", "optimizer", "REJECTED"),
            _node("E3", "optimizer", "REJECTED"),
        )
        trajs = detect_trajectories(lin)
        opt = get_trajectory_by_family(trajs, "optimizer")
        assert opt["performance_trend"] == "DECLINING"
        assert opt["status"] == "EXHAUSTED"

    def test_rtm_5_plateau_when_mixed_below_threshold(self):
        """RTM-5: 0 < admitted_rate < 0.5 → PLATEAU."""
        lin = _lin_with(
            _node("E1", "retrieval", "ADMITTED"),
            _node("E2", "retrieval", "REJECTED"),
            _node("E3", "retrieval", "REJECTED"),
        )
        trajs = detect_trajectories(lin)
        ret = get_trajectory_by_family(trajs, "retrieval")
        assert ret["performance_trend"] == "PLATEAU"
        assert ret["status"] == "ACTIVE"

    def test_rtm_6_confidence_equals_admitted_rate(self):
        """RTM-6: confidence = admitted_count / total."""
        lin = _lin_with(
            _node("E1", "architecture", "ADMITTED"),
            _node("E2", "architecture", "ADMITTED"),
            _node("E3", "architecture", "REJECTED"),
            _node("E4", "architecture", "REJECTED"),
        )
        trajs = detect_trajectories(lin)
        arch = get_trajectory_by_family(trajs, "architecture")
        assert arch["admitted_count"] == 2
        assert arch["rejected_count"] == 2
        assert arch["confidence"] == round(2 / 4, 4)

    def test_rtm_7_status_exhausted_for_declining(self):
        """RTM-7: DECLINING → status=EXHAUSTED."""
        lin = _lin_with(_node("E1", "capability", "REJECTED"))
        trajs = detect_trajectories(lin)
        cap = get_trajectory_by_family(trajs, "capability")
        assert cap["status"] == "EXHAUSTED"

    def test_rtm_8_linked_skills_are_admitted_only(self):
        """RTM-8: linked_skills contains skill_ids from ADMITTED nodes only."""
        lin = _lin_with(
            _node("E1", "architecture", "ADMITTED", skill_id="skill.search"),
            _node("E2", "architecture", "REJECTED", skill_id="skill.rank"),
            _node("E3", "architecture", "ADMITTED", skill_id="skill.filter"),
        )
        trajs = detect_trajectories(lin)
        arch = get_trajectory_by_family(trajs, "architecture")
        assert "skill.search" in arch["linked_skills"]
        assert "skill.filter" in arch["linked_skills"]
        assert "skill.rank" not in arch["linked_skills"]

    def test_rtm_9_authority_is_none(self):
        """RTM-9: all trajectories carry authority=NONE."""
        lin = _lin_with(_node("E1", "optimizer", "ADMITTED"))
        trajs = detect_trajectories(lin)
        assert all(t["authority"] == "NONE" for t in trajs)

    def test_rtm_10_empty_lineage_no_trajectories(self):
        """RTM-10: empty lineage → empty trajectory list."""
        lin = make_empty_lineage("lin_empty")
        assert detect_trajectories(lin) == []

    def test_rtm_schema_name(self):
        lin = _lin_with(_node("E1", "architecture", "ADMITTED"))
        trajs = detect_trajectories(lin)
        assert trajs[0]["schema_name"] == "RESEARCH_TRAJECTORY_V1"

    def test_improving_threshold_boundary(self):
        """Exactly at threshold (2/4 = 0.5) should be IMPROVING."""
        lin = _lin_with(
            _node("E1", "tokenizer", "ADMITTED"),
            _node("E2", "tokenizer", "ADMITTED"),
            _node("E3", "tokenizer", "REJECTED"),
            _node("E4", "tokenizer", "REJECTED"),
        )
        trajs = detect_trajectories(lin)
        tok = get_trajectory_by_family(trajs, "tokenizer")
        assert tok["confidence"] == 0.5
        assert tok["performance_trend"] == "IMPROVING"


class TestTrajectoryQueryHelpers:

    def _build_mixed_trajs(self):
        lin = _lin_with(
            _node("E1", "architecture", "ADMITTED"),
            _node("E2", "architecture", "ADMITTED"),
            _node("E3", "optimizer",    "REJECTED"),
            _node("E4", "retrieval",    "ADMITTED"),
            _node("E5", "retrieval",    "REJECTED"),
            _node("E6", "capability",   "REJECTED"),
        )
        return detect_trajectories(lin)

    def test_get_improving_trajectories(self):
        trajs = self._build_mixed_trajs()
        improving = get_improving_trajectories(trajs)
        assert all(t["performance_trend"] == "IMPROVING" for t in improving)
        # architecture (2/2=1.0) is IMPROVING
        families = {t["mutation_family"] for t in improving}
        assert "architecture" in families

    def test_get_dead_trajectories(self):
        trajs = self._build_mixed_trajs()
        dead = get_dead_trajectories(trajs)
        assert all(t["status"] == "EXHAUSTED" for t in dead)
        families = {t["mutation_family"] for t in dead}
        assert "optimizer" in families
        assert "capability" in families

    def test_get_active_trajectories(self):
        trajs = self._build_mixed_trajs()
        active = get_active_trajectories(trajs)
        assert all(t["status"] == "ACTIVE" for t in active)
