from __future__ import annotations
from typing import Any
from .write_gate import append_event, WriteGateResult

def append_town_event(payload: dict[str, Any]) -> WriteGateResult:
    return append_event(channel="town", payload=payload)
