"""TEMPLE_V1: Transparent Exploration via Membrane-Permissioned Learning Enhancements.

Pure generative exploration layer. Assembles typed artifacts with no authority.
Non-sovereign. Non-mutating. Non-authoritative.

Single responsibility:
- Build a TEMPLE_EXPLORATION_V1 artifact from input threads, frictions, tensions, sketches, exports
- Return it with authority="NONE"
- No reducer, no ledger, no state, no replay, no mayor path

Law:
- TEMPLE est libre en expression et nul en autorité.
- Toute sortie TEMPLE doit être transmutée par la membrane avant de compter institutionnellement.
- Seule une décision autorisée par le reducer peut muter l'état gouverné.
"""
from __future__ import annotations

from typing import Any


def run_temple_exploration(
    *,
    session_id: str,
    theme: str,
    her_threads: list[dict],
    hal_frictions: list[dict],
    tension_map: list[dict],
    center_sketches: list[dict],
    export_candidates: list[dict],
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Assemble a TEMPLE_EXPLORATION_V1 artifact.

    Args:
        session_id: Unique identifier for this exploration session
        theme: Thematic focus or research question
        her_threads: List of HER generative threads
        hal_frictions: List of HAL structural critiques
        tension_map: List of structural tensions
        center_sketches: List of core sketches/metaphors
        export_candidates: List of export candidates
        notes: Optional session notes

    Returns:
        dict with schema_name="TEMPLE_EXPLORATION_V1", authority="NONE"

    Invariants:
    - authority is always "NONE"
    - No state mutations
    - No ledger appends
    - No reducer calls
    """
    exploration = {
        "schema_name": "TEMPLE_EXPLORATION_V1",
        "schema_version": "1.0.0",
        "session_id": session_id,
        "theme": theme,
        "her_threads": her_threads,
        "hal_frictions": hal_frictions,
        "tension_map": tension_map,
        "center_sketches": center_sketches,
        "export_candidates": export_candidates,
        "authority": "NONE",
    }

    if notes:
        exploration["notes"] = notes

    return exploration
