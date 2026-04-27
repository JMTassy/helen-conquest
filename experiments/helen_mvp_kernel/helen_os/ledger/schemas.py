"""Event envelope schema and constructors."""
from __future__ import annotations

import uuid
from typing import Any

from helen_os.ledger.hash_chain import compute_event_hash

EVENT_TYPES = frozenset({
    "COGNITION_STARTED",
    "COGNITION_TERMINATED",
    "EFFECT_PROPOSED",
    "EFFECT_AUTHORIZED",
    "EFFECT_DENIED",
    "EFFECT_EXECUTED",
    "EFFECT_FAILED",
    "MEMORY_READ",
    "MEMORY_WRITE_PROPOSED",
    "MEMORY_WRITE_ADMITTED",
    "DECAY_APPLIED",
    "OPERATOR_DECISION",
})

ACTOR_KINDS = frozenset({"AI", "OPERATOR", "SYSTEM", "RUNTIME"})


class SchemaViolation(Exception):
    pass


def make_actor(kind: str, actor_id: str, policy_hash: str) -> dict:
    if kind not in ACTOR_KINDS:
        raise SchemaViolation(f"unknown actor kind: {kind}")
    return {"kind": kind, "id": actor_id, "policy_hash": policy_hash}


def make_envelope(
    *,
    event_type: str,
    session_id: str,
    timestamp: str,
    actor: dict,
    payload: dict,
    input_hash: str,
    output_hash: str,
    prev_event_hash: str,
) -> dict:
    if event_type not in EVENT_TYPES:
        raise SchemaViolation(f"unknown event_type: {event_type}")
    if not isinstance(actor, dict) or actor.get("kind") not in ACTOR_KINDS:
        raise SchemaViolation(f"invalid actor: {actor!r}")
    if not isinstance(payload, dict):
        raise SchemaViolation("payload must be a dict")
    envelope: dict[str, Any] = {
        "event_id": "E-" + uuid.uuid4().hex,
        "event_type": event_type,
        "session_id": session_id,
        "timestamp": timestamp,
        "actor": actor,
        "payload": payload,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "prev_event_hash": prev_event_hash,
    }
    envelope["event_hash"] = compute_event_hash(envelope)
    return envelope
