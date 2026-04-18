from __future__ import annotations
from typing import Any

def finalize_mission(mission: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Deterministic. No ambiguity, no LLM judgment.

    Fails if:  any step failed OR any step missing receipt_refs
    Running if: any step not yet succeeded
    Succeeds if: all steps succeeded and all have receipt_refs
    """
    if any(s["status"] == "failed" for s in steps):
        mission["status"] = "failed"
        return mission

    if any(s["status"] != "succeeded" for s in steps):
        mission["status"] = "running"
        return mission

    if any(not s.get("receipt_refs") for s in steps):
        mission["status"] = "failed"
        return mission

    mission["status"] = "succeeded"
    return mission

def apply_step_result(
    step: dict[str, Any],
    *,
    status: str,
    output_refs: list[str],
    receipt_refs: list[str],
    last_error: str | None = None,
) -> dict[str, Any]:
    step["status"] = status
    step["output_refs"] = list(output_refs)
    step["receipt_refs"] = list(receipt_refs)
    step["last_error"] = last_error
    return step
