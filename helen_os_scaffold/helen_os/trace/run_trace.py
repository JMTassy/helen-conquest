"""
helen_os/trace/run_trace.py — CWL v1.0.1 Standard Grade

Append-only trace logger for non-sovereign telemetry.
Implements S1 (RunTrace Determinism) spec lock.

NORMATIVE RULES (S1):
  - authority=False ALWAYS (enforced in _append, cannot be overridden by caller)
  - tick: orchestrator clock integer, NOT wall-clock (caller must supply)
  - seq: monotone integer, loaded from file on init, incremented per append
  - Hash core MUST NOT include wall-time (timestamp lives in meta only)
  - verify() validates chain integrity without side effects or mutation

Hash formula (Channel C):
  payload_hash_i = SHA256(canonical_json(hash_core_i))
  cum_hash_i = SHA256(b"HELEN_TRACE_V1" || prev_cum_hash_bytes || payload_hash_bytes)

  hash_core_i = {
    "authority": false,
    "event_type": <str>,
    "payload": <dict>,
    "schema_version": "TRACE_EVENT_V1",
    "seq": <int>,
    "tick": <int>
  }

NON-COMPLIANCE POLICY:
  - Callers MUST NOT pass authority=True; _append raises ValueError if attempted
  - Callers MUST supply tick from a deterministic source; wall-clock is advisory only
  - Implementations MUST NOT mutate events after write
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ──────────────────────────────────────────────────────────────────
# Constants (frozen v1.0.1)
# ──────────────────────────────────────────────────────────────────

PREFIX_TRACE = b"HELEN_TRACE_V1"
ZERO_HASH = "0" * 64
SCHEMA_VERSION = "TRACE_EVENT_V1"
HASH_LAW = "CWL_TRACE_V1"


# ──────────────────────────────────────────────────────────────────
# Hash utilities
# ──────────────────────────────────────────────────────────────────

def _payload_hash(hash_core: dict) -> str:
    """SHA256(canonical_json(hash_core)).

    Canonical JSON: sort_keys=True, no extra whitespace.
    hash_core MUST contain only deterministic fields.
    """
    s = json.dumps(hash_core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()


def _trace_cum_hash(prev: str, ph: str) -> str:
    """SHA256(PREFIX_TRACE || prev_trace_hash_bytes || payload_hash_bytes).

    Raw byte concatenation, no delimiters.
    """
    return hashlib.sha256(
        PREFIX_TRACE + bytes.fromhex(prev) + bytes.fromhex(ph)
    ).hexdigest()


# ──────────────────────────────────────────────────────────────────
# TraceLogger
# ──────────────────────────────────────────────────────────────────

class TraceLogger:
    """
    Append-only trace logger (non-sovereign, authority=False always).

    S1 Compliance:
      - tick is provided by caller (orchestrator clock, not wall-time)
      - seq is monotone (loaded from last event on init, +1 per append)
      - Timestamp is metadata ONLY (in meta.timestamp, not in hash core)
      - authority=False is ENFORCED in _append; cannot be overridden

    Usage:
        logger = TraceLogger("storage/run_trace.ndjson")
        cum_hash = logger.append_conquest_tick(tick=42, epoch=1, ...)
        valid, errors = logger.verify()
    """

    def __init__(self, path: Union[str, Path]):
        """Initialize logger, load seq + prev_hash from existing trace file."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Bootstrap from existing trace (idempotent)
        self._seq, self._prev_hash = self._bootstrap()

    # ── Private helpers ──────────────────────────────────────────

    def _bootstrap(self) -> Tuple[int, str]:
        """Load (next_seq, prev_cum_hash) from the last CWL_TRACE_V1 event."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return 0, ZERO_HASH

        last_seq = -1
        last_hash = ZERO_HASH

        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("hash_law") == HASH_LAW:
                        seq = ev.get("seq", -1)
                        if seq > last_seq:
                            last_seq = seq
                            last_hash = ev.get("cum_hash", last_hash)
                except json.JSONDecodeError:
                    pass  # Malformed lines are skipped (not fatal at bootstrap)

        return last_seq + 1, last_hash

    def _append(self, event_type: str, payload: dict, tick: int) -> dict:
        """
        Core append — builds hash over deterministic fields only.

        Hash core (DETERMINISTIC — used for payload_hash):
          schema_version, seq, tick, event_type, payload, authority

        Metadata (NOT hashed — wall-time audit trail only):
          meta.timestamp

        Raises:
            ValueError: if payload contains authority=True
        """
        # S1 enforcement: authority=False always
        if payload.get("authority") is True:
            raise ValueError(
                "S1 violation: authority=True is forbidden in trace events. "
                "Only MAYOR can issue authoritative events (Channel A only)."
            )

        # Hash core: only deterministic fields (sorted by json.dumps sort_keys)
        hash_core: dict = {
            "authority": False,
            "event_type": event_type,
            "payload": payload,
            "schema_version": SCHEMA_VERSION,
            "seq": self._seq,
            "tick": tick,
        }

        ph = _payload_hash(hash_core)
        ch = _trace_cum_hash(self._prev_hash, ph)

        event = {
            **hash_core,
            "payload_hash": ph,
            "prev_cum_hash": self._prev_hash,
            "cum_hash": ch,
            "hash_law": HASH_LAW,
            "meta": {
                # Timestamp is ADVISORY ONLY — not included in hash core
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Advance state
        self._prev_hash = ch
        self._seq += 1
        return event

    # ── Public API ────────────────────────────────────────────────

    def append_conquest_tick(
        self,
        epoch: int = 0,
        input_ref: Optional[Dict[str, str]] = None,
        state_before: Optional[Dict[str, Any]] = None,
        state_after: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        tick: int = 0,
    ) -> str:
        """
        Append a CONQUEST_TICK_V1 trace event.

        Args:
            tick: Orchestrator clock tick (deterministic, NOT wall-time).
                  Use game engine's internal step counter.
            epoch: Game epoch number
            input_ref: Reference to SERPENT_MODE_V1 AST (inc. serpent_ast_hash)
            state_before: Game state snapshot before tick
            state_after: Game state snapshot after tick
            metrics: Tick metrics (delta_score, stability, entropy, ...)

        Returns:
            cum_hash of this event (str) — suitable for Merkle leaf pinning.

        Note:
            tick_id (uuid) from the old API is REMOVED. Use (seq, tick) pair
            as the canonical event identifier: globally unique within a trace.
        """
        payload = {
            "schema": "CONQUEST_TICK_V1",
            "epoch": int(epoch),
            "input_ref": input_ref or {},
            "state_before": state_before or {},
            "state_after": state_after or {},
            "metrics": metrics or {},
        }
        ev = self._append("conquest_tick", payload, tick=tick)
        return ev["cum_hash"]

    def append_event(
        self,
        event_type: str,
        payload: dict,
        tick: int,
    ) -> str:
        """
        Generic trace event append.

        Args:
            event_type: Event type string (e.g. "boot_success", "policy_eval")
            payload: Event payload dict (must NOT contain authority=True)
            tick: Orchestrator clock tick (deterministic)

        Returns:
            cum_hash of this event (str)
        """
        ev = self._append(event_type, payload, tick=tick)
        return ev["cum_hash"]

    def current_hash(self) -> str:
        """Return current cumulative trace hash (suitable for seal's final_trace_hash)."""
        return self._prev_hash

    def current_seq(self) -> int:
        """Return the seq that would be assigned to the NEXT event."""
        return self._seq

    def verify(self) -> Tuple[bool, List[str]]:
        """
        Verify chain integrity of this trace file without side effects.

        Checks:
          1. All CWL_TRACE_V1 events have valid payload_hash (hash core match)
          2. Cumulative hash chain is unbroken (prev → cur)
          3. No event has authority=True

        Returns:
            (valid: bool, errors: list[str])

        Note:
            Non-CWL_TRACE_V1 events (legacy) are skipped, not rejected.
        """
        errors: List[str] = []

        if not self.path.exists():
            return True, []

        events: List[dict] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_no}: JSON parse error: {e}")

        if errors:
            return False, errors

        current = ZERO_HASH
        for ev in events:
            if ev.get("hash_law") != HASH_LAW:
                continue  # Legacy events accepted without strict verification

            seq = ev.get("seq", "?")

            # 1. Authority enforcement
            if ev.get("authority") is True:
                errors.append(f"seq={seq}: authority=True in trace event (S1 violation)")

            # 2. Reconstruct hash core from stored fields
            hash_core = {
                "authority": False,  # always False per spec
                "event_type": ev.get("event_type"),
                "payload": ev.get("payload"),
                "schema_version": ev.get("schema_version"),
                "seq": ev.get("seq"),
                "tick": ev.get("tick"),
            }
            expected_ph = _payload_hash(hash_core)
            actual_ph = ev.get("payload_hash", "")

            if expected_ph != actual_ph:
                errors.append(
                    f"seq={seq}: payload_hash mismatch "
                    f"(expected {expected_ph[:8]}... got {actual_ph[:8]}...)"
                )
                # Advance with stored hash to continue detecting further errors
                current = ev.get("cum_hash", current)
                continue

            # 3. Cumulative hash chain
            expected_ch = _trace_cum_hash(current, expected_ph)
            actual_ch = ev.get("cum_hash", "")
            if expected_ch != actual_ch:
                errors.append(
                    f"seq={seq}: cum_hash mismatch "
                    f"(expected {expected_ch[:8]}... got {actual_ch[:8]}...)"
                )
            current = actual_ch

        return len(errors) == 0, errors


# ──────────────────────────────────────────────────────────────────
# Module-level convenience (backward compat shim — DEPRECATED)
# ──────────────────────────────────────────────────────────────────

def _tid() -> str:  # noqa — kept for import compat, DO NOT USE in new code
    """
    DEPRECATED: tick_id is no longer used. Use (seq, tick) pair instead.
    Returns a deterministic placeholder to avoid import breakage.
    """
    return "tick_DEPRECATED_use_seq_tick"
