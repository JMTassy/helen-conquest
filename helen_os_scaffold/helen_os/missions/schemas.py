from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ProposalSource = Literal["dialogue", "trigger", "reaction", "chronos", "street"]
StepKind = Literal["analyze", "write", "check", "simulate", "compile", "review"]
ProposalStatus = Literal["pending", "promotable", "rejected"]
MissionStatus = Literal["pending", "running", "succeeded", "failed"]
StepStatus = Literal["queued", "running", "succeeded", "failed"]

@dataclass
class ProposalV1:
    artifact_type: Literal["PROPOSAL_V1"]
    proposal_id: str
    source: str
    title: str
    goal: str
    step_kinds: list
    input_refs: list
    risk_tier: str
    status: str
    reason_codes: list

@dataclass
class MissionV1:
    artifact_type: Literal["MISSION_V1"]
    mission_id: str
    source_proposal_id: str
    goal: str
    status: str
    created_from: str
    step_ids: list

@dataclass
class MissionStepV1:
    artifact_type: Literal["MISSION_STEP_V1"]
    step_id: str
    mission_id: str
    step_kind: str
    status: str
    input_refs: list
    output_refs: list
    receipt_refs: list
    last_error: str | None

@dataclass
class ExecutionReceiptV1:
    artifact_type: Literal["EXECUTION_RECEIPT_V1"]
    receipt_id: str
    mission_id: str
    step_id: str
    worker_id: str
    status: Literal["ok", "fail"]
    input_hash: str
    output_hash: str
    trace_ref: str
    created_at_tick: int
