"""Ledger replay — reconstruct governed history from append-only entries.

Law: Only append-only reducer decisions may be replayed into governed historical state.

Single responsibility:
- Replay all ledger entries in order
- Reconstruct governed state deterministically
- Return final state reached by incremental decision application
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision


def replay_ledger_to_state(
    ledger: Mapping[str, Any],
    initial_state: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Reconstruct governed state by replaying ledger entries in order.

    Law: Only append-only reducer decisions may be replayed into governed state.

    Input: ledger (append-only decision entries), initial_state (starting state)
    Output: final_state (reconstructed by applying all decisions in order)

    Determinism: same ledger + same initial_state → same final_state
    """
    # Validate ledger schema
    if not isinstance(ledger, dict):
        return initial_state

    if ledger.get("schema_name") != "DECISION_LEDGER_V1":
        return initial_state

    # Start with initial state
    current_state = dict(initial_state)

    # Replay entries in order
    entries = ledger.get("entries", [])
    for i, entry in enumerate(entries):
        # Validate entry structure
        if not isinstance(entry, dict):
            # Invalid entry: fail closed
            return initial_state

        if entry.get("schema_name") is not None:
            # Entry should not have schema_name at top level (decision is nested)
            continue

        # Extract decision
        decision = entry.get("decision")
        if decision is None:
            # Missing decision: skip
            continue

        # Validate decision schema
        if decision.get("schema_name") != "SKILL_PROMOTION_DECISION_V1":
            # Non-decision entry: skip
            continue

        # Verify entry index matches position
        if entry.get("entry_index") != i:
            # Index mismatch: fail closed (indicates corruption)
            return initial_state

        # Apply decision to current state
        new_state = apply_skill_promotion_decision(current_state, decision)

        # Only update if decision was ADMITTED or ROLLED_BACK (only these change state)
        dt = decision.get("decision_type")
        if dt in ("ADMITTED", "ROLLED_BACK"):
            current_state = new_state
        # Non-ADMITTED/ROLLED_BACK decisions don't mutate state (as expected from updater)

    return current_state
