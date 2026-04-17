"""Experiment Selection Policy — governed, typed, deterministic.

Law:
  The Selection Policy is NON-SOVEREIGN.
  It directs which experiment to run next — it does not mutate state.
  Only reducer-emitted decisions may alter governed state.

Constitutional separation:
  HER / Autoresearch proposes experiments (EXPERIMENT_CANDIDATE_V1)
  Selection Policy ranks and selects (EXPERIMENT_SELECTION_DECISION_V1)
  Reducer governs skill admission (SKILL_PROMOTION_DECISION_V1)

Selection flow:
  1. candidates → governance_filter() → filtered candidates
  2. filtered candidates → score_candidate() → scored list
  3. scored list → classify_tier() → REPAIR | EXPLOIT | EXPLORE | VALIDATE
  4. best candidate → EXPERIMENT_SELECTION_DECISION_V1

MVP scoring function (linear weighted sum):
  S = w_ei * expected_improvement
    + w_ig * information_gain
    + w_sa * strategic_alignment
    + w_fc * failure_cluster_priority
    + w_bn * branch_novelty
    + w_r  * risk          (negative weight)
    + w_c  * cost          (negative weight)
    + w_rd * redundancy    (negative weight)

Tier classification (REPAIR checked first):
  REPAIR:   failure_cluster_priority >= tier_thresholds.repair_failure_cluster_priority
  EXPLOIT:  strategic_alignment >= tier_thresholds.exploit_strategic_alignment
  EXPLORE:  branch_novelty >= tier_thresholds.explore_branch_novelty
  VALIDATE: (default)

Governance filter (hard reject before scoring):
  risk > governance_filter.max_risk       → excluded
  redundancy > governance_filter.max_redundancy → excluded

Single responsibility:
  MVP_POLICY    → frozen default policy object
  passes_governance_filter() → bool
  score_candidate()          → float (weighted sum)
  classify_tier()            → tier str
  run_selection()            → EXPERIMENT_SELECTION_DECISION_V1
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.canonical import sha256_prefixed


# ── Frozen default policy (MVP) ───────────────────────────────────────────────

MVP_POLICY: dict[str, Any] = {
    "schema_name":    "SELECTION_POLICY_V1",
    "schema_version": "1.0.0",
    "policy_id":      "MVP_POLICY_V1",
    "weights": {
        "expected_improvement":     3.0,
        "information_gain":         2.0,
        "strategic_alignment":      2.0,
        "failure_cluster_priority": 3.0,
        "branch_novelty":           2.0,
        "risk":                    -2.0,
        "cost":                    -1.0,
        "redundancy":              -1.0,
    },
    "tier_thresholds": {
        "repair_failure_cluster_priority": 0.7,
        "exploit_strategic_alignment":     0.7,
        "explore_branch_novelty":          0.6,
    },
    "governance_filter": {
        "max_risk":       0.8,
        "max_redundancy": 0.85,
    },
    "max_candidates": 10,
    "authority":      "NONE",
}


# ── Governance filter ─────────────────────────────────────────────────────────

def passes_governance_filter(
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> bool:
    """
    Return True iff candidate passes the policy's hard rejection filters.

    A candidate is excluded if:
      - risk > governance_filter.max_risk
      - redundancy > governance_filter.max_redundancy
    """
    si = candidate.get("scoring_inputs", {})
    gf = policy.get("governance_filter", {})
    max_risk       = float(gf.get("max_risk", 0.8))
    max_redundancy = float(gf.get("max_redundancy", 0.85))
    return (
        float(si.get("risk", 1.0)) <= max_risk
        and float(si.get("redundancy", 1.0)) <= max_redundancy
    )


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_candidate(
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> float:
    """
    Compute the linear weighted score for a candidate.

    S = Σ w_i * x_i   (weights from policy, inputs from candidate.scoring_inputs)

    Returns:
        float score (unbounded; higher is better).
    """
    si = candidate.get("scoring_inputs", {})
    w  = policy.get("weights", {})

    score = (
        float(w.get("expected_improvement",     3.0)) * float(si.get("expected_improvement",     0.0))
      + float(w.get("information_gain",         2.0)) * float(si.get("information_gain",         0.0))
      + float(w.get("strategic_alignment",      2.0)) * float(si.get("strategic_alignment",      0.0))
      + float(w.get("failure_cluster_priority", 3.0)) * float(si.get("failure_cluster_priority", 0.0))
      + float(w.get("branch_novelty",           2.0)) * float(si.get("branch_novelty",           0.0))
      + float(w.get("risk",                    -2.0)) * float(si.get("risk",                     0.0))
      + float(w.get("cost",                    -1.0)) * float(si.get("cost",                     0.0))
      + float(w.get("redundancy",              -1.0)) * float(si.get("redundancy",               0.0))
    )
    return round(score, 6)


# ── Tier classification ───────────────────────────────────────────────────────

_TIER_REASONS: dict[str, str] = {
    "REPAIR":   "FAILURE_CLUSTER_PRIORITY",
    "EXPLOIT":  "PROMISING_TRAJECTORY_EXPLOITATION",
    "EXPLORE":  "BRANCH_NOVELTY",
    "VALIDATE": "CONFIRMATION_NEEDED",
}


def classify_tier(
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> str:
    """
    Assign a priority tier to a candidate based on policy thresholds.

    Evaluation order (first match wins):
      1. REPAIR   — failure_cluster_priority >= repair threshold
      2. EXPLOIT  — strategic_alignment >= exploit threshold
      3. EXPLORE  — branch_novelty >= explore threshold
      4. VALIDATE — default

    Returns:
        One of "REPAIR", "EXPLOIT", "EXPLORE", "VALIDATE".
    """
    si = candidate.get("scoring_inputs", {})
    t  = policy.get("tier_thresholds", {})

    repair_t  = float(t.get("repair_failure_cluster_priority", 0.7))
    exploit_t = float(t.get("exploit_strategic_alignment",     0.7))
    explore_t = float(t.get("explore_branch_novelty",          0.6))

    if float(si.get("failure_cluster_priority", 0.0)) >= repair_t:
        return "REPAIR"
    if float(si.get("strategic_alignment", 0.0)) >= exploit_t:
        return "EXPLOIT"
    if float(si.get("branch_novelty", 0.0)) >= explore_t:
        return "EXPLORE"
    return "VALIDATE"


# ── Selection runner ──────────────────────────────────────────────────────────

class NoValidCandidateError(ValueError):
    """Raised when all candidates fail the governance filter."""
    pass


def run_selection(
    candidates: list[Mapping[str, Any]],
    policy: Mapping[str, Any],
    decision_id: str,
) -> dict[str, Any]:
    """
    Run the full selection pipeline: filter → score → classify → decide.

    Args:
        candidates:   List of EXPERIMENT_CANDIDATE_V1 dicts.
        policy:       SELECTION_POLICY_V1 dict.
        decision_id:  Unique identifier for the resulting decision.

    Returns:
        EXPERIMENT_SELECTION_DECISION_V1 dict (authority=NONE).

    Raises:
        NoValidCandidateError: if no candidate passes the governance filter.

    Determinism:
        Same candidates list in same order + same policy → same decision.
        Tie-breaking is stable (first highest-scoring candidate wins).
    """
    max_c = int(policy.get("max_candidates", len(candidates)))
    bounded = list(candidates)[:max_c]

    # Step 1: Governance filter
    valid = [c for c in bounded if passes_governance_filter(c, policy)]

    if not valid:
        raise NoValidCandidateError(
            f"No candidates pass governance filter from {len(bounded)} provided."
        )

    # Step 2: Score all valid candidates
    scored: list[tuple[float, dict[str, Any]]] = [
        (score_candidate(c, policy), dict(c)) for c in valid
    ]

    # Step 3: Sort descending by score (stable — preserves original order on ties)
    scored.sort(key=lambda x: -x[0])
    best_score, best_candidate = scored[0]

    # Step 4: Classify tier
    tier = classify_tier(best_candidate, policy)
    si   = best_candidate.get("scoring_inputs", {})

    return {
        "schema_name":           "EXPERIMENT_SELECTION_DECISION_V1",
        "schema_version":        "1.0.0",
        "decision_id":           decision_id,
        "policy_id":             str(policy.get("policy_id", "UNKNOWN")),
        "selected_candidate_id": str(best_candidate.get("candidate_id", "")),
        "selection_tier":        tier,
        "selection_reason":      _TIER_REASONS[tier],
        "score_breakdown": {
            "expected_improvement":     float(si.get("expected_improvement", 0.0)),
            "information_gain":         float(si.get("information_gain", 0.0)),
            "strategic_alignment":      float(si.get("strategic_alignment", 0.0)),
            "risk_score":               float(si.get("risk", 0.0)),
            "cost_score":               float(si.get("cost", 0.0)),
            "redundancy_score":         float(si.get("redundancy", 0.0)),
            "failure_cluster_priority": float(si.get("failure_cluster_priority", 0.0)),
            "branch_novelty":           float(si.get("branch_novelty", 0.0)),
            "final_score":              best_score,
        },
        "authority": "NONE",
    }


# ── Policy hash ───────────────────────────────────────────────────────────────

def policy_hash(policy: Mapping[str, Any]) -> str:
    """
    Return deterministic SHA-256 of the policy.
    A change in any weight or threshold produces a different hash.
    """
    return sha256_prefixed(dict(policy))
