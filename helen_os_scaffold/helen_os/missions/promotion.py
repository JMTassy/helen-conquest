"""
helen_os/missions/promotion.py — Governance transition logic.

Two pure functions that implement the promotion gate and the mission
status update rule.

Functions:
  evaluate_proposal(proposal_dict)  → EvaluationResult
  update_mission_status(mission, steps) → updated mission dict

Invariants:
  I1  evaluate_proposal is deterministic — same inputs → same verdict.
  I2  update_mission_status mirrors mission_reducer.finalize_mission but
      takes typed dicts; does NOT mutate in place (returns new dict).
  I3  Neither function performs I/O or writes to storage.
  I4  Promotion decisions never claim sovereignty.
"""
from __future__ import annotations

from typing import Any, Literal

EvaluationVerdict = Literal["PASS", "WARN", "BLOCK"]


class EvaluationResult:
    """Result of evaluate_proposal()."""

    __slots__ = ("verdict", "reason_codes", "score")

    def __init__(
        self,
        verdict: EvaluationVerdict,
        reason_codes: list[str],
        score: float,
    ) -> None:
        self.verdict      = verdict
        self.reason_codes = list(reason_codes)
        self.score        = score  # 0.0–1.0; higher = more concern

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict":      self.verdict,
            "reason_codes": self.reason_codes,
            "score":        self.score,
        }

    def __repr__(self) -> str:
        return (
            f"EvaluationResult(verdict={self.verdict!r}, "
            f"reason_codes={self.reason_codes!r}, score={self.score})"
        )


# ── Cap-gate predicates ───────────────────────────────────────────────────────

_HIGH_RISK_TIERS = frozenset({"high", "critical"})
_ALLOWED_STEP_KINDS = frozenset({"analyze", "write", "check", "simulate", "compile", "review"})


def _check_input_refs(p: dict[str, Any]) -> tuple[bool, list[str]]:
    refs = p.get("input_refs") or []
    if not refs:
        return False, ["NO_INPUT_REFS"]
    return True, []


def _check_step_kinds(p: dict[str, Any]) -> tuple[bool, list[str]]:
    kinds = p.get("step_kinds") or []
    bad   = [k for k in kinds if k not in _ALLOWED_STEP_KINDS]
    if bad:
        return False, [f"INVALID_STEP_KIND:{k}" for k in bad]
    return True, []


def _check_risk_tier(p: dict[str, Any]) -> tuple[bool, list[str]]:
    tier = p.get("risk_tier", "low")
    if tier in _HIGH_RISK_TIERS:
        return False, [f"HIGH_RISK_TIER:{tier}"]
    return True, []


# ── evaluate_proposal ────────────────────────────────────────────────────────

def evaluate_proposal(proposal: dict[str, Any]) -> EvaluationResult:
    """
    Deterministic evaluation of a PROPOSAL_V1 dict.

    Evaluation tiers:
      BLOCK  — missing required structural fields; will never succeed.
      WARN   — high risk tier; requires additional review before promotion.
      PASS   — proposal meets all structural requirements.

    Returns:
        EvaluationResult with verdict, reason_codes, and score (0.0–1.0).
    """
    all_reason_codes: list[str] = []

    ok_refs,   codes_refs   = _check_input_refs(proposal)
    ok_kinds,  codes_kinds  = _check_step_kinds(proposal)
    ok_risk,   codes_risk   = _check_risk_tier(proposal)

    if not ok_refs:
        all_reason_codes.extend(codes_refs)
    if not ok_kinds:
        all_reason_codes.extend(codes_kinds)

    # Hard BLOCK: structural violations
    if not ok_refs or not ok_kinds:
        return EvaluationResult(
            verdict="BLOCK",
            reason_codes=all_reason_codes,
            score=1.0,
        )

    # Soft WARN: high risk tier passes structurally but needs review
    if not ok_risk:
        all_reason_codes.extend(codes_risk)
        return EvaluationResult(
            verdict="WARN",
            reason_codes=all_reason_codes,
            score=0.5,
        )

    # PASS
    return EvaluationResult(
        verdict="PASS",
        reason_codes=[],
        score=0.0,
    )


# ── update_mission_status ─────────────────────────────────────────────────────

def update_mission_status(
    mission: dict[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute new mission status from step statuses.

    Rules (in priority order):
      1. Any step FAILED → mission FAILED.
      2. Any step without receipt_refs and status=succeeded → mission FAILED
         (receipt integrity violation).
      3. Any step not yet SUCCEEDED → mission RUNNING.
      4. All steps SUCCEEDED with receipts → mission SUCCEEDED.

    Returns a new dict (does not mutate input).
    """
    mission = dict(mission)  # shallow copy

    for step in steps:
        if step.get("status") == "failed":
            mission["status"] = "failed"
            return mission

    for step in steps:
        if step.get("status") == "succeeded" and not step.get("receipt_refs"):
            mission["status"] = "failed"
            return mission

    for step in steps:
        if step.get("status") != "succeeded":
            mission["status"] = "running"
            return mission

    mission["status"] = "succeeded"
    return mission
