#!/usr/bin/env python3
"""
iso_coaster_renderer.py

Pure HTML/SVG renderer for Oracle Town iso-coaster visualization.

Reads frozen config (iso_coaster_config.py) and CityState to produce
an ISO-perspective visualization of the jurisdiction.

CONSTITUTIONAL GUARANTEES:
- Deterministic (K5): identical CityState → identical HTML
- Pure: no I/O, no time, no randomness during rendering
- Config-driven: all visual rules from frozen iso_coaster_config.py
- Honest: no inference, no speculation, no animation
- Diff-friendly: canonical HTML output

This module enforces VISUAL_DISCIPLINE_CHARTER rules:
  ✓ No speculative animations
  ✓ No progress bars
  ✓ No "attempted" states
  ✓ No predictions
  ✓ No auto-expansion
  ✓ No gamification
  ✓ No reinterpretation of silence
  ✓ No helpful inferences
"""

from typing import Dict, List, Tuple
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# Inline Config (for self-contained rendering)
# ─────────────────────────────────────────────────────────────────────
# These are copies from iso_coaster_config.py for deterministic rendering

MODULE_ARCHETYPES = {
    "OBS": {
        "name": "Observatory",
        "role": "Observation & Ingestion",
        "symbol": "⌖",
        "description": "Receives signals from external world",
        "position": (0, 0),
    },
    "INSIGHT": {
        "name": "Library",
        "role": "Pattern Analysis",
        "symbol": "📚",
        "description": "Analyzes and detects patterns",
        "position": (0, 1),
    },
    "MEMORY": {
        "name": "Vault",
        "role": "Historical Data",
        "symbol": "🔐",
        "description": "Stores all historical verdicts",
        "position": (-1, 2),
    },
    "BRIEF": {
        "name": "Scriptorium",
        "role": "Synthesis",
        "symbol": "✍",
        "description": "Synthesizes briefs and claims",
        "position": (0, 2),
    },
    "TRI": {
        "name": "Courthouse",
        "role": "Verification & Authority",
        "symbol": "⚖",
        "description": "Immutable verification gates (K-gates)",
        "position": (0, 3),
        "immutable": True,
    },
    "PUBLISH": {
        "name": "Gate",
        "role": "Ledger Commit",
        "symbol": "🚪",
        "description": "Publishes verdicts to ledger",
        "position": (1, 2),
    },
}

STATUS_COLORS = {
    "OK": "#10b981",      # Green
    "OFF": "#6b7280",     # Gray
    "FAIL": "#ef4444",    # Red
}

STATUS_BRIGHTNESS = {
    "OK": 1.0,
    "OFF": 0.4,
    "FAIL": 0.8,
}


# ─────────────────────────────────────────────────────────────────────
# ISO Perspective Calculation
# ─────────────────────────────────────────────────────────────────────

def iso_project(x: int, y: int) -> Tuple[float, float]:
    """
    Project grid coordinates to ISO perspective (2D canvas).

    ISO formula (30-degree isometric):
    - screen_x = (x - y) * cos(30°)
    - screen_y = (x + y) * sin(30°)
    """
    iso_x = (x - y) * 0.866  # cos(30°) ≈ 0.866
    iso_y = (x + y) * 0.5    # sin(30°) = 0.5
    return (iso_x, iso_y)


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

