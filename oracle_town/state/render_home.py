#!/usr/bin/env python3
"""
ORACLE TOWN Home Page Renderer
Deterministic 70-column ASCII terminal output from city state JSON.
"""

import json
import sys
from pathlib import Path

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]
WIDTH = 70  # Hard constraint: 70 columns inner width
BORDER_LEFT = "┃"
BORDER_RIGHT = "┃"


def bar(progress, width=8):
    """
    Render progress bar: █ (filled) and ░ (empty).
    progress: 0-8 (clamped)
    Returns: exactly 'width' characters
    """
    p = max(0, min(8, progress))  # Clamp to 0-8
    filled = "█" * p
    empty = "░" * (width - p)
    return filled + empty


def fit(text, width, ellipsis="…"):
    """
    Deterministic text fitting to exact width.
    - If text fits: pad with spaces on right
    - If text too long: truncate and append ellipsis, then pad
    Always returns exactly 'width' characters.
    """
    if len(text) <= width:
        return text + " " * (width - len(text))
    # Truncate to make room for ellipsis
    truncated = text[: width - len(ellipsis)]
    return truncated + ellipsis + " " * (width - len(truncated) - len(ellipsis))


def render(state):
    """
    Render HOME page from city state dict.
    Returns list of lines (no trailing newlines).
    """
    lines = []

    # Header
    lines.append("┏" + "━" * WIDTH + "┓")

    # Title line
    date = state.get("date", "????-??-??")
    run_id = state.get("run_id", 0)
    mode = state.get("mode", "UNKNOWN")
    title_inner = f"ORACLE TOWN — HOME  {date}  MODE:{mode}  RUN:{run_id:06d}"
    lines.append(BORDER_LEFT + fit(title_inner, WIDTH) + BORDER_RIGHT)

    # Separator
    lines.append("┣" + "━" * WIDTH + "┫")

    # One Bet
    one_bet = state.get("one_bet", "")
    bet_inner = f"ONE BET : {one_bet}"
    lines.append(BORDER_LEFT + fit(bet_inner, WIDTH) + BORDER_RIGHT)

    # Queue (up to 7 items)
    queue = state.get("queue", [])
    queue_display = " | ".join(queue[:7]) if queue else "(empty)"
    queue_inner = f"QUEUE(≤7): {queue_display}"
    lines.append(BORDER_LEFT + fit(queue_inner, WIDTH) + BORDER_RIGHT)

    # Alerts and Anomalies
    alerts_count = len(state.get("alerts", []))
    anomalies_count = len(state.get("anomalies", []))
    anom_str = ""
    if anomalies_count > 0:
        first_anom = state.get("anomalies", [{}])[0]
        anom_type = first_anom.get("type", "unknown")
        anom_sev = first_anom.get("severity", "?")
        anom_str = f" ({anom_type}/{anom_sev})"
    meta_inner = f"ALERTS:{alerts_count}  ANOM:{anomalies_count}{anom_str}"
    lines.append(BORDER_LEFT + fit(meta_inner, WIDTH) + BORDER_RIGHT)

    # Separator before modules
    lines.append("┣" + "━" * WIDTH + "┫")

    # Module grid (3 columns: name, status bar, desc)
    modules = state.get("modules", {})
    for mod_name in MODULE_ORDER:
        mod = modules.get(mod_name, {})
        status = mod.get("status", "OFF")
        progress = mod.get("progress", 0)
        desc = mod.get("desc", "")

        # Format: "NAME | █████░░░ | description"
        bar_str = bar(progress, 8)
        if desc:
            mod_line = f"{mod_name} | {bar_str} | {desc}"
        else:
            mod_line = f"{mod_name} | {bar_str} | {status}"
        lines.append(BORDER_LEFT + fit(mod_line, WIDTH) + BORDER_RIGHT)

    # Footer separator
    lines.append("┣" + "━" * WIDTH + "┫")

    # Artifacts (if any)
    artifacts = state.get("artifacts", [])
    if artifacts:
        for artifact in artifacts[:3]:  # Show up to 3
            art_line = f"◆ {artifact}"
            lines.append(BORDER_LEFT + fit(art_line, WIDTH) + BORDER_RIGHT)
    else:
        empty_line = "(no artifacts)"
        lines.append(BORDER_LEFT + fit(empty_line, WIDTH) + BORDER_RIGHT)

    # Bottom border
    lines.append("┗" + "━" * WIDTH + "┛")

    return lines


def main():
    """Load city_current.json and render HOME."""
    state_dir = Path(__file__).parent
    state_file = state_dir / "city_current.json"

    if not state_file.exists():
        print(f"Error: {state_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(state_file) as f:
        state = json.load(f)

    lines = render(state)
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
