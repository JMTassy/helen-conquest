#!/usr/bin/env python3
"""
ORACLE TOWN 14-Day Growth Simulator
Progressive city growth: 1 module unlock per day (max).
Generates sim_day_XX_prev.json and sim_day_XX_current.json for days 1-14.
"""

import json
from pathlib import Path

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]
MODULE_DESC = {
    "OBS": "Observation collector",
    "INS": "Insight engine",
    "BRF": "Brief factory",
    "TRI": "Tribunal (verdict)",
    "PUB": "Publisher",
    "MEM": "Memory linker",
    "EVO": "Self-evolution",
}


def create_base_state(date, run_id, one_bet):
    """Create minimal state dict."""
    return {
        "date": date,
        "run_id": run_id,
        "mode": "DAILY",
        "one_bet": one_bet,
        "queue": [],
        "alerts": [],
        "anomalies": [],
        "modules": {
            name: {"status": "OFF", "progress": 0, "desc": ""}
            for name in MODULE_ORDER
        },
        "artifacts": [],
    }


def progress_for_day(day, module_status):
    """Compute progress 0-8 for a module on a given day."""
    if module_status == "OFF":
        return 0
    if module_status == "BLD":
        # Build phase: 2-6 progress
        return 2 + (day % 5)
    if module_status == "OK":
        # Fully operational: 8
        return 8
    if module_status == "WRN":
        return 6
    if module_status == "FLR":
        return 2
    return 0


def simulate_day(day_num):
    """
    Simulate a single day.
    Returns: (prev_state, curr_state, one_bet)
    """
    # Determine which module(s) to unlock today
    unlock_idx = min(day_num - 1, len(MODULE_ORDER) - 1)
    unlock_module = MODULE_ORDER[unlock_idx]

    # Previous day state (day-1)
    prev = create_base_state(f"2026-01-{29 + day_num - 1:02d}", 172 + day_num - 1, "")

    # Build modules for prev: all OFF except those before unlock_idx
    for i, mod_name in enumerate(MODULE_ORDER):
        if i < unlock_idx:
            # Already unlocked on previous day
            prev["modules"][mod_name]["status"] = "OK"
            prev["modules"][mod_name]["progress"] = 8
            prev["modules"][mod_name]["desc"] = f"{MODULE_DESC[mod_name]} active"
        elif i == unlock_idx:
            # Unlocking TODAY, so prev is OFF
            prev["modules"][mod_name]["status"] = "OFF"
            prev["modules"][mod_name]["progress"] = 0
            prev["modules"][mod_name]["desc"] = ""
        # else: OFF (future unlock)

    # Current day state (day)
    curr = create_base_state(f"2026-01-{29 + day_num:02d}", 173 + day_num, "")
    curr["one_bet"] = f"Day {day_num}: Unlock {unlock_module}"
    curr["queue"] = [f"Process {unlock_module}", "Analyze output"]

    # Build modules for curr: all OFF except those up to unlock_idx
    for i, mod_name in enumerate(MODULE_ORDER):
        if i < unlock_idx:
            # Already operational
            curr["modules"][mod_name]["status"] = "OK"
            curr["modules"][mod_name]["progress"] = 8
            curr["modules"][mod_name]["desc"] = f"{MODULE_DESC[mod_name]} active"
        elif i == unlock_idx:
            # Unlocking NOW
            curr["modules"][mod_name]["status"] = "BLD"
            curr["modules"][mod_name]["progress"] = 2 + (day_num % 5)
            curr["modules"][mod_name]["desc"] = f"Unlocking {MODULE_DESC[mod_name]}"
        # else: OFF (future unlock)

    # Days 8+ have smoother progression (no new unlocks)
    if day_num >= 8:
        curr["one_bet"] = f"Day {day_num}: Continuous refinement"
        for i, mod_name in enumerate(MODULE_ORDER):
            if i <= unlock_idx:
                curr["modules"][mod_name]["status"] = "OK"
                curr["modules"][mod_name]["progress"] = min(8, 4 + day_num // 2)
                curr["modules"][mod_name]["desc"] = f"{MODULE_DESC[mod_name]} evolving"

    return prev, curr


def main():
    """Generate 14 days of simulation."""
    state_dir = Path(__file__).parent

    for day in range(1, 15):
        prev_state, curr_state = simulate_day(day)

        # Write to files
        prev_file = state_dir / f"sim_day_{day:02d}_prev.json"
        curr_file = state_dir / f"sim_day_{day:02d}_current.json"

        with open(prev_file, "w") as f:
            json.dump(prev_state, f, indent=2)

        with open(curr_file, "w") as f:
            json.dump(curr_state, f, indent=2)

        print(f"Day {day:2d}: {prev_state['date']} → {curr_state['date']}")

    print(f"\nGenerated 14 days in {state_dir}")


if __name__ == "__main__":
    main()
