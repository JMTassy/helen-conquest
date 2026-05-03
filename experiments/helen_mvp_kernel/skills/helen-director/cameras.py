"""12-angle camera library — typed, ordered, immutable.

Sourced from operator-supplied HELEN-MV-CAMERA-ANGLE-SHEET.
Indices are stable: position k always refers to the same camera angle,
across all runs and all projects, so the receipt's camera assignments
are bit-stable for replay.
"""

from typing import Dict, List

CAMERA_LIBRARY: List[Dict[str, str]] = [
    {"index": 1, "name": "extreme_close_up",      "lens": "85-100mm macro", "motion": "static",      "use": "activation, intimacy"},
    {"index": 2, "name": "close_up",              "lens": "50-85mm",        "motion": "slow_zoom_in", "use": "authority, empathy"},
    {"index": 3, "name": "medium_close_up",       "lens": "50mm",           "motion": "static",      "use": "dialogue, confession, command"},
    {"index": 4, "name": "medium_shot",           "lens": "35-50mm",        "motion": "slight_dolly", "use": "ritual gestures, interface control"},
    {"index": 5, "name": "low_angle",             "lens": "28-35mm",        "motion": "tilt_up",     "use": "sovereignty, dominance, mythic rise"},
    {"index": 6, "name": "high_angle",            "lens": "35-50mm",        "motion": "tilt_down",   "use": "vulnerability, observation"},
    {"index": 7, "name": "side_profile",          "lens": "85mm",           "motion": "static",      "use": "concentration, listening, piloting"},
    {"index": 8, "name": "back_view",             "lens": "24-35mm",        "motion": "slow_push_in", "use": "reveal scale, cathedral interface"},
    {"index": 9, "name": "over_the_shoulder",     "lens": "35-50mm",        "motion": "static",      "use": "computer use, witness mode, proof screen"},
    {"index": 10, "name": "mirror_shot",          "lens": "50mm",           "motion": "static",      "use": "duality, oracle self-dialogue, identity split"},
    {"index": 11, "name": "wide_hero",            "lens": "24mm",           "motion": "slow_orbit",  "use": "worldbuilding, temple-metaverse, title shot"},
    {"index": 12, "name": "insert_hands_on_iface", "lens": "50-85mm macro", "motion": "static",      "use": "tactile control, system piloting, ledger confirm"},
]


def select_camera_for_shot(shot_index: int) -> Dict[str, str]:
    """Deterministic per-shot camera selection. Index is 1-based to match shot_id."""
    if shot_index < 1:
        raise ValueError(f"shot_index must be >= 1, got {shot_index}")
    return CAMERA_LIBRARY[(shot_index - 1) % len(CAMERA_LIBRARY)]
