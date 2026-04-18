import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime

MEM_PATH = Path(__file__).resolve().parent / "memory.ndjson"

# Simple regex extractors for preferences + facts
PREF_PATTERNS = [
    (re.compile(r"\bI prefer (.+)$", re.I), "user.preference.general"),
    (re.compile(r"\bMy preference is (.+)$", re.I), "user.preference.general"),
    (re.compile(r"\bI like (.+)$", re.I), "user.preference.likes"),
]
FACT_PATTERNS = [
    (re.compile(r"\bI am (.+)$", re.I), "user.profile.identity"),
    (re.compile(r"\bMy name is (.+)$", re.I), "user.profile.name"),
    (re.compile(r"\bI work as (.+)$", re.I), "user.profile.role"),
]


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def make_event(**kwargs) -> Dict[str, Any]:
    return {
        "schema_version": "MEMORY_V1",
        "event_id": "ev_" + uuid.uuid4().hex[:12],
        "t": now_iso(),
        **kwargs,
    }


def load_events() -> List[Dict[str, Any]]:
    if not MEM_PATH.exists():
        return []
    events = []
    for line in MEM_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def append_event(ev: Dict[str, Any]) -> None:
    MEM_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MEM_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def conflict_predicate(prior_value: Any, new_value: Any) -> str:
    if isinstance(prior_value, bool) and isinstance(new_value, bool) and prior_value != new_value:
        return "bool_flip"
    if isinstance(prior_value, (int, float)) and isinstance(new_value, (int, float)) and prior_value != new_value:
        return "number_diff"
    if prior_value != new_value:
        return "json_diff" if isinstance(prior_value, (dict, list)) or isinstance(new_value, (dict, list)) else "string_diff"
    return "json_diff"


@dataclass
class Pending:
    request_id: str
    key: str
    prior_event_id: str
    new_event_id: str
    prior_value: Any
    new_value: Any


class MemoryKernel:
    def __init__(self):
        self.events = load_events()
        self.pending = self._build_pending()

    def _build_pending(self) -> Dict[str, Pending]:
        pending = {}
        # attach any outstanding confirmation requests
        for ev in self.events:
            if ev.get("type") == "memory_confirmation_request":
                req = ev.get("request", {})
                pending[req.get("request_id")] = Pending(
                    request_id=req.get("request_id"),
                    key=ev.get("key"),
                    prior_event_id="",
                    new_event_id="",
                    prior_value=None,
                    new_value=None,
                )
            if ev.get("type") == "memory_resolution":
                req = ev.get("resolution", {}).get("request_id")
                if req in pending:
                    del pending[req]
        return pending

    def _last_value(self, key: str) -> Tuple[str, Any]:
        for ev in reversed(self.events):
            if ev.get("key") == key and ev.get("type") == "memory_observation":
                return ev.get("event_id"), ev.get("value")
        return "", None

    def append_observation(self, key: str, value: Any, actor: str, status: str, source: Dict[str, Any]):
        ev = make_event(
            type="memory_observation",
            actor=actor,
            key=key,
            value=value,
            status=status,
            source=source,
        )
        append_event(ev)
        self.events.append(ev)
        return ev

    def process_user_text(self, text: str, actor: str, turn_id: int) -> Dict[str, Any]:
        pending_question = None
        observations = []

        for pattern, key in PREF_PATTERNS + FACT_PATTERNS:
            m = pattern.search(text)
            if m:
                observations.append((key, m.group(1).strip()))

        for key, val in observations:
            ev = self.append_observation(
                key=key,
                value=val,
                actor=actor,
                status="OBSERVED",
                source={"turn_id": turn_id, "message_id": None, "span": "user_text"},
            )
            prior_id, prior_val = self._last_value(key)
            # If conflict, emit conflict + confirmation request
            if prior_id and prior_val is not None and prior_val != val:
                pred = conflict_predicate(prior_val, val)
                conflict_ev = make_event(
                    type="memory_conflict_detected",
                    actor="system",
                    key=key,
                    value=None,
                    status="DISPUTED",
                    conflict={
                        "predicate": pred,
                        "prior_event_id": prior_id,
                        "prior_value": prior_val,
                        "new_event_id": ev["event_id"],
                        "new_value": val,
                    },
                )
                append_event(conflict_ev)
                self.events.append(conflict_ev)

                request_id = "req_" + uuid.uuid4().hex[:8]
                question = f"Conflict on {key}. Confirm new, keep old, or keep both?"
                req_ev = make_event(
                    type="memory_confirmation_request",
                    actor="assistant",
                    key=key,
                    value=None,
                    status="DISPUTED",
                    request={
                        "request_id": request_id,
                        "question": question,
                        "options": ["confirm_new", "confirm_old", "keep_both"],
                    },
                )
                append_event(req_ev)
                self.events.append(req_ev)
                self.pending[request_id] = Pending(
                    request_id=request_id,
                    key=key,
                    prior_event_id=prior_id,
                    new_event_id=ev["event_id"],
                    prior_value=prior_val,
                    new_value=val,
                )
                pending_question = question

        return {"pending_question": pending_question}

    def confirm_pending(self, choice: str, actor: str, turn_id: int) -> Tuple[bool, str]:
        if not self.pending:
            return False, "No pending confirmation."
        request_id, p = next(iter(self.pending.items()))
        choice_map = {
            "new": "confirm_new",
            "old": "confirm_old",
            "both": "keep_both",
        }
        if choice not in choice_map:
            return False, "Invalid choice. Use: new | old | both"
        ch = choice_map[choice]

        resp_ev = make_event(
            type="memory_confirmation_response",
            actor=actor,
            key=p.key,
            value=None,
            status="CONFIRMED",
            response={"request_id": request_id, "choice": ch},
        )
        append_event(resp_ev)
        self.events.append(resp_ev)

        kept = []
        if ch == "confirm_new":
            kept = [p.new_event_id]
        elif ch == "confirm_old":
            kept = [p.prior_event_id]
        else:
            kept = [p.prior_event_id, p.new_event_id]

        res_ev = make_event(
            type="memory_resolution",
            actor="system",
            key=p.key,
            value=None,
            status="CONFIRMED",
            resolution={
                "request_id": request_id,
                "kept": kept,
                "status_updates": [
                    {"event_id": k, "status": "DISPUTED"} for k in kept
                ],
            },
        )
        append_event(res_ev)
        self.events.append(res_ev)
        del self.pending[request_id]
        return True, f"Recorded confirmation: {ch}"

    def summarize_context(self, max_items: int = 10) -> str:
        # Simple summary: last N observations
        obs = [e for e in self.events if e.get("type") == "memory_observation"]
        obs = obs[-max_items:]
        parts = []
        for e in obs:
            parts.append(f"{e.get('key')}={e.get('value')} [{e.get('status')}]")
        return "; ".join(parts) if parts else "(none)"
