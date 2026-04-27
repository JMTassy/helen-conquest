"""Deterministic replay: load events, fold, return state and state_hash."""
from __future__ import annotations

from pathlib import Path

from helen_os.kernel.reducer import fold
from helen_os.kernel.state import State, state_hash
from helen_os.ledger.event_log import read_events


def replay_from_path(
    ledger_path: str | Path,
    forbidden_tokens: list[str] | None = None,
) -> tuple[State, str]:
    events = read_events(ledger_path)
    state = fold(events, forbidden_tokens=forbidden_tokens)
    return state, state_hash(state)
