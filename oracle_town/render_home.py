#!/usr/bin/env python3
"""
ORACLE TOWN — HOME Renderer (ASCII-safe, deterministic 70-column)
Loads oracle_town/state/city_current.json and renders deterministic output.

Usage:
  python3 oracle_town/render_home.py
  python3 oracle_town/render_home.py --json oracle_town/state/city_current.json --prev oracle_town/state/city_prev.json
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]
INNER_W = 70  # strict inner width (between borders)
BAR_W = 8

STATE_DIR = Path(__file__).parent / "state"
DEFAULT_CUR = STATE_DIR / "city_current.json"
DEFAULT_PREV = STATE_DIR / "city_prev.json"


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def bar(progress: int, width: int = BAR_W) -> str:
    """Render 8-tick progress bar (ASCII-safe)."""
    p = clamp(int(progress), 0, width)
    return "█" * p + "░" * (width - p)


def pad(s: str, w: int) -> str:
    """Pad or truncate to exact width (ASCII-safe, len==display width)."""
    s = str(s).replace("\t", " ")  # tabs are width landmines
    if len(s) > w:
        return s[:w]
    return s + (" " * (w - len(s)))


def row(content: str) -> str:
    """Create bordered row with guaranteed inner width."""
    return "┃" + pad(content, INNER_W) + "┃"




def hline(kind: str = "mid") -> str:
    """Horizontal line (top/mid/bot)."""
    if kind == "top":
        return "┏" + ("━" * INNER_W) + "┓"
    if kind == "bot":
        return "┗" + ("━" * INNER_W) + "┛"
    return "┣" + ("━" * INNER_W) + "┫"


def load_json(p: Path) -> Dict[str, Any]:
    """Load JSON safely."""
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_home(state: Dict[str, Any]) -> List[str]:
    """Render HOME page from state dict."""
    date = str(state.get("date", "????-??-??"))
    run_id = int(state.get("run_id", 0))
    mode = str(state.get("mode", "DAILY")).upper()

    one_bet = str(state.get("one_bet", ""))
    queue = state.get("queue", []) or []
    alerts = state.get("alerts", []) or []
    anomalies = state.get("anomalies", []) or []
    modules = state.get("modules", {}) or {}
    artifacts = state.get("artifacts", []) or []

    lines: List[str] = []

    # Header
    lines.append(hline("top"))
    header = f"ORACLE TOWN — HOME  {date}  {mode}  RUN:{run_id:06d}"
    lines.append(row(header))
    lines.append(hline("mid"))

    # One Bet
    lines.append(row("ONE BET : " + one_bet))

    # Queue (up to 7)
    q = " | ".join([str(x) for x in queue[:7]])
    lines.append(row("QUEUE(≤7): " + q))

    # Alerts & Anomalies
    anom_short = "none"
    if anomalies:
        a0 = anomalies[0]
        code = str(a0.get("code", a0.get("type", "anom")))
        sev = str(a0.get("severity", ""))
        anom_short = f"{code}/{sev}".strip("/")
    lines.append(
        row(
            f"ALERTS: {len(alerts)}    ANOMALIES: {len(anomalies)} ({anom_short})"
        )
    )
    lines.append(hline("mid"))

    # City Map (ASCII)
    lines.append(row("CITY MAP (ASCII)"))
    lines.append(row(""))

    lines.append(row("  [OBS]──►[INS]──►[BRF]──►[TRI]──►[PUB]"))

    # Extract statuses + progress for each module
    st = {}
    pr = {}
    for m in MODULE_ORDER:
        mm = modules.get(m, {}) or {}
        st[m] = str(mm.get("status", "OFF"))[:3]
        pr[m] = int(mm.get("progress", 0))

    # Status + bar row (top pipeline)
    status_row = (
        f"  {pad(st['OBS'], 3)} {bar(pr['OBS'])}  "
        f"{pad(st['INS'], 3)} {bar(pr['INS'])}  "
        f"{pad(st['BRF'], 3)} {bar(pr['BRF'])}  "
        f"{pad(st['TRI'], 3)} {bar(pr['TRI'])}  "
        f"{pad(st['PUB'], 3)} {bar(pr['PUB'])}"
    )
    lines.append(row(status_row))
    lines.append(row(""))

    # Side modules (MEM ↔ EVO)
    lines.append(row("      [MEM]◄──────────────►[EVO]"))
    side_row = f"      {pad(st['MEM'], 3)} {bar(pr['MEM'])}   {pad(st['EVO'], 3)} {bar(pr['EVO'])}"
    lines.append(row(side_row))
    lines.append(row(""))

    # Artifacts
    lines.append(hline("mid"))
    lines.append(row("LAST ARTIFACTS (5)"))
    if artifacts:
        for i, a in enumerate(artifacts[:5], 1):
            lines.append(row(f"{i}) {a}"))
    else:
        lines.append(row("(no artifacts)"))

    lines.append(hline("bot"))

    return lines


def render_diff(cur: Dict[str, Any], prev: Optional[Dict[str, Any]]) -> List[str]:
    """Render delta between current and previous state."""
    if not prev:
        return ["DIFF: (no previous state)"]

    out: List[str] = []
    out.append(f"DIFF (since RUN {int(prev.get('run_id', 0)):06d})")
    out.append("")

    cm = cur.get("modules", {}) or {}
    pm = prev.get("modules", {}) or {}

    changed_any = False
    for m in MODULE_ORDER:
        c = cm.get(m, {}) or {}
        p = pm.get(m, {}) or {}
        cst, pst = str(c.get("status", "OFF")), str(p.get("status", "OFF"))
        cpr, ppr = int(c.get("progress", 0)), int(p.get("progress", 0))
        if (cst != pst) or (cpr != ppr):
            changed_any = True
            out.append(f"- {m}  {pst:<3}  {bar(ppr)}")
            desc = str(c.get("desc", ""))[:34]
            out.append(f"+ {m}  {cst:<3}  {bar(cpr)}  ({desc})")
            out.append("")

    # Alert/anomaly count deltas
    ca, pa = (
        len(cur.get("alerts", []) or []),
        len(prev.get("alerts", []) or []),
    )
    cn, pn = (
        len(cur.get("anomalies", []) or []),
        len(prev.get("anomalies", []) or []),
    )
    if ca != pa:
        changed_any = True
        out.append(f"- ALERTS: {pa}")
        out.append(f"+ ALERTS: {ca}")
        out.append("")
    if cn != pn:
        changed_any = True
        out.append(f"- ANOMALIES: {pn}")
        out.append(f"+ ANOMALIES: {cn}")

    if not changed_any:
        out.append("(no changes)")

    return out


def assert_width(lines: List[str]) -> None:
    """Enforce that all framed lines are exactly 72 chars (hard invariant)."""
    bad = [(k, len(x), x) for k, x in enumerate(lines) if len(x) != 72]
    if bad:
        k, n, x = bad[0]
        raise AssertionError(
            f"WIDTH_INVARIANT_BROKEN: line {k} has {n} chars "
            f"(expected 72): {x!r}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(DEFAULT_CUR))
    ap.add_argument("--prev", default=str(DEFAULT_PREV))
    args = ap.parse_args()

    cur_path = Path(args.json)
    prev_path = Path(args.prev)

    if not cur_path.exists():
        print(f"Error: {cur_path} not found", file=__import__("sys").stderr)
        __import__("sys").exit(1)

    cur = load_json(cur_path)
    prev = load_json(prev_path) if prev_path.exists() else None

    # Render HOME
    home_lines = render_home(cur)
    assert_width(home_lines)
    for ln in home_lines:
        print(ln)

    # Render DIFF (no width constraint; it's unframed)
    print()
    for ln in render_diff(cur, prev):
        print(ln)


if __name__ == "__main__":
    main()
