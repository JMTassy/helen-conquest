#!/usr/bin/env python3
"""
ORACLE TOWN — Diff-only comparator
Show delta between city_current.json and city_prev.json (minimal, git-friendly output).

Usage:
  python3 oracle_town/diff_city.py
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]
BAR_W = 8

STATE_DIR = Path(__file__).parent / "state"
CUR = STATE_DIR / "city_current.json"
PREV = STATE_DIR / "city_prev.json"


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def bar(progress: int, width: int = BAR_W) -> str:
    """Render progress bar."""
    p = clamp(int(progress), 0, width)
    return "█" * p + "░" * (width - p)


def load(p: Path) -> Dict[str, Any]:
    """Load JSON state file."""
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def diff(cur: Dict[str, Any], prev: Optional[Dict[str, Any]]) -> List[str]:
    """Generate delta-only diff (minimal output)."""
    if not prev:
        return ["DIFF: (no previous state)"]

    out: List[str] = []
    out.append(
        f"DIFF: {prev.get('date', '?')} (run {int(prev.get('run_id', 0)):06d}) "
        f"→ {cur.get('date', '?')} (run {int(cur.get('run_id', 0)):06d})"
    )
    out.append("")

    cm = cur.get("modules", {}) or {}
    pm = prev.get("modules", {}) or {}

    changed = False
    for m in MODULE_ORDER:
        c = cm.get(m, {}) or {}
        p = pm.get(m, {}) or {}
        cst, pst = str(c.get("status", "OFF")), str(p.get("status", "OFF"))
        cpr, ppr = int(c.get("progress", 0)), int(p.get("progress", 0))

        if (cst != pst) or (cpr != ppr):
            changed = True
            out.append(f"- {m}  {pst:<3}  {bar(ppr)}")
            desc = str(c.get("desc", ""))[:40]
            out.append(f"+ {m}  {cst:<3}  {bar(cpr)}  ({desc})")
            out.append("")

    ca, pa = (
        len(cur.get("alerts", []) or []),
        len(prev.get("alerts", []) or []),
    )
    cn, pn = (
        len(cur.get("anomalies", []) or []),
        len(prev.get("anomalies", []) or []),
    )
    if ca != pa:
        changed = True
        out.append(f"- ALERTS: {pa}")
        out.append(f"+ ALERTS: {ca}")
        out.append("")
    if cn != pn:
        changed = True
        out.append(f"- ANOMALIES: {pn}")
        out.append(f"+ ANOMALIES: {cn}")
        out.append("")

    if not changed:
        out.append("(no changes)")

    return out


def main() -> None:
    if not CUR.exists():
        print(f"Error: {CUR} not found", file=sys.stderr)
        sys.exit(1)

    cur = load(CUR)
    prev = load(PREV) if PREV.exists() else None

    print("\n".join(diff(cur, prev)))


if __name__ == "__main__":
    main()
