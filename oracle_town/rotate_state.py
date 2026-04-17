#!/usr/bin/env python3
"""
ORACLE TOWN — State Rotator
Move city_current.json → city_prev.json (before each run).
Preserves history for diff comparison.

Usage:
  python3 oracle_town/rotate_state.py
"""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

STATE_DIR = Path(__file__).parent / "state"
CUR = STATE_DIR / "city_current.json"
PREV = STATE_DIR / "city_prev.json"


def main() -> None:
    if not CUR.exists():
        print("! No city_current.json to rotate", file=sys.stderr)
        return

    try:
        shutil.copy2(CUR, PREV)
        print(f"✓ Rotated: {CUR.name} → {PREV.name}")
    except Exception as e:
        print(f"Error rotating state: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
