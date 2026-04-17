"""Autonomous research step — deterministic decision cycle.

Law: Autonomous exploration is allowed; only reducer-emitted, ledger-bound
     decisions may alter governed state.

Single responsibility:
- Execute task (envelope)
- Type failure if any (failure_report)
- Build promotion packet from failure (if typed)
- Reduce promotion through membrane (decision)
- Apply decision to state (next_state)
- Return complete cycle result (deterministic)

No autonomy of sovereignty. All state changes flow through reducer.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from helen_os.executor.helen_executor_v1 import execute_skill
from helen_os.evolution.failure_bridge import route_failure
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision
from helen_os.state.decision_ledger_v1 import append_decision_to_ledger


def _build_promotion_packet_from_failure(
    failure_report: Mapping[str, Any],
    task: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Minimal promotion packet builder from typed failure.

    Future: can become sophisticated skill evolution engine.
    For now: simple proposal to retry or upgrade failed skill.
    """
    skill_id = task.get("skill_id", "skill.unknown")
    current_version = task.get("current_version", "0.1.0")

    # Simple version bump
    version_parts = current_version.split(".")
    try:
        patch = int(version_parts[2]) + 1
        new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
    except (ValueError, IndexError):
        new_version = "1.0.0"

    # Minimal promotion packet
    return {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": f"autoresearch_{failure_report.get('failure_report_id', 'unknown')}",
        "skill_id": skill_id,
        "candidate_version": new_version,
        "lineage": {
            "parent_skill_id": skill_id,
            "parent_version": current_version,
            "proposal_sha256": "sha256:" + "0" * 64,  # Placeholder
        },
        "capability_manifest_sha256": "sha256:" + "1" * 64,  # Placeholder
        "doctrine_surface": {
            "law_surface_version": "v1",
            "transfer_required": False,
        },
        "evaluation": {
            "threshold_name": "recovery",
            "threshold_value": 0.0,
            "observed_value": 1.0,  # Assume failure recovery
            "passed": True,
        },
        "receipts": [],  # No receipts for autoresearch proposal (will fail, which is correct)
    }


def autoresearch_step(
    task: Mapping[str, Any],
    state: Mapping[str, Any],
    ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    One deterministic autonomy step.

    Input: task (work request), state (current governed state),
           ledger (optional decision journal)
    Output: complete cycle with envelope, optional failure, optional promotion,
            decision, updated state, updated ledger

    Determinism: same task + same state → same output
    """
    # Step 1: Execute task
    execution_envelope = execute_skill(task)

    failure_report = None
    promotion_packet = None
    decision = None
    next_state = dict(state)  # Copy for safety

    # Step 2-5: If task failed, try to propose improvement
    if execution_envelope.get("exit_code", 0) != 0:
        # Step 2: Type the failure
        failure_report = route_failure(
            {
                "schema_name": "FAILURE_REPORT_V1",
                "schema_version": "1.0.0",
                "failure_report_id": execution_envelope.get("task_id", "unknown"),
                "failure_class": "EXECUTION_FAILED",
                "reason_code": "ERR_TASK_FAILED",
                "typed_failure": {
                    "exit_code": execution_envelope.get("exit_code"),
                    "message": execution_envelope.get("stderr", ""),
                },
            }
        )

        # Step 3: If failure is typed, build proposal
        if failure_report is not None:
            promotion_packet = _build_promotion_packet_from_failure(
                failure_report, task
            )

            # Step 4: Run through reducer
            reducer_result = reduce_promotion_packet(promotion_packet, state)

            # Build decision object — schema requires "decision_type", not "decision"
            decision = {
                "schema_name": "SKILL_PROMOTION_DECISION_V1",
                "schema_version": "1.0.0",
                "decision_id": f"autoresearch_{promotion_packet['packet_id']}",
                "skill_id": promotion_packet["skill_id"],
                "candidate_version": promotion_packet["candidate_version"],
                "decision_type": reducer_result.decision,   # ADMITTED | REJECTED | QUARANTINED
                "reason_code": reducer_result.reason_code,
            }

            # Step 5: If ADMITTED, update state
            if reducer_result.decision == "ADMITTED":
                next_state = apply_skill_promotion_decision(state, decision)

    # Step 6: Append decision to ledger if present and ADMITTED
    next_ledger = ledger
    if ledger is not None and decision is not None:
        if decision.get("decision_type") == "ADMITTED":   # was: .get("decision")
            next_ledger = append_decision_to_ledger(ledger, decision)

    # Step 7: Return complete cycle
    return {
        "execution_envelope": execution_envelope,
        "failure_report": failure_report,
        "promotion_packet": promotion_packet,
        "decision": decision,
        "next_state": next_state,
        "next_ledger": next_ledger,
    }
