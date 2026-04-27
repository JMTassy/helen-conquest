"""Pure reducer: events → State.

Reads only events. Never reads wall-clock, filesystem (beyond loading the
event list once at the boundary), or invokes tools. Same input → same output.
"""
from __future__ import annotations

from helen_os.authority.language_firewall import scan_payload as scan_authority_payload
from helen_os.kernel.state import State
from helen_os.ledger.hash_chain import (
    ChainBreak,
    GENESIS_HASH,
    compute_event_hash,
)


class PolicyViolation(Exception):
    pass


def fold(events: list[dict], forbidden_tokens: list[str] | None = None) -> State:
    state = State()
    prev = GENESIS_HASH
    tokens = forbidden_tokens or []

    for i, e in enumerate(events):
        if e.get("prev_event_hash") != prev:
            raise ChainBreak(
                f"chain break at index {i}: expected prev={prev[:8]}, got {str(e.get('prev_event_hash',''))[:8]}"
            )
        recomputed = compute_event_hash(e)
        if recomputed != e.get("event_hash"):
            raise ChainBreak(
                f"event_hash mismatch at index {i}: stored={str(e.get('event_hash',''))[:8]}, computed={recomputed[:8]}"
            )

        actor_kind = e.get("actor", {}).get("kind")
        if actor_kind == "AI" and tokens:
            scan_authority_payload(e.get("payload", {}), tokens)

        et = e["event_type"]

        if et in ("EFFECT_AUTHORIZED", "EFFECT_DENIED") and actor_kind != "SYSTEM":
            raise PolicyViolation(
                f"event {i} ({et}) must be authored by SYSTEM, got actor.kind={actor_kind}"
            )
        if et == "EFFECT_PROPOSED" and actor_kind not in ("AI", "OPERATOR"):
            raise PolicyViolation(
                f"event {i} (EFFECT_PROPOSED) must be authored by AI or OPERATOR, got {actor_kind}"
            )
        if et in ("EFFECT_EXECUTED", "EFFECT_FAILED") and actor_kind != "RUNTIME":
            raise PolicyViolation(
                f"event {i} ({et}) must be authored by RUNTIME, got {actor_kind}"
            )

        if et == "COGNITION_STARTED":
            state.cognition_active = True
            state.session_id = e["session_id"]
            state.terminated = False
            state.last_verdict = None
        elif et == "COGNITION_TERMINATED":
            state.cognition_active = False
            state.terminated = True
            state.last_verdict = e.get("payload", {}).get("verdict")
        elif et == "EFFECT_PROPOSED":
            state.proposed_count += 1
        elif et == "EFFECT_AUTHORIZED":
            state.authorized_count += 1
        elif et == "EFFECT_DENIED":
            state.denied_count += 1
        elif et == "EFFECT_EXECUTED":
            state.executed_count += 1
        elif et == "EFFECT_FAILED":
            state.failed_count += 1

        state.events_seen += 1
        state.last_event_hash = e["event_hash"]
        prev = e["event_hash"]

    return state
