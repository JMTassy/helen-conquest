"""HELEN OS Interactive Dialog Box.

Non-sovereign conversational interface over the constitutional kernel.
No authority claimed. Governance remains in reducer + state updater.
"""
from __future__ import annotations

import json
from pathlib import Path

from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision


def _load_state_file(path: str) -> dict:
    """Load state from JSON file or create empty."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {
            "schema_name": "SKILL_LIBRARY_STATE_V1",
            "schema_version": "1.0.0",
            "law_surface_version": "v1",
            "active_skills": {},
        }


def _save_state_file(path: str, state: dict) -> None:
    """Save state to JSON file."""
    Path(path).write_text(json.dumps(state, indent=2))


def run_dialog(state_file: str = "helen_state.json"):
    """Interactive dialog box for HELEN OS kernel."""
    print("\n" + "=" * 60)
    print("HELEN OS — Constitutional Governance Kernel")
    print("=" * 60)
    print("Non-sovereign dialog. Authority remains in reducer.")
    print("Type 'exit' to quit, 'state' to show current state.\n")

    state = _load_state_file(state_file)

    while True:
        try:
            user_input = input("you > ").strip()

            if user_input.lower() in {"exit", "quit", "bye"}:
                print("helen > session closed")
                break

            if user_input.lower() == "state":
                print("helen >", json.dumps(state, indent=2))
                continue

            if user_input.lower() == "help":
                print(
                    "helen > Commands:\n"
                    "         'state' — show current active state\n"
                    "         'exit' — close session\n"
                    "         JSON packet — run through reducer\n"
                )
                continue

            # Parse as JSON packet
            try:
                packet = json.loads(user_input)
            except json.JSONDecodeError:
                print("helen > Error: Invalid JSON. Use 'help' for commands.")
                continue

            # Run through membrane
            result = reduce_promotion_packet(packet, state)

            # Show decision
            print(
                f"helen > Decision: {result.decision} "
                f"({result.reason_code})"
            )

            # If admitted, apply to state
            if result.decision == "ADMITTED":
                # Create decision object
                decision = {
                    "schema_name": "SKILL_PROMOTION_DECISION_V1",
                    "schema_version": "1.0.0",
                    "decision_id": f"dialog_{packet.get('packet_id', 'unknown')}",
                    "skill_id": packet["skill_id"],
                    "candidate_version": packet["candidate_version"],
                    "decision": "ADMITTED",
                    "reason_code": result.reason_code,
                }

                # Apply to state
                new_state = apply_skill_promotion_decision(state, decision)
                state = new_state

                # Show state change
                active = state.get("active_skills", {})
                print(f"helen > State: {packet['skill_id']} → {packet['candidate_version']}")
                print(f"         ({len(active)} active skills)")

                # Save
                _save_state_file(state_file, state)
                print(f"helen > Saved to {state_file}")
            else:
                print(f"helen > Reason: {result.explanation or result.reason_code}")

        except KeyboardInterrupt:
            print("\nhelen > session interrupted")
            break
        except Exception as e:
            print(f"helen > Error: {e}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="helen",
        description="HELEN OS Constitutional Governance Kernel",
    )
    parser.add_argument(
        "--state",
        default="helen_state.json",
        help="State file (default: helen_state.json)",
    )

    args = parser.parse_args()
    run_dialog(state_file=args.state)


if __name__ == "__main__":
    main()
