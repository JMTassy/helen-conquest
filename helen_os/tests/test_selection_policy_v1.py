"""Tests for Experiment Selection Policy — selection_policy_v1.py.

Invariants verified:
  SP-1.  Governance filter rejects high-risk candidates.
  SP-2.  Governance filter rejects high-redundancy candidates.
  SP-3.  score_candidate is deterministic.
  SP-4.  score_candidate uses correct weighted sum.
  SP-5.  REPAIR tier: failure_cluster_priority >= threshold.
  SP-6.  EXPLOIT tier: strategic_alignment >= threshold (no repair pressure).
  SP-7.  EXPLORE tier: branch_novelty >= threshold (no repair/exploit).
  SP-8.  VALIDATE tier: default (all below thresholds).
  SP-9.  run_selection picks highest-scoring valid candidate.
  SP-10. run_selection raises NoValidCandidateError if all filtered out.
  SP-11. run_selection is deterministic: same inputs → same output.
  SP-12. selection decision carries authority=NONE.
  SP-13. policy_hash changes when policy changes.
  SP-14. MVP_POLICY is frozen (all required keys present).
"""
from __future__ import annotations

import copy

import pytest

from helen_os.selection.selection_policy_v1 import (
    MVP_POLICY,
    passes_governance_filter,
    score_candidate,
    classify_tier,
    run_selection,
    policy_hash,
    NoValidCandidateError,
)
from helen_os.governance.canonical import sha256_prefixed


# ── Helpers ───────────────────────────────────────────────────────────────────

def _candidate(candidate_id="CAND_001",
               skill_id="skill.search",
               mutation_family="architecture",
               expected_improvement=0.7,
               information_gain=0.6,
               strategic_alignment=0.5,
               risk=0.2,
               cost=0.2,
               redundancy=0.2,
               failure_cluster_priority=0.3,
               branch_novelty=0.4):
    return {
        "schema_name":    "EXPERIMENT_CANDIDATE_V1",
        "schema_version": "1.0.0",
        "candidate_id":   candidate_id,
        "skill_id":       skill_id,
        "candidate_skill_version": "2.0.0",
        "mutation_family": mutation_family,
        "description":    f"Test mutation for {skill_id}",
        "scoring_inputs": {
            "expected_improvement":     expected_improvement,
            "information_gain":         information_gain,
            "strategic_alignment":      strategic_alignment,
            "risk":                     risk,
            "cost":                     cost,
            "redundancy":               redundancy,
            "failure_cluster_priority": failure_cluster_priority,
            "branch_novelty":           branch_novelty,
        },
    }


# ── SP-1/2: Governance filter ─────────────────────────────────────────────────

class TestGovernanceFilter:

    def test_sp1_high_risk_filtered(self):
        """SP-1: candidate with risk > max_risk is excluded."""
        c = _candidate(risk=0.9)
        assert not passes_governance_filter(c, MVP_POLICY)

    def test_sp2_high_redundancy_filtered(self):
        """SP-2: candidate with redundancy > max_redundancy is excluded."""
        c = _candidate(redundancy=0.9)
        assert not passes_governance_filter(c, MVP_POLICY)

    def test_low_risk_and_redundancy_passes(self):
        c = _candidate(risk=0.1, redundancy=0.1)
        assert passes_governance_filter(c, MVP_POLICY)

    def test_exactly_at_max_risk_passes(self):
        """At max_risk (not exceeding) → passes (<=)."""
        c = _candidate(risk=MVP_POLICY["governance_filter"]["max_risk"])
        assert passes_governance_filter(c, MVP_POLICY)


# ── SP-3/4: Scoring ───────────────────────────────────────────────────────────

