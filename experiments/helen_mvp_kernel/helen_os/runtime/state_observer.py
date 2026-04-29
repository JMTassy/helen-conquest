"""State Observer — continuous projection of ledger state.

Reads the existing append-only ledger. Runs fold() to compute the current
State. Yields snapshots as new events arrive.

No new state engine. No new reducer. No schema mutation. No kernel mutation.
Kernel is source of truth. Surface subscribes.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Generator

from helen_os.kernel.reducer import fold
from helen_os.kernel.state import state_hash
from helen_os.ledger.event_log import read_events


def current_snapshot(ledger_path: Path) -> dict:
    """Compute the current state projection from the full ledger."""
    events = read_events(ledger_path)
    if not events:
        return {
            "state_hash": None,
            "last_receipt": None,
            "event_count": 0,
            "last_event_type": None,
            "terminated": False,
            "cognition_active": False,
        }
    state = fold(events)
    last_event = events[-1]
    return {
        "state_hash": state_hash(state),
        "last_receipt": last_event.get("event_hash"),
        "event_count": state.events_seen,
        "last_event_type": last_event.get("event_type"),
        "terminated": state.terminated,
        "cognition_active": state.cognition_active,
    }


def tail(
    ledger_path: Path,
    poll_interval: float = 0.1,
) -> Generator[dict, None, None]:
    """Continuously yield state snapshots whenever the ledger grows.

    Yields the initial snapshot immediately, then one snapshot per
    new event appended to the ledger. Never mutates state.
    """
    ledger_path = Path(ledger_path)
    last_count = 0

    while True:
        events = read_events(ledger_path)
        count = len(events)
        if count != last_count:
            last_count = count
            if events:
                state = fold(events)
                last_event = events[-1]
                yield {
                    "state_hash": state_hash(state),
                    "last_receipt": last_event.get("event_hash"),
                    "event_count": state.events_seen,
                    "last_event_type": last_event.get("event_type"),
                    "terminated": state.terminated,
                    "cognition_active": state.cognition_active,
                }
        time.sleep(poll_interval)
