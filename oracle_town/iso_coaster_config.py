#!/usr/bin/env python3
"""
iso_coaster_config.py

Frozen tileset and building mappings for iso-coaster visualization.

This file defines:
1. Module → building archetype mapping (what each jurisdiction looks like)
2. Status → visual state rules (OK, OFF, FAIL)
3. Canonical ISO perspective rules

NO LOGIC. Pure configuration (data only).
"""

from typing import Dict


# ─────────────────────────────────────────────────────────────────────
# MODULE → BUILDING ARCHETYPES (frozen)
# ─────────────────────────────────────────────────────────────────────
#
# Each module is represented as an ISO building type.
# This mapping is IMMUTABLE and intentional.
#

MODULE_ARCHETYPES = {
    "OBS": {
        "name": "Observatory",
        "role": "Observation & Ingestion",
        "symbol": "⌖",  # Compass rose
        "description": "Receives signals from external world",
        "position": (0, 0),  # Reference point
    },
    "INSIGHT": {
        "name": "Library",
        "role": "Pattern Analysis",
        "symbol": "📚",  # Books
        "description": "Analyzes and detects patterns",
        "position": (0, 1),
    },
    "MEMORY": {
        "name": "Vault",
        "role": "Historical Data",
        "symbol": "🔐",  # Lock
        "description": "Stores all historical verdicts",
        "position": (-1, 2),
    },
    "BRIEF": {
        "name": "Scriptorium",
        "role": "Synthesis",
        "symbol": "✍",  # Writing hand
        "description": "Synthesizes briefs and claims",
        "position": (0, 2),
    },
    "TRI": {
        "name": "Courthouse",
        "role": "Verification & Authority",
        "symbol": "⚖",  # Scales of justice
        "description": "Immutable verification gates (K-gates)",
        "position": (0, 3),
        "immutable": True,  # Constitutional marker
    },
    "PUBLISH": {
        "name": "Gate",
        "role": "Ledger Commit",
        "symbol": "🚪",  # Door/Gate
        "description": "Publishes verdicts to ledger",
        "position": (1, 2),
    },
}


# ─────────────────────────────────────────────────────────────────────
# STATUS → VISUAL STATE RULES (frozen)
# ─────────────────────────────────────────────────────────────────────
#
# How each status should appear in iso-coaster visualization.
#

STATUS_VISUALS = {
    "OK": {
        "color": "green",      # Lit, operational
        "brightness": 1.0,     # Fully visible
        "glyph": "✓",          # Checkmark
        "description": "Building is operational",
    },
    "OFF": {
        "color": "gray",       # Unlit, inactive
        "brightness": 0.4,     # Dimmed
        "glyph": "○",          # Circle (empty)
        "description": "Building is inactive",
    },
    "FAIL": {
        "color": "red",        # Error, blocked
        "brightness": 0.8,     # Visible warning
        "glyph": "✗",          # X mark
        "description": "Building is sealed/blocked (error state)",
    },
}


# ─────────────────────────────────────────────────────────────────────
# CANONICAL ISO PERSPECTIVE RULES (frozen)
# ─────────────────────────────────────────────────────────────────────
#
# How the town is projected onto 2D space.
# These rules are immutable.
#

ISO_PERSPECTIVE = {
    "tile_width": 32,          # ISO diamond width
    "tile_height": 16,         # ISO diamond height
    "x_offset": 0.866,         # cos(30°) for proper ISO aspect
    "y_offset": 0.5,           # sin(30°)
    "viewpoint": "north-west",  # Camera angle (locked)
}


# ─────────────────────────────────────────────────────────────────────
# NETWORK TOPOLOGY (frozen)
# ─────────────────────────────────────────────────────────────────────
#
# How modules connect to each other (deterministic data flow).
# These links are NEVER to be reinterpreted.
#

NETWORK_TOPOLOGY = {
    "OBS": ["INSIGHT"],          # Observations → Insights
    "INSIGHT": ["MEMORY", "BRIEF"],  # Insights → Memory + Synthesis
    "MEMORY": ["TRI"],           # Memory contributes to TRI
    "BRIEF": ["TRI"],            # Synthesis contributes to TRI
    "TRI": ["PUBLISH"],          # TRI verdict → Publication
    "PUBLISH": [],               # Publish terminal (ledger)
}


# ─────────────────────────────────────────────────────────────────────
# VISUAL DISCIPLINE RULES (constitutional)
# ─────────────────────────────────────────────────────────────────────
#
# WHAT NEVER HAPPENS IN iso-coaster VISUALIZATION:
# These are written down to prevent future weakening.
#

VISUAL_DISCIPLINE_RULES = [
    "❌ No speculative animations (buildings don't 'build' mid-run)",
    "❌ No progress bars tied to REJECT (failure is not progress)",
    "❌ No 'attempted' states (only OK, OFF, or FAIL)",
    "❌ No predictions (only what has been decided)",
    "❌ No auto-expansion of details (show structure only)",
    "❌ No gamification (no points, badges, celebrations)",
    "❌ No reinterpretation of silence (REFUSE renders as OFF)",
    "❌ No 'helpful' inferences (absence is not a signal)",
]


# ─────────────────────────────────────────────────────────────────────
# AUXILIARY FUNCTIONS (pure configuration getters)
# ─────────────────────────────────────────────────────────────────────

def get_module_archetype(module_name: str) -> Dict:
    """Get architectural definition for a module."""
    return MODULE_ARCHETYPES.get(module_name, {})


def get_status_visual(status: str) -> Dict:
    """Get visual properties for a status."""
    return STATUS_VISUALS.get(status, STATUS_VISUALS.get("OFF"))


def get_network_links(module_name: str) -> list:
    """Get downstream modules from a module."""
    return NETWORK_TOPOLOGY.get(module_name, [])


def is_module_immutable(module_name: str) -> bool:
    """Check if a module is marked as immutable (constitutional)."""
    archetype = get_module_archetype(module_name)
    return archetype.get("immutable", False)


# ─────────────────────────────────────────────────────────────────────
# SELF-TEST (for CI)
# ─────────────────────────────────────────────────────────────────────

def self_test():
    """Verify configuration integrity."""
    errors = []

    # Check all modules in TOPOLOGY exist in ARCHETYPES
    all_modules = set(MODULE_ARCHETYPES.keys())
    topology_modules = set(NETWORK_TOPOLOGY.keys())

    for module in topology_modules:
        if module not in all_modules:
            errors.append(f"Module {module} in TOPOLOGY but not ARCHETYPES")

    # Check all statuses are defined
    valid_statuses = set(STATUS_VISUALS.keys())
    if not valid_statuses:
        errors.append("No statuses defined")

    # Check each archetype has required fields
    for name, arch in MODULE_ARCHETYPES.items():
        required = {"name", "role", "symbol", "description"}
        missing = required - set(arch.keys())
        if missing:
            errors.append(f"Module {name} missing fields: {missing}")

    if errors:
        print("❌ Configuration integrity check FAILED:")
        for error in errors:
            print(f"  • {error}")
        return False

    print("✅ Configuration integrity verified")
    return True


if __name__ == "__main__":
    import sys

    if not self_test():
        sys.exit(1)

    print("\nConfiguration loaded:")
    print(f"  Modules: {len(MODULE_ARCHETYPES)}")
    print(f"  Statuses: {len(STATUS_VISUALS)}")
    print(f"  Network links: {sum(len(v) for v in NETWORK_TOPOLOGY.values())}")
    print(f"  Discipline rules: {len(VISUAL_DISCIPLINE_RULES)}")
    sys.exit(0)
