"""Kernel state — derived purely from the event log by the reducer."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from helen_os.ledger.hash_chain import GENESIS_HASH, canonical_json, sha256_hex


@dataclass
class State:
    session_id: Optional[str] = None
    cognition_active: bool = False
    last_event_hash: str = GENESIS_HASH
    proposed_count: int = 0
    authorized_count: int = 0
    denied_count: int = 0
    executed_count: int = 0
    failed_count: int = 0
    events_seen: int = 0
    terminated: bool = False
    last_verdict: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def state_hash(state: State) -> str:
    return sha256_hex(canonical_json(state.to_dict()))
