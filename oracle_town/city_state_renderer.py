#!/usr/bin/env python3
"""
city_state_renderer.py

Pure, deterministic renderer for Oracle Town CityState snapshots.

CONSTITUTIONAL GUARANTEES:
- Deterministic (K5): identical CityState → identical output
- Pure: no I/O, no global state, no time, no randomness
- Honest: absence of data is rendered explicitly
- Diff-friendly: fixed layout, fixed ordering, canonical text

This module performs NO interpretation.
It renders ONLY what is present in CityState.
"""

from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────
# Canonical constants (frozen)
# ─────────────────────────────────────────────────────────────────────

MODULE_ORDER = ["OBS", "INSIGHT", "MEMORY", "BRIEF", "TRI", "PUBLISH"]

STATUS_GLYPHS = {
    "OK": "████▉",
    "OFF": "░░░░░",
    "FAIL": "█████",  # visually heavy on purpose
}

STATUS_LABELS = {"OK", "OFF", "FAIL"}


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

def render_city_state(city_state: Dict) -> str:
    """
    Render a CityState dict into a canonical ASCII snapshot.

    Parameters
    ----------
    city_state : dict
        Authoritative CityState object (already produced by TRI / Mayor).

    Returns
    -------
    str
        Canonical ASCII rendering (diffable, deterministic).

    K5 Guarantee
    ────────────
    Same CityState dict → byte-identical output, every time.
    No time, no randomness, no I/O, no global state.
    """

    lines: List[str] = []

    # Header
    lines.extend(_render_header(city_state))
    lines.append(_hr())

    # Verdict summary
    lines.extend(_render_verdicts(city_state))
    lines.append(_hr())

    # City layout
    lines.extend(_render_city_layout(city_state))
    lines.append(_hr())

    # Insights
    lines.extend(_render_insights(city_state))
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Rendering helpers (pure functions)
# ─────────────────────────────────────────────────────────────────────

def _render_header(city_state: Dict) -> List[str]:
    """Render title and policy information."""
    date = _get_str(city_state, "date")
    run_id = _get_str(city_state, "run_id")

    policy = city_state.get("policy", {})
    policy_version = _get_str(policy, "version")
    policy_hash = _get_str(policy, "hash")

    # Truncate hash for display
    hash_short = policy_hash[:20] if policy_hash != "∅" else "∅"

    return [
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
        f"┃ ORACLE TOWN — {date:<10} RUN {run_id:<13} ┃",
        "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
        f"┃ Policy: {policy_version:<2} ({hash_short}…)",
    ]


def _render_verdicts(city_state: Dict) -> List[str]:
    """Render verdict counts."""
    verdicts = city_state.get("verdicts", {})
    accepted = _get_int(verdicts, "accepted")
    rejected = _get_int(verdicts, "rejected")

    return [
        f"┃ Verdicts: ACCEPT {accepted} | REJECT {rejected:<2}",
    ]


def _render_city_layout(city_state: Dict) -> List[str]:
    """Render the city layout with module states."""
    modules = city_state.get("modules", {})

    def m(name: str) -> str:
        """Format a single module display."""
        status = _get_module_status(modules, name)
        glyph = _glyph(status)
        return f"[{name}] {status:<4} {glyph}"

    return [
        "┃ CITY STATE",
        "┃",
        f"┃        {m('OBS')}",
        "┃         │",
        f"┃      {m('INSIGHT')}",
        "┃         │",
        f"┃ {m('MEMORY')}─┼─{m('BRIEF')}──{m('PUBLISH')}",
        "┃         │",
        f"┃        {m('TRI')} (IMMUTABLE)",
    ]


def _render_insights(city_state: Dict) -> List[str]:
    """Render top insights."""
    insights = city_state.get("top_insights")

    lines = ["┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫", "┃ TOP INSIGHTS"]

    if not insights:
        lines.append("┃ • (none)")
        lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
        return lines

    for item in insights:
        item_str = str(item)
        # Truncate if too long
        if len(item_str) > 40:
            item_str = item_str[:37] + "…"
        lines.append(f"┃ • {item_str}")

    lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    return lines


# ─────────────────────────────────────────────────────────────────────
# Canonical utilities (no inference, no coercion)
# ─────────────────────────────────────────────────────────────────────

def _glyph(status: str) -> str:
    """Get visual representation of status."""
    return STATUS_GLYPHS.get(status, "?????")


def _get_module_status(modules: Dict, name: str) -> str:
    """
    Get status of a module.

    Returns 'OK', 'OFF', or 'FAIL'.
    Invalid states → 'OFF' (honest default).
    """
    entry = modules.get(name)
    if not isinstance(entry, dict):
        return "OFF"
    status = entry.get("status")
    if status not in STATUS_LABELS:
        return "OFF"
    return status


def _get_str(d: Dict, key: str) -> str:
    """
    Get string from dict.

    Returns value if present and non-empty.
    Returns '∅' (empty set symbol) if missing or empty.
    This makes absence explicit and visible.
    """
    v = d.get(key)
    if isinstance(v, str) and v.strip():
        return v
    return "∅"


def _get_int(d: Dict, key: str) -> int:
    """
    Get integer from dict.

    Returns value if present and non-negative.
    Returns 0 (honest default) if missing or invalid.
    """
    v = d.get(key)
    if isinstance(v, int) and v >= 0:
        return v
    return 0


def _hr() -> str:
    """Horizontal rule (fixed width)."""
    return "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫"


# ─────────────────────────────────────────────────────────────────────
# Self-test (optional, for CI/verification)
# ─────────────────────────────────────────────────────────────────────

def _self_test_determinism():
    """K5 determinism self-test: same input → identical output."""
    test_state = {
        "date": "2026-01-31",
        "run_id": "daily-01",
        "policy": {"version": "v7", "hash": "sha256:abc123def456"},
        "verdicts": {"accepted": 1, "rejected": 6},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "OFF"},
        },
        "top_insights": ["P1 blocked temporal selector", "P0 blocked missing evidence"],
    }

    # Run 10 times, verify identical
    outputs = []
    for i in range(10):
        output = render_city_state(test_state)
        outputs.append(output)

    # All should be identical
    for i in range(1, 10):
        if outputs[i] != outputs[0]:
            print(f"❌ K5 DETERMINISM FAILED at iteration {i}")
            print(f"Iteration 0:\n{outputs[0]}")
            print(f"\nIteration {i}:\n{outputs[i]}")
            return False

    print("✅ K5 Determinism verified (10 identical iterations)")
    return True


if __name__ == "__main__":
    import sys

    # Test mode: run determinism verification
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = _self_test_determinism()
        sys.exit(0 if success else 1)

    # Demo mode: render sample state
    sample = {
        "date": "2026-01-31",
        "run_id": "daily-01",
        "policy": {"version": "v7", "hash": "sha256:abc123def456"},
        "verdicts": {"accepted": 1, "rejected": 6},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "OFF"},
        },
        "top_insights": ["P1 blocked temporal selector", "P0 blocked missing evidence"],
    }

    print(render_city_state(sample))