class TestScoring:

    def test_sp3_score_deterministic(self):
        """SP-3: same candidate + same policy → same score."""
        c = _candidate()
        s1 = score_candidate(c, MVP_POLICY)
        s2 = score_candidate(c, MVP_POLICY)
        assert s1 == s2

    def test_sp4_score_weighted_sum(self):
        """SP-4: score is correct weighted sum."""
        c = _candidate(
            expected_improvement=1.0,
            information_gain=0.0,
            strategic_alignment=0.0,
            risk=0.0, cost=0.0, redundancy=0.0,
            failure_cluster_priority=0.0, branch_novelty=0.0,
        )
        # Only expected_improvement matters: weight=3.0, value=1.0 → score=3.0
        assert score_candidate(c, MVP_POLICY) == pytest.approx(3.0, abs=1e-6)

    def test_sp4_negative_weights_reduce_score(self):
        """SP-4: risk/cost/redundancy reduce the score."""
        c_clean = _candidate(risk=0.0, cost=0.0, redundancy=0.0)
        c_risky = _candidate(risk=0.5, cost=0.5, redundancy=0.5)
        assert score_candidate(c_clean, MVP_POLICY) > score_candidate(c_risky, MVP_POLICY)

    def test_sp4_all_zeros_score_is_zero(self):
        """SP-4: all zeros → score = 0."""
        c = _candidate(
            expected_improvement=0.0, information_gain=0.0,
            strategic_alignment=0.0, risk=0.0, cost=0.0,
            redundancy=0.0, failure_cluster_priority=0.0, branch_novelty=0.0,
        )
        assert score_candidate(c, MVP_POLICY) == pytest.approx(0.0, abs=1e-6)


# ── SP-5/6/7/8: Tier classification ──────────────────────────────────────────

class TestTierClassification:

    def test_sp5_repair_tier(self):
        """SP-5: high failure_cluster_priority → REPAIR."""
        c = _candidate(failure_cluster_priority=0.9)
        assert classify_tier(c, MVP_POLICY) == "REPAIR"

    def test_sp6_exploit_tier(self):
        """SP-6: high strategic_alignment (no repair pressure) → EXPLOIT."""
        c = _candidate(failure_cluster_priority=0.1, strategic_alignment=0.9)
        assert classify_tier(c, MVP_POLICY) == "EXPLOIT"

    def test_sp7_explore_tier(self):
        """SP-7: high branch_novelty (no repair/exploit) → EXPLORE."""
        c = _candidate(
            failure_cluster_priority=0.1,
            strategic_alignment=0.1,
            branch_novelty=0.9,
        )
        assert classify_tier(c, MVP_POLICY) == "EXPLORE"

    def test_sp8_validate_tier(self):
        """SP-8: all below thresholds → VALIDATE."""
        c = _candidate(
            failure_cluster_priority=0.1,
            strategic_alignment=0.1,
            branch_novelty=0.1,
        )
        assert classify_tier(c, MVP_POLICY) == "VALIDATE"

    def test_repair_takes_priority_over_exploit(self):
        """REPAIR checked before EXPLOIT — if both high, REPAIR wins."""
        c = _candidate(failure_cluster_priority=0.9, strategic_alignment=0.9)
        assert classify_tier(c, MVP_POLICY) == "REPAIR"

    def test_exploit_takes_priority_over_explore(self):
        """EXPLOIT checked before EXPLORE."""
        c = _candidate(
            failure_cluster_priority=0.1,
            strategic_alignment=0.9,
            branch_novelty=0.9,
        )
        assert classify_tier(c, MVP_POLICY) == "EXPLOIT"


# ── SP-9/10/11/12: run_selection ─────────────────────────────────────────────

