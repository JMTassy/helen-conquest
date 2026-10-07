"""Shared fixture builders. Pure functions, deterministic, no I/O."""
from __future__ import annotations

import copy
from typing import Any


def make_discrimination(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema": "DISCRIMINATION_V0",
        "distinction_id": "D-e58-goldset-window",
        "h_plus": "The E48 safety threshold of 0.003 is sufficient for goldset expansion.",
        "h_minus": "The window width after re-centering falls below 0.003 and expansion must wait.",
        "x_star": "Recompute window width with w_refs re-centred on the current goldset.",
        "e_plus": [{"ref": "temple/autoresearch/outbox/AR-initrank-e48.json", "note": "threshold origin"}],
        "e_minus": [{"ref": "temple/autoresearch/outbox/AR-initrank-e58-prescreen-formula.json", "note": "width=0.0015"}],
        "witness": {"kind": "replay", "requirement": "Deterministic re-run of the width computation on the pinned goldset."},
        "status": "OPEN",
        "scope": "autoresearch/init_ranking",
        "provenance": {"producer": "W1", "source_refs": ["AR-initrank-e58-prescreen-formula.json"]},
        "authority": False,
    }
    out = copy.deepcopy(base)
    for key, value in overrides.items():
        if value is _DELETE:
            out.pop(key, None)
        else:
            out[key] = value
    return out


class _Delete:
    pass


_DELETE = _Delete()
DELETE = _DELETE
