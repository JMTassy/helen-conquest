"""REPLAY_PROOF_V1 — Deterministic membrane proof.

Proves:
1. Same packet + same state → same decision bytes
2. Same decision → same state hash
3. Replay across runs produces zero drift
"""
from __future__ import annotations

import json
from pathlib import Path

from helen_os.governance.canonical import sha256_prefixed
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision


def load_json(path: str) -> dict:
    """Load JSON file or fail loudly."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


def replay_packet(packet: dict, state: dict, runs: int = 10) -> dict:
    """
    Replay the same packet through the reducer multiple times.

    Proves: same input → same decision → same state hash (zero drift)

    Args:
        packet: SKILL_PROMOTION_PACKET_V1
        state: SKILL_LIBRARY_STATE_V1
        runs: number of replay iterations

    Returns:
        {
          "packet_id": str,
          "runs": int,
          "decision_hashes": [str],
          "state_hashes": [str],
          "all_identical": bool,
          "drift_detected": bool,
        }
    """
    decision_hashes = []
    state_hashes = []

    for i in range(runs):
        # Run reducer
        result = reduce_promotion_packet(packet, state)

        # Serialize decision
        decision_obj = {
            "decision": result.decision,
            "reason_code": result.reason_code,
        }
        decision_hash = sha256_prefixed(decision_obj)
        decision_hashes.append(decision_hash)

        # Apply (if admitted)
        if result.decision == "ADMITTED":
            decision_full = {
                "schema_name": "SKILL_PROMOTION_DECISION_V1",
                "schema_version": "1.0.0",
                "decision_id": f"replay_{i}",
                "skill_id": packet["skill_id"],
                "candidate_version": packet["candidate_version"],
                "decision": result.decision,
                "reason_code": result.reason_code,
            }
            new_state = apply_skill_promotion_decision(state, decision_full)
            state_hash = sha256_prefixed(new_state)
            state_hashes.append(state_hash)

    # Check for drift
    first_decision = decision_hashes[0] if decision_hashes else None
    all_decisions_identical = all(h == first_decision for h in decision_hashes)

    first_state = state_hashes[0] if state_hashes else None
    all_states_identical = all(h == first_state for h in state_hashes)

    return {
        "packet_id": packet.get("packet_id", "unknown"),
        "runs": runs,
        "decision_hashes": decision_hashes,
        "state_hashes": state_hashes,
        "all_decisions_identical": all_decisions_identical,
        "all_states_identical": all_states_identical,
        "drift_detected": not (all_decisions_identical and all_states_identical),
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="replay_proof_v1",
        description="HELEN OS Determinism Proof",
    )
    parser.add_argument("--packet", required=True, help="Packet JSON file")
    parser.add_argument("--state", required=True, help="State JSON file")
    parser.add_argument(
        "--runs", type=int, default=10, help="Number of replay iterations"
    )

    args = parser.parse_args()

    # Load
    packet = load_json(args.packet)
    state = load_json(args.state)

    # Replay
    result = replay_packet(packet, state, runs=args.runs)

    # Report
    print("\n" + "=" * 70)
    print("REPLAY_PROOF_V1 — Determinism Verification")
    print("=" * 70)
    print(f"\nPacket ID:              {result['packet_id']}")
    print(f"Runs:                   {result['runs']}")
    print(f"\nDecisions identical:    {result['all_decisions_identical']}")
    print(f"States identical:       {result['all_states_identical']}")
    print(f"Drift detected:         {result['drift_detected']}")

    if result["drift_detected"]:
        print("\n❌ DRIFT DETECTED — Membrane is NOT deterministic")
        print(f"Decision hashes: {result['decision_hashes']}")
        print(f"State hashes:    {result['state_hashes']}")
        return 1
    else:
        print("\n✅ NO DRIFT — Membrane is perfectly deterministic")
        print(f"Canonical hash (decision): {result['decision_hashes'][0]}")
        if result["state_hashes"]:
            print(f"Canonical hash (state):    {result['state_hashes'][0]}")
        return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
