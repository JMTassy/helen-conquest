"""
ORACLE scoring (Mayor evaluation in %)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from receipt.compute_gap import compute_receipt_gap


def compute_progress_percent(tribunal_bundle: Dict[str, Any], attestations_ledger: Dict[str, Any], policies: Dict[str, Any]) -> int:
    """
    Progress % is a governance metric for emulator only:
      base = 1 - gap / hard_count
      penalty if kill_switches fail
    Clamped to [0, 100].
    """
    hard_count = 0
    for o in tribunal_bundle.get("required_obligations", []):
        if isinstance(o, dict) and o.get("severity") == "HARD":
            hard_count += 1

    gap, _missing = compute_receipt_gap(tribunal_bundle, attestations_ledger)
    denom = max(hard_count, 1)

    base = 1.0 - (gap / denom)
    if not bool(policies.get("kill_switches_pass", False)):
        base -= 0.35

    if base < 0.0:
        base = 0.0
    if base > 1.0:
        base = 1.0

    return int(round(100 * base))


def delta_percent(before: int, after: int) -> int:
    return int(after - before)
