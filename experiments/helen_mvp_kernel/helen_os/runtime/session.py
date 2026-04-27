"""Session: only public API for mutating the ledger.

Public methods (no bypass):
  - start_session()
  - propose_shell(command, requester_id="ai-cognition")
  - terminate(verdict)
  - inspect()
  - replay()
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from helen_os.authority.desire_firewall import scan_payload as scan_desires
from helen_os.authority.gate import Verdict, decide_shell
from helen_os.authority.language_firewall import scan_payload as scan_authority
from helen_os.authority.policy import (
    load_forbidden_desires,
    load_forbidden_tokens,
    load_permissions,
    policy_hash,
)
from helen_os.kernel.reducer import fold
from helen_os.kernel.state import State, state_hash
from helen_os.kernel.verdicts import VALID_TERMINATION_VERDICTS, Verdicts
from helen_os.ledger.event_log import append_event, read_events
from helen_os.ledger.hash_chain import canonical_json, sha256_hex
from helen_os.ledger.schemas import make_actor, make_envelope


class Session:
    def __init__(
        self,
        ledger_path: str | Path,
        permissions_path: str | Path,
        tokens_path: str | Path,
        desires_path: str | Path,
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.permissions_path = Path(permissions_path)
        self.tokens_path = Path(tokens_path)
        self.desires_path = Path(desires_path)
        self.permissions = load_permissions(self.permissions_path)
        self.forbidden_tokens = load_forbidden_tokens(self.tokens_path)
        self.forbidden_desires = load_forbidden_desires(self.desires_path)
        self._policy_hash = policy_hash(self.permissions_path)
        self.state: State = self._fresh_replay()

    # ---- internal -------------------------------------------------------

    def _fresh_replay(self) -> State:
        events = read_events(self.ledger_path)
        return fold(events, forbidden_tokens=self.forbidden_tokens)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _actor(self, kind: str, actor_id: str) -> dict:
        return make_actor(kind, actor_id, self._policy_hash)

    def _append_and_replay(self, event: dict) -> dict:
        # Defense in depth: if AI-authored, scan once at write time too.
        if event["actor"]["kind"] == "AI":
            scan_authority(event["payload"], self.forbidden_tokens)
            scan_desires(event["payload"], self.forbidden_desires)
        append_event(self.ledger_path, event)
        self.state = self._fresh_replay()
        return event

    def _current_session_id(self) -> str:
        if not self.state.session_id or not self.state.cognition_active:
            raise RuntimeError("no active session — call start_session() first")
        return self.state.session_id

    # ---- public ---------------------------------------------------------

    def start_session(self) -> str:
        sid = "S-" + uuid.uuid4().hex[:12]
        ev = make_envelope(
            event_type="COGNITION_STARTED",
            session_id=sid,
            timestamp=self._now_iso(),
            actor=self._actor("RUNTIME", "kernel"),
            payload={"reason": "session_start"},
            input_hash="",
            output_hash="",
            prev_event_hash=self.state.last_event_hash,
        )
        self._append_and_replay(ev)
        return sid

    def propose_shell(self, command: str, requester_id: str = "ai-cognition") -> dict:
        sid = self._current_session_id()
        cmd_hash = sha256_hex(canonical_json({"command": command}))

        # 1. AI proposes
        ev_proposed = make_envelope(
            event_type="EFFECT_PROPOSED",
            session_id=sid,
            timestamp=self._now_iso(),
            actor=self._actor("AI", requester_id),
            payload={"effect_kind": "shell", "command": command},
            input_hash=cmd_hash,
            output_hash="",
            prev_event_hash=self.state.last_event_hash,
        )
        self._append_and_replay(ev_proposed)

        # 2. Gate decides
        verdict, reason = decide_shell(command, self.permissions)
        gate_actor = self._actor("SYSTEM", "gate")

        if verdict == Verdict.DENIED:
            ev_denied = make_envelope(
                event_type="EFFECT_DENIED",
                session_id=sid,
                timestamp=self._now_iso(),
                actor=gate_actor,
                payload={"effect_kind": "shell", "command": command, "gate_reason": reason},
                input_hash=cmd_hash,
                output_hash="",
                prev_event_hash=self.state.last_event_hash,
            )
            self._append_and_replay(ev_denied)
            return {"verdict": Verdict.DENIED, "reason": reason, "outcome": None}

        # 3. Authorized → append and execute
        ev_auth = make_envelope(
            event_type="EFFECT_AUTHORIZED",
            session_id=sid,
            timestamp=self._now_iso(),
            actor=gate_actor,
            payload={"effect_kind": "shell", "command": command, "gate_reason": reason},
            input_hash=cmd_hash,
            output_hash="",
            prev_event_hash=self.state.last_event_hash,
        )
        self._append_and_replay(ev_auth)

        from helen_os.tools.terminal_executor import run_authorized
        allowed_set = set(self.permissions["shell"]["allow"])
        try:
            outcome = run_authorized(command, allowed_set)
            ev_exec = make_envelope(
                event_type="EFFECT_EXECUTED",
                session_id=sid,
                timestamp=self._now_iso(),
                actor=self._actor("RUNTIME", "sandbox"),
                payload={"effect_kind": "shell", "command": command, "outcome": outcome.to_dict()},
                input_hash=cmd_hash,
                output_hash=sha256_hex(canonical_json(outcome.to_dict())),
                prev_event_hash=self.state.last_event_hash,
            )
            self._append_and_replay(ev_exec)
            return {"verdict": Verdict.AUTHORIZED, "reason": reason, "outcome": outcome.to_dict()}
        except Exception as e:  # noqa: BLE001
            ev_fail = make_envelope(
                event_type="EFFECT_FAILED",
                session_id=sid,
                timestamp=self._now_iso(),
                actor=self._actor("RUNTIME", "sandbox"),
                payload={"effect_kind": "shell", "command": command, "error": repr(e)},
                input_hash=cmd_hash,
                output_hash="",
                prev_event_hash=self.state.last_event_hash,
            )
            self._append_and_replay(ev_fail)
            return {"verdict": Verdict.AUTHORIZED, "reason": reason, "error": repr(e), "outcome": None}

    def terminate(self, verdict: str, operator_id: str | None = None) -> str:
        if verdict not in VALID_TERMINATION_VERDICTS:
            raise ValueError(f"invalid termination verdict: {verdict}")
        sid = self.state.session_id or "no-session"
        if verdict == Verdicts.OPERATOR_SHIP:
            actor = self._actor("OPERATOR", operator_id or "operator")
        else:
            actor = self._actor("RUNTIME", "kernel")
        ev = make_envelope(
            event_type="COGNITION_TERMINATED",
            session_id=sid,
            timestamp=self._now_iso(),
            actor=actor,
            payload={"verdict": verdict},
            input_hash="",
            output_hash="",
            prev_event_hash=self.state.last_event_hash,
        )
        self._append_and_replay(ev)
        return verdict

    def inspect(self) -> dict:
        return {
            "session_id": self.state.session_id,
            "cognition_active": self.state.cognition_active,
            "events_seen": self.state.events_seen,
            "proposed": self.state.proposed_count,
            "authorized": self.state.authorized_count,
            "denied": self.state.denied_count,
            "executed": self.state.executed_count,
            "failed": self.state.failed_count,
            "terminated": self.state.terminated,
            "last_verdict": self.state.last_verdict,
            "last_event_hash": self.state.last_event_hash,
            "state_hash": state_hash(self.state),
        }

    def replay(self) -> dict:
        st = self._fresh_replay()
        return {"events_seen": st.events_seen, "state_hash": state_hash(st)}
