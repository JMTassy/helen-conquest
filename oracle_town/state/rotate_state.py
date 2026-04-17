#!/usr/bin/env python3
"""
ORACLE TOWN State Rotation
Move city_current.json → city_prev.json before writing new current state.
"""

import json
import shutil
from pathlib import Path

STATE_DIR = Path(__file__).parent
PREV_FILE = STATE_DIR / "city_prev.json"
CURR_FILE = STATE_DIR / "city_current.json"


def rotate():
    """Rotate: current → prev. Returns prev state (for linking)."""
    if CURR_FILE.exists():
        # Backup: current → prev
        shutil.copy(CURR_FILE, PREV_FILE)
        prev_state = json.loads(CURR_FILE.read_text())
        print(f"✓ Rotated state: {CURR_FILE.name} → {PREV_FILE.name}")
        return prev_state
    else:
        # No current state yet (first run)
        if PREV_FILE.exists():
            return json.loads(PREV_FILE.read_text())
        else:
            print("! No state files found (fresh start)")
            return None


if __name__ == "__main__":
    prev = rotate()
    if prev:
        print(f"  Previous run: {prev.get('run_id')}, date: {prev.get('date')}")
