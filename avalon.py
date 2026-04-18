#!/usr/bin/env python3

import json
import sys
from datetime import datetime

STATE_FILE = "state.json"

# ---------- Core Mechanics ----------

def entropy_tick(state):
    """Automatic entropy increase each day"""
    state["entropy"] += 0.3

def hunger_tick(state):
    """Automatic hunger increase each day"""
    state["hunger"] += 1
    if state["hunger"] >= 4:
        state["stability"] -= 1

def apply_action(state, action):
    """Apply sealed action and log entry"""
    if action == "research":
        state["knowledge_efficiency"] += 0.2
        state["ledger"].append(entry("RESEARCH_INITIATED"))
    elif action == "expand":
        state["territory"] += 1
        state["entropy"] += 0.5
        state["ledger"].append(entry("TERRITORY_EXPANDED"))
    elif action == "stabilize":
        state["stability"] += 1
        state["hunger"] -= 1  # Stabilize reduces hunger
        state["ledger"].append(entry("STABILITY_REINFORCED"))
    elif action == "none":
        state["ledger"].append(entry("NO_ACTION"))
    else:
        print("Invalid action. Use: research, expand, stabilize, or none")
        sys.exit(1)

def entry(label):
    """Create single ledger entry"""
    return {
        "day": state["day"] + 1,
        "timestamp": datetime.utcnow().isoformat(),
        "label": label
    }

# ---------- Display ----------

def display_state(state):
    """Show current castle state"""
    print("\n" + "="*50)
    print(f"AVALON — DAY {state['day']}")
    print("="*50)
    print(f"Territory:           {state['territory']}")
    print(f"Stability:           {state['stability']}")
    print(f"Entropy:             {round(state['entropy'], 2)}")
    print(f"Knowledge Efficiency: {round(state['knowledge_efficiency'], 2)}")
    print(f"Hunger:              {state['hunger']}")
    print(f"Ledger Entries:      {len(state['ledger'])}")
    print("="*50 + "\n")

def display_ledger(state):
    """Show recent ledger entries"""
    if state["ledger"]:
        print("LEDGER (last 3 entries):")
        for entry in state["ledger"][-3:]:
            print(f"  Day {entry['day']}: {entry['label']}")
    print()

# ---------- Main Execution ----------

def main():
    global state

    # Load current state
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    # Advance day
    state["day"] += 1

    # Apply automatic ticks
    entropy_tick(state)
    hunger_tick(state)

    # Get action from command line
    if len(sys.argv) != 2:
        print("Usage: python avalon.py [research|expand|stabilize|none]")
        sys.exit(1)

    action = sys.argv[1]
    apply_action(state, action)

    # Save state
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    # Display result
    display_state(state)
    display_ledger(state)
    print(f"✓ Action sealed: {action.upper()}")

if __name__ == "__main__":
    main()
