# oracle/canonical.py
import hashlib
import json
from copy import deepcopy

def _sort_votes(votes):
    return sorted(votes, key=lambda v: v.get("team",""))

def _strip_fields(obj):
    """
    Remove/normalize fields that must not affect deterministic hashes.
    Enforces: votes[].timestamp, event_log[].t removed if present.
    """
    if isinstance(obj, dict):
        obj = {k: _strip_fields(v) for k, v in obj.items()}
        if "votes" in obj and isinstance(obj["votes"], list):
            obj["votes"] = _sort_votes([{k:v for k,v in vote.items() if k != "timestamp"} for vote in obj["votes"]])
        if "event_log" in obj and isinstance(obj["event_log"], list):
            obj["event_log"] = [{k:v for k,v in ev.items() if k != "t"} for ev in obj["event_log"]]
        # Remove run timestamps if present
        obj.pop("run_id", None)
        obj.pop("timestamp_start", None)
        obj.pop("timestamp_end", None)
        return obj
    if isinstance(obj, list):
        return [_strip_fields(x) for x in obj]
    return obj

def canonical_bytes(payload: dict) -> bytes:
    p = deepcopy(payload)
    p = _strip_fields(p)
    s = json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")

def sha256_hex(payload: dict) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()
