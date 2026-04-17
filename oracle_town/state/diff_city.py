#!/usr/bin/env python3
"""
ORACLE TOWN City Diff Viewer
Compare city_prev.json and city_current.json, display only deltas.
"""

import json
import sys
from pathlib import Path

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]


def bar(progress, width=8):
    """Render progress bar."""
    p = max(0, min(8, progress))
    filled = "█" * p
    empty = "░" * (width - p)
    return filled + empty


def get_module(state, name):
    """Safely get module data."""
    return state.get("modules", {}).get(name, {})


def diff():
    """Load both states and print deltas."""
    state_dir = Path(__file__).parent
    prev_file = state_dir / "city_prev.json"
    curr_file = state_dir / "city_current.json"

    if not prev_file.exists() or not curr_file.exists():
        print(f"Error: state files not found", file=sys.stderr)
        sys.exit(1)

    with open(prev_file) as f:
        prev_state = json.load(f)
    with open(curr_file) as f:
        curr_state = json.load(f)

    prev_date = prev_state.get("date", "????-??-??")
    curr_date = curr_state.get("date", "????-??-??")
    prev_run = prev_state.get("run_id", 0)
    curr_run = curr_state.get("run_id", 0)

    print(f"DIFF: {prev_date} (run {prev_run}) → {curr_date} (run {curr_run})")
    print()

    # Top-level changes
    if prev_state.get("one_bet") != curr_state.get("one_bet"):
        print(f"- ONE_BET: {prev_state.get('one_bet', '')}")
        print(f"+ ONE_BET: {curr_state.get('one_bet', '')}")
        print()

    # Module changes
    changes = []
    for mod_name in MODULE_ORDER:
        p_mod = get_module(prev_state, mod_name)
        c_mod = get_module(curr_state, mod_name)

        p_status = p_mod.get("status", "OFF")
        c_status = c_mod.get("status", "OFF")
        p_prog = p_mod.get("progress", 0)
        c_prog = c_mod.get("progress", 0)
        p_desc = p_mod.get("desc", "")
        c_desc = c_mod.get("desc", "")

        if p_status != c_status or p_prog != c_prog or p_desc != c_desc:
            changes.append((mod_name, p_mod, c_mod))

    if changes:
        print("MODULE CHANGES:")
        for mod_name, p_mod, c_mod in changes:
            p_bar = bar(p_mod.get("progress", 0))
            c_bar = bar(c_mod.get("progress", 0))
            print(f"  - {mod_name:3} | {p_bar} | {p_mod.get('desc', '')}")
            print(f"  + {mod_name:3} | {c_bar} | {c_mod.get('desc', '')}")
        print()

    # Queue changes
    prev_queue = prev_state.get("queue", [])
    curr_queue = curr_state.get("queue", [])
    if prev_queue != curr_queue:
        print(f"QUEUE CHANGE:")
        print(f"  - {prev_queue}")
        print(f"  + {curr_queue}")
        print()

    # Anomalies
    prev_anom = prev_state.get("anomalies", [])
    curr_anom = curr_state.get("anomalies", [])
    if prev_anom != curr_anom:
        print(f"ANOMALIES CHANGE:")
        if prev_anom:
            for a in prev_anom:
                print(f"  - {a.get('type', '?')}/{a.get('severity', '?')}")
        if curr_anom:
            for a in curr_anom:
                print(f"  + {a.get('type', '?')}/{a.get('severity', '?')}")
        print()

    if not changes and prev_queue == curr_queue and prev_anom == curr_anom:
        print("(no changes)")


if __name__ == "__main__":
    diff()
