from __future__ import annotations
from typing import Any
from .write_gate import append_event, WriteGateResult

def append_trace_event(payload: dict[str, Any]) -> WriteGateResult:
    return append_event(channel="trace", payload=payload)
