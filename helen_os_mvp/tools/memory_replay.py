#!/usr/bin/env python3

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
MEM_PATH = ROOT / "memory" / "memory.ndjson"


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass
class Pending:
    key: str
    request_id: str
    prior_event_id: str
    new_event_id: str
    predicate: str


def conflict_predicate(prior_value: Any, new_value: Any) -> str:
    if isinstance(prior_value, bool) and isinstance(new_value, bool) and prior_value != new_value:
        return "bool_flip"
    if isinstance(prior_value, (int, float)) and isinstance(new_value, (int, float)) and prior_value != new_value:
        return "number_diff"
    if prior_value != new_value:
        return "json_diff" if (isinstance(prior_value, (dict, list)) or isinstance(new_value, (dict, list))) else "string_diff"
    return "json_diff"


def read_events() -> List[Dict[str, Any]]:
    if not MEM_PATH.exists():
        return []
    out = []
    for line in MEM_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def replay(events: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Pending], str]:
    kv: Dict[str, Any] = {}
    latest_by_key: Dict[str, Dict[str, Any]] = {}
    pending: Dict[str, Pending] = {}

    for ev in events:
        t = ev["type"]
        key = ev.get("key")

        if t == "memory_observation":
            status = ev.get("status")
            if status != "OBSERVED":
                continue
            if not key:
                continue
            new_value = ev.get("value")
            new_id = ev["event_id"]

            if key in latest_by_key:
                prior = latest_by_key[key]
                prior_value = prior.get("value")
                prior_id = prior.get("event_id")

                if prior_value != new_value:
                    pred = conflict_predicate(prior_value, new_value)
                    # leave kv unchanged until resolution
                    pending_id = None
                    for p in pending.values():
                        if p.key == key:
                            pending_id = p.request_id
                            break
                    if not pending_id:
                        pass

            latest_by_key[key] = {"event_id": new_id, "value": new_value, "status": "OBSERVED"}

        elif t == "memory_confirmation_request":
            req = ev["request"]
            request_id = req["request_id"]
            if not key or key not in latest_by_key:
                continue
            new_id = latest_by_key[key]["event_id"]
            prior_id = None
            prior_value = None
            for prev in reversed(events):
                if prev.get("key") == key and prev.get("type") == "memory_observation" and prev.get("event_id") != new_id:
                    pv = prev.get("value")
                    if pv != latest_by_key[key]["value"]:
                        prior_id = prev.get("event_id")
                        prior_value = pv
                        break
            if prior_id is None:
                continue
            pred = conflict_predicate(prior_value, latest_by_key[key]["value"])
            pending[request_id] = Pending(key=key, request_id=request_id, prior_event_id=prior_id, new_event_id=new_id, predicate=pred)

        elif t == "memory_resolution":
            res = ev["resolution"]
            request_id = res["request_id"]
            if request_id in pending:
                p = pending[request_id]
                kept = res.get("kept", [])
                if p.prior_event_id in kept and p.new_event_id in kept:
                    prior_val = None
                    new_val = None
                    for ev2 in events:
                        if ev2.get("event_id") == p.prior_event_id:
                            prior_val = ev2.get("value")
                        if ev2.get("event_id") == p.new_event_id:
                            new_val = ev2.get("value")
                    kv[key] = {"mode": "keep_both", "values": [prior_val, new_val], "event_ids": [p.prior_event_id, p.new_event_id]}
                else:
                    keep_id = kept[0] if kept else p.new_event_id
                    keep_val = None
                    for ev2 in events:
                        if ev2.get("event_id") == keep_id:
                            keep_val = ev2.get("value")
                            break
                    kv[key] = {"mode": "single", "value": keep_val, "event_id": keep_id}
                del pending[request_id]

    state_hash = sha256_hex(canon({"kv": kv, "pending": {k: p.__dict__ for k, p in pending.items()}}))
    return kv, pending, state_hash


def main():
    kv, pending, state_hash = replay(read_events())
    print(canon({"state_hash": state_hash, "kv": kv, "pending": {k: p.__dict__ for k, p in pending.items()}}))


if __name__ == "__main__":
    main()