def render_iso_coaster(city_state: Dict) -> str:
    """
    Render a CityState dict into an ISO-coaster HTML visualization.

    Parameters
    ----------
    city_state : dict
        Authoritative CityState object (from city_state_renderer).

    Returns
    -------
    str
        Canonical HTML with embedded SVG visualization (deterministic).

    K5 Guarantee
    ────────────
    Same CityState dict → byte-identical HTML output, every time.
    """

    # Get module states
    modules = city_state.get("modules", {})

    # Calculate SVG bounds (with padding)
    coords = []
    for module_name, archetype in MODULE_ARCHETYPES.items():
        pos = archetype.get("position", (0, 0))
        iso_pos = iso_project(pos[0], pos[1])
        coords.append(iso_pos)

    # Find bounds
    if coords:
        min_x = min(c[0] for c in coords) - 60
        max_x = max(c[0] for c in coords) + 60
        min_y = min(c[1] for c in coords) - 60
        max_y = max(c[1] for c in coords) + 60
    else:
        min_x = min_y = -100
        max_x = max_y = 100

    width = max_x - min_x
    height = max_y - min_y

    # Build SVG
    svg_elements = []

    # Background
    svg_elements.append(f'<rect width="{width}" height="{height}" fill="#0f172a"/>')

    # Grid lines (light, subtle)
    for i in range(-2, 3):
        for j in range(-2, 3):
            x1, y1 = iso_project(i, j)
            x2, y2 = iso_project(i + 1, j)
            x1 -= min_x
            y1 -= min_y
            x2 -= min_x
            y2 -= min_y
            svg_elements.append(
                f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                f'stroke="#334155" stroke-width="0.5" opacity="0.3"/>'
            )

    # Render modules (buildings)
    module_order = ["OBS", "INSIGHT", "MEMORY", "BRIEF", "TRI", "PUBLISH"]
    for module_name in module_order:
        if module_name not in MODULE_ARCHETYPES:
            continue

        archetype = MODULE_ARCHETYPES[module_name]
        status = _get_module_status(modules, module_name)

        # ISO position
        pos = archetype.get("position", (0, 0))
        iso_x, iso_y = iso_project(pos[0], pos[1])
        screen_x = iso_x - min_x
        screen_y = iso_y - min_y

        # Render building
        svg_elements.extend(_render_building(
            module_name,
            archetype,
            status,
            screen_x,
            screen_y,
        ))

    svg_content = "\n    ".join(svg_elements)

    # Build complete HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oracle Town — Iso-Coaster</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }}
        .header {{
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background: #1e293b;
            border-radius: 4px;
            border-left: 3px solid #3b82f6;
        }}
        .stat {{
            display: flex;
            flex-direction: column;
        }}
        .stat-label {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #e2e8f0;
        }}
        .container {{
            border: 1px solid #334155;
            border-radius: 4px;
            overflow: hidden;
            background: #0f172a;
        }}
        svg {{
            display: block;
            width: 100%;
            height: auto;
        }}
        .tooltip {{
            display: none;
            position: absolute;
            background: #1e293b;
            border: 1px solid #334155;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 100;
        }}
        .disclaimer {{
            margin-top: 20px;
            padding: 15px;
            background: #1e293b;
            border-left: 3px solid #f59e0b;
            color: #94a3b8;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Oracle Town — Iso-Coaster</h1>
        <p>Jurisdiction state visualization (read-only, non-authoritative)</p>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="stat-label">Policy Version</div>
            <div class="stat-value">{_safe_str(city_state.get("policy", {}).get("version"))}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Verdicts (Accept)</div>
            <div class="stat-value">{_safe_int(city_state.get("verdicts", {}).get("accepted"))}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Verdicts (Reject)</div>
            <div class="stat-value">{_safe_int(city_state.get("verdicts", {}).get("rejected"))}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Snapshot Date</div>
            <div class="stat-value">{_safe_str(city_state.get("date"))}</div>
        </div>
    </div>

    <div class="container">
        <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            {svg_content}
        </svg>
    </div>

    <div class="disclaimer">
        <strong>⚠️ Disclaimer:</strong> This visualization shows jurisdiction state
        at a point in time. It is NOT authoritative. The true state is in the ledger.
        This rendering is for visibility only and does not affect governance decisions.
    </div>
</body>
</html>"""

    return html


# ─────────────────────────────────────────────────────────────────────
# Rendering Helpers (pure functions)
# ─────────────────────────────────────────────────────────────────────

def _render_building(
    module_name: str,
    archetype: Dict,
    status: str,
    x: float,
    y: float,
) -> List[str]:
    """Render a single building (module) in ISO perspective."""

    color = STATUS_COLORS.get(status, STATUS_COLORS["OFF"])
    brightness = STATUS_BRIGHTNESS.get(status, 0.5)

    # Adjust color brightness
    color_rgb = _hex_to_rgb(color)
    adjusted_rgb = tuple(int(c * brightness) for c in color_rgb)
    adjusted_color = _rgb_to_hex(adjusted_rgb)

    # Building dimensions (ISO diamond)
    size = 30

    # Diamond shape (ISO building)
    points = [
        (x, y - size),           # Top
        (x + size, y),           # Right
        (x, y + size),           # Bottom
        (x - size, y),           # Left
    ]

    elements = []

    # Diamond (building outline)
    points_str = " ".join(f"{px:.0f},{py:.0f}" for px, py in points)
    elements.append(
        f'<polygon points="{points_str}" fill="{adjusted_color}" '
        f'stroke="#334155" stroke-width="1.5" opacity="{brightness}"/>'
    )

    # Module label (centered at building)
    elements.append(
        f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" dy=".3em" '
        f'font-size="11" font-weight="bold" fill="#e2e8f0" '
        f'pointer-events="none">{module_name}</text>'
    )

    # Status indicator (small circle at top)
    indicator_color = STATUS_COLORS[status]
    elements.append(
        f'<circle cx="{x:.0f}" cy="{y - size - 8:.0f}" r="4" '
        f'fill="{indicator_color}" opacity="{brightness}"/>'
    )

    # Immutable marker (for TRI)
    if archetype.get("immutable"):
        elements.append(
            f'<text x="{x:.0f}" y="{y + size + 15:.0f}" text-anchor="middle" '
            f'font-size="10" fill="#fbbf24" pointer-events="none">'
            f'IMMUTABLE</text>'
        )

    return elements


def _get_module_status(modules: Dict, name: str) -> str:
    """Get status of a module (OK, OFF, FAIL)."""
    entry = modules.get(name)
    if not isinstance(entry, dict):
        return "OFF"
    status = entry.get("status")
    if status not in {"OK", "OFF", "FAIL"}:
        return "OFF"
    return status


def _safe_str(value) -> str:
    """Safe string conversion (no inference)."""
    if isinstance(value, str) and value.strip():
        return value[:50]  # Truncate long values
    return "∅"


def _safe_int(value) -> int:
    """Safe integer conversion."""
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# ─────────────────────────────────────────────────────────────────────
# Self-Test (for CI)
# ─────────────────────────────────────────────────────────────────────

def _self_test_determinism():
    """K5 determinism self-test: same input → identical output."""
    test_state = {
        "date": "2026-01-31",
        "run_id": "test-iso",
        "policy": {"version": "v7", "hash": "sha256:test"},
        "verdicts": {"accepted": 5, "rejected": 10},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "FAIL"},
        },
    }

    # Run 5 times, verify identical
    outputs = []
    for i in range(5):
        output = render_iso_coaster(test_state)
        outputs.append(output)

    # All should be identical
    for i in range(1, 5):
        if outputs[i] != outputs[0]:
            print(f"❌ K5 DETERMINISM FAILED at iteration {i}")
            return False

    print("✅ K5 Determinism verified (5 identical iterations)")
    return True


if __name__ == "__main__":
    import sys

    # Test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = _self_test_determinism()
        sys.exit(0 if success else 1)

    # Demo mode
    sample = {
        "date": "2026-01-31",
        "run_id": "demo",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 1, "rejected": 5},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "FAIL"},
        },
    }

    html = render_iso_coaster(sample)
    print(html)
