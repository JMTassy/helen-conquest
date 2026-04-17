#!/usr/bin/env python3
# Validate EVENT_V1 schema + HAL_VERDICT_V1 for turn payloads.

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema missing. pip install jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_EVENT = ROOT / "schemas" / "event_v1.schema.json"
SCHEMA_HAL = ROOT / "schemas" / "hal_verdict_v1.schema.json"


def load_schema(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_sorted_unique(arr):
    return arr == sorted(arr) and len(arr) == len(set(arr))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_turn_schema.py <ledger.ndjson>")
        return 2
    path = Path(sys.argv[1])
    ev_schema = load_schema(SCHEMA_EVENT)
    hal_schema = load_schema(SCHEMA_HAL)
    ev_validator = jsonschema.Draft202012Validator(ev_schema)
    hal_validator = jsonschema.Draft202012Validator(hal_schema)

    errors = []
    idx = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        for e in ev_validator.iter_errors(ev):
            errors.append(f"Line {idx}: {e.message}")
        if ev.get("type") == "turn":
            payload = ev.get("payload", {})
            if payload.get("channel_contract") != "HER_HAL_V1":
                errors.append(f"Line {idx}: turn missing channel_contract HER_HAL_V1")
            hal = payload.get("hal")
            if not isinstance(hal, dict):
                errors.append(f"Line {idx}: turn missing hal object")
            else:
                for e in hal_validator.iter_errors(hal):
                    errors.append(f"Line {idx}: hal {e.message}")
                # sortedness requirements
                rc = hal.get("reason_codes", [])
                rf = hal.get("required_fixes", [])
                if rc and not is_sorted_unique(rc):
                    errors.append(f"Line {idx}: reason_codes must be sorted+unique")
                if rf and not is_sorted_unique(rf):
                    errors.append(f"Line {idx}: required_fixes must be sorted+unique")
        idx += 1

    if errors:
        print("TURN_SCHEMA_VALIDATE: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("TURN_SCHEMA_VALIDATE: PASS")
    print(f" events={idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