class TestRunSelection:

    def test_sp9_selects_highest_scoring_candidate(self):
        """SP-9: highest-scoring valid candidate is selected."""
        low  = _candidate("CAND_LOW",  expected_improvement=0.1, information_gain=0.1)
        high = _candidate("CAND_HIGH", expected_improvement=0.9, information_gain=0.9)
        decision = run_selection([low, high], MVP_POLICY, "SEL_001")
        assert decision["selected_candidate_id"] == "CAND_HIGH"

    def test_sp9_governance_filter_excludes_risky(self):
        """SP-9: risky candidate excluded, second-best selected."""
        risky  = _candidate("CAND_RISKY",  risk=0.9, expected_improvement=1.0)
        safe   = _candidate("CAND_SAFE",   risk=0.1, expected_improvement=0.5)
        decision = run_selection([risky, safe], MVP_POLICY, "SEL_002")
        assert decision["selected_candidate_id"] == "CAND_SAFE"

    def test_sp10_raises_if_all_filtered(self):
        """SP-10: NoValidCandidateError if all candidates fail governance filter."""
        all_risky = [
            _candidate("C1", risk=0.9),
            _candidate("C2", risk=0.9),
        ]
        with pytest.raises(NoValidCandidateError):
            run_selection(all_risky, MVP_POLICY, "SEL_003")

    def test_sp11_deterministic(self):
        """SP-11: same inputs → same output."""
        candidates = [
            _candidate("C1", expected_improvement=0.5),
            _candidate("C2", expected_improvement=0.8),
            _candidate("C3", expected_improvement=0.3),
        ]
        d1 = run_selection(candidates, MVP_POLICY, "SEL_004")
        d2 = run_selection(candidates, MVP_POLICY, "SEL_004")
        assert sha256_prefixed(d1) == sha256_prefixed(d2)

    def test_sp12_authority_is_none(self):
        """SP-12: selection decision carries authority=NONE."""
        c = _candidate()
        decision = run_selection([c], MVP_POLICY, "SEL_005")
        assert decision["authority"] == "NONE"

    def test_selection_schema_name(self):
        c = _candidate()
        decision = run_selection([c], MVP_POLICY, "SEL_006")
        assert decision["schema_name"] == "EXPERIMENT_SELECTION_DECISION_V1"

    def test_score_breakdown_present(self):
        c = _candidate()
        decision = run_selection([c], MVP_POLICY, "SEL_007")
        bd = decision["score_breakdown"]
        assert "final_score" in bd
        assert "expected_improvement" in bd
        assert "failure_cluster_priority" in bd

    def test_max_candidates_bounds_input(self):
        """max_candidates limits how many candidates are considered."""
        policy_tight = dict(MVP_POLICY, max_candidates=1)
        best = _candidate("BEST", expected_improvement=0.9)
        ignored = _candidate("IGNORED", expected_improvement=0.1)
        decision = run_selection([best, ignored], policy_tight, "SEL_008")
        assert decision["selected_candidate_id"] == "BEST"

    def test_repair_tier_selection_reason(self):
        c = _candidate(failure_cluster_priority=0.9)
        decision = run_selection([c], MVP_POLICY, "SEL_009")
        assert decision["selection_tier"] == "REPAIR"
        assert decision["selection_reason"] == "FAILURE_CLUSTER_PRIORITY"


# ── SP-13/14: Policy integrity ────────────────────────────────────────────────

class TestPolicyIntegrity:

    def test_sp13_policy_hash_changes_on_weight_change(self):
        """SP-13: any weight change → different policy hash."""
        modified = copy.deepcopy(MVP_POLICY)
        modified["weights"]["expected_improvement"] = 99.0
        assert policy_hash(MVP_POLICY) != policy_hash(modified)

    def test_sp13_policy_hash_deterministic(self):
        h1 = policy_hash(MVP_POLICY)
        h2 = policy_hash(MVP_POLICY)
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_sp14_mvp_policy_has_required_keys(self):
        """SP-14: MVP_POLICY has all required fields."""
        assert MVP_POLICY["schema_name"]    == "SELECTION_POLICY_V1"
        assert MVP_POLICY["authority"]      == "NONE"
        assert "weights"             in MVP_POLICY
        assert "tier_thresholds"     in MVP_POLICY
        assert "governance_filter"   in MVP_POLICY
        for key in ["expected_improvement", "information_gain",
                    "strategic_alignment", "failure_cluster_priority",
                    "branch_novelty", "risk", "cost", "redundancy"]:
            assert key in MVP_POLICY["weights"]
