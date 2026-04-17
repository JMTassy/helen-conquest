"""Research Trajectory Map (RTM) — detect and classify exploration directions.

Law:
  Trajectories are non-sovereign analysis artifacts (authority=NONE).
  They summarise the ELG into performance trends per mutation_family.
  They are INPUTS to the Experiment Selection Policy — not governance outputs.

Algorithm:
  1. Group EXPERIMENT_LINEAGE_V1 nodes by mutation_family.
  2. For each group, compute admitted_count / total → admitted_rate.
  3. Assign performance_trend:
       IMPROVING  → admitted_rate >= IMPROVING_THRESHOLD (default 0.5)
       DECLINING  → admitted_count == 0
       PLATEAU    → otherwise
  4. Assign status:
       ACTIVE     → IMPROVING or PLATEAU with at least one admission
       EXHAUSTED  → DECLINING
  5. confidence = admitted_count / total (rounds to 4 decimal places)

Single responsibility:
  detect_trajectories(lineage)          → list[RESEARCH_TRAJECTORY_V1]
  get_trajectory_by_family(trajs, fam)  → RESEARCH_TRAJECTORY_V1 | None
  get_improving_trajectories(trajs)     → list (only IMPROVING)
  get_dead_trajectories(trajs)          → list (DECLINING status=EXHAUSTED)
"""
from __future__ import annotations

from typing import Any, Mapping

# ── Constants (frozen) ────────────────────────────────────────────────────────

IMPROVING_THRESHOLD: float = 0.5   # admitted_rate >= this → IMPROVING
MUTATION_FAMILIES: frozenset[str] = frozenset({
    "optimizer", "architecture", "retrieval",
    "regularization", "tokenizer", "capability", "other",
})


# ── Core detection function ───────────────────────────────────────────────────

def detect_trajectories(
    lineage: Mapping[str, Any],
    improving_threshold: float = IMPROVING_THRESHOLD,
) -> list[dict[str, Any]]:
    """
    Produce a list of RESEARCH_TRAJECTORY_V1 from an EXPERIMENT_LINEAGE_V1.

    Deterministic: same lineage → same trajectories (sorted by mutation_family).

    Args:
        lineage:             EXPERIMENT_LINEAGE_V1 dict.
        improving_threshold: admitted_rate threshold for IMPROVING trend.

    Returns:
        List of RESEARCH_TRAJECTORY_V1 dicts, one per mutation_family present,
        sorted alphabetically by mutation_family.
    """
    nodes: list[dict[str, Any]] = list(lineage.get("nodes", []))

    # Group by mutation_family
    by_family: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        family = node.get("mutation_family", "other")
        by_family.setdefault(family, []).append(node)

    trajectories: list[dict[str, Any]] = []

    for family in sorted(by_family.keys()):   # sorted → deterministic
        family_nodes = by_family[family]
        total = len(family_nodes)
        if total == 0:
            continue

        admitted = [n for n in family_nodes if n.get("reducer_decision") == "ADMITTED"]
        admitted_count = len(admitted)
        rejected_count = total - admitted_count
        admitted_rate = admitted_count / total

        # Performance trend
        if admitted_count == 0:
            trend = "DECLINING"
        elif admitted_rate >= improving_threshold:
            trend = "IMPROVING"
        else:
            trend = "PLATEAU"

        # Status
        if trend == "DECLINING":
            status = "EXHAUSTED"
        else:
            status = "ACTIVE"

        # Confidence
        confidence = round(admitted_rate, 4)

        # Linked skills: unique skill_ids from admitted nodes
        linked_skills = sorted({n["skill_id"] for n in admitted})

        # Origin experiments: all experiment_ids in this family, sorted
        origin_experiments = sorted(n["experiment_id"] for n in family_nodes)

        trajectory: dict[str, Any] = {
            "schema_name":        "RESEARCH_TRAJECTORY_V1",
            "schema_version":     "1.0.0",
            "trajectory_id":      f"TRAJ_{family.upper()}",
            "mutation_family":    family,
            "origin_experiments": origin_experiments,
            "experiment_count":   total,
            "admitted_count":     admitted_count,
            "rejected_count":     rejected_count,
            "performance_trend":  trend,
            "confidence":         confidence,
            "linked_skills":      linked_skills,
            "status":             status,
            "authority":          "NONE",
        }
        trajectories.append(trajectory)

    return trajectories


# ── Query helpers (pure, no mutation) ────────────────────────────────────────

def get_trajectory_by_family(
    trajectories: list[dict[str, Any]],
    mutation_family: str,
) -> dict[str, Any] | None:
    """Return the trajectory for a given mutation_family, or None."""
    for t in trajectories:
        if t.get("mutation_family") == mutation_family:
            return t
    return None


def get_improving_trajectories(
    trajectories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return only IMPROVING trajectories (promising directions)."""
    return [t for t in trajectories if t.get("performance_trend") == "IMPROVING"]


def get_dead_trajectories(
    trajectories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return DECLINING / EXHAUSTED trajectories (dead zones)."""
    return [t for t in trajectories if t.get("status") == "EXHAUSTED"]


def get_active_trajectories(
    trajectories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return ACTIVE trajectories (IMPROVING or PLATEAU with admissions)."""
    return [t for t in trajectories if t.get("status") == "ACTIVE"]
