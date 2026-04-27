"""Desire firewall: AI may not propose effects naming forbidden desires."""
from __future__ import annotations

from typing import Any


class DesireLeakage(Exception):
    pass


def scan_payload(payload: Any, desires: list[str]) -> None:
    needles = [d.lower() for d in desires]

    def _visit(v: Any) -> None:
        if isinstance(v, str):
            low = v.lower()
            for d in needles:
                if d in low:
                    raise DesireLeakage(f"forbidden_desire:{d}")
        elif isinstance(v, dict):
            for x in v.values():
                _visit(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                _visit(x)

    _visit(payload)
