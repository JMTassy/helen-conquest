#!/usr/bin/env python3
"""
ORACLE TOWN Home Page Renderer — Enhanced with Symbols & Glyphs
Deterministic 70-column ASCII+Unicode output with optional emoji support.

Modes:
  --ascii   : ASCII-safe (no emoji, ✓▲!✗· badges + ASCII symbols)
  --unicode : Unicode-enhanced (emoji in dedicated column, wcwidth-safe)
"""

import json
import sys
from pathlib import Path

try:
    from wcwidth import wcswidth
    HAS_WCWIDTH = True
except ImportError:
    HAS_WCWIDTH = False
    # Fallback: assume emoji = 2 cols, ASCII = 1 col
    def wcswidth(text):
        width = 0
        for ch in text:
            if ord(ch) > 127:
                width += 2
            else:
                width += 1
        return width

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]
WIDTH = 70

# Glyph layer definitions
ROLE_ICONS = {
    "OBS": ("👁", "O"),   # (unicode, ascii fallback)
    "INS": ("🧠", "B"),
    "BRF": ("📝", "B"),
    "TRI": ("⚖", "T"),
    "PUB": ("📣", "P"),
    "MEM": ("🗃", "M"),
    "EVO": ("🧬", "E"),
}

STATUS_BADGES = {
    "OK": ("✓", "✓"),
    "BLD": ("▲", "^"),
    "WRN": ("!", "!"),
    "FLR": ("✗", "x"),
    "OFF": ("·", "-"),
}

GRAVITY_SYMBOLS = {
    "alert": ("⚠", "A"),
    "anomaly": ("🕳", "o"),
    "blocked": ("⛔", "#"),
}

SIGILS = "⟐∿ ⊕ ∴ ⧉"  # Ritual symbols


def get_symbol(key, mode="unicode"):
    """Get symbol (unicode or ascii fallback)."""
    if mode == "ascii":
        # Extract fallback (2nd element of tuple)
        if key in ROLE_ICONS:
            return ROLE_ICONS[key][1]
        if key in STATUS_BADGES:
            return STATUS_BADGES[key][1]
        if key in GRAVITY_SYMBOLS:
            return GRAVITY_SYMBOLS[key][1]
    else:
        # Unicode
        if key in ROLE_ICONS:
            return ROLE_ICONS[key][0]
        if key in STATUS_BADGES:
            return STATUS_BADGES[key][0]
        if key in GRAVITY_SYMBOLS:
            return GRAVITY_SYMBOLS[key][0]
    return "?"


def display_len(text):
    """Get display width (accounts for emoji = 2 cols)."""
    if HAS_WCWIDTH:
        return wcswidth(text) if wcswidth(text) > 0 else len(text)
    else:
        width = 0
        for ch in text:
            if ord(ch) > 127:
                width += 2
            else:
                width += 1
        return width


def fit(text, width, ellipsis="…"):
    """
    Fit text to exact display width.
    - If fits: pad right
    - If too long: truncate + ellipsis + pad
    """
    dlen = display_len(text)
    if dlen <= width:
        return text + " " * (width - dlen)

    # Truncate to fit ellipsis
    result = ""
    remaining = width - display_len(ellipsis)
    for ch in text:
        if display_len(result + ch) <= remaining:
            result += ch
        else:
            break
    result += ellipsis
    pad = width - display_len(result)
    return result + " " * pad


def bar(progress, width=8):
    """Render progress bar (ASCII safe)."""
    p = max(0, min(8, progress))
    filled = "█" * p
    empty = "░" * (width - p)
    return filled + empty


