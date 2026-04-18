from __future__ import annotations
from dataclasses import asdict, replace
from typing import Any
from .ids import stable_id
from .schemas import ProposalV1, MissionV1, MissionStepV1

ALLOWED_STEP_KINDS = {"analyze", "write", "check", "simulate", "compile", "review"}

def create_proposal_and_maybe_promote(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Single entrypoint: validate -> cap gates -> filter stub -> mission+steps.
    Returns in-memory bundle. Caller decides persistence (trace channel only).
    """
    proposal = _validate_and_normalize_proposal(payload)

    gate = _cap_gates(proposal)
    if not gate["ok"]:
        proposal = replace(proposal, status="rejected", reason_codes=gate["reason_codes"])
        return {
            "proposal": asdict(proposal),
            "promotion_class": "REJECTED",
            "reason_codes": gate["reason_codes"],
            "mission": None,
            "steps": [],
        }

    filt = _v3_filter_stub(proposal)
    if filt["status"] == "BLOCK":
        proposal = replace(proposal, status="rejected", reason_codes=["FILTER_BLOCK"])
        return {
            "proposal": asdict(proposal),
            "promotion_class": "REJECTED",
            "reason_codes": ["FILTER_BLOCK"],
            "mission": None,
            "steps": [],
        }

    proposal = replace(proposal, status="promotable")
    mission, steps = _create_mission_and_steps(proposal)
    return {
        "proposal": asdict(proposal),
        "promotion_class": "PROMOTABLE_TO_MISSION",
        "reason_codes": [],
        "mission": asdict(mission),
        "steps": [asdict(s) for s in steps],
    }

def _validate_and_normalize_proposal(payload: dict[str, Any]) -> ProposalV1:
    required = ["proposal_id", "source", "title", "goal", "step_kinds", "input_refs", "risk_tier"]
    for k in required:
        if k not in payload:
            raise ValueError(f"missing field: {k}")
    if not payload["step_kinds"] or any(sk not in ALLOWED_STEP_KINDS for sk in payload["step_kinds"]):
        raise ValueError("invalid step_kinds")
    return ProposalV1(
        artifact_type="PROPOSAL_V1",
        proposal_id=payload["proposal_id"],
        source=payload["source"],
        title=payload["title"],
        goal=payload["goal"],
        step_kinds=list(payload["step_kinds"]),
        input_refs=list(payload["input_refs"]),
        risk_tier=payload["risk_tier"],
        status="pending",
        reason_codes=[],
    )

def _cap_gates(proposal: ProposalV1) -> dict[str, Any]:
    if not proposal.input_refs:
        return {"ok": False, "reason_codes": ["NO_INPUT_REFS"]}
    return {"ok": True, "reason_codes": []}

def _v3_filter_stub(proposal: ProposalV1) -> dict[str, Any]:
    # Stub: always PASS. Replace with real AEON/COMM/GROUND/DET scores later.
    return {"status": "PASS", "overall_L_v3": 0.0}

def _create_mission_and_steps(proposal: ProposalV1) -> tuple[MissionV1, list[MissionStepV1]]:
    mission_id = stable_id("M", {
        "proposal_id": proposal.proposal_id,
        "goal": proposal.goal,
        "step_kinds": proposal.step_kinds,
    })
    step_ids: list[str] = []
    steps: list[MissionStepV1] = []
    for i, kind in enumerate(proposal.step_kinds, start=1):
        sid = stable_id("S", {"mission_id": mission_id, "i": i, "kind": kind})
        step_ids.append(sid)
        steps.append(MissionStepV1(
            artifact_type="MISSION_STEP_V1",
            step_id=sid,
            mission_id=mission_id,
            step_kind=kind,
            status="queued",
            input_refs=proposal.input_refs,
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
