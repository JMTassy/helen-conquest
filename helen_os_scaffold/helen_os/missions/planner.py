"""
helen_os/missions/planner.py — Deterministic mission planner.

Converts a validated ProposalV1 into (MissionV1, list[MissionStepV1]).

Invariants:
  I1  Pure function — no I/O, no side effects.
  I2  Deterministic — same proposal → same mission_id and step_ids.
  I3  Only proposal_service (or this module) may construct MissionV1 objects.
  I4  planner does NOT persist.  Caller routes artifacts to trace channel.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .ids import stable_id
from .schemas import MissionV1, MissionStepV1, ProposalV1


def plan_mission(
    proposal: "ProposalV1 | dict[str, Any]",
) -> tuple[MissionV1, list[MissionStepV1]]:
    """
    Deterministically build (MissionV1, steps) from a ProposalV1 or its dict form.

    Args:
        proposal: Either a ProposalV1 dataclass or the dict produced by asdict(proposal).

    Returns:
        (mission, steps) — fully typed, in-memory only.
    """
    if isinstance(proposal, dict):
        proposal = _from_dict(proposal)

    mission_id = stable_id("M", {
        "proposal_id": proposal.proposal_id,
        "goal": proposal.goal,
        "step_kinds": proposal.step_kinds,
    })

    step_ids: list[str] = []
    steps: list[MissionStepV1] = []

    for idx, kind in enumerate(proposal.step_kinds, start=1):
        sid = stable_id("S", {"mission_id": mission_id, "i": idx, "kind": kind})
        step_ids.append(sid)
        steps.append(MissionStepV1(
            artifact_type="MISSION_STEP_V1",
            step_id=sid,
            mission_id=mission_id,
            step_kind=kind,
            status="queued",
            input_refs=list(proposal.input_refs),
            output_refs=[],
            receipt_refs=[],
            last_error=None,
        ))

    mission = MissionV1(
        artifact_type="MISSION_V1",
        mission_id=mission_id,
        source_proposal_id=proposal.proposal_id,
        goal=proposal.goal,
        status="pending",
        created_from=proposal.source,
        step_ids=step_ids,
    )

    return mission, steps


def plan_mission_as_dicts(
    proposal: "ProposalV1 | dict[str, Any]",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Same as plan_mission() but returns (mission_dict, step_dicts).
    Useful when callers work in dict-space.
    """
    mission, steps = plan_mission(proposal)
    return asdict(mission), [asdict(s) for s in steps]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _from_dict(d: dict[str, Any]) -> ProposalV1:
    """Reconstruct a ProposalV1 from its dict representation."""
    return ProposalV1(
        artifact_type=d["artifact_type"],
        proposal_id=d["proposal_id"],
        source=d["source"],
        title=d["title"],
        goal=d["goal"],
        step_kinds=list(d["step_kinds"]),
        input_refs=list(d["input_refs"]),
        risk_tier=d["risk_tier"],
        status=d["status"],
        reason_codes=list(d.get("reason_codes", [])),
    )
