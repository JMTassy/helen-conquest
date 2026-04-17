#!/usr/bin/env python3
"""
ORACLE TOWN — 14-Day Growth Simulator
Progressive unlock: at most 1 new module per day.
Output: oracle_town/state/sim_day_XX_{prev,current}.json

Usage:
  python3 oracle_town/simulate_14_days.py
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Dict, Any

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]

STATE_DIR = Path(__file__).parent / "state"


def write_json(p: Path, obj: Dict[str, Any]) -> None:
    """Write JSON with trailing newline."""
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def make_state(date: str, run_id: int) -> Dict[str, Any]:
    """Create minimal state dict."""
    return {
        "date": date,
        "run_id": run_id,
        "mode": "SIM",
        "one_bet": "Simulated growth",
        "queue": [],
        "alerts": [],
        "anomalies": [],
        "modules": {m: {"status": "OFF", "progress": 0, "desc": ""} for m in MODULE_ORDER},
        "artifacts": [],
    }


def advance_module(state: Dict[str, Any], mod: str, day: int) -> None:
    """Advance one module through lifecycle (OFF → BLD → OK)."""
    m = state["modules"][mod]
    if m["status"] == "OFF":
        m["status"] = "BLD"
        m["progress"] = 2
        m["desc"] = f"enabled day {day}"
    elif m["status"] == "BLD":
        m["status"] = "OK"
        m["progress"] = 8
        m["desc"] = f"stabilized day {day}"
    # else: OK (steady)


def main() -> None:
    # Bootstrap: Day 0
    prev = make_state("2026-01-29", 1000)
    prev["modules"]["OBS"]["status"] = "BLD"
    prev["modules"]["OBS"]["progress"] = 4
    prev["modules"]["OBS"]["desc"] = "bootstrap"

    # Simulate 14 days
    for day in range(1, 15):
        date = f"2026-02-{day:02d}"
        cur = json.loads(json.dumps(prev))  # deep copy via JSON roundtrip
        cur["date"] = date
        cur["run_id"] = prev["run_id"] + 1

        # Unlock exactly one module per day (1st 7 days unlock, then stabilize)
        target_idx = min(day - 1, len(MODULE_ORDER) - 1)
        target_mod = MODULE_ORDER[target_idx]
        advance_module(cur, target_mod, day)

        # Earlier modules auto-stabilize (optional, for realistic growth)
        for i, m in enumerate(MODULE_ORDER):
            if i < target_idx:
                mm = cur["modules"][m]
                if mm["status"] == "BLD":
                    mm["status"] = "OK"
                    mm["progress"] = 8
                    mm["desc"] = f"stabilized day {day}"

        # Write state pair
        write_json(STATE_DIR / f"sim_day_{day:02d}_prev.json", prev)
        write_json(STATE_DIR / f"sim_day_{day:02d}_current.json", cur)

        prev = cur

    print(f"✓ Generated 14 days of simulation in {STATE_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