def render(state, mode="unicode"):
    """
    Render HOME page with enhanced symbolism.
    mode: "ascii" or "unicode"
    """
    lines = []
    border_l = "┃"
    border_r = "┃"

    # === HEADER ===
    lines.append("┏" + "━" * WIDTH + "┓")

    date = state.get("date", "????-??-??")
    run_id = state.get("run_id", 0)
    mode_str = state.get("mode", "UNKNOWN")
    title_inner = f"ORACLE TOWN — HOME  {date}  {mode_str}  {run_id:06d}"
    lines.append(border_l + fit(title_inner, WIDTH) + border_r)

    lines.append("┣" + "━" * WIDTH + "┫")

    # === ONE BET ===
    one_bet = state.get("one_bet", "")
    bet_inner = f"ONE BET : {one_bet}"
    lines.append(border_l + fit(bet_inner, WIDTH) + border_r)

    # === QUEUE ===
    queue = state.get("queue", [])
    queue_display = " | ".join(queue[:7]) if queue else "(empty)"
    queue_inner = f"QUEUE(≤7): {queue_display}"
    lines.append(border_l + fit(queue_inner, WIDTH) + border_r)

    # === ALERTS & ANOMALIES (with symbols) ===
    alerts_count = len(state.get("alerts", []))
    anomalies = state.get("anomalies", [])
    anomalies_count = len(anomalies)

    alert_sym = get_symbol("alert", mode)
    anom_sym = get_symbol("anomaly", mode)

    anom_detail = ""
    if anomalies_count > 0:
        first_anom = anomalies[0]
        anom_type = first_anom.get("type", "unknown")
        anom_sev = first_anom.get("severity", "?")
        anom_detail = f" ({anom_type}/{anom_sev})"

    meta_inner = f"{alert_sym}:{alerts_count}  {anom_sym}:{anomalies_count}{anom_detail}"
    lines.append(border_l + fit(meta_inner, WIDTH) + border_r)

    # === SIGILS (ritual identity) ===
    sigil_inner = f"⸻ SIGILS: {SIGILS}"
    lines.append(border_l + fit(sigil_inner, WIDTH) + border_r)

    lines.append("┣" + "━" * WIDTH + "┫")

    # === MODULE TABLE ===
    modules = state.get("modules", {})

    # Header row (fixed layout)
    header = "MOD │ ST │ PROG     │ NOTES"
    if mode == "unicode":
        header = "MOD │ ◆ │ ST │ PROG     │ NOTES"
    lines.append(border_l + fit(header, WIDTH) + border_r)
    lines.append("┣" + "━" * WIDTH + "┫")

    for mod_name in MODULE_ORDER:
        mod = modules.get(mod_name, {})
        status = mod.get("status", "OFF")
        progress = mod.get("progress", 0)
        desc = mod.get("desc", "")

        status_badge = get_symbol(status, mode)
        bar_str = bar(progress, 8)

        # Build module line
        if mode == "unicode":
            icon = get_symbol(mod_name, mode)
            mod_line = f"{mod_name} │ {icon} │ {status_badge} │ {bar_str} │ {desc}"
        else:
            mod_line = f"{mod_name} │ {status_badge} │ {bar_str} │ {desc}"

        lines.append(border_l + fit(mod_line, WIDTH) + border_r)

    lines.append("┣" + "━" * WIDTH + "┫")

    # === ARTIFACTS ===
    artifacts = state.get("artifacts", [])
    if artifacts:
        for artifact in artifacts[:2]:
            art_line = f"◆ {artifact}"
            lines.append(border_l + fit(art_line, WIDTH) + border_r)
    else:
        empty_line = "(no artifacts)"
        lines.append(border_l + fit(empty_line, WIDTH) + border_r)

    lines.append("┗" + "━" * WIDTH + "┛")

    return lines


def main():
    """Load state and render with mode from args."""
    mode = "unicode"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--ascii":
            mode = "ascii"
        elif sys.argv[1] == "--unicode":
            mode = "unicode"

    state_dir = Path(__file__).parent
    state_file = state_dir / "city_current.json"

    if not state_file.exists():
        print(f"Error: {state_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(state_file) as f:
        state = json.load(f)

    lines = render(state, mode=mode)
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
