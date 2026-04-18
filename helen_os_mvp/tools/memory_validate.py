#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema missing. pip install jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "memory" / "memory_schema_v1.json"
MEM_PATH = ROOT / "memory" / "memory.ndjson"

AUTHORITY_BANNED = re.compile(r"\b(VERDICT|RECEIPT|SEALED|APPROVED|TERMINATION|SHIP)\b", re.IGNORECASE)


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def iter_events(path: Path):
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        ev = json.loads(line)
        if not isinstance(ev, dict):
            raise ValueError(f"Line {i}: event not object")
        out.append(ev)
    return out


def authority_leak_check(ev):
    blob = json.dumps(ev, ensure_ascii=False)
    return not AUTHORITY_BANNED.search(blob)


def main() -> int:
    schema = load_schema()
    events = iter_events(MEM_PATH)
    validator = jsonschema.Draft202012Validator(schema)

    seen_ids = set()
    errors = []

    for idx, ev in enumerate(events):
        for e in validator.iter_errors(ev):
            errors.append(f"Line {idx}: schema error: {e.message}")

        eid = ev.get("event_id")
        if eid in seen_ids:
            errors.append(f"Line {idx}: duplicate event_id {eid}")
        seen_ids.add(eid)

        if not authority_leak_check(ev):
            errors.append(f"Line {idx}: authority-leak token present")

        t = ev.get("type")
        status = ev.get("status")
        if status == "CONFIRMED" and t not in (
            "memory_confirmation_response",
            "memory_resolution",
            "memory_snapshot",
        ):
            errors.append(f"Line {idx}: status=CONFIRMED not allowed for type={t}")

    if errors:
        print("MEMORY_VALIDATE: FAIL")
        for e in errors:
            print(" -", e)
        return 1

    print("MEMORY_VALIDATE: PASS")
    print(f" events={len(events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
